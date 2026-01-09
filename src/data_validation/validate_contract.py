def validate_contract(df):
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