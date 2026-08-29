from custom_components.huawei_sms.interaction import (
    SmsType,
    can_reply_to_sender,
    normalize_sms,
    validate_sms,
)


def test_normalize_sms_removes_accents_and_whitespace() -> None:
    assert normalize_sms("  Séjour,   Température ? ") == "sejour, temperature ?"


def test_validate_query() -> None:
    result = validate_sms("Salon, température ?")
    assert result.valid is True
    assert result.sms_type is SmsType.QUERY
    assert result.room == "salon"
    assert result.payload == "temperature"


def test_validate_command() -> None:
    result = validate_sms("Salon, éteins lumière.")
    assert result.valid is True
    assert result.sms_type is SmsType.COMMAND
    assert result.payload == "eteins lumiere"


def test_reject_invalid_sms() -> None:
    result = validate_sms("do anything without an envelope")
    assert result.valid is False
    assert result.error == "invalid_format"


def test_replyable_phone_number() -> None:
    assert can_reply_to_sender("+33612345678") is True
    assert can_reply_to_sender("ServiceName") is False
