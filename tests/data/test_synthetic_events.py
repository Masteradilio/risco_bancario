from decimal import Decimal

from src.data.synthetic import (
    PopulationConfig,
    generate_credit_events,
    generate_monthly_history,
    generate_population,
)


def event_bundle():
    population = generate_population(PopulationConfig(seed=91, clients=40, contracts_per_client=2))
    history = generate_monthly_history(population)
    return population, history, generate_credit_events(population, history)


def test_defaults_follow_observable_snapshots_and_are_reproducible() -> None:
    population, history, events = event_bundle()
    assert events == generate_credit_events(population, history)
    assert events.defaults
    for default in events.defaults:
        if default.is_redefault:
            continue
        prior = [
            item
            for item in history.snapshots
            if item.contract_id == default.contract_id
            and item.reference_date < default.default_date
        ]
        assert prior
        assert default.exposure_at_default == prior[-1].balance


def test_collections_and_recoveries_occur_after_initial_default() -> None:
    _, _, events = event_bundle()
    defaults = {item.default_id: item for item in events.defaults}
    assert all(
        item.event_date > defaults[item.default_id].default_date for item in events.collections
    )
    assert all(
        item.recovery_date > defaults[item.default_id].default_date for item in events.recoveries
    )
    assert all(
        item.net_amount == item.gross_amount - item.cost_amount for item in events.recoveries
    )
    cash_by_default: dict[str, list] = {}
    for item in events.recoveries:
        if item.source == "cash_collection":
            cash_by_default.setdefault(item.default_id, []).append(item)
    assert cash_by_default
    assert all(len(items) == 6 for items in cash_by_default.values())
    assert all(
        len({item.recovery_date for item in items}) == 6 for items in cash_by_default.values()
    )


def test_collateral_execution_and_costs_are_generated() -> None:
    _, _, events = event_bundle()
    secured = [item for item in events.recoveries if item.source == "collateral_execution"]
    assert secured
    assert all(item.gross_amount > 0 and item.cost_amount > 0 for item in secured)
    assert all(item.cost_type == "judicial_and_operational" for item in secured)
    assert all(
        item.cost_type == "operational"
        for item in events.recoveries
        if item.source in {"cash_collection", "post_writeoff_collection"}
    )


def test_cures_and_redefaults_have_valid_temporal_order() -> None:
    _, _, events = event_bundle()
    defaults = {item.default_id: item for item in events.defaults}
    assert events.cures
    assert all(item.cure_date > defaults[item.default_id].default_date for item in events.cures)
    redefaults = [item for item in events.defaults if item.is_redefault]
    assert redefaults
    cure_by_contract = {item.contract_id: item for item in events.cures}
    assert all(
        item.default_date > cure_by_contract[item.contract_id].cure_date for item in redefaults
    )


def test_writeoffs_reconcile_pre_writeoff_net_recoveries() -> None:
    _, _, events = event_bundle()
    defaults = {item.default_id: item for item in events.defaults}
    assert events.writeoffs
    for writeoff in events.writeoffs:
        default = defaults[writeoff.default_id]
        recovered = sum(
            (
                item.net_amount
                for item in events.recoveries
                if item.default_id == writeoff.default_id and not item.post_writeoff
            ),
            Decimal("0"),
        )
        assert recovered + writeoff.amount == default.exposure_at_default
        assert writeoff.writeoff_date > default.default_date


def test_post_writeoff_recoveries_are_retained() -> None:
    _, _, events = event_bundle()
    writeoffs = {item.default_id: item for item in events.writeoffs}
    post = [item for item in events.recoveries if item.post_writeoff]
    assert post
    assert all(item.recovery_date > writeoffs[item.default_id].writeoff_date for item in post)


def test_public_event_tables_have_no_latent_fields() -> None:
    _, _, events = event_bundle()
    assert all(
        not key.startswith("_latent")
        for rows in events.as_tables().values()
        for row in rows
        for key in row
    )
