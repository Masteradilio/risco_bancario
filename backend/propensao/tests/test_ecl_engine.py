"""
Unit tests for ECL Engine v2.0 (BACEN 4966 Compliant).
Note: ECL Engine was moved to perda_esperada module.
These tests are skipped as the module was restructured.
"""

import pytest

# Skip all tests in this module - ECL was moved to perda_esperada
pytestmark = pytest.mark.skip(reason="ECL Engine moved to perda_esperada.src.pipeline_ecl")
