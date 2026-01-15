from data_validation.infer_contract import infer_contract
import pytest
import pandas as pd
from data_validation.types import Contract

#Test Error handling. Confirm error occurss if user input something other than a pandas DataFrame 
def test_infer_contract_requires_dataframe():
    with pytest.raises(TypeError, match="pandas DataFrame"):
        infer_contract(None)

    with pytest.raises(TypeError, match="pandas DataFrame"):
        infer_contract("not a dataframe")


def test_infer_contract_returns_contract():
    df = pd.DataFrame({"a": [1, 2, 3]})
    contract = infer_contract(df)

    assert isinstance(contract, Contract)