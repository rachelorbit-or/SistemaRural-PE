"""Fachada del sistema: junta las clases y controla quién puede hacer cada acción."""
from datetime import date, datetime

from sistemarural.almacen_datos import AlmacenDatos
from sistemarural.citas import Cita, Servicio
from sistemarural.cifrador import Cifrador
from sistemarural.errores import (AccesoDenegado, ErrorDeValidacion, PacienteNoEncontrado)
from sistemarural.historia_clinica import Atencion
from sistemarural.inventario import Inventario, Medicamento, Receta
from sistemarural.personas import PersonalFactory
from sistemarural.reportes import GeneradorReporte
from sistemarural.validadores import validar_dni

SERVICIOS_BASE = ("Medicina", "Odontología", "Psicología", "Control del niño", "Obstetricia")
DNI_PERSONAL_DEMO = ("10000001", "10000002", "10000003") # usuarios ficticios de prueba 

class SistemaChontapaccha:
    """Punto único de acceso para la interfaz: valida roles, guarda y carga los datos."""

    def __init__(self, almacen: AlmacenDatos, cifrador: Cifrador):
        self.__almacen = almacen
        self.__cifrador = cifrador
        self.__personal = {}
        self.__pacientes = {}
        self.__servicios = {}
        self.__citas = []
        self.__inventario = Inventario()
        self.__contador_historias = 0

    # --- Consultas ---
    @property
    def inventario(self) -> Inventario:
        return self.__inventario

    def listar_personal(self) -> list:
        return list(self.__personal.values())

    def personal_por_cargo(self, codigo_cargo: str) -> list:
        return list(filter(lambda p: p.codigo_cargo == codigo_cargo, self.__personal.values()))

    def listar_servicios(self) -> list:
        return list(self.__servicios.values())

    def obtener_servicio(self, nombre: str) -> Servicio:
        servicio = self.__servicios.get(nombre)
        if servicio is None:
            raise ErrorDeValidacion(f"No existe el servicio {nombre!r}.")
        return servicio

    def obtener_personal(self, dni: str):
        persona = self.__personal.get(dni)
        if persona is None:
            raise ErrorDeValidacion(f"No existe personal con DNI {dni}.")
        return persona

    def obtener_paciente(self, dni: str):
        if not validar_dni(dni):
            raise ErrorDeValidacion("El DNI debe tener exactamente 8 dígitos numéricos.")
        paciente = self.__pacientes.get(dni)
        if paciente is None:
            raise PacienteNoEncontrado(f"No existe un paciente con DNI {dni}.")
        return paciente

    def buscar_pacientes(self, texto: str) -> list:
        """Busca por DNI o por parte del nombre (RQ-06 del EP: filtros simples)."""
        texto = texto.strip().lower()
        if not texto:
            return list(self.__pacientes.values())
        return list(filter(lambda p: texto in p.dni or texto in p.nombres.lower(),
                           self.__pacientes.values()))

    def listar_citas(self, nombre_servicio: str, fecha: date = None) -> list:
        return self.obtener_servicio(nombre_servicio).listar_citas(fecha)

    def todas_las_atenciones(self) -> list:
        return [atencion for paciente in self.__pacientes.values() if paciente.historia
                for atencion in paciente.historia.listar_atenciones()]

    # --- Acciones controladas por rol ---
    @staticmethod
    def _exigir(usuario, capacidad: str, accion: str) -> None:
        if usuario is None or not hasattr(usuario, capacidad):
            raise AccesoDenegado(f"Su cargo no permite {accion}.")

    def registrar_personal(self, cargo: str, dni: str, nombres: str, fecha_nacimiento: date,
                           direccion: str, nombre_servicio: str = None):
        if dni in self.__personal:
            raise ErrorDeValidacion(f"Ya existe personal con DNI {dni}.")
        persona = PersonalFactory.crear_personal(cargo, dni, nombres, fecha_nacimiento, direccion)
        if nombre_servicio:
            self.obtener_servicio(nombre_servicio).agregar_personal(persona)
        self.__personal[dni] = persona
        self.guardar()
        return persona

    def registrar_paciente(self, usuario, dni: str, nombres: str, fecha_nacimiento: date,
                           direccion: str):
        self._exigir(usuario, "registrar_paciente", "registrar pacientes")
        paciente = usuario.registrar_paciente(dni, nombres, fecha_nacimiento, direccion)
        self.__almacen.guardar_paciente(paciente)  # Lanza error si el DNI ya existe.
        self.__pacientes[paciente.dni] = paciente
        return paciente

    def abrir_historia(self, usuario, dni: str):
        self._exigir(usuario, "registrar_paciente", "abrir historias clínicas")
        paciente = self.obtener_paciente(dni)
        numero = f"HC-{self.__contador_historias + 1:05d}"
        historia = paciente.abrir_historia(numero)
        self.__contador_historias += 1
        self.guardar()
        return historia

    def registrar_atencion(self, usuario, dni: str, motivo: str, diagnostico: str,
                           resolucion: str = "resuelto"):
        self._exigir(usuario, "registrar_atencion", "registrar atenciones")
        paciente = self.obtener_paciente(dni)
        if paciente.historia is None:
            raise ErrorDeValidacion("El paciente aún no tiene historia clínica.")
        atencion = usuario.registrar_atencion(paciente.historia, motivo, diagnostico,
                                              self.__cifrador, resolucion)
        self.guardar()
        return atencion

    def ver_diagnosticos(self, usuario, dni: str) -> list:
        """Lista (fecha, motivo, diagnóstico); solo para cargos con permiso (RQ-04)."""
        permiso = getattr(usuario, "puede_ver_diagnostico", None)
        if permiso is None or not permiso():
            raise AccesoDenegado("Su cargo no permite ver diagnósticos.")
        paciente = self.obtener_paciente(dni)
        if paciente.historia is None:
            return []
        return [(a.fecha, a.motivo, a.ver_diagnostico(usuario))
                for a in paciente.historia.listar_atenciones()]

    def preparar_historia(self, usuario, dni: str) -> dict:
        self._exigir(usuario, "apoyar_atencion", "preparar historias")
        paciente = self.obtener_paciente(dni)
        if paciente.historia is None:
            raise ErrorDeValidacion("El paciente aún no tiene historia clínica.")
        return usuario.apoyar_atencion(paciente.historia)

    def programar_cita(self, usuario, dni: str, nombre_servicio: str, dni_personal: str,
                       fecha: date, turno: str, hoy: date = None) -> Cita:
        self._exigir(usuario, "programar_cita", "programar citas")
        cita = usuario.programar_cita(self.obtener_paciente(dni),
                                      self.obtener_servicio(nombre_servicio),
                                      self.obtener_personal(dni_personal), fecha, turno, hoy)
        self.__citas.append(cita)
        self.guardar()
        return cita

    def cancelar_cita(self, usuario, cita: Cita) -> None:
        self._exigir(usuario, "programar_cita", "cancelar citas")
        cita.cancelar()
        self.guardar()

    def asignar_horario(self, usuario, nombre_servicio: str, dia: str, turno: str,
                        dni_personal: str):
        self._exigir(usuario, "programar_cita", "asignar horarios")
        horario = self.obtener_servicio(nombre_servicio).asignar_horario(
            dia, turno, self.obtener_personal(dni_personal))
        self.guardar()
        return horario
    def quitar_de_horario(self, usuario, nombre_servicio: str, dia: str, turno: str,
                          dni_personal: str) -> None:
        self._exigir(usuario, "programar_cita", "modificar horarios")
        self.obtener_servicio(nombre_servicio).quitar_de_horario(dia, turno, dni_personal)
        self.guardar()

    def dispensar_receta(self, usuario, dni: str, items: list) -> Receta:
        if usuario is None or not hasattr(usuario, "puede_ver_diagnostico"):
            raise AccesoDenegado("Solo el personal del establecimiento puede dispensar recetas.")
        receta = Receta.generar(self.obtener_paciente(dni), items)
        receta.dispensar(self.__inventario)
        self.guardar()
        return receta

    def reporte(self, desde: date, hasta: date) -> dict:
        """Reporte para la DIRESA más el estado del inventario."""
        resultado = GeneradorReporte.reporte_diresa(self.todas_las_atenciones(), desde, hasta)
        resultado["a_reponer"] = GeneradorReporte.nombres_a_reponer(self.__inventario)
        resultado["unidades_en_stock"] = GeneradorReporte.unidades_en_stock(self.__inventario)
        return resultado

    # --- Guardado y carga ---
    def guardar(self) -> None:
        a = self.__almacen
        a.guardar_seccion("config", [{"umbral": self.__inventario.umbral,
                                      "contador_historias": self.__contador_historias}])
        a.guardar_seccion("inventario", [{"codigo": m.codigo, "nombre": m.nombre, "stock": m.stock}
                                         for m in self.__inventario.listar()])
        a.guardar_seccion("personal", [
            {"cargo": p.codigo_cargo, "dni": p.dni, "nombres": p.nombres,
             "fecha_nacimiento": p.fecha_nacimiento.isoformat(), "direccion": p.direccion}
            for p in self.__personal.values()],
            ("dni", "nombres", "fecha_nacimiento", "direccion"))
        a.guardar_seccion("historias", [
            {"dni": p.dni, "numero": p.historia.numero,
             "fecha_apertura": p.historia.fecha_apertura.isoformat(),
             "atenciones": [{"fecha": at.fecha.isoformat(), "motivo": at.motivo,
                             "diagnostico": at.diagnostico_cifrado, "resolucion": at.resolucion}
                            for at in p.historia.listar_atenciones()]}
            for p in self.__pacientes.values() if p.historia],
            ("dni", "numero", "fecha_apertura", "atenciones"))
        a.guardar_seccion("servicios", [
            {"nombre": s.nombre, "personal": [p.dni for p in s.listar_personal()],
             "horarios": [{"dia": h.dia, "turno": h.turno,
                           "personal": [p.dni for p in h.listar_personal()]}
                          for h in s.listar_horarios()]}
            for s in self.__servicios.values()],
            ("personal", "horarios"))
        a.guardar_seccion("citas", [
            {"paciente": c.paciente.dni, "servicio": c.servicio.nombre, "personal": c.personal.dni,
             "fecha": c.fecha.isoformat(), "turno": c.turno, "estado": c.estado}
            for c in self.__citas],
            ("paciente", "personal", "fecha"))

    def cargar(self) -> None:
        """Reconstruye todo el sistema a partir del archivo."""
        a = self.__almacen
        config = a.cargar_seccion("config")
        if config:
            self.__inventario = Inventario(config[0]["umbral"])
            self.__contador_historias = config[0]["contador_historias"]
        for r in a.cargar_seccion("inventario"):
            self.__inventario.agregar_medicamento(Medicamento(r["codigo"], r["nombre"], r["stock"]))
        for r in a.cargar_seccion("personal"):
            self.__personal[r["dni"]] = PersonalFactory.crear_personal(
                r["cargo"], r["dni"], r["nombres"], date.fromisoformat(r["fecha_nacimiento"]),
                r["direccion"])
        self.__pacientes = {p.dni: p for p in a.listar_pacientes()}
        for r in a.cargar_seccion("historias"):
            historia = self.__pacientes[r["dni"]].abrir_historia(
                r["numero"], date.fromisoformat(r["fecha_apertura"]))
            for at in r["atenciones"]:
                historia.agregar_atencion(Atencion(
                    datetime.fromisoformat(at["fecha"]), at["motivo"], at["diagnostico"],
                    self.__cifrador, at["resolucion"]))
        for r in a.cargar_seccion("servicios"):
            servicio = Servicio(r["nombre"])
            for dni in r["personal"]:
                servicio.agregar_personal(self.__personal[dni])
            for h in r["horarios"]:
                for dni in h["personal"]:
                    servicio.asignar_horario(h["dia"], h["turno"], self.__personal[dni])
            self.__servicios[servicio.nombre] = servicio
        # Las canceladas se cargan primero para no chocar con la regla de duplicados.
        citas = sorted(a.cargar_seccion("citas"), key=lambda r: r["estado"] != "cancelada")
        for r in citas:
            cita = Cita(self.__pacientes[r["paciente"]], self.__servicios[r["servicio"]],
                        self.__personal[r["personal"]], date.fromisoformat(r["fecha"]), r["turno"])
            cita.servicio.registrar_cita(cita)
            if r["estado"] == "cancelada":
                cita.cancelar()
            self.__citas.append(cita)

    def sembrar_datos_demo(self) -> None:
        """Si el sistema está vacío, crea servicios, personal y medicamentos FICTICIOS de prueba."""
        for nombre in SERVICIOS_BASE:
            if nombre not in self.__servicios:
                self.__servicios[nombre] = Servicio(nombre)
        if not self.__personal:
            nacimiento = date(1990, 1, 1)
            self.registrar_personal("medico", "10000001", "Médico Demo", nacimiento,
                                    "Dirección de prueba", "Medicina")
            self.registrar_personal("tecnico_enfermeria", "10000002", "Técnico Demo", nacimiento,
                                    "Dirección de prueba", "Medicina")
            self.registrar_personal("admisionista", "10000003", "Admisionista Demo", nacimiento,
                                    "Dirección de prueba", "Medicina")
        if not self.__inventario.listar():
            for codigo, nombre, stock in [("M01", "Paracetamol 500 mg", 50),
                                          ("M02", "Amoxicilina 500 mg", 8),
                                          ("M03", "Ibuprofeno 400 mg", 30)]:
                self.__inventario.agregar_medicamento(Medicamento(codigo, nombre, stock))
        demo =[p for p in self.__personal.values () if p.dni in DNI_PERSONAL_DEMO]
        for servicio in self .__servicios.values():
            if not servicio.listar_personal():
                for persona in demo:
                    servicio.agregar_personal(persona)
        self.guardar()
