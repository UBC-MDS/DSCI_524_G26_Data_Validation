import pandas as pd
from data_validation.validate_contract import validate_contract
from data_validation.types import Contract, ColumnRule


def test_validate_contract():
    """
    Test validate_contract with 5 representative edge cases:
    1. Success path
    2. Missing required column (strict mode)
    3. Data type mismatch
    4. Numeric range violation
    5. Invalid categorical values
    """

    contract = Contract(
        name="test_contract",
        columns={
            "age": ColumnRule(dtype="int64", min_value=0, max_value=100, max_missing_frac=0.0),
            "city": ColumnRule(dtype="object", allowed_values={"Vancouver", "Toronto"})
        }
    )

    # --- Edge Case 1: Valid DataFrame (success path) ---
    df_valid = pd.DataFrame({"age": [25, 30], "city": ["Vancouver", "Toronto"]})
    result = validate_contract(df_valid, contract)
    assert result.ok is True
    assert len(result.issues) == 0

    # --- Edge Case 2: Missing required column (strict mode) ---
    df_missing = pd.DataFrame({"city": ["Vancouver"]})
    result_strict = validate_contract(df_missing, contract, strict=True)
    # Should fail because 'age' is missing
    assert result_strict.ok is False
    assert any(issue.kind == "missing_column" for issue in result_strict.issues)

    # --- Edge Case 3: Data type mismatch ---
    df_wrong_type = pd.DataFrame({"age": ["25", "30"], "city": ["Vancouver", "Toronto"]})
    # Should fail because 'age' is str instead of int64
    result_type = validate_contract(df_wrong_type, contract)
    assert result_type.ok is False
    assert any(issue.kind == "dtype" for issue in result_type.issues)

    # --- Edge Case 4: Numeric range violation ---
    df_out_of_range = pd.DataFrame({"age": [150], "city": ["Toronto"]})
    # Should fail because age 150 is above max_value 100
    result_range = validate_contract(df_out_of_range, contract)
    assert result_range.ok is False
    assert any(issue.kind == "range" for issue in result_range.issues)

    # --- Edge Case 5: Invalid categorical values ---
    df_bad_cat = pd.DataFrame({"age": [25], "city": ["Seattle"]})
    # Should fail because 'Seattle' is not an allowed city
    result_cat = validate_contract(df_bad_cat, contract)
    assert result_cat.ok is False
    assert any(issue.kind == "category" for issue in result_cat.issues)
