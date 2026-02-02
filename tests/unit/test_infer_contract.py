from pyos_data_validation.infer_contract import infer_contract
import pytest
import pandas as pd
from pyos_data_validation.types import Contract
from pyos_data_validation.types import ColumnRule


# This test verifies that infer_contract enforces its input contract.
# The function is expected to only accept pandas DataFrame inputs.
# Passing any other type should raise a clear TypeError to prevent silent misuse.
def test_infer_contract_requires_dataframe():
    with pytest.raises(TypeError, match="pandas DataFrame"):
        infer_contract(None)

    with pytest.raises(TypeError, match="pandas DataFrame"):
        infer_contract("not a dataframe")


# This test checks that infer_contract returns a Contract object.
# Given a valid DataFrame, the function should always produce a structured
# Contract representing the inferred schema and constraints.
def test_infer_contract_returns_contract():
    df = pd.DataFrame({"a": [1, 2, 3]})
    contract = infer_contract(df)

    assert isinstance(contract, Contract)


# This test ensures that infer_contract creates exactly one ColumnRule
# for each column present in the input DataFrame.
# The resulting contract should mirror the DataFrame schema.
def test_infer_contract_creates_rule_per_column():
    df = pd.DataFrame({"age": [20, 30, 40], "height": [170, 180, 175]})

    contract = infer_contract(df)

    assert set(contract.columns.keys()) == {"age", "height"}


# This test verifies that each entry in contract.columns
# is stored as a ColumnRule object.
# This ensures the contract contains structured, typed rules
# rather than raw metadata.
def test_infer_contract_stores_columnrule_objects():
    df = pd.DataFrame({"age": [20, 30, 40], "height": [170, 180, 175]})

    contract = infer_contract(df)

    for rule in contract.columns.values():
        assert isinstance(rule, ColumnRule)


# Edge tests developed with support of LLM to ensure functionality
# This test validates that the inferred missingness fraction
# always falls within valid bounds [0, 1].
# It protects against incorrect normalization or division logic.
def test_missing_fraction_between_zero_and_one():
    df = pd.DataFrame({"a": [1, None, 3]})
    contract = infer_contract(df)

    frac = contract.columns["a"].max_missing_frac
    assert 0.0 <= frac <= 1.0


# This test checks that infer_contract correctly distinguishes
# between numeric and categorical columns.
# Numeric columns should infer numeric bounds,
# while categorical columns should infer allowed value sets.
def test_numeric_and_categorical_rules():
    df = pd.DataFrame({"num": [1, 2, 3], "cat": ["a", "b", "a"]})

    contract = infer_contract(df)

    assert contract.columns["num"].min_value is not None
    assert contract.columns["num"].allowed_values is None

    assert contract.columns["cat"].allowed_values == {"a", "b"}


# Milestone 4 Functions
# This test verifies that an empty DataFrame produces
# an empty contract with no column rules.
# The function should fail gracefully rather than error.
def test_infer_contract_empty_dataframe_returns_empty_columns():
    df = pd.DataFrame()
    contract = infer_contract(df)
    assert contract.columns == {}


# This test confirms that missingness is computed exactly,
# not approximately, for a known missing-value pattern.
# It ensures deterministic and reproducible behavior.
def test_missing_fraction_exact_value():
    df = pd.DataFrame({"a": [1, None, None, 4]})  # 2 missing out of 4 = 0.5
    contract = infer_contract(df)
    assert contract.columns["a"].max_missing_frac == 0.5


# This test checks that columns containing only missing values
# do not cause errors and correctly infer a missingness of 1.0.
# This is a critical edge case for real-world datasets.
def test_all_missing_column_missingness_is_one():
    df = pd.DataFrame({"a": [None, None, None]})
    contract = infer_contract(df)
    assert contract.columns["a"].max_missing_frac == 1.0


# This test verifies that boolean columns are treated as
# categorical-like variables.
# The function should infer allowed_values based on unique
# boolean values rather than numeric bounds.
def test_boolean_column_allowed_values():
    df = pd.DataFrame({"flag": [True, False, True]})
    contract = infer_contract(df)
    assert contract.columns["flag"].allowed_values == {"True", "False"}
