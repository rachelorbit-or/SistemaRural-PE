"""Cifrado de datos personales para no guardarlos en texto plano (RQ-08, RD-02)."""
import hashlib
import hmac
import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from sistemarural.errores import ErrorDeCifrado


class Cifrador:
    """Cifra y descifra textos con una clave secreta (cifrado Fernet)."""

    def __init__(self, clave: bytes):
        self.__clave = clave  # La clave es privada y nunca se muestra.
        self.__fernet = Fernet(clave)

    @staticmethod
    def generar_clave() -> bytes:
        return Fernet.generate_key()

    @classmethod
    def desde_archivo(cls, ruta) -> "Cifrador":
        """Lee la clave de un archivo; si no existe, crea una nueva."""
        ruta = Path(ruta)
        if not ruta.exists():
            ruta.parent.mkdir(parents=True, exist_ok=True)
            ruta.write_bytes(cls.generar_clave())
            try:
                os.chmod(ruta, 0o600)  # Solo el dueño puede leer la clave.
            except OSError:
                pass
        return cls(ruta.read_bytes())

    def cifrar(self, texto: str) -> str:
        return self.__fernet.encrypt(texto.encode("utf-8")).decode("ascii")

    def descifrar(self, token: str) -> str:
        try:
            return self.__fernet.decrypt(token.encode("ascii")).decode("utf-8")
        except InvalidToken as error:
            raise ErrorDeCifrado("No se pudo descifrar el dato con la clave actual.") from error

    def identificador_seguro(self, valor: str) -> str:
        """Huella irreversible de un valor (por ejemplo, el DNI).

        Se usa la clave secreta (HMAC) porque un DNI tiene solo 8 dígitos y
        un hash simple se podría adivinar probando todas las combinaciones.
        """
        return hmac.new(self.__clave, valor.encode("utf-8"), hashlib.sha256).hexdigest()
