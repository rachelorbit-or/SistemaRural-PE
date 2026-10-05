"""Almacén local de datos con patrón Singleton (RQ-01, RQ-08, RD-02, RD-03)."""
import json
from datetime import date
from pathlib import Path

from sistemarural.cifrador import Cifrador
from sistemarural.errores import (ErrorDeAlmacenamiento, ErrorDeValidacion,
                                  PacienteDuplicado, PacienteNoEncontrado)
from sistemarural.personas import Paciente
from sistemarural.validadores import validar_dni


class AlmacenDatos:
    """Guarda los datos en un archivo local; los datos sensibles van cifrados.

    Patrón Singleton: solo existe una instancia, así todos los módulos
    usan el mismo archivo y pasan por el mismo cifrado.
    """

    __instancia = None

    def __init__(self, ruta_archivo, cifrador: Cifrador):
        self.__ruta = Path(ruta_archivo)
        self.__cifrador = cifrador
        self.__registros = self.__leer_archivo()

    @classmethod
    def obtener_instancia(cls, ruta_archivo=None, cifrador: Cifrador = None) -> "AlmacenDatos":
        """Devuelve la única instancia; la crea la primera vez que se llama."""
        if cls.__instancia is None:
            if ruta_archivo is None or cifrador is None:
                raise ErrorDeValidacion(
                    "La primera vez se debe indicar la ruta del archivo y el cifrador.")
            cls.__instancia = cls(ruta_archivo, cifrador)
        return cls.__instancia

    @classmethod
    def reiniciar(cls) -> None:
        """Descarta la instancia actual (se usa en las pruebas)."""
        cls.__instancia = None

    # --- Operaciones con pacientes ---
    def guardar_paciente(self, paciente: Paciente) -> None:
        clave = self.__cifrador.identificador_seguro(paciente.dni)
        if clave in self.__registros["pacientes"]:
            raise PacienteDuplicado(f"Ya existe un paciente con DNI {paciente.dni}.")
        cifrar = self.__cifrador.cifrar
        self.__registros["pacientes"][clave] = {
            "dni": cifrar(paciente.dni),
            "nombres": cifrar(paciente.nombres),
            "fecha_nacimiento": cifrar(paciente.fecha_nacimiento.isoformat()),
            "direccion": cifrar(paciente.direccion),
        }
        self.__escribir_archivo()

    def existe_paciente(self, dni: str) -> bool:
        if not validar_dni(dni):
            return False
        return self.__cifrador.identificador_seguro(dni) in self.__registros["pacientes"]

    def cargar_paciente(self, dni: str) -> Paciente:
        if not validar_dni(dni):
            raise ErrorDeValidacion("El DNI debe tener exactamente 8 dígitos numéricos.")
        registro = self.__registros["pacientes"].get(self.__cifrador.identificador_seguro(dni))
        if registro is None:
            raise PacienteNoEncontrado(f"No existe un paciente con DNI {dni}.")
        return self.__construir_paciente(registro)

    def listar_pacientes(self) -> list:
        return [self.__construir_paciente(r) for r in self.__registros["pacientes"].values()]

    # --- Secciones generales (historias, citas, personal, inventario, etc.) ---
    def guardar_seccion(self, nombre: str, registros: list, campos_cifrados: tuple = ()) -> None:
        """Guarda una lista de registros; los campos indicados se cifran antes de escribirse."""
        cifrados = list(campos_cifrados)
        protegidos = [
            {campo: (self.__cifrador.cifrar(json.dumps(valor, ensure_ascii=False))
                     if campo in cifrados else valor)
             for campo, valor in registro.items()}
            for registro in registros
        ]
        self.__registros["secciones"][nombre] = {"cifrados": cifrados, "registros": protegidos}
        self.__escribir_archivo()

    def cargar_seccion(self, nombre: str) -> list:
        """Devuelve los registros de una sección con sus campos ya descifrados."""
        seccion = self.__registros["secciones"].get(nombre)
        if seccion is None:
            return []
        cifrados = seccion["cifrados"]
        return [
            {campo: (json.loads(self.__cifrador.descifrar(valor)) if campo in cifrados else valor)
             for campo, valor in registro.items()}
            for registro in seccion["registros"]
        ]

    # --- Métodos internos ---
    def __construir_paciente(self, registro: dict) -> Paciente:
        descifrar = self.__cifrador.descifrar
        return Paciente(
            descifrar(registro["dni"]),
            descifrar(registro["nombres"]),
            date.fromisoformat(descifrar(registro["fecha_nacimiento"])),
            descifrar(registro["direccion"]),
        )

    def __leer_archivo(self) -> dict:
        if not self.__ruta.exists():
            return {"pacientes": {}, "secciones": {}}
        try:
            datos = json.loads(self.__ruta.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as error:
            raise ErrorDeAlmacenamiento("No se pudo leer el archivo de datos.") from error
        datos.setdefault("pacientes", {})
        datos.setdefault("secciones", {})
        return datos

    def __escribir_archivo(self) -> None:
        self.__ruta.parent.mkdir(parents=True, exist_ok=True)
        temporal = self.__ruta.with_suffix(".tmp")
        temporal.write_text(json.dumps(self.__registros, ensure_ascii=False), encoding="utf-8")
        temporal.replace(self.__ruta)  # Reemplazo completo para no dejar datos a medias.
