# Reporte de pruebas funcionales (RTF4 v2)

Plataforma de evaluación de proyectos institucionales: pruebas de caja negra de HU-003,
HU-005 y HU-007.

- **Fecha de ejecución:** 13/11/2026, de 17:31:37 a 17:32:32 (hora de Colombia)
- **Ejecutado por:** Joimar Danilo Urrego David
- **Versión probada:** commit `9747ece` de la rama de pruebas
- **Base de datos:** nueva, con `flask --app app init-db --demo` y `pruebas_funcionales/datos_prueba.sql`
- **Herramientas:** Postman/Newman para la API (28 casos) y Playwright con pytest para las pantallas (33 casos)
- **Orden:** el de la matriz de la sección 5, de CP-01 a CP-61
- **Resultado:** 61 de 61 casos pasaron
- **Preparación** (ferias por fechas y asignaciones de HU-006): sin problemas

## Resumen por tarea de Jira

Los casos sin sesión (CP-56 a CP-61) se cuentan en la tarea de la historia que prueban.

| Tarea | Historia | Casos | Pasaron | Fallaron |
|---|---|---|---|---|
| PDEP-61 | HU-003 | 19 | 19 | 0 |
| PDEP-62 | HU-005 | 19 | 19 | 0 |
| PDEP-63 | HU-007 | 23 | 23 | 0 |

## Resultado de cada caso

| CP | HU | Tarea | Herramienta | Prueba | Resultado | Detalle si falló |
|---|---|---|---|---|---|---|
| CP-01 | HU-003 | PDEP-61 | Playwright | `test_cp01_registra_estudiante_muestra_aviso_verde` | Pasó |  |
| CP-02 | HU-003 | PDEP-61 | Playwright | `test_cp02_registra_docente_muestra_aviso_verde` | Pasó |  |
| CP-03 | HU-003 | PDEP-61 | Postman | `CP-03` | Pasó |  |
| CP-04 | HU-003 | PDEP-61 | Playwright | `test_cp04_nombres_vacios_marca_el_campo` | Pasó |  |
| CP-05 | HU-003 | PDEP-61 | Playwright | `test_cp05_correo_vacio_marca_el_campo` | Pasó |  |
| CP-06 | HU-003 | PDEP-61 | Playwright | `test_cp06_correo_sin_arroba_marca_el_campo` | Pasó |  |
| CP-07 | HU-003 | PDEP-61 | Playwright | `test_cp07_sin_programa_marca_la_lista` | Pasó |  |
| CP-08 | HU-003 | PDEP-61 | Playwright | `test_cp08_correo_personal_muestra_recuadro_rojo` | Pasó |  |
| CP-09 | HU-003 | PDEP-61 | Postman | `CP-09` | Pasó |  |
| CP-10 | HU-003 | PDEP-61 | Postman | `CP-10` | Pasó |  |
| CP-11 | HU-003 | PDEP-61 | Playwright | `test_cp11_correo_repetido_muestra_recuadro_rojo` | Pasó |  |
| CP-12 | HU-003 | PDEP-61 | Postman | `CP-12` | Pasó |  |
| CP-13 | HU-003 | PDEP-61 | Postman | `CP-13` | Pasó |  |
| CP-14 | HU-003 | PDEP-61 | Postman | `CP-14` | Pasó |  |
| CP-15 | HU-003 | PDEP-61 | Playwright | `test_cp15_estudiante_no_ve_registrar_usuario` | Pasó |  |
| CP-16 | HU-003 | PDEP-61 | Postman | `CP-16` | Pasó |  |
| CP-17 | HU-003 | PDEP-61 | Playwright | `test_cp17_evaluador_no_ve_registrar_usuario` | Pasó |  |
| CP-18 | HU-005 | PDEP-62 | Playwright | `test_cp18_inscribe_proyecto_en_feria_abierta` | Pasó |  |
| CP-19 | HU-005 | PDEP-62 | Postman | `CP-19` | Pasó |  |
| CP-20 | HU-005 | PDEP-62 | Playwright | `test_cp20_nombre_vacio_marca_el_campo` | Pasó |  |
| CP-21 | HU-005 | PDEP-62 | Playwright | `test_cp21_sin_feria_marca_feria_y_asignaturas` | Pasó |  |
| CP-22 | HU-005 | PDEP-62 | Playwright | `test_cp22_pia_con_una_asignatura_no_se_envia` | Pasó |  |
| CP-23 | HU-005 | PDEP-62 | Postman | `CP-23` | Pasó |  |
| CP-24 | HU-005 | PDEP-62 | Postman | `CP-24` | Pasó |  |
| CP-25 | HU-005 | PDEP-62 | Postman | `CP-25` | Pasó |  |
| CP-26 | HU-005 | PDEP-62 | Postman | `CP-26` | Pasó |  |
| CP-27 | HU-005 | PDEP-62 | Playwright | `test_cp27_feria_futura_aun_no_abre` | Pasó |  |
| CP-28 | HU-005 | PDEP-62 | Playwright | `test_cp28_feria_que_inicia_hoy_acepta_la_inscripcion` | Pasó |  |
| CP-29 | HU-005 | PDEP-62 | Postman | `CP-29` | Pasó |  |
| CP-30 | HU-005 | PDEP-62 | Playwright | `test_cp30_feria_vencida_plazo_vencido` | Pasó |  |
| CP-31 | HU-005 | PDEP-62 | Playwright | `test_cp31_proyecto_repetido_en_la_misma_feria` | Pasó |  |
| CP-32 | HU-005 | PDEP-62 | Postman | `CP-32` | Pasó |  |
| CP-33 | HU-005 | PDEP-62 | Playwright | `test_cp33_evaluador_no_ve_inscribir_proyecto` | Pasó |  |
| CP-34 | HU-005 | PDEP-62 | Postman | `CP-34` | Pasó |  |
| CP-35 | HU-007 | PDEP-63 | Playwright | `test_cp35_nota_vacia_marca_el_criterio` | Pasó |  |
| CP-36 | HU-007 | PDEP-63 | Postman | `CP-36` | Pasó |  |
| CP-37 | HU-007 | PDEP-63 | Postman | `CP-37` | Pasó |  |
| CP-38 | HU-007 | PDEP-63 | Playwright | `test_cp38_nota_mayor_a_5_marca_el_criterio` | Pasó |  |
| CP-39 | HU-007 | PDEP-63 | Postman | `CP-39` | Pasó |  |
| CP-40 | HU-007 | PDEP-63 | Postman | `CP-40` | Pasó |  |
| CP-41 | HU-007 | PDEP-63 | Playwright | `test_cp41_guardar_borrador_sin_puntaje` | Pasó |  |
| CP-42 | HU-007 | PDEP-63 | Playwright | `test_cp42_cancelar_la_confirmacion_no_envia_nada` | Pasó |  |
| CP-43 | HU-007 | PDEP-63 | Playwright | `test_cp43_confirmar_muestra_puntaje_3_90` | Pasó |  |
| CP-44 | HU-007 | PDEP-63 | Playwright | `test_cp44_evaluacion_confirmada_queda_solo_lectura` | Pasó |  |
| CP-45 | HU-007 | PDEP-63 | Postman | `CP-45` | Pasó |  |
| CP-46 | HU-007 | PDEP-63 | Playwright | `test_cp46_confirmar_desde_pendiente_muestra_5_00` | Pasó |  |
| CP-47 | HU-007 | PDEP-63 | Playwright | `test_cp47_limites_de_la_escala_muestran_2_60` | Pasó |  |
| CP-48 | HU-007 | PDEP-63 | Playwright | `test_cp48_proyecto_no_asignado_muestra_recuadro_rojo` | Pasó |  |
| CP-49 | HU-007 | PDEP-63 | Postman | `CP-49` | Pasó |  |
| CP-50 | HU-007 | PDEP-63 | Playwright | `test_cp50_feria_sin_rubrica_no_muestra_el_formulario` | Pasó |  |
| CP-51 | HU-007 | PDEP-63 | Postman | `CP-51` | Pasó |  |
| CP-52 | HU-007 | PDEP-63 | Postman | `CP-52` | Pasó |  |
| CP-53 | HU-007 | PDEP-63 | Postman | `CP-53` | Pasó |  |
| CP-54 | HU-007 | PDEP-63 | Playwright | `test_cp54_estudiante_no_ve_calificar_proyecto` | Pasó |  |
| CP-55 | HU-007 | PDEP-63 | Postman | `CP-55` | Pasó |  |
| CP-56 | Todas | PDEP-61 | Playwright | `test_cp56_sin_sesion_registrar_usuario_lleva_a_ingresar` | Pasó |  |
| CP-57 | Todas | PDEP-62 | Playwright | `test_cp57_sin_sesion_inscribir_proyecto_lleva_a_ingresar` | Pasó |  |
| CP-58 | Todas | PDEP-63 | Playwright | `test_cp58_sin_sesion_calificar_proyecto_lleva_a_ingresar` | Pasó |  |
| CP-59 | Todas | PDEP-61 | Postman | `CP-59` | Pasó |  |
| CP-60 | Todas | PDEP-62 | Postman | `CP-60` | Pasó |  |
| CP-61 | Todas | PDEP-63 | Postman | `CP-61` | Pasó |  |

Los archivos de cada tramo están en esta misma carpeta: `newman/` (resultado JSON de
Newman) y `pytest/` (resultado JUnit de pytest).
