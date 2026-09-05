# Huawei HiLink SMS for Home Assistant

[Français](README.fr.md)

See [FILES.md](FILES.md) for a short bilingual description of every project file.

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

## Lovelace card

The integration bundles a card for reading, replying to, composing, and deleting SMS.

To add it to a dashboard:

1. Restart Home Assistant after installing the integration.
2. Under **Settings → Dashboards → Resources**, add `/huawei_sms/huawei-sms-card.js` as a **JavaScript module**.
3. Edit your dashboard, add a **Manual card**, and paste:

```yaml
type: custom:huawei-sms-card
entity: sensor.sms_huawei_e3372
title: Modem messages
show_unread_only: false
```

If necessary, replace `sensor.sms_huawei_e3372` with the entity ID of your SMS sensor.

Available options:

- `entity` (required): Huawei SMS sensor entity ID.
- `title`: card heading.
- `show_unread_only`: only display unread messages when `true`.

The card displays SMS content with text-only DOM nodes and asks for confirmation before deletion.

## Status

This is an early community release. Back up the modem inbox before testing destructive services. Configuration through the Home Assistant UI is planned.

## SIM PIN management

Under **Developer tools → Actions**, use:

- `huawei_sms.get_pin_status`: read SIM/PIN status and remaining attempts.
- `huawei_sms.verify_pin`: unlock the SIM after startup using `current_pin`, without disabling PIN protection.
- `huawei_sms.enable_pin`: enable PIN verification using `current_pin`.
- `huawei_sms.disable_pin`: disable PIN verification using `current_pin`.
- `huawei_sms.change_pin`: change the PIN using `current_pin` and `new_pin`.

PINs must be strings of 4–8 digits, e.g. `"0123"`, preserving leading zeroes.
Input fields are masked; the integration does not retain PINs in its attributes
or configuration. Avoid putting PINs in automations, whose YAML and traces may
retain action data. Incorrect PINs consume attempts and may require the PUK to
unblock the SIM. Operations are never automatically retried. Support depends on
HiLink firmware and access permissions.

**This feature cannot retrieve the current PIN.** Status responses contain only
`sim_state`, `pin_opt_state` (raw modem codes), `pin_attempts_remaining` and
`puk_attempts_remaining`; absent fields are `null`. Successful reads also populate
the sensor's `pin_status` attribute, which is invalidated after successful changes.
It is not refreshed automatically.

Example action sequence:

```yaml
- action: huawei_sms.get_pin_status
  response_variable: sim_pin
```

Restart Home Assistant after updating to load the new actions.

### PIN management card

Add `/huawei_sms/huawei-sim-pin-card.js` as a Lovelace **JavaScript module** resource,
then add this card to your dashboard:

```yaml
type: custom:huawei-sim-pin-card
entity: sensor.sms_huawei_e3372
title: SIM PIN
```

The card reads status, enables/disables PIN verification and changes the PIN with
new-PIN confirmation. Fields are masked and cleared when submitted. Click the
status button to refresh the information. Card controls currently use French labels.

PIN unlocking is manual: no PIN is stored or submitted automatically at startup.
Automated tests use a simulated modem; PIN operations still require validation
on the relevant HiLink models using a PIN-protected SIM.
