# Refined summarize_violations Specification
# (Incorporating LLM Review Feedback)

from typing import Optional, Dict, Union
from data_validation.types import ValidationResult, Summary
from collections import Counter

def summarize_violations(
    result: ValidationResult, 
    *, 
    top_k: int = 5, 
    weights: Optional[Dict[str, Union[int, float]]] = None
) -> Summary:
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
        'missingness', 'range', 'category') and values should be positive
        numeric weights (int or float, higher = more severe). 
        
        If None, default weights are used:
        
        - missing_column: 10 (most severe)
        - extra_column: 8
        - dtype: 7
        - range: 5
        - category: 5
        - missingness: 3
        
        If a custom weights dict is provided, it completely replaces the
        default weights. Issue kinds not in the custom dict will default
        to weight 1. To override only specific kinds while keeping other
        defaults, explicitly include all desired weights.
    
    Returns
    -------
    Summary
        An actionable summary containing:
        
        - ``ok`` : bool
            True if there are no issues (same as result.ok).
        - ``top_issues`` : List[Issue]
            The top_k most severe issues, ranked by weighted severity.
            If fewer than top_k issues exist, returns all issues.
            If no issues exist, returns an empty list.
        - ``counts_by_kind`` : Dict[str, int]
            Count of issues grouped by their kind (e.g., {'dtype': 2, 
            'missingness': 1, 'range': 3}). Empty dict if no issues.
    
    Raises
    ------
    TypeError
        If result is not a ValidationResult instance.
        If weights is not a dict or None.
    ValueError
        If top_k is not a positive integer.
        If weights contains non-numeric values.
        If weights contains negative or zero values.
    
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
    
    1. Column name (dataset-level issues with column=None sort first, 
       then alphabetically)
    2. Kind (alphabetically)
    3. Original order in result.issues
    
    Examples
    --------
    Basic usage with default weights:
    
    >>> from data_validation import validate_contract, summarize_violations
    >>> result = validate_contract(df, contract)
    >>> summary = summarize_violations(result, top_k=3)
    >>> print(f"Found {len(summary.top_issues)} critical issues")
    Found 3 critical issues
    >>> for issue in summary.top_issues:
    ...     if issue.column:
    ...         print(f"  - {issue.column}: {issue.message}")
    ...     else:
    ...         print(f"  - {issue.message}")
      - age: value out of expected range
      - status: unknown category 'inactive'
      - salary: 12% missing values exceeds limit
    
    Using counts for quick overview:
    
    >>> print(summary.counts_by_kind)
    {'range': 3, 'dtype': 2, 'missingness': 1}
    >>> if summary.counts_by_kind.get('missing_column', 0) > 0:
    ...     print("Critical: Missing required columns!")
    
    Custom weights to prioritize specific issue types:
    
    >>> # Prioritize range violations
    >>> summary = summarize_violations(
    ...     result, 
    ...     top_k=5,
    ...     weights={
    ...         'missing_column': 10,
    ...         'dtype': 10,
    ...         'range': 20,  # Highest priority
    ...         'category': 5,
    ...         'missingness': 5
    ...     }
    ... )
    >>> summary.top_issues[0].kind
    'range'
    
    Handling validation success (no issues):
    
    >>> result = ValidationResult(ok=True, issues=[])
    >>> summary = summarize_violations(result)
    >>> summary.ok
    True
    >>> len(summary.top_issues)
    0
    >>> summary.counts_by_kind
    {}
    """
    # Define default weights AT THE VERY START
    DEFAULT_WEIGHTS = {
        'missing_column': 10,
        'extra_column': 8,
        'dtype': 7,
        'range': 5,
        'category': 5,
        'missingness': 3
    }
    
    # Input validation - result type
    if not isinstance(result, ValidationResult):
        raise TypeError("result must be a ValidationResult instance")
    
    # Input validation - top_k type
    if not isinstance(top_k, int):
        raise TypeError("top_k must be an integer")
    
    # Input validation - top_k value
    if top_k <= 0:
        raise ValueError("top_k must be a positive integer")
    
    # Input validation - weights type and values
    if weights is not None:
        if not isinstance(weights, dict):
            raise TypeError("weights must be a dict or None")
        
        for kind, weight in weights.items():
            if not isinstance(weight, (int, float)):
                raise ValueError(
                    f"Weight for '{kind}' must be numeric, got {type(weight).__name__}"
                )
            if weight <= 0:
                raise ValueError(
                    f"Weight for '{kind}' must be positive, got {weight}"
                )
    
    # Determine which weights to use
    if weights is None:
        weights_to_use = DEFAULT_WEIGHTS
    else:
        # Custom weights completely replace defaults
        weights_to_use = weights
    
    # Handle empty results
    if not result.issues:
        return Summary(
            ok=result.ok,
            top_issues=[],
            counts_by_kind={}
        )
    
    # Count issues by kind - includes ALL issues, not just top_k
    counts_by_kind = dict(Counter(issue.kind for issue in result.issues))
    
    # Sort issues by severity
    # Tiebreaker: weight (descending), column (None first, then alphabetical), kind (alphabetical)
    def sort_key(issue):
        weight = weights_to_use.get(issue.kind, 1)  # Default to 1 for unknown kinds
        # Use tuple: (False, "") for None sorts before (True, "actual_name")
        if issue.column is None:
            column_sort = (False, "")
        else:
            column_sort = (True, issue.column)
        return (-weight, column_sort, issue.kind)
    
    sorted_issues = sorted(result.issues, key=sort_key)
    
    # Take top_k issues
    top_issues = sorted_issues[:top_k]
    
    return Summary(
        ok=result.ok,
        top_issues=top_issues,
        counts_by_kind=counts_by_kind
    )








