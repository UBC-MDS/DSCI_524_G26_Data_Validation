from dataclasses import dataclass
from typing import Any, List, Dict, Optional, Tuple
from data_validation import validate_contract

@dataclass
class ColumnRules:
    dtype: Any
    required: bool = True
    allow_nulls: bool = True
    value_range: Optional[Tuple[float, float]] = None
    allowed_values: Optional[List[Any]] = None

@dataclass
class Contract:
    columns: Dict[str, ColumnRules]

@dataclass
class ValidationResult:
    passed: bool
    errors: List[str]
    warnings: List[str]
    column_details: Dict[str, List[str]]

import pandas as pd
import pytest

def test_validate_contract():
    """
    Test validate_contract for Milestone 2.
    Tests include: success path, missing columns (strict vs non-strict),
    data type mismatches, and null value violations.
    """
    
    contract = Contract(columns={
        "age": ColumnRules(dtype="int64", value_range=(0, 100), allow_nulls=False),
        "city": ColumnRules(dtype="object", allowed_values=["Vancouver", "Toronto"])
    })

    # --- Edge Case 1: The "Happy Path" (Success) ---
    df_valid = pd.DataFrame({"age": [25, 30], "city": ["Vancouver", "Toronto"]})
    result = validate_contract(df_valid, contract)
    assert result.passed is True [cite: 111]
    assert len(result.errors) == 0

    # --- Edge Case 2: Missing Required Column (Strict Mode) ---
    df_missing = pd.DataFrame({"city": ["Vancouver"]})
    result_strict = validate_contract(df_missing, contract, strict=True)
    assert result_strict.passed is False [cite: 63]
    assert "Missing required columns" in result_strict.errors[0]

    # --- Edge Case 3: Missing Required Column (Non-Strict Mode) ---
    result_warn = validate_contract(df_missing, contract, strict=False)
    assert result_warn.passed is True  # Should pass because error moved to warnings
    assert len(result_warn.warnings) > 0 [cite: 63]

    # --- Edge Case 4: Data Type Mismatch ---
    df_wrong_type = pd.DataFrame({"age": ["25", "30"], "city": ["Vancouver", "Toronto"]})
    result_type = validate_contract(df_wrong_type, contract)
    assert result_type.passed is False
    assert "expected dtype int64" in result_type.errors[0]

    # --- Edge Case 5: Null Values where Not Allowed ---
    df_nulls = pd.DataFrame({"age": [25, None], "city": ["Vancouver", "Toronto"]})
    result_null = validate_contract(df_nulls, contract)
    assert result_null.passed is False
    assert "contains null values" in result_null.errors[0]