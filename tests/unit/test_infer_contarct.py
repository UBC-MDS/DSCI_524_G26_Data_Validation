from data_validation.infer_contract import infer_contract

import pandas as pd

def infer_contract(df):
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df object must be a pandas DataFrame")