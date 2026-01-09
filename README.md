# Welcome to data_validation

|        |        |
|--------|--------|
| Package | [![Latest PyPI Version](https://img.shields.io/pypi/v/data_validation.svg)](https://pypi.org/project/data_validation/) [![Supported Python Versions](https://img.shields.io/pypi/pyversions/data_validation.svg)](https://pypi.org/project/data_validation/)  |
| Meta   | [![Code of Conduct](https://img.shields.io/badge/Contributor%20Covenant-v2.0%20adopted-ff69b4.svg)](CODE_OF_CONDUCT.md) |

*TODO: the above badges that indicate python version and package version will only work if your package is on PyPI.
If you don't plan to publish to PyPI, you can remove them.*

`data_validation` is a lightweight Python package for defining, validating, and comparing **data contracts** for tabular datasets. It enables data scientists to formalize assumptions about their data—such as schema, missingness constraints, numeric ranges, and categorical domains—and to automatically validate new datasets against those expectations. The package supports reproducible workflows and CI-friendly automation by producing structured validation outputs and clear, actionable error messages suitable for use in unit tests and GitHub Actions.

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

- **`validate_and_fail(df, contract, *, policy=...) -> None`**  
  A CI-oriented helper that raises a typed exception when validation fails under a configurable policy (for example, treating warnings as errors or allowing limited drift). Designed for straightforward integration into automated testing and deployment pipelines.


## Get started

You can install this package into your preferred Python environment using pip:

```bash
$ pip install data_validation
```

TODO: Add a brief example of how to use the package to this section

To use data_validation in your code:

```python
>>> import data_validation
>>> data_validation.hello_world()
```

## Contributors
- Manikanth Goud Gurujala 
- Eduardo Rafael Sanchez Martinez
- Yonas Gebre Marie
- Rahiq Raees

## Copyright

- Copyright © 2026 Eduardo, Yonas, Manikanth, Rahiq.
- Free software distributed under the [MIT License](./LICENSE).
