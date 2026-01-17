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
    errors = []
    warnings = []
    column_details = {}

    df_columns = set(df.columns)
    contract_columns = set(contract.columns.keys())

    # --- Column presence checks ---
    required_columns = {
        col for col, rules in contract.columns.items() if rules.required
    }

    missing_columns = required_columns - df_columns
    extra_columns = df_columns - contract_columns

    if missing_columns:
        msg = f"Missing required columns: {missing_columns}"
        if strict:
            errors.append(msg)
        else:
            warnings.append(msg)

    if extra_columns and strict:
        errors.append(f"Unexpected extra columns: {extra_columns}")

    # --- Per-column validation ---
    for col, rules in contract.columns.items():
        column_details[col] = []

        if col not in df.columns:
            continue

        series = df[col]

        # --- Data type check ---
        if not pd.api.types.is_dtype_equal(series.dtype, rules.dtype):
            error = f"{col}: expected dtype {rules.dtype}, got {series.dtype}"
            errors.append(error)
            column_details[col].append(error)

        # --- Null check ---
        if not rules.allow_nulls and series.isnull().any():
            error = f"{col}: contains null values but nulls are not allowed"
            errors.append(error)
            column_details[col].append(error)

        # --- Numeric range check ---
        if rules.value_range is not None:
            if not pd.api.types.is_numeric_dtype(series):
                error = f"{col}: value_range specified but column is not numeric"
                errors.append(error)
                column_details[col].append(error)
            else:
                min_val, max_val = rules.value_range
                mask = series.dropna().between(min_val, max_val, inclusive="both")
                if not mask.all():
                    error = f"{col}: values found outside range {rules.value_range}"
                    errors.append(error)
                    column_details[col].append(error)

        # --- Categorical values check ---
        if rules.allowed_values is not None:
            invalid = set(series.dropna().unique()) - set(rules.allowed_values)
            if invalid:
                error = f"{col}: invalid categorical values {invalid}"
                errors.append(error)
                column_details[col].append(error)

    passed = len(errors) == 0

    return ValidationResult(
        passed=passed,
        errors=errors,
        warnings=warnings,
        column_details=column_details
    )