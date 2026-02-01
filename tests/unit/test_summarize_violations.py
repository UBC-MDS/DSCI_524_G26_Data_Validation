"""
Unit tests for summarize_violations function.

Tests cover basic functionality, edge cases, error handling, and specification compliance.
This test suite ensures that summarize_violations correctly prioritizes validation issues
by severity, handles various edge cases, and provides actionable summaries for debugging.

Improvements based on LLM review conducted 2026-01-16.
Enhanced documentation for Milestone 4 on 2026-01-31.
"""

import pytest
from pyos_data_validation.summarize_violations import summarize_violations
from pyos_data_validation.types import ValidationResult, Issue


# ============================================================================
# Basic Functionality Tests
# ============================================================================


def test_empty_result():
    """Test that empty ValidationResult returns empty Summary.
    
    When validation passes with no issues, summarize_violations should:
    - Return ok=True (matching the input result)
    - Return an empty top_issues list
    - Return an empty counts_by_kind dictionary
    
    This is the "happy path" scenario where all data is valid.
    """
    result = ValidationResult(ok=True, issues=[])

    summary = summarize_violations(result)

    assert summary.ok is True
    assert len(summary.top_issues) == 0
    assert summary.counts_by_kind == {}


def test_single_issue():
    """Test with one issue.
    
    With exactly one validation issue, summarize_violations should:
    - Return ok=False
    - Return that single issue in top_issues
    - Count that issue correctly in counts_by_kind
    
    This tests the minimal failing case.
    """
    issue = Issue(kind="dtype", message="Type mismatch", column="age")
    result = ValidationResult(ok=False, issues=[issue])

    summary = summarize_violations(result)

    assert summary.ok is False
    assert len(summary.top_issues) == 1
    assert summary.top_issues[0] == issue
    assert summary.counts_by_kind == {"dtype": 1}


def test_ok_field_matches_result():
    """Test that summary.ok matches result.ok.
    
    The summary's ok field should always mirror the validation result's ok field:
    - True when result.ok is True
    - False when result.ok is False
    
    This ensures consistency between validation results and summaries.
    """
    result_ok = ValidationResult(ok=True, issues=[])
    summary_ok = summarize_violations(result_ok)
    assert summary_ok.ok is True

    result_fail = ValidationResult(
        ok=False, issues=[Issue(kind="dtype", message="Error", column="col1")]
    )
    summary_fail = summarize_violations(result_fail)
    assert summary_fail.ok is False


# ============================================================================
# Top-k Functionality Tests
# ============================================================================


def test_top_k_limits_results():
    """Test that top_k limits the number of returned issues.
    
    The top_k parameter should:
    - Limit top_issues to the specified number
    - NOT affect counts_by_kind (which should include all issues)
    
    This is important for producing concise summaries while maintaining
    complete statistics about all issue types.
    """
    issues = [
        Issue(kind="dtype", message=f"Issue {i}", column=f"col{i}") for i in range(10)
    ]
    result = ValidationResult(ok=False, issues=issues)

    summary = summarize_violations(result, top_k=3)

    assert len(summary.top_issues) == 3
    # counts should still include all issues
    assert summary.counts_by_kind == {"dtype": 10}


def test_top_k_exceeds_issue_count():
    """Test that top_k larger than issue count returns all issues.
    
    When top_k is larger than the number of available issues:
    - Return all available issues
    - Do not pad with empty/null issues
    
    This prevents array index errors and handles small issue lists gracefully.
    """
    issues = [
        Issue(kind="dtype", message="Issue 1", column="col1"),
        Issue(kind="range", message="Issue 2", column="col2"),
    ]
    result = ValidationResult(ok=False, issues=issues)

    summary = summarize_violations(result, top_k=10)

    assert len(summary.top_issues) == 2
    assert summary.counts_by_kind == {"dtype": 1, "range": 1}


@pytest.mark.parametrize(
    "top_k,expected_count",
    [
        (1, 1),
        (3, 3),
        (5, 5),
        (7, 7),
        (100, 10),  # More than available
    ],
)
def test_top_k_various_values(top_k, expected_count):
    """Test top_k with various values using parametrization.
    
    This parametrized test verifies that top_k works correctly across
    a range of values, including edge cases like:
    - top_k = 1 (minimum)
    - top_k > number of issues (returns all)
    
    Ensures robust handling of different top_k parameters.
    """
    issues = [
        Issue(kind="dtype", message=f"Issue {i}", column=f"col{i}") for i in range(10)
    ]
    result = ValidationResult(ok=False, issues=issues)

    summary = summarize_violations(result, top_k=top_k)

    assert len(summary.top_issues) == min(expected_count, 10)


# ============================================================================
# Severity Ranking and Weights Tests
# ============================================================================


def test_severity_ranking():
    """Test that issues are ranked by severity using default weights.
    
    Default severity weights (higher = more severe):
    - missing_column: 10 (most severe)
    - extra_column: 8
    - dtype: 7
    - range: 5
    - category: 5
    - missingness: 3 (least severe)
    
    This test ensures schema-level issues (missing columns) are prioritized
    over distribution-level issues (missingness).
    """
    issues = [
        Issue(kind="missingness", message="Low severity", column="col1"),
        Issue(kind="missing_column", message="High severity", column="col2"),
        Issue(kind="range", message="Medium severity", column="col3"),
    ]
    result = ValidationResult(ok=False, issues=issues)

    summary = summarize_violations(result)

    # missing_column should be first (highest default weight = 10)
    assert summary.top_issues[0].kind == "missing_column"
    # missingness should be last (lowest default weight = 3)
    assert summary.top_issues[-1].kind == "missingness"


def test_custom_weights():
    """Test that custom weights override defaults.
    
    Users can provide custom weights to prioritize specific issue types
    based on their use case. For example, a user might care more about
    range violations than dtype mismatches.
    
    Custom weights completely replace the defaults.
    """
    issues = [
        Issue(kind="range", message="Should be first", column="col1"),
        Issue(kind="dtype", message="Should be second", column="col2"),
    ]
    result = ValidationResult(ok=False, issues=issues)

    # Give range higher weight than dtype
    summary = summarize_violations(result, weights={"range": 20, "dtype": 5})

    assert summary.top_issues[0].kind == "range"
    assert summary.top_issues[1].kind == "dtype"


def test_unknown_kind_defaults_to_weight_one():
    """Test that issue kinds not in custom weights default to weight 1.
    
    When custom weights are provided but don't cover all issue kinds:
    - Known kinds use their specified weights
    - Unknown kinds default to weight 1
    
    This ensures all issues are still ranked, even with partial weight
    specifications.
    """
    issues = [
        Issue(kind="custom_kind", message="Unknown", column="col1"),
        Issue(kind="dtype", message="Known", column="col2"),
    ]
    result = ValidationResult(ok=False, issues=issues)

    # Only specify dtype weight
    summary = summarize_violations(result, weights={"dtype": 10})

    # dtype should be first (weight 10 > 1)
    assert summary.top_issues[0].kind == "dtype"
    assert summary.top_issues[1].kind == "custom_kind"


def test_float_weights():
    """Test that float weights work correctly.
    
    Weights can be float values (not just integers), allowing for
    fine-grained severity tuning.
    
    This is useful when users need precise control over prioritization.
    """
    issues = [
        Issue(kind="range", message="Lower priority", column="col1"),
        Issue(kind="dtype", message="Higher priority", column="col2"),
    ]
    result = ValidationResult(ok=False, issues=issues)

    summary = summarize_violations(result, weights={"dtype": 10.5, "range": 3.2})

    assert summary.top_issues[0].kind == "dtype"


# ============================================================================
# Tiebreaker and Sorting Tests
# ============================================================================


def test_tiebreaker_ordering():
    """Test that issues with same weight are ordered by column, then kind.
    
    When multiple issues have the same severity weight, they are ordered by:
    1. Column name (None/null sorts first, then alphabetically)
    2. Kind (alphabetically)
    3. Original order in result.issues
    
    This deterministic tiebreaking ensures consistent, predictable results
    even when issues have equal severity.
    """
    issues = [
        Issue(kind="range", message="Msg 1", column="zebra"),
        Issue(kind="dtype", message="Msg 2", column="apple"),
        Issue(kind="range", message="Msg 3", column="apple"),
        Issue(kind="dtype", message="Msg 4", column=None),  # dataset-level
    ]
    result = ValidationResult(ok=False, issues=issues)

    # Give all same weight to test tiebreaking
    summary = summarize_violations(result, weights={"dtype": 5, "range": 5})

    # None column should sort first
    assert summary.top_issues[0].column is None
    assert summary.top_issues[0].kind == "dtype"

    # Then 'apple' before 'zebra'
    assert summary.top_issues[1].column == "apple"

    # Within 'apple', 'dtype' before 'range' (alphabetically)
    assert summary.top_issues[1].kind == "dtype"
    assert summary.top_issues[2].kind == "range"
    assert summary.top_issues[2].column == "apple"

    # Finally 'zebra'
    assert summary.top_issues[3].column == "zebra"


# ============================================================================
# counts_by_kind Tests
# ============================================================================


def test_counts_by_kind_with_multiple_kinds():
    """Test that counts_by_kind correctly groups diverse issues.
    
    The counts_by_kind dictionary should:
    - Group issues by their kind
    - Count each group accurately
    - Include all kinds present in the result
    
    This provides a high-level overview of issue distribution,
    useful for identifying patterns in validation failures.
    """
    issues = [
        Issue(kind="dtype", message="M1", column="col1"),
        Issue(kind="dtype", message="M2", column="col2"),
        Issue(kind="range", message="M3", column="col3"),
        Issue(kind="missing_column", message="M4", column="col4"),
        Issue(kind="missingness", message="M5", column="col5"),
        Issue(kind="missingness", message="M6", column="col6"),
        Issue(kind="missingness", message="M7", column="col7"),
    ]
    result = ValidationResult(ok=False, issues=issues)

    summary = summarize_violations(result)

    assert summary.counts_by_kind == {
        "dtype": 2,
        "range": 1,
        "missing_column": 1,
        "missingness": 3,
    }


def test_counts_by_kind_single_kind():
    """Test counts_by_kind with all issues of same kind.
    
    When all issues are of the same type, counts_by_kind should
    have a single entry with the correct total count.
    
    This edge case ensures the counting logic handles homogeneous
    issue lists correctly.
    """
    issues = [
        Issue(kind="dtype", message=f"Issue {i}", column=f"col{i}") for i in range(5)
    ]
    result = ValidationResult(ok=False, issues=issues)

    summary = summarize_violations(result)

    assert summary.counts_by_kind == {"dtype": 5}


# ============================================================================
# Error Handling Tests
# ============================================================================


def test_invalid_result_type():
    """Test that invalid result type raises TypeError.
    
    summarize_violations should only accept ValidationResult objects.
    Passing any other type should raise a clear TypeError.
    
    This prevents misuse and provides clear error messages.
    """
    with pytest.raises(TypeError):
        summarize_violations("not a result")


def test_negative_top_k():
    """Test that negative top_k raises ValueError.
    
    top_k must be a positive integer. Negative values don't make
    logical sense (can't return negative number of issues).
    """
    result = ValidationResult(ok=True, issues=[])

    with pytest.raises(ValueError):
        summarize_violations(result, top_k=-1)


def test_zero_top_k():
    """Test that top_k=0 raises ValueError.
    
    top_k must be at least 1. Zero doesn't make sense as it would
    return no issues, defeating the purpose of summarization.
    """
    result = ValidationResult(ok=True, issues=[])

    with pytest.raises(ValueError):
        summarize_violations(result, top_k=0)


def test_non_integer_top_k():
    """Test that non-integer top_k raises TypeError or ValueError.
    
    top_k must be an integer. Float or string values should be rejected
    even if they could be converted to integers.
    
    This enforces type safety and prevents ambiguous behavior.
    """
    result = ValidationResult(ok=True, issues=[])

    with pytest.raises((TypeError, ValueError)):
        summarize_violations(result, top_k=3.5)

    with pytest.raises((TypeError, ValueError)):
        summarize_violations(result, top_k="5")


def test_negative_weight_raises_error():
    """Test that negative weights raise ValueError.
    
    Weights represent severity and must be positive. Negative weights
    would create illogical prioritization.
    """
    result = ValidationResult(ok=True, issues=[])

    with pytest.raises(ValueError):
        summarize_violations(result, weights={"dtype": -5})


def test_zero_weight_raises_error():
    """Test that zero weights raise ValueError.
    
    Zero-weighted issues would have no priority and create ambiguous
    sorting. Minimum weight should be a small positive number.
    """
    result = ValidationResult(ok=True, issues=[])

    with pytest.raises(ValueError):
        summarize_violations(result, weights={"dtype": 0})


def test_non_numeric_weight_raises_error():
    """Test that non-numeric weight values raise ValueError.
    
    Weights must be numeric (int or float) to enable severity comparison.
    String values like "high" or "critical" are not allowed.
    """
    result = ValidationResult(ok=True, issues=[])

    with pytest.raises(ValueError):
        summarize_violations(result, weights={"dtype": "high"})


def test_weights_not_dict_raises_error():
    """Test that non-dict weights parameter raises TypeError.
    
    The weights parameter must be a dictionary mapping issue kinds to
    numeric weights. Lists, tuples, or strings are not valid.
    
    This enforces the expected data structure.
    """
    result = ValidationResult(ok=True, issues=[])

    with pytest.raises(TypeError):
        summarize_violations(result, weights=[10, 5, 3])

    with pytest.raises(TypeError):
        summarize_violations(result, weights="invalid")


def test_mixed_valid_invalid_weights():
    """Test that dict with some invalid weights raises ValueError.
    
    If even one weight in the dictionary is invalid (negative, zero,
    or non-numeric), the entire weights parameter should be rejected.
    
    This fails-fast approach prevents partial application of invalid
    weight specifications.
    """
    result = ValidationResult(ok=True, issues=[])

    # Mix of valid and invalid weights
    with pytest.raises(ValueError):
        summarize_violations(result, weights={"dtype": 10, "range": -5})

    with pytest.raises(ValueError):
        summarize_violations(result, weights={"dtype": "high", "range": 5})


# ============================================================================
# Integration Tests
# ============================================================================


def test_realistic_validation_summary():
    """Test with a realistic scenario combining multiple aspects.
    
    This integration test simulates a real-world validation failure with:
    - Multiple issue types at different severity levels
    - A mix of schema and distribution problems
    - More issues than top_k (tests truncation)
    
    Validates that the complete workflow produces sensible, actionable
    summaries that help users prioritize fixes.
    """
    issues = [
        # High severity - missing columns
        Issue(
            kind="missing_column", message="Required column missing", column="user_id"
        ),
        Issue(
            kind="missing_column", message="Required column missing", column="timestamp"
        ),
        # Medium severity - dtype issues
        Issue(kind="dtype", message="Expected int, got str", column="age"),
        Issue(kind="dtype", message="Expected float, got int", column="salary"),
        # Lower severity - range and category issues
        Issue(kind="range", message="Value out of range", column="age"),
        Issue(kind="category", message="Unknown category", column="status"),
        Issue(kind="missingness", message="Too many missing values", column="phone"),
    ]
    result = ValidationResult(ok=False, issues=issues)

    summary = summarize_violations(result, top_k=5)

    # Check basic properties
    assert summary.ok is False
    assert len(summary.top_issues) == 5
    assert len(summary.counts_by_kind) == 5

    # Check counts
    assert summary.counts_by_kind["missing_column"] == 2
    assert summary.counts_by_kind["dtype"] == 2
    assert summary.counts_by_kind["range"] == 1

    # Check that highest severity issues are prioritized
    # missing_column should be in top positions (default weight = 10)
    top_kinds = [issue.kind for issue in summary.top_issues[:2]]
    assert "missing_column" in top_kinds


def test_all_default_weight_kinds():
    """Test that all default weight kinds are handled correctly.
    
    This comprehensive test includes one issue of each default kind:
    - missing_column (weight 10)
    - extra_column (weight 8)
    - dtype (weight 7)
    - range (weight 5)
    - category (weight 5)
    - missingness (weight 3)
    
    Verifies the complete default severity hierarchy is working as designed.
    """
    issues = [
        Issue(kind="missing_column", message="Missing", column="col1"),
        Issue(kind="extra_column", message="Extra", column="col2"),
        Issue(kind="dtype", message="Type error", column="col3"),
        Issue(kind="range", message="Range error", column="col4"),
        Issue(kind="category", message="Category error", column="col5"),
        Issue(kind="missingness", message="Missing values", column="col6"),
    ]
    result = ValidationResult(ok=False, issues=issues)

    # Set top_k=6 to see all 6 issues
    summary = summarize_violations(result, top_k=6)

    # Verify all are counted
    assert len(summary.counts_by_kind) == 6

    # Verify severity ordering (based on default weights)
    # missing_column (10) should be first
    assert summary.top_issues[0].kind == "missing_column"

    # extra_column (8) should be second
    assert summary.top_issues[1].kind == "extra_column"

    # dtype (7) should be third
    assert summary.top_issues[2].kind == "dtype"

    # range and category (both 5) sort by column name (col4 before col5)
    assert summary.top_issues[3].kind == "range"
    assert summary.top_issues[4].kind == "category"

    # missingness (3) should be last
    assert summary.top_issues[5].kind == "missingness"


# ============================================================================
# Edge Cases and Boundary Conditions
# ============================================================================


def test_top_k_equals_one():
    """Test top_k=1 returns only the most severe issue.
    
    With top_k=1, the summary should contain only the single highest-priority
    issue, but counts_by_kind should still reflect all issues.
    
    This is useful for "show me the #1 problem to fix first" scenarios.
    """
    issues = [
        Issue(kind="missingness", message="Low", column="col1"),
        Issue(kind="missing_column", message="High", column="col2"),
        Issue(kind="dtype", message="Medium", column="col3"),
    ]
    result = ValidationResult(ok=False, issues=issues)

    summary = summarize_violations(result, top_k=1)

    assert len(summary.top_issues) == 1
    assert summary.top_issues[0].kind == "missing_column"
    # But all should still be counted
    assert sum(summary.counts_by_kind.values()) == 3


def test_large_number_of_issues():
    """Test with a large number of issues.
    
    Ensures the function handles large validation results efficiently without
    performance degradation or memory issues.
    
    With 1000 issues but top_k=5, only the top 5 should be returned,
    but all 1000 should be counted.
    """
    issues = [
        Issue(kind="dtype", message=f"Issue {i}", column=f"col{i}") for i in range(1000)
    ]
    result = ValidationResult(ok=False, issues=issues)

    summary = summarize_violations(result, top_k=5)

    assert len(summary.top_issues) == 5
    assert summary.counts_by_kind["dtype"] == 1000


def test_none_column_sorting():
    """Test that issues with column=None are handled correctly in sorting.
    
    Dataset-level issues (column=None) represent problems not tied to a
    specific column. These should sort before column-specific issues.
    
    After dataset-level issues, column-specific issues sort alphabetically
    by column name.
    
    This ensures dataset-level problems get visibility.
    """
    issues = [
        Issue(kind="dtype", message="Col issue", column="zebra"),
        Issue(kind="dtype", message="Dataset issue", column=None),
        Issue(kind="dtype", message="Col issue", column="apple"),
    ]
    result = ValidationResult(ok=False, issues=issues)

    summary = summarize_violations(result)

    # column=None should sort first
    assert summary.top_issues[0].column is None
    # Then alphabetically
    assert summary.top_issues[1].column == "apple"
    assert summary.top_issues[2].column == "zebra"