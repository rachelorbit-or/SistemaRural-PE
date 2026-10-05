"""Reportes para la DIRESA y control de stock con programación funcional (RQ-05, RQ-06)."""
from datetime import date
from functools import reduce

from sistemarural.errores import ErrorDeValidacion


class GeneradorReporte:
    """Funciones que transforman colecciones sin modificarlas (map, filter y reduce)."""

    @staticmethod
    def filtrar_por_fecha(atenciones, desde: date, hasta: date) -> list:
        """Atenciones entre dos fechas, ambas incluidas (función filter)."""
        if desde > hasta:
            raise ErrorDeValidacion("La fecha inicial no puede ser posterior a la final.")
        return list(filter(lambda a: desde <= a.fecha.date() <= hasta, atenciones))

    @staticmethod
    def atenciones_por_resolucion(atenciones) -> dict:
        """Cuenta cuántas atenciones fueron resueltas y cuántas referidas (función reduce)."""
        return reduce(
            lambda conteo, a: {**conteo, a.resolucion: conteo.get(a.resolucion, 0) + 1},
            atenciones,
            {},
        )

    @staticmethod
    def totalizar(atenciones) -> int:
        """Total de atenciones (función reduce)."""
        return reduce(lambda total, _: total + 1, atenciones, 0)

    @staticmethod
    def nombres_a_reponer(inventario) -> list:
        """Nombres de los medicamentos con stock bajo (función map)."""
        return list(map(lambda m: m.nombre, inventario.stock_bajo()))

    @staticmethod
    def unidades_en_stock(inventario) -> int:
        """Suma de unidades disponibles en todo el inventario (función reduce)."""
        return reduce(lambda total, m: total + m.stock, inventario.listar(), 0)

    @classmethod
    def reporte_diresa(cls, atenciones, desde: date, hasta: date) -> dict:
        """Reporte del periodo: total de atenciones y cuántas fueron resueltas o referidas."""
        del_periodo = cls.filtrar_por_fecha(atenciones, desde, hasta)
        return {
            "desde": desde,
            "hasta": hasta,
            "total": cls.totalizar(del_periodo),
            "por_resolucion": cls.atenciones_por_resolucion(del_periodo),
        }
