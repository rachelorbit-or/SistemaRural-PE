"""Historia clínica y atenciones (RQ-02, RQ-04, RQ-08)."""
from datetime import date, datetime

from sistemarural.cifrador import Cifrador
from sistemarural.errores import AccesoDenegado, ErrorDeValidacion
from sistemarural.inventario import Receta

RESOLUCIONES = ("resuelto", "referido")


class Atencion:
    """Una atención médica. El diagnóstico se guarda cifrado, nunca en texto plano."""

    def __init__(self, fecha: datetime, motivo: str, diagnostico_cifrado: str, cifrador: Cifrador,
                 resolucion: str = "resuelto"):
        if not isinstance(fecha, datetime):
            raise ErrorDeValidacion("La fecha de la atención no es válida.")
        if not isinstance(motivo, str) or not motivo.strip():
            raise ErrorDeValidacion("El motivo de la atención no puede estar vacío.")
        if resolucion not in RESOLUCIONES:
            raise ErrorDeValidacion(f"La resolución debe ser una de: {', '.join(RESOLUCIONES)}.")
        self.__fecha = fecha
        self.__resolucion = resolucion
        self.__motivo = motivo.strip()
        self.__diagnostico_cifrado = diagnostico_cifrado
        self.__cifrador = cifrador

    @classmethod
    def registrar(cls, motivo: str, diagnostico: str, cifrador: Cifrador,
                  fecha: datetime = None, resolucion: str = "resuelto") -> "Atencion":
        """Crea una atención cifrando el diagnóstico antes de guardarlo."""
        if not isinstance(diagnostico, str) or not diagnostico.strip():
            raise ErrorDeValidacion("El diagnóstico no puede estar vacío.")
        return cls(fecha or datetime.now(), motivo, cifrador.cifrar(diagnostico.strip()),
                   cifrador, resolucion)

    @property
    def fecha(self) -> datetime:
        return self.__fecha

    @property
    def motivo(self) -> str:
        return self.__motivo

    @property
    def resolucion(self) -> str:
        return self.__resolucion

    def generar_receta(self, paciente, items) -> Receta:
        """Genera la receta de esta atención (RQ-05)."""
        return Receta.generar(paciente, items, self.__fecha.date())

    @property
    def diagnostico_cifrado(self) -> str:
        return self.__diagnostico_cifrado

    def ver_diagnostico(self, usuario) -> str:
        """Devuelve el diagnóstico solo si el cargo del usuario lo permite (RQ-04)."""
        permiso = getattr(usuario, "puede_ver_diagnostico", None)
        if permiso is None or not permiso():
            raise AccesoDenegado("Este usuario no tiene permiso para ver diagnósticos.")
        return self.__cifrador.descifrar(self.__diagnostico_cifrado)


class HistoriaClinica:
    """Conjunto de atenciones de un paciente (composición: nace con el paciente)."""

    def __init__(self, numero: str, fecha_apertura: date = None):
        if not isinstance(numero, str) or not numero.strip():
            raise ErrorDeValidacion("El número de historia clínica no puede estar vacío.")
        self.__numero = numero.strip()
        self.__fecha_apertura = fecha_apertura or date.today()
        self.__atenciones = []

    @property
    def numero(self) -> str:
        return self.__numero

    @property
    def fecha_apertura(self) -> date:
        return self.__fecha_apertura

    def agregar_atencion(self, atencion: Atencion) -> None:
        if not isinstance(atencion, Atencion):
            raise ErrorDeValidacion("Solo se pueden agregar atenciones a la historia clínica.")
        self.__atenciones.append(atencion)

    def listar_atenciones(self) -> tuple:
        """Devuelve una copia de solo lectura, para que nadie altere la historia por fuera."""
        return tuple(self.__atenciones)
