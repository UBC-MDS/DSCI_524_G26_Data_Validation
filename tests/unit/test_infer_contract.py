from data_validation.infer_contract import infer_contract
import pytest
import pandas as pd

def test_infer_contract_requires_dataframe():
    with pytest.raises(TypeError, match="pandas DataFrame"):
        infer_contract(None)

    with pytest.raises(TypeError, match="pandas DataFrame"):
        infer_contract("not a dataframe")