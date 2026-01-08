def infer_contract(df):
    """
    Derive a data contract from a pandas DataFrame.

    Derives expected column types, acceptable missingness, numeric bounds,
    and categorical domains. This defines the expected structure and
    constraints of valid data based on the input DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        A pandas DataFrame used to derive the data contract. This should be an
        example of “good” data that represents what you expect future data
        to look like.

    Returns
    -------
    Contract
        The derived data contract describing expected schema and constraints.
    """
