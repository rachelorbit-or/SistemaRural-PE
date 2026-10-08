"""Inventario de medicamentos y recetas (RQ-05)."""
from datetime import date

from sistemarural.errores import ErrorDeValidacion, StockInsuficiente

ESTADO_PENDIENTE = "pendiente"
ESTADO_DISPENSADA = "dispensada"


def _validar_cantidad(cantidad) -> None:
    """La cantidad debe ser un número entero positivo."""
    if isinstance(cantidad, bool) or not isinstance(cantidad, int) or cantidad <= 0:
        raise ErrorDeValidacion("La cantidad debe ser un número entero mayor que cero.")


class Medicamento:
    """Medicamento con su código, nombre y unidades disponibles."""

    def __init__(self, codigo: str, nombre: str, stock: int):
        if not isinstance(codigo, str) or not codigo.strip():
            raise ErrorDeValidacion("El código del medicamento no puede estar vacío.")
        if not isinstance(nombre, str) or not nombre.strip():
            raise ErrorDeValidacion("El nombre del medicamento no puede estar vacío.")
        if isinstance(stock, bool) or not isinstance(stock, int) or stock < 0:
            raise ErrorDeValidacion("El stock debe ser un número entero, cero o mayor.")
        self.__codigo = codigo.strip()
        self.__nombre = nombre.strip()
        self.__stock = stock

    @property
    def codigo(self) -> str:
        return self.__codigo

    @property
    def nombre(self) -> str:
        return self.__nombre

    @property
    def stock(self) -> int:
        return self.__stock

    def hay_stock(self, cantidad: int = 1) -> bool:
        return self.__stock >= cantidad

    def reponer(self, cantidad: int) -> None:
        _validar_cantidad(cantidad)
        self.__stock += cantidad

    def descontar(self, cantidad: int) -> None:
        _validar_cantidad(cantidad)
        if cantidad > self.__stock:
            raise StockInsuficiente(
                f"{self.__nombre}: se piden {cantidad} y solo hay {self.__stock}.")
        self.__stock -= cantidad


class Inventario:
    """Conjunto de medicamentos con alerta de stock bajo (agregación)."""

    def __init__(self, umbral: int = 10):
        if isinstance(umbral, bool) or not isinstance(umbral, int) or umbral < 0:
            raise ErrorDeValidacion("El umbral debe ser un número entero, cero o mayor.")
        self.__umbral = umbral
        self.__medicamentos = {}

    @property
    def umbral(self) -> int:
        return self.__umbral

    def agregar_medicamento(self, medicamento: Medicamento) -> None:
        if medicamento.codigo in self.__medicamentos:
            raise ErrorDeValidacion(f"Ya existe el medicamento con código {medicamento.codigo}.")
        self.__medicamentos[medicamento.codigo] = medicamento

    def obtener(self, codigo: str) -> Medicamento:
        medicamento = self.__medicamentos.get(codigo)
        if medicamento is None:
            raise ErrorDeValidacion(f"No existe el medicamento con código {codigo}.")
        return medicamento

    def registrar_entrada(self, codigo: str, cantidad: int) -> None:
        self.obtener(codigo).reponer(cantidad)

    def registrar_salida(self, codigo: str, cantidad: int) -> None:
        self.obtener(codigo).descontar(cantidad)

    def listar(self) -> tuple:
        return tuple(self.__medicamentos.values())

    def stock_bajo(self) -> list:
        """Medicamentos cuyo stock llegó al umbral o por debajo (función filter)."""
        return list(filter(lambda m: m.stock <= self.__umbral, self.__medicamentos.values()))


class Receta:
    """Receta de un paciente; al dispensarla descuenta el stock del inventario."""

    def __init__(self, paciente, items: tuple, fecha: date):
        self.__paciente = paciente
        self.__items = items
        self.__fecha = fecha
        self.__estado = ESTADO_PENDIENTE

    @classmethod
    def generar(cls, paciente, items, fecha: date = None) -> "Receta":
        """Crea la receta a partir de pares (código, cantidad); junta los repetidos."""
        if not items:
            raise ErrorDeValidacion("La receta debe tener al menos un medicamento.")
        totales = {}
        for codigo, cantidad in items:
            _validar_cantidad(cantidad)
            totales[codigo] = totales.get(codigo, 0) + cantidad
        return cls(paciente, tuple(totales.items()), fecha or date.today())

    @property
    def paciente(self):
        return self.__paciente

    @property
    def fecha(self) -> date:
        return self.__fecha

    @property
    def estado(self) -> str:
        return self.__estado

    @property
    def items(self) -> tuple:
        return self.__items

    def dispensar(self, inventario: Inventario) -> None:
        """Descuenta todo o nada: si falta stock de algo, no se descuenta nada."""
        if self.__estado == ESTADO_DISPENSADA:
            raise ErrorDeValidacion("La receta ya fue dispensada.")
        faltantes = [codigo for codigo, cantidad in self.__items
                     if not inventario.obtener(codigo).hay_stock(cantidad)]
        if faltantes:
            raise StockInsuficiente(f"Stock insuficiente de: {', '.join(faltantes)}.")
        for codigo, cantidad in self.__items:
            inventario.registrar_salida(codigo, cantidad)
        self.__estado = ESTADO_DISPENSADA
