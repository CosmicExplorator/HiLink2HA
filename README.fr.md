# Huawei HiLink SMS pour Home Assistant

[English](README.md)

Consultez [FILES.md](FILES.md) pour une description courte et bilingue de chaque fichier du projet.

Intégration personnalisée Home Assistant permettant d’envoyer, recevoir et gérer les SMS des modems Huawei en mode HiLink. Elle est initialement développée et testée avec le Huawei E3372 à l’adresse `http://192.168.8.1`.

## Fonctionnalités

- Lecture locale périodique de la boîte SMS
- Envoi et suppression de SMS avec les services Home Assistant
- Lecture et gestion du répertoire de la carte SIM
- Événement `huawei_sms_received` lors d’un nouveau message autorisé
- Commandes Home Assistant facultatives par SMS avec liste d’expéditeurs autorisés
- Services traduits en français et en anglais

## Installation avec HACS

1. Dans HACS, ajoutez ce dépôt comme dépôt personnalisé de type **Intégration**.
2. Installez **Huawei HiLink SMS**.
3. Redémarrez Home Assistant.
4. Ouvrez **Paramètres → Appareils et services → Ajouter une intégration**.
5. Recherchez **Huawei HiLink SMS**, saisissez l’adresse du modem et terminez le test de connexion.

La configuration graphique est recommandée. Le YAML reste temporairement disponible pour les installations existantes :

```yaml
sensor:
  - platform: huawei_sms
    name: SMS Huawei E3372
    url: http://192.168.8.1/
    max_messages: 20
    country_code: "+33"
    allowed_senders:
      - "+33612345678"
    interactions_file: /config/huawei_sms_interactions.yaml
```

Les commandes SMS sont désactivées lorsque la liste des expéditeurs autorisés est vide. Si elles sont activées, le fichier d’interactions doit associer explicitement les noms acceptés par SMS aux entités Home Assistant :

```yaml
targets:
  salon:
    lumiere: light.salon
    temperature: sensor.temperature_salon
```

N’exposez pas arbitrairement toutes les entités. Seuls les messages provenant de `allowed_senders` sont interprétés. Le contenu des SMS apparaît dans les attributs de l’entité : excluez celle-ci de Recorder si leur confidentialité est importante.

## Services

`huawei_sms.send`, `huawei_sms.delete`, `huawei_sms.delete_all`, `huawei_sms.add_contact` et `huawei_sms.delete_contact`.

## Carte Lovelace

L’intégration fournit une carte permettant de lire, répondre, rédiger et supprimer des SMS.

Pour l’ajouter à un tableau de bord :

1. Redémarrez Home Assistant après l’installation de l’intégration.
2. Dans **Paramètres → Tableaux de bord → Ressources**, ajoutez `/huawei_sms/huawei-sms-card.js` avec le type **Module JavaScript**.
3. Modifiez votre tableau de bord, ajoutez une **carte manuelle**, puis collez :

```yaml
type: custom:huawei-sms-card
entity: sensor.sms_huawei_e3372
title: Messages du modem
show_unread_only: false
```

Si nécessaire, remplacez `sensor.sms_huawei_e3372` par l’identifiant du capteur SMS de votre installation.

Options disponibles :

- `entity` (obligatoire) : identifiant du capteur Huawei SMS.
- `title` : titre de la carte.
- `show_unread_only` : affiche uniquement les messages non lus si la valeur est `true`.

La carte affiche le contenu des SMS uniquement avec des nœuds texte et demande confirmation avant toute suppression.

## État du projet

Il s’agit d’une première version communautaire. Sauvegardez la boîte du modem avant de tester les services destructifs. La configuration graphique Home Assistant est prévue.

## Gestion du code PIN SIM

Dans **Outils de développement → Actions**, utiliser :

- `huawei_sms.get_pin_status` : lire le statut SIM/PIN et les tentatives restantes.
- `huawei_sms.verify_pin` : déverrouiller la SIM après démarrage avec `current_pin`, sans désactiver la protection PIN.
- `huawei_sms.enable_pin` : activer la demande du PIN avec `current_pin`.
- `huawei_sms.disable_pin` : désactiver la demande du PIN avec `current_pin`.
- `huawei_sms.change_pin` : changer le PIN avec `current_pin` et `new_pin`.

Les PIN doivent être des chaînes de 4 à 8 chiffres, par exemple `"0123"`, pour
conserver les zéros initiaux. Les champs de saisie sont masqués. L'intégration ne
conserve pas les PIN dans ses attributs ou sa configuration. Éviter de les écrire
dans des automatisations : leur YAML et leurs traces peuvent conserver les données
d'action. Un mauvais PIN consomme une tentative ; la SIM peut ensuite exiger le
PUK. Aucun essai automatique n'est effectué. Ces fonctions dépendent du firmware
HiLink et de ses permissions d'accès.

**Le code PIN actuel ne peut pas être récupéré par cette fonctionnalité.** La
lecture retourne uniquement `sim_state`, `pin_opt_state` (codes bruts du modem),
`pin_attempts_remaining` et `puk_attempts_remaining`. Un champ non fourni vaut
`null`. Le résultat est aussi disponible dans l'attribut `pin_status` du capteur
après une lecture réussie, puis invalidé après une modification réussie. Il n'est
pas actualisé automatiquement.

Exemple de lecture dans une séquence d'actions :

```yaml
- action: huawei_sms.get_pin_status
  response_variable: sim_pin
```

Redémarrer Home Assistant après la mise à jour pour charger les nouvelles actions.

### Carte de gestion du PIN

Ajouter `/huawei_sms/huawei-sim-pin-card.js` comme ressource Lovelace de type
**Module JavaScript**, puis ajouter cette carte au dashboard :

```yaml
type: custom:huawei-sim-pin-card
entity: sensor.sms_huawei_e3372
title: Code PIN SIM
```

La carte propose la lecture du statut, le déverrouillage, l'activation, la désactivation et le
changement du PIN avec confirmation du nouveau code. Les champs sont masqués et
effacés à l'envoi. Cliquer sur **Lire le statut** pour actualiser les informations.

Le déverrouillage est manuel : aucun PIN n’est mémorisé ni envoyé automatiquement
au démarrage. Les tests automatisés utilisent un modem simulé ; les opérations
doivent être validées sur les modèles HiLink concernés avec une SIM protégée.
