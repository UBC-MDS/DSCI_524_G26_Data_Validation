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