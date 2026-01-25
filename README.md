# Welcome to pyos_data_validation

|        |        |
|--------|--------|
| Package | [![Latest PyPI Version](https://img.shields.io/pypi/v/pyos_data_validation.svg)](https://pypi.org/project/pyos_data_validation/) [![Supported Python Versions](https://img.shields.io/pypi/pyversions/pyos_data_validation.svg)](https://pypi.org/project/pyos_data_validation/)  |
| Meta   | [![Code of Conduct](https://img.shields.io/badge/Contributor%20Covenant-v2.0%20adopted-ff69b4.svg)](CODE_OF_CONDUCT.md) |


`pyos_data_validation` is a lightweight Python package for defining, validating, and comparing **data contracts** for tabular datasets. It enables data scientists to formalize assumptions about their data—such as schema, missingness constraints, numeric ranges, and categorical domains—and to automatically validate new datasets against those expectations. The package supports reproducible workflows and CI-friendly automation by producing structured validation outputs and clear, actionable error messages suitable for use in unit tests and GitHub Actions.

---

## Functions included

- **`infer_contract(df, *, config=...) -> Contract`**  
  Infers a data contract from a pandas DataFrame by learning expected column types, acceptable missingness levels, numeric bounds (e.g., quantile-based), and categorical domains up to a configurable cardinality. This provides a fast, data-driven starting point for contract-first validation in new projects.

- **`validate_contract(df, contract, *, strict=True) -> ValidationResult`**  
  Validates a DataFrame against a `Contract` by checking for missing or extra columns, dtype mismatches, missingness violations, out-of-range numeric values, and unseen categorical levels. Returns a structured `ValidationResult` containing overall pass/fail status along with per-column errors and warnings.

- **`compare_contracts(contract_a, contract_b) -> DriftReport`**  
  Compares two contracts (for example, a “training” contract versus a “latest” contract) to identify schema drift (added or removed columns, dtype changes) and distribution drift (numeric range shifts or categorical churn). Produces a `DriftReport` summarizing what changed and the severity of those changes.

- **`summarize_violations(result, *, top_k=5, weights=None) -> Summary`**  
  Converts a `ValidationResult` into an actionable summary by ranking columns by severity, grouping issues by type (schema, missingness, or distribution), and highlighting the most critical failures to address first. This supports concise reporting in CI logs and pull requests without being limited to simple formatting.


The `pyos_data_validation` package is inspired by existing data quality and schema-validation tools such as Pandera, Great Expectations, and Pydantic. Pandera and Great Expectations provide powerful, production-grade frameworks for defining and validating data expectations on tabular datasets, while Pydantic focuses on validating structured Python objects and API inputs. In contrast, `pyos_data_validation` is intentionally lightweight and educational in scope, focusing on a minimal set of abstractions—data contracts, validation results, and contract comparison—to support small projects, teaching, and CI-friendly workflows. Unlike production-grade tools, this package prioritizes clarity and minimal abstractions over completeness.


## Get started

You can install this package locally into your preferred Python environment using pip:

    $ pip install -e .

### Basic usage

A typical workflow is to infer a contract from an existing dataset and then validate
new data against it.

```python
    import pandas as pd
    from pyos_data_validation.infer_contract import infer_contract
    from pyos_data_validation.validate_contract import validate_contract

    # example data
    df = pd.DataFrame({
        "age": [23, 45, 31],
        "income": [50000, 72000, 61000],
        "city": ["A", "B", "A"],
    })

    # infer a contract from the data
    contract = infer_contract(df)

    # validate the same (or new) data against the contract
    result = validate_contract(df, contract)

    print(result.ok)
    print(result.issues)
```

The validation result contains a boolean pass/fail flag and a list of issues describing
any contract violations. This makes the package suitable for lightweight data checks
and CI-friendly workflows.


## Contributors
- Manikanth Goud Gurujala 
- Eduardo Rafael Sanchez Martinez
- Yonas Gebre Marie
- Rahiq Raees

## Copyright

- Copyright © 2026 Eduardo, Yonas, Manikanth, Rahiq.
- Free software distributed under the [MIT License](./LICENSE).
