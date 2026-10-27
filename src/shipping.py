"""Cálculo de tarifas de envío de paquetería.

La librería expone tres funciones públicas que comparten un contrato de
validación estricto y trabajan exclusivamente con `decimal.Decimal`:

- `volumetric_weight`: peso volumétrico a partir de las dimensiones del paquete.
- `billable_weight`: peso facturable (el mayor entre real y volumétrico).
- `shipping_cost`: tarifa final por zona, con servicio express opcional.

Uso:

    >>> from shipping import shipping_cost
    >>> shipping_cost(2, 30, 20, 10, "B")
    Decimal('11.10')
"""

from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal

__all__ = ["volumetric_weight", "billable_weight", "shipping_cost"]

# Redondeo a dos decimales para pesos volumétricos y tarifas.
_CENTS = Decimal("0.01")

# Divisor del peso volumétrico: producto de dimensiones en cm3 / 5000.
_VOLUMETRIC_DIVISOR = Decimal(5000)

# Paso del techo del peso facturable y límite máximo aceptado.
_WEIGHT_STEP_KG = Decimal("0.5")
_MAX_BILLABLE_KG = Decimal("30")

# Multiplicador aplicado al total cuando el servicio express está activo.
_EXPRESS_MULTIPLIER = Decimal("1.5")

# Tarifa por zona: (precio base, precio por kg facturable).
_ZONE_RATES = {
    "A": (Decimal("5.00"), Decimal("1.20")),
    "B": (Decimal("7.50"), Decimal("1.80")),
    "C": (Decimal("12.00"), Decimal("2.50")),
}


def _to_decimal(value: int | Decimal, name: str) -> Decimal:
    """Convierte a `Decimal` un valor numérico admitido por la API pública.

    Se admiten `int` y `Decimal`. `bool` se rechaza de forma explícita porque
    es subclase de `int` en Python, y `float` se rechaza porque introduce
    imprecisión binaria.

    Args:
        value: Valor a convertir.
        name: Nombre del parámetro, usado en el mensaje de error.

    Returns:
        El valor expresado como `Decimal`.

    Raises:
        TypeError: Si el tipo de `value` no es `int` ni `Decimal`.
    """
    if isinstance(value, bool):
        raise TypeError(f"{name} debe ser int o Decimal, no bool")
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    raise TypeError(f"{name} debe ser int o Decimal, no {type(value).__name__}")


def _require_positive(value: int | Decimal, name: str) -> Decimal:
    """Valida el tipo de un valor numérico y exige que sea mayor que cero.

    Los valores no finitos (`NaN`, `Infinity`) se rechazan también: no son
    comparables con cero de forma útil y provocarían errores aritméticos no
    controlados en los cálculos posteriores.

    Args:
        value: Valor a validar.
        name: Nombre del parámetro, usado en los mensajes de error.

    Returns:
        El valor validado expresado como `Decimal`.

    Raises:
        TypeError: Si el tipo de `value` no es `int` ni `Decimal`.
        ValueError: Si el valor no es finito o no es mayor que cero.
    """
    number = _to_decimal(value, name)
    if not number.is_finite():
        raise ValueError(f"{name} debe ser un número finito, recibido: {value!r}")
    if number <= 0:
        raise ValueError(f"{name} debe ser mayor que 0, recibido: {value!r}")
    return number


def volumetric_weight(
    length_cm: int | Decimal,
    width_cm: int | Decimal,
    height_cm: int | Decimal,
) -> Decimal:
    """Calcula el peso volumétrico del paquete.

    El peso volumétrico es el producto de las tres dimensiones dividido entre
    5000, redondeado a dos decimales con `ROUND_HALF_UP`.

    Args:
        length_cm: Largo del paquete en centímetros.
        width_cm: Ancho del paquete en centímetros.
        height_cm: Alto del paquete en centímetros.

    Returns:
        El peso volumétrico en kg, con dos decimales.

    Raises:
        TypeError: Si alguna medida no es `int` ni `Decimal`.
        ValueError: Si alguna medida no es mayor que cero.

    Example:
        >>> volumetric_weight(30, 20, 10)
        Decimal('1.20')
    """
    length = _require_positive(length_cm, "length_cm")
    width = _require_positive(width_cm, "width_cm")
    height = _require_positive(height_cm, "height_cm")
    volumetric = (length * width * height) / _VOLUMETRIC_DIVISOR
    return volumetric.quantize(_CENTS, rounding=ROUND_HALF_UP)


def billable_weight(
    actual_kg: int | Decimal,
    length_cm: int | Decimal,
    width_cm: int | Decimal,
    height_cm: int | Decimal,
) -> Decimal:
    """Calcula el peso facturable del paquete.

    El peso facturable es el mayor entre el peso real y el peso volumétrico,
    redondeado al alza hasta el siguiente múltiplo de 0.5 kg. El límite de
    30 kg se comprueba sobre el valor ya redondeado.

    Args:
        actual_kg: Peso real del paquete en kg.
        length_cm: Largo del paquete en centímetros.
        width_cm: Ancho del paquete en centímetros.
        height_cm: Alto del paquete en centímetros.

    Returns:
        El peso facturable en kg, con dos decimales.

    Raises:
        TypeError: Si algún valor no es `int` ni `Decimal`.
        ValueError: Si algún valor no es mayor que cero o si el peso facturable
            supera los 30 kg.

    Example:
        >>> billable_weight(2, 30, 20, 10)
        Decimal('2.00')
    """
    real_weight = _require_positive(actual_kg, "actual_kg")
    volumetric = volumetric_weight(length_cm, width_cm, height_cm)
    base = max(real_weight, volumetric)
    steps = (base / _WEIGHT_STEP_KG).to_integral_value(rounding=ROUND_CEILING)
    billable = (steps * _WEIGHT_STEP_KG).quantize(_CENTS, rounding=ROUND_HALF_UP)
    if billable > _MAX_BILLABLE_KG:
        raise ValueError(
            f"el peso facturable {billable} kg supera el máximo de "
            f"{_MAX_BILLABLE_KG} kg"
        )
    return billable


def shipping_cost(
    actual_kg: int | Decimal,
    length_cm: int | Decimal,
    width_cm: int | Decimal,
    height_cm: int | Decimal,
    zone: str,
    express: bool = False,
) -> Decimal:
    """Calcula la tarifa de envío del paquete.

    La tarifa es el precio base de la zona más el precio por kg aplicado al
    peso facturable. Con `express=True` el total se multiplica por 1.5. El
    resultado se redondea a dos decimales con `ROUND_HALF_UP`.

    Args:
        actual_kg: Peso real del paquete en kg.
        length_cm: Largo del paquete en centímetros.
        width_cm: Ancho del paquete en centímetros.
        height_cm: Alto del paquete en centímetros.
        zone: Zona de destino: "A", "B" o "C".
        express: Indica si se aplica el servicio express.

    Returns:
        La tarifa de envío, con dos decimales.

    Raises:
        TypeError: Si algún valor numérico no es `int` ni `Decimal`, o si
            `express` no es un `bool`.
        ValueError: Si algún valor no es mayor que cero, si `zone` no es una
            zona válida o si el peso facturable supera los 30 kg.

    Example:
        >>> shipping_cost(2, 30, 20, 10, "B")
        Decimal('11.10')
        >>> shipping_cost(2, 30, 20, 10, "B", express=True)
        Decimal('16.65')
    """
    if not isinstance(zone, str) or zone not in _ZONE_RATES:
        raise ValueError(f"zone debe ser 'A', 'B' o 'C', recibido: {zone!r}")
    if not isinstance(express, bool):
        raise TypeError(f"express debe ser bool, no {type(express).__name__}")

    base_price, price_per_kg = _ZONE_RATES[zone]
    billable = billable_weight(actual_kg, length_cm, width_cm, height_cm)
    total = base_price + price_per_kg * billable
    if express:
        total = total * _EXPRESS_MULTIPLIER
    return total.quantize(_CENTS, rounding=ROUND_HALF_UP)
