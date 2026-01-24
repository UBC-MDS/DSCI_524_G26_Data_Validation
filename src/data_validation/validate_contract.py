import pandas as pd
# Import the classes from your team's types file
from data_validation.types import Issue, ValidationResult, Contract

def validate_contract(df, contract, strict=True):
    """
    Validate a pandas DataFrame against a predefined data contract.

    This function validates an input DataFrame by comparing it against a
    contract that defines expected columns, data types, missingness
    thresholds, numeric value limits, and allowed categorical values.
    All columns defined in the contract are treated as required. Validation
    results are returned as a collection of structured issues describing
    any detected violations.

    Parameters
    ----------
    df : pandas.DataFrame
        The DataFrame to be validated.

    contract : Contract
        A data contract defining the expected columns and validation rules
        for each column, including:
        - expected data type (as a string),
        - maximum allowed fraction of missing values,
        - minimum and maximum values for numeric columns,
        - allowed categorical values.

    strict : bool, optional, default=True
        If True, the presence of extra columns in the DataFrame that are not
        defined in the contract is reported as validation issues. If False,
        extra columns are ignored.

    Returns
    -------
    ValidationResult
        An object containing:
        - a boolean flag (`ok`) indicating whether validation succeeded,
        - a list of Issue objects describing all detected validation problems.

    Notes
    -----
    The function performs the following checks:
    - Missing columns defined in the contract
    - Unexpected extra columns (when strict mode is enabled)
    - Data type mismatches based on dtype string comparison
    - Missingness violations based on maximum allowed missing fraction
    - Minimum and maximum value violations for numeric columns
    - Invalid or unseen categorical values

    Examples
    --------
    >>> result = validate_contract(df, contract)
    >>> result.ok
    True
    
    """
    issues = []
    df_columns = set(df.columns)
    contract_columns = set(contract.columns.keys())

    # --- Column presence checks ----
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
        # Treat "str" and "object" as equivalent for string columns
        observed_dtype = str(series.dtype)
        expected_dtype = rules.dtype
        
        # Normalize string types
        if observed_dtype in ("object", "str", "string") and expected_dtype in ("object", "str", "string"):
            # Both are string types, consider them matching
            pass
        elif observed_dtype != expected_dtype:
            issues.append(Issue(
                kind="dtype",
                message=f"{col}: expected {expected_dtype}, got {observed_dtype}",
                column=col,
                expected=expected_dtype,
                observed=observed_dtype
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