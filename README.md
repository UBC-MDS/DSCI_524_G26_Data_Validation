# Welcome to pyos_data_validation

|        |        |
|--------|--------|
| Package | [![TestPyPI](https://img.shields.io/badge/TestPyPI-0.1.4-blue)](https://test.pypi.org/project/pyos-data-validation/) [![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)](https://test.pypi.org/project/pyos-data-validation/) |
| CI / Release | [![Release to TestPyPI](https://github.com/UBC-MDS/DSCI_524_G26_Data_Validation/actions/workflows/release.yml/badge.svg?branch=main)](https://github.com/UBC-MDS/DSCI_524_G26_Data_Validation/actions/workflows/release.yml) [![codecov](https://codecov.io/gh/UBC-MDS/DSCI_524_G26_Data_Validation/branch/main/graph/badge.svg)](https://codecov.io/gh/UBC-MDS/DSCI_524_G26_Data_Validation) |
| Meta   | [![Code of Conduct](https://img.shields.io/badge/Contributor%20Covenant-v2.0%20adopted-ff69b4.svg)](CODE_OF_CONDUCT.md) |
| Documentation | [View Full Documentation](https://ubc-mds.github.io/DSCI_524_G26_Data_Validation/) |

`pyos_data_validation` is a lightweight Python package for defining, validating, and comparing **data contracts** for tabular datasets. It enables data scientists to formalize assumptions about their data—such as schema, missingness constraints, numeric ranges, and categorical domains—and to automatically validate new datasets against those expectations. The package supports reproducible workflows and CI-friendly automation by producing structured validation outputs and clear, actionable error messages suitable for use in unit tests and GitHub Actions.

---

## Table of Contents
- [Function Reference](#function-reference)
- [Quick Start](#get-started)
- [Usage Examples](#usage-examples)
- [Developer Guide](#developer-guide)
- [Contributors](#contributors)

---

## Function Reference

### Overview

| Function | Purpose | Primary Input | Primary Output | Use Case |
|----------|---------|---------------|----------------|----------|
| [`infer_contract()`](#infer_contract) | Learn data contract from existing data | DataFrame | `Contract` | Bootstrap validation rules from sample data |
| [`validate_contract()`](#validate_contract) | Validate data against a contract | DataFrame + Contract | `ValidationResult` | Check if new data meets expectations |
| [`compare_contracts()`](#compare_contracts) | Detect schema and distribution drift | Two Contracts | `DriftReport` | Monitor data evolution over time |
| [`summarize_violations()`](#summarize_violations) | Rank and group validation issues | ValidationResult | `Summary` | Prioritize data quality fixes |

---

### `infer_contract()`

Infers a data contract from a pandas DataFrame by automatically learning column types, acceptable missingness levels, numeric bounds, and categorical domains.

**Signature**:
```python
infer_contract(df: pd.DataFrame) -> Contract
```

**Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `df` | `pd.DataFrame` | Yes | - | The input DataFrame to analyze and create a contract from |

**Returns**:

| Type | Description |
|------|-------------|
| `Contract` | A contract object containing schema definitions, column types, value constraints, and validation rules |

**Contract Object Structure**:
```python
Contract(
    columns={
        'column_name': ColumnRule(
            dtype='int64',                      # Inferred data type as string
            max_missing_frac=0.05,              # Observed missing fraction
            min_value=10,                       # Minimum value (numeric only)
            max_value=100,                      # Maximum value (numeric only)
            allowed_values={'A', 'B', 'C'}      # Unique values (categorical only)
        ),
        # ... more columns
    }
)
```

**Inference Behavior**:

| Column Type | dtype | max_missing_frac | min_value / max_value | allowed_values |
|-------------|-------|------------------|------------------------|----------------|
| **Numeric** (int, float) | String representation of dtype | Fraction of NaN values | Min and max of non-null values | `None` |
| **String/Object** | `'object'`, `'str'`, or `'string'` | Fraction of NaN values | `None` | Set of unique non-null values (as strings) |
| **Boolean** | `'bool'` | Fraction of NaN values | `None` | Set of unique values (as strings) |
| **Categorical** | `'category'` | Fraction of NaN values | `None` | Set of unique values (as strings) |

**Raises**:

| Exception | When |
|-----------|------|
| `TypeError` | If `df` is not a pandas DataFrame |

**Example**:
```python
import pandas as pd
from pyos_data_validation.infer_contract import infer_contract

# Sample data
df = pd.DataFrame({
    "age": [23, 45, 31, 28, 52],
    "income": [50000, 72000, 61000, 58000, 95000],
    "city": ["NYC", "SF", "NYC", "LA", "SF"],
    "score": [8.5, 9.2, 7.8, 8.1, 9.5]
})

# Infer contract from data
contract = infer_contract(df)

# Access contract details
print(contract.columns['age'].dtype)           # 'int64'
print(contract.columns['age'].min_value)       # 23
print(contract.columns['age'].max_value)       # 52
print(contract.columns['city'].allowed_values) # {'NYC', 'SF', 'LA'}
print(contract.columns['score'].min_value)     # 7.8

# Check missingness
print(contract.columns['age'].max_missing_frac) # 0.0 (no missing values)
```

---

### `validate_contract()`

Validates a DataFrame against a contract by checking for schema compliance, type mismatches, missingness violations, range violations, and unexpected categorical values. All columns defined in the contract are treated as required.

**Signature**:
```python
validate_contract(
    df: pd.DataFrame,
    contract: Contract,
    strict: bool = True
) -> ValidationResult
```

**Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `df` | `pd.DataFrame` | Yes | - | The DataFrame to validate |
| `contract` | `Contract` | Yes | - | The contract defining expected schema and constraints |
| `strict` | `bool` | No | `True` | If `True`, extra columns cause validation issues; if `False`, extra columns are ignored |

**Returns**:

| Type | Description |
|------|-------------|
| `ValidationResult` | Object containing validation status and list of issues |

**ValidationResult Object Structure**:
```python
ValidationResult(
    ok=True,  # False if any validation issues occurred
    issues=[
        Issue(
            kind='missing_column' | 'extra_column' | 'dtype' | 
                 'missingness' | 'range' | 'category',
            message='Detailed description of the issue',
            column='column_name',  # or None for dataset-level issues
            expected=<expected_value>,
            observed=<observed_value>
        ),
        # ... more issues
    ]
)
```

**Validation Checks Performed**:

| Check Type | `kind` Value | Description | Fails Validation? |
|------------|--------------|-------------|-------------------|
| Missing columns | `'missing_column'` | Expected columns not present in DataFrame | Yes |
| Extra columns | `'extra_column'` | DataFrame has columns not in contract | Yes (if `strict=True`) |
| Dtype mismatches | `'dtype'` | Column type doesn't match contract (with normalization for string types) | Yes |
| Missingness violations | `'missingness'` | Missing value fraction exceeds `max_missing_frac` | Yes |
| Range violations | `'range'` | Numeric values outside `[min_value, max_value]` | Yes |
| Category violations | `'category'` | Categorical values not in `allowed_values` | Yes |

**Type Normalization**:
- String types (`'object'`, `'str'`, `'string'`) are treated as equivalent
- Other dtypes must match exactly

**Example**:
```python
import pandas as pd
from pyos_data_validation.validate_contract import validate_contract

# Assume we have an inferred contract from training data
df_new = pd.DataFrame({
    "age": [25, 150, 30],        # 150 violates range
    "income": [52000, 68000, 59000],
    "city": ["NYC", "Paris", "SF"],  # "Paris" not in allowed_values
})

# Validate with strict mode (default)
result = validate_contract(df_new, contract, strict=True)

if result.ok:
    print("✓ Validation passed!")
else:
    print(f"✗ Validation failed with {len(result.issues)} issues:")
    for issue in result.issues:
        print(f"  [{issue.kind}] {issue.column}: {issue.message}")

# Example output:
# ✗ Validation failed with 2 issues:
#   [range] age: age: max value 150 exceeds 52
#   [category] city: city: invalid values {'Paris'}

# Validate with non-strict mode (extra columns allowed)
df_extra = df_new.copy()
df_extra['extra_col'] = [1, 2, 3]

result_lenient = validate_contract(df_extra, contract, strict=False)
print(f"Strict mode would have {len(result.issues)} issues")
print(f"Non-strict mode has {len(result_lenient.issues)} issues")
```

**Accessing Issue Details**:
```python
# Get all issues of a specific kind
dtype_issues = [issue for issue in result.issues if issue.kind == 'dtype']

# Get all issues for a specific column
age_issues = [issue for issue in result.issues if issue.column == 'age']

# Print detailed information
for issue in result.issues:
    print(f"Column: {issue.column}")
    print(f"Type: {issue.kind}")
    print(f"Expected: {issue.expected}")
    print(f"Observed: {issue.observed}")
    print(f"Message: {issue.message}")
    print("---")
```

---

### `compare_contracts()`

Compares two contracts to identify schema drift (structural changes) and constraint drift (value range or domain changes). Useful for monitoring data evolution between training and production datasets.

**Signature**:
```python
compare_contracts(
    contract_a: Contract,
    contract_b: Contract
) -> DriftReport
```

**Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `contract_a` | `Contract` | Yes | - | The baseline contract (e.g., from training data) |
| `contract_b` | `Contract` | Yes | - | The comparison contract (e.g., from new/production data) |

**Returns**:

| Type | Description |
|------|-------------|
| `DriftReport` | Object containing detected drift categorized by type |

**DriftReport Object Structure**:
```python
DriftReport(
    added_columns=set(),           # Columns in contract_b but not in contract_a
    removed_columns=set(),         # Columns in contract_a but not in contract_b
    dtype_changes={},              # {column: (old_dtype, new_dtype)}
    range_changes=set(),           # Columns with min_value or max_value changes
    category_changes=set(),        # Columns with allowed_values changes
    missingness_changes={}         # {column: (old_max_missing_frac, new_max_missing_frac)}
)
```

**Drift Detection Logic**:

| Drift Type | Field | Detection Criteria |
|------------|-------|-------------------|
| **Column additions** | `added_columns` | Column exists in `contract_b.columns` but not in `contract_a.columns` |
| **Column removals** | `removed_columns` | Column exists in `contract_a.columns` but not in `contract_b.columns` |
| **Type changes** | `dtype_changes` | For shared columns, `dtype` differs between contracts |
| **Range changes** | `range_changes` | For shared columns (same dtype), `min_value` or `max_value` differs |
| **Category changes** | `category_changes` | For shared columns (same dtype), `allowed_values` differs |
| **Missingness changes** | `missingness_changes` | For shared columns, `max_missing_frac` differs |

**Important Notes**:
- Range and category changes are only detected when dtypes match between contracts
- The comparison is directional: "added" means present in `contract_b` only
- All fields return empty collections when no drift is detected

**Raises**:

| Exception | When |
|-----------|------|
| `TypeError` | If either contract is not a `Contract` instance |
| `TypeError` | If any column rule is not a `ColumnRule` instance |
| `ValueError` | If `max_missing_frac` is not numeric or outside [0, 1] range |
| `ValueError` | If `min_value` exceeds `max_value` for any column |

**Example**:
```python
from pyos_data_validation.compare_contracts import compare_contracts

# Training data contract (January)
df_train = pd.DataFrame({
    "age": [23, 45, 31, 28],
    "income": [50000, 72000, 61000, 58000],
    "city": ["NYC", "SF", "NYC", "LA"]
})
contract_train = infer_contract(df_train)

# Production data contract (6 months later)
df_prod = pd.DataFrame({
    "age": [22, 48, 35, 29, 95],           # Age range expanded
    "income": [51000, 73000, 62000, 59000, 120000],  # Income range expanded
    "city": ["NYC", "SF", "Berlin", "LA", "Tokyo"],  # New cities
    "subscription_tier": ["basic", "premium", "basic", "premium", "premium"]  # New column
})
contract_prod = infer_contract(df_prod)

# Compare contracts
drift = compare_contracts(contract_train, contract_prod)

# Check for schema drift
print(f"New columns: {drift.added_columns}")
# Output: {'subscription_tier'}

print(f"Removed columns: {drift.removed_columns}")
# Output: set()

print(f"Type changes: {drift.dtype_changes}")
# Output: {}

# Check for distribution drift
print(f"Range changes: {drift.range_changes}")
# Output: {'age', 'income'}

print(f"Category changes: {drift.category_changes}")
# Output: {'city'}

print(f"Missingness changes: {drift.missingness_changes}")
# Output: {} (if missingness rates are the same)

# Programmatic drift detection
has_schema_drift = bool(
    drift.added_columns or 
    drift.removed_columns or 
    drift.dtype_changes
)

has_distribution_drift = bool(
    drift.range_changes or 
    drift.category_changes or 
    drift.missingness_changes
)

if has_schema_drift:
    print("⚠️  Schema drift detected - model retraining may be required")

if has_distribution_drift:
    print("📊 Distribution drift detected - monitor model performance")
```

**Accessing Detailed Drift Information**:
```python
# Examine dtype changes in detail
for col, (old_dtype, new_dtype) in drift.dtype_changes.items():
    print(f"{col}: {old_dtype} → {new_dtype}")

# Examine missingness changes in detail
for col, (old_frac, new_frac) in drift.missingness_changes.items():
    change_pct = (new_frac - old_frac) / old_frac * 100
    print(f"{col}: missingness changed by {change_pct:.1f}%")

# Check specific columns for range drift
if 'age' in drift.range_changes:
    old_range = (contract_train.columns['age'].min_value, 
                 contract_train.columns['age'].max_value)
    new_range = (contract_prod.columns['age'].min_value, 
                 contract_prod.columns['age'].max_value)
    print(f"Age range changed from {old_range} to {new_range}")
```
---

### `summarize_violations()`

Converts a ValidationResult into an actionable summary by ranking issues by severity, counting issues by type, and highlighting the most critical problems to address first.

**Signature**:
```python
summarize_violations(
    result: ValidationResult,
    *,
    top_k: int = 5,
    weights: Optional[Dict[str, Union[int, float]]] = None
) -> Summary
```

**Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `result` | `ValidationResult` | Yes | - | The validation result to summarize |
| `top_k` | `int` | No | `5` | Number of top issues to highlight (must be positive) |
| `weights` | `Dict[str, Union[int, float]]` | No | `None` | Custom weights for issue severity ranking |

**Default Weights** (when `weights=None`):

| Issue Kind | Weight | Rationale |
|------------|--------|-----------|
| `missing_column` | 10 | Most severe - data cannot be processed |
| `extra_column` | 8 | High - unexpected data structure |
| `dtype` | 7 | High - may cause runtime errors |
| `range` | 5 | Medium - data quality issue |
| `category` | 5 | Medium - unexpected values |
| `missingness` | 3 | Low-Medium - may affect analysis |

**Custom Weights Behavior**:
- If `weights` is provided, it **completely replaces** the defaults
- Issue kinds not in the custom dict default to weight `1`
- All weights must be positive numeric values

**Returns**:

| Type | Description |
|------|-------------|
| `Summary` | Object containing prioritized issues and statistics |

**Summary Object Structure**:
```python
Summary(
    ok=True,                    # Same as result.ok
    top_issues=[...],           # Top K most severe issues (sorted by weight)
    counts_by_kind={            # Count of issues by kind
        'dtype': 2,
        'range': 3,
        'category': 1
    }
)
```

**Sorting Logic**:

Issues are sorted by the following criteria (in order):
1. **Weight** (descending) - Higher weight = higher priority
2. **Column name** - Issues with `column=None` sort first, then alphabetically
3. **Kind** (alphabetically)

**Raises**:

| Exception | When |
|-----------|------|
| `TypeError` | If `result` is not a `ValidationResult` instance |
| `TypeError` | If `top_k` is not an integer |
| `TypeError` | If `weights` is not a dict or None |
| `ValueError` | If `top_k` is not positive |
| `ValueError` | If any weight value is non-numeric |
| `ValueError` | If any weight value is not positive |

**Example - Basic Usage**:
```python
from pyos_data_validation.summarize_violations import summarize_violations

# Assume we have validation results with issues
result = validate_contract(df_messy, contract)

# Basic summary with default settings
summary = summarize_violations(result)

print(f"Validation passed: {summary.ok}")
print(f"Total issues: {len(result.issues)}")

# Show top 5 most severe issues
print("\n Top Issues to Fix:")
for i, issue in enumerate(summary.top_issues, 1):
    print(f"{i}. [{issue.kind}] {issue.column}: {issue.message}")

# Example output:
#  Top Issues to Fix:
# 1. [missing_column] user_id: Missing required column: user_id
# 2. [extra_column] debug_flag: Unexpected extra column: debug_flag
# 3. [dtype] age: age: expected int64, got object
# 4. [range] salary: salary: max value 250000 exceeds 150000
# 5. [category] status: status: invalid values {'archived'}

# Group by issue type
print("\n📊 Issues by Type:")
for kind, count in summary.counts_by_kind.items():
    print(f"  {kind}: {count}")

# Example output:
# 📊 Issues by Type:
#   missing_column: 1
#   extra_column: 1
#   dtype: 2
#   range: 3
#   category: 1
```

---


## Comparison with Other Tools

`pyos_data_validation` is inspired by production-grade data validation frameworks but serves a different purpose:

| Feature | pyos_data_validation | [Pandera](https://pandera.readthedocs.io/) | [Great Expectations](https://greatexpectations.io/) | [Pydantic](https://docs.pydantic.dev/) |
|---------|---------------------|---------|-------------------|----------|
| **Target Use Case** | Educational, lightweight validation | Production data validation | Enterprise data quality | API input validation |
| **Learning Curve** | Low | Medium | High | Low-Medium |
| **Contract Inference** |  Automatic |  Limited |  Profiling |  Manual only |
| **Drift Detection** |  Built-in |  No |  Via profiling |  No |
| **Tabular Data Focus** |  Yes | Yes | Yes | No (objects) |
| **CI/CD Friendly** | Simple integration | Yes |  Complex setup |  Yes |
| **Minimal Dependencies** |  pandas only |  Medium |  Heavy |  Minimal |
| **Validation Customization** |  Basic |  Extensive |  Extensive |  Extensive |

**When to use pyos_data_validation:**
- Small to medium projects
- Educational purposes and learning data validation concepts
- Quick prototyping of validation logic
- Lightweight CI/CD checks without complex infrastructure
- When you need simple drift detection out of the box

**When to use alternatives:**
- **[Pandera](https://pandera.readthedocs.io/)**: Production ML pipelines with complex validation rules and custom checks
- **[Great Expectations](https://greatexpectations.io/)**: Enterprise data quality monitoring with extensive reporting and data docs
- **[Pydantic](https://docs.pydantic.dev/)**: API request/response validation or configuration management with type safety

---

## Get started

You can install this package locally into your preferred Python environment using pip:

```bash
    pip install -e .
```

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

    print(result.passed)
    print(result.issues)
```

The validation result contains a boolean pass/fail flag and a list of issues describing
any contract violations. This makes the package suitable for lightweight data checks
and CI-friendly workflows.

---

## Developer Guide

This section is for contributors and developers working on the `pyos_data_validation` package.

### Setting up the development environment

Clone the repository:

```bash
git clone https://github.com/UBC-MDS/DSCI_524_G26_Data_Validation.git
```

Change the directory to the project:

```bash
cd DSCI_524_G26_Data_Validation
```

Create the conda environment:

```bash
conda env create -f environment.yml
```

Activate the environment: 

```bash
conda activate pyos_data_validation
```

Install the package in editable mode with development dependencies:

```bash
pip install -e ".[dev,tests,docs]"
```

### Running tests

Run the test suite with coverage:

```bash
pytest --cov=pyos_data_validation --cov-report=term --cov-branch
```

Run tests for a specific module:

```bash
pytest tests/unit/test_infer_contract.py -v
```

### Code quality checks

Check code style with ruff:

```bash
ruff check .
```

Format code with ruff:

```bash
ruff format .
```

### Building documentation

Generate the API reference documentation:

```bash
quartodoc build
```

Build the documentation locally using Quarto:

```bash
quarto render
```

The built documentation will be available in the `docs/` directory. You can open it in your browser:

```bash
open docs/index.html
```

### Preview documentation

To view the website after rendering from the terminal, run:

```bash
quarto preview
```


### Deploying documentation

Documentation is automatically built and deployed to GitHub Pages when changes are pushed to the `main` branch. The deployment is handled by the `.github/workflows/docs-publish.yml` workflow.

View the live documentation at: https://ubc-mds.github.io/DSCI_524_G26_Data_Validation/


## Contributors
- Manikanth Goud Gurujala 
- Eduardo Rafael Sanchez Martinez
- Yonas Gebre Marie
- Rahiq Raees

## Copyright

- Copyright © 2026 Eduardo, Yonas, Manikanth, Rahiq.
- Free software distributed under the [MIT License](./LICENSE).

## Support

- [Full Documentation](https://ubc-mds.github.io/DSCI_524_G26_Data_Validation/)
- [Issue Tracker](https://github.com/UBC-MDS/DSCI_524_G26_Data_Validation/issues)
- [Project Board](https://github.com/UBC-MDS/DSCI_524_G26_Data_Validation/projects?query=is%3Aopen)
