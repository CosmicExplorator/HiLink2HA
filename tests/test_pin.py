"""Test PIN requests without contacting a modem or consuming SIM attempts."""

from unittest.mock import MagicMock

import pytest

from custom_components.huawei_sms.pin import PinManager, validate_pin


@pytest.fixture
def modem():
    connection = MagicMock()
    client = MagicMock()
    manager = PinManager("http://modem/", connection, client)
    return manager, connection, client.return_value.pin


@pytest.mark.parametrize("value", ["0123", "12345678"])
def test_valid_pin_preserves_zeroes(value):
    assert validate_pin(value) == value


@pytest.mark.parametrize(
    "value", [1234, None, "123", "123456789", "１２３４", "1234\n", " 1234"]
)
def test_invalid_pin(value):
    with pytest.raises(ValueError):
        validate_pin(value)


@pytest.mark.parametrize(
    "operation,code",
    [
        ("verify_pin", "0"),
        ("enable_pin", "1"),
        ("disable_pin", "2"),
        ("change_pin", "3"),
    ],
)
def test_operation_payload(modem, operation, code):
    manager, connection, pin = modem
    new_pin = "0567" if operation == "change_pin" else None
    manager.operate(operation, "0123", new_pin)
    connection.assert_called_once_with("http://modem/")
    pin.operate.assert_called_once_with(
        operate_type=code, current_pin="0123", new_pin=new_pin
    )
    assert "0123" not in repr(vars(manager))


def test_bad_new_pin_never_contacts_modem(modem):
    manager, connection, pin = modem
    with pytest.raises(ValueError):
        manager.operate("change_pin", "0123", "bad")
    connection.assert_not_called()
    pin.operate.assert_not_called()


@pytest.mark.parametrize(
    "operation", ["verify_pin", "enable_pin", "disable_pin", "change_pin"]
)
def test_no_retry_on_failure(modem, operation):
    manager, _, pin = modem
    pin.operate.side_effect = RuntimeError("Rejected")
    with pytest.raises(RuntimeError):
        manager.operate(
            operation, "0123", "0567" if operation == "change_pin" else None
        )
    assert pin.operate.call_count == 1


def test_status_filters_secrets_and_preserves_zero_attempts(modem):
    manager, _, pin = modem
    pin.status.return_value = {
        "SimState": "257",
        "PinOptState": "1",
        "SimPinTimes": 0,
        "SimPukTimes": "10",
        "CurrentPin": "0123",
        "SavedPin": "0123",
    }
    assert manager.read_status() == {
        "sim_state": "257",
        "pin_opt_state": "1",
        "pin_attempts_remaining": "0",
        "puk_attempts_remaining": "10",
    }


def test_missing_status_is_unknown(modem):
    manager, _, pin = modem
    pin.status.return_value = {}
    assert all(value is None for value in manager.read_status().values())


@pytest.mark.parametrize(
    "operation", ["verify_pin", "enable_pin", "disable_pin", "change_pin"]
)
def test_invalid_current_pin_never_contacts_modem(modem, operation):
    manager, connection, pin = modem
    with pytest.raises(ValueError):
        manager.operate(operation, "bad", "0567" if operation == "change_pin" else None)
    connection.assert_not_called()
    pin.operate.assert_not_called()
