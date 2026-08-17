from __future__ import annotations

from pathlib import Path

from scripts.run_portfolio_benchmark import (
    generate_benchmark_markdown_report,
    run_governance_dimension,
    run_model_risk_dimension,
    run_performance_dimension,
    run_stress_test_dimension,
)


def test_portfolio_benchmark_dimensions_and_report_generation(tmp_path: Path) -> None:
    # 1. Stress test dimension
    stress = run_stress_test_dimension()
    assert stress["n_contracts"] == 1000
    assert stress["total_ecl_stressed"] > stress["total_ecl_base"]
    assert stress["sicr_migrations"] > 0

    # 2. Model risk dimension
    mrm = run_model_risk_dimension(stress)
    assert mrm["auc_roc"] > 0.75
    assert mrm["brier_score"] < 0.05

    # 3. Performance dimension (small batch for quick unit test)
    perf = run_performance_dimension(batch_size=100)
    assert perf["batch_size"] == 100
    assert perf["throughput_per_second"] > 0

    # 4. Governance dimension
    gov = run_governance_dimension()
    assert gov["golden_cases_checked"] > 0
    assert gov["reconciliation_passed"] is True

    # 5. Report generation
    report_file = tmp_path / "TEST_BENCHMARK.md"
    results = {
        "stress_testing": stress,
        "model_risk": mrm,
        "performance": perf,
        "governance": gov,
    }
    generate_benchmark_markdown_report(results, report_file)
    assert report_file.is_file()
    content = report_file.read_text(encoding="utf-8")
    assert "Scorecard de Robustez" in content
    assert "Throughput" in content
