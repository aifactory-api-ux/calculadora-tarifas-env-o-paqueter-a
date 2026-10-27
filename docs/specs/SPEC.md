# Proposal

## Why

El equipo de logística interna de paquetería calcula hoy las tarifas de envío en scripts dispersos, cada uno con su propia versión del cálculo de peso volumétrico, redondeo y tarifas por zona; eso genera discrepancias entre cotizaciones y código duplicado que no se puede reutilizar. Se necesita una única librería Python pequeña, con aritmética decimal exacta y contrato de validación estricto, que el equipo consuma como dependencia en sus scripts.

## What Changes

- Se crea la librería `shipping` en `src/shipping.py` con tres funciones públicas: `volumetric_weight`, `billable_weight` y `shipping_cost`.
- Todo el cálculo se realiza con `decimal.Decimal` (sin `float`): el peso volumétrico y la tarifa final se redondean a 2 decimales con `ROUND_HALF_UP`, y el peso facturable se redondea hacia arriba al siguiente múltiplo de 0.5 kg.
- Se define un contrato de validación de entradas común a la API pública: pesos y medidas aceptan `int` o `Decimal` (`float` y `bool` → `TypeError`), los valores deben ser mayores que 0 (`ValueError` si no), `zone` debe ser exactamente `"A"`, `"B"` o `"C"` (`ValueError` en cualquier otro valor) y `express` debe ser `bool` (`TypeError` en caso contrario).
- Se impone un límite de 30 kg sobre el peso facturable: superarlo lanza `ValueError`.
- Se añade la suite de pruebas pytest en `tests/test_shipping.py` cubriendo ejemplos de referencia, redondeo a múltiplos de 0.5 kg, límite de 30 kg, express y todas las validaciones.
- Se añade un README breve con la API pública, las tarifas por zona y ejemplos de uso.
- Se añade un `Dockerfile` y un `docker-compose.yml` en la raíz del repositorio que construyen y ejecutan el proyecto (la imagen ejecuta la suite de pruebas, ya que la librería no expone servidor); `docker compose up --build` debe terminar con código de salida 0.

## Capabilities

### New Capabilities
- `volumetric-weight`: cálculo del peso volumétrico (producto de dimensiones dividido entre 5000) con redondeo a 2 decimales `ROUND_HALF_UP`.
- `billable-weight`: cálculo del peso facturable como el mayor entre peso real y volumétrico, redondeado hacia arriba al siguiente múltiplo de 0.5 kg, con límite superior de 30 kg.
- `shipping-rate`: cálculo de la tarifa de envío por zona (A/B/C), base + precio por kg sobre el peso facturable, con multiplicador express y redondeo final a 2 decimales `ROUND_HALF_UP`.
- `input-validation`: contrato común de validación de tipos y valores de la API pública (`int`/`Decimal` admitidos, `float`/`bool` rechazados, positividad, dominio de `zone`, tipo de `express`).
- `container-image`: empaquetado containerizado del proyecto mediante `Dockerfile` y `docker-compose.yml` en la raíz, cuya ejecución corre la suite de pruebas y termina con código 0.

### Modified Capabilities
- Ninguna. El repositorio no tiene especificaciones publicadas (`openspec/specs` está vacío); esta entrega introduce el primer conjunto de capacidades del proyecto.

## Impact

- Archivos nuevos: `src/shipping.py`, `tests/test_shipping.py`, `README.md`, `pyproject.toml`, `Dockerfile`, `docker-compose.yml`.
- Dependencias: sólo biblioteca estándar (`decimal`) en tiempo de ejecución; `pytest` como dependencia de desarrollo (usada en la imagen Docker).
- Sin servidor HTTP, sin base de datos, sin frontend ni servicios externos: la librería es una dependencia de los scripts Python del equipo de logística interno.
- El paquete se distribuye con layout `src/` (`src/shipping.py`) para poder instalarse como dependencia.
- Equipo de trabajo: únicamente el agente Developer, que escribe y ejecuta también las pruebas (no hay rol QA ni DevSec en esta entrega).


<!-- specs/billable-weight/spec.md -->
# Spec Delta

## Purpose

Define how the billable weight (peso facturable) of a parcel is obtained from the real weight and the parcel dimensions, including the rounding up to 0.5 kg steps and the maximum weight the library accepts.

## ADDED Requirements

### Requirement: Billable weight is the greatest of real and volumetric weight
The library SHALL compute the billable weight as the greater of the real weight and the volumetric weight of the parcel, and SHALL return the result as a `Decimal` value.

#### Scenario: Real weight greater than volumetric weight
- **WHEN** the billable weight is calculated for a real weight of 2 kg and dimensions 30 cm x 20 cm x 10 cm (volumetric weight 1.20 kg)
- **THEN** the billable weight is 2 kg before the 0.5 kg step rounding, that is `Decimal("2.00")` after rounding

#### Scenario: Volumetric weight greater than real weight
- **WHEN** the billable weight is calculated for a real weight of 1 kg and dimensions 25 cm x 40 cm x 40 cm (volumetric weight 8 kg)
- **THEN** the billable weight is `Decimal("8.00")`

### Requirement: Billable weight rounded up to the next multiple of 0.5 kg
The library SHALL round the billable weight up (never down) to the next multiple of 0.5 kg, keeping the value unchanged when it is already an exact multiple of 0.5 kg.

#### Scenario: Exact multiple of 0.5 kg is preserved
- **WHEN** the billable weight is calculated for a real weight of 2.0 kg and dimensions 30 cm x 20 cm x 10 cm
- **THEN** the result is exactly `Decimal("2.00")`

#### Scenario: Fractional kilogram is rounded up
- **WHEN** the billable weight is calculated for a real weight of 2.01 kg and dimensions 30 cm x 20 cm x 10 cm
- **THEN** the result is exactly `Decimal("2.50")`

#### Scenario: Volumetric weight is rounded up to the next step
- **WHEN** the billable weight is calculated for a real weight of 1 kg and dimensions 40 cm x 30 cm x 30 cm (volumetric weight 7.2 kg)
- **THEN** the result is exactly `Decimal("7.50")`

### Requirement: Billable weight limited to 30 kg
The library SHALL raise a `ValueError` when the computed billable weight exceeds 30 kg, regardless of whether the excess comes from the real weight or from the volumetric weight. A billable weight of exactly 30 kg SHALL be accepted.

#### Scenario: Exactly 30 kg is accepted
- **WHEN** the billable weight is calculated for a real weight of 30 kg and dimensions 30 cm x 20 cm x 10 cm
- **THEN** no exception is raised and the result is exactly `Decimal("30.00")`

#### Scenario: Real weight above the limit
- **WHEN** the billable weight is calculated for a real weight of 30.5 kg and dimensions 30 cm x 20 cm x 10 cm
- **THEN** a `ValueError` is raised

#### Scenario: Volumetric weight above the limit
- **WHEN** the billable weight is calculated for a real weight of 1 kg and dimensions 100 cm x 100 cm x 100 cm (volumetric weight 200 kg)
- **THEN** a `ValueError` is raised


<!-- specs/container-image/spec.md -->
# Spec Delta

## Purpose

Define how the project is packaged and executed in containers, so that the library and its test suite can be built and verified reproducibly on any machine with a container runtime.

## ADDED Requirements

### Requirement: Root Dockerfile building the library and its test environment
The repository SHALL provide a `Dockerfile` at the repository root that builds a runnable image containing the library, its dependencies and the test tooling required to execute the test suite.

#### Scenario: Dockerfile present at the repository root
- **WHEN** the repository root is listed
- **THEN** a file named `Dockerfile` exists at the root of the repository

#### Scenario: Image provides the library and the test runner
- **WHEN** the image defined by the root `Dockerfile` is built
- **THEN** the image can import the `shipping` library and can execute `pytest` over the `tests/` directory

### Requirement: Root docker-compose service building and running the project
The repository SHALL provide a `docker-compose.yml` at the repository root that defines at least one service that builds the image from the root `Dockerfile` and runs the project.

#### Scenario: Compose file present at the repository root
- **WHEN** the repository root is listed
- **THEN** a file named `docker-compose.yml` exists at the root of the repository

#### Scenario: Compose service runs the test suite
- **WHEN** `docker compose up --build` is executed from the repository root
- **THEN** the service starts the image built from the root `Dockerfile` and runs the pytest suite over the `tests/` directory

### Requirement: Containerized run completes successfully
The containerized run SHALL execute the whole test suite and SHALL terminate with exit code 0 when every test passes.

#### Scenario: Successful containerized run
- **WHEN** `docker compose up --build` is executed from the repository root and the test suite passes
- **THEN** the command exits with code 0 and the pytest summary reports no failed tests

#### Scenario: No external service required
- **WHEN** `docker compose up --build` is executed from the repository root
- **THEN** the run completes without requiring any external service (database, API or message broker) to be available


<!-- specs/input-validation/spec.md -->
# Spec Delta

## Purpose

Define the validation contract shared by every public function of the library (accepted argument types, positivity of numeric inputs, allowed zones and express flag) so that invalid usage fails fast with predictable errors.

## ADDED Requirements

### Requirement: Numeric inputs accept only integers and decimals
Every numeric argument (real weight, length, width, height) SHALL accept `int` and `Decimal` values, and SHALL raise a `TypeError` for any other type, including `float` and `bool`.

#### Scenario: Integer weight accepted
- **WHEN** the shipping cost is calculated for a real weight of 2 kg and dimensions 30 cm x 20 cm x 10 cm in zone `"B"`
- **THEN** no exception is raised and the result is exactly `Decimal("11.10")`

#### Scenario: Decimal weight accepted
- **WHEN** the shipping cost is calculated for a real weight of `Decimal("2")` and dimensions `Decimal("30")` x `Decimal("20")` x `Decimal("10")` in zone `"B"`
- **THEN** no exception is raised and the result is exactly `Decimal("11.10")`

#### Scenario: Float weight rejected
- **WHEN** the shipping cost is calculated for a real weight of 2.0 (a float) and dimensions 30 cm x 20 cm x 10 cm in zone `"B"`
- **THEN** a `TypeError` is raised

#### Scenario: Boolean weight rejected
- **WHEN** the shipping cost is calculated for a real weight of `True` and dimensions 30 cm x 20 cm x 10 cm in zone `"B"`
- **THEN** a `TypeError` is raised

#### Scenario: Float dimension rejected
- **WHEN** the volumetric weight is calculated for dimensions 30.0 cm (a float) x 20 cm x 10 cm
- **THEN** a `TypeError` is raised

#### Scenario: Boolean dimension rejected
- **WHEN** the volumetric weight is calculated for dimensions `True` (a bool) x 20 cm x 10 cm
- **THEN** a `TypeError` is raised

### Requirement: Numeric inputs must be greater than zero
Every numeric argument SHALL be greater than zero, and the library SHALL raise a `ValueError` when a numeric argument is zero or negative.

#### Scenario: Zero real weight rejected
- **WHEN** the billable weight is calculated for a real weight of 0 kg and dimensions 30 cm x 20 cm x 10 cm
- **THEN** a `ValueError` is raised

#### Scenario: Negative real weight rejected
- **WHEN** the billable weight is calculated for a real weight of -1 kg and dimensions 30 cm x 20 cm x 10 cm
- **THEN** a `ValueError` is raised

#### Scenario: Zero dimension rejected
- **WHEN** the volumetric weight is calculated for dimensions 0 cm x 20 cm x 10 cm
- **THEN** a `ValueError` is raised

#### Scenario: Negative dimension rejected
- **WHEN** the volumetric weight is calculated for dimensions 30 cm x -20 cm x 10 cm
- **THEN** a `ValueError` is raised

### Requirement: Zone restricted to the letters A, B and C
The `zone` argument SHALL be exactly the string `"A"`, `"B"` or `"C"`, and the library SHALL raise a `ValueError` for any other value, whatever its type.

#### Scenario: Each known zone accepted
- **WHEN** the shipping cost is calculated in zone `"A"`, `"B"` and `"C"` for a real weight of 2 kg and dimensions 30 cm x 20 cm x 10 cm
- **THEN** no exception is raised and the results are `Decimal("7.40")`, `Decimal("11.10")` and `Decimal("17.00")` respectively

#### Scenario: Lowercase zone rejected
- **WHEN** the shipping cost is calculated in zone `"a"` for a real weight of 2 kg and dimensions 30 cm x 20 cm x 10 cm
- **THEN** a `ValueError` is raised

#### Scenario: Unknown zone rejected
- **WHEN** the shipping cost is calculated in zone `"D"` for a real weight of 2 kg and dimensions 30 cm x 20 cm x 10 cm
- **THEN** a `ValueError` is raised

#### Scenario: Non string zone rejected
- **WHEN** the shipping cost is calculated with `zone=None` for a real weight of 2 kg and dimensions 30 cm x 20 cm x 10 cm
- **THEN** a `ValueError` is raised

### Requirement: Express option must be a boolean
The `express` argument SHALL be a `bool`, and the library SHALL raise a `TypeError` when any other value is supplied.

#### Scenario: Boolean express accepted
- **WHEN** the shipping cost is calculated with `express=True` and with `express=False` for a real weight of 2 kg and dimensions 30 cm x 20 cm x 10 cm in zone `"B"`
- **THEN** no exception is raised and the results are `Decimal("16.65")` and `Decimal("11.10")` respectively

#### Scenario: Integer express rejected
- **WHEN** the shipping cost is calculated with `express=1` for a real weight of 2 kg and dimensions 30 cm x 20 cm x 10 cm in zone `"B"`
- **THEN** a `TypeError` is raised

#### Scenario: String express rejected
- **WHEN** the shipping cost is calculated with `express="true"` for a real weight of 2 kg and dimensions 30 cm x 20 cm x 10 cm in zone `"B"`
- **THEN** a `TypeError` is raised


<!-- specs/shipping-rate/spec.md -->
# Spec Delta

## Purpose

Define the shipping tariff charged for a parcel, based on the destination zone, the billable weight and the optional express service, so that every consumer of the library obtains the same amount to charge.

## ADDED Requirements

### Requirement: Zone tariff table
The library SHALL charge a fixed base amount plus a price per kilogram applied to the billable weight, using exactly these tariffs: zone `"A"` = 5.00 + 1.20 per kg, zone `"B"` = 7.50 + 1.80 per kg, zone `"C"` = 12.00 + 2.50 per kg.

#### Scenario: Zone B tariff
- **WHEN** the shipping cost is calculated for a real weight of 2 kg and dimensions 30 cm x 20 cm x 10 cm in zone `"B"` (billable weight 2 kg)
- **THEN** the result is exactly `Decimal("11.10")`

#### Scenario: Zone A tariff
- **WHEN** the shipping cost is calculated for a real weight of 2 kg and dimensions 30 cm x 20 cm x 10 cm in zone `"A"` (billable weight 2 kg)
- **THEN** the result is exactly `Decimal("7.40")`

#### Scenario: Zone C tariff
- **WHEN** the shipping cost is calculated for a real weight of 2 kg and dimensions 30 cm x 20 cm x 10 cm in zone `"C"` (billable weight 2 kg)
- **THEN** the result is exactly `Decimal("17.00")`

### Requirement: Shipping cost computed over the billable weight
The library SHALL apply the tariff to the billable weight (the greatest of real and volumetric weight, rounded up to the next multiple of 0.5 kg) and not to the real weight alone.

#### Scenario: Volumetric weight drives the tariff
- **WHEN** the shipping cost is calculated for a real weight of 1 kg and dimensions 40 cm x 30 cm x 30 cm in zone `"A"` (billable weight 7.5 kg)
- **THEN** the result is exactly `Decimal("14.00")`

### Requirement: Express service multiplies the total by 1.5
The library SHALL multiply the tariff total by 1.5 when the express option is enabled, and SHALL leave the total unmultiplied when the express option is not enabled.

#### Scenario: Express tariff
- **WHEN** the shipping cost is calculated for a real weight of 2 kg and dimensions 30 cm x 20 cm x 10 cm in zone `"B"` with express enabled
- **THEN** the result is exactly `Decimal("16.65")`

#### Scenario: Express not enabled by default
- **WHEN** the shipping cost is calculated for a real weight of 2 kg and dimensions 30 cm x 20 cm x 10 cm in zone `"B"` and the express option is omitted
- **THEN** the result is exactly `Decimal("11.10")`

### Requirement: Shipping cost rounded to two decimals with ROUND_HALF_UP
The library SHALL round the final shipping cost, after any express multiplication, to two decimal places using `ROUND_HALF_UP`.

#### Scenario: Third decimal of exactly five rounds up
- **WHEN** the shipping cost is calculated for a real weight of 2.5 kg and dimensions 30 cm x 20 cm x 10 cm in zone `"C"` with express enabled (raw total 27.375)
- **THEN** the result is exactly `Decimal("27.38")`

#### Scenario: Result type is Decimal
- **WHEN** the shipping cost is calculated for a real weight of 2 kg and dimensions 30 cm x 20 cm x 10 cm in zone `"B"`
- **THEN** the returned value is an instance of `Decimal` and not a `float`


<!-- specs/volumetric-weight/spec.md -->
# Spec Delta

## Purpose

Define how the parcel volumetric weight (dimensional weight) is derived from the three parcel dimensions, so that any consumer of the library obtains the same dimensional weight and the same rounding for identical inputs.

## ADDED Requirements

### Requirement: Volumetric weight derived from parcel dimensions
The library SHALL compute the volumetric weight as `length_cm * width_cm * height_cm / 5000`, using exact decimal arithmetic and no binary floating point, and SHALL return the result as a `Decimal` value.

#### Scenario: Reference parcel dimensions
- **WHEN** the volumetric weight is calculated for dimensions 30 cm x 20 cm x 10 cm
- **THEN** the result is exactly `Decimal("1.20")`

#### Scenario: Dimensions supplied as Decimal values
- **WHEN** the volumetric weight is calculated for dimensions `Decimal("30")` x `Decimal("20")` x `Decimal("10")`
- **THEN** the result is exactly `Decimal("1.20")`

#### Scenario: Result type is Decimal
- **WHEN** the volumetric weight is calculated for dimensions 30 cm x 20 cm x 10 cm
- **THEN** the returned value is an instance of `Decimal` and not a `float`

### Requirement: Volumetric weight rounded to two decimals with ROUND_HALF_UP
The library SHALL round the volumetric weight to two decimal places using `ROUND_HALF_UP`, so that a third decimal of exactly 5 is always rounded up.

#### Scenario: Third decimal of exactly five rounds up
- **WHEN** the volumetric weight is calculated for dimensions 25 cm x 201 cm x 1 cm (raw value 1.005)
- **THEN** the result is exactly `Decimal("1.01")`

#### Scenario: Value below the half rounds down
- **WHEN** the volumetric weight is calculated for dimensions 40 cm x 30 cm x 30 cm (raw value 7.2)
- **THEN** the result is exactly `Decimal("7.20")`


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
