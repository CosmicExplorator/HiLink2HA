import pytest

from custom_components.huawei_sms.dictionary import InteractionFamily, understand


def test_understand_french_command() -> None:
    intent = understand("allume lumiere")
    assert intent.family is InteractionFamily.COMMAND
    assert intent.action == "turn_on"
    assert intent.target == "lumiere"
    assert intent.allowed_domains == ("light", "switch")


def test_temperature_range_is_restricted() -> None:
    with pytest.raises(ValueError, match="5 et 35"):
        understand("regle chauffage 50 degres")


def test_help_is_available_in_both_languages() -> None:
    assert understand("help").action == "help"
    assert understand("aide").action == "help"
