# data_validation/types.py
"""
Minimal shared dataclasses for the toy `data_validation` project.

These types are intentionally small and "data-only" (no pandas dependency, no logic).
They support:
- infer_contract -> Contract
- validate_contract -> ValidationResult
- compare_contracts -> DriftReport
- summarize_violations -> Summary
- validate_and_fail -> raise on ValidationResult.ok == False
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


# -------------------------
# Contract
# -------------------------

@dataclass(frozen=True)
class ColumnRule:
    """
    Minimal per-column expectations.

    dtype: simple string such as "int", "float", "string", "bool", "datetime", "category"
    max_missing_frac: fraction of missing values allowed in [0, 1]
    min_value/max_value: numeric bounds (optional)
    allowed_values: allowed categorical values (optional)
    """
    dtype: str
    max_missing_frac: float = 0.0
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_values: Optional[Set[str]] = None


@dataclass(frozen=True)
class Contract:
    """Dataset contract = mapping of column name -> ColumnRule."""
    columns: Dict[str, ColumnRule]
    name: str = "contract"


# -------------------------
# Validation
# -------------------------

@dataclass(frozen=True)
class Issue:
    """
    A single validation issue.

    kind examples:
      - "missing_column", "extra_column"
      - "dtype", "missingness", "range", "category"
    column=None for dataset-level issues.
    """
    kind: str
    message: str
    column: Optional[str] = None
    observed: Any = None
    expected: Any = None


@dataclass(frozen=True)
class ValidationResult:
    """Output of validate_contract()."""
    ok: bool
    issues: List[Issue] = field(default_factory=list)


# -------------------------
# Contract comparison (drift)
# -------------------------

@dataclass(frozen=True)
class DriftReport:
    """
    Output of compare_contracts().

    Keep it tiny: only what changed between two contracts.
    """
    added_columns: Set[str] = field(default_factory=set)
    removed_columns: Set[str] = field(default_factory=set)
    dtype_changes: Dict[str, Tuple[str, str]] = field(default_factory=dict)  # col -> (old, new)
    range_changes: Set[str] = field(default_factory=set)                    # cols whose min/max changed
    category_changes: Set[str] = field(default_factory=set)                 # cols whose allowed_values changed


# -------------------------
# Summarization
# -------------------------

@dataclass(frozen=True)
class Summary:
    """
    Output of summarize_violations().

    counts_by_kind is useful for CI logs ("dtype: 2, missingness: 1").
    """
    ok: bool
    top_issues: List[Issue] = field(default_factory=list)
    counts_by_kind: Dict[str, int] = field(default_factory=dict)


# -------------------------
# CI helper exception
# -------------------------

class ContractViolationError(AssertionError):
    """Raised by validate_and_fail when validation fails."""
    pass
 