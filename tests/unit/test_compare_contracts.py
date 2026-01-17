"""
Basic unit tests for compare_contracts.
"""

from data_validation.compare_contracts import compare_contracts
from data_validation.types import ColumnRule, Contract


def test_added_and_removed_columns():
    """Detect added and removed columns between contracts."""
    contract_a = Contract(columns={"age": ColumnRule(dtype="int")})
    contract_b = Contract(columns={"height": ColumnRule(dtype="int")})

    report = compare_contracts(contract_a, contract_b)

    assert report.added_columns == {"height"}
    assert report.removed_columns == {"age"}
    assert report.has_drift is True


def test_dtype_change():
    """Detect dtype changes for shared columns."""
    contract_a = Contract(columns={"age": ColumnRule(dtype="int")})
    contract_b = Contract(columns={"age": ColumnRule(dtype="float")})

    report = compare_contracts(contract_a, contract_b)

    assert report.dtype_changes == {"age": ("int", "float")}
    assert report.has_drift is True


def test_range_change():
    """Detect min/max range changes for shared columns."""
    contract_a = Contract(columns={"score": ColumnRule(dtype="float", min_value=0.0, max_value=1.0)})
    contract_b = Contract(columns={"score": ColumnRule(dtype="float", min_value=-1.0, max_value=1.0)})

    report = compare_contracts(contract_a, contract_b)

    assert report.range_changes == {"score"}
    assert report.has_drift is True


def test_category_and_missingness_changes():
    """Detect category and missingness changes for shared columns."""
    contract_a = Contract(
        columns={
            "status": ColumnRule(dtype="category", allowed_values={"new", "old"}, max_missing_frac=0.05)
        }
    )
    contract_b = Contract(
        columns={
            "status": ColumnRule(dtype="category", allowed_values={"new", "old", "unknown"}, max_missing_frac=0.10)
        }
    )

    report = compare_contracts(contract_a, contract_b)

    assert report.category_changes == {"status"}
    assert report.missingness_changes == {"status": (0.05, 0.10)}
    assert report.has_drift is True


def test_no_drift():
    """No differences yields an empty report."""
    contract_a = Contract(columns={"age": ColumnRule(dtype="int", min_value=0.0, max_value=120.0)})
    contract_b = Contract(columns={"age": ColumnRule(dtype="int", min_value=0.0, max_value=120.0)})

    report = compare_contracts(contract_a, contract_b)

    assert report.added_columns == set()
    assert report.removed_columns == set()
    assert report.dtype_changes == {}
    assert report.range_changes == set()
    assert report.category_changes == set()
    assert report.missingness_changes == {}
    assert report.has_drift is False
