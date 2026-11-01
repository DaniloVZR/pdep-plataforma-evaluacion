# Diagramas del RTF3 (versión 3)

Fuentes de las figuras del documento de diseño de pruebas estructurales.

| Archivo | Figura | Herramienta |
|---|---|---|
| `clases_hu003.puml` | Figura 1. Clases de HU-003 | PlantUML |
| `clases_hu005.puml` | Figura 2. Clases de HU-005 (incluye `SqliteProyectoRepositorio`) | PlantUML |
| `clases_hu007.puml` | Figura 3. Clases de HU-007 (incluye `SqliteEvaluacionRepositorio` y `SqliteRubricaRepositorio`) | PlantUML |
| `clases_excepciones.puml` | Jerarquía de excepciones (apoyo; no es una figura de la v3) | PlantUML |
| `grafos.py` | Figuras 4 a 7. Actividad (flujo interno) de HU-003, HU-005 y HU-007 | Python + Graphviz |
| `grafos.py` | Figuras 8 a 10. Subprocesos: flujo interno de los validadores y de `Rubrica.pesos_validos` | Python + Graphviz |

Cambios de la versión 3 (retroalimentación del Trabajo 5):

- Las Figuras 2 y 3 muestran los repositorios SQLite, como la Figura 1, y las tres figuras de
  clases tienen una nota sobre cómo `construir_servicio()` usa la base temporal en las pruebas.
- El nodo 2 de las Figuras 4, 5 y 6 y el nodo 14 de la Figura 6 son subprocesos; su detalle,
  con un rombo por cada `if`, `for` o `except`, está en las Figuras 8 a 10.
- La flecha punteada de las Figuras 4, 5 y 7 es la salida `ErrorPersistencia` (500). No suma a
  V(G) porque no la decide el servicio sino `transaccion()` en el repositorio.

`estilo.iuml` es el estilo común (blanco y negro) que incluyen los `.puml`.

`grafos.py` define una sola vez los nodos, las aristas y los caminos básicos de cada
método. Al ejecutarlo verifica que V(G) = E − N + 2 = decisiones + 1, que cada camino
recorre aristas existentes y que los caminos son linealmente independientes; luego dibuja
los diagramas de actividad y escribe `caminos.json` con las tablas de la sección 5.2.
Los validadores (`Val_*.png`) se verifican con V(G) = E − N + 2 = decisiones + 1.

```bash
cd docs/diagramas
java -jar plantuml.jar -tpng clases_*.puml   # requiere PlantUML
python grafos.py                              # requiere Graphviz (comando dot)
```
