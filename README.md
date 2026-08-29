# Huawei HiLink SMS for Home Assistant

[Français](README.fr.md)

Custom Home Assistant integration for sending, receiving and managing SMS with Huawei modems running in HiLink mode. Initially developed and tested with the Huawei E3372 at `http://192.168.8.1`.

## Features

- Local polling of the SMS inbox
- Send and delete SMS from Home Assistant services
- Read and manage the SIM phone book
- Fire a `huawei_sms_received` event for new messages from allowed senders
- Optional, allow-listed Home Assistant commands over SMS
- English and French service translations

## HACS installation

1. In HACS, add this repository as a custom repository of type **Integration**.
2. Install **Huawei HiLink SMS**.
3. Restart Home Assistant.
4. Go to **Settings → Devices & services → Add integration**.
5. Search for **Huawei HiLink SMS**, enter the modem URL and complete the connection test.

The UI setup is recommended. YAML remains available temporarily for existing installations:

```yaml
sensor:
  - platform: huawei_sms
    name: Huawei E3372 SMS
    url: http://192.168.8.1/
    max_messages: 20
    country_code: "+33"
    allowed_senders:
      - "+33612345678"
    interactions_file: /config/huawei_sms_interactions.yaml
```

SMS commands are disabled when the allowed-senders option is empty. If enabled, the interactions file must explicitly map names accepted over SMS to Home Assistant entities:

```yaml
targets:
  living_room:
    light: light.living_room
    temperature: sensor.living_room_temperature
```

Do not expose arbitrary entity IDs. Only messages from `allowed_senders` are interpreted. SMS content is available in entity attributes, so exclude the entity from Recorder if message privacy matters.

## Services

`huawei_sms.send`, `huawei_sms.delete`, `huawei_sms.delete_all`, `huawei_sms.add_contact`, and `huawei_sms.delete_contact`.

## Status

This is an early community release. Back up the modem inbox before testing destructive services. Configuration through the Home Assistant UI is planned.
