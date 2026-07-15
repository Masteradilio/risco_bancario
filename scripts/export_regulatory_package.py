"""Export the versioned regulatory evidence package."""

from pathlib import Path

from src.regulatory.traceability.package import export_regulatory_package

if __name__ == "__main__":
    result = export_regulatory_package(Path("evidence/regulatory"))
    print(
        f"regulatory package: {len(result['artifacts'])} artifacts, "
        f"{result['release_blockers']} blockers"
    )
