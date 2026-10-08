"""Personas del sistema: pacientes y personal del establecimiento (RQ-01, RQ-04)."""
from abc import ABC, abstractmethod
from datetime import date

from sistemarural.citas import Cita
from sistemarural.errores import ErrorDeValidacion
from sistemarural.historia_clinica import Atencion, HistoriaClinica
from sistemarural.validadores import validar_dni


class Persona(ABC):
    """Clase base abstracta con los datos comunes de toda persona."""

    def __init__(self, dni: str, nombres: str, fecha_nacimiento: date, direccion: str):
        if not validar_dni(dni):
            raise ErrorDeValidacion("El DNI debe tener exactamente 8 dígitos numéricos.")
        self.__dni = dni  # El DNI no cambia una vez creada la persona.
        self.nombres = nombres
        self.fecha_nacimiento = fecha_nacimiento
        self.direccion = direccion

    # --- Getters y setters (los atributos reales son privados) ---
    @property
    def dni(self) -> str:
        return self.__dni

    @property
    def nombres(self) -> str:
        return self.__nombres

    @nombres.setter
    def nombres(self, valor: str) -> None:
        if not isinstance(valor, str) or not valor.strip():
            raise ErrorDeValidacion("Los nombres no pueden estar vacíos.")
        self.__nombres = valor.strip()

    @property
    def fecha_nacimiento(self) -> date:
        return self.__fecha_nacimiento

    @fecha_nacimiento.setter
    def fecha_nacimiento(self, valor: date) -> None:
        if not isinstance(valor, date) or valor > date.today():
            raise ErrorDeValidacion("La fecha de nacimiento no es válida.")
        self.__fecha_nacimiento = valor

    @property
    def direccion(self) -> str:
        return self.__direccion

    @direccion.setter
    def direccion(self, valor: str) -> None:
        if not isinstance(valor, str) or not valor.strip():
            raise ErrorDeValidacion("La dirección no puede estar vacía.")
        self.__direccion = valor.strip()

    # --- Comportamiento ---
    def edad(self, hoy: date = None) -> int:
        """Calcula la edad en años a partir de la fecha de nacimiento."""
        hoy = hoy or date.today()
        nac = self.fecha_nacimiento
        cumplio = (hoy.month, hoy.day) >= (nac.month, nac.day)
        return hoy.year - nac.year - (0 if cumplio else 1)

    @abstractmethod
    def tipo(self) -> str:
        """Nombre del tipo de persona (lo define cada subclase)."""


class Paciente(Persona):
    """Persona atendida en el establecimiento."""

    def __init__(self, dni: str, nombres: str, fecha_nacimiento: date, direccion: str):
        super().__init__(dni, nombres, fecha_nacimiento, direccion)
        self.__historia = None  # Se crea con abrir_historia().

    @property
    def historia(self):
        return self.__historia

    def abrir_historia(self, numero: str, fecha_apertura: date = None) -> HistoriaClinica:
        """Crea la historia clínica del paciente (solo puede tener una)."""
        if self.__historia is not None:
            raise ErrorDeValidacion("El paciente ya tiene una historia clínica abierta.")
        self.__historia = HistoriaClinica(numero, fecha_apertura)
        return self.__historia

    def tipo(self) -> str:
        return "Paciente"


class Personal(Persona):
    """Trabajador del establecimiento. Cada cargo define sus permisos."""

    CODIGO = None

    @property
    @abstractmethod
    def cargo(self) -> str:
        """Nombre del cargo."""

    @property
    def codigo_cargo(self) -> str:
        """Código corto del cargo, usado por la fábrica y al guardar los datos."""
        return self.CODIGO

    @abstractmethod
    def puede_ver_diagnostico(self) -> bool:
        """Indica si el cargo tiene permiso para ver diagnósticos (RQ-04)."""

    def tipo(self) -> str:
        return self.cargo


class Medico(Personal):
    CODIGO = "medico"

    @property
    def cargo(self) -> str:
        return "Médico"

    def puede_ver_diagnostico(self) -> bool:
        return True

    def registrar_atencion(self, historia: HistoriaClinica, motivo: str,
                           diagnostico: str, cifrador,
                           resolucion: str = "resuelto") -> Atencion:
        """Registra una atención en la historia, con el diagnóstico cifrado."""
        atencion = Atencion.registrar(motivo, diagnostico, cifrador, resolucion=resolucion)
        historia.agregar_atencion(atencion)
        return atencion


class TecnicoEnfermeria(Personal):
    CODIGO = "tecnico_enfermeria"

    @property
    def cargo(self) -> str:
        return "Técnico de enfermería"

    def puede_ver_diagnostico(self) -> bool:
        return False

    def apoyar_atencion(self, historia: HistoriaClinica) -> dict:
        """Ubica la historia y entrega un resumen, sin mostrar ningún diagnóstico."""
        atenciones = historia.listar_atenciones()
        return {
            "numero": historia.numero,
            "total_atenciones": len(atenciones),
            "ultima_atencion": atenciones[-1].fecha.date() if atenciones else None,
        }


class Admisionista(Personal):
    CODIGO = "admisionista"

    @property
    def cargo(self) -> str:
        return "Admisionista"

    def puede_ver_diagnostico(self) -> bool:
        return False

    def registrar_paciente(self, dni: str, nombres: str, fecha_nacimiento: date,
                           direccion: str) -> Paciente:
        """Crea un paciente validando sus datos (el guardado lo hace el sistema)."""
        return Paciente(dni, nombres, fecha_nacimiento, direccion)

    def programar_cita(self, paciente: Paciente, servicio, personal,
                       fecha: date, turno: str, hoy: date = None) -> Cita:
        """Programa una cita de un paciente en un servicio."""
        return Cita.programar(paciente, servicio, personal, fecha, turno, hoy)


class PersonalFactory:
    """Patrón Factory Method: crea el tipo de personal correcto según el cargo.

    Así el permiso de ver diagnósticos se asigna en un solo lugar.
    """

    _TIPOS = {
        "medico": Medico,
        "tecnico_enfermeria": TecnicoEnfermeria,
        "admisionista": Admisionista,
    }

    @classmethod
    def crear_personal(cls, cargo: str, dni: str, nombres: str,
                       fecha_nacimiento: date, direccion: str) -> Personal:
        clase = cls._TIPOS.get(str(cargo).strip().lower())
        if clase is None:
            raise ErrorDeValidacion(f"Cargo no reconocido: {cargo!r}.")
        return clase(dni, nombres, fecha_nacimiento, direccion)
