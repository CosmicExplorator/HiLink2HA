# Release checklist

This file tracks the work required before publishing Huawei HiLink SMS through HACS.

## Repository and packaging

- [x] One integration under `custom_components/huawei_sms`
- [x] `manifest.json` contains the required HACS metadata
- [x] `hacs.json` exists at the repository root
- [x] English and French documentation
- [x] English and French service translations
- [x] Open-source license
- [x] Original brand icon (no Huawei or Home Assistant trademark)
- [x] HACS and Hassfest GitHub Actions
- [x] Python compilation and unit-test workflow
- [ ] Add a GitHub repository description and topics
- [ ] Enable GitHub Issues

## Integration quality

- [ ] Add UI configuration (`config_flow`) while keeping a documented YAML migration path
- [ ] Move modem I/O into a shared client/coordinator
- [ ] Avoid registering duplicate services when multiple modems are configured
- [ ] Add device and entity metadata
- [ ] Translate runtime user-facing errors and replies
- [ ] Add diagnostics with SMS content, phone numbers, IMSI and IMEI redacted
- [x] Add unit tests for SMS validation, intent parsing and entity authorization
- [ ] Add unit tests for inbox parsing, number normalization and modem services

## Safe Huawei E3372 validation

- [ ] Connect and read device information without changing modem state
- [ ] Read inbox and SIM contacts
- [ ] Send one SMS to an explicitly approved test number
- [ ] Receive one test SMS and verify the Home Assistant event
- [ ] Delete one dedicated test SMS only
- [ ] Verify accented and multipart SMS
- [ ] Verify behavior after modem restart and temporary network loss
- [ ] Verify an unauthorized sender cannot trigger a Home Assistant command

## Public release

- [ ] Make the GitHub repository public
- [ ] Ensure HACS, Hassfest and Python workflows pass without ignored checks
- [ ] Add the integration to `home-assistant/brands` if required by validation
- [ ] Create and publish GitHub release `v0.1.0` (a tag alone is insufficient)
- [ ] Install `v0.1.0` as a HACS custom repository on a test instance
- [ ] Submit the repository to `hacs/default` only after the release is stable
