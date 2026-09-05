#!/usr/bin/env python3
"""
Script de validation HACS et Hassfest local pour Huawei HiLink SMS.
Basé sur les exigences officielles de HACS et Home Assistant.
"""

import json
import sys
from pathlib import Path

# Chemins
ROOT = Path("/config/development/HiLink2HA")
COMPONENT = ROOT / "custom_components" / "huawei_sms"

# Couleurs pour l'affichage
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

all_results = []

def check(passed, message):
    """Affiche un résultat de validation et stocke le booléen."""
    symbol = "✅" if passed else "❌"
    color = GREEN if passed else RED
    print(f"{color}{symbol} {message}{RESET}")
    all_results.append(passed)
    return passed

def check_file_exists(path, description):
    """Vérifie qu'un fichier existe."""
    exists = path.exists()
    return check(exists, f"{description} : {path.relative_to(ROOT)}")

def check_json_file(path, description, required_keys=None):
    """Vérifie qu'un fichier JSON existe et contient les clés requises."""
    if not path.exists():
        return check(False, f"{description} : {path.relative_to(ROOT)} (manquant)")
    
    try:
        with open(path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        return check(False, f"{description} : {path.relative_to(ROOT)} (JSON invalide: {e})")
    
    if required_keys:
        missing = [k for k in required_keys if k not in data]
        if missing:
            return check(False, f"{description} : clés manquantes {missing}")
    
    return check(True, f"{description} : {path.relative_to(ROOT)}")

def validate_manifest():
    """Valide le fichier manifest.json."""
    print(f"\n{YELLOW}=== Validation manifest.json ==={RESET}")
    path = COMPONENT / "manifest.json"
    
    required_keys = ["domain", "name", "version", "documentation", "issue_tracker"]
    check_json_file(path, "manifest.json", required_keys)
    
    with open(path) as f:
        data = json.load(f)
    
    # Vérifications supplémentaires
    check("domain" in data and data["domain"] == "huawei_sms", "  - domain = 'huawei_sms'")
    check("name" in data and bool(data["name"]), "  - name présent")
    check("version" in data and bool(data["version"]), "  - version présente (format X.Y.Z)")
    check("documentation" in data and data["documentation"].startswith("https://"), "  - documentation URL valide")
    check("issue_tracker" in data and data["issue_tracker"].startswith("https://"), "  - issue_tracker URL valide")
    check("iot_class" in data, "  - iot_class présent (recommandé)")
    check("requirements" in data, "  - requirements présent (pour les dépendances)")
    check("config_flow" in data and data["config_flow"] == True, "  - config_flow = true")
    check("codeowners" in data, "  - codeowners présent (recommandé)")

def validate_hacs_json():
    """Valide le fichier hacs.json."""
    print(f"\n{YELLOW}=== Validation hacs.json ==={RESET}")
    path = ROOT / "hacs.json"
    
    required_keys = ["name"]
    check_json_file(path, "hacs.json", required_keys)
    
    with open(path) as f:
        data = json.load(f)
    
    check("name" in data and bool(data["name"]), "  - name présent")
    check("render_readme" in data, "  - render_readme présent (recommandé)")

def validate_files_structure():
    """Valide la structure des fichiers."""
    print(f"\n{YELLOW}=== Validation structure des fichiers ==={RESET}")
    
    required_files = [
        (COMPONENT / "__init__.py", "__init__.py"),
        (COMPONENT / "manifest.json", "manifest.json"),
        (COMPONENT / "config_flow.py", "config_flow.py"),
        (COMPONENT / "const.py", "const.py"),
        (COMPONENT / "sensor.py", "sensor.py"),
        (COMPONENT / "services.yaml", "services.yaml"),
        (COMPONENT / "strings.json", "strings.json"),
        (ROOT / "README.md", "README.md"),
        (ROOT / "LICENSE", "LICENSE"),
        (ROOT / "hacs.json", "hacs.json"),
        (ROOT / "custom_components" / "huawei_sms" / "translations" / "en.json", "translations/en.json"),
        (ROOT / "custom_components" / "huawei_sms" / "translations" / "fr.json", "translations/fr.json"),
    ]
    
    for path, desc in required_files:
        check_file_exists(path, desc)

def validate_brand():
    """Valide les icônes de marque."""
    print(f"\n{YELLOW}=== Validation marque (brand) ==={RESET}")
    
    brand_files = [
        (ROOT / "brand" / "icon.png", "brand/icon.png (pour HACS)"),
        (COMPONENT / "brand" / "icon.png", "custom_components/huawei_sms/brand/icon.png (pour HA 2026.3+)"),
    ]
    
    for path, desc in brand_files:
        check_file_exists(path, desc)

def validate_requirements():
    """Valide les dépendances Python."""
    print(f"\n{YELLOW}=== Validation requirements ==={RESET}")
    
    manifest_path = COMPONENT / "manifest.json"
    with open(manifest_path) as f:
        data = json.load(f)
    
    if "requirements" not in data:
        check(False, "Pas de requirements dans manifest.json")
        return
    
    requirements = data["requirements"]
    if not isinstance(requirements, list) or not requirements:
        check(False, "requirements doit être une liste non vide")
        return
    
    check(True, f"Dépendances : {requirements}")

def validate_github_workflows():
    """Valide les workflows GitHub."""
    print(f"\n{YELLOW}=== Validation workflows GitHub ==={RESET}")
    
    workflow_dir = ROOT / ".github" / "workflows"
    
    required_workflows = [
        (workflow_dir / "validate.yml", "validate.yml (HACS/Hassfest)"),
        (workflow_dir / "python.yml", "python.yml (tests/lint)"),
    ]
    
    for path, desc in required_workflows:
        check_file_exists(path, desc)

def validate_pyproject():
    """Valide le fichier pyproject.toml."""
    print(f"\n{YELLOW}=== Validation pyproject.toml ==={RESET}")
    path = ROOT / "pyproject.toml"
    
    if not path.exists():
        check(False, "pyproject.toml manquant")
        return
    
    try:
        with open(path) as f:
            content = f.read()
        
        check("pytest" in content, "  - pytest configuré")
        check("ruff" in content or "flake8" in content or "black" in content, "  - linter configuré")
    except IOError:
        check(False, "pyproject.toml inaccessible")

def main():
    """Exécute toutes les validations."""
    global all_results
    all_results = []
    
    print(f"\n{YELLOW}=========================================={RESET}")
    print(f"{YELLOW}  Validation HACS & Hassfest pour HiLink2HA{RESET}")
    print(f"{YELLOW}=========================================={RESET}")
    
    validate_manifest()
    validate_hacs_json()
    validate_files_structure()
    validate_brand()
    validate_requirements()
    validate_github_workflows()
    validate_pyproject()
    
    # Résumé
    print(f"\n{YELLOW}=========================================={RESET}")
    print(f"{YELLOW}  RÉSULTATS{RESET}")
    print(f"{YELLOW}=========================================={RESET}")
    
    all_passed = all(all_results)
    passed_count = sum(all_results)
    total_count = len(all_results)
    
    print(f"{GREEN if all_passed else RED}{passed_count}/{total_count} vérifications passées{RESET}")
    
    print(f"\n{GREEN if all_passed else RED}=== {'✅ TOUT EST VALIDE' if all_passed else '❌ DES ERREURS À CORRIGER'} ==={RESET}")
    
    if not all_passed:
        print(f"\n{YELLOW}Corrige les erreurs ci-dessus pour passer la validation HACS.{RESET}")
        sys.exit(1)
    else:
        print(f"\n{GREEN}Ton intégration est prête pour HACS !{RESET}")
        sys.exit(0)

if __name__ == "__main__":
    main()
