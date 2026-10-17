"""Command line interface for the governance and cost board."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import yaml

from governance_board import __version__
from governance_board.aggregate import aggregate
from governance_board.config import ConfigError, Settings, load_settings
from governance_board.controls import (
    ControlError,
    disengage_kill_switch,
    engage_kill_switch,
    load_yaml_mapping,
    rollback_agent,
    write_mapping,
)
from governance_board.evalkit.runner import EvalError, run_path
from governance_board.generate import ProfileError, generate, load_profile
from governance_board.inventory import InventorySchemaError, load_inventory
from governance_board.logging_setup import log_event, setup_logging
from governance_board.policy import PolicyReport, Violation, check_policy, render_text
from governance_board.prompts import RegistryError, current_versions, load_registry
from governance_board.report import write_report
from governance_board.secretscan import scan_path
from governance_board.trace import TraceError, dump_jsonl, load_jsonl

LOGGER = logging.getLogger("governance_board.cli")


def _parse_today(value: str | None, settings: Settings) -> datetime:
    raw = value or settings.today.isoformat()
    try:
        return datetime.strptime(raw, "%Y-%m-%d")
    except ValueError as exc:
        raise ConfigError(f"--today must be YYYY-MM-DD, got {raw!r}") from exc


def _emit_policy(report: PolicyReport, as_json: bool) -> None:
    if as_json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(render_text(report), end="")


def cmd_policy(args: argparse.Namespace, settings: Settings) -> int:
    today = _parse_today(args.today, settings).date()
    try:
        inventory = load_inventory(Path(args.inventory))
    except InventorySchemaError as exc:
        report = PolicyReport(violations=tuple(Violation("schema", None, message) for message in exc.messages))
        _emit_policy(report, args.json)
        log_event(LOGGER, logging.ERROR, "inventory schema failed", event="policy_schema")
        return 1
    prompts = None
    if args.prompts:
        prompts = current_versions(load_registry(Path(args.prompts)))
    report = check_policy(inventory, today=today, prompts=prompts)
    _emit_policy(report, args.json)
    log_event(
        LOGGER,
        logging.INFO,
        "policy check finished",
        event="policy_check",
        violations=len(report.violations),
        ok=report.ok,
    )
    return 0 if report.ok else 1


def cmd_generate(args: argparse.Namespace, settings: Settings) -> int:
    del settings
    inventory = load_inventory(Path(args.inventory))
    events, meta = generate(inventory, load_profile(Path(args.profile)))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(dump_jsonl(events), encoding="utf-8")
    meta_path = out.with_suffix(".meta.json")
    meta_path.write_text(json.dumps(meta.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    log_event(LOGGER, logging.INFO, "traces written", event="generate_traces", path=str(out), events=meta.event_count)
    print(f"wrote {out} ({meta.event_count} events)")
    return 0


def _load_meta(traces: Path) -> dict[str, object]:
    meta_path = traces.with_suffix(".meta.json")
    if not meta_path.exists():
        return {}
    loaded = json.loads(meta_path.read_text(encoding="utf-8"))
    if isinstance(loaded, dict):
        return loaded
    return {}


def cmd_report(args: argparse.Namespace, settings: Settings) -> int:
    del settings
    inventory = load_inventory(Path(args.inventory))
    events = load_jsonl(Path(args.traces))
    board = aggregate(inventory, events)
    extra = {
        "trace_file": args.traces,
        "event_count": len(events),
        "meta": _load_meta(Path(args.traces)),
        "command": "python -m governance_board report",
    }
    write_report(board, Path(args.out), generated_on=args.generated_on, extra=extra)
    log_event(
        LOGGER,
        logging.INFO,
        "report written",
        event="report",
        alerts=len(board.alerts),
        out=args.out,
    )
    print(f"wrote {args.out} ({len(board.alerts)} alerts)")
    return 0


def cmd_demo(args: argparse.Namespace, settings: Settings) -> int:
    root = Path(args.root)
    inventory_path = root / "inventory" / "fleet.yaml"
    profile_path = root / "traces" / "generation.yaml"
    prompts_path = root / "prompts" / "registry.yaml"
    today = _parse_today(args.today, settings).date()
    inventory = load_inventory(inventory_path)
    prompts = current_versions(load_registry(prompts_path))
    report = check_policy(inventory, today=today, prompts=prompts)
    if not report.ok:
        _emit_policy(report, False)
        return 1
    events, meta = generate(inventory, load_profile(profile_path))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "traces.jsonl").write_text(dump_jsonl(events), encoding="utf-8")
    (out / "traces.meta.json").write_text(
        json.dumps(meta.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    board = aggregate(inventory, events)
    write_report(
        board,
        out,
        generated_on=today.isoformat(),
        extra={"label": "simulated", "meta": meta.to_dict(), "event_count": meta.event_count},
    )
    print(f"policy: PASS ({len(inventory.agents)} agents)")
    print(f"wrote {out / 'index.html'} ({meta.event_count} simulated events, {len(board.alerts)} alerts)")
    return 0


def _run_eval(path: Path, settings: Settings) -> int:
    result = run_path(path, settings=settings)
    payload = {
        "ok": result.ok,
        "cases": result.case_count,
        "breaches": [item.to_dict() for item in result.breaches],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    log_event(
        LOGGER,
        logging.INFO if result.ok else logging.ERROR,
        "eval finished",
        event="eval",
        ok=result.ok,
        breaches=len(result.breaches),
    )
    return 0 if result.ok else 1


def cmd_eval(args: argparse.Namespace, settings: Settings) -> int:
    return _run_eval(Path(args.suite), settings)


def cmd_eval_regression(args: argparse.Namespace, settings: Settings) -> int:
    return _run_eval(Path(args.suite), settings)


def cmd_secretscan(args: argparse.Namespace, settings: Settings) -> int:
    del settings
    findings = scan_path(Path(args.root))
    for finding in findings:
        print(f"{finding.path}:{finding.line}: {finding.rule}")
    log_event(LOGGER, logging.INFO, "secret scan finished", event="secretscan", findings=len(findings))
    return 1 if findings else 0


def cmd_kill_switch(args: argparse.Namespace, settings: Settings) -> int:
    del settings
    inventory = load_yaml_mapping(Path(args.inventory))
    if args.disengage:
        updated = disengage_kill_switch(inventory, args.agent_id)
    else:
        updated = engage_kill_switch(inventory, args.agent_id)
    destination = Path(args.inventory) if args.in_place else Path(args.output)
    write_mapping(destination, updated)
    print(f"wrote {destination}")
    return 0


def cmd_rollback(args: argparse.Namespace, settings: Settings) -> int:
    del settings
    registry = load_registry(Path(args.registry))
    inventory = load_yaml_mapping(Path(args.inventory)) if args.inventory else None
    new_registry, new_inventory = rollback_agent(registry, inventory, args.agent_id, args.to_version)
    write_mapping(Path(args.registry_output), new_registry)
    print(f"wrote {args.registry_output}")
    if new_inventory is not None:
        if not args.inventory_output:
            raise ControlError("--inventory-output is required when --inventory is set")
        write_mapping(Path(args.inventory_output), new_inventory)
        print(f"wrote {args.inventory_output}")
    return 0


def cmd_version(args: argparse.Namespace, settings: Settings) -> int:
    del args, settings
    print(__version__)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="governance-board", description="Synthetic agent governance and cost board")
    sub = parser.add_subparsers(dest="command", required=True)

    policy = sub.add_parser("policy", help="run policy-as-code checks")
    policy.add_argument("--inventory", required=True)
    policy.add_argument("--prompts")
    policy.add_argument("--today")
    policy.add_argument("--json", action="store_true")
    policy.set_defaults(func=cmd_policy)

    generate_cmd = sub.add_parser("generate-traces", help="write seeded synthetic JSONL traces")
    generate_cmd.add_argument("--inventory", required=True)
    generate_cmd.add_argument("--profile", required=True)
    generate_cmd.add_argument("--out", required=True)
    generate_cmd.set_defaults(func=cmd_generate)

    report = sub.add_parser("report", help="write a static HTML and Markdown board")
    report.add_argument("--inventory", required=True)
    report.add_argument("--traces", required=True)
    report.add_argument("--out", required=True)
    report.add_argument("--generated-on", required=True)
    report.set_defaults(func=cmd_report)

    demo = sub.add_parser("demo", help="policy, generate, and write a board under --out")
    demo.add_argument("--root", default=".")
    demo.add_argument("--out", default="demo-out")
    demo.add_argument("--today")
    demo.set_defaults(func=cmd_demo)

    eval_cmd = sub.add_parser("eval", help="run invariant evals (must pass)")
    eval_cmd.add_argument("--suite", default="evals/suite.yaml")
    eval_cmd.set_defaults(func=cmd_eval)

    regression = sub.add_parser("eval-regression", help="run the forced-regression suite (must fail)")
    regression.add_argument("--suite", default="evals/regression.yaml")
    regression.set_defaults(func=cmd_eval_regression)

    scan = sub.add_parser("secretscan", help="scan a tree for secret-shaped strings")
    scan.add_argument("--root", default=".")
    scan.set_defaults(func=cmd_secretscan)

    kill = sub.add_parser("kill-switch", help="engage or disengage an agent kill switch")
    kill.add_argument("--inventory", required=True)
    kill.add_argument("--agent-id", required=True)
    kill.add_argument("--output")
    kill.add_argument("--in-place", action="store_true")
    kill.add_argument("--disengage", action="store_true")
    kill.set_defaults(func=cmd_kill_switch)

    roll = sub.add_parser("rollback", help="point a prompt registry at an older version")
    roll.add_argument("--registry", required=True)
    roll.add_argument("--registry-output", required=True)
    roll.add_argument("--agent-id", required=True)
    roll.add_argument("--to-version", required=True)
    roll.add_argument("--inventory")
    roll.add_argument("--inventory-output")
    roll.set_defaults(func=cmd_rollback)

    version = sub.add_parser("version", help="print the package version")
    version.set_defaults(func=cmd_version)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        settings = load_settings()
        setup_logging(settings.log_level)
        if args.command == "kill-switch" and not args.in_place and not args.output:
            parser.error("kill-switch requires --output or --in-place")
        return int(args.func(args, settings))
    except (
        ConfigError,
        TraceError,
        ProfileError,
        RegistryError,
        ControlError,
        EvalError,
        OSError,
        yaml.YAMLError,
        json.JSONDecodeError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
