"""Grafos de flujo de HU-003, HU-005 y HU-007.

Una sola definición genera los diagramas de actividad (DOT), verifica
V(G) = E − N + 2 = decisiones + 1 y comprueba que cada camino listado
recorre aristas que existen.
"""
import json
import subprocess

FONT = "Liberation Sans"
GRUPO_CICLO = set()
HANDLER = ("manejar_error_dominio(e)",
           "jsonify({codigo, mensaje}),", "e.estado_http")


def hu003():
    n = {
        1: ("act", "UsuarioControlador.registrar_usuario()", ["datos = request.get_json(silent=True)", "servicio.registrar(datos)"]),
        2: ("dec", "usuario_validador", ["validar_datos_registro(datos)", "¿cuerpo, tipos y", "campos válidos?"]),
        3: ("err", "", ["raise DatoInvalidoError", "→ HTTP 400"]),
        4: ("act", "RegistroUsuarioServicio.registrar()", ["correo = normalizar_correo(datos['correo'])", "dominios = institucion_repo.listar_dominios()"]),
        5: ("dec", "", ["¿dominio_es_institucional(", "correo, dominios)?"]),
        6: ("err", "", ["raise CorreoNoInstitucionalError", "→ HTTP 422"]),
        7: ("dec", "", ["¿usuario_repo", ".existe_correo(correo)?"]),
        8: ("err", "", ["raise CorreoDuplicadoError", "→ HTTP 409"]),
        9: ("dec", "", ["¿programa_repo", ".existe(programa_id)?"]),
        10: ("err", "", ["raise ProgramaNoEncontradoError", "→ HTTP 404"]),
        11: ("act", "", ["faltantes = set(asignatura_ids)", "− asignatura_repo.ids_existentes(ids)"]),
        12: ("dec", "", ["¿faltantes vacío?"]),
        13: ("err", "", ["raise AsignaturaNoEncontradaError", "→ HTTP 404"]),
        14: ("act", "SqliteUsuarioRepositorio.guardar()", ["try: with transaccion(conexion):", "INSERT usuario;", "INSERT usuario_asignatura"]),
        15: ("dec", "", ["¿except", "ConflictoUnicidadError?", "(UNIQUE → ROLLBACK)"]),
        16: ("err", "", ["raise CorreoDuplicadoError", "→ HTTP 409"]),
        17: ("act", "UsuarioControlador", ["return Usuario → jsonify(usuario), 201"]),
        18: ("han", "create_app", list(HANDLER)),
        19: ("fin", "", ["Respuesta HTTP al cliente"]),
    }
    e = [(1, 2, ""), (2, 3, "no"), (2, 4, "sí"), (3, 18, ""), (4, 5, ""), (5, 6, "no"), (5, 7, "sí"),
         (6, 18, ""), (7, 8, "sí"), (7, 9, "no"), (8, 18, ""), (9, 10, "no"), (9, 11, "sí"), (10, 18, ""),
         (11, 12, ""), (12, 13, "no"), (12, 14, "sí"), (13, 18, ""), (14, 15, ""), (15, 16, "sí"),
         (15, 17, "no"), (16, 18, ""), (17, 19, ""), (18, 19, "")]
    caminos = [
        ("C1", [1, 2, 3, 18, 19], "Datos inválidos", "correo = None", "DatoInvalidoError, 400; no se consulta la BD"),
        ("C2", [1, 2, 4, 5, 6, 18, 19], "Dominio no institucional", "correo = \"ana@gmail.com\"", "CorreoNoInstitucionalError, 422"),
        ("C3", [1, 2, 4, 5, 7, 8, 18, 19], "Correo ya registrado", "existe_correo → True", "CorreoDuplicadoError, 409; guardar() no se llama"),
        ("C4", [1, 2, 4, 5, 7, 9, 10, 18, 19], "Programa inexistente", "programa_repo.existe → False", "ProgramaNoEncontradoError, 404"),
        ("C5", [1, 2, 4, 5, 7, 9, 11, 12, 13, 18, 19], "Asignatura inexistente", "asignatura_ids = [1, 99]", "AsignaturaNoEncontradaError, 404"),
        ("C6", [1, 2, 4, 5, 7, 9, 11, 12, 14, 15, 16, 18, 19], "Duplicado detectado por UNIQUE", "guardar() lanza ConflictoUnicidadError", "CorreoDuplicadoError, 409"),
        ("C7", [1, 2, 4, 5, 7, 9, 11, 12, 14, 15, 17, 19], "Registro exitoso", "\" Ana@PascualBravo.EDU.CO \"", "Usuario con correo en minúsculas, 201"),
    ]
    return n, e, caminos


def hu005():
    n = {
        1: ("act", "ProyectoControlador.inscribir_proyecto()", ["datos = request.get_json(silent=True)", "servicio.inscribir(datos)"]),
        2: ("dec", "proyecto_validador", ["validar_datos_inscripcion(", "datos): ¿tipos, campos", "y RN009 válidos?"]),
        3: ("err", "", ["raise DatoInvalidoError", "→ HTTP 400"]),
        4: ("dec", "InscripcionServicio.inscribir()", ["¿equipo_repo", ".existe(equipo_id)?"]),
        5: ("err", "", ["raise EquipoNoEncontradoError", "→ HTTP 404"]),
        6: ("act", "", ["feria = feria_repo.obtener(feria_id)"]),
        7: ("dec", "", ["¿feria is None?"]),
        8: ("err", "", ["raise FeriaNoEncontradaError", "→ HTTP 404"]),
        9: ("dec", "", ["¿feria.acepta_", "asignaturas(ids)?", "(ids ⊆ asignatura_ids)"]),
        10: ("err", "", ["raise AsignaturaNoParticipanteError", "→ HTTP 422"]),
        11: ("act", "", ["hoy = reloj.hoy()   # date, America/Bogota"]),
        12: ("dec", "", ["¿hoy < feria.fecha_inicio?"]),
        13: ("err", "", ["raise InscripcionNoAbiertaError", "→ HTTP 422"]),
        14: ("dec", "", ["¿hoy > feria.fecha_fin?"]),
        15: ("err", "", ["raise PlazoVencidoError", "→ HTTP 422"]),
        16: ("act", "", ["nombre_normalizado = normalizar_nombre(nombre)"]),
        17: ("dec", "", ["¿proyecto_repo", ".existe_en_feria(equipo_id,", "nombre_normalizado,", "feria.id)?"]),
        18: ("err", "", ["raise ProyectoDuplicadoError", "→ HTTP 409"]),
        19: ("act", "SqliteProyectoRepositorio.registrar()", ["try: with transaccion(conexion):", "INSERT proyecto;", "INSERT proyecto_asignatura"]),
        20: ("dec", "", ["¿except", "ConflictoUnicidadError?", "(UNIQUE → ROLLBACK)"]),
        21: ("err", "", ["raise ProyectoDuplicadoError", "→ HTTP 409"]),
        22: ("act", "ProyectoControlador", ["return Proyecto → jsonify(proyecto), 201"]),
        23: ("han", "create_app", list(HANDLER)),
        24: ("fin", "", ["Respuesta HTTP al cliente"]),
    }
    e = [(1, 2, ""), (2, 3, "no"), (2, 4, "sí"), (3, 23, ""), (4, 5, "no"), (4, 6, "sí"), (5, 23, ""),
         (6, 7, ""), (7, 8, "sí"), (7, 9, "no"), (8, 23, ""), (9, 10, "no"), (9, 11, "sí"), (10, 23, ""),
         (11, 12, ""), (12, 13, "sí"), (12, 14, "no"), (13, 23, ""), (14, 15, "sí"), (14, 16, "no"),
         (15, 23, ""), (16, 17, ""), (17, 18, "sí"), (17, 19, "no"), (18, 23, ""), (19, 20, ""),
         (20, 21, "sí"), (20, 22, "no"), (21, 23, ""), (22, 24, ""), (23, 24, "")]
    c = [1, 2, 4, 6, 7, 9, 11, 12, 14, 16, 17, 19, 20]
    caminos = [
        ("C1", [1, 2, 3, 23, 24], "Solicitud mal formada", "PIA con asignatura_ids = [1]", "DatoInvalidoError, 400"),
        ("C2", [1, 2, 4, 5, 23, 24], "Equipo inexistente", "equipo_repo.existe → False", "EquipoNoEncontradoError, 404"),
        ("C3", [1, 2, 4, 6, 7, 8, 23, 24], "Feria inexistente", "feria_repo.obtener → None", "FeriaNoEncontradaError, 404"),
        ("C4", [1, 2, 4, 6, 7, 9, 10, 23, 24], "Asignatura fuera de la feria", "asignatura_ids = [1, 9]", "AsignaturaNoParticipanteError, 422"),
        ("C5", c[:8] + [13, 23, 24], "Antes del inicio", "hoy = fecha_inicio − 1 día", "InscripcionNoAbiertaError, 422"),
        ("C6", c[:9] + [15, 23, 24], "Después del fin", "hoy = fecha_fin + 1 día", "PlazoVencidoError, 422"),
        ("C7", c[:11] + [18, 23, 24], "Proyecto ya inscrito", "existe_en_feria → True", "ProyectoDuplicadoError, 409"),
        ("C8", c + [21, 23, 24], "Duplicado detectado por UNIQUE", "registrar() lanza ConflictoUnicidadError", "ProyectoDuplicadoError, 409"),
        ("C9", c + [22, 24], "Inscripción exitosa", "hoy = fecha_inicio y hoy = fecha_fin", "Proyecto inscrito, 201"),
    ]
    return n, e, caminos


def hu007():
    n = {
        1: ("act", "EvaluacionControlador.calificar_proyecto()", ["datos = request.get_json(silent=True)", "servicio.calificar(proyecto_id, datos)"]),
        2: ("dec", "calificacion_validador", ["validar_solicitud_", "calificacion(datos):", "¿evaluador_id, notas", "y confirmar válidos?"]),
        3: ("err", "", ["raise DatoInvalidoError", "→ HTTP 400"]),
        4: ("act", "CalificacionServicio.calificar()", ["evaluacion = evaluacion_repo.obtener_asignada(", "evaluador_id, proyecto_id)"]),
        5: ("dec", "", ["¿evaluacion is None?"]),
        6: ("err", "", ["raise EvaluadorNoAsignadoError", "→ HTTP 403"]),
        7: ("dec", "", ["¿evaluacion.estado", "is CONFIRMADA?"]),
        8: ("err", "", ["raise EvaluacionYaConfirmadaError", "→ HTTP 409"]),
        9: ("act", "", ["rubrica = rubrica_repo.obtener_por_feria(feria_id)"]),
        10: ("dec", "", ["¿rubrica is None?"]),
        11: ("err", "", ["raise RubricaNoEncontradaError", "→ HTTP 422"]),
        12: ("dec", "validar_rubrica(rubrica)", ["¿not rubrica.criterios?"]),
        13: ("err", "", ["raise RubricaSinCriteriosError", "→ HTTP 422"]),
        14: ("dec", "", ["¿rubrica", ".pesos_validos()?", "(peso > 0 y", "|Σ peso − 1| ≤ 1e-6)"]),
        15: ("err", "", ["raise PesosInvalidosError", "→ HTTP 422"]),
        16: ("dec", "validar_notas_completas()", ["¿set(notas) ==", "rubrica.ids_criterios()?"]),
        17: ("err", "", ["raise NotasIncompletasError", "→ HTTP 422"]),
        18: ("act", "Rubrica.calcular_puntaje(notas)", ["puntaje = 0.0"]),
        19: ("dec", "", ["for criterio in", "rubrica.criterios:", "¿quedan criterios?"]),
        20: ("dec", "Rubrica.validar_nota()", ["nota = notas[criterio.id]", "¿int|float, no bool", "y math.isfinite?"]),
        21: ("err", "", ["raise TipoNotaInvalidoError", "→ HTTP 422"]),
        22: ("dec", "", ["¿nota_minima ≤ nota", "≤ nota_maxima?"]),
        23: ("err", "", ["raise NotaFueraDeRangoError", "→ HTTP 422"]),
        24: ("act", "", ["puntaje += nota × criterio.peso"]),
        25: ("act", "", ["return round(puntaje, 2)"]),
        26: ("dec", "Evaluacion.con_calificacion()", ["¿confirmar?"]),
        27: ("act", "", ["estado = BORRADOR", "fecha_confirmacion = None"]),
        28: ("act", "", ["estado = CONFIRMADA", "fecha_confirmacion = reloj.ahora()"]),
        29: ("act", "SqliteEvaluacionRepositorio", ["with transaccion(conexion):", "UPDATE evaluacion;", "DELETE + INSERT calificacion_criterio"]),
        30: ("act", "EvaluacionControlador", ["return → jsonify(estado, puntaje_visible), 200"]),
        31: ("han", "create_app", list(HANDLER)),
        32: ("fin", "", ["Respuesta HTTP al cliente"]),
    }
    e = [(1, 2, ""), (2, 3, "no"), (2, 4, "sí"), (3, 31, ""), (4, 5, ""), (5, 6, "sí"), (5, 7, "no"),
         (6, 31, ""), (7, 8, "sí"), (7, 9, "no"), (8, 31, ""), (9, 10, ""), (10, 11, "sí"), (10, 12, "no"),
         (11, 31, ""), (12, 13, "sí"), (12, 14, "no"), (13, 31, ""), (14, 15, "no"), (14, 16, "sí"),
         (15, 31, ""), (16, 17, "no"), (16, 18, "sí"), (17, 31, ""), (18, 19, ""), (19, 20, "sí"),
         (19, 25, "no"), (20, 21, "no"), (20, 22, "sí"), (21, 31, ""), (22, 23, "no"), (22, 24, "sí"),
         (23, 31, ""), (24, 19, ""), (25, 26, ""), (26, 27, "no"), (26, 28, "sí"), (27, 29, ""),
         (28, 29, ""), (29, 30, ""), (30, 32, ""), (31, 32, "")]
    b = [1, 2, 4, 5, 7, 9, 10, 12, 14, 16, 18, 19, 20, 22]
    vuelta = [24, 19]
    caminos = [
        ("C1", [1, 2, 3, 31, 32], "Solicitud mal formada", "confirmar = \"true\" (texto)", "DatoInvalidoError, 400"),
        ("C2", [1, 2, 4, 5, 6, 31, 32], "Evaluador sin asignación", "obtener_asignada → None", "EvaluadorNoAsignadoError, 403"),
        ("C3", [1, 2, 4, 5, 7, 8, 31, 32], "Evaluación ya confirmada", "estado = CONFIRMADA", "EvaluacionYaConfirmadaError, 409"),
        ("C4", [1, 2, 4, 5, 7, 9, 10, 11, 31, 32], "Feria sin rúbrica", "obtener_por_feria → None", "RubricaNoEncontradaError, 422"),
        ("C5", b[:8] + [13, 31, 32], "Rúbrica sin criterios", "criterios = ()", "RubricaSinCriteriosError, 422"),
        ("C6", b[:9] + [15, 31, 32], "Pesos inválidos", "pesos 0.5 + 0.3 = 0.8", "PesosInvalidosError, 422"),
        ("C7", b[:10] + [17, 31, 32], "Notas incompletas", "notas de 2 de 3 criterios", "NotasIncompletasError, 422"),
        ("C8", b[:13] + [21, 31, 32], "Nota de tipo inválido", "nota = \"4.5\" (str)", "TipoNotaInvalidoError, 422"),
        ("C9", b + [23, 31, 32], "Nota fuera de rango", "nota = 5.01", "NotaFueraDeRangoError, 422"),
        ("C10", b + vuelta + [25, 26, 27, 29, 30, 32], "Un criterio, sin confirmar", "1 criterio (peso 1.0), nota 4.5, confirmar = false", "BORRADOR, puntaje_visible = None, 200"),
        ("C11", b + vuelta + [25, 26, 28, 29, 30, 32], "Un criterio, confirmado", "1 criterio, nota 4.5, confirmar = true", "CONFIRMADA, 4.5, 200"),
        ("C12", b + vuelta + [20, 22] + vuelta + [20, 22] + vuelta + [25, 26, 28, 29, 30, 32], "Varios criterios, confirmado", "notas 4.0/3.0/5.0, pesos 0.5/0.3/0.2", "CONFIRMADA, 3.9, 200"),
    ]
    return n, e, caminos


def verificar(nombre, n, e, caminos):
    aristas = {(a, b) for a, b, _ in e}
    decisiones = sum(1 for t in n.values() if t[0] == "dec")
    vg = len(e) - len(n) + 2
    assert vg == decisiones + 1, (nombre, vg, decisiones)
    assert len(caminos) == vg, (nombre, len(caminos), vg)
    for cid, seq, *_ in caminos:
        for a, b in zip(seq, seq[1:]):
            assert (a, b) in aristas, (nombre, cid, a, b)
    # independencia lineal de los caminos (rango del vector de aristas)
    idx = {ar: i for i, ar in enumerate(sorted(aristas))}
    filas = []
    for _, seq, *_ in caminos:
        v = [0] * len(idx)
        for a, b in zip(seq, seq[1:]):
            v[idx[(a, b)]] += 1
        filas.append(v)
    rango = rango_matriz(filas)
    assert rango == vg, (nombre, "rango", rango)
    return {"N": len(n), "E": len(e), "decisiones": decisiones, "VG": vg}


def rango_matriz(m):
    from fractions import Fraction
    m = [[Fraction(x) for x in fila] for fila in m]
    rango, col = 0, 0
    filas, cols = len(m), len(m[0])
    while rango < filas and col < cols:
        piv = next((r for r in range(rango, filas) if m[r][col] != 0), None)
        if piv is None:
            col += 1
            continue
        m[rango], m[piv] = m[piv], m[rango]
        for r in range(filas):
            if r != rango and m[r][col] != 0:
                f = m[r][col] / m[rango][col]
                m[r] = [x - f * y for x, y in zip(m[r], m[rango])]
        rango += 1
        col += 1
    return rango


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def etiqueta(num, comp, lineas, tipo):
    filas = []
    if comp:
        filas.append(f'<FONT POINT-SIZE="8.5"><I>{esc(comp)}</I></FONT>')
    for i, l in enumerate(lineas):
        filas.append(esc(l))
    cuerpo = "<BR/>".join(filas)
    return f'<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="1"><TR><TD VALIGN="TOP"><B>{num}</B>  </TD><TD ALIGN="LEFT">{cuerpo}</TD></TR></TABLE>>'


def dot(nombre, n, e, incluir=None, conector_salida=None, conector_entrada=None):
    incluir = set(incluir or n)
    l = ['digraph G {',
         f'graph [rankdir=TB, splines=ortho, fontname="{FONT}", nodesep=0.5, ranksep=0.3, pad=0.2, dpi=200, newrank=true];',
         f'node [fontname="{FONT}", fontsize=10.5, penwidth=1.1, color=black];',
         f'edge [fontname="{FONT}", fontsize=9.5, penwidth=1.0, arrowsize=0.65, color=black];',
         'ini [shape=circle, style=filled, fillcolor=black, label="", width=0.22, fixedsize=true];',
         'finx [shape=doublecircle, style=filled, fillcolor=black, label="", width=0.14, fixedsize=true];']
    for k, (t, comp, lin) in n.items():
        if k not in incluir:
            continue
        lab = etiqueta(k, comp, lin, t)
        grupo = ', group=eje' if t != "err" else ''
        if k in GRUPO_CICLO:
            grupo = ', group=salida'
        if t == "dec":
            l.append(f'n{k} [shape=diamond, label={lab}, margin="0.02,0.02"{grupo}];')
        elif t == "err":
            l.append(f'n{k} [shape=box, style="rounded,filled", fillcolor="#E7E7E7", label={lab}];')
        elif t == "han":
            l.append(f'n{k} [shape=box, style="rounded,bold", label={lab}];')
        elif t == "fin":
            l.append(f'n{k} [shape=box, style="rounded", label={lab}, group=eje];')
        else:
            l.append(f'n{k} [shape=box, style="rounded", label={lab}{grupo}];')
    primero = min(incluir)
    if conector_entrada:
        l.append(f'ini [shape=circle, style="", fillcolor=white, label=<<B>{conector_entrada}</B>>, width=0.38, fixedsize=true];')
    l.append(f'ini -> n{primero};')
    for a, b, lab in e:
        if a in incluir and b in incluir:
            attrs = []
            if lab:
                attrs.append(f'xlabel=" [{lab}] "')
            if n[a][0] == "err" and n[b][0] == "han":
                attrs.append('constraint=false')
            if n[a][0] == "dec" and n[b][0] == "err":
                attrs.append('tailport=e, headport=w')
            if (a, b) == (24, 19):
                l.append('n19:w -> n24:w [dir=back];')
                continue
            l.append(f'n{a} -> n{b} [{", ".join(attrs)}];')
        elif a in incluir and conector_salida and b not in incluir:
            l.append(f'conA [shape=circle, label=<<B>{conector_salida}</B>>, width=0.38, fixedsize=true];')
            l.append(f'n{a} -> conA [xlabel=" [{lab}] "];' if lab else f'n{a} -> conA;')
    fin_num = max(k for k, v in n.items() if v[0] == "fin")
    if fin_num in incluir:
        l.append(f'n{fin_num} -> finx;')
    han = [k for k, v in n.items() if v[0] == "han" and k in incluir]
    exito = [a for a, b, _ in e if b == fin_num and n[a][0] == "act" and a in incluir]
    if han and exito:
        l.append(f'{{rank=same; n{exito[0]}; n{han[0]};}}')
    elif han and conector_salida:
        l.append(f'{{rank=same; conA; n{han[0]};}}')
    # errores a la derecha de su decisión
    for a, b, lab in e:
        if a in incluir and b in incluir and n[a][0] == "dec" and n[b][0] == "err":
            l.append(f'{{rank=same; n{a}; n{b};}}')
    l.append("}")
    with open(nombre + ".dot", "w") as f:
        f.write("\n".join(l))
    subprocess.run(["dot", "-Tpng", nombre + ".dot", "-o", nombre + ".png"], check=True)


def exportar():
    pruebas = {
        "HU-003": ["test_c1_datos_invalidos", "test_c2_correo_no_institucional", "test_c3_correo_duplicado",
                   "test_c4_programa_inexistente", "test_c5_asignatura_inexistente",
                   "test_c6_conflicto_de_unicidad_al_guardar", "test_c7_registro_exitoso_normaliza_correo_y_rol"],
        "HU-005": ["test_c1_datos_invalidos", "test_c2_equipo_inexistente", "test_c3_feria_inexistente",
                   "test_c4_asignatura_no_participa", "test_c5_un_dia_antes_del_inicio",
                   "test_c6_un_dia_despues_del_fin", "test_c7_proyecto_duplicado",
                   "test_c8_conflicto_de_unicidad_al_registrar", "test_c9_inscripcion_exitosa"],
        "HU-007": ["test_c1_solicitud_mal_formada", "test_c2_evaluador_no_asignado", "test_c3_evaluacion_ya_confirmada",
                   "test_c4_feria_sin_rubrica", "test_c5_rubrica_sin_criterios", "test_c6_pesos_que_no_suman_uno",
                   "test_c7_falta_la_nota_de_un_criterio", "test_c8_nota_de_tipo_texto", "test_c9_nota_fuera_de_rango",
                   "test_c10_un_criterio_sin_confirmar_queda_en_borrador", "test_c11_un_criterio_confirmado",
                   "test_c12_varios_criterios_confirmado"],
    }
    salida = {}
    for nombre, f in (("HU-003", hu003), ("HU-005", hu005), ("HU-007", hu007)):
        n, e, c = f()
        m = verificar(nombre, n, e, c)
        salida[nombre] = {"metricas": m, "caminos": [
            {"id": cid, "nodos": "→".join(map(str, seq)), "descripcion": d, "entrada": ent, "resultado": res,
             "prueba": pruebas[nombre][i]} for i, (cid, seq, d, ent, res) in enumerate(c)]}
    with open("caminos.json", "w") as fh:
        json.dump(salida, fh, ensure_ascii=False, indent=1)



if __name__ == "__main__":
    exportar()
    res = {}
    for nombre, f in (("HU-003", hu003), ("HU-005", hu005), ("HU-007", hu007)):
        n, e, c = f()
        res[nombre] = verificar(nombre, n, e, c)
    print(json.dumps(res, indent=1))
    n, e, _ = hu003(); dot("Act_HU003", n, e)
    n, e, _ = hu005(); dot("Act_HU005", n, e)
    n, e, _ = hu007()
    dot("Act_HU007_a", n, e, incluir=list(range(1, 18)) + [31, 32], conector_salida="A")
    GRUPO_CICLO.update({25, 26, 29, 30, 32})
    dot("Act_HU007_b", n, e, incluir=list(range(18, 33)), conector_entrada="A")
