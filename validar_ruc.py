"""
Prueba de viabilidad del componente tecnico mas incierto: validacion de RUC.
SistemaRural-PE - UAIN1288P
"""
import re

PATRON_RUC = re.compile(r"^(10|20)\d{9}$")


def validar_ruc(ruc: str) -> bool:
    """Devuelve True si el RUC cumple el patron: 11 digitos, prefijo 10 o 20."""
    return bool(PATRON_RUC.match(ruc))


casos_prueba = [
    ("10456789123", True),   # persona natural, 11 digitos, valido
    ("20601234567", True),   # persona juridica, 11 digitos, valido
    ("10111222333", True),
    ("20999888777", True),
    ("10000000001", True),
    ("20123456789", True),
    ("30456789123", False),  # prefijo invalido (no es 10 ni 20)
    ("15456789123", False),  # prefijo invalido
    ("1045678912", False),   # 10 digitos (falta uno)
    ("104567891234", False), # 12 digitos (uno de mas)
    ("1045A789123", False),  # contiene una letra
    ("", False),             # cadena vacia
    ("20-601234567", False), # contiene un guion
    ("10456789123 ", False), # espacio extra al final
    ("00456789123", False),  # prefijo invalido
]

if __name__ == "__main__":
    correctos = 0
    print(f"{'RUC':<16} {'Esperado':<10} {'Obtenido':<10} {'Resultado'}")
    print("-" * 50)
    for ruc, esperado in casos_prueba:
        obtenido = validar_ruc(ruc)
        ok = obtenido == esperado
        correctos += ok
        print(f"{ruc!r:<16} {str(esperado):<10} {str(obtenido):<10} {'OK' if ok else 'FALLO'}")
    print("-" * 50)
    print(f"Resultado final: {correctos}/{len(casos_prueba)} casos correctos")
