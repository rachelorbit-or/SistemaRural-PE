"""Servicios y citas médicas (RQ-03)."""
from datetime import date

from sistemarural.errores import ErrorDeValidacion
from sistemarural.horarios import TURNOS, Horario

ESTADO_PROGRAMADA = "programada"
ESTADO_CANCELADA = "cancelada"


class Cita:
    """Cita de un paciente con un miembro del personal, en un servicio, fecha y turno."""

    def __init__(self, paciente, servicio, personal, fecha: date, turno: str):
        self.__paciente = paciente
        self.__servicio = servicio
        self.__personal = personal
        self.__fecha = fecha
        self.__turno = turno
        self.__estado = ESTADO_PROGRAMADA

    @classmethod
    def programar(cls, paciente, servicio, personal, fecha: date, turno: str,
                  hoy: date = None) -> "Cita":
        """Valida los datos, crea la cita y la registra en el servicio."""
        hoy = hoy or date.today()
        if not isinstance(fecha, date) or fecha < hoy:
            raise ErrorDeValidacion("La fecha de la cita no puede ser anterior a hoy.")
        if turno not in TURNOS:
            raise ErrorDeValidacion(f"El turno debe ser uno de: {', '.join(TURNOS)}.")
        cita = cls(paciente, servicio, personal, fecha, turno)
        servicio.registrar_cita(cita)
        return cita

    @property
    def paciente(self):
        return self.__paciente

    @property
    def servicio(self):
        return self.__servicio

    @property
    def personal(self):
        return self.__personal

    @property
    def fecha(self) -> date:
        return self.__fecha

    @property
    def turno(self) -> str:
        return self.__turno

    @property
    def estado(self) -> str:
        return self.__estado

    def cancelar(self) -> None:
        if self.__estado == ESTADO_CANCELADA:
            raise ErrorDeValidacion("La cita ya está cancelada.")
        self.__estado = ESTADO_CANCELADA


class Servicio:
    """Servicio del establecimiento (medicina, odontología, etc.) con su personal y sus citas."""

    def __init__(self, nombre: str):
        if not isinstance(nombre, str) or not nombre.strip():
            raise ErrorDeValidacion("El nombre del servicio no puede estar vacío.")
        self.__nombre = nombre.strip()
        self.__personal = []
        self.__citas = []
        self.__horarios = {}  # (día, turno) -> Horario

    @property
    def nombre(self) -> str:
        return self.__nombre

    def agregar_personal(self, personal) -> None:
        if any(p.dni == personal.dni for p in self.__personal):
            raise ErrorDeValidacion("Esa persona ya pertenece al servicio.")
        self.__personal.append(personal)

    def listar_personal(self) -> tuple:
        return tuple(self.__personal)

    def asignar_horario(self, dia: str, turno: str, personal) -> Horario:
        """Asigna una persona del servicio a un día y turno (composición con Horario)."""
        if all(p.dni != personal.dni for p in self.__personal):
            raise ErrorDeValidacion("El personal indicado no pertenece a este servicio.")
        if (dia, turno) not in self.__horarios:
            self.__horarios[(dia, turno)] = Horario(dia, turno)
        horario = self.__horarios[(dia, turno)]
        horario.asignar(personal)
        return horario

    def quitar_de_horario(self, dia: str, turno: str, dni: str) -> None:
        horario = self.__horarios.get((dia, turno))
        if horario is None:
            raise ErrorDeValidacion("Ese día y turno no tiene horario asignado.")
        horario.quitar(dni)
        if not horario.listar_personal():
            del self.__horarios[(dia, turno)]

    def listar_horarios(self) -> tuple:
        return tuple(self.__horarios.values())

    def registrar_cita(self, cita: Cita) -> None:
        if all(p.dni != cita.personal.dni for p in self.__personal):
            raise ErrorDeValidacion("El personal indicado no pertenece a este servicio.")
        repetida = any(
            c.estado == ESTADO_PROGRAMADA and c.paciente.dni == cita.paciente.dni
            and c.fecha == cita.fecha and c.turno == cita.turno
            for c in self.__citas
        )
        if repetida:
            raise ErrorDeValidacion("El paciente ya tiene una cita en esa fecha y turno.")
        self.__citas.append(cita)

    def listar_citas(self, fecha: date = None) -> list:
        """Citas programadas del servicio; se pueden filtrar por fecha (función filter)."""
        activas = filter(lambda c: c.estado == ESTADO_PROGRAMADA, self.__citas)
        if fecha is not None:
            activas = filter(lambda c: c.fecha == fecha, activas)
        return list(activas)
