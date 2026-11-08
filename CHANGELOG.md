# Changelog

Historique des versions de l'application. Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/),
numérotation [SemVer](https://semver.org/lang/fr/) : **MAJEURE**.**FONCTIONNALITÉ**.**CORRECTIF**.

## [1.1.0] — 2026-11-08

### Ajouté
- **Volume système Windows en temps réel** (knob 1) : nouvelle action `sysvolume` qui règle le niveau réel de Windows via `pycaw` (`dir`: `up` / `down` / `mute`, `step` optionnel, défaut 5), au lieu des simples touches média
- **Zone tactile du volume** : le bandeau affiche « Vol % » avec barre de niveau, et « Muet » (rouge) quand le son est coupé
- **Surveillance du volume en arrière-plan** (0,5 s) : le bandeau se met à jour même si le volume est changé depuis Windows (barre des tâches, clavier…)
- `requirements.txt` pour une installation en une ligne (`pip install -r requirements.txt`)
- README bilingue (français + anglais)

### Modifié
- Config par défaut du knob 1 : `volume` (touches média) → `sysvolume` (volume système réel)
- **Bandeau unifié** : les zones « Vol » et « Lum » partagent désormais le même moteur d'affichage (libellé, %, barre de niveau) ; la zone « Lum » garde son comportement (rotation = ±10, appui sur le knob 4 = extinction/rallumage avec mémorisation du dernier niveau) mais le bandeau redessiné affiche désormais **les deux niveaux synchronisés** — un changement de luminosité met aussi à jour l'affichage du volume en temps réel
- Suppression d'une ligne vide parasite en tête de fichier (le shebang est bien en ligne 1)

### Dégradation élégante
- Si `pycaw` est absent, l'action `sysvolume` retombe automatiquement sur les touches média

## [1.0.0] — 2026-11-08

### Ajouté
- Version initiale : application de contrôle open source pour l'Ajazz AKP05E / AKP05 (Windows)
- **10 touches LCD** : icônes Material Icons (~2500 noms, police téléchargée une fois puis mise en cache hors ligne) ou images perso, couleurs CSS et libellés configurables
- **4 encodeurs rotatifs** : appui + rotation CW/CCW
- **Bandeau tactile** 800×112 : une zone de 200 px par encodeur, avec « Lum % » + barre
- **Luminosité** (knob 4) : rotation = réglage par pas, appui = extinction/rallumage avec mémorisation du niveau
- **Actions configurables** via `akp05e_config.json` : `open`, `url`, `keys`, `text`, `run`, `volume`, `mediaplay`, `medianext`, `mediaprev`, `mediastop`, `brightness`, `brightness_toggle`
- **Keepalive automatique** toutes les 10 s (« CONNECT ») — sinon le deck se déconnecte au bout de ~15 s
- Gestion de la déconnexion (câble débranché)
- Protocole HID rétro-ingénieré (VID `0x0300` / PID `0x3004`, paquets 1024 octets, commandes `CRT`, images JPEG 112×112 / 800×112 pivotées de 180°)
- Licence MIT, `README.md`, `.gitignore`

[1.1.0]: https://github.com/dalbertini/akp05e-interface/commits/main/
[1.0.0]: https://github.com/dalbertini/akp05e-interface/commits/main/
