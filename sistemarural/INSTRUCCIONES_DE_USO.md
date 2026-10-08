# SistemaRural-PE: cómo ejecutarlo

Sistema local para el Puesto de Salud Chontapaccha (datos de prueba ficticios).

## Requisitos
- Python 3.10 o superior (en Windows, el instalador de python.org ya incluye tkinter).
- En Linux, si falta tkinter: `sudo apt install python3-tk`.

## Instalación y ejecución
```
pip install -r requirements.txt
python main.py
```
La primera vez se crea la carpeta `datos/` con la clave de cifrado y el archivo de datos
(no se suben a GitHub; están en `.gitignore`). Se cargan un médico, un técnico de enfermería y un
admisionista **ficticios**, y tres medicamentos de prueba.

## Pruebas automatizadas
```
pytest
```

## Qué puede hacer cada cargo
| Acción | Admisionista | Médico | Técnico de enfermería |
|---|---|---|---|
| Registrar pacientes y abrir historias | Sí | No | No |
| Programar y cancelar citas, asignar horarios | Sí | No | No |
| Registrar atenciones y ver diagnósticos | No | Sí | No |
| Preparar la historia (sin ver diagnósticos) | No | No | Sí |
| Dispensar recetas, ver inventario y reporte | Sí | Sí | Sí |
