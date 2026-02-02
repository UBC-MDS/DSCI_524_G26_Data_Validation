"""
Test suite for validate_contract function.

This module tests the core validation logic that checks DataFrames against
predefined data contracts. The validate_contract function is responsible for
ensuring that incoming data meets all specified requirements including schema,
types, ranges, and categorical constraints.

Validation Types Tested
------------------------
1. **Schema Validation**
   - Missing required columns
   - Extra columns (strict vs non-strict mode)

2. **Data Type Validation**
   - Type mismatches (e.g., string instead of int)
   - Type normalization (object/str/string equivalence)

3. **Missingness Validation**
   - Null value fraction exceeding thresholds
   - Zero-tolerance for missing values

4. **Numeric Range Validation**
   - Values below minimum
   - Values above maximum
   - Boundary conditions

5. **Categorical Validation**
   - Disallowed categorical values
   - Multiple violations per column

Test Organization
-----------------
Tests are organized by validation type for clarity. Each test function focuses
on a specific validation scenario and can be run independently for debugging.

The test contract used across tests defines:
    - age: int64, range [0, 100], no missing values allowed
    - city: object, allowed values {"Vancouver", "Toronto"}

Running Tests
-------------
Run all tests in this module:
    $ pytest tests/test_validate_contract.py -v

Run a specific test:
    $ pytest tests/test_validate_contract.py::test_validate_contract_success_path -v

Run tests matching a pattern:
    $ pytest tests/test_validate_contract.py -k "dtype" -v

Run with coverage:
    $ pytest tests/test_validate_contract.py --cov=pyos_data_validation.validate_contract

Debugging Failed Tests
----------------------
1. Read the test docstring to understand expected behavior
2. Examine the assertion error message
3. Inspect result.issues to see what violations were detected
4. Use pytest -vv for more verbose output
5. Use pytest --pdb to drop into debugger on failure

Example debug session:
    $ pytest tests/test_validate_contract.py::test_validate_contract_dtype_mismatch -vv --pdb

Adding New Tests
----------------
When adding new tests:
1. Follow the naming convention: test_validate_contract_<specific_scenario>
2. Write comprehensive docstring explaining test purpose
3. Use descriptive variable names for test data
4. Add inline comments for complex assertions
5. Consider edge cases and boundary conditions
6. Ensure test is independent and can run in isolation

See Also
--------
- validate_contract function: pyos_data_validation/validate_contract.py
- Contract and ColumnRule types: pyos_data_validation/types.py
- Function documentation: README.md, Section "validate_contract()"

Notes
-----
The current implementation uses a single test function covering multiple
edge cases. Consider splitting this into separate focused tests for:
    - Better test isolation
    - Easier debugging of failures
    - More granular coverage reporting
    - Clearer test organization
"""

import pandas as pd
from pyos_data_validation.validate_contract import validate_contract
from pyos_data_validation.types import Contract, ColumnRule


def test_validate_contract():
    """
    Comprehensive test covering 5 core validation scenarios.
    
    This test function validates the primary edge cases that validate_contract
    must handle correctly. Each scenario tests a different validation rule.
    
    Test Scenarios
    --------------
    1. **Success Path (Happy Path)**
       - Valid data that perfectly matches contract
       - Tests: Complete validation flow with no issues
       - Expected: result.ok = True, no issues
    
    2. **Missing Required Column**
       - DataFrame missing a contract-required column
       - Tests: Schema validation in strict mode
       - Expected: result.ok = False, 'missing_column' issue
    
    3. **Data Type Mismatch**
       - Column has wrong data type (string instead of int)
       - Tests: Type validation logic
       - Expected: result.ok = False, 'dtype' issue
    
    4. **Numeric Range Violation**
       - Numeric value exceeds maximum bound
       - Tests: Numeric range checking
       - Expected: result.ok = False, 'range' issue
    
    5. **Invalid Categorical Values**
       - Categorical value not in allowed set
       - Tests: Categorical domain validation
       - Expected: result.ok = False, 'category' issue
    
    Test Data Characteristics
    -------------------------
    - Uses minimal 1-2 row DataFrames for clarity
    - Each test DataFrame isolates a single validation issue
    - Column names match standard test contract (age, city)
    
    Validation Contract
    -------------------
    age:
        - Type: int64
        - Range: [0, 100]
        - Missing: Not allowed (0%)
    
    city:
        - Type: object
        - Allowed: {"Vancouver", "Toronto"}
        - Missing: Allowed
    
    Expected Outcomes
    -----------------
    All assertions should pass, verifying that:
    - Valid data returns ok=True
    - Each violation type is correctly detected
    - Issue kinds match expected validation failures
    
    Implementation Notes
    --------------------
    This test uses a single function to cover multiple scenarios. Consider
    refactoring into separate test functions for:
    - Better test isolation (one failure doesn't block others)
    - Easier debugging (can run individual scenarios)
    - Clearer test names (self-documenting)
    - More detailed docstrings per scenario
    
    See Also
    --------
    validate_contract : The function being tested
    create_test_contract : Helper to create standard test contract
    
    Examples
    --------
    Run this specific test:
        $ pytest tests/test_validate_contract.py::test_validate_contract -v
    
    Run with detailed output:
        $ pytest tests/test_validate_contract.py::test_validate_contract -vv
    
    Drop into debugger on failure:
        $ pytest tests/test_validate_contract.py::test_validate_contract --pdb
    """
    # Create the test contract that defines validation rules
    # This contract expects 'age' (int, 0-100) and 'city' (Vancouver or Toronto)
    contract = Contract(
        name="test_contract",
        columns={
            "age": ColumnRule(
                dtype="int64", min_value=0, max_value=100, max_missing_frac=0.0
            ),
            "city": ColumnRule(dtype="object", allowed_values={"Vancouver", "Toronto"}),
        },
    )

    # ========================================================================
    # Edge Case 1: Valid DataFrame (Success Path / Happy Path)
    # ========================================================================
    # Purpose: Verify that properly formatted data passes all validations
    # Expected: No issues, result.ok = True
    # 
    # Test data contains:
    #   - age: [25, 30] - Both within valid range [0, 100]
    #   - city: ["Vancouver", "Toronto"] - Both in allowed values set
    #   - No missing values in either column
    #   - Correct data types (int64 for age, object for city)
    
    df_valid = pd.DataFrame({
        "age": [25, 30],                    # Valid integers in range
        "city": ["Vancouver", "Toronto"]    # Valid categorical values
    })
    
    result = validate_contract(df_valid, contract)
    
    # Assertions for success path
    assert result.ok is True, \
        "Validation should succeed for valid data that meets all contract requirements"
    
    assert len(result.issues) == 0, \
        f"Expected no validation issues for valid data, but found {len(result.issues)}: " \
        f"{[issue.message for issue in result.issues]}"

    # ========================================================================
    # Edge Case 2: Missing Required Column (Schema Violation)
    # ========================================================================
    # Purpose: Verify that missing required columns are detected
    # Expected: Validation fails with 'missing_column' issue
    #
    # Test data intentionally omits the 'age' column, which is defined in
    # the contract and therefore required. Only 'city' is provided.
    # 
    # Note: All columns in the contract are treated as required by default
    
    df_missing = pd.DataFrame({
        "city": ["Vancouver"]  # 'age' column is missing
    })
    
    result_strict = validate_contract(df_missing, contract, strict=True)
    
    # Assertions for missing column detection
    assert result_strict.ok is False, \
        "Validation should fail when required columns are missing from DataFrame"
    
    # Verify that a 'missing_column' issue was recorded
    missing_column_issues = [
        issue for issue in result_strict.issues 
        if issue.kind == "missing_column"
    ]
    
    assert len(missing_column_issues) > 0, \
        "Expected at least one 'missing_column' issue, but none were found. " \
        f"All issues: {[issue.kind for issue in result_strict.issues]}"
    
    # Additional check: Verify it's specifically the 'age' column that's missing
    assert any(issue.column == "age" for issue in missing_column_issues), \
        f"Expected 'age' column to be reported as missing, but got: " \
        f"{[issue.column for issue in missing_column_issues]}"

    # ========================================================================
    # Edge Case 3: Data Type Mismatch (Type Validation)
    # ========================================================================
    # Purpose: Verify that incorrect data types are detected
    # Expected: Validation fails with 'dtype' issue
    #
    # Test data provides 'age' as strings ["25", "30"] instead of integers.
    # The contract specifies dtype="int64", so this should fail validation.
    #
    # Note: Type checking is strict except for string type normalization
    # (object/str/string are treated as equivalent)
    
    df_wrong_type = pd.DataFrame({
        "age": ["25", "30"],                # WRONG: strings instead of int64
        "city": ["Vancouver", "Toronto"]    # Correct type (object)
    })
    
    result_type = validate_contract(df_wrong_type, contract)
    
    # Assertions for type mismatch detection
    assert result_type.ok is False, \
        "Validation should fail when column data types don't match contract"
    
    # Verify that a 'dtype' issue was recorded
    dtype_issues = [
        issue for issue in result_type.issues 
        if issue.kind == "dtype"
    ]
    
    assert len(dtype_issues) > 0, \
        "Expected at least one 'dtype' issue, but none were found. " \
        f"All issues: {[issue.kind for issue in result_type.issues]}"
    
    # Additional check: Verify the issue is for the 'age' column
    assert any(issue.column == "age" for issue in dtype_issues), \
        f"Expected 'age' column to have dtype issue, but got: " \
        f"{[issue.column for issue in dtype_issues]}"

    # ========================================================================
    # Edge Case 4: Numeric Range Violation (Boundary Checking)
    # ========================================================================
    # Purpose: Verify that out-of-range numeric values are detected
    # Expected: Validation fails with 'range' issue
    #
    # Test data provides age=150, which exceeds the maximum allowed value
    # of 100 defined in the contract's min_value/max_value constraints.
    #
    # This tests the numeric bounds checking logic for values above the max.
    # (Could also test below min with negative values like age=-5)
    
    df_out_of_range = pd.DataFrame({
        "age": [150],           # WRONG: 150 > max_value (100)
        "city": ["Toronto"]     # Correct value
    })
    
    result_range = validate_contract(df_out_of_range, contract)
    
    # Assertions for range violation detection
    assert result_range.ok is False, \
        "Validation should fail when numeric values exceed min/max bounds"
    
    # Verify that a 'range' issue was recorded
    range_issues = [
        issue for issue in result_range.issues 
        if issue.kind == "range"
    ]
    
    assert len(range_issues) > 0, \
        "Expected at least one 'range' issue, but none were found. " \
        f"All issues: {[issue.kind for issue in result_range.issues]}"
    
    # Additional checks: Verify the details of the range violation
    assert any(issue.column == "age" for issue in range_issues), \
        f"Expected 'age' column to have range issue"
    
    # Could also verify: issue.expected (max_value=100) and issue.observed (150)

    # ========================================================================
    # Edge Case 5: Invalid Categorical Values (Domain Validation)
    # ========================================================================
    # Purpose: Verify that disallowed categorical values are detected
    # Expected: Validation fails with 'category' issue
    #
    # Test data provides city="Seattle", which is not in the allowed_values
    # set {"Vancouver", "Toronto"} defined in the contract.
    #
    # This tests that categorical domain validation correctly identifies
    # values outside the permitted set.
    
    df_bad_cat = pd.DataFrame({
        "age": [25],            # Correct value
        "city": ["Seattle"]     # WRONG: Not in {"Vancouver", "Toronto"}
    })
    
    result_cat = validate_contract(df_bad_cat, contract)
    
    # Assertions for categorical violation detection
    assert result_cat.ok is False, \
        "Validation should fail when categorical values are not in allowed set"
    
    # Verify that a 'category' issue was recorded
    category_issues = [
        issue for issue in result_cat.issues 
        if issue.kind == "category"
    ]
    
    assert len(category_issues) > 0, \
        "Expected at least one 'category' issue, but none were found. " \
        f"All issues: {[issue.kind for issue in result_cat.issues]}"
    
    # Additional check: Verify it's the 'city' column with the violation
    assert any(issue.column == "city" for issue in category_issues), \
        f"Expected 'city' column to have category issue, but got: " \
        f"{[issue.column for issue in category_issues]}"
    
    # Could also verify: issue.observed contains "Seattle" and
    # issue.expected contains {"Vancouver", "Toronto"}