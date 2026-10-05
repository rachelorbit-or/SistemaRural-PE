import pytest
from sistemarural.cifrador import Cifrador
from sistemarural.errores import ErrorDeCifrado
from sistemarural.reportes import GeneradorReporte


def test_cifrar_y_descifrar_devuelve_el_texto_original():
    cifrador = Cifrador(Cifrador.generar_clave())
    token = cifrador.cifrar("Rosa Quispe")
    assert token != "Rosa Quispe"
    assert cifrador.descifrar(token) == "Rosa Quispe"


def test_otra_clave_no_puede_descifrar():
    token = Cifrador(Cifrador.generar_clave()).cifrar("dato")
    with pytest.raises(ErrorDeCifrado):
        Cifrador(Cifrador.generar_clave()).descifrar(token)


def test_la_huella_del_dni_es_estable_pero_no_legible():
    cifrador = Cifrador(Cifrador.generar_clave())
    assert cifrador.identificador_seguro("12345678") == cifrador.identificador_seguro("12345678")
    assert "12345678" not in cifrador.identificador_seguro("12345678")


def test_conteo_por_resolucion_sin_atenciones_es_vacio():
    assert GeneradorReporte.atenciones_por_resolucion([]) == {}