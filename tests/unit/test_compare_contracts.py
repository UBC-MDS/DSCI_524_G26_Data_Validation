"""
Unit tests for compare_contracts.

The compare_contracts function should:
- Identify schema drift (added/removed columns, dtype changes).
- Identify constraint drift (range, category, missingness changes).
- Validate input contracts and raise on invalid rules.
- Report drift in a consistent shape and ordering.
"""

import pytest

from pyos_data_validation.compare_contracts import compare_contracts
from pyos_data_validation.types import ColumnRule, Contract


def test_added_and_removed_columns():
    """Detects added/removed columns, which would break downstream schema.

    We swap the single column name between contracts to ensure both the
    addition and removal are reported in the correct direction.
    """
    contract_a = Contract(columns={"age": ColumnRule(dtype="int")})
    contract_b = Contract(columns={"height": ColumnRule(dtype="int")})

    report = compare_contracts(contract_a, contract_b)

    # New column appears only in contract_b; old column only in contract_a.
    assert report.added_columns == {"height"}
    assert report.removed_columns == {"age"}
    assert report.has_drift is True


def test_dtype_change():
    """Detects dtype changes for shared columns, a common schema break.

    We keep the column name but change its dtype to verify the change is
    reported as an (old, new) pair.
    """
    contract_a = Contract(columns={"age": ColumnRule(dtype="int")})
    contract_b = Contract(columns={"age": ColumnRule(dtype="float")})

    report = compare_contracts(contract_a, contract_b)

    # Dtype changes are reported as (old, new).
    assert report.dtype_changes == {"age": ("int", "float")}
    assert report.has_drift is True


def test_range_change():
    """Detects numeric range drift when dtype stays the same.

    We change the min bound for a float column and verify the column is
    flagged in the range_changes set.
    """
    contract_a = Contract(
        columns={"score": ColumnRule(dtype="float", min_value=0.0, max_value=1.0)}
    )
    contract_b = Contract(
        columns={"score": ColumnRule(dtype="float", min_value=-1.0, max_value=1.0)}
    )

    report = compare_contracts(contract_a, contract_b)

    # Same dtype but different bounds should trigger range drift.
    assert report.range_changes == {"score"}
    assert report.has_drift is True


def test_category_and_missingness_changes():
    """Detects category and missingness drift for a shared categorical column.

    We expand allowed values and relax max_missing_frac to confirm both
    change types are captured in the report.
    """
    contract_a = Contract(
        columns={
            "status": ColumnRule(
                dtype="category", allowed_values={"new", "old"}, max_missing_frac=0.05
            )
        }
    )
    contract_b = Contract(
        columns={
            "status": ColumnRule(
                dtype="category",
                allowed_values={"new", "old", "unknown"},
                max_missing_frac=0.10,
            )
        }
    )

    report = compare_contracts(contract_a, contract_b)

    # Allowed values expansion and missingness change are recorded independently.
    assert report.category_changes == {"status"}
    assert report.missingness_changes == {"status": (0.05, 0.10)}
    assert report.has_drift is True


def test_missingness_only_change():
    """Detects missingness drift without implying other drift types.

    We change only max_missing_frac and confirm dtype/range/category drift
    remain empty.
    """
    contract_a = Contract(
        columns={"age": ColumnRule(dtype="int", max_missing_frac=0.05)}
    )
    contract_b = Contract(
        columns={"age": ColumnRule(dtype="int", max_missing_frac=0.10)}
    )

    report = compare_contracts(contract_a, contract_b)

    # Only missingness should change; all other categories remain empty.
    assert report.missingness_changes == {"age": (0.05, 0.10)}
    assert report.dtype_changes == {}
    assert report.range_changes == set()
    assert report.category_changes == set()


def test_category_only_change():
    """Detects category drift without implying other drift types.

    We expand allowed_values and confirm dtype/range/missingness drift
    stay empty.
    """
    contract_a = Contract(
        columns={"status": ColumnRule(dtype="category", allowed_values={"new", "old"})}
    )
    contract_b = Contract(
        columns={
            "status": ColumnRule(
                dtype="category", allowed_values={"new", "old", "unknown"}
            )
        }
    )

    report = compare_contracts(contract_a, contract_b)

    # Only categories should change; other buckets remain empty.
    assert report.category_changes == {"status"}
    assert report.dtype_changes == {}
    assert report.range_changes == set()
    assert report.missingness_changes == {}


def test_range_change_none_to_value():
    """Detects range drift when optional bounds become defined.

    We move min/max from None to numeric values to verify the column is
    flagged as a range change.
    """
    contract_a = Contract(
        columns={"score": ColumnRule(dtype="float", min_value=None, max_value=None)}
    )
    contract_b = Contract(
        columns={"score": ColumnRule(dtype="float", min_value=0.0, max_value=1.0)}
    )

    report = compare_contracts(contract_a, contract_b)

    # Optional bounds become defined, which is a drift.
    assert report.range_changes == {"score"}


def test_category_change_none_to_set():
    """Detects category drift when allowed_values becomes defined.

    We move allowed_values from None to a set to confirm category drift
    is reported.
    """
    contract_a = Contract(
        columns={"status": ColumnRule(dtype="category", allowed_values=None)}
    )
    contract_b = Contract(
        columns={"status": ColumnRule(dtype="category", allowed_values={"new", "old"})}
    )

    report = compare_contracts(contract_a, contract_b)

    # Optional category set becomes defined, which is a drift.
    assert report.category_changes == {"status"}


def test_none_to_none_no_drift():
    """Confirms no drift when optional fields stay None.

    We keep min/max as None in both contracts and verify the report does
    not flag a range or category change.
    """
    contract_a = Contract(
        columns={"score": ColumnRule(dtype="float", min_value=None, max_value=None)}
    )
    contract_b = Contract(
        columns={"score": ColumnRule(dtype="float", min_value=None, max_value=None)}
    )

    report = compare_contracts(contract_a, contract_b)

    # Optional fields unchanged -> no drift reported.
    assert report.range_changes == set()
    assert report.category_changes == set()


def test_dtype_change_blocks_range_drift():
    """Ensures dtype changes suppress range drift for that column.

    We change dtype and bounds to confirm only dtype drift is reported.
    """
    contract_a = Contract(
        columns={"score": ColumnRule(dtype="int", min_value=0.0, max_value=10.0)}
    )
    contract_b = Contract(
        columns={"score": ColumnRule(dtype="float", min_value=-1.0, max_value=10.0)}
    )

    report = compare_contracts(contract_a, contract_b)

    # Dtype change is reported; range changes are ignored when dtype differs.
    assert report.dtype_changes == {"score": ("int", "float")}
    assert report.range_changes == set()


def test_dtype_change_blocks_category_drift():
    """Ensures dtype changes suppress category drift for that column.

    We change dtype and allowed_values to verify only dtype drift appears.
    """
    contract_a = Contract(
        columns={"status": ColumnRule(dtype="category", allowed_values={"new", "old"})}
    )
    contract_b = Contract(
        columns={
            "status": ColumnRule(
                dtype="string", allowed_values={"new", "old", "unknown"}
            )
        }
    )

    report = compare_contracts(contract_a, contract_b)

    # Dtype change is reported; category changes are ignored when dtype differs.
    assert report.dtype_changes == {"status": ("category", "string")}
    assert report.category_changes == set()


def test_invalid_contract_type_raises_typeerror():
    """Validates inputs: non-Contract arguments should raise TypeError.

    We pass a string in place of contract_a to ensure the guard triggers.
    """
    contract_b = Contract(columns={"age": ColumnRule(dtype="int")})

    with pytest.raises(TypeError):
        compare_contracts("not-a-contract", contract_b)


def test_invalid_missing_frac_raises_valueerror():
    """Validates rule constraints: max_missing_frac must be within [0, 1].

    We set max_missing_frac above 1.0 to confirm the validation raises.
    """
    contract_a = Contract(
        columns={"age": ColumnRule(dtype="int", max_missing_frac=1.5)}
    )
    contract_b = Contract(columns={"age": ColumnRule(dtype="int")})

    with pytest.raises(ValueError):
        compare_contracts(contract_a, contract_b)


def test_non_columnrule_raises_typeerror():
    """Validates inputs: every column must map to a ColumnRule instance.

    We inject a plain string for a column rule to ensure TypeError is raised.
    """
    contract_a = Contract(columns={"age": "not-a-rule"})
    contract_b = Contract(columns={"age": ColumnRule(dtype="int")})

    with pytest.raises(TypeError):
        compare_contracts(contract_a, contract_b)


def test_non_numeric_missing_frac_raises_valueerror():
    """Validates rule constraints: max_missing_frac must be numeric.

    We pass a non-numeric value and confirm the validation raises.
    """
    contract_a = Contract(
        columns={"age": ColumnRule(dtype="int", max_missing_frac="high")}
    )
    contract_b = Contract(columns={"age": ColumnRule(dtype="int")})

    with pytest.raises(ValueError):
        compare_contracts(contract_a, contract_b)


def test_invalid_contract_b_raises_valueerror():
    """Validates both contracts: contract_b must pass the same checks.

    We put an invalid missingness fraction in contract_b to ensure its
    validation is not skipped.
    """
    contract_a = Contract(columns={"age": ColumnRule(dtype="int")})
    contract_b = Contract(
        columns={"age": ColumnRule(dtype="int", max_missing_frac=2.0)}
    )

    with pytest.raises(ValueError):
        compare_contracts(contract_a, contract_b)


def test_min_greater_than_max_raises_valueerror():
    """Validates numeric bounds: min_value cannot exceed max_value.

    We set min_value > max_value to confirm the guard raises ValueError.
    """
    contract_a = Contract(
        columns={"age": ColumnRule(dtype="int", min_value=10.0, max_value=1.0)}
    )
    contract_b = Contract(
        columns={"age": ColumnRule(dtype="int", min_value=0.0, max_value=10.0)}
    )

    with pytest.raises(ValueError):
        compare_contracts(contract_a, contract_b)


@pytest.mark.parametrize(
    "contract_a,contract_b",
    [
        (
            Contract(columns={"a": ColumnRule(dtype="int")}),
            Contract(columns={"b": ColumnRule(dtype="int")}),
        ),
        (
            Contract(columns={"a": ColumnRule(dtype="int")}),
            Contract(columns={"a": ColumnRule(dtype="float")}),
        ),
        (
            Contract(columns={"a": ColumnRule(dtype="float", min_value=0.0)}),
            Contract(columns={"a": ColumnRule(dtype="float", min_value=1.0)}),
        ),
        (
            Contract(columns={"a": ColumnRule(dtype="category", allowed_values={"x"})}),
            Contract(
                columns={"a": ColumnRule(dtype="category", allowed_values={"x", "y"})}
            ),
        ),
        (
            Contract(columns={"a": ColumnRule(dtype="int", max_missing_frac=0.05)}),
            Contract(columns={"a": ColumnRule(dtype="int", max_missing_frac=0.10)}),
        ),
    ],
)
def test_has_drift_true_for_any_nonempty_change(contract_a, contract_b):
    """Reports has_drift True for any non-empty drift category.

    We parametrize over each drift type and confirm has_drift flips to True
    whenever at least one drift bucket is populated.
    """
    report = compare_contracts(contract_a, contract_b)
    assert report.has_drift is True


def test_has_drift_false_for_no_drift():
    """Reports has_drift False when contracts are identical.

    We compare two identical contracts to ensure the summary flag is False.
    """
    contract_a = Contract(columns={"age": ColumnRule(dtype="int")})
    contract_b = Contract(columns={"age": ColumnRule(dtype="int")})

    report = compare_contracts(contract_a, contract_b)

    assert report.has_drift is False


def test_multiple_columns_mixed_drift():
    """Aggregates drift across multiple columns and drift types.

    We introduce one change per drift category to confirm all are captured
    in a single report.
    """
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

    # Each drift category should reflect the intended column(s).
    assert report.added_columns == {"e"}
    assert report.removed_columns == set()
    assert report.dtype_changes == {"a": ("int", "float")}
    assert report.range_changes == {"b"}
    assert report.category_changes == {"c"}
    assert report.missingness_changes == {"d": (0.01, 0.10)}


def test_missingness_reports_old_new_order():
    """Confirms missingness changes are ordered as (old, new).

    We increase max_missing_frac and verify the tuple preserves old-to-new
    ordering for downstream reporting.
    """
    contract_a = Contract(
        columns={"age": ColumnRule(dtype="int", max_missing_frac=0.05)}
    )
    contract_b = Contract(
        columns={"age": ColumnRule(dtype="int", max_missing_frac=0.20)}
    )

    report = compare_contracts(contract_a, contract_b)

    assert report.missingness_changes["age"] == (0.05, 0.20)


def test_dtype_reports_old_new_order():
    """Confirms dtype changes are ordered as (old, new).

    We change dtype and ensure the report preserves the old-to-new ordering.
    """
    contract_a = Contract(columns={"age": ColumnRule(dtype="int")})
    contract_b = Contract(columns={"age": ColumnRule(dtype="float")})

    report = compare_contracts(contract_a, contract_b)

    assert report.dtype_changes["age"] == ("int", "float")


def test_no_drift():
    """Confirms no drift yields empty buckets and has_drift False.

    We keep all fields identical to verify each drift bucket is empty and
    the summary flag remains False.
    """
    contract_a = Contract(
        columns={"age": ColumnRule(dtype="int", min_value=0.0, max_value=120.0)}
    )
    contract_b = Contract(
        columns={"age": ColumnRule(dtype="int", min_value=0.0, max_value=120.0)}
    )

    report = compare_contracts(contract_a, contract_b)

    assert report.added_columns == set()
    assert report.removed_columns == set()
    assert report.dtype_changes == {}
    assert report.range_changes == set()
    assert report.category_changes == set()
    assert report.missingness_changes == {}
    assert report.has_drift is False
