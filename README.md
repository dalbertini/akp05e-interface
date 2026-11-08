# AKP05E Interface

**FR** — Application de contrôle **open source** (Python, Windows) pour le deck **Ajazz AKP05E / AKP05** — sans le logiciel propriétaire. *(English below)*

## Fonctionnalités (FR)

- **10 touches LCD** : icônes Material Icons (~2500, mises en cache après premier téléchargement) ou images perso, couleurs et libellés configurables
- **4 encodeurs rotatifs** : appui + rotation CW/CCW, actions configurables
- **Volume système Windows en temps réel** (knob 1) : réglage du niveau réel de Windows via `pycaw`, appui = muet, et la zone tactile affiche **Vol %** + barre — mise à jour même si le volume est changé depuis Windows (barre des tâches, clavier)
- **Luminosité** (knob 4) : rotation = réglage des écrans, appui = extinction/rallumage, zone tactile **Lum %** + barre
- **Bandeau tactile** : une zone de 200 px par encodeur
- **Actions configurables** via `akp05e_config.json` : lancer un programme, ouvrir une URL, raccourcis clavier, taper du texte, commande, volume système, volume/média, luminosité
- **Keepalive automatique** (le deck coupe sinon la connexion au bout de ~15 s)
- Gestion de la déconnexion (câble débranché)

## Installation (FR)

```
pip install -r requirements.txt
python akp05e_app.py
```

Au premier lancement, `akp05e_config.json` (config par défaut) est créé à côté du script, et la police d'icônes est téléchargée une fois dans `.icons_cache/`. Ensuite, tout fonctionne hors ligne. Si tu avais déjà un `akp05e_config.json`, mets à jour les entrées `encoder_1_*` pour profiter du volume système réel (ou supprime le fichier pour le régénérer).

> Ferme le logiciel Ajazz officiel avant de lancer l'application : les deux s'excluent (accès HID exclusif au deck).

## Configuration (FR)

`akp05e_config.json` — exemple :

```json
"3": {"icon": "code", "color": "#80DEEA", "bg": "#101418", "label": "VSCode",
      "action": {"type": "open", "path": "C:\\Program Files\\...\\Code.exe"}}
```

Types d'actions : `open`, `url`, `keys`, `text`, `run`, `sysvolume` (volume système réel, `dir`: `up`/`down`/`mute`, `step` optionnel), `volume` (touches média), `mediaplay`, `medianext`, `mediaprev`, `mediastop`, `brightness`, `brightness_toggle`.

Événements configurables : `button_1`..`button_10`, `encoder_N_button`, `encoder_N_cw`, `encoder_N_ccw`.

---

# English

**Open source** control application (Python, Windows) for the **Ajazz AKP05E / AKP05** deck — no proprietary software required.

## Features

- **10 LCD keys** with configurable labels, colors, ~2500 Material Icons (cached after first download) or custom images
- **4 rotary encoders** with push + CW/CCW actions
- **Real-time Windows system volume** (knob 1): sets the actual Windows master level via `pycaw`, push = mute; the touch strip zone shows **Vol %** + bar and updates even when volume changes from Windows itself
- **Brightness control** (knob 4): rotation adjusts screens, push toggles on/off, touch strip zone shows **%** + bar
- **Configurable actions** via `akp05e_config.json`: launch programs, open URLs, keyboard shortcuts, type text, run commands, system volume, media, brightness
- **Automatic keepalive** (the deck otherwise disconnects after ~15 s)
- Hot-unplug handling

## Install

```
pip install -r requirements.txt
python akp05e_app.py
```

A default `akp05e_config.json` is created next to the script on first run; the icon font is downloaded once into `.icons_cache/`, then everything works offline. Close the official Ajazz software first — both need exclusive HID access.

Action types: `open`, `url`, `keys`, `text`, `run`, `sysvolume` (real system volume, `dir`: `up`/`down`/`mute`, optional `step`), `volume` (media keys), `mediaplay`, `medianext`, `mediaprev`, `mediastop`, `brightness`, `brightness_toggle`. Events: `button_1`..`button_10`, `encoder_N_button`, `encoder_N_cw`, `encoder_N_ccw`.

## Protocol

Reverse-engineered, cross-checked with the open source projects [mirajazz](https://github.com/4ndv/mirajazz) (Rust), [opendeck-akp05](https://github.com/ambiso/opendeck-akp05) (plugin OpenDeck) et [zeccola/ajazz-akp05](https://github.com/zeccola/ajazz-akp05) (Python).
HID vendor-defined (VID `0x0300` / PID `0x3004`), 1024-byte packets, framed `CRT` commands (`DIS`/`LIG`/`CLE`/`STP`/`BAT`/`CONNECT`), 112×112 JPEG images (keys) and 800×112 (strip) rotated by 180°.

## License

MIT — see [LICENSE](LICENSE). Icons: Material Icons (Google, Apache 2.0).
"Ajazz" and "AKP05E" belong to their respective owners; this project is not affiliated.

Version history: see [CHANGELOG.md](CHANGELOG.md).
