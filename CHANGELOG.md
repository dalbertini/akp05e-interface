# Changelog

Historique des versions de l'application. Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/),
numérotation [SemVer](https://semver.org/lang/fr/) : **MAJEURE**.**FONCTIONNALITÉ**.**CORRECTIF**.

## [2.13.2] — 2026-11-11

### Corrigé
- **Page « album » : détection et lecture enfin fonctionnelles avec les feeds sans URL (Qobuz)** — le serveur ne renvoie pas l'URL de lecture des morceaux par défaut : la navigation envoie désormais `want_url:1` (mécanisme xmlbrowser standard de LMS), ce qui fournit l'URL réelle de chaque morceau (`playlist play <url>`).
- **Un item drillable (`hasitems`) n'est plus joué en direct** même s'il possède une URL — sinon le clic sur un album l'aurait lu sans jamais ouvrir la page « album ».
- **Nouvelle « feuille » de menu jouable** : un item dont le sous-niveau est vide mais qui possède une URL de lecture est joué directement (utile pour les morceaux `hasitems` des feeds Qobuz).
- Refactor : les branches cmd/item_id de la navigation partagent `lms_open_level()` (page album / lecture feuille / navigation + diagnostic).

## [2.13.3] — 2026-11-11

### Corrigé
- **Page « album » : feeds Qobuz où chaque morceau est un répertoire** — certains feeds renvoient des morceaux `hasitems` SANS URL, l'URL de lecture étant un cran plus bas (dans un sous-niveau contenant exactement 1 item jouable). La navigation sonde désormais le premier morceau : si son sous-niveau est un morceau jouable, les URLs de TOUS les morceaux sont résolues (une requête chacune) et la page « album » complète s'ouvre. Une liste d'albums (sous-niveau de plusieurs éléments) échoue à la sonde et reste en navigation normale.
- Journaux : `[lms] album « … » : N morceaux (URLs résolues un par un)`, et un message explicite si la résolution échoue en cours de route.

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
 https://github.com/dalbertini/akp05e-interface/commits/main/
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
