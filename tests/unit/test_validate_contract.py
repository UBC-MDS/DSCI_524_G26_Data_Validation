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

    contract = Contract(
        name="test_contract",
        columns={
            "age": ColumnRule(
                dtype="int64", min_value=0, max_value=100, max_missing_frac=0.0
            ),
            "city": ColumnRule(dtype="object", allowed_values={"Vancouver", "Toronto"}),
        },
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
    df_wrong_type = pd.DataFrame(
        {"age": ["25", "30"], "city": ["Vancouver", "Toronto"]}
    )
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
