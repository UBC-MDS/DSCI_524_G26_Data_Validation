from pyos_data_validation.infer_contract import infer_contract
import pytest
import pandas as pd
from pyos_data_validation.types import Contract
from pyos_data_validation.types import ColumnRule


# Test Error handling. Confirm error occurss if user input something other than a pandas DataFrame
def test_infer_contract_requires_dataframe():
    with pytest.raises(TypeError, match="pandas DataFrame"):
        infer_contract(None)

    with pytest.raises(TypeError, match="pandas DataFrame"):
        infer_contract("not a dataframe")


# Test object returned is an object fo type Contract
def test_infer_contract_returns_contract():
    df = pd.DataFrame({"a": [1, 2, 3]})
    contract = infer_contract(df)

    assert isinstance(contract, Contract)


# Test contract creates rules per column in the df
def test_infer_contract_creates_rule_per_column():
    df = pd.DataFrame({"age": [20, 30, 40], "height": [170, 180, 175]})

    contract = infer_contract(df)

    assert set(contract.columns.keys()) == {"age", "height"}

# Test contract stores rules per column in the df
def test_infer_contract_stores_columnrule_objects():
    df = pd.DataFrame({"age": [20, 30, 40], "height": [170, 180, 175]})

    contract = infer_contract(df)

    for rule in contract.columns.values():
        assert isinstance(rule, ColumnRule)


# Edge tests developed with support of LLM to ensure functionality
# Edge test: missingness is a valid fraction
def test_missing_fraction_between_zero_and_one():
    df = pd.DataFrame({"a": [1, None, 3]})
    contract = infer_contract(df)

    frac = contract.columns["a"].max_missing_frac
    assert 0.0 <= frac <= 1.0


# Edge test: numeric vs categorical handling
def test_numeric_and_categorical_rules():
    df = pd.DataFrame({"num": [1, 2, 3], "cat": ["a", "b", "a"]})

    contract = infer_contract(df)

    assert contract.columns["num"].min_value is not None
    assert contract.columns["num"].allowed_values is None

    assert contract.columns["cat"].allowed_values == {"a", "b"}

#MIlestone 4 Functions 

# 1) Empty DataFrame should produce an empty contract.columns mapping
def test_infer_contract_empty_dataframe_returns_empty_columns():
    df = pd.DataFrame()
    contract = infer_contract(df)
    assert contract.columns == {}

