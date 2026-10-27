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
