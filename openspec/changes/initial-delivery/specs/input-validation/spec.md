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
