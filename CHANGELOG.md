# Changelog

Historique des versions de l'application. Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/),
numérotation [SemVer](https://semver.org/lang/fr/) : **MAJEURE**.**FONCTIONNALITÉ**.**CORRECTIF**.

## [1.8.1] — 2026-11-09

### Corrigé
- **Saccades du VU-mètre lors des changements de volume/luminosité** : chaque refresh du bandeau redessinait la zone 3 ("VU") puis attendait le prochain passage du fil VU pour repeindre (~80 ms de scintillement, plus deux envois concurrents). `set_strip` mémorise désormais la dernière image réellement affichée et les refresh recopient les pixels du dernier rendu VU — plus de scintillement, et le fil VU n'a plus besoin de réenvoyer une frame juste après un refresh (moins de contention sur le bus HID).

## [1.8.0] — 2026-11-09

### Ajouté
- **VU-mètre temps réel sur la zone 3 du bandeau tactile** : niveau de crête du son système via le peak meter WASAPI (pycaw `IAudioMeterInformation`, gère les deux générations de l'API). Barre verticale segmentée vert/ambre/rouge, marqueur de crête (peak-hold) qui retombe lentement, "Muet" si le son est coupé. Animation ~12 FPS (le bandeau plafonne à ~15-17 FPS, mesuré au chronomètre) — ne redessine que si le niveau change. Désactivable : `"vu_meter": {"enabled": false}` dans `akp05e_config.json` (réglage `fps` 2-30, défaut 12).

## [1.7.0] — 2026-11-09

### Ajouté
- **Page « Raccourcis »** (fournie par défaut) : 10 touches de raccourcis clavier Windows — Copier (Ctrl+C), Coller (Ctrl+V), Couper (Ctrl+X), Tout sélectionner (Ctrl+A), Gras (Ctrl+B), Italique (Ctrl+I), Souligné (Ctrl+U), Impr. écran, Échap, Annuler (Ctrl+Z). Utilise l'action `{"type": "keys", "keys": [...]}` (SendInput) — personnalise chaque touche dans `akp05e_config.json`.

## [1.6.3] — 2026-11-09

### Corrigé
- **Températures des disques enfin affichées** : un motif `"hw"` comme `"C:]"` matchait toutes les mesures du capteur `[C:]` (usure, heures, température…) et le tie-break par libellé le plus court sélectionnait la mauvaise. `hw_match` accepte désormais une **liste de sous-chaînes** (toutes requises, ex. `["C:]", "Drive Temperature"]`) et privilégie une température en cas de correspondances multiples. Boutons 6/7 par défaut : SSD C: et SSD E:/F: sur `Drive Temperature`.

## [1.6.2] — 2026-11-09

### Modifié
- **Page « Hardware » par défaut alignée sur les capteurs réels** (calibré sur un portable CPU Intel + Quadro M1200 + HD Graphics 530) : 7 touches — CPU (Package), iGPU (GPU Core Temperature), dGPU (GPU Temperature, 0 °C = Optimus endormi), PCH, CPU % (Total CPU Usage), SSD C: et SSD E: (Drive Temperature). Les motifs `"hw"` sont des sous-chaînes uniques des libellés HWiNFO — adapte-les via `--list-sensors` si ton matériel diffère.

## [1.6.1] — 2026-11-09

### Corrigé
- **Crash « access violation » de la page Hardware** : ctypes tronquait en 32 bits les handles et pointeurs 64 bits retournés par `OpenFileMapping`/`MapViewOfFile` sous Windows x64 — les prototypes WinAPI sont désormais déclarés explicitement (`restype`/`argtypes`).
- **Décodage des mesures aligné sur la vraie structure `#pragma pack(1)`** de HWiNFO : libellés aux offsets 12/140 (au lieu de 16/144), unité à 268, valeurs `double` à 284 — les libellés et valeurs étaient illisibles.
- **Garde-fous** : signature `HWiS` et dimensions de sections validées avant toute lecture en mémoire.

## [1.6.0] — 2026-11-09

### Ajouté
- **Page « Hardware » (HWiNFO64)** : températures et capteurs du PC en temps réel sur les touches via HWiNFO64 (licence Pro, option « Shared Memory Support » à activer). Nouveau type de bouton `"hw"` avec code couleur des températures (vert < 70 °C < orange < 85 °C < rouge), seuils personnalisables (`"thresholds"`), rafraîchissement toutes les 2 s (`"refresh"`).
- **Mode `--list-sensors`** : `python akp05e_app.py --list-sensors` affiche toutes les mesures disponibles pour choisir les capteurs à afficher sur les touches.
- **Lecture de la mémoire partagée HWiNFO64 par `ctypes`** — aucune dépendance supplémentaire à installer.

## [1.5.2] — 2026-11-08

### Ajouté
- **Gestes du bandeau tactile activés avec le mappage réel du firmware** (établi par calibration en v1.5.1) : tap zone 1..4 = codes `0x40`–`0x43`, swipe gauche = `0x39` (page précédente), swipe droit = `0x38` (page suivante). Un tap sur une zone déclenche l'action du knob correspondant (par défaut, tap zone 2 — carrousel — = page suivante) ; les codes `0x3A`/`0x3B` (probables swipe haut/bas) restent signalés comme inconnus.

## [1.5.1] — 2026-11-08

### Modifié
- **Mode calibration du bandeau tactile** : le firmware réel n'utilise pas les codes de gestes de la doc de référence (0x30..0x3F) mais d'autres rapports (0x38-0x43 observés sur le matériel de test). En attendant le mappage exact, chaque événement tactile est journalisé un par un avec son code et son état (`[tactile] code=0x.. état=..`) — sans dédoublonnage — pour établir la correspondance geste ↔ code et activer les actions par tap/swipe dans une prochaine version.

## [1.5.0] — 2026-11-08

### Ajouté
- **Changement de page au toucher sur le bandeau tactile** : **swipe gauche/droite** = page précédente/suivante ; **tap** sur une zone déclenche l'action du knob correspondant (et par défaut, tap sur la zone 2 — celle du carrousel — = page suivante). Retour console `[tactile] swipe …` / `[tactile] tap zone N`.
- **Journalisation des codes d'entrée inconnus** (`[protocole] entrée inconnue : 0x…`, une fois par code) pour affiner le mappage du protocole avec les retours du matériel réel. Le mappage des gestes (rapports 0x30..0x3F) suit la doc de référence ; si un firmware diffère, ces messages permettront de calibrer.

## [1.4.2] — 2026-11-08

### Corrigé
- **Bandeau tactile corrompu (zones brouillées qui évoluent à chaque rafraîchissement)** : le JPEG du bandeau était encodé en qualité 90 et le carrousel coloré introduit en v1.4.0 l'a fait grossir au point de déborder du buffer du firmware — le milieu de l'image se corrompait (carrés, décalages horizontaux), le délai de 2 ms de la v1.4.1 n'était donc pas la bonne piste. Le bandeau est désormais **compressé adaptativement** (`_pil_to_jpeg_capped`) : la qualité JPEG baisse automatiquement (80 → 65 → 50 → 35) jusqu'à rester sous 12 Ko, la taille qui s'affichait correctement dans les versions ≤ 1.3.x. Un avertissement s'affiche si la limite restait dépassée.

## [1.4.1] — 2026-11-08

### Corrigé
- **Bandeau brouillé au milieu (zones pages)** : les paquets HID de l'upload JPEG étaient envoyés en rafale sans délai ; le carrousel rendait l'image plus lourde (plus de paquets) et le firmware du deck en perdait certains en route — le JPEG se corrompait au milieu (zones gauche/droite lisibles, centre brouillé, confirmé par photo). Un délai de 2 ms entre les paquets (`_upload_jpeg`) laisse le firmware absorber les données.
- Ajout d'un **numéro de version affiché au démarrage** (`AKP05E Interface v1.4.1 — connecté`) pour diagnostiquer facilement la version en cours.


## [1.4.0] — 2026-11-08

### Ajouté
- **Zone 2 du bandeau en carrousel de pages** : la page courante s'affiche dans une **pilule arrondie** au centre, avec les pages précédente/suivante en **grisé** et des flèches triangulaires de chaque côté.
- **Mini-icône Material + couleur d'accent sur la page active** : chaque page peut définir `"icon"` et `"color"` (accent CSS) — la pilule prend le contour et le logo dans cette couleur (Accueil : `home` turquoise, Qobuz : `music_note` bleu ciel).
- La zone 2 reste utilisable en libellé libre si les pages ne sont pas activées (compat config plate).

## [1.3.1] — 2026-11-08

### Modifié
- **Retrait des boutons de bascule de page** : devenus redondants depuis que le knob 2 fait défiler les pages (v1.3.0).

## [1.3.0] — 2026-11-08

### Ajouté
- **Le knob 2 fait défiler les pages** : rotation CW = page suivante, CCW = page précédente (action `{"type": "page", "page": "next"}` / `"prev"`), actif sur toutes les pages et compatible avec les futures pages.
- L'appui du knob 2 reste libre (configurable).

## [1.2.1] — 2026-11-08

### Modifié
- **Page Qobuz** : le bouton Stop est retiré (Qobuz ne le gère pas) — touches : 1 = Play/Pause, 2 = Suivant, 3 = Précédent, 4 = Mute.
- **Page Accueil** : les boutons multimédia (6-8) sont retirés — ces commandes restent disponibles sur la page Qobuz.

## [1.2.0] — 2026-11-08

### Ajouté
- **Pages de profils** : la config classique forme la page « accueil » ; des pages supplémentaires se définissent dans la clé `pages`. Nouvelle action `{"type": "page", "page": "nom"}` pour basculer.
- **Page « Qobuz » par défaut** : Play/Pause, Suivant, Précédent, Mute (volume système) — pilotée par les touches média système (SMTC).

### Corrigé
- **Les touches média ne fonctionnaient pas** : les codes envoyés étaient des codes d'usage HID (0xE8…) et non les codes virtuels Windows officiels (`VK_MEDIA_PLAY_PAUSE` 0xB3, `VK_MEDIA_NEXT_TRACK` 0xB0, `VK_VOLUME_MUTE` 0xAD…).

## [1.1.2] — 2026-11-08

### Corrigé
- **Volume système invisible (« K1 ») avec pycaw ≥ 20240210** : l'application détecte automatiquement l'ancienne (`.Activate()`) ou la nouvelle (`.EndpointVolume`) génération de l'API pycaw.

## [1.1.1] — 2026-11-08

### Corrigé
- **Volume système bloqué sur « K1 »** : COM n'était pas initialisé dans les threads — chaque appel échouait silencieusement. COM est désormais initialisé dans chaque thread appelant (`_com_init()`).
- Les erreurs de lecture du volume ne sont plus avalées ; l'échec d'import de pycaw affiche sa cause exacte.

## [1.1.0] — 2026-11-08

### Ajouté
- **Volume système Windows en temps réel** (knob 1) via `pycaw` + zone tactile « Vol % » + surveillance en arrière-plan (0,5 s).
- `requirements.txt`, README bilingue (français + anglais).

### Modifié
- Config par défaut du knob 1 : `volume` → `sysvolume` (volume système réel) ; bandeau unifié Vol/Lum synchronisés.

## [1.0.0] — 2026-11-08

### Ajouté
- Version initiale : application de contrôle open source pour l'Ajazz AKP05E / AKP05 (Windows) — touches LCD Material Icons, 4 encodeurs, bandeau tactile, luminosité, actions configurables, keepalive, protocole HID rétro-ingénieré, licence MIT.

[1.8.1]: https://github.com/dalbertini/akp05e-interface/commits/main/
[1.8.0]: https://github.com/dalbertini/akp05e-interface/commits/main/
[1.7.0]: https://github.com/dalbertini/akp05e-interface/commits/main/
[1.6.3]: https://github.com/dalbertini/akp05e-interface/commits/main/
[1.6.2]: https://github.com/dalbertini/akp05e-interface/commits/main/
[1.6.1]: https://github.com/dalbertini/akp05e-interface/commits/main/
[1.6.0]: https://github.com/dalbertini/akp05e-interface/commits/main/
[1.5.2]: https://github.com/dalbertini/akp05e-interface/commits/main/
[1.5.1]: https://github.com/dalbertini/akp05e-interface/commits/main/
[1.5.0]: https://github.com/dalbertini/akp05e-interface/commits/main/
[1.4.2]: https://github.com/dalbertini/akp05e-interface/commits/main/
[1.4.1]: https://github.com/dalbertini/akp05e-interface/commits/main/
[1.4.0]: https://github.com/dalbertini/akp05e-interface/commits/main/
[1.3.1]: https://github.com/dalbertini/akp05e-interface/commits/main/
[1.3.0]: https://github.com/dalbertini/akp05e-interface/commits/main/
[1.2.1]: https://github.com/dalbertini/akp05e-interface/commits/main/
[1.2.0]: https://github.com/dalbertini/akp05e-interface/commits/main/
[1.1.2]: https://github.com/dalbertini/akp05e-interface/commits/main/
[1.1.1]: https://github.com/dalbertini/akp05e-interface/commits/main/
[1.1.0]: https://github.com/dalbertini/akp05e-interface/commits/main/
[1.0.0]: https://github.com/dalbertini/akp05e-interface/commits/main/
