"""Constants for Huawei HiLink SMS."""

DOMAIN = "huawei_sms"
PLATFORMS = ["sensor"]

CONF_ALLOWED_SENDERS = "allowed_senders"
CONF_COUNTRY_CODE = "country_code"
CONF_INTERACTIONS_FILE = "interactions_file"
CONF_MAX_MESSAGES = "max_messages"

DEFAULT_COUNTRY_CODE = "+33"
DEFAULT_INTERACTIONS_FILE = "/config/huawei_sms_interactions.yaml"
DEFAULT_MAX_MESSAGES = 20
DEFAULT_NAME = "Huawei E3372 SMS"
DEFAULT_URL = "http://192.168.8.1/"
