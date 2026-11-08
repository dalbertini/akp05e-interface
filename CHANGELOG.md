# Changelog

Historique des versions de l'application. Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/),
numérotation [SemVer](https://semver.org/lang/fr/) : **MAJEURE**.**FONCTIONNALITÉ**.**CORRECTIF**.

## [1.4.0] — 2026-11-08

### Ajouté
- **Zone 2 du bandeau en carrousel de pages** : la page courante s'affiche dans une **pilule arrondie** au centre, avec les pages précédente/suivante en **grisé** et des flèches triangulaires de chaque côté.
- **Mini-icône Material + couleur d'accent sur la page active** : chaque page peut définir `"icon"` (nom Material Icons, ex. `music_note`) et `"color"` (accent CSS) — la pilule prend le contour et le logo dans cette couleur (Accueil : `home` turquoise, Qobuz : `music_note` bleu ciel). Si la police d'icônes n'est pas encore en cache, la pilule s'affiche sans logo.
- La zone 2 reste utilisable en libellé libre si les pages ne sont pas activées (compat config plate).


## [1.3.1] — 2026-11-08

### Modifié
- **Retrait des boutons de bascule de page** (« Qobuz » sur la page accueil, « Accueil » sur la page Qobuz) : devenus redondants depuis que le knob 2 fait défiler les pages (v1.3.0) — les touches libèrent de la place pour de futures actions.

## [1.3.0] — 2026-11-08

### Ajouté
- **Le knob 2 fait défiler les pages** : rotation CW = page suivante, CCW = page précédente (action `{"type": "page", "page": "next"}` / `"prev"`), actif sur toutes les pages et automatiquement compatible avec les futures pages ajoutées dans la config.
- L'appui du knob 2 reste libre (configurable).

## [1.2.1] — 2026-11-08

### Modifié
- **Page Qobuz** : le bouton Stop est retiré (Qobuz ne le gère pas) — les touches se répartissent désormais : 1 = Play/Pause, 2 = Suivant, 3 = Précédent, 4 = Mute, 10 = Accueil.
- **Page Accueil** : les boutons multimédia (6 = Play, 7 = Suivant, 8 = Précédent) sont retirés — ces commandes restent disponibles sur la page Qobuz. La touche 9 (Mute) est conservée.

## [1.2.0] — 2026-11-08

### Ajouté
- **Pages de profils** : la config classique forme la page « accueil » ; des pages supplémentaires se définissent dans la clé `pages` (chacune avec ses touches, ses encodeurs et son libellé). Nouvelle action `{"type": "page", "page": "nom"}` pour basculer ; la zone 2 du bandeau affiche le nom de la page courante.
- **Page « Qobuz » par défaut** : Play/Pause, Suivant, Précédent, Mute (volume système) — pilotée par les touches média système, compatible Qobuz, Spotify, VLC, etc.

### Corrigé
- **Les touches média ne fonctionnaient pas** (Play/Stop/Suiv./Préc., volume) : les codes envoyés étaient des codes d'usage HID (0xE8…) et non les codes virtuels Windows officiels (`VK_MEDIA_PLAY_PAUSE` 0xB3, `VK_MEDIA_NEXT_TRACK` 0xB0, `VK_VOLUME_MUTE` 0xAD…) — Windows ignorait les événements. Le presse-bouton média envoie désormais les bons VK down/up, visibles par toutes les applications.

## [1.1.2] — 2026-11-08

### Corrigé
- **Volume système à nouveau invisible (« K1 ») avec pycaw ≥ 20240210** : la nouvelle API pycaw fait de `AudioUtilities.GetSpeakers()` un objet `AudioDevice` sans méthode `.Activate()` — le volume est désormais accessible via l'attribut `.EndpointVolume`. L'application détecte automatiquement l'ancienne ou la nouvelle génération de l'API (`_get_endpoint()`), les deux versions de pycaw sont supportées.
- `test_volume.py` (diagnostic) mis à jour pour tester les deux générations de l'API.

## [1.1.1] — 2026-11-08

### Corrigé
- **Le volume système restait bloqué sur « K1 »** : COM n'était pas initialisé dans les threads (surveilleur de volume, actions) — chaque appel échouait silencieusement. COM est désormais initialisé dans chaque thread appelant (`_com_init()`).
- Les erreurs de lecture du volume ne sont plus avalées : la première erreur est affichée dans la console.
- Si `pycaw`/`comtypes` sont introuvables, le message de démarrage affiche la cause exacte de l'échec d'import.

## [1.1.0] — 2026-11-08

### Ajouté
- **Volume système Windows en temps réel** (knob 1) : nouvelle action `sysvolume` qui règle le niveau réel de Windows via `pycaw` (`dir`: `up` / `down` / `mute`, `step` optionnel, défaut 5)
- **Zone tactile du volume** : le bandeau affiche « Vol % » avec barre de niveau, et « Muet » (rouge) quand le son est coupé
- **Surveillance du volume en arrière-plan** (0,5 s) : le bandeau se met à jour même si le volume est changé depuis Windows
- `requirements.txt`, README bilingue (français + anglais)

### Modifié
- Config par défaut du knob 1 : `volume` (touches média) → `sysvolume` (volume système réel)
- **Bandeau unifié** : zones « Vol » et « Lum » partageant le même moteur d'affichage, mises à jour synchronisées

## [1.0.0] — 2026-11-08

### Ajouté
- Version initiale : application de contrôle open source pour l'Ajazz AKP05E / AKP05 (Windows)
- **10 touches LCD** : icônes Material Icons (~2500 noms, police téléchargée une fois puis mise en cache hors ligne) ou images perso, couleurs CSS et libellés configurables
- **4 encodeurs rotatifs** : appui + rotation CW/CCW
- **Bandeau tactile** 800×112 : une zone de 200 px par encodeur, avec « Lum % » + barre
- **Luminosité** (knob 4) : rotation = réglage par pas, appui = extinction/rallumage avec mémorisation du niveau
- **Actions configurables** via `akp05e_config.json` : `open`, `url`, `keys`, `text`, `run`, `volume`, `mediaplay`, `medianext`, `mediaprev`, `mediastop`, `brightness`, `brightness_toggle`
- **Keepalive automatique** toutes les 10 s (« CONNECT »)
- Gestion de la déconnexion (câble débranché)
- Protocole HID rétro-ingénieré (VID `0x0300` / PID `0x3004`, paquets 1024 octets, commandes `CRT`, images JPEG 112×112 / 800×112 pivotées de 180°)
- Licence MIT, `README.md`, `.gitignore`

[1.4.0]: https://github.com/dalbertini/akp05e-interface/commits/main/
[1.3.1]: https://github.com/dalbertini/akp05e-interface/commits/main/
[1.3.0]: https://github.com/dalbertini/akp05e-interface/commits/main/
[1.2.1]: https://github.com/dalbertini/akp05e-interface/commits/main/
[1.2.0]: https://github.com/dalbertini/akp05e-interface/commits/main/
[1.1.2]: https://github.com/dalbertini/akp05e-interface/commits/main/
[1.1.1]: https://github.com/dalbertini/akp05e-interface/commits/main/
[1.1.0]: https://github.com/dalbertini/akp05e-interface/commits/main/
[1.0.0]: https://github.com/dalbertini/akp05e-interface/commits/main/
