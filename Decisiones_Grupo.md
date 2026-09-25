# Bitácora de decisiones — SistemaRural-PE

## Ciclo 1: Pivote de establecimiento

**24/09/2026:** [FECHA]

Ante la falta de respuesta a la solicitud de visita a Chontapaccha
(Oficio DA/SIC-00377-2026), el equipo evaluó como alternativa el
Hospital II-E Simón Bolívar de Cajamarca, por su amplia información
pública disponible.

Tras un análisis comparativo, se determinó que su perfil (hospital de
mayor complejidad, con quirófano y telesalud) no correspondía al caso
de referencia del desafío (Puesto de Salud, categoría I-1, sin sistema
alguno). El equipo decidió retornar a Chontapaccha como caso principal,
documentando la entrevista pendiente como limitación en el informe en
lugar de forzar un cambio de establecimiento.

## Ciclo 2: Ajuste tras prueba de viabilidad (validación de RUC)

**24/09/2026:** [FECHA]

La prueba del componente más incierto (AFND_RUC, ver sección 4 del
informe) confirmó la viabilidad del enfoque de validación de RUC
mediante expresión regular en Python (15/15 casos correctos).

Como resultado, el equipo ajustó el cronograma: se incorporó
explícitamente la tarea de integrar esta validación al módulo funcional
en el hito H5 (Tabla 2), y se acordó incluir una clase `ValidadorRUC`
en el diagrama de clases UML, en lugar de tratarla como un detalle
menor de RQ-04.
