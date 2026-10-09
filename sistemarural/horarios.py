"""Horarios del personal por día y turno (RQ-07)."""
from sistemarural.errores import ErrorDeValidacion

DIAS = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")
TURNOS = ("mañana", "tarde")


class Horario:
    """Personal asignado a un día y turno (reemplaza la pizarra del establecimiento)."""

    def __init__(self, dia: str, turno: str):
        if dia not in DIAS:
            raise ErrorDeValidacion(f"El día debe ser uno de: {', '.join(DIAS)}.")
        if turno not in TURNOS:
            raise ErrorDeValidacion(f"El turno debe ser uno de: {', '.join(TURNOS)}.")
        self.__dia = dia
        self.__turno = turno
        self.__personal = []

    @property
    def dia(self) -> str:
        return self.__dia

    @property
    def turno(self) -> str:
        return self.__turno

    def asignar(self, personal) -> None:
        if any(p.dni == personal.dni for p in self.__personal):
            raise ErrorDeValidacion("Esa persona ya está asignada a ese día y turno.")
        self.__personal.append(personal)

    def listar_personal(self) -> tuple:
        return tuple(self.__personal)

    def quitar(self, dni: str) -> None:
        for p in self.__personal:
            if p.dni == dni:
                self.__personal.remove(p)
                return
        raise ErrorDeValidacion("Esa persona no está asignada a ese día y turno.")
