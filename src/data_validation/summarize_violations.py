def summarize_violations(result, *, top_k=5, weights=None):
    """
    Convert a ValidationResult into an actionable summary.

    Ranks columns by severity, groups issues by type (schema vs missingness
    vs distribution), and highlights the most important failures to fix first.
    This supports concise reporting in CI logs and pull requests without
    being limited to simple formatting.

    Parameters
    ----------
    result : ValidationResult
        The validation result object to summarize, typically returned
        by the validate_contract function.
    top_k : int, optional
        Number of top violations to highlight (default is 5). Set to a 
        higher value to see more issues, or lower for a quick overview.
    weights : dict, optional
        Custom weights for ranking violation severity by type. Keys should
        be violation types ('schema', 'missingness', 'distribution') and 
        values should be numeric weights. If None, default weights are used.

    Returns
    -------
    Summary
        An actionable summary object containing:
        
        - ``top_violations`` : list
            The top_k most severe violations, ranked by severity.
        - ``by_type`` : dict
            Violations grouped by type (schema, missingness, distribution).
        - ``total_count`` : int
            Total number of violations found.
        - ``critical_columns`` : list
            Columns with the most severe issues to address first.

    See Also
    --------
    validate_contract : Validate a DataFrame against a contract.
    validate_and_fail : Validate and raise an exception on failure.

    Examples
    --------
    >>> from data_validation import validate_contract, summarize_violations
    >>> result = validate_contract(df, contract)
    >>> summary = summarize_violations(result, top_k=3)
    >>> print(summary.top_violations)
    ['age: out of range', 'status: unknown category', 'salary: 12% missing']
    """
    pass
