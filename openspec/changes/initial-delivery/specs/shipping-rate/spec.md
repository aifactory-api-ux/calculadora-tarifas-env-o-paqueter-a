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
