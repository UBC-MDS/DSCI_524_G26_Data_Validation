def compare_contracts(contract_a, contract_b):
    """
    Compare two data contracts to detect schema and constraint drift.

    This function compares a reference (baseline) contract against an observed
    (latest) contract and reports differences in:
    - schema: added/removed columns and dtype changes
    - constraints: numeric bound changes, categorical domain changes, and
      missingness threshold changes

    The comparison is directional:
    - "added" means present in contract_b but not in contract_a
    - "removed" means present in contract_a but not in contract_b
    - "old" refers to contract_a and "new" refers to contract_b

    Drift definitions
    -----------------
    - Added columns:
        column in contract_b.columns but not in contract_a.columns
    - Removed columns:
        column in contract_a.columns but not in contract_b.columns
    - Dtype changes:
        for columns present in both contracts, ColumnRule.dtype differs
        (reported as (old_dtype, new_dtype))
    - Range changes (numeric bounds):
        for columns present in both contracts, min_value and/or max_value differs
        (only meaningful when numeric bounds are provided; this function compares
        the stored contract values, not raw data)
    - Category changes:
        for columns present in both contracts, allowed_values differs
    - Missingness changes:
        for columns present in both contracts, max_missing_frac differs
        (reported as (old_max_missing_frac, new_max_missing_frac))

    Parameters
    ----------
    contract_a : Contract
        Reference contract representing the expected schema and constraints.

    contract_b : Contract
        Observed contract representing the latest schema and constraints.

    Returns
    -------
    DriftReport
        A report containing only detected differences between the two contracts:
        - added_columns, removed_columns
        - dtype_changes (col -> (old, new))
        - range_changes (set of columns whose min/max changed)
        - category_changes (set of columns whose allowed_values changed)
        - missingness_changes (col -> (old, new))

    Notes
    -----
    This function compares contract metadata only and does not inspect raw data.
    Drift is evaluated only for columns that exist in both contracts, except for
    added or removed columns detected via column name differences. Handling of
    optional fields (min_value, max_value, allowed_values) is implementation-
    defined; document your chosen rule if it matters for users.

    Raises
    ------
    TypeError
        If contract_a or contract_b is not a Contract instance, or if a column
        rule is not a ColumnRule instance.
    ValueError
        If max_missing_frac is non-numeric, outside [0, 1], or if min_value
        exceeds max_value.

    Examples
    --------
    >>> report = compare_contracts(contract_a, contract_b)
    >>> report.has_drift
    True
    >>> report.missingness_changes
    {'age': (0.05, 0.20)}
    """
    from pyos_data_validation.types import ColumnRule, Contract, DriftReport

    if not isinstance(contract_a, Contract) or not isinstance(contract_b, Contract):
        raise TypeError("contract_a and contract_b must be Contract instances")

    def validate_contract(contract):
        for column, rule in contract.columns.items():
            if not isinstance(rule, ColumnRule):
                raise TypeError(
                    f"Column rule for {column} must be a ColumnRule instance"
                )
            if not isinstance(rule.max_missing_frac, (int, float)):
                raise ValueError(f"max_missing_frac for {column} must be numeric")
            if rule.max_missing_frac < 0 or rule.max_missing_frac > 1:
                raise ValueError(
                    f"max_missing_frac for {column} must be between 0 and 1"
                )
            if rule.min_value is not None and rule.max_value is not None:
                if rule.min_value > rule.max_value:
                    raise ValueError(f"min_value cannot exceed max_value for {column}")

    validate_contract(contract_a)
    validate_contract(contract_b)

    columns_a = set(contract_a.columns.keys())
    columns_b = set(contract_b.columns.keys())

    added_columns = columns_b - columns_a
    removed_columns = columns_a - columns_b

    dtype_changes = {}
    range_changes = set()
    category_changes = set()
    missingness_changes = {}

    for column in columns_a & columns_b:
        rule_a = contract_a.columns[column]
        rule_b = contract_b.columns[column]

        if rule_a.dtype != rule_b.dtype:
            dtype_changes[column] = (rule_a.dtype, rule_b.dtype)

        if rule_a.dtype == rule_b.dtype:
            if (
                rule_a.min_value != rule_b.min_value
                or rule_a.max_value != rule_b.max_value
            ):
                range_changes.add(column)

            if rule_a.allowed_values != rule_b.allowed_values:
                category_changes.add(column)

        if rule_a.max_missing_frac != rule_b.max_missing_frac:
            missingness_changes[column] = (
                rule_a.max_missing_frac,
                rule_b.max_missing_frac,
            )

    return DriftReport(
        added_columns=added_columns,
        removed_columns=removed_columns,
        dtype_changes=dtype_changes,
        range_changes=range_changes,
        category_changes=category_changes,
        missingness_changes=missingness_changes,
    )
