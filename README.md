# AKP05E Interface

Application de contrôle **open source** (Python, Windows) pour le deck **Ajazz AKP05E / AKP05** — sans le logiciel propriétaire.

## Fonctionnalités

- **10 touches LCD** : icônes Material Icons (~2500, mises en cache après premier téléchargement) ou images perso, couleurs et libellés configurables
- **4 encodeurs rotatifs** : appui + rotation CW/CCW, actions configurables
- **Bandeau tactile** : une zone par encodeur, avec indicateur de luminosité en temps réel (barre + %)
- **Luminosité** : le knob 4 règle la luminosité de tous les écrans (rotation), éteint/rallume le deck (appui, avec mémorisation du niveau)
- **Actions configurables** via `akp05e_config.json` : lancer un programme, ouvrir une URL, raccourcis clavier, taper du texte, commande, volume/média
- **Keepalive automatique** (le deck coupe sinon la connexion au bout de ~15 s)
- Gestion de la déconnexion (câble débranché)

## Installation

```
pip install pywinusb pillow
python akp05e_app.py
```

Au premier lancement, `akp05e_config.json` (config par défaut) est créé à côté du script, et la police d'icônes est téléchargée une fois dans `.icons_cache/`. Ensuite, tout fonctionne hors ligne.

> Ferme le logiciel Ajazz officiel avant de lancer l'application : les deux s'excluent (accès HID exclusif au deck).

## Configuration

`akp05e_config.json` — exemple :

```json
"3": {"icon": "code", "color": "#80DEEA", "bg": "#101418", "label": "VSCode",
      "action": {"type": "open", "path": "C:\\Program Files\\...\\Code.exe"}}
```

Types d'actions : `open`, `url`, `keys`, `text`, `run`, `volume`, `mediaplay`, `medianext`, `mediaprev`, `mediastop`, `brightness`, `brightness_toggle`.

Événements configurables : `button_1`..`button_10`, `encoder_N_button`, `encoder_N_cw`, `encoder_N_ccw`.

## Protocole

Rétro-ingénierie croisée avec les projets open source de la même famille : [mirajazz](https://github.com/4ndv/mirajazz) (Rust), [opendeck-akp05](https://github.com/ambiso/opendeck-akp05) (plugin OpenDeck) et [zeccola/ajazz-akp05](https://github.com/zeccola/ajazz-akp05) (Python).
HID vendor-defined (VID `0x0300` / PID `0x3004`), paquets de 1024 octets, commandes cadrées `CRT` (`DIS`/`LIG`/`CLE`/`STP`/`BAT`/`CONNECT`), images JPEG 112×112 (touches) et 800×112 (bandeau) tournées de 180°.

## Licence

MIT — voir [LICENSE](LICENSE). Icônes : Material Icons (Google, Apache 2.0).
"Ajazz" et "AKP05E" appartiennent à leurs propriétaires ; ce projet n'est pas affilié.
