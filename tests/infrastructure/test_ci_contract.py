"""Executable contracts for CI and production container definitions."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_github_actions_are_immutable_and_required_gates_exist() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    delivery = (ROOT / ".github/workflows/cd.yml").read_text(encoding="utf-8")
    actions = re.findall(r"uses:\s+([^\s#]+)", workflow + delivery)

    assert {"quality:", "dependency-audit:", "secret-scan:", "containers:"} <= set(
        line.strip() for line in workflow.splitlines()
    )
    assert actions
    assert all(re.fullmatch(r"[^@]+@[0-9a-f]{40}", action) for action in actions)
    assert "permissions:\n  contents: read" in workflow
    assert "requirements-ci.lock" in workflow


def test_delivery_is_immutable_environment_scoped_and_supports_release_notes() -> None:
    workflow = (ROOT / ".github/workflows/cd.yml").read_text(encoding="utf-8")

    assert "environment: ${{ needs.plan.outputs.environment }}" in workflow
    assert "packages: write" in workflow
    assert "--generate-notes" in workflow
    assert "python -m scripts.deploy plan" in workflow
    assert "push: true" in workflow
    assert ":latest" not in workflow


def test_api_container_is_non_root_and_has_a_healthcheck() -> None:
    dockerfile = (ROOT / "docker/Dockerfile.api").read_text(encoding="utf-8")

    assert "USER appuser" in dockerfile
    assert "HEALTHCHECK" in dockerfile
    assert "src.interfaces.api.app:create_app" in dockerfile
    assert "COPY --chown=appuser:appuser src ./src" in dockerfile


def test_frontend_container_is_non_root_and_proxies_only_api() -> None:
    dockerfile = (ROOT / "docker/Dockerfile.frontend").read_text(encoding="utf-8")
    nginx = (ROOT / "docker/nginx.conf").read_text(encoding="utf-8")

    assert "nginxinc/nginx-unprivileged" in dockerfile
    assert "npm ci" in dockerfile
    assert "location /api/" in nginx
    assert "proxy_pass http://api:8000" in nginx
    assert "try_files $uri $uri/ /index.html" in nginx
