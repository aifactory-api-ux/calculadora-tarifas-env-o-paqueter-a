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
