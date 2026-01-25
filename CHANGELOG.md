# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Added `compare_contracts` function for detecting schema and constraint drift between data contracts.
- Added support for missingness drift detection (`max_missing_frac`).
- Added `has_drift` convenience property to `DriftReport`.

### Changed
- Improved `DriftReport` to include missingness-related changes.
- Updated documentation for `compare_contracts` with explicit drift definitions and directionality.
- Renamed the package in documentation/metadata to `pyos_data_validation`.

### Tests
- Added comprehensive unit tests for `compare_contracts`, covering schema drift, constraint drift, edge cases, and error handling.
- Added comprehensive unit tests for `validate_contract`, covering edge cases, and error handling.

## [0.1.0] - (1979-01-01)

- First release
