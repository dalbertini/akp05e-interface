# Changelog

Historique des versions de l'application. Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/),
numérotation [SemVer](https://semver.org/lang/fr/) : **MAJEURE**.**FONCTIONNALITÉ**.**CORRECTIF**.

## [1.2.0] — 2026-11-08

### Ajouté
- **Pages de profils** : la config classique forme la page « accueil » ; des pages supplémentaires se définissent dans la clé `pages` (chacune avec ses touches, ses encodeurs et son libellé). Nouvelle action `{"type": "page", "page": "nom"}` pour basculer ; la zone 2 du bandeau affiche le nom de la page courante.
- **Page « Qobuz » par défaut** : Play/Pause, Stop, Suivant, Précédent, Mute (volume système) + retour accueil — pilotée par les touches média système, compatible Qobuz, Spotify, VLC, etc.
- Sur la page accueil, la touche 10 ouvre la page Qobuz (icône music_note), la touche 9 utilise le vrai volume système (muet).

### Corrigé
- **Les touches média ne fonctionnaient pas** (Play/Stop/Suiv./Préc., volume) : les codes envoyés étaient des codes d'usage HID (0xE8…) et non les codes virtuels Windows officiels (`VK_MEDIA_PLAY_PAUSE` 0xB3, `VK_MEDIA_NEXT_TRACK` 0xB0, `VK_VOLUME_MUTE` 0xAD…) — Windows ignorait les événements. Le presse-bouton média envoie désormais les bons VK down/up, visibles par toutes les applications.

## [1.1.2] — 2026-11-08

### Corrigé
- **Volume système à nouveau invisible (« K1 ») avec pycaw ≥ 20240210** : la nouvelle API pycaw fait de `AudioUtilities.GetSpeakers()` un objet `AudioDevice` sans méthode `.Activate()` — le volume est désormais accessible via l'attribut `.EndpointVolume`. L'application détecte automatiquement l'ancienne ou la nouvelle génération de l'API (`_get_endpoint()`), les deux versions de pycaw sont supportées.
- `test_volume.py` (diagnostic) mis à jour pour tester les deux générations de l'API.

## [1.1.1] — 2026-11-08

### Corrigé
- **Le volume système restait bloqué sur « K1 »** : les appels audio Windows (COM) sont effectués depuis des threads (surveilleur de volume, actions), mais COM n'y était pas initialisé — chaque appel échouait silencieusement. COM est désormais initialisé dans chaque thread appelant (`_com_init()`).
- Les erreurs de lecture du volume ne sont plus avalées : la première erreur est affichée dans la console.
- Si `pycaw`/`comtypes` sont introuvables, le message de démarrage affiche la cause exacte de l'échec d'import et rappelle d'installer avec le même interpréteur (`python -m pip install pycaw`).

## [1.1.0] — 2026-11-08

### Ajouté
- **Volume système Windows en temps réel** (knob 1) : nouvelle action `sysvolume` qui règle le niveau réel de Windows via `pycaw` (`dir`: `up` / `down` / `mute`, `step` optionnel, défaut 5), au lieu des simples touches média
- **Zone tactile du volume** : le bandeau affiche « Vol % » avec barre de niveau, et « Muet » (rouge) quand le son est coupé
- **Surveillance du volume en arrière-plan** (0,5 s) : le bandeau se met à jour même si le volume est changé depuis Windows (barre des tâches, clavier…)
- `requirements.txt` pour une installation en une ligne (`pip install -r requirements.txt`)
- README bilingue (français + anglais)

### Modifié
- Config par défaut du knob 1 : `volume` (touches média) → `sysvolume` (volume système réel)
- **Bandeau unifié** : les zones « Vol » et « Lum » partagent désormais le même moteur d'affichage (libellé, %, barre de niveau) ; la zone « Lum » garde son comportement (rotation = ±10, appui sur le knob 4 = extinction/rallumage avec mémorisation du dernier niveau) mais le bandeau redessiné affiche désormais **les deux niveaux synchronisés**
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

[1.2.0]: https://github.com/dalbertini/akp05e-interface/commits/main/
[1.1.2]: https://github.com/dalbertini/akp05e-interface/commits/main/
[1.1.1]: https://github.com/dalbertini/akp05e-interface/commits/main/
[1.1.0]: https://github.com/dalbertini/akp05e-interface/commits/main/
[1.0.0]: https://github.com/dalbertini/akp05e-interface/commits/main/
