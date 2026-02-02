# Refined summarize_violations Specification
# (Incorporating LLM Review Feedback)

from typing import Optional, Dict, Union
from pyos_data_validation.types import ValidationResult, Summary
from collections import Counter


def summarize_violations(
    result: ValidationResult,
    *,
    top_k: int = 5,
    weights: Optional[Dict[str, Union[int, float]]] = None,
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
    infer_contract : Infer a contract from a DataFrame.

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

    >>> import pandas as pd
    >>> from pyos_data_validation import infer_contract, validate_contract, summarize_violations
    >>>
    >>> # Create training data to establish contract
    >>> training_df = pd.DataFrame({
    ...     "age": [25, 40, 35],
    ...     "salary": [50000, 75000, 62000],
    ...     "department": ["HR", "Engineering", "Sales"]
    ... })
    >>>
    >>> # Infer contract from training data
    >>> contract = infer_contract(training_df)
    >>>
    >>> # Create test data with violations
    >>> test_df = pd.DataFrame({
    ...     "age": [30, 55, 22],  # 55 and 22 outside expected range
    ...     "salary": [58000, 72000, 45000],  # 45000 below minimum
    ...     "department": ["HR", "Sales", "Marketing"],  # Marketing not in contract
    ...     "bonus": [5000, 8000, 3000]  # Extra column not in contract
    ... })
    >>>
    >>> # Validate and get issues
    >>> result = validate_contract(test_df, contract)
    >>> summary = summarize_violations(result, top_k=3)
    >>>
    >>> print(f"Validation passed: {summary.ok}")
    Validation passed: False
    >>> print(f"Found {len(summary.top_issues)} critical issues")
    Found 3 critical issues
    >>>
    >>> # Show top issues by severity
    >>> for issue in summary.top_issues:
    ...     print(f"  - {issue.column}: {issue.kind}")
      - bonus: extra_column
      - age: range
      - age: range

    Using counts for quick overview of issue types:

    >>> print(summary.counts_by_kind)
    {'extra_column': 1, 'range': 3, 'category': 1}
    >>>
    >>> # Check for critical schema issues
    >>> if summary.counts_by_kind.get('missing_column', 0) > 0:
    ...     print("Critical: Missing required columns!")
    >>> if summary.counts_by_kind.get('extra_column', 0) > 0:
    ...     print("Warning: Extra columns detected")
    Warning: Extra columns detected

    Custom weights to prioritize specific issue types:

    >>> # Make range violations highest priority
    >>> custom_summary = summarize_violations(
    ...     result,
    ...     top_k=5,
    ...     weights={
    ...         'missing_column': 10,
    ...         'extra_column': 8,
    ...         'dtype': 7,
    ...         'range': 20,  # Highest priority!
    ...         'category': 5,
    ...         'missingness': 3
    ...     }
    ... )
    >>>
    >>> # Now range issues come first
    >>> print(f"Top issue type: {custom_summary.top_issues[0].kind}")
    Top issue type: range
    >>> print(f"Top issue column: {custom_summary.top_issues[0].column}")
    Top issue column: age

    Handling validation success (no issues):

    >>> # Valid data that passes all checks
    >>> valid_df = pd.DataFrame({
    ...     "age": [30, 42],
    ...     "salary": [58000, 72000],
    ...     "department": ["HR", "Sales"]
    ... })
    >>>
    >>> result = validate_contract(valid_df, contract)
    >>> summary = summarize_violations(result)
    >>>
    >>> print(f"Validation passed: {summary.ok}")
    Validation passed: True
    >>> print(f"Issues found: {len(summary.top_issues)}")
    Issues found: 0
    >>> print(f"Counts: {summary.counts_by_kind}")
    Counts: {}
    """

    # Define default weights AT THE VERY START
    DEFAULT_WEIGHTS = {
        "missing_column": 10,
        "extra_column": 8,
        "dtype": 7,
        "range": 5,
        "category": 5,
        "missingness": 3,
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
                raise ValueError(f"Weight for '{kind}' must be positive, got {weight}")

    # Determine which weights to use
    if weights is None:
        weights_to_use = DEFAULT_WEIGHTS
    else:
        # Custom weights completely replace defaults
        weights_to_use = weights

    # Handle empty results
    if not result.issues:
        return Summary(ok=result.ok, top_issues=[], counts_by_kind={})

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

    return Summary(ok=result.ok, top_issues=top_issues, counts_by_kind=counts_by_kind)
