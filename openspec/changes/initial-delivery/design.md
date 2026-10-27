# Design

## Context

El repositorio está vacío salvo el andamiaje de OpenSpec (`openspec/`) y un `.gitignore`: no existe código Python, ni `pyproject.toml`, ni pruebas, ni contenedores. Ver `proposal.md` para la motivación.

Restricciones que condicionan el diseño:

- Biblioteca consumida como dependencia en scripts Python del equipo de logística interno: sin servidor HTTP, sin CLI, sin interfaz, sin base de datos ni servicios externos.
- Sólo biblioteca estándar en tiempo de ejecución (`decimal`); `pytest` como dependencia de desarrollo.
- Aritmética exacta: los importes y pesos no admiten `float`; el contrato de entradas (ver `specs/input-validation/spec.md`) rechaza `float` y `bool`.
- Entrega siempre containerizada: el proyecto se construye y ejecuta en Docker; como no hay servidor, el contenedor ejecuta la suite de pruebas.
- El equipo es únicamente el agente **Developer**, sin roles QA ni DevSec: el Developer escribe y ejecuta también las pruebas de cada grupo de tareas.
- Los requisitos de comportamiento están fijados en `specs/`; este documento sólo explica cómo se implementan.

## Goals / Non-Goals

**Goals:**

- Una única unidad de código importable, `src/shipping.py`, con las tres funciones públicas `volumetric_weight`, `billable_weight` y `shipping_cost`, sin estado global ni efectos de entrada/salida.
- Aritmética `Decimal` de principio a fin: los únicos puntos de redondeo son los fijados por las especificaciones (2 decimales `ROUND_HALF_UP` para peso volumétrico y tarifa; techo a múltiplos de 0.5 kg para el peso facturable).
- Un único punto de validación reutilizado por las tres funciones, de modo que el contrato de tipos y valores sea idéntico en toda la API.
- Pruebas pytest que fijen cada valor numérico de las especificaciones (incluidos los ejemplos `1.20`, `11.10`, `16.65` y `14.00`).
- Build y ejecución reproducibles en contenedor: `Dockerfile` + `docker-compose.yml` en la raíz, con `docker compose up --build` como comando de verificación de la entrega.

**Non-Goals:**

- Servidor, API HTTP, CLI, GUI o cualquier forma de interfaz.
- Persistencia, base de datos, cola de mensajes o cualquier servicio externo; tampoco multi-parcela, seguro de mercancía, recargos de combustible o tipos de cambio.
- Zonas, tarifas o unidades distintas de las fijadas (kg y cm, zonas `"A"`, `"B"`, `"C"`).
- Dependencias de terceros en tiempo de ejecución; cualquier librería externa de redondeo o de validación.
- Capacidades de packaging avanzadas (publicación en un índice, wheels multiplataforma, versionado semántico propio): el `pyproject.toml` sólo describe metadatos y el comando de instalación.

## Decisions

### D1 — Layout `src/` con un único módulo `shipping`

`src/shipping.py` es el módulo distribuible; `pyproject.toml` (setuptools, `package-dir = {"" = "src"}`) lo expone como paquete `shipping`. El import real es `from shipping import shipping_cost`.

Alternativas: (a) `shipping.py` en la raíz del repositorio — se descarta porque el mismo nombre quedaría en `sys.path` al ejecutar pytest desde la raíz y podría ensuciar el espacio de nombres del proyecto de pruebas; (b) paquete con submódulos (`src/shipping/weights.py`, `src/shipping/rates.py`) — se descarta porque la API pedida es de tres funciones y un solo módulo mantiene el coste de lectura en el mínimo; se admite crecer a submódulos si la biblioteca crece.

### D2 — Funciones puras a nivel de módulo, con `__all__`

`volumetric_weight`, `billable_weight` y `shipping_cost` son funciones puras con los nombres y las firmas fijados en el enunciado. `__all__` declara la superficie pública.

Alternativa: API orientada a objetos (`Shipment`, `Carrier`) — se descarta porque el enunciado fija nombres de funciones y argumentos, y la lógica de tarifas es estática.

### D3 — Frontera de tipos: `int` y `Decimal` aceptados, `float` y `bool` rechazados

El contrato es verificado con `isinstance(value, bool)` primero (en Python `bool` es subclase de `int`, así que un chequeo de `int` solo dejaría pasar `True`/`False`), después `isinstance(value, int)` o `isinstance(value, Decimal)`, y en caso contrario `TypeError`. Los `int` válidos se convierten con `Decimal(value)` (conversión exacta); los `Decimal` se usan tal cual.

El chequeo de tipo precede al de valor: un `float` negativo debe producir `TypeError` (tipo incorrecto) y no `ValueError` (valor incorrecto). Un `Decimal` negativo produce `ValueError`.

Alternativa: aceptar `float` y convertirlo con `Decimal(str(value))` — se descarta explícitamente porque el enunciado exige `TypeError` para `float` y `bool`, y la conversión desde texto reintroduce la imprecisión binaria que se quiere evitar.

### D4 — Validación única reutilizable

Dos auxiliares privados en `src/shipping.py`:

- `_to_decimal(value, name) -> Decimal`: aplica D3 y devuelve el `Decimal` listo para operar.
- `_require_positive(value, name) -> Decimal`: aplica `_to_decimal` y exige `value > 0`; si no, `ValueError` indicando el parámetro y el valor recibido.

Todas las medidas y el peso real pasan por `_require_positive`. `zone` se valida contra las claves de la tabla de tarifas y cualquier valor distinto de `"A"`, `"B"`, `"C"` produce `ValueError` (también para `None` u otros tipos, según el requisito). `express` se valida con `isinstance(express, bool)`; cualquier otro valor produce `TypeError`.

Alternativa: usar un esquema de validación externo (pydantic) — se descarta por la restricción de sólo biblioteca estándar.

### D5 — Peso volumétrico: producto exacto y un único redondeo

`volumetric_weight` calcula `Decimal(length) * Decimal(width) * Decimal(height) / Decimal(5000)` —la división por `Decimal(5000)` es exacta en aritmética decimal— y aplica `quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)`.

Alternativa: `round(float(...), 2)` — se descarta: introduce `float` y redondeo a mitad a pares, que no reproduce `1.005 -> 1.01`.

### D6 — Peso facturable: máximo, techo a 0.5 kg y límite de 30 kg sobre el valor facturable

`billable_weight` toma el máximo entre el peso real y el peso volumétrico, y aplica el techo al múltiplo de 0.5 kg mediante `steps = (value / Decimal("0.5")).to_integral_value(rounding=ROUND_CEILING)` y `result = steps * Decimal("0.5")`. Con esto `2.0 -> 2.0`, `2.01 -> 2.5` y `7.2 -> 7.5`.

El límite de 30 kg se comprueba **sobre el peso facturable ya redondeado** (`result > 30` ⇒ `ValueError`), porque la magnitud que se cobra es la redondeada: `30.0` se acepta, `30.5` se rechaza, y un peso real de `29.9` (que se factura como `30.0`) también se acepta. El mensaje de error incluye el peso facturable calculado.

Alternativa: comprobar el límite antes del redondeo — se descarta porque permitiría facturar `30.5` (un peso real de `30.1` redondea a `30.5` y se cobraría por encima del tope) o rechazaría `29.9`, que sí cabe en el límite una vez facturado.

### D7 — Tarifa: base + precio por kg sobre el peso facturable, un único redondeo final

`shipping_cost` obtiene el peso facturable con `billable_weight` (por lo que hereda su validación y su límite de 30 kg), calcula `base + rate * billable` con la tabla de tarifas, multiplica ese total por `Decimal("1.5")` cuando `express` es `True`, y **entonces** aplica un único `quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)`.

El redondeo se hace una sola vez, al final: redondear el total base antes de multiplicar por 1.5 cambiaría el céntimo final en casos como `18.25 * 1.5 = 27.375 -> 27.38` frente a `round(18.25, 2) * 1.5 = 27.375` (mismo valor aquí, pero frágil ante cualquier tarifa con más decimales).

La tabla de tarifas es un mapeo privado a nivel de módulo:

```
_ZONE_RATES = {
    "A": (Decimal("5.00"), Decimal("1.20")),
    "B": (Decimal("7.50"), Decimal("1.80")),
    "C": (Decimal("12.00"), Decimal("2.50")),
}
```

Alternativa: constantes sueltas (`BASE_A`, `KG_A`, ...) — se descarta porque un mapeo permite validar `zone` con una única fuente de verdad. Alternativa: tabla pública y mutable — se descarta para que las tarifas no puedan alterarse en tiempo de ejecución por accidente.

### D8 — Pruebas pytest agrupadas por capacidad y README breve

- `tests/test_shipping.py`: suite principal con los tres casos del enunciado (`11.10`, `16.65`, `14.00`), el redondeo a 0.5 kg (`2.0 -> 2.0`, `2.01 -> 2.5`), el límite de 30 kg (30 kg aceptado, 30.5 kg y volumétrico 200 kg rechazados), el redondeo `ROUND_HALF_UP` (`1.005 -> 1.01`, `27.375 -> 27.38`) y todas las validaciones (`float`, `bool`, valores ≤ 0, `zone` inválida, `express` no booleano).
- `tests/test_readme.py`: verifica que el README documente las tres funciones públicas, las tres zonas y un ejemplo de uso.
- `tests/test_container.py`: verifica que en la raíz existan `Dockerfile` y `docker-compose.yml`, que el compose construya desde el `Dockerfile` de la raíz y que su comando sea la suite de pruebas.
- `README.md` (raíz): documento breve en español con el propósito, la instalación, las tres funciones y sus firmas, la tabla de tarifas por zona, el multiplicador express, las reglas de redondeo, el contrato de validación y los ejemplos `11.10`, `16.65` y `14.00`. Es la referencia que consumen los scripts del equipo de logística, así que se escribe en el mismo idioma que la documentación interna.

`pyproject.toml` declara `[tool.pytest.ini_options] testpaths = ["tests"]` y `pythonpath = ["src"]` (para que la suite importe el módulo sin necesidad de instalar el paquete), más el extra de desarrollo `dev` con `pytest`.

Alternativa: una única suite monolítica en `tests/test_shipping.py` — se descarta porque el enunciado ubica ahí la suite principal, pero los grupos de documentación y de contenedores merecen archivos propios.

### D9 — Contenedor: imagen de pruebas como servicio de compose

`Dockerfile` (raíz):

1. `FROM python:3.12-slim` como base.
2. `WORKDIR /app`.
3. Copia `pyproject.toml` y `src/`, instala el paquete (`pip install --no-cache-dir .`) y `pytest`.
4. Copia `tests/`.
5. `CMD ["pytest", "-q"]`.

`docker-compose.yml` (raíz) define un servicio único (`shipping-tests`) con `build: .` (usa el `Dockerfile` de la raíz), `command: ["pytest", "-q"]` y `restart: "no"`, sin `ports` (no hay servidor) ni `depends_on` (no hay servicios externos).

El servicio termina al terminar la suite, de modo que `docker compose up --build` devuelve el código de salida del contenedor: 0 si todos los tests pasan.

Alternativa: una imagen "producto" sin dependencias de desarrollo — se descarta porque, al no haber servidor, la única cosa ejecutable útil del proyecto es su suite de pruebas; el contenedor ejecuta precisamente eso.

### D10 — Roles: un único agente Developer

Todos los grupos de tareas (implementación, pruebas, README y contenedores) los ejecuta el agente Developer, que escribe y ejecuta las pruebas él mismo. No se generan tareas de revisión QA ni DevSec, ni pasos de validación manual por terceros.

## Risks / Trade-offs

- [Riesgo] El orden de redondeo (un único redondeo final) puede divergir de la expectativa de quien apply redondeos intermedios → Mitigación: el orden queda documentado en el README y fijado por el test `27.375 -> 27.38` y por los ejemplos del enunciado.
- [Riesgo] `bool` es subclase de `int` en Python, por lo que un chequeo ingenuo dejaría pasar `True`/`False` como pesos → Mitigación: `_to_decimal` excluye `bool` explícitamente y hay tests dedicados para pesos y dimensiones booleanos.
- [Riesgo] El techo a 0.5 kg puede empujar un paquete de 30.0 a 30.5 kg y disparar el `ValueError` → Mitigación: el límite se evalúa sobre el peso facturable redondeado (decisión D6) y el mensaje de error informa del valor calculado, para que el consumidor entienda por qué se rechaza el envío.
- [Riesgo] El redondeo al alza puede subir de 29.9 a 30.0 kg, moviendo un envío al borde del tope → Mitigación: es el comportamiento especificado; se documenta en el README.
- [Riesgo] Un consumidor que pase `float` obtendrá `TypeError` en vez de un cálculo aproximado → Mitigación: el README muestra `Decimal` y `int` como tipos de entrada admitidos.
- [Riesgo] `docker compose up --build` necesita un runtime de contenedores disponible en el entorno donde se verifica → Mitigación: `Dockerfile` y `docker-compose.yml` son ficheros estáticos y verificables sin runtime (`tests/test_container.py`), y la verificación final del comando se ejecuta donde exista el runtime.
- [Trade-off] La tabla de tarifas es privada y fija: no puede ampliarse con zonas nuevas en tiempo de ejecución → Aceptado: el enunciado fija las tres tarifas; ampliar zonas exigiría otro cambio.

## Migration Plan

No aplica: es el primer despliegue del proyecto, no hay datos ni usuarios previos que migrar.

Puesta en marcha: publicar el paquete `shipping` en el canal interno de distribución de Python (índice privado o copia versionada) e actualizar los scripts de logística para importar `from shipping import shipping_cost`. Revertir consiste en volver a la versión previa del paquete/scripts, sin estado que restaurar.

## Open Questions

- Canal concreto de distribución al equipo de logística (índice pip privado, copia versionada en el repositorio de scripts): es una decisión de publicación posterior a esta entrega. No cambia las especificaciones, ni el diseño, ni el desglose de tareas, por lo que no se resuelve aquí ni bloquea la implementación.
