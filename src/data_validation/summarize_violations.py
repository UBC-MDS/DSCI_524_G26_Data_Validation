def summarize_violations(result, *, top_k=5, weights=None):
    """
    Convert a ValidationResult into an actionable summary.

    This function takes a validation result and produces a concise summary
    highlighting the most critical issues. Issues are ranked by severity
    (using the kind-based weights) and counted by type.

    Parameters
    ----------
    result : ValidationResult
        The validation result object to summarize, typically returned
        by the validate_contract function. Must contain a list of Issues.
    top_k : int, optional
        Number of top violations to highlight (default is 5). Must be
        a positive integer. Set to a higher value to see more issues,
        or lower for a quick overview.
    weights : dict, optional
        Custom weights for ranking violation severity by issue kind. 
        Keys should be issue kinds (e.g., 'missing_column', 'dtype', 
        'missingness', 'range', 'category') and values should be numeric 
        weights (higher = more severe). If None, default weights are used:
        
        - missing_column: 10 (most severe)
        - extra_column: 8
        - dtype: 7
        - range: 5
        - category: 5
        - missingness: 3
        
        Issues with unknown kinds default to weight 1.

    Returns
    -------
    Summary
        An actionable summary containing:
        
        - ``ok`` : bool
            True if there are no issues (same as result.ok).
        - ``top_issues`` : List[Issue]
            The top_k most severe issues, ranked by weighted severity.
            If fewer than top_k issues exist, returns all issues.
        - ``counts_by_kind`` : Dict[str, int]
            Count of issues grouped by their kind (e.g., {'dtype': 2, 
            'missingness': 1, 'range': 3}).

    Raises
    ------
    TypeError
        If result is not a ValidationResult instance.
        If weights is not a dict or None.
    ValueError
        If top_k is not a positive integer.
        If weights contains non-numeric values.

    See Also
    --------
    validate_contract : Validate a DataFrame against a contract.
    validate_and_fail : Validate and raise an exception on failure.

    Notes
    -----
    The severity ranking helps users prioritize which issues to fix first.
    Schema issues (missing/extra columns, dtype mismatches) are typically
    weighted higher than distribution issues (ranges, categories) since
    they represent more fundamental problems.
    
    When multiple issues have the same weight, they are ordered by:
    1. Column name (if present)
    2. Kind
    3. Original order in result.issues

    Examples
    --------
    >>> from data_validation import validate_contract, summarize_violations
    >>> result = validate_contract(df, contract)
    >>> summary = summarize_violations(result, top_k=3)
    >>> print(f"Found {len(summary.top_issues)} critical issues")
    Found 3 critical issues
    >>> for issue in summary.top_issues:
    ...     print(f"  - {issue.column}: {issue.message}")
      - age: value out of expected range
      - status: unknown category 'inactive'
      - salary: 12% missing values exceeds limit
    
    >>> # Use custom weights to prioritize range issues
    >>> summary = summarize_violations(
    ...     result, 
    ...     top_k=5,
    ...     weights={'range': 20, 'dtype': 10, 'missingness': 5}
    ... )
    >>> print(summary.counts_by_kind)
    {'range': 3, 'dtype': 2, 'missingness': 1}
    """
    pass
