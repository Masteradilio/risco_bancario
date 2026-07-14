from pathlib import Path

DESIGN = Path("docs/data/SYNTHETIC_DATA_DESIGN.md")


def test_design_covers_required_causal_components() -> None:
    text = DESIGN.read_text(encoding="utf-8")
    required = (
        "## Grafo de entidades",
        "## Variáveis latentes internas",
        "## Ciclo macroeconômico",
        "### Renda e emprego",
        "### Utilização e pagamentos",
        "### Atraso e default",
        "## Garantias, renegociação, cura e perdas",
    )
    assert all(item in text for item in required)


def test_target_is_future_derived_and_generator_is_separate() -> None:
    text = DESIGN.read_text(encoding="utf-8")
    assert "(t, t+12 meses]" in text
    assert "não importa pipelines de treino" in text
    assert "Não existe coluna estática" in text


def test_latent_fields_are_forbidden_in_public_exports() -> None:
    text = DESIGN.read_text(encoding="utf-8")
    assert "prefixo `_latent`" in text
    assert "allowlists de schema" in text
    assert "nenhum dataset público ou de modelagem" in text
