import pytest

from custom_components.huawei_sms.resolver import EntityResolver, normalize_name


def test_normalize_name() -> None:
    assert normalize_name("Lumière_Séjour") == "lumiere sejour"


def test_resolve_only_declared_entity() -> None:
    resolver = EntityResolver(
        {"targets": {"salon": {"lumière": "light.salon", "température": "sensor.salon"}}}
    )
    assert resolver.resolve("salon", "lumiere", ("light",)) == "light.salon"


def test_reject_domain_mismatch() -> None:
    resolver = EntityResolver({"targets": {"salon": {"temp": "sensor.salon"}}})
    with pytest.raises(ValueError, match="incompatible"):
        resolver.resolve("salon", "temp", ("light",))


def test_reject_invalid_entity_id() -> None:
    with pytest.raises(ValueError, match="invalide"):
        EntityResolver({"targets": {"salon": "../../secrets.yaml"}})
