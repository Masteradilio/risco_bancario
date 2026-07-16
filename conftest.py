"""Repository-wide deterministic test environment."""

from __future__ import annotations

import os

# Joblib cannot discover physical cores on current Windows runners after WMIC
# removal. Its documented override prevents a non-actionable runtime warning and
# keeps parallelism deterministic in every pytest tree, including legacy tests.
os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")
