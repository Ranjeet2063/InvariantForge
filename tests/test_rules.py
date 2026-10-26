"""
Tests for Ramanujan Mathematical Invariant Catalog.
"""

from invariant_forge.invariant_rules import InvariantCatalog


def test_invariant_catalog_lookup():
    rules = InvariantCatalog.get_applicable_rules(["VAULT_ERC4626"])
    assert len(rules) >= 3
    rule_ids = [r.rule_id for r in rules]
    assert "INV_VAULT_001" in rule_ids
    assert "INV_VAULT_002" in rule_ids
    assert "INV_VAULT_003" in rule_ids


def test_generic_fallback_rules():
    rules = InvariantCatalog.get_applicable_rules(["UNKNOWN_PATTERN"])
    assert len(rules) >= 1
    assert any(r.rule_id == "INV_VAULT_001" for r in rules)
