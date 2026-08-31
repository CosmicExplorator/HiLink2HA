# File guide / Guide des fichiers

## Integration / Intégration

| File | English | Français |
| --- | --- | --- |
| `custom_components/huawei_sms/__init__.py` | Loads and unloads the integration. | Charge et décharge l’intégration. |
| `custom_components/huawei_sms/config_flow.py` | Provides UI setup, the read-only connection test and editable options. | Fournit la configuration graphique, le test de connexion en lecture seule et les options. |
| `custom_components/huawei_sms/const.py` | Contains shared names and default values. | Contient les noms et valeurs par défaut partagés. |
| `custom_components/huawei_sms/sensor.py` | Reads SMS and SIM contacts, exposes the sensor and registers SMS services. | Lit les SMS et contacts SIM, expose le capteur et enregistre les services SMS. |
| `custom_components/huawei_sms/interaction.py` | Normalizes and validates received SMS commands. | Normalise et valide les commandes reçues par SMS. |
| `custom_components/huawei_sms/dictionary.py` | Converts recognized French command words into actions. | Convertit les mots de commande français reconnus en actions. |
| `custom_components/huawei_sms/resolver.py` | Resolves allowed names to explicitly declared Home Assistant entities. | Associe les noms autorisés aux entités Home Assistant déclarées explicitement. |
| `custom_components/huawei_sms/dispatcher.py` | Reads entity states or calls an authorized Home Assistant service. | Lit l’état des entités ou appelle un service Home Assistant autorisé. |
| `custom_components/huawei_sms/manifest.json` | Declares the integration, version and Python dependency to Home Assistant. | Déclare l’intégration, sa version et sa dépendance Python à Home Assistant. |
| `custom_components/huawei_sms/services.yaml` | Defines the fields accepted by SMS and contact services. | Définit les champs acceptés par les services SMS et contacts. |
| `custom_components/huawei_sms/strings.json` | Contains the default English UI text. | Contient les textes anglais utilisés par défaut dans l’interface. |
| `custom_components/huawei_sms/translations/en.json` | English translations. | Traductions anglaises. |
| `custom_components/huawei_sms/translations/fr.json` | French translations. | Traductions françaises. |
| `custom_components/huawei_sms/brand/icon.png` | Local icon displayed by Home Assistant 2026.3 and later. | Icône locale affichée par Home Assistant 2026.3 et versions ultérieures. |
| `custom_components/huawei_sms/frontend/huawei-sms-card.js` | Bundled Lovelace card for viewing and managing SMS. | Carte Lovelace intégrée pour consulter et gérer les SMS. |

## Repository / Dépôt

| File | English | Français |
| --- | --- | --- |
| `hacs.json` | Tells HACS how to display and install the repository. | Indique à HACS comment afficher et installer le dépôt. |
| `brand/icon.png` | Original project icon used in the HACS repository listing. | Icône originale utilisée dans la liste des dépôts HACS. |
| `README.md` | English installation and usage guide. | Guide d’installation et d’utilisation en anglais. |
| `README.fr.md` | French installation and usage guide. | Guide d’installation et d’utilisation en français. |
| `RELEASE_CHECKLIST.md` | Tracks completed work and remaining publication tasks. | Suit les travaux terminés et les étapes restantes avant publication. |
| `pyproject.toml` | Configures pytest and Ruff. | Configure pytest et Ruff. |
| `.github/workflows/validate.yml` | Runs HACS and Hassfest validation. | Exécute les validations HACS et Hassfest. |
| `.github/workflows/python.yml` | Runs lint, compilation and unit tests. | Exécute le lint, la compilation et les tests unitaires. |
| `tests/` | Contains unit tests; no test contacts the real modem. | Contient les tests unitaires ; aucun ne contacte le modem réel. |
| `.gitignore` | Excludes caches and local development files. | Exclut les caches et fichiers locaux de développement. |
| `LICENSE` | MIT license terms. | Conditions de la licence MIT. |

## Runtime flow / Fonctionnement

```text
Home Assistant UI
    → config_flow.py
    → __init__.py
    → sensor.py
    → huawei-lte-api
    → Huawei HiLink modem

Incoming authorized SMS
    → interaction.py
    → dictionary.py
    → resolver.py
    → dispatcher.py
    → Home Assistant entity or service
```

Files under `.pytest_cache`, `.ruff_cache` and `__pycache__` are generated locally and are not committed.

Les fichiers sous `.pytest_cache`, `.ruff_cache` et `__pycache__` sont générés localement et ne sont pas versionnés.
