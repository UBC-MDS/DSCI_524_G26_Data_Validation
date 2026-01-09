def compare_contracts(contract_a, contract_b):
    """
    Compare two data contracts to detect schema and distribution drift.

    This function examines the differences between a baseline contract
    (for example, training data) and a new contract (for example, recent
    production data). It identifies schema drift such as added or removed
    columns and data type changes, along with distribution drift such as
    numeric range shifts or categorical domain churn.

    Parameters
    ----------
    contract_a : Contract
        The baseline contract representing expected schema and constraints.

    contract_b : Contract
        The comparison contract representing the latest observed schema
        and constraints.

    Returns
    -------
    DriftReport
        A structured report summarizing detected drift, including:
        - schema changes (added/removed columns, dtype changes),
        - distribution changes (range shifts, new/missing categories),
        - severity levels or categories for each change.

    Notes
    -----
    Typical usage compares a stable reference contract against a newly
    inferred contract to decide whether downstream model or pipeline
    retraining is required.

    Examples
    --------
    >>> report = compare_contracts(contract_a, contract_b)
    >>> report.has_drift
    True
    """
