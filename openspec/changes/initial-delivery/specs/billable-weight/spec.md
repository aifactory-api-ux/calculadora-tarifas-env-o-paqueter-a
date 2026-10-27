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
