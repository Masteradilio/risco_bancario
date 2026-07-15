"""Contract tests for the local/CI quality command."""

from scripts.quality import command_matrix


def test_quality_matrix_covers_all_required_gates() -> None:
    matrix = command_matrix()
    flattened = [" ".join(command) for commands in matrix.values() for command in commands]

    assert set(matrix) == {"static", "tests", "frontend"}
    assert any("black --check" in command for command in flattened)
    assert any("ruff check" in command for command in flattened)
    assert any("ruff check src --select S" in command for command in flattened)
    assert any("mypy" in command for command in flattened)
    assert any("--cov=src" in command and "--cov-report=xml" in command for command in flattened)
    assert all(
        "tests/documentation" in command
        for command in flattened
        if "black --check" in command or "ruff check" in command or "pytest" in command
        if "backend/bancos_de_dados/tests" not in command
        if "ruff check src --select S" not in command
    )
    assert any("backend/bancos_de_dados/tests" in command for command in flattened)
    assert any("npm" in command and "run build" in command for command in flattened)


def test_quality_commands_do_not_delegate_to_a_shell() -> None:
    forbidden = {"sh", "bash", "powershell", "pwsh", "cmd", "cmd.exe"}
    for commands in command_matrix().values():
        for command in commands:
            assert command[0].lower() not in forbidden
