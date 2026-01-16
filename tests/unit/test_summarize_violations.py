"""
Unit tests for summarize_violations function.

Tests the basic functionality and key edge cases.
"""

import pytest
from data_validation.summarize_violations import summarize_violations
from data_validation.types import ValidationResult, Issue, Summary


def test_empty_result():
    """Test that empty ValidationResult returns empty Summary."""
    result = ValidationResult(ok=True, issues=[])
    
    summary = summarize_violations(result)
    
    assert summary.ok is True
    assert len(summary.top_issues) == 0
    assert summary.counts_by_kind == {}


def test_single_issue():
    """Test with one issue."""
    issue = Issue(kind='dtype', message='Type mismatch', column='age')
    result = ValidationResult(ok=False, issues=[issue])
    
    summary = summarize_violations(result)
    
    assert summary.ok is False
    assert len(summary.top_issues) == 1
    assert summary.top_issues[0] == issue
    assert summary.counts_by_kind == {'dtype': 1}


def test_top_k_limits_results():
    """Test that top_k limits the number of returned issues."""
    issues = [
        Issue(kind='dtype', message=f'Issue {i}', column=f'col{i}')
        for i in range(10)
    ]
    result = ValidationResult(ok=False, issues=issues)
    
    summary = summarize_violations(result, top_k=3)
    
    assert len(summary.top_issues) == 3
    # counts should still include all issues
    assert summary.counts_by_kind == {'dtype': 10}


def test_severity_ranking():
    """Test that issues are ranked by severity."""
    issues = [
        Issue(kind='missingness', message='Low severity', column='col1'),
        Issue(kind='missing_column', message='High severity', column='col2'),
        Issue(kind='range', message='Medium severity', column='col3'),
    ]
    result = ValidationResult(ok=False, issues=issues)
    
    summary = summarize_violations(result)
    
    # missing_column should be first (highest default weight)
    assert summary.top_issues[0].kind == 'missing_column'
    # missingness should be last (lowest default weight)
    assert summary.top_issues[-1].kind == 'missingness'


def test_custom_weights():
    """Test that custom weights override defaults."""
    issues = [
        Issue(kind='range', message='Should be first', column='col1'),
        Issue(kind='dtype', message='Should be second', column='col2'),
    ]
    result = ValidationResult(ok=False, issues=issues)
    
    # Give range higher weight than dtype
    summary = summarize_violations(result, weights={'range': 20, 'dtype': 5})
    
    assert summary.top_issues[0].kind == 'range'


def test_invalid_result_type():
    """Test that invalid result type raises TypeError."""
    with pytest.raises(TypeError):
        summarize_violations("not a result")


def test_negative_top_k():
    """Test that negative top_k raises ValueError."""
    result = ValidationResult(ok=True, issues=[])
    
    with pytest.raises(ValueError):
        summarize_violations(result, top_k=-1)