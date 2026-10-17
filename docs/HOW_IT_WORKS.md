# Cómo funciona

Esto es para contarlo en una entrevista, en castellano rioplatense. Los datos son simulados. La empresa Harborline Cooperative es ficticia.

## Para qué sirve

Mirá: el modelo razona, pero la confianza sale del sistema de alrededor. Este repo es ese sistema, en chico. Tiene un inventario de 12 agentes, reglas que corren en CI, trazas JSONL sintéticas y un tablero HTML estático de costo y latencia.

No atiende a nadie. No llama a un proveedor pago. Si lo corrés en tu máquina, el costo es cero.

## Analogía

Fijate en el encargado de un edificio. No vive en cada departamento. Tiene una planilla: quién es el responsable, quién lo cubre, y qué departamentos necesitan que alguien firme antes de tocar la llave de gas. Tiene un medidor. Si el medidor se dispara, no se pone a discutir con el caño: cierra la llave y anota qué versión de la canilla estaba puesta.

Acá la planilla es `inventory/fleet.yaml`. El medidor es el agregador de trazas. La llave es el kill switch. La versión de la canilla es el registro de prompts.

## Paso a paso

1. **Inventario.** Cada agente tiene id, dueño, dueño de respaldo, versión, modelo simulado, propósito, clases de datos, tier (bajo, medio, alto), compuertas de aprobación, topes de presupuesto, SLO y fecha de última revisión. El esquema JSON rechaza un archivo mal formado.

2. **Política.** `python3 -m governance_board policy` lee el inventario y el registro de prompts. Un agente de tier alto sin compuerta humana, o sin dueño de respaldo distinto, falla. Un tope por corrida más grande que el tope diario falla. Una revisión más vieja que N días falla. La fecha de "hoy" se inyecta (`--today` o `GOVERNANCE_TODAY`) para que el chequeo sea reproducible.

3. **Fixture que tiene que fallar.** `inventory/violating.yaml` es válido para el esquema y inválido para la política. CI exige que ese comando salga con código distinto de cero.

4. **Trazas.** El generador usa una semilla fija y escribe JSONL: corrida, agente, versión, tiempo, estado, tokens, costo en micro-USD, latencia, aprobación y efectos. Los números salen de un rate card simulado, no de un proveedor.

5. **Agregador.** Por agente calcula costo, latencia p50/p95, tasa de aprobación humana, tasa de rechazo y quema del tope diario. Si un día se pasa del tope, o si la p95 se pasa del SLO, deja una alerta.

6. **Tablero.** Un HTML con CSS y gráficos SVG adentro, más un Markdown. No hay CDN ni red.

7. **Evals.** No miran la secuencia exacta de herramientas. Miran invariantes: ningún efecto dañino, costo dentro del tope, ningún efecto externo sin `approval: approved`. `eval-regression` corre un caso malo y **tiene que fallar**. CI comprueba esa falla.

8. **Incidente de costo.** El runbook corta el agente (`kill-switch`) y vuelve el prompt a una versión anterior (`rollback`).

## Glosario

| Palabra | Qué es acá |
| --- | --- |
| Tier | Rubro interno: bajo, medio o alto. No es una categoría legal. |
| Compuerta | Un humano tiene que aprobar antes de un efecto que sale del sistema. |
| Efecto | Algo que la corrida dice que hizo, por ejemplo escribir una nota de libro mayor. |
| micro-USD | Millonésima de dólar. 1,000,000 micro-USD = 1 USD en esta convención. |
| SLO | Objetivo de p95 de latencia y de costo por corrida. En este repo los números de SLO son [EST] y los de latencia son simulados. |
| Kill switch | Campo del inventario. Enganchado significa `status: disabled`. |
| Casete | Respuesta grabada de un proveedor falso. Sirve para no ir a la red. |

## Límites honestos

- No certifica nada. El mapa a NIST y a la ley de IA de la UE es material de estudio. Mirá `docs/RISKS.md`.
- No mide si la respuesta está bien. Mide gates, costo y latencia simulada.
- No pagina a nadie. La alerta queda en el HTML.
- No hay usuarios ni permisos.
- El generador no es tráfico real. Si cambiás la semilla, cambian los números.
- Reescribir el YAML con el kill switch o el rollback puede perder comentarios.

Si te preguntan "¿esto corrió en producción?", la respuesta es no. Corrió en esta repo, con datos sintéticos, y el comando está en el README.
