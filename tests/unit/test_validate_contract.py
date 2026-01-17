import pandas as pd
from data_validation.validate_contract import validate_contract
from data_validation.types import Contract, ColumnRule, Issue, ValidationResult

def test_validate_contract():
    """
    Test validate_contract for Milestone 2 with 3-5 edge cases. 
    """
    contract = Contract(
        name="test_contract",
        columns={
            "age": ColumnRule(dtype="int64", min_value=0, max_value=100, max_missing_frac=0.0),
            "city": ColumnRule(dtype="object", allowed_values={"Vancouver", "Toronto"})
        }
    )

    # --- Edge Case 1: Success Path ---
    df_valid = pd.DataFrame({"age": [25, 30], "city": ["Vancouver", "Toronto"]})
    result = validate_contract(df_valid, contract)
    assert result.ok is True  
    assert len(result.issues) == 0

    # --- Edge Case 2: Missing Column (Strict) ---
    df_missing = pd.DataFrame({"city": ["Vancouver"]})
    result_strict = validate_contract(df_missing, contract, strict=True)
    assert result_strict.ok is False  # [cite: 63]
    assert any(i.kind == "missing_column" for i in result_strict.issues)

    # --- Edge Case 3: Data Type Mismatch ---
    df_wrong_type = pd.DataFrame({"age": ["25", "30"], "city": ["Vancouver", "Toronto"]})
    result_type = validate_contract(df_wrong_type, contract)
    assert result_type.ok is False # [cite: 111]
    assert any(i.kind == "dtype" for i in result_type.issues)

    # --- Edge Case 4: Numeric Range Violation ---
    df_out_of_range = pd.DataFrame({"age": [150], "city": ["Toronto"]})
    result_range = validate_contract(df_out_of_range, contract)
    assert result_range.ok is False # [cite: 111]
    assert any(i.kind == "range" for i in result_range.issues)

    # --- Edge Case 5: Invalid Categorical Values ---
    df_bad_cat = pd.DataFrame({"age": [25], "city": ["Seattle"]})
    result_cat = validate_contract(df_bad_cat, contract)
    assert result_cat.ok is False #[cite: 108]
    assert any(i.kind == "category" for i in result_cat.issues)