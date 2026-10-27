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
