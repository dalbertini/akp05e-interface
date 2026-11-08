# Changelog

Historique des versions de l'application. Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/),
numérotation [SemVer](https://semver.org/lang/fr/) : **MAJEURE**.**FONCTIONNALITÉ**.**CORRECTIF**.

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
