# Changelog

Historique des versions de l'application. Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/),
numérotation [SemVer](https://semver.org/lang/fr/) : **MAJEURE**.**FONCTIONNALITÉ**.**CORRECTIF**.

## [2.19.11] — 2026-11-13

### Corrigé

- **Détection des radios renforcée** — si la v2.19.10 suffisait dans la plupart des cas, une liste mixte (flux + morceaux) ou des URL personnalisées du plugin Radio Paradise (`radioparadise://…`) pouvaient encore être prises pour un album. Nouveau critère (une seule condition suffit) : au moins UNE URL `http(s)://` dans le niveau, OU le niveau appartient à une appli radio (`radioparadise`, `radios`, `tunein` — la commande CLI est propagée à tous les sous-niveaux). Résultat : plus aucune allusion à un album (ni « ▶ Album » en zone 3, ni page « Jouer l'album ») à n'importe quelle profondeur de l'appli Radio Paradise ; les albums Qobuz (`qobuz://…`) gardent leur page album intacte.

## [2.19.10] — 2026-11-13

### Corrigé

- **Les listes de radios ne sont plus traitées comme des albums** — dans l'appli Radio Paradise, la page de choix des mixes (Main Mix, Mellow Mix, Rockit…) affichait « ▶ Album » en zone 3, et ouvrir un mix montrait une page album (« Jouer l'album » + boutons morceaux avec surlignage bleu « sélection ») alors que ce sont des flux webradio : lancer « l'album » aurait mis tous les flux en file. Nouveau critère : une liste dont toutes les URL sont `http(s)://` (flux) n'est ni un album, ni « ▶ Album » — navigation normale où chaque bouton lance sa radio, et le titre du morceau (v2.19.9) occupe la zone 3. Les albums Qobuz (`qobuz://…`) et le bouton « Jouer l'album » sont inchangés ; la zone 3 garde la pause/reprise quand une radio de la page joue.

## [2.19.9] — 2026-11-13

### Ajouté

- **Morceau en cours aussi sur les pages LMS** — la zone 3 du bandeau affichait « K3 » (rien) sur les pages LMS quand elle n'avait ni position « i/N » ni bouton : elle montre maintenant le morceau en cours + l'artiste, comme sur l'accueil. Les boutons existants (« i/N », « ▶ Album », « ▶ Sélect. ») gardent la priorité — ce sont des zones tactiles. `poll_vu` sautant déjà les pages LMS, aucun conflit.

## [2.19.8] — 2026-11-13

### Corrigé

- **Le morceau radio s'affiche enfin** — le diagnostic v2.19.7 a livré la réponse du serveur : le morceau live est dans `remoteMeta` (`title`/`artist`), mais ce serveur met le **nom de la station** dans `current_title` (« FIP (MP3) »), et le décodage laissait `current_title` écraser le titre de `remoteMeta`. Nouvel ordre de priorité pour un flux : ① `remoteMeta` (présent = source live : titre + artiste), ② `current_title` s'il diffère du titre de piste (avec décodage « Artiste - Titre »), ③ titre de piste. Et dans la branche « lecteur affiché », le titre du `status` est prioritaire sur `current_title`. Le bandeau suit maintenant le morceau réellement diffusé par la webradio, morceau par morceau.

## [2.19.7] — 2026-11-13

### Corrigé

- **Le diagnostic ne pouvait structurellement jamais tirer** — le titre du bandeau de David venait de la branche « titre absent du poll `players` ET lecteur affiché ≠ candidat », qui interroge `now_info` à **chaque** cycle (d'où l'artiste toujours à jour) ; or le dump *one-shot* n'était câblé que dans les branches « titre déjà connu », jamais atteintes dans ce cas. Le dump est maintenant appelé dans les **trois** branches — il partira forcément dès qu'un lecteur joue avec un titre affiché.

## [2.19.6] — 2026-11-13

### Corrigé

- **Diagnostic du lecteur qui joue : dump one-shot inconditionnel** — les trois hypothèses de détection de flux (`http://`, tout schéma non-fichier, playlist ≤ 1 piste) n'ont jamais déclenché le diagnostic sur le serveur réel. On arrête de deviner : dès qu'un candidat joue avec un titre affiché (changement de titre ou re-poll de ~20 s), le dump part **sans condition** — `status` brut + `playing_track` brut du lecteur, tronqués — une fois par lancement (`[lms] bandeau : lecteur qui joue 'X' — status -> … — playing_track -> …`). Ce diagnostic permettra de localiser définitivement où ce serveur LMS range les métadonnées live des webradios.

## [2.19.5] — 2026-11-13

### Corrigé

- **Détection de flux élargie (le diagnostic webradio ne tirait jamais)** — test réel v2.19.4 : zone 3 = « FIP (MP3) » + artiste, mais **aucun** diagnostic en console. Cause : le dump et le décodage des métadonnées live exigeaient une URL `http(s)://` — or un favori radio joué via un plugin renvoie une URL d'un autre schéma (tunein, favoris…), vide, ou une playlist mono-piste. Est désormais considéré « flux » : une URL `://` non-fichier, ou le champ `remote` du `status` = 1, ou une playlist de ≤ 1 piste. Le diagnostic brut *one-shot* finira donc par tomber pour toute webradio, quel que soit le chemin serveur.

## [2.19.4] — 2026-11-13

### Corrigé

- **Bandeau : candidat de secours quand « isplaying » ment** — test réel v2.19.3 : FIP jouait sur la Squeezebox Radio Cuisine depuis plus d'une minute, aucune branche du titre n'a tiré. Cause : le poll `players` ne remontait **aucun** lecteur avec `isplaying=1` (flag non fiable chez certains serveurs/modèles — le vieux `playing=None`). Désormais, si aucun lecteur ne se dit « playing », le lecteur **affiché** dont le `status` (déjà interrogé chaque cycle, zéro requête) dit `mode=play` devient le candidat du bandeau, avec un diagnostic *one-shot* qui dump le poll `players` brut pour documenter le bug serveur.

## [2.19.3] — 2026-11-13

### Corrigé

- **Webradios sur le bandeau (round 2)** — après test réel v2.19.2 sur FIP : pas de titre, artiste juste mais figé, et aucun diagnostic. Trois causes : ① le re-poll de 20 s ne mettait à jour l'artiste **que si le titre était trouvé** — désormais titre et artiste sont rafraîchis indépendamment ; ② le diagnostic webradio ne se déclenchait que si `now_info` renvoyait un titre — il tire maintenant même sans titre, y compris depuis le re-poll ; ③ nouvelles sources de métadonnées live : `remoteMeta` (dict des métadonnées ICY du flux : artiste/titre) puis `track` top-level, en complément du décodage de `current_title`.

## [2.19.2] — 2026-11-13

### Corrigé

- **Webradios (FIP…) sur le bandeau** : le `title` d'une piste radio est le **nom du flux** (« FIP (MP3) »), pas le morceau en cours — et comme ce titre ne change jamais, l'artiste n'était rafraîchi quasiment jamais. Désormais : ① les métadonnées live du flux (métadonnées ICY dans `current_title`, souvent au format « Artiste - Titre ») sont décodées et affichées ; ② tant que le titre affiché est inchangé, un re-poll de `status` toutes les ~20 s suit le morceau réellement diffusé ; ③ au premier flux radio détecté, un diagnostic *one-shot* (`[lms] bandeau : webradio sur 'X' — status -> …`) dump la réponse brute du serveur pour documenter les champs live réels.

## [2.19.1] — 2026-11-13

### Corrigé

- **Titre du bandeau robuste** : le champ `title` du poll `players` est souvent vide (LMS ne le renvoie pas systématiquement). Le titre affiché en zone 3 privilégie désormais le `status` du lecteur affiché — déjà interrogé chaque cycle, donc **zéro requête supplémentaire** — puis le champ du poll, puis une requête `status` dédiée en repli tant que le titre manque. Si le serveur ne répond toujours pas, un diagnostic brut *one-shot* (`[lms] bandeau : titre indisponible pour 'X' — status -> …`) remplace l'ancien `playing=None`.

## [2.19.0] — 2026-11-13

### Ajouté
- **Titre du morceau en cours sur le bandeau tactile (zone 3)** — quand un lecteur Lyrion/Squeezebox joue, la zone 3 affiche le **titre** (grand) et l'**artiste** (petit, dessous) à la place du VU-mètre ; dès que la lecture s'arrête, le VU-mètre reprend sa place. Le lecteur affiché est prioritaire (s'il joue), sinon le premier lecteur actif. Les titres trop longs sont tronqués proprement avec « … » (jamais de débordement sur la zone voisine). Coût réseau quasi nul : le titre vient du poll `players` (2 s) déjà en place, et l'artiste n'est demandé au serveur **qu'au changement de morceau** (une requête `status` par titre). Le bandeau n'est repeint que lorsque le titre change (une fois par morceau), pas en continu. `"strip_title": {"enabled": false}` dans la config pour garder le VU-mètre en permanence. Sur les pages LMS, la zone 3 garde ses sémantiques existantes (position « i/N », boutons ▶ Album / ▶ Sélect.).

## [2.18.4] — 2026-11-13

### Corrigé
- **`--identify` : `HidD_GetFeature` ne répond pas non plus** (test réel v2.18.3 : aucune ligne « Feature report », aucune erreur — toutes les combinaisons report ID / taille ont échoué). Dernière piste documentée : ajazz-control-center précise que la réponse `VER` se lit via GET_REPORT **`HIDIOCGINPUT`/`HIDIOCGFEATURE`** — soit aussi le report **INPUT**. Le mode tente donc désormais `HidD_GetInputReport` (report IDs `0x00` puis `0x01`, tailles selon `InputReportByteLength` puis 33→1025) après l'échec des feature reports, avec un handle robuste (`hid_handle`/`_hid_handle`/`handle` selon la version de pywinusb). Si tout échoue, une ligne de diagnostic est affichée (« GET_REPORT direct : aucune réponse sur N essais (handle=…, FeatureReportByteLength=…, InputReportByteLength=…) ») pour que le résultat soit définitivement documenté dans un rapport de bug.

## [2.18.3] — 2026-11-13

### Corrigé
- **`--identify` : `find_feature_reports()` de pywinusb ne retourne rien** (test réel v2.18.2 : aucune ligne « Feature report », aucun message d'erreur) — le descripteur HID de l'AKP05E ne déclare **aucun item Feature**, donc pywinusb n'expose pas le report 0x01. Le mode tente désormais un **GET_REPORT direct** : `HidD_GetFeature` (hid.dll, via ctypes), exactement ce que fait `hid_get_feature_report` (hidapi) chez DeckBridge/mirajazz — sans passer par le descripteur. Essais sur les report IDs `0x01` puis `0x00`, avec les tailles croissantes (`FeatureReportByteLength` des capacités si exposé, puis 21/33/65/…/513 octets — `HidD_GetFeature` est strict sur la longueur) ; chaque réponse non vide est affichée en hex + ASCII et recherchée pour le motif de version (`V` + chiffre + alphanumériques). Tenté à l'ouverture puis après chaque handshake `VER` muet.

## [2.18.2] — 2026-11-13

### Corrigé
- **`--identify` : les 3 handshakes `VER` restent muets** (test réel v2.18.1) — et pour cause : sur ce firmware, la réponse `VER` n'arrive **jamais** sur le endpoint IN. Constat croisé de deux projets open source : DeckBridge (*« The CRT VER reply never arrives on V3.AKP05E.02.007, but feature report 0x01 returns the version text »*) et ajazz-control-center (*« the VER response is pulled via GET_REPORT (HIDIOCGINPUT/HIDIOCGFEATURE), not delivered unsolicited on the interrupt-IN endpoint »*). Le mode lit donc désormais les **feature reports HID (GET_REPORT)** — le chemin qui renvoie directement le texte de version (ex. `V3.AKP05E.02.007`) : lecture directe à l'ouverture, puis relecture après chaque handshake `VER` muet ; la chaîne détectée est affichée en clair (« VERSION FIRMWARE (feature report) : … ») et les handshakes sont ignorés si elle est déjà obtenue. Les 3 handshakes `VER` de la v2.18.1 sont conservés en repli diagnostic.

## [2.18.1] — 2026-11-13

### Corrigé
- **`--identify` : le `VER` seul reste muet** (test réel : aucune réponse, pas même un ACK) — la référence ajazz-control-center parle d'un « CRT VER handshake » ayant répondu `V3.AKP05E.01.007` sur un AKP05E de série. Le mode tente désormais 3 handshakes : `VER` direct au boot, puis `DIS` → `VER` (après initialisation), puis `CONNECT` → `VER` (après keepalive), et s'arrête au premier qui répond. Premier test réel : le deck de David se présente comme « HOTSPOTEKUSB HID DEMO » (fabricant USB HOTSPOTEK — confirmant l'origine Mirabox/HOTSPOTEK), n° de série `C771C778173B`.

## [2.18.0] — 2026-11-13

### Ajouté
- **Mode `--identify` : identification exacte du matériel et du firmware** — l'AKP05E étant un rebrand AJAZZ du matériel Mirabox/HOTSPOTEK (aucune doc officielle), ce mode affiche le VID/PID, les chaînes USB (fabricant, produit, n° de série, version) et interroge le firmware du deck via la commande `VER`, affichée en hexadécimal à copier-coller dans tout rapport de bug. Guidance PowerShell incluse si aucun appareil n'est détecté.
- **README : nouvelle section « Matériel & références »** — note sur l'origine Mirabox du matériel, tableau des projets open source de la famille (SDK officiel Mirabox, opendeck-akp05, mirajazz, DeckBridge, AKP05E-Open-Firmware, zeccola/ajazz-akp05, ajazz-control-center) avec leur niveau d'activité vérifié, et les tailles de bandeau variables selon les révisions matérielles (176×112, 800×112, 800×128).

## [2.17.1] — 2026-11-13

### Amélioré
- **`--calibrate-strip` : sondes à gros chiffres lisibles** (police 24 px au lieu de 11 — les repères étaient illisibles sur les photos du premier test réel). Résultats du premier passage : le firmware **redimensionne** l'image au panneau (grille 800x112 affichée plein cadre), la hauteur native est **supérieure à 112** (estimation ~128), et une sonde 800x480 fait **déborder le buffer du firmware** (corruption attendue, sonde retirée). Nouvelles sondes : 800x128 (candidat natif, limite actuelle 112 marquée en jaune vif), 1024x128 et 1024x112 pour trancher la largeur.

## [2.17.0] — 2026-11-13

### Ajouté
- **Mode `--calibrate-strip` : calibration du bandeau tactile** — le logo de démarrage AJAZZ occupe plus de pixels que les images 800x112 envoyées par l'app, signe que la résolution native du bandeau est probablement supérieure. `python akp05e_app.py --calibrate-strip` affiche successivement 5 sondes graduées (grille 800x112 de référence, puis 1024x112, 800x140, 1024x140 et 800x480) : repères de colonnes tous les 100 px, lignes tous les 14 px, limites des 4 zones tactiles en bleu et cadre rouge au bord exact de l'image. Une photo de chaque sonde suffit à déduire la résolution réelle et si le firmware recadre ou redimensionne. Knob 1 : sonde suivante/précédente ; appui knob 1 ou n'importe quelle touche : quitter.

## [2.16.4] — 2026-11-13

### Corrigé
- **Icône systray : dernier débordement corrigé** (test réel) — « argument 11: int too long to convert » : `CreateWindowExW` avait son type de retour (handle 64 bits) mais pas ses types d'arguments ; le `hInstance` renvoyé par `GetModuleHandleW` débordait en conversion 32 bits. La signature complète des 12 arguments est désormais déclarée.

## [2.16.3] — 2026-11-13

### Corrigé
- **Icône systray : `CreateBitmap` introuvable** (test réel) — cette API n'existe pas dans `user32.dll` ; elle est désormais chargée depuis `gdi32.dll`, comme le reste des APIs de dessin. Tous les prototypes ctypes du tray sont déclarés en un seul endroit (`_tray_set_prototypes()`), avec types d'arguments et de retour explicites.

## [2.16.2] — 2026-11-13

### Corrigé
- **Icône systray absente après démarrage automatique** — la fenêtre du tray était créée sur le thread principal alors que sa boucle de messages tournait dans un autre thread : Windows exige que les messages d'une fenêtre soient traités par le thread qui l'a créée. Toute la création (fenêtre + icône) et le pompage des messages s'exécutent désormais dans le thread dédié du systray. De plus, `start()` ne lève plus jamais d'exception : en cas de panne, un message clair s'affiche et **l'application continue de fonctionner sans icône** (un échec pouvait tuer l'app en silence, invisible sous `pythonw`).
- Note : sous Windows 11, les nouvelles icônes peuvent être masquées dans le chevron « ^ » de la zone de notification — glisser l'icône AKP05E sur la barre des tâches pour l'épingler.

## [2.16.1] — 2026-11-13

### Corrigé
- **Autostart sans droits administrateur** — `--install-autostart` échouait avec « Erreur : Accès refusé » : la commande `schtasks /SC ONLOGON` exige une console élevée. L'app tente toujours le Planificateur en premier, puis **retombe automatiquement** sur un raccourci dans le dossier Démarrage (créé via PowerShell + WScript.Shell, aucun droit admin requis). Le délai de 30 s est alors assuré par l'app elle-même (le raccourci ajoute `--startup`, et le démarrage patiente `startup_delay` secondes — 30 par défaut, réglable dans la config). `--uninstall-autostart` retire les deux formes ; « À propos » reflète l'état.

## [2.16.0] — 2026-11-13

### Ajouté
- **Icône systray** (ctypes pur, zéro dépendance) : icône près de l'horloge Windows, générée par l'app et reflétant l'état du deck — **vert** = connecté, **gris avec lune** = veille, **rouge avec croix** = déconnecté ; tooltip « AKP05E vX.Y.Z — page courante ». Clic droit : *Veille / Réveiller le deck*, *Luminosité +10 / -10 / par défaut*, *Page suivante / précédente*, *À propos*, *Quitter* (sortie propre identique à Ctrl+C). Double-clic : *À propos*. Les actions transitent par une file exécutée par la boucle principale — le menu ne touche jamais le deck directement.
- **Autostart** : `python akp05e_app.py --install-autostart` programme le lancement automatique via le **Planificateur de tâches** (à l'ouverture de session, après **30 s** pour laisser l'USB et le réseau arriver ; utilise `pythonw.exe` si disponible, donc sans fenêtre console). `--uninstall-autostart` le retire. L'état est affiché dans « À propos ».

## [2.15.1] — 2026-11-13

### Corrigé
- **Veille étanche** — pendant la veille du deck, la touche horloge se rallumait seule à chaque changement de minute (et les minuteurs/chronos actifs ou le VU-mètre auraient fait de même) : ces repeints directs contournaient les gardes de veille. Les deux seuls points de sortie des images vers le deck (`set_image` et `set_strip`) ignorent désormais tout envoi tant que le deck dort — plus rien ne peut s'afficher, quelle que soit la source. La restauration au réveil est inchangée.

## [2.15.0] — 2026-11-13

### Ajouté
- **Reprise automatique après la veille du PC** — pendant la veille du PC, l'USB se suspend et le firmware du deck redémarre : il affichait son logo de démarrage (touches + bandeau tactile) et l'affichage de l'app n'était pas restauré. Un watchdog détecte la sortie de veille (saut d'horloge murale > 30 s), attend 3 s (paramétrable via la clé de config `resume_repaint_delay`, en secondes) puis renvoie le handshake d'ouverture et repeint la page et le bandeau : **l'affichage repart exactement où il en était**, sans relancer l'app. Console : `[resume] sortie de veille du PC détectée…` puis `[resume] deck repeint après le réveil du PC`.
- **Auto-reconnexion du deck** — si la liaison HID échoue (PC réveillé, câble rebranché…), l'app tente maintenant de fermer et rouvrir la connexion puis de tout repeinter, au lieu d'afficher « Deck débranché — relance l'application ». Ce message n'apparaît plus que si la reconnexion échoue.

## [2.14.9] — 2026-11-13

### Modifié
- **Veille : écrans réellement éteints** — la luminosité 0 coupe le rétroéclairage, mais les images restaient en mémoire d'écran. La mise en veille vide désormais toutes les mémoires d'écran (commande `CLE` : touches, écran, bandeau tactile) : écrans totalement noirs, rien ne traîne. Au réveil, une simple pression restaure la luminosité précédente et repeint la page et le bandeau — l'affichage repart exactement où on en était.

## [2.14.8] — 2026-11-13

### Corrigé
- **Mise en veille : le deck se rallumait au relâchement de la touche « Veille »** — la presse passait bien le deck en veille, mais le RELÂCHEMENT de la même touche arrivait juste après et le réveillait aussitôt (effet « baisse puis retour de luminosité »). Les relâchements sont désormais absorbés pendant la veille : seule une nouvelle PRESSION (touche, encodeur, rotation, bandeau tactile) réveille le deck, toujours sans exécuter l'action de l'événement de réveil.

### Modifié
- **Veille complète** : pendant la veille, plus AUCUN rafraîchissement n'est envoyé au deck (horloge, poll LMS, VU-mètre, bandeau tactile) — le deck reste totalement dormant ; tout est repeint au réveil. Console : `[veille] deck en veille complète — appuie sur une touche pour le réveiller` puis `[veille] deck réveillé`.

## [2.14.7] — 2026-11-12

### Ajouté
- **Mise en veille du deck** — nouvelle action `{"type": "sleep"}` : éteint les écrans (luminosité 0, maintenue par le keepalive) et **n'importe quel événement** (touche, encodeur, rotation, bandeau tactile) réveille le deck au niveau de luminosité précédent. L'événement de réveil est consommé : son action ne s'exécute pas, pour éviter les clics accidentels. Une touche « Veille » (icône lune, violet) est ajoutée automatiquement sur la page d'accueil au premier emplacement libre ; accueil complet -> remplacer une touche par `{"type": "sleep"}`.

## [2.14.6] — 2026-11-12

### Revenu en arrière
- **Page Hardware : retour à l'affichage sans décimale** — testé sur le deck, le format « 45.7 °C » était moins lisible que « 46 °C » et les capteurs progressent par paliers de 0,5 : la demi-unité n'apportait rien. Le format de la 2.14.4 est restauré (décimale uniquement sous 9,95).

## [2.14.5] — 2026-11-12

### Modifié
- **Page Hardware : températures avec un chiffre après la virgule** — « 45.7 °C » au lieu de « 46 °C » (la décimale était coupée dès que la valeur dépassait 10). Aucun autre changement sur la page : libellés, unités, seuils de couleur et rafraîchissement restent identiques.

## [2.14.4] — 2026-11-11

### Corrigé
- **Volume LMS : fin du lag de 2 secondes sur le bandeau** — tourner le knob 1 sur une sous-page LMS envoyait bien la commande au serveur, mais le bandeau n'affichait le nouveau volume qu'au prochain cycle de rafraîchissement (toutes les 2 s). Le bandeau se met maintenant à jour immédiatement (valeur optimiste + redessin sans attendre le poll, qui resynchronise l'état réel du serveur) ; idem pour le bouton muet.

### Optimisé
- **Encodage du bandeau : un seul passage par rafraîchissement** — la compression adaptative (2.14.3) retâtait jusqu'à 4 qualités à chaque redessin ; la dernière qualité valide est désormais mémorisée (rendu aussi plus stable visuellement).

## [2.14.3] — 2026-11-11

### Corrigé
- **Bandeau tactile : artefacts « carrés de pixels » pendant la lecture** — après l'apparition de la pilule « ▶ Album » (bandeau enrichi : pilule à liseret, triangle, carrousel avec icône, noms de lecteur longs), le JPEG du bandeau frôlait la limite du buffer firmware : la zone 1 (fin du JPEG = gauche physique après rotation 180°) se corrompait en blocs, puis les artefacts se propageaient vers la zone 4 au fil des rafraîchissements (knob 1). Marge de sécurité : taille max abaissée de 12000 à 9000 octets, qualités de compression étendues (80→20), délai inter-paquets doublé (4 ms) pour les gros transferts, et une ligne de diagnostic « [bandeau] JPEG du bandeau : N octets » affichée au premier envoi.

## [2.14.2] — 2026-11-11

### Corrigé
- **Carrousel du bandeau : pilule « Accueil » avec l'icône d'une autre page sur les sous-pages LMS** — les sous-pages (lecteur, favoris, applis, navigation, album) ne font pas partie du cycle du carrousel : l'index retombait à 0 et la pilule affichait « Accueil »… avec l'icône de la sous-page réelle (haut-parleur du lecteur, pièce puzzle de la navigation), comme si les icônes changeaient toutes seules. La pilule affiche désormais la page ou la sous-page COURANTE (« Lecteur », « Applis », « Album »…), les voisines grises restant celles de l'ancre « LMS ».

## [2.14.1] — 2026-11-11

### Corrigé
- **« i/N » : position du morceau enfin récupérée** — le serveur LMS ne renvoie pas toujours « playlist_cur » dans « status » (diagnostic utilisateur : cur absent, tracks présent). La lecture utilise désormais « status - 1 » (piste EN COURS, pas la première de la liste) avec l'URL (tags u), et un fallback « playlist index ? » pour la position.
- **Tap zone 3 : pause/reprise réparée** — même cause racine : sans l'URL de la piste en cours, l'app ne pouvait pas reconnaître que l'album affiché était celui qui jouait et relançait l'album à chaque tap. L'URL de la piste courante est maintenant connue, donc le tap pause l'album affiché en lecture, reprend en pause, et lance un autre album sinon.

## [2.14.0] — 2026-11-11

### Corrigé
- **Tap zone 3 : lancement d'un album2 pendant la lecture d'album1** — le tap mettait systématiquement en pause au lieu de lancer l'album affiché. La pause/reprise ne s'applique désormais QUE si la piste en cours appartient au niveau affiché ; naviguer vers un autre album et taper le lance (l'album1 s'arrête, remplacé par album2).
- **« i/N » : diagnostics one-shot renforcés** — si la position reste absente du bandeau, la console imprime une ligne explicite (« position indisponible… », « pas d'info de lecture (playing=None)… » ou « playing_info a échoué… ») à copier pour le diagnostic.

## [2.13.9] — 2026-11-11

### Ajouté
- **Tap zone 3 = pause / reprise** : pendant la lecture d'un album, un tap sur la zone 3 met en pause (console `[lms] pause (…)`) ; un nouveau tap reprend ; lecteur arrêté = lancement de l'album complet comme avant.

### Corrigé
- **« i/N » désormais maintenu en pause** (l'info de lecture était coupée dès que le lecteur ne jouait plus) et **diagnostic one-shot** en console si la position du morceau reste indisponible (ligne `[lms] bandeau : position indisponible (cur=…, tracks=…, mode=…)` à copier en cas de problème).

## [2.13.8] — 2026-11-11

### Ajouté
- **« i/N » sur la zone 3 du bandeau** : quand le lecteur affiché joue une liste d'au moins 2 pistes (album lancé via « ▶ Album »…), la zone 3 affiche la position du morceau en cours et le total (ex. « 3/12 »), mise à jour en temps réel.

### Modifié
- **Zone 3 redessinée** : pilule arrondie avec liseret bleu accent (même style que le carrousel de la zone 2), centrée verticalement dans la zone — l'ancien libellé gris était perdu en haut du petit écran. S'applique à « i/N », « ▶ Album » et « ▶ Sélect. ».

## [2.13.7] — 2026-11-11

### Corrigé
- **Le symbole « ▶ » ne s'affichait pas sur le bandeau tactile** — le glyphe U+25B6 ne fait pas partie du jeu de caractères WGL4 de la police utilisée (Arial). Le triangle de « ▶ Album » / « ▶ Sélect. » (zone 3) est désormais dessiné en polygone (indépendant de la police), en couleur d'accent bleue avec son libellé, pour bien indiquer que la zone est active.

## [2.13.6] — 2026-11-11

### Corrigé
- **Tap sur le bandeau tactile : les actions LMS ne s'exécutaient pas** (retour « Type d'action inconnu ») — le tap sur une zone appelait le distributeur d'actions générique, qui ne connaît pas les types `lms_*`. Il suit désormais le même routage que l'appui physique sur l'encodeur : les actions LMS vont au gestionnaire LMS. Concerne notamment « ▶ Jouer l'album » (zone 3) introduit en 2.13.5.

## [2.13.5] — 2026-11-11

### Ajouté
- **« ▶ Jouer l'album » dans la zone 3 du bandeau tactile** (demande utilisateur) : sur la page des morceaux d'une appli (Qobuz…), la zone 3 affiche **« ▶ Album »** dès que le niveau courant contient au moins 2 morceaux jouables — **un tap dessus lance l'album complet** (1er morceau en lecture, les suivants en file). L'appui du knob 3 fait de même ; la rotation du knob 3 continue de faire défiler la liste, et le retour reste sur la touche 10.
- **Page « album » : la zone 3 affiche « ▶ Sélect. »** (l'appui du knob 3 / le tap joue le morceau sélectionné).

## [2.13.4] — 2026-11-11

### Corrigé
- **Page « album » : niveaux Qobuz mixtes** — la sonde des « morceaux-répertoires » accepte désormais les items qui possèdent DÉJÀ leur URL de lecture (want_url) à côté d'items à résoudre un par un ; seuls les items sans URL demandent une requête supplémentaire.
- **Clic sur un morceau d'un feed Qobuz = lecture directe** — un sous-niveau contenant exactement 1 morceau jouable est désormais joué immédiatement, au lieu d'ouvrir une page « album » d'un seul titre.
- **Diagnostic précis** : en cas d'échec de la détection, la console affiche l'item BLOQUANT et son index (`[lms] ... bloquant à l'index N : …`) en plus du premier élément du niveau.

## [2.13.3] — 2026-11-11

### Corrigé
- **Page « album » : feeds Qobuz où chaque morceau est un répertoire** — certains feeds renvoient des morceaux `hasitems` SANS URL, l'URL de lecture étant un cran plus bas (dans un sous-niveau contenant exactement 1 item jouable). La navigation sonde désormais le premier morceau : si son sous-niveau est un morceau jouable, les URLs de TOUS les morceaux sont résolues (une requête chacune) et la page « album » complète s'ouvre. Une liste d'albums (sous-niveau de plusieurs éléments) échoue à la sonde et reste en navigation normale.
- Journaux : `[lms] album « … » : N morceaux (URLs résolues un par un)`, et un message explicite si la résolution échoue en cours de route.

## [2.13.2] — 2026-11-11

### Corrigé
- **Page « album » : détection et lecture enfin fonctionnelles avec les feeds sans URL (Qobuz)** — le serveur ne renvoie pas l'URL de lecture des morceaux par défaut : la navigation envoie désormais `want_url:1` (mécanisme xmlbrowser standard de LMS), ce qui fournit l'URL réelle de chaque morceau (`playlist play <url>`).
- **Un item drillable (`hasitems`) n'est plus joué en direct** même s'il possède une URL — sinon le clic sur un album l'aurait lu sans jamais ouvrir la page « album ».
- **Nouvelle « feuille » de menu jouable** : un item dont le sous-niveau est vide mais qui possède une URL de lecture est joué directement (utile pour les morceaux `hasitems` des feeds Qobuz).
- Refactor : les branches cmd/item_id de la navigation partagent `lms_open_level()` (page album / lecture feuille / navigation + diagnostic).

## [2.13.0] — 2026-11-11

### Ajouté
- **Page « album » dans la navigation des applis (Qobuz…)** : appuyer sur un album n'ouvre plus une cascade de répertoires — une page dédiée s'affiche avec **« ▶ Jouer l'album »** (touche 1 : l'album complet en playlist) et **les morceaux directement sur les touches 2-9** (« 01 Artiste – Titre », appui = lecture du morceau). **Knob 3** : rotation = sélection du morceau (touche mise en évidence, la liste défile au-delà de 8), **appui = lecture du morceau sélectionné**. Touche 10 = retour. Fonctionne avec toute appli LMS dont le sous-niveau est une liste de morceaux (Qobuz, Radio Paradise…).

## [2.13.1] — 2026-11-11

### Corrigé
- **Page « album » : les en-têtes décoratifs du menu (type `text`/`header`, renvoyés par certains plugins comme Qobuz) ne font plus échouer la détection de la page album** — seuls les morceaux comptent désormais.
- **Diagnostic console** : si un clic sur un album ouvre encore un répertoire au lieu de la page album, la ligne `[lms] pas une page album : N él., 1er=…` affiche le premier élément renvoyé par le serveur (à copier dans une issue).

## [2.12.3] — 2026-11-11

### Ajouté
- **Support du mode compilé (EXE PyInstaller)** : une fois l'application figée en `.exe`, la configuration (`akp05e_config.json`) et le cache d'icônes (`.icons_cache/`) sont rangés **à côté de l'EXE** — plus dans le dossier temporaire interne de PyInstaller, qui était effacé à chaque lancement.

## [2.12.2] — 2026-11-11

### Corrigé
- **Assistant `--setup-lms` : le serveur était détecté à l'écran du réseau mais rejeté par l'application** — les LMS récents répondent à la découverte par un simple datagramme `E` : l'adresse du serveur est l'IP *émettrice* du paquet, pas un payload `IPAD:` (format ancien, toujours accepté). La découverte lit désormais aussi l'IP émettrice des réponses `E` (les émissions `e` des lecteurs Squeezebox sont ignorées).

## [2.12.1] — 2026-11-11

### Corrigé
- **Assistant `--setup-lms` : « Aucun serveur détecté » alors que le serveur est joignable** — le broadcast général `255.255.255.255` est souvent filtré (box, pare-feu Windows). La découverte émet désormais AUSSI un broadcast dirigé vers le sous-réseau local (p.ex. `192.168.1.255`, calculé depuis l'adresse IP du PC), en plusieurs salves, avec un délai d'écoute allongé (~3 s).

## [2.12.0] — 2026-11-11

### Ajouté
- **Assistant de configuration LMS `--setup-lms`** : `python akp05e_app.py --setup-lms` détecte automatiquement le serveur Lyrian Media Server sur le réseau local (découverte Squeezebox : broadcast UDP 3483), vérifie la connexion (nombre de lecteurs), propose le serveur trouvé ou accepte une saisie manuelle (IP ou IP:port), puis enregistre l'adresse dans `akp05e_config.json` — l'application démarre ensuite normalement. Au lancement, un indice rappelle la commande si LMS n'est pas configuré. Plus besoin d'éditer le JSON à la main.

## [2.11.0] — 2026-11-11

### Ajouté
- **Écran d'infos caché sur la touche horloge** : un appui affiche la version de l'application, la licence (MIT) et un petit crédit — la touche revient automatiquement à l'horloge au bout de ~8 secondes.

### Modifié
- **Raccourci « Minut. » retiré de la page d'accueil** (nouvelles configurations) : la touche est éteinte ; la page des minuteurs reste entièrement accessible via le carrousel du knob 2. Les configurations existantes gardent leurs touches — supprimer simplement l'entrée correspondante dans `akp05e_config.json`.
- **Touche « LMS » d'accueil : plus d'ajout automatique en double** — si une touche pointe déjà vers la page LMS, l'application n'en ajoute pas une seconde dans le premier emplacement libre.

## [2.10.4] — 2026-11-11

### Corrigé
- **Page principale LMS : la rotation du knob 1 ne changeait toujours pas le volume** — la page ne mappait en réalité AUCUNE action sur le knob 1 (le correctif v2.10.3 visait par erreur un bloc inactif de la page du lecteur). Le knob 1 (rotation et appui/muet) y est désormais mappé sur le volume système, à l'identique de l'accueil ; la page du lecteur reste gérée par l'attachement automatique à la squeezebox affichée.

## [2.10.3] — 2026-11-11

### Corrigé
- **Page principale LMS : la rotation du knob 1 ne changeait pas le volume général** — la page mappait le knob 1 sur le volume du lecteur LMS « sélectionné », souvent absent. Le knob 1 pilote désormais le volume système (rotation et appui/muet), à l'identique de l'accueil ; le volume de la squeezebox reste réservé aux pages du lecteur (lecteur, favoris, applis, navigation).

## [2.10.2] — 2026-11-11

### Corrigé
- **Knob 1 : volume de la Squeezebox uniquement sur les sous-pages LMS** (lecteur, favoris, applis, navigation). Sur la page principale LMS et partout ailleurs (accueil, autres pages), le knob 1 et la zone 1 du bandeau tactile reviennent au volume général de Windows — y compris après un retour accueil au knob 2, qui ne reste plus bloqué sur « Vol SBT … ».

## [2.10.1] — 2026-11-11

### Corrigé
- **VU-mètre encore visible sur les pages LMS et leurs sous-pages** (lecteur, favoris, applis, navigation) malgré la v2.10.0 : le bandeau recollait les pixels du VU en cache sans vérifier que la zone 3 devait bien l'afficher. Le recollage n'a désormais lieu que si la zone est « VU » — sur les pages LMS, la zone 3 affiche bien « K3 ».

## [2.10.0] — 2026-11-11

### Ajouté
- **Volume de la Squeezebox affichée, partout** : dès qu'un lecteur LMS est sélectionné, le knob 1 pilote son volume (appui = muet) **sur toutes les pages**, et la zone 1 du bandeau tactile affiche « Vol SBT Orange » / « Vol SBR Cuisine » (noms courts automatiques : Touch → SBT, Radio → SBR) avec le pourcentage en temps réel — plus seulement dans la page du lecteur.
- **Retour accueil instantané** : un appui sur le knob 2 ramène toujours à l'accueil, quelle que soit la page (rotation et swipe du knob 2 conservent le carrousel).

### Modifié
- **VU-mètre retiré des pages LMS** (lecteur, favoris, applis, navigation) : la zone 3 du bandeau affiche « K3 » en attendant la future redéfinition des touches knob et de l'écran tactile ; le VU-mètre reste actif sur toutes les autres pages.
- **Quitter la page du lecteur efface la squeezebox sélectionnée** : le bouton « Retour » vers la liste des lecteurs rend le knob 1 et la zone 1 au volume système Windows.

## [2.9.3] — 2026-11-11

### Corrigé
- **« [erreur lms peinture] 'NoneType' object has no attribute 'find_output_reports' » au quit** : à la fermeture (Ctrl+C), `device.close()` met le périphérique HID à `None`, mais les threads démons de rafraîchissement (poll LMS toutes les 2 s, minuteurs…) pouvaient encore tenter une peinture pendant le shutdown. L'envoi HID (`_send`) devient un no-op silencieux quand le deck est fermé — plus d'erreur ni de traceback à la sortie, en complément du correctif v2.8.6.
## [2.9.2] — 2026-11-11

### Corrigé
- **Libellés tronqués sur les touches** (Radio Paradise : « World/Eclectic Mix », « Global Mix A (World/Eclectic) »…) : le texte est désormais découpé en 2 lignes équilibrées, la police s'ajuste automatiquement (20 → 11 px par crans de 1) jusqu'à ce que la plus large ligne tienne dans les 112 px, et un mot composé trop long est recoupé en 3 lignes au plancher. Aucun rafraîchissement supplémentaire : le rendu reste statique, donc aucun impact sur le débit HID.
## [2.9.1] — 2026-11-11

### Modifié
- **Touches de liste LMS sans contenu = touches éteintes** : sur les pages Applis, Favoris, Navigation (et lecteurs au-delà de la liste), les emplacements sans élément n'affichent plus « - / (vide) » avec une icône — la touche est simplement éteinte (aplat noir, propre). Exemple : 3 applis installées (Radio Paradise, Qobuz, Effets sonores) → touches 4 à 9 éteintes, la touche 10 (Retour) reste inchangée.
## [2.9.0] — 2026-11-11

### Ajouté
- **Touche horloge** : nouvelle action `{"type": "clock", "color": "#81D4FA"}` — liseré arrondi double, heure `HH:MM` en grand et date en français (« mer. 11 nov. ») dessous. Repeinte automatiquement au changement de minute (aucun trafic HID inutile), protégée par la génération de peinture v2.8.7. Le clic est sans effet.

### Modifié
- **Le raccourci « LMS » entre dans le carrousel** (pilule du bandeau, knob 2, swipe) quand LMS est configuré ; les sous-pages LMS (lecteur, favoris, applis, navigation) restent en accès direct par navigation interne.
- **La touche 5 « F5 / Rafraîchir » de l'accueil laisse place à l'horloge** dans la config par défaut (pour une config existante : remplacer la touche 5 par `{"action": {"type": "clock", "color": "#81D4FA"}}`).
## [2.8.7] — 2026-11-11

### Corrigé
- **Icônes obsolètes ou en doublon au changement de page** : les threads de rafraîchissement (LMS, minuteurs, chronomètre, capteurs HWiNFO, bandeau) vérifient la page AVANT de peindre, mais l'envoi des images arrivait APRÈS le changement de page — des touches gardaient alors des icônes de l'ancienne page. Nouveau mécanisme de « génération de peinture » : chaque changement de page invalide les peintures en cours et chaque thread abandonne l'envoi si la page a changé entre-temps (12 gardes).
## [2.8.6] — 2026-11-10

### Corrigé
- **« Fatal Python error: _enter_buffered_busy » au Ctrl+C** : les threads démons (poll LMS, volume, hardware…) pouvaient encore écrire sur la console pendant la finalisation de l'interpréteur (bug CPython corrigé en 3.13). Après « Au revoir. », stdout/stderr sont détournés vers `/dev/null` : plus rien à verrouiller, plus de crash à la sortie — sans rien changer au comportement.
## [2.8.5] — 2026-11-10

### Corrigé
- **Descente des dossiers d'applis SANS commande** (diagnostic : Main Mix de Radio Paradise, `type=outline`, clés `hasitems`/`id`, aucune `cmd`) : protocole CLI strict du xmlbrowser — pour descendre, on RENVOIE la commande du niveau courant en ajoutant `item_id:<id>` (comme les favoris). La pile de navigation mémorise désormais la commande et les paramètres de chaque niveau, donc l'imbrication (mixes Radio Paradise, dossiers Qobuz) s'enchaîne naturellement.
## [2.8.4] — 2026-11-10

### Corrigé
- **Descente dans les dossiers des applis (Qobuz, Radio Paradise)** : les éléments de menu au format « actions » du xmlbrowser JSON (`{actions: {go: {cmd: [...], params: [...], itemsParams: [...]}}}`) sont désormais reconnus — commandes et paramètres en listes transmis tels quels au CLI, `params` **et** `itemsParams` concaténés, `weblink` en repli d'URL, `isaudio` compté comme jouable. Le diagnostic « élément non jouable » affiche aussi le résumé des `actions`.
## [2.8.3] — 2026-11-10

### Corrigé
- **Navigation des applis enfin fonctionnelle** : le mot-clé `items` manquait dans la commande CLI (`radioparadise 0 100` au lieu de `radioparadise items 0 100`) — commande invalide, le serveur fermait la connexion. Il est désormais ajouté automatiquement (sans doublon si le menu du plugin le contient déjà), en like du correctif `favorites playlist play` v2.4.5.
## [2.8.2] — 2026-11-10

### Corrigé
- **Navigation dans les applis (Qobuz, Radio Paradise)** : le délai des requêtes passe à 10 s (les plugins interrogent parfois des API distantes), les `params` renvoyés par la découverte sont transmis puis réessayés sans, et si un niveau reste vide la console affiche `[lms] diagnostic navigation — commande -> réponse brute` à copier dans une issue.

### Modifié
- **Pages LMS retirées du carrousel** (et du knob 2 / swipe) : elles restent accessibles par la touche « LMS » de l'accueil et leur navigation interne.
## [2.8.1] — 2026-11-10

### Corrigé
- **Page « Applis » vide sur certains serveurs** : la découverte interroge désormais « apps » **puis** « radios » (où certaines versions rangent Radio Paradise), **avec un lecteur puis sans** (certaines versions exigent un contexte lecteur), accepte toute clé de boucle `*_loop` et les champs `go`/`title` en repli. Si rien n'est trouvé, la console affiche une ligne de diagnostic `[lms] diagnostic apps — réponse brute : …` à copier dans une issue.

## [2.8.0] — 2026-11-10

### Ajouté
- **Page « Applis » dynamique** : l'application découvre les applis installées sur le serveur LMS (Qobuz, Radio Paradise…) et en affiche jusqu'à 9 (knob 3 pour faire défiler). Plus besoin de boutons statiques.
- **Navigateur d'applis générique** : ouvrir une appli liste ses éléments (Favoris Qobuz, mixes Radio Paradise…) ; un clic sur un dossier le parcourt, un clic sur un morceau/flux le joue sur le lecteur affiché — retour (touche 10 ou knob 3 appuyé) pour remonter d'un niveau, puis revenir aux applis.
- **Lecture LMS des applis** : lecture via `playlist play` (allume le lecteur), avec diagnostic console `[lms] élément non jouable — …` si le serveur renvoie un format imprévu.

### Modifié
- L'ancien bouton « Qobuz » (touches média du PC) quitte la page LMS Applis — la page Qobuz reste disponible dans la config pour le PC.
## [2.7.3] — 2026-11-10

### Modifié
- **Radios : retour de l'icône radio stylisée** au-dessus des touches radios de la page Favoris (le cœur reste réservé au bouton « Favoris » et à la pilule de page).

## [2.7.2] — 2026-11-10

### Modifié
- **Cœur pour les favoris** : les touches radios des pages Favoris arborent désormais l'icône « favorite » (petit cœur), le bouton « Favoris » aussi, et la pilule de page passe de l'étoile au cœur.
- **Bouton « Applis »** : logo « grid_view » (grille fine), dans le bleu de la page.
- **Boutons « Retour » unifiés** : flèche courbée « undo » stylisée en blanc sur fond noir sur toutes les pages LMS (lecteur, favoris, applis).

## [2.7.1] — 2026-11-10

### Modifié
- **Logos de lecteurs distinctifs** : les Squeezebox Touch affichent une icône « tablet » (tablette tactile — le plus proche d'un Touch), les Squeezebox Radio l'icône « radio », les autres lecteurs restent « speaker ». Distinction immédiate sur la page des lecteurs et la touche d'identification.

## [2.7.0] — 2026-11-10

### Ajouté
- **Touche « LMS » sur l'accueil** : ajoutée automatiquement au premier emplacement libre de la page d'accueil quand LMS est configuré — plus besoin de naviguer au knob 2 pour atteindre la page LMS. Message explicatif dans la console si l'accueil est complet.
- **Petits logos d'action sur les touches LMS** (icônes Material, affichées en haut de la touche) : haut-parleur (lecteurs), alimentation, lecture ▶ / pause ⏸ selon l'état réel du lecteur, radio (favoris), synchronisation, échange de lecteur…
- **Noms de lecteurs « Touch » conservés** : « Squeezebox Touch Salon » → « Touch Salon » (comme « Radio ») — plus compact, toujours identifiable.

### Modifié
- **Polices harmonisées** : la même police partout sur les touches — la petite (20 px), la seule qui tient entière dans les 112 px des petits écrans ; les noms longs restent coupés sur deux lignes équilibrées.

## [2.6.1] — 2026-11-10

### Corrigé
- **Radio active toujours pas surlignée au démarrage chez certains serveurs** : la détection lit désormais tous les champs du `status` LMS (`url`, `title` de `playlist_loop`, `current_title`, y compris au niveau racine — selon la version du serveur, l'un ou l'autre est renseigné).
- **Diagnostic** : si le lecteur joue mais qu'aucun favori ne correspond, la console affiche une fois `[lms] diagnostic radio active — station=…, titre=…, url=…` avec les URL des favoris, à copier dans une issue.

## [2.6.0] — 2026-11-10

### Ajouté
- **Dégradés sur toutes les couleurs d'état LMS** : lecteurs allumés en dégradé vert → noir (page des lecteurs et touche d'identification), radios actives en dégradé bleu → noir.

### Corrigé
- **Radio active non surlignée en arrivant sur la page Favoris** : l'application récupère désormais aussi le **nom de station** du `status` LMS (`title` de `playlist_loop`), plus fiable que le `current_title` (métadonnée du morceau) ; la query string des URLs est ignorée pour la comparaison (ex. `?_=123`).

## [2.5.2] — 2026-11-10

### Modifié
- **Surlignage de la radio active dès le démarrage** : l'URL du flux en cours (requête `status` LMS) est comparée à l'URL des favoris — la radio déjà en lecture quand l'application démarre est reconnue sans avoir à la relancer.
- **Dégradé bleu → noir** : le fond de la touche de la radio active passe d'un bleu soutenu (haut) au noir (bas), au lieu du bleu plein trop vif.

## [2.5.1] — 2026-11-10

### Modifié
- **Surlignage de la radio active plus visible** : fond **bleu vif** (texte blanc) au lieu du vert Lyrion trop sombre.
- **Détection fiable** : le `current_title` d'une webradio est souvent la métadonnée du morceau en cours (pas le nom de la station), ce qui empêchait le surlignage. L'application mémorise désormais la dernière radio lancée depuis le deck pour chaque lecteur ; le titre en cours reste prioritaire s'il désigne une autre station (changement depuis l'interface web LMS).

## [2.5.0] — 2026-11-10

### Ajouté
- **Radio active surlignée en vert** : sur la page Favoris, la radio en cours de lecture sur le lecteur affiché passe en fond vert Lyrion (même code couleur que les lecteurs allumés) avec le sous-titre « >> en cours ». Détection robuste du titre en cours (noms normalisés — « FIP Rock (MP3) » ≈ « FIP Rock » —, le nom le plus long gagne pour ne pas confondre FIP et FIP Rock).

## [2.4.6] — 2026-11-10

### Corrigé
- **Tous les favoris lançaient la même radio** : l'identifiant doit être passé avec le préfixe `item_id:` (`favorites playlist play item_id:<id>`). Sans ce préfixe, LMS ignore l'identifiant et joue le premier favori de la liste.

## [2.4.5] — 2026-11-10

### Corrigé
- **Les radios des favoris ne se lançaient pas** (« requête échouée : Remote end closed connection without response ») : la commande CLI envoyée était `favorites play <id>`, qui n'existe pas dans l'API LMS. La commande correcte est `favorites playlist play <id>`.

## [2.4.4] — 2026-11-10

### Corrigé
- **Favoris introuvables sur certains serveurs LMS** : certaines versions du serveur renvoient les favoris dans la clé `loop_loop` au lieu de `favorites_loop`. Ce format est désormais reconnu (également `itemLoop` et `items`) — les radios (FIP, FIP Rock…) apparaissent enfin dans la page Favoris.

## [2.4.3] — 2026-11-10

### Corrigé
- **Console inondée par le diagnostic favoris** : tant que la liste des favoris restait vide, le message de diagnostic (réponse brute du serveur) et l'avertissement « dossier de favoris introuvable » étaient réimprimés à chaque cycle de rafraîchissement (toutes les 2 s). Ces messages ne s'affichent désormais plus qu'une seule fois.

## [2.4.2] — 2026-11-10

### Ajouté
- **Radios manuelles dans la config** : `"lms": {"radios": [{"name": "FIP", "url": "http://…"}]}` — liste affichée en tête de la page Favoris (dédupliquée avec les favoris découverts). Débloque la page Favoris même si le serveur ne renvoie pas ses favoris ; les entrées manuelles sont jouées par URL directe.
- **Diagnostic favoris** : si aucun favori exploitable n'est trouvé, la console affiche la réponse brute de LMS (`[lms] diagnostic — réponse favorites items : …`) à copier dans une issue pour comprendre la structure du serveur.

## [2.4.1] — 2026-11-10

### Corrigé
- **Volume % du lecteur sur le bandeau tactile (zone 1)** : la requête « players » de LMS ne renvoie PAS « mixer volume » — le pourcentage restait à 0 alors que le knob fonctionnait. Le volume est désormais interrogé explicitement (« mixer volume ? ») pour le lecteur affiché.
- **Noms des Squeezebox et des radios tronqués** : les touches LMS utilisent une police plus petite et coupent les noms longs sur deux lignes — tout s'affiche en entier.

### Ajouté
- **Favoris robustes** : dossier insensible à la casse, repli automatique sur l'arborescence imbriquée (feedMode) si le serveur ne renvoie pas la liste plate, message explicite dans la console (favoris trouvés, ou dossiers disponibles si le dossier configuré est introuvable — l'arbre complet est alors utilisé).

## [2.4.0] — 2026-11-10

### Modifié
- **Page LMS repensée : un bouton par Squeezebox.** Fini le bouton « Veille » qui allumait/éteignait TOUS les lecteurs d'un coup : la page « lms » affiche désormais **6 boutons = 6 lecteurs** (nom raccourci automatiquement — « Squeezebox Touch Orange » → « Orange », fond vert Lyrion si allumé, titre en cours affiché) ; un appui ouvre la page du lecteur.

### Ajouté
- **Page lecteur (lms_player)** : identification (nom en couleur, vert Lyrion si allumé), alim on/off de ce lecteur SEUL, lecture/pause avec le titre en cours, favoris, mes applis, retour LMS. Knob 1 = volume de ce lecteur (appui = muet) ; la zone 1 du bandeau tactile affiche son volume % en temps réel.
- **Page favoris (lms_favs)** : 9 touches de favoris radios du lecteur (indicateur « >> en cours »), knob 3 = défilement au-delà de 9 favoris, appui knob 3 ou touche 10 = retour.
- **Page applis (lms_apps)** : Qobuz (page média) + Radio Paradise (flux joué sur le lecteur courant, URL configurable via \"lms\": {\"radio_paradise_url\": …}).
- Les pages LMS sont désormais **générées par l'application** : une ancienne définition \"pages.lms\" dans akp05e_config.json est ignorée (aucune édition de config nécessaire). Les actions v2.3 (lms_power_all, lms_select_player, lms_favorite…) restent reconnues pour compatibilité.

## [2.3.1] — 2026-11-10

### Corrigé
- **Radios des touches LMS : les dossiers de favoris sont désormais parcourus** (récursivement, via `favorites items … item_id:<id>` — les favoris LMS utilisent des ids hiérarchiques). Avant, seuls les favoris de premier niveau apparaissaient : les radios rangées dans un dossier donnaient des touches « (vide) ».

### Ajouté
- Option `"folder": "Nom du dossier"` dans la clé `"lms"` de la config : limite les touches Radio au contenu de ce dossier de favoris précis (sinon tout l'arbre est aplati, dossiers compris).

## [2.3.0] — 2026-11-10

### Ajouté
- **Intégration Lyrion Media Server (LMS / Squeezebox)** : nouvelle page « LMS » pilotant tous les Squeezebox de la maison (3 Touch + 3 Radio). Clé de config `"lms": {"host": "…", "port": 9000}` (hôte vide = désactivé) — lecteurs et favoris radios découverts automatiquement via l'API JSON-RPC de LMS, en stdlib (urllib), zéro dépendance. Boutons : « Veille » (tout allumer/éteindre, affiche « X/Y allumés »), « Lecteur » (nom du lecteur sélectionné), « Lecture » (pause/reprise, affiche le morceau en cours), « Maison » (synchronise tous les lecteurs sur le sélectionné / dissocie), touches 5-10 : **6 radios des favoris LMS** (nom automatique, indicateur « en cours »). Knob 1 = volume du lecteur sélectionné (appui = muet), knob 3 = changer de lecteur (appui = allumer/éteindre). Rafraîchissement automatique toutes les 2 s ; LMS injoignable = touches « LMS ? » sans plantage. Nouvelles actions : `lms_power_all`, `lms_power_selected`, `lms_select_player`, `lms_playpause`, `lms_volume`, `lms_mute`, `lms_sync`, `lms_favorite`.

## [2.2.0] — 2026-11-09

### Ajouté
- **Changement de page automatique selon l'application active** : la clé `"auto_pages"` de la config associe un nom de processus (fenêtre au premier plan, comparaison partielle sans casse) à une page. Par défaut : Qobuz/Spotify/VLC → page « Qobuz », HWiNFO64 → page « hardware ». Le deck revient à la page précédente quand on quitte l'application ; une navigation manuelle (knob 2) pendant qu'elle est active est respectée jusqu'au prochain changement d'application. Clé absente ou vide = fonction désactivée. Détection stdlib (ctypes), sans dépendance.

## [2.1.1] — 2026-11-09

### Modifié
- **Le chronomètre déménage dans la page « minuteurs »** : touche « Chrono » (libellé violet, sous-titre « chrono ») — plus de page « chronos » séparée, pour garder le carrousel des pages léger. L'action `{"type": "stopwatch"}` reste utilisable sur n'importe quelle page.

## [2.1.0] — 2026-11-09

### Ajouté
- **Minuteur réglable (page « minuteurs »)** : nouvelle touche « Régl. » — le **knob 3** ajuste la durée de **1 à 99 min** (le libellé de la touche suit en direct), et un **appui sur le knob 3 démarre** le minuteur réglable immédiatement. Config : action `{"type": "timer", "minutes": 0}` + `timer_adjust` / `timer_start` sur les encodeurs.
- **Page « chronos »** : chronomètre — clic court = départ / pause / reprise, **clic long (> 0,6 s) = remise à zéro**, temps écoulé mm:ss en temps réel sur la touche (gris = prêt, vert = en cours, ambre = pause). Nouvelle action `{"type": "stopwatch"}`. Le chronomètre continue même si on change de page (comme le minuteur).

## [2.0.2] — 2026-11-09

### Modifié
- **Luminosité par défaut à 30 %** au démarrage (au lieu de 60 %) : `DEFAULT_BRIGHTNESS = 30` et `"brightness": 30` dans la config par défaut. Un `akp05e_config.json` existant conserve sa valeur ; mets `"brightness": 30` dedans (ou supprime-le pour le régénérer) pour appliquer le nouveau défaut. Le knob 4 règle toujours la luminosité à la volée.

## [2.0.1] — 2026-11-09

### Corrigé
- **Appui long sur un minuteur : ne relance plus jamais le minuteur.** Le deck peut renvoyer des événements « appui » répétés pendant un appui maintenu : chacun écrasait l'instant initial d'appui, si bien qu'au relâchement la durée paraissait courte (< 0,6 s) et la branche « reprise » redémarrait le minuteur juste après la réinitialisation. L'instant d'appui d'origine est désormais conservé et le clic long remet complètement le minuteur à l'état « préréglage » (touche grise, pas de décompte).

### Modifié
- **Alarme de fin de minuteur plus douce** : carillon descendant Sol 5 → Do 5 (plus grave), 3 répétitions bien espacées — au lieu de bips aigus en rafale.

## [2.0.0] — 2026-11-09

### Ajouté
- **Page « minuteurs »** : préréglages 1/2/5/10/20/30 min, un minuteur actif à la fois (démarrer un autre minuteur remplace l'actif). Clic court = départ / pause / reprise (ou acquitte l'alarme), **clic long (> 0,6 s) = réinitialise**. Affichage du temps restant en temps réel sur la touche : préréglage gris, vert = en cours, ambre = pause, rouge clignotant = fini. **Alarme sonore** à la fin (bips winsound) + clignotement ; le minuteur poursuit même si on change de page. Nouvelle action `{"type": "timer", "minutes": N}`.

### Modifié
- **Page accueil** : les touches « Copie » (texte) et « Mute » sont retirées ; nouvelle touche « Minut. » (icône timer) vers la page « minuteurs ». Le mute reste accessible sur le knob 1 (appui) et la page Qobuz.

## [1.9.0] — 2026-11-09

### Ajouté
- **Zoom universel sur le knob 3** (défaut global) : rotation = Ctrl+molette dans la fenêtre active (navigateurs, Office, PDF…), CW = grossir, CCW = réduire, appui = Ctrl+0 (zoom 100 %). Implémenté par un envoi souris SendInput (structure `INPUT_MOUSE` à empreinte identique au clavier, 40 octets x64) avec Ctrl maintenu. Nouvelle action `{"type": "zoom", "dir": "in"|"out"|"reset"}` — le knob 3 reste surclassable par page via `"encoders"` (sans action configurée, le zoom s'applique partout).

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

[2.14.8]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.14.9]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.15.0]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.15.1]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.17.0]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.17.1]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.18.0]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.19.9]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.19.10]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.19.11]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.19.8]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.19.7]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.19.6]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.19.5]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.19.4]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.19.3]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.19.2]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.19.1]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.19.0]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.18.4]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.18.3]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.18.2]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.18.1]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.16.3]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.16.4]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.16.0]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.16.1]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.16.2]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.0.0]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.0.1]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.0.2]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.1.0]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.1.1]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.2.0]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.3.0]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.8.4]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.8.6]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.8.7]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.9.0]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.9.1]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.9.2]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.14.7]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.14.6]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.14.5]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.14.4]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.14.3]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.14.2]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.14.1]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.14.0]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.13.9]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.13.8]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.13.7]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.13.6]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.13.5]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.13.4]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.13.3]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.13.2]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.13.1]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.13.0]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.12.3]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.12.2]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.12.1]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.12.0]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.11.0]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.10.4]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.10.3]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.10.2]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.10.1]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.10.0]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.9.3]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.8.5]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.8.3]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.8.2]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.8.1]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.8.0]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.7.3]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.7.2]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.7.1]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.7.0]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.6.1]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.6.0]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.5.2]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.5.1]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.5.0]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.4.6]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.4.5]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.4.4]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.4.3]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.4.2]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.4.1]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.4.0]: https://github.com/dalbertini/akp05e-interface/commits/main/
[2.3.1]: https://github.com/dalbertini/akp05e-interface/commits/main/
[1.9.0]: https://github.com/dalbertini/akp05e-interface/commits/main/
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
