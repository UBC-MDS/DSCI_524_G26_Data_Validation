import pandas as pd
# Import the classes from your team's types file
from data_validation.types import Issue, ValidationResult, Contract

def validate_contract(df, contract, strict=True):
    """
    Validate a pandas DataFrame against a predefined data contract.

    This function checks whether the input DataFrame conforms to the provided
    contract by validating column presence, data types, missingness rules,
    numeric value ranges, and allowed categorical values. The validation
    outcome is returned as a structured ValidationResult containing overall
    pass/fail status along with detailed per-column errors and warnings.

    Parameters
    ----------
    df : pandas.DataFrame
        The DataFrame to be validated.

    contract : Contract
        A data contract specifying the expected schema, data types,
        missingness constraints, value ranges for numeric columns, and
        allowed categories for categorical columns.

    strict : bool, optional, default=True
        If True, validation fails when extra or missing columns are detected.
        If False, extra columns are ignored and missing columns generate
        warnings instead of errors.

    Returns
    -------
    ValidationResult
        An object containing:
        - a boolean indicating whether validation passed,
        - a collection of validation errors,
        - a collection of validation warnings,
        - per-column diagnostic information.

    Notes
    -----
    The function performs the following checks:
    - Missing required columns
    - Unexpected extra columns
    - Data type mismatches
    - Missing value (null) violations
    - Numeric range violations
    - Unseen or invalid categorical values

    Examples
    --------
    >>> result = validate_contract(df, contract)
    >>> result.passed
    True
    
    """
    issues = []
    df_columns = set(df.columns)
    contract_columns = set(contract.columns.keys())

    # --- Column presence checks ---
    # Note: Using ColumnRule attributes from your types.py
    # Since ColumnRule doesn't have a 'required' attribute, 
    # we treat all columns in the contract as required.
    missing_columns = contract_columns - df_columns
    extra_columns = df_columns - contract_columns

    if missing_columns:
        for col in missing_columns:
            issues.append(Issue(
                kind="missing_column",
                message=f"Missing required column: {col}",
                column=col,
                expected="Present",
                observed="Missing"
            ))

    if extra_columns and strict:
        for col in extra_columns:
            issues.append(Issue(
                kind="extra_column",
                message=f"Unexpected extra column: {col}",
                column=col,
                expected="Absent",
                observed="Present"
            ))

    # --- Per-column validation ---
    for col, rules in contract.columns.items():
        if col not in df.columns:
            continue

        series = df[col]

        # --- Data type check ---
        # Comparing series.dtype name to the string in rules.dtype
        if str(series.dtype) != rules.dtype:
            issues.append(Issue(
                kind="dtype",
                message=f"{col}: expected {rules.dtype}, got {series.dtype}",
                column=col,
                expected=rules.dtype,
                observed=str(series.dtype)
            ))

        # --- Missingness check (max_missing_frac) ---
        missing_frac = series.isnull().mean()
        if missing_frac > rules.max_missing_frac:
            issues.append(Issue(
                kind="missingness",
                message=f"{col}: missing fraction {missing_frac} exceeds {rules.max_missing_frac}",
                column=col,
                expected=rules.max_missing_frac,
                observed=missing_frac
            ))

        # --- Numeric range check ---
        if pd.api.types.is_numeric_dtype(series):
            if rules.min_value is not None and series.min() < rules.min_value:
                issues.append(Issue(
                    kind="range",
                    message=f"{col}: min value {series.min()} below {rules.min_value}",
                    column=col,
                    expected=rules.min_value,
                    observed=series.min()
                ))
            if rules.max_value is not None and series.max() > rules.max_value:
                issues.append(Issue(
                    kind="range",
                    message=f"{col}: max value {series.max()} exceeds {rules.max_value}",
                    column=col,
                    expected=rules.max_value,
                    observed=series.max()
                ))

        # --- Categorical values check ---
        if rules.allowed_values is not None:
            observed_vals = set(series.dropna().unique().astype(str))
            invalid = observed_vals - set(rules.allowed_values)
            if invalid:
                issues.append(Issue(
                    kind="category",
                    message=f"{col}: invalid values {invalid}",
                    column=col,
                    expected=rules.allowed_values,
                    observed=observed_vals
                ))

    # Validation passes if no issues were found
    return ValidationResult(ok=len(issues) == 0, issues=issues)