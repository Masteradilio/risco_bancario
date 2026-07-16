import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from src.data.synthetic import generate_macroeconomic_bundle
from src.data.synthetic.macroeconomics import _load_policy


def test_macro_bundle_is_reproducible_and_versioned() -> None:
    bundle = generate_macroeconomic_bundle(seed=91)
    assert bundle == generate_macroeconomic_bundle(seed=91)
    assert bundle.policy_version == "1.0.0"
    assert len(bundle.policy_hash) == 64


def test_observed_history_is_monthly_and_complete() -> None:
    observed = generate_macroeconomic_bundle(seed=91).observed
    assert len(observed) == 120
    assert observed[0].reference_date == date(2016, 1, 1)
    assert observed[-1].reference_date == date(2025, 12, 1)
    assert len({item.reference_date for item in observed}) == len(observed)
    assert {item.regime for item in observed} >= {"recession", "recovery", "shock"}


def test_four_forward_paths_have_monthly_trajectories() -> None:
    scenarios = generate_macroeconomic_bundle(seed=91).scenarios
    assert {item.scenario_id for item in scenarios} == {
        "upside",
        "base",
        "downside",
        "stress",
    }
    for scenario_id in {item.scenario_id for item in scenarios}:
        path = [item for item in scenarios if item.scenario_id == scenario_id]
        assert len(path) == 60
        assert path[0].reference_date == date(2026, 1, 1)
        assert path[-1].reference_date == date(2030, 12, 1)


def test_probability_weights_are_versioned_and_stress_is_unweighted() -> None:
    weights = dict(generate_macroeconomic_bundle(seed=91).scenario_weights)
    assert sum(weights.values()) == Decimal("1.0000")
    assert weights == {
        "upside": Decimal("0.1500"),
        "base": Decimal("0.7000"),
        "downside": Decimal("0.1500"),
        "stress": Decimal("0.0000"),
    }


def test_terminal_paths_have_economically_ordered_severity() -> None:
    scenarios = generate_macroeconomic_bundle(seed=91).scenarios
    terminal = {
        item.scenario_id: item
        for item in scenarios
        if item.reference_date.year == 2030 and item.reference_date.month == 12
    }
    assert terminal["upside"].gdp_growth > terminal["base"].gdp_growth
    assert terminal["base"].gdp_growth > terminal["downside"].gdp_growth
    assert terminal["downside"].gdp_growth > terminal["stress"].gdp_growth
    assert terminal["upside"].unemployment < terminal["base"].unemployment
    assert terminal["base"].unemployment < terminal["downside"].unemployment
    assert terminal["downside"].unemployment < terminal["stress"].unemployment


def test_risk_pressure_is_non_linear_under_adverse_paths() -> None:
    scenarios = generate_macroeconomic_bundle(seed=91).scenarios
    terminal = {
        item.scenario_id: item for item in scenarios if item.reference_date == date(2030, 12, 1)
    }
    downside_increment = terminal["downside"].risk_pressure - terminal["base"].risk_pressure
    stress_increment = terminal["stress"].risk_pressure - terminal["base"].risk_pressure
    assert terminal["upside"].risk_pressure < terminal["base"].risk_pressure
    assert downside_increment > 0
    assert stress_increment > downside_increment * 2


def test_public_macro_tables_have_no_latent_fields() -> None:
    tables = generate_macroeconomic_bundle(seed=91).as_tables()
    assert all(
        not key.startswith("_latent") for rows in tables.values() for row in rows for key in row
    )


@pytest.mark.parametrize(
    "mutation,message",
    [
        (
            lambda document: document["forecast"]["scenarios"].reverse(),
            "requires upside",
        ),
        (
            lambda document: document["forecast"]["scenarios"][0].update(weight="0.20"),
            "weights must sum",
        ),
        (
            lambda document: (
                document["forecast"]["scenarios"][1].update(weight="0.60"),
                document["forecast"]["scenarios"][-1].update(weight="0.10"),
            ),
            "stress is a sensitivity",
        ),
    ],
)
def test_macro_policy_fails_closed(tmp_path: Path, mutation, message: str) -> None:
    source = Path("config/synthetic/macroeconomic_scenarios/1.0.0.json")
    document = json.loads(source.read_text(encoding="utf-8"))
    mutation(document)
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        _load_policy(path)
