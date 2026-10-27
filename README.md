# shipping — Calculadora de tarifas de envío de paquetería

## Propósito

`shipping` es una librería Python que centraliza el cálculo de las tarifas de
envío de paquetería del equipo de logística interno. Expone tres funciones
públicas —peso volumétrico, peso facturable y tarifa final— con aritmética
decimal exacta (`decimal.Decimal`, sin `float`) y un contrato de validación
estricto, de modo que todas las cotizaciones del equipo salgan de la misma
implementación.

La librería no es un servicio: no expone servidor, CLI ni interfaz de usuario.
Se consume como dependencia desde los scripts Python del equipo.

## Requisitos

- Python 3.10 o superior.
- Sin dependencias de terceros en tiempo de ejecución: sólo `decimal` de la
  biblioteca estándar.
- `pytest` como dependencia de desarrollo (extra `dev`).

## Instalación

Desde la raíz del repositorio:

```bash
pip install .
```

Para instalar el paquete en modo editable junto con las herramientas de
desarrollo:

```bash
pip install -e ".[dev]"
```

Los scripts del equipo importan la librería con:

```python
from shipping import shipping_cost
```

## API pública

Las tres funciones son puras, devuelven `Decimal` y comparten el mismo
contrato de validación.

### `volumetric_weight(length_cm, width_cm, height_cm) -> Decimal`

Calcula el peso volumétrico del paquete: el producto de las tres dimensiones
en centímetros dividido entre 5000, redondeado a dos decimales con
`ROUND_HALF_UP`.

```python
volumetric_weight(30, 20, 10)   # Decimal('1.20')
```

### `billable_weight(actual_kg, length_cm, width_cm, height_cm) -> Decimal`

Calcula el peso facturable del paquete: el mayor entre el peso real y el peso
volumétrico, redondeado **hacia arriba** al siguiente múltiplo de 0.5 kg. Si el
peso facturable ya redondeado supera los 30 kg, se lanza `ValueError`.

```python
billable_weight(2, 30, 20, 10)     # Decimal('2.00')
billable_weight(Decimal("2.01"), 30, 20, 10)   # Decimal('2.50')
```

### `shipping_cost(actual_kg, length_cm, width_cm, height_cm, zone, express=False) -> Decimal`

Calcula la tarifa de envío: precio base de la zona más el precio por kg
aplicado al peso facturable. Con `express=True` el total se multiplica por 1.5.
El resultado se redondea a dos decimales con `ROUND_HALF_UP`.

```python
shipping_cost(2, 30, 20, 10, "B")                # Decimal('11.10')
shipping_cost(2, 30, 20, 10, "B", express=True)  # Decimal('16.65')
```

## Reglas de cálculo

### Peso volumétrico

```
peso_volumetrico = (largo_cm * ancho_cm * alto_cm) / 5000
```

### Peso facturable

```
peso_facturable = techo_a_0_5_kg(max(peso_real, peso_volumetrico))
```

El redondeo al alza nunca baja el peso: un múltiplo exacto de 0.5 kg se
conserva (2.0 → 2.0) y cualquier fracción se sube al paso siguiente
(2.01 → 2.5, 7.2 → 7.5).

El límite de **30 kg** se comprueba sobre el peso facturable ya redondeado:
30 kg exactos se aceptan y 30.5 kg se rechazan con `ValueError`.

### Redondeos

- Peso volumétrico y tarifa final: dos decimales con `ROUND_HALF_UP`.
- Peso facturable: techo al siguiente múltiplo de 0.5 kg (nunca hacia abajo).
- La tarifa aplica un **único** redondeo, después de la posible multiplicación
  por el factor express (por ejemplo, 27.375 → 27.38).

## Tarifas por zona

| Zona | Precio base | Precio por kg facturable |
| --- | --- | --- |
| `"A"` | 5.00 | 1.20 |
| `"B"` | 7.50 | 1.80 |
| `"C"` | 12.00 | 2.50 |

```
tarifa = precio_base + precio_por_kg * peso_facturable
tarifa_express = tarifa * 1.5
```

El multiplicador del servicio express es **1.5** y se aplica al total completo
(base más parte por peso) antes del redondeo final.

## Contrato de validación

| Argumento | Tipos admitidos | Rechazo |
| --- | --- | --- |
| `actual_kg`, `length_cm`, `width_cm`, `height_cm` | `int` o `Decimal` | `float` o `bool` → `TypeError`; valor menor o igual que 0 → `ValueError`; valor no finito (`NaN`, `Infinity`) → `ValueError` |
| `zone` | `str` | cualquier valor distinto de `"A"`, `"B"` o `"C"` → `ValueError` |
| `express` | `bool` | cualquier otro tipo → `TypeError` |

El chequeo de tipo precede al de valor: un peso `float` negativo produce
`TypeError` y no `ValueError`. `bool` se rechaza de forma explícita porque en
Python es subclase de `int`.

## Ejemplos de uso

```python
from decimal import Decimal

from shipping import shipping_cost

# 2 kg, 30 x 20 x 10 cm, zona B: 7.50 + 1.80 x 2.00 = 11.10
shipping_cost(2, 30, 20, 10, "B")                # Decimal('11.10')

# El mismo envío con servicio express: 11.10 x 1.5 = 16.65
shipping_cost(2, 30, 20, 10, "B", express=True)  # Decimal('16.65')

# 1 kg, 40 x 30 x 30 cm, zona A: el peso facturable es 7.50 kg (7.20 volumétrico
# redondeado al alza), 5.00 + 1.20 x 7.50 = 14.00
shipping_cost(1, 40, 30, 30, "A")                # Decimal('14.00')
```

## Pruebas

La suite se ejecuta con `pytest` desde la raíz del repositorio:

```bash
pytest
```

El `pyproject.toml` configura `pythonpath = ["src"]`, de modo que la suite
importa el módulo sin necesidad de instalar el paquete.
