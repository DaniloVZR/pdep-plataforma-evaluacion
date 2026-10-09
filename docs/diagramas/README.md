# Diagramas del RTF3 (versión 2)

Fuentes de las figuras del documento de diseño de pruebas estructurales.

| Archivo | Figura | Herramienta |
|---|---|---|
| `clases_hu003.puml` | Figura 1. Clases de HU-003 | PlantUML |
| `clases_hu005.puml` | Figura 2. Clases de HU-005 | PlantUML |
| `clases_hu007.puml` | Figura 3. Clases de HU-007 | PlantUML |
| `clases_excepciones.puml` | Figura 4. Excepciones y manejo de errores | PlantUML |
| `grafos.py` | Figuras 5 a 8. Actividad (flujo interno) de HU-003, HU-005 y HU-007 | Python + Graphviz |

`estilo.iuml` es el estilo común (blanco y negro) que incluyen los `.puml`.

`grafos.py` define una sola vez los nodos, las aristas y los caminos básicos de cada
método. Al ejecutarlo verifica que V(G) = E − N + 2 = decisiones + 1, que cada camino
recorre aristas existentes y que los caminos son linealmente independientes; luego dibuja
los diagramas de actividad y escribe `caminos.json` con las tablas de la sección 5.2.

```bash
cd docs/diagramas
java -jar plantuml.jar -tpng clases_*.puml   # requiere PlantUML
python grafos.py                              # requiere Graphviz (comando dot)
```
