"""Deterministic synthetic population and contract origination."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal
from hashlib import sha256
from random import Random

from ...domain.exceptions import DomainValidationError

CENT = Decimal("0.01")
RATE = Decimal("0.00000001")


@dataclass(frozen=True, slots=True)
class PopulationConfig:
    seed: int = 20260714
    clients: int = 30
    contracts_per_client: int = 2
    start_date: date = date(2016, 1, 1)
    end_date: date = date(2025, 12, 1)

    def __post_init__(self) -> None:
        if self.clients < 7:
            raise DomainValidationError("clients must be at least 7 to cover the product catalog")
        if self.contracts_per_client < 1:
            raise DomainValidationError("contracts_per_client must be positive")
        if self.end_date < self.start_date:
            raise DomainValidationError("end_date cannot precede start_date")


@dataclass(frozen=True, slots=True)
class EconomicGroupRecord:
    economic_group_id: str
    sector: str


@dataclass(frozen=True, slots=True)
class CounterpartyRecord:
    counterparty_id: str
    party_type: str
    economic_group_id: str | None
    inception_date: date


@dataclass(frozen=True, slots=True)
class ClientRecord:
    client_id: str
    counterparty_id: str
    client_type: str
    relationship_start_date: date
    region: str


@dataclass(frozen=True, slots=True)
class ContractRecord:
    contract_id: str
    client_id: str
    counterparty_id: str
    product_code: str
    facility_type: str
    origination_date: date
    maturity_date: date
    effective_interest_rate: Decimal
    original_amount: Decimal
    credit_limit: Decimal
    initial_drawn_amount: Decimal
    currency: str
    acquired_credit_impaired: bool
    policy_version: str


@dataclass(frozen=True, slots=True)
class ScheduleRecord:
    contract_id: str
    installment_number: int
    due_date: date
    opening_balance: Decimal
    principal: Decimal
    interest: Decimal
    payment: Decimal
    closing_balance: Decimal


@dataclass(frozen=True, slots=True)
class CollateralRecord:
    collateral_id: str
    contract_id: str
    collateral_type: str
    valuation_date: date
    appraised_value: Decimal
    enforceable_share: Decimal
    currency: str


@dataclass(frozen=True, slots=True)
class SyntheticPortfolio:
    groups: tuple[EconomicGroupRecord, ...]
    counterparties: tuple[CounterpartyRecord, ...]
    clients: tuple[ClientRecord, ...]
    contracts: tuple[ContractRecord, ...]
    schedules: tuple[ScheduleRecord, ...]
    collateral: tuple[CollateralRecord, ...]
    generator_version: str
    seed: int

    def as_tables(self) -> dict[str, list[dict[str, object]]]:
        return {
            "economic_groups": [asdict(item) for item in self.groups],
            "counterparties": [asdict(item) for item in self.counterparties],
            "clients": [asdict(item) for item in self.clients],
            "contracts": [asdict(item) for item in self.contracts],
            "schedules": [asdict(item) for item in self.schedules],
            "collateral": [asdict(item) for item in self.collateral],
        }


@dataclass(frozen=True, slots=True)
class ProductProfile:
    code: str
    facility_type: str
    term_months: int
    annual_rate: Decimal
    minimum_amount: int
    maximum_amount: int
    collateral_type: str | None = None
    acquired_credit_impaired: bool = False


PRODUCTS = (
    ProductProfile("personal_loan", "amortized", 36, Decimal("0.24"), 2_000, 50_000),
    ProductProfile("vehicle_finance", "amortized", 60, Decimal("0.18"), 15_000, 120_000, "vehicle"),
    ProductProfile("mortgage", "amortized", 240, Decimal("0.11"), 80_000, 500_000, "real_estate"),
    ProductProfile("credit_card", "revolving", 12, Decimal("0.72"), 1_000, 30_000),
    ProductProfile("overdraft", "revolving", 12, Decimal("0.48"), 500, 15_000),
    ProductProfile("credit_commitment", "commitment", 24, Decimal("0.15"), 10_000, 200_000),
    ProductProfile(
        "financial_guarantee", "financial_guarantee", 18, Decimal("0.03"), 20_000, 250_000
    ),
    ProductProfile(
        "acquired_distressed",
        "amortized",
        48,
        Decimal("0.20"),
        5_000,
        80_000,
        acquired_credit_impaired=True,
    ),
)


def _rng(seed: int, namespace: str) -> Random:
    digest = sha256(f"{seed}:{namespace}".encode()).digest()
    return Random(int.from_bytes(digest[:8], "big"))  # noqa: S311 - deterministic synthetic data


def _money(value: Decimal | int | str) -> Decimal:
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_EVEN)


def _rate(value: Decimal | int | str) -> Decimal:
    return Decimal(value).quantize(RATE, rounding=ROUND_HALF_EVEN)


def _add_months(value: date, months: int) -> date:
    month_index = value.year * 12 + value.month - 1 + months
    year, month_zero = divmod(month_index, 12)
    return date(year, month_zero + 1, min(value.day, 28))


def _random_month(rng: Random, start: date, end: date) -> date:
    span = (end.year - start.year) * 12 + end.month - start.month
    return _add_months(start, rng.randint(0, span))


def _annuity_schedule(contract: ContractRecord, months: int) -> tuple[ScheduleRecord, ...]:
    monthly_rate = contract.effective_interest_rate / Decimal("12")
    balance = contract.initial_drawn_amount
    if monthly_rate == 0:
        fixed_payment = _money(balance / months)
    else:
        fixed_payment = _money(
            balance * monthly_rate / (Decimal("1") - (Decimal("1") + monthly_rate) ** -months)
        )
    rows: list[ScheduleRecord] = []
    for installment in range(1, months + 1):
        opening = balance
        interest = _money(opening * monthly_rate)
        principal = _money(fixed_payment - interest)
        if installment == months or principal > opening:
            principal = opening
            payment = _money(principal + interest)
        else:
            payment = fixed_payment
        balance = _money(opening - principal)
        rows.append(
            ScheduleRecord(
                contract.contract_id,
                installment,
                _add_months(contract.origination_date, installment),
                opening,
                principal,
                interest,
                payment,
                balance,
            )
        )
    return tuple(rows)


def generate_population(config: PopulationConfig | None = None) -> SyntheticPortfolio:
    config = config or PopulationConfig()
    population_rng = _rng(config.seed, "population")
    contract_rng = _rng(config.seed, "contracts")
    groups: list[EconomicGroupRecord] = []
    counterparties: list[CounterpartyRecord] = []
    clients: list[ClientRecord] = []
    sectors = ("services", "retail", "industry", "agriculture", "technology")
    regions = ("north", "northeast", "central_west", "southeast", "south")

    for index in range(config.clients):
        party_type = "PF" if index % 3 else "PJ"
        group_id = None
        if party_type == "PJ":
            group_number = index // 6 + 1
            group_id = f"GRP-{group_number:04d}"
            if not any(item.economic_group_id == group_id for item in groups):
                groups.append(EconomicGroupRecord(group_id, sectors[group_number % len(sectors)]))
        counterparty_id = f"CP-{index + 1:06d}"
        client_id = f"CL-{index + 1:06d}"
        inception = _random_month(population_rng, date(2005, 1, 1), config.start_date)
        relationship = _random_month(population_rng, inception, config.start_date)
        counterparties.append(CounterpartyRecord(counterparty_id, party_type, group_id, inception))
        clients.append(
            ClientRecord(
                client_id, counterparty_id, party_type, relationship, regions[index % len(regions)]
            )
        )

    contracts: list[ContractRecord] = []
    schedules: list[ScheduleRecord] = []
    collateral: list[CollateralRecord] = []
    contract_index = 0
    for client in clients:
        for _ in range(config.contracts_per_client):
            profile = PRODUCTS[contract_index % len(PRODUCTS)]
            contract_index += 1
            amount = _money(contract_rng.randint(profile.minimum_amount, profile.maximum_amount))
            origination = _random_month(contract_rng, config.start_date, config.end_date)
            maturity = _add_months(origination, profile.term_months)
            if profile.facility_type == "revolving":
                credit_limit = amount
                drawn = _money(amount * Decimal(str(contract_rng.uniform(0.05, 0.85))))
            elif profile.facility_type in {"commitment", "financial_guarantee"}:
                credit_limit = amount
                drawn = Decimal("0.00")
            else:
                credit_limit = amount
                drawn = amount
            contract = ContractRecord(
                f"CT-{contract_index:08d}",
                client.client_id,
                client.counterparty_id,
                profile.code,
                profile.facility_type,
                origination,
                maturity,
                _rate(profile.annual_rate),
                amount,
                credit_limit,
                drawn,
                "BRL",
                profile.acquired_credit_impaired,
                "2026.07.1",
            )
            contracts.append(contract)
            if profile.facility_type == "amortized":
                schedules.extend(_annuity_schedule(contract, profile.term_months))
            if profile.collateral_type:
                multiplier = (
                    Decimal("1.20") if profile.collateral_type == "real_estate" else Decimal("1.10")
                )
                collateral.append(
                    CollateralRecord(
                        f"COL-{len(collateral) + 1:07d}",
                        contract.contract_id,
                        profile.collateral_type,
                        origination,
                        _money(amount * multiplier),
                        Decimal("0.90000000"),
                        "BRL",
                    )
                )

    return SyntheticPortfolio(
        tuple(groups),
        tuple(counterparties),
        tuple(clients),
        tuple(contracts),
        tuple(schedules),
        tuple(collateral),
        "0.1.0",
        config.seed,
    )
