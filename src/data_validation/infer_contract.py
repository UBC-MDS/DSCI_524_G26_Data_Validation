import pandas as pd
from data_validation.types import Contract
from data_validation.types import ColumnRule
from pandas.api.types import is_numeric_dtype, is_categorical_dtype, is_bool_dtype


def infer_contract(df):
    """
    Derive a data contract from a pandas DataFrame.

    Derives per-column expectations—including expected data type, allowable
    missingness, optional numeric bounds, and optional categorical domains.
    The resulting contract defines the expected schema and validation
    constraints for future datasets, based on the observed structure of
    the input DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        A pandas DataFrame used to derive the data contract. This should be an
        example of “good” data that represents the expected structure and
        constraints of future datasets.

    Returns
    -------
    Contract
        A Contract object mapping column names to ColumnRule definitions,
        describing the expected schema and constraints of the dataset.
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")
    
    columns = {}
    for col in df.columns:
        s = df[col]

        # very simple dtype string
        dtype_str = str(s.dtype)

        # fraction missing in [0, 1]
        missing_frac = float(s.isna().mean())

        # only numeric columns get min/max
        min_value = max_value = None
        if is_numeric_dtype(s):
            min_value = float(s.min()) if s.notna().any() else None
            max_value = float(s.max()) if s.notna().any() else None

        # only categorical-like columns get allowed_values
        allowed_values = None
        if s.dtype == "object" or is_categorical_dtype(s) or is_bool_dtype(s):
            allowed_values = set(map(str, s.dropna().unique()))

        columns[col] = ColumnRule(
            dtype=dtype_str,
            max_missing_frac=missing_frac,
            min_value=min_value,
            max_value=max_value,
            allowed_values=allowed_values,
        )


    
    return Contract(columns=columns)