"""
Basic unit tests for compare_contracts.
"""

import pytest

from pyos_data_validation.compare_contracts import compare_contracts
from pyos_data_validation.types import ColumnRule, Contract


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


def test_missingness_only_change():
    """Detect missingness drift without other changes."""
    contract_a = Contract(columns={"age": ColumnRule(dtype="int", max_missing_frac=0.05)})
    contract_b = Contract(columns={"age": ColumnRule(dtype="int", max_missing_frac=0.10)})

    report = compare_contracts(contract_a, contract_b)

    assert report.missingness_changes == {"age": (0.05, 0.10)}
    assert report.dtype_changes == {}
    assert report.range_changes == set()
    assert report.category_changes == set()


def test_category_only_change():
    """Detect category drift without other changes."""
    contract_a = Contract(columns={"status": ColumnRule(dtype="category", allowed_values={"new", "old"})})
    contract_b = Contract(columns={"status": ColumnRule(dtype="category", allowed_values={"new", "old", "unknown"})})

    report = compare_contracts(contract_a, contract_b)

    assert report.category_changes == {"status"}
    assert report.dtype_changes == {}
    assert report.range_changes == set()
    assert report.missingness_changes == {}


def test_range_change_none_to_value():
    """None to value for range triggers drift."""
    contract_a = Contract(columns={"score": ColumnRule(dtype="float", min_value=None, max_value=None)})
    contract_b = Contract(columns={"score": ColumnRule(dtype="float", min_value=0.0, max_value=1.0)})

    report = compare_contracts(contract_a, contract_b)

    assert report.range_changes == {"score"}


def test_category_change_none_to_set():
    """None to set for categories triggers drift."""
    contract_a = Contract(columns={"status": ColumnRule(dtype="category", allowed_values=None)})
    contract_b = Contract(columns={"status": ColumnRule(dtype="category", allowed_values={"new", "old"})})

    report = compare_contracts(contract_a, contract_b)

    assert report.category_changes == {"status"}


def test_none_to_none_no_drift():
    """None to None for optional fields yields no drift."""
    contract_a = Contract(columns={"score": ColumnRule(dtype="float", min_value=None, max_value=None)})
    contract_b = Contract(columns={"score": ColumnRule(dtype="float", min_value=None, max_value=None)})

    report = compare_contracts(contract_a, contract_b)

    assert report.range_changes == set()
    assert report.category_changes == set()


def test_dtype_change_blocks_range_drift():
    """Range drift is not reported when dtype changes."""
    contract_a = Contract(columns={"score": ColumnRule(dtype="int", min_value=0.0, max_value=10.0)})
    contract_b = Contract(columns={"score": ColumnRule(dtype="float", min_value=-1.0, max_value=10.0)})

    report = compare_contracts(contract_a, contract_b)

    assert report.dtype_changes == {"score": ("int", "float")}
    assert report.range_changes == set()


def test_dtype_change_blocks_category_drift():
    """Category drift is not reported when dtype changes."""
    contract_a = Contract(columns={"status": ColumnRule(dtype="category", allowed_values={"new", "old"})})
    contract_b = Contract(columns={"status": ColumnRule(dtype="string", allowed_values={"new", "old", "unknown"})})

    report = compare_contracts(contract_a, contract_b)

    assert report.dtype_changes == {"status": ("category", "string")}
    assert report.category_changes == set()


def test_invalid_contract_type_raises_typeerror():
    """Invalid contract types raise TypeError."""
    contract_b = Contract(columns={"age": ColumnRule(dtype="int")})

    with pytest.raises(TypeError):
        compare_contracts("not-a-contract", contract_b)


def test_invalid_missing_frac_raises_valueerror():
    """Invalid missingness fraction raises ValueError."""
    contract_a = Contract(columns={"age": ColumnRule(dtype="int", max_missing_frac=1.5)})
    contract_b = Contract(columns={"age": ColumnRule(dtype="int")})

    with pytest.raises(ValueError):
        compare_contracts(contract_a, contract_b)


def test_non_columnrule_raises_typeerror():
    """Non-ColumnRule entries raise TypeError."""
    contract_a = Contract(columns={"age": "not-a-rule"})
    contract_b = Contract(columns={"age": ColumnRule(dtype="int")})

    with pytest.raises(TypeError):
        compare_contracts(contract_a, contract_b)


def test_non_numeric_missing_frac_raises_valueerror():
    """Non-numeric max_missing_frac raises ValueError."""
    contract_a = Contract(columns={"age": ColumnRule(dtype="int", max_missing_frac="high")})
    contract_b = Contract(columns={"age": ColumnRule(dtype="int")})

    with pytest.raises(ValueError):
        compare_contracts(contract_a, contract_b)


def test_invalid_contract_b_raises_valueerror():
    """Invalid contract_b triggers validation on the second contract."""
    contract_a = Contract(columns={"age": ColumnRule(dtype="int")})
    contract_b = Contract(columns={"age": ColumnRule(dtype="int", max_missing_frac=2.0)})

    with pytest.raises(ValueError):
        compare_contracts(contract_a, contract_b)


def test_min_greater_than_max_raises_valueerror():
    """Invalid range bounds raise ValueError."""
    contract_a = Contract(columns={"age": ColumnRule(dtype="int", min_value=10.0, max_value=1.0)})
    contract_b = Contract(columns={"age": ColumnRule(dtype="int", min_value=0.0, max_value=10.0)})

    with pytest.raises(ValueError):
        compare_contracts(contract_a, contract_b)


@pytest.mark.parametrize(
    "contract_a,contract_b",
    [
        (Contract(columns={"a": ColumnRule(dtype="int")}), Contract(columns={"b": ColumnRule(dtype="int")})),
        (Contract(columns={"a": ColumnRule(dtype="int")}), Contract(columns={"a": ColumnRule(dtype="float")})),
        (Contract(columns={"a": ColumnRule(dtype="float", min_value=0.0)}), Contract(columns={"a": ColumnRule(dtype="float", min_value=1.0)})),
        (Contract(columns={"a": ColumnRule(dtype="category", allowed_values={"x"})}), Contract(columns={"a": ColumnRule(dtype="category", allowed_values={"x", "y"})})),
        (Contract(columns={"a": ColumnRule(dtype="int", max_missing_frac=0.05)}), Contract(columns={"a": ColumnRule(dtype="int", max_missing_frac=0.10)})),
    ],
)
def test_has_drift_true_for_any_nonempty_change(contract_a, contract_b):
    """Any non-empty drift category flips has_drift to True."""
    report = compare_contracts(contract_a, contract_b)
    assert report.has_drift is True


def test_has_drift_false_for_no_drift():
    """No drift yields has_drift False."""
    contract_a = Contract(columns={"age": ColumnRule(dtype="int")})
    contract_b = Contract(columns={"age": ColumnRule(dtype="int")})

    report = compare_contracts(contract_a, contract_b)

    assert report.has_drift is False


def test_multiple_columns_mixed_drift():
    """Aggregate drift across multiple columns."""
    contract_a = Contract(
        columns={
            "a": ColumnRule(dtype="int"),
            "b": ColumnRule(dtype="float", min_value=0.0, max_value=1.0),
            "c": ColumnRule(dtype="category", allowed_values={"x", "y"}),
            "d": ColumnRule(dtype="int", max_missing_frac=0.01),
        }
    )
    contract_b = Contract(
        columns={
            "a": ColumnRule(dtype="float"),
            "b": ColumnRule(dtype="float", min_value=-1.0, max_value=1.0),
            "c": ColumnRule(dtype="category", allowed_values={"x", "y", "z"}),
            "d": ColumnRule(dtype="int", max_missing_frac=0.10),
            "e": ColumnRule(dtype="int"),
        }
    )

    report = compare_contracts(contract_a, contract_b)

    assert report.added_columns == {"e"}
    assert report.removed_columns == set()
    assert report.dtype_changes == {"a": ("int", "float")}
    assert report.range_changes == {"b"}
    assert report.category_changes == {"c"}
    assert report.missingness_changes == {"d": (0.01, 0.10)}


def test_missingness_reports_old_new_order():
    """Missingness changes are reported as (old, new)."""
    contract_a = Contract(columns={"age": ColumnRule(dtype="int", max_missing_frac=0.05)})
    contract_b = Contract(columns={"age": ColumnRule(dtype="int", max_missing_frac=0.20)})

    report = compare_contracts(contract_a, contract_b)

    assert report.missingness_changes["age"] == (0.05, 0.20)


def test_dtype_reports_old_new_order():
    """Dtype changes are reported as (old, new)."""
    contract_a = Contract(columns={"age": ColumnRule(dtype="int")})
    contract_b = Contract(columns={"age": ColumnRule(dtype="float")})

    report = compare_contracts(contract_a, contract_b)

    assert report.dtype_changes["age"] == ("int", "float")


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
