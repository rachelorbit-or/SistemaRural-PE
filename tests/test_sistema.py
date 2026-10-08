"""Pruebas del sistema completo: roles, flujos y guardado cifrado (CE-01 a CE-06)."""
from datetime import date, timedelta

import pytest

from sistemarural.almacen_datos import AlmacenDatos
from sistemarural.cifrador import Cifrador
from sistemarural.errores import (AccesoDenegado, ErrorDeValidacion, PacienteDuplicado,
                                  StockInsuficiente)
from sistemarural.sistema import SistemaChontapaccha

NACIMIENTO = date(1985, 3, 14)
MANANA = date.today() + timedelta(days=1)


def crear_sistema(tmp_path):
    """Crea un sistema nuevo con datos de prueba en una carpeta temporal."""
    AlmacenDatos.reiniciar()
    cifrador = Cifrador.desde_archivo(tmp_path / "clave.key")
    almacen = AlmacenDatos.obtener_instancia(tmp_path / "datos.json", cifrador)
    sistema = SistemaChontapaccha(almacen, cifrador)
    sistema.sembrar_datos_demo()
    return sistema


def roles(sistema):
    return (sistema.personal_por_cargo("admisionista")[0],
            sistema.personal_por_cargo("medico")[0],
            sistema.personal_por_cargo("tecnico_enfermeria")[0])


def paciente_con_historia(sistema, admisionista, dni="12345678"):
    sistema.registrar_paciente(admisionista, dni, "Rosa Quispe", NACIMIENTO, "Jr. Los Pinos 123")
    sistema.abrir_historia(admisionista, dni)


def test_flujo_completo_y_control_de_diagnosticos(tmp_path):
    sistema = crear_sistema(tmp_path)
    admisionista, medico, tecnico = roles(sistema)
    paciente_con_historia(sistema, admisionista)
    sistema.registrar_atencion(medico, "12345678", "Dolor abdominal", "Gastritis leve")
    assert sistema.ver_diagnosticos(medico, "12345678")[0][2] == "Gastritis leve"
    for otro in (tecnico, admisionista):
        with pytest.raises(AccesoDenegado):
            sistema.ver_diagnosticos(otro, "12345678")


def test_solo_el_admisionista_registra_pacientes_y_solo_el_medico_atiende(tmp_path):
    sistema = crear_sistema(tmp_path)
    admisionista, medico, tecnico = roles(sistema)
    with pytest.raises(AccesoDenegado):
        sistema.registrar_paciente(medico, "12345678", "Rosa Quispe", NACIMIENTO, "Jr. Lima 1")
    paciente_con_historia(sistema, admisionista)
    with pytest.raises(AccesoDenegado):
        sistema.registrar_atencion(tecnico, "12345678", "Control", "Sano")


def test_no_permite_pacientes_duplicados_en_el_sistema(tmp_path):
    sistema = crear_sistema(tmp_path)
    admisionista, _, _ = roles(sistema)
    paciente_con_historia(sistema, admisionista)
    with pytest.raises(PacienteDuplicado):
        sistema.registrar_paciente(admisionista, "12345678", "Otra Persona", NACIMIENTO, "Jr. Lima 2")
    assert len(sistema.buscar_pacientes("")) == 1


def test_no_se_atiende_sin_historia_clinica(tmp_path):
    sistema = crear_sistema(tmp_path)
    admisionista, medico, _ = roles(sistema)
    sistema.registrar_paciente(admisionista, "12345678", "Rosa Quispe", NACIMIENTO, "Jr. Lima 1")
    with pytest.raises(ErrorDeValidacion):
        sistema.registrar_atencion(medico, "12345678", "Control", "Sano")


def test_buscar_pacientes_por_dni_y_por_nombre(tmp_path):
    sistema = crear_sistema(tmp_path)
    admisionista, _, _ = roles(sistema)
    sistema.registrar_paciente(admisionista, "12345678", "Rosa Quispe", NACIMIENTO, "Jr. Lima 1")
    sistema.registrar_paciente(admisionista, "87654321", "Juan Rojas", NACIMIENTO, "Jr. Lima 2")
    assert [p.dni for p in sistema.buscar_pacientes("rosa")] == ["12345678"]
    assert [p.dni for p in sistema.buscar_pacientes("8765")] == ["87654321"]
    assert len(sistema.buscar_pacientes("")) == 2


def test_tecnico_prepara_la_historia_sin_ver_diagnosticos(tmp_path):
    sistema = crear_sistema(tmp_path)
    admisionista, medico, tecnico = roles(sistema)
    paciente_con_historia(sistema, admisionista)
    sistema.registrar_atencion(medico, "12345678", "Dolor abdominal", "Gastritis leve")
    resumen = sistema.preparar_historia(tecnico, "12345678")
    assert resumen["total_atenciones"] == 1
    assert "Gastritis" not in str(resumen)


def test_citas_se_programan_y_cancelan_segun_el_rol(tmp_path):
    sistema = crear_sistema(tmp_path)
    admisionista, medico, tecnico = roles(sistema)
    paciente_con_historia(sistema, admisionista)
    with pytest.raises(AccesoDenegado):
        sistema.programar_cita(tecnico, "12345678", "Medicina", medico.dni, MANANA, "mañana")
    cita = sistema.programar_cita(admisionista, "12345678", "Medicina", medico.dni, MANANA, "mañana")
    assert sistema.listar_citas("Medicina") == [cita]
    sistema.cancelar_cita(admisionista, cita)
    assert sistema.listar_citas("Medicina") == []


def test_dispensar_receta_descuenta_y_respeta_el_stock(tmp_path):
    sistema = crear_sistema(tmp_path)
    admisionista, medico, _ = roles(sistema)
    paciente_con_historia(sistema, admisionista)
    sistema.dispensar_receta(medico, "12345678", [("M01", 10)])
    assert sistema.inventario.obtener("M01").stock == 40
    with pytest.raises(StockInsuficiente):
        sistema.dispensar_receta(medico, "12345678", [("M02", 99)])
    assert sistema.inventario.obtener("M02").stock == 8


def test_reporte_diresa_y_estado_del_inventario(tmp_path):
    sistema = crear_sistema(tmp_path)
    admisionista, medico, _ = roles(sistema)
    paciente_con_historia(sistema, admisionista)
    sistema.registrar_atencion(medico, "12345678", "Consulta", "Dx uno", "resuelto")
    sistema.registrar_atencion(medico, "12345678", "Consulta", "Dx dos", "referido")
    hoy = date.today()
    reporte = sistema.reporte(hoy, hoy)
    assert reporte["total"] == 2
    assert reporte["por_resolucion"] == {"resuelto": 1, "referido": 1}
    assert reporte["a_reponer"] == ["Amoxicilina 500 mg"]


def test_todo_se_recupera_al_reiniciar_el_sistema(tmp_path):
    sistema = crear_sistema(tmp_path)
    admisionista, medico, _ = roles(sistema)
    paciente_con_historia(sistema, admisionista)
    sistema.registrar_atencion(medico, "12345678", "Dolor abdominal", "Gastritis leve", "referido")
    sistema.programar_cita(admisionista, "12345678", "Medicina", medico.dni, MANANA, "tarde")
    sistema.asignar_horario(admisionista, "Medicina", "lunes", "mañana", medico.dni)
    sistema.dispensar_receta(medico, "12345678", [("M01", 5)])

    AlmacenDatos.reiniciar()  # Se simula cerrar y volver a abrir el programa.
    cifrador = Cifrador.desde_archivo(tmp_path / "clave.key")
    almacen = AlmacenDatos.obtener_instancia(tmp_path / "datos.json", cifrador)
    nuevo = SistemaChontapaccha(almacen, cifrador)
    nuevo.cargar()

    medico_nuevo = nuevo.personal_por_cargo("medico")[0]
    assert nuevo.obtener_paciente("12345678").nombres == "Rosa Quispe"
    assert nuevo.ver_diagnosticos(medico_nuevo, "12345678")[0][2] == "Gastritis leve"
    assert nuevo.todas_las_atenciones()[0].resolucion == "referido"
    assert len(nuevo.listar_citas("Medicina")) == 1
    assert len(nuevo.obtener_servicio("Medicina").listar_horarios()) == 1
    assert nuevo.inventario.obtener("M01").stock == 45


def test_la_numeracion_de_historias_continua_tras_reiniciar(tmp_path):
    sistema = crear_sistema(tmp_path)
    admisionista, _, _ = roles(sistema)
    paciente_con_historia(sistema, admisionista, "12345678")
    AlmacenDatos.reiniciar()
    cifrador = Cifrador.desde_archivo(tmp_path / "clave.key")
    almacen = AlmacenDatos.obtener_instancia(tmp_path / "datos.json", cifrador)
    nuevo = SistemaChontapaccha(almacen, cifrador)
    nuevo.cargar()
    admisionista_nuevo = nuevo.personal_por_cargo("admisionista")[0]
    nuevo.registrar_paciente(admisionista_nuevo, "87654321", "Juan Rojas", NACIMIENTO, "Jr. Cusco 5")
    historia = nuevo.abrir_historia(admisionista_nuevo, "87654321")
    assert historia.numero == "HC-00002"


def test_el_archivo_de_datos_no_contiene_informacion_sensible_en_texto_plano(tmp_path):
    sistema = crear_sistema(tmp_path)
    admisionista, medico, _ = roles(sistema)
    paciente_con_historia(sistema, admisionista)
    sistema.registrar_atencion(medico, "12345678", "Dolor abdominal", "Gastritis leve")
    sistema.programar_cita(admisionista, "12345678", "Medicina", medico.dni, MANANA, "mañana")
    contenido = (tmp_path / "datos.json").read_text(encoding="utf-8")
    for dato in ["12345678", "Rosa Quispe", "Dolor abdominal", "Gastritis", "Jr. Los Pinos",
                 "10000001", "Médico Demo", MANANA.isoformat()]:
        assert dato not in contenido
