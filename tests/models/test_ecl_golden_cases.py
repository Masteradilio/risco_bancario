import csv
from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path

from src.application.services import load_scenario_set
from src.domain.contracts import (
    AmortizationMethod,
    AmortizationTerms,
    ModificationRequest,
    modify_contract,
    project_amortized_schedule,
)
from src.domain.scenarios import MacroTrajectoryPoint, MacroVariable
from src.ecl.calculation import (
    BaselineRiskPeriod,
    POCICashFlow,
    POCIScenarioCashFlows,
    Stage1ContractInput,
    Stage1RiskPeriod,
    Stage2ContractInput,
    Stage2RiskPeriod,
    calculate_probability_weighted_scenario_ecl,
    calculate_stage1_ecl,
    calculate_stage2_ecl,
    measure_poci_scenarios,
)
from src.ecl.stage3 import (
    Stage3CashFlowPeriod,
    Stage3ContractInput,
    Stage3ScenarioProjection,
    calculate_stage3_ecl,
)
from src.models.forward_looking import load_macro_risk_policy

FIXTURE = Path(__file__).parents[1] / "fixtures" / "golden" / "ecl_cases.csv"
SCENARIOS = ("upside", "base", "downside", "stress")


def _expected(case_id: str) -> Decimal:
    with FIXTURE.open(encoding="utf-8", newline="") as stream:
        row = next(item for item in csv.DictReader(stream) if item["case_id"] == case_id)
    return Decimal(row["expected_value"])


def _month(start: date, offset: int) -> date:
    index = start.month - 1 + offset
    return date(start.year + index // 12, index % 12 + 1, 1)


def _neutral_scenario_set(start: date, months: int):
    scenario_set = load_scenario_set(seed=91)
    values = (
        MacroVariable("gdp_growth", "2.20"),
        MacroVariable("inflation", "4.50"),
        MacroVariable("policy_rate", "9.00"),
        MacroVariable("unemployment", "7.50"),
        MacroVariable("household_debt", "49.00"),
        MacroVariable("risk_pressure", "0.00"),
    )
    trajectories = tuple(
        replace(
            trajectory,
            periods=tuple(
                MacroTrajectoryPoint(_month(start, offset), values) for offset in range(months)
            ),
        )
        for trajectory in scenario_set.trajectories
    )
    return replace(scenario_set, reference_date=start, trajectories=trajectories)


def _stage3_projection(period: Stage3CashFlowPeriod) -> tuple[Stage3ScenarioProjection, ...]:
    return tuple(Stage3ScenarioProjection(scenario_id, (period,)) for scenario_id in SCENARIOS)


def test_golden_stage1_amortized() -> None:
    periods = (
        Stage1RiskPeriod(date(2026, 1, 1), "0.10", "0.50", "100"),
        Stage1RiskPeriod(date(2026, 2, 1), "0.10", "0.50", "90"),
    )
    result = calculate_stage1_ecl(
        Stage1ContractInput("G-ST1", date(2025, 12, 31), "0", periods),
        _neutral_scenario_set(date(2026, 1, 1), 2),
        load_macro_risk_policy(),
    )
    assert result.scenario_ecl.probability_weighted_ecl == _expected("stage1_amortized")
    for scenario in result.scenario_ecl.scenario_results:
        for period in scenario.periods:
            assert period.expected_loss == (
                period.marginal_pd * period.lgd * period.ead * period.discount_factor
            ).quantize(Decimal("0.01"))


def test_golden_stage2_lifetime() -> None:
    periods = tuple(
        Stage2RiskPeriod(
            _month(date(2026, 1, 1), offset), "0.10", "0.50", "100", expected_prepayment_rate="0.10"
        )
        for offset in range(3)
    )
    result = calculate_stage2_ecl(
        Stage2ContractInput("G-ST2", date(2025, 12, 31), "0", 3, 0, "0", periods),
        _neutral_scenario_set(date(2026, 1, 1), 3),
        load_macro_risk_policy(),
    )
    assert result.scenario_ecl.probability_weighted_ecl == _expected("stage2_lifetime")


def test_golden_stage3_cash_shortfall() -> None:
    period = Stage3CashFlowPeriod(
        date(2026, 1, 1), "100", "60", collateral_recovery="20", collection_costs="5"
    )
    result = calculate_stage3_ecl(
        Stage3ContractInput(
            "G-ST3", date(2025, 12, 31), "100", "25", "0", _stage3_projection(period)
        ),
        _neutral_scenario_set(date(2026, 1, 1), 1),
    )
    assert result.probability_weighted_ecl == _expected("stage3_cash_shortfall")


def test_golden_revolving_with_ccf() -> None:
    baseline = (BaselineRiskPeriod(date(2026, 1, 1), "0.10", "0.50", "100", "100", "0.50", "1"),)
    result = calculate_probability_weighted_scenario_ecl(
        baseline,
        _neutral_scenario_set(date(2026, 1, 1), 1),
        "portfolio",
        load_macro_risk_policy(),
    )
    assert result.probability_weighted_ecl == _expected("revolving_ccf")


def test_golden_secured_contract() -> None:
    period = Stage3CashFlowPeriod(date(2026, 1, 1), "100", "20", guarantee_recovery="50")
    result = calculate_stage3_ecl(
        Stage3ContractInput(
            "G-SEC", date(2025, 12, 31), "100", "30", "0", _stage3_projection(period)
        ),
        _neutral_scenario_set(date(2026, 1, 1), 1),
    )
    assert result.probability_weighted_ecl == _expected("secured_contract")


def test_golden_poci() -> None:
    payment_date = date(2027, 1, 1)
    cashflows = tuple(
        POCIScenarioCashFlows(scenario_id, (POCICashFlow(payment_date, amount),))
        for scenario_id, amount in zip(SCENARIOS, ("99", "88", "77", "66"), strict=True)
    )
    result = measure_poci_scenarios(
        "G-POCI",
        date(2026, 1, 1),
        "80",
        (POCICashFlow(payment_date, "110"),),
        (POCICashFlow(payment_date, "88"),),
        cashflows,
        load_scenario_set(seed=91),
    )
    assert result.probability_weighted_lifetime_ecl == _expected("poci")


def test_golden_modification_uses_revised_schedule_and_original_eir() -> None:
    original_terms = AmortizationTerms(
        "G-MOD", date(2026, 1, 15), "12000", 12, "0.12", AmortizationMethod.PRICE
    )
    original = project_amortized_schedule(original_terms)
    carrying = original.periods[2].closing_balance
    revised_terms = AmortizationTerms(
        "G-MOD", date(2026, 4, 15), carrying, 15, "0.08", AmortizationMethod.PRICE
    )
    modification = modify_contract(
        original, ModificationRequest(3, revised_terms, derecognize=False)
    )
    start = date(2026, 4, 1)
    periods = tuple(
        Stage2RiskPeriod(
            _month(start, offset),
            "0.01",
            "0.40",
            schedule_period.opening_balance,
        )
        for offset, schedule_period in enumerate(modification.revised_schedule.periods)
    )
    result = calculate_stage2_ecl(
        Stage2ContractInput(
            "G-MOD",
            date(2026, 3, 31),
            modification.applied_effective_interest_rate,
            15,
            0,
            "0",
            periods,
        ),
        _neutral_scenario_set(start, 15),
        load_macro_risk_policy(),
    )
    assert modification.applied_effective_interest_rate == original.effective_interest_rate
    assert result.scenario_ecl.probability_weighted_ecl == _expected("modification")


def test_golden_multi_scenario_integrates_before_weighting() -> None:
    baseline = tuple(
        BaselineRiskPeriod(
            _month(date(2026, 1, 1), offset), "0.10", "0.50", "100", "100", "0.50", "1"
        )
        for offset in range(3)
    )
    result = calculate_probability_weighted_scenario_ecl(
        baseline, load_scenario_set(seed=91), "portfolio", load_macro_risk_policy()
    )
    assert result.probability_weighted_ecl == _expected("multi_scenario")
    repeated = calculate_probability_weighted_scenario_ecl(
        baseline, load_scenario_set(seed=91), "portfolio", load_macro_risk_policy()
    )
    assert repeated == result
