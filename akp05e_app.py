#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AKP05E Deck — application de contrôle open source pour l'Ajazz AKP05E / AKP05
(VID 0x0300 / PID 0x3004) sous Windows.

Licence MIT. Aucun logiciel propriétaire requis : uniquement `pywinusb`
(HID natif Windows) et `Pillow` (génération des icônes JPEG).

    pip install pywinusb pillow pycaw

Au premier lancement, un fichier `akp05e_config.json` est créé à côté du
script : édite-le pour associer des actions aux touches et aux encodeurs,
puis relance l'application.

Icônes : chaque touche accepte soit un nom d'icône Material Icons
(~2500 noms, https://fonts.google.com/icons), soit le chemin d'une image
perso. Couleurs : formats CSS acceptés ("#4CAF50", "red", "rgb(10,20,30)")
pour l'icône ("color") et le fond de touche ("bg"). La police d'icônes
est téléchargée au premier usage puis mise en cache (`.icons_cache/`) —
ensuite tout fonctionne hors ligne.

Protocole rétro-ingénieré, croisé avec mirajazz (Rust), opendeck-akp05
(plugin OpenDeck) et zeccola/ajazz-akp05 (Python) — confirmé sur matériel réel :
  - HID vendor-defined (usage page 0xFFA0), paquets de 1024 octets,
    commandes cadrées [0x00, 'C','R','T', 0,0, <CMD>, payload...].
  - Touches LCD 1..10 : images JPEG 112x112 pivotées de 180°.
    (numérotation "wire-key" différente de la numérotation des pressions :
     rangée du haut 1-5 -> wire-keys 11-15, rangée du bas 6-10 -> 6-10.)
  - Encodeurs : press 0x37/0x35/0x33/0x36, twist CW/CCW 0xA1/0xA0,
    0x51/0x50, 0x91/0x90, 0x71/0x70.
  - Keepalive "CONNECT" toutes les 10 s obligatoire (sinon le deck se
    déconnecte au bout de ~15 s).

Types d'actions configurables dans akp05e_config.json :
  {"type": "open",    "path": "C:\\Program Files\\...\\app.exe"}
  {"type": "url",     "url": "https://github.com"}
  {"type": "keys",    "keys": ["ctrl", "shift", "esc"]}   # frappe de raccourci
  {"type": "text",    "text": "Bonjour !"}                # texte tapé
  {"type": "run",     "cmd": "notepad", "args": []}
  {"type": "volume",  "dir": "up"}                        # touche média
  {"type": "sysvolume", "dir": "up", "step": 5}           # volume système réel
  {"type": "mediaplay"} {"type": "medianext"} {"type": "mediaprev"} {"type": "mediastop"}
  {"type": "brightness", "dir": "up"}                     # luminosité du deck
  {"type": "brightness_toggle"}                            # knob 4 : on/off
  {"type": "sleep"}                                        # mise en veille : écrans éteints,
                                                           # n'importe quel événement réveille
  {"type": "zoom", "dir": "in"}                            # Ctrl+molette ("out"/"reset"=Ctrl+0)
  {"type": "timer", "minutes": 5}                          # minuteur : clic = départ/pause/reprise,
                                                           # clic long = réinitialise, alarme à la fin
                                                           # ("minutes": 0 = durée réglable, knob 3)
  {"type": "stopwatch"}                                    # chronomètre : clic = départ/pause/reprise,
                                                           # clic long = remise à zéro
  {"type": "timer_adjust", "dir": "up"}                    # knob 3 : durée réglable +1 min ("down" = -1)
  {"type": "timer_start"}                                  # knob 3 appuyé : démarre le minuteur réglable
  {"type": "lms_power_all"}                                 # LMS : allume/éteint TOUS les Squeezebox
  {"type": "lms_power_selected"}                             # LMS : allume/éteint le lecteur sélectionné
  {"type": "lms_select_player"}                              # LMS : change de lecteur ("dir": "prev")
  {"type": "lms_playpause"}                                 # LMS : pause / reprise du lecteur sélectionné
  {"type": "lms_volume", "dir": "up", "step": 5}             # LMS : volume du lecteur sélectionné
  {"type": "lms_mute"}                                       # LMS : muet du lecteur sélectionné
  {"type": "lms_sync"}                                      # LMS : synchronise tous les lecteurs (ou dissocie)
  {"type": "lms_favorite", "index": 0}                       # LMS : joue le favori n°0 (radios)
  {"type": "page", "page": "qobuz"}                         # changer de page
  {"type": "page", "page": "next"}                          # ou "prev" : défiler
(Par défaut, le knob 2 fait défiler les pages : CW = suivante, CCW = précédente.
Le knob 3, s'il n'a pas d'action configurée, fait le ZOOM Ctrl+molette :
CW = grossir, CCW = réduire, appui = Ctrl+0 — dans la fenêtre active.)
PAGES DE PROFILS : la config classique ("buttons"/"encoders") forme la page
"accueil". Des pages supplémentaires se définissent dans la clé "pages" :
  {"pages": {"qobuz": {"label": "Qobuz", "buttons": {...}, "encoders": {...}}}}
Chaque page a ses touches et encodeurs propres ; la zone 2 du bandeau affiche
le nom de la page courante. Bascule via l'action {"type": "page", ...}.
CHANGEMENT DE PAGE AUTOMATIQUE : la clé "auto_pages" associe un nom de
processus (fenêtre au premier plan, comparaison partielle, sans casse) à
une page. Ex. {"qobuz": "qobuz", "spotify": "qobuz"} : mettre Qobuz ou
Spotify au premier plan bascule le deck sur la page "qobuz", et il revient
à la page précédente quand on la quitte. Une navigation manuelle (knob 2)
pendant que l'application est active est respectée jusqu'au prochain
changement d'application. Clé absente ou vide = fonction désactivée.
INTÉGRATION LYRION MEDIA SERVER (LMS / Squeezebox) : la clé "lms"
({"host": "192.168.1.24", "port": 9000}) active les pages « lms » :
  • page « lms » : 6 boutons = 6 lecteurs, appui = ouvrir la page du
    lecteur (nom raccourci, fond vert Lyrion si allumé) ;
  • page « lms_player » (par lecteur) : identification (nom en couleur,
    logo Lyrion), alim on/off individuel, lecture/pause + titre en cours,
    favoris, mes applis, retour LMS ; knob 1 = volume de CE lecteur
    (appui = muet) ; la zone 1 du bandeau tactile affiche son volume % ;
  • page « lms_favs » : favoris radios de ce lecteur (knob 3 = défilement,
    appui = retour ; touche 10 = retour) ;
  • page « lms_apps » : Qobuz + Radio Paradise (URL configurable via
    "lms": {"radio_paradise_url": ...}).
Option "folder": "Radios" limite les favoris au contenu de ce dossier
(sinon tout l'arbre est aplati, dossiers compris). Option "radios" :
liste MANUELLE de webradios, affichée avant les favoris découverts (utile
si le serveur ne renvoie pas ses favoris) :
  "lms": {"host": "...", "radios": [{"name": "FIP",
                                     "url": "http://fip.fr/fip.aac"}]}
API JSON-RPC de LMS, stdlib uniquement — hôte vide = désactivé.
CONFIGURATION ASSISTÉE : `python akp05e_app.py --setup-lms` détecte
automatiquement le serveur Lyrion sur le réseau local (découverte
Squeezebox : broadcast UDP 3483), vérifie la connexion et enregistre
son adresse dans akp05e_config.json — l'application démarre ensuite
normalement avec la nouvelle configuration.
Une page supplémentaire est fournie par défaut : "qobuz" (play/stop/suiv./
prec./mute + retour accueil), pilotée par les touches média système (SMTC) —
fonctionne avec Qobuz, Spotify, VLC, etc.
Les pages « raccourcis » (copier/coller/couper, Ctrl+A/B/I/U/Z, Impr. écran,
Échap), « hardware » (températures HWiNFO64) et « minuteurs » (préréglages
1/2/5/10/20/30 min + durée réglable au knob 3, alarme + touche « Chrono »
chronomètre : clic = départ/pause/reprise, clic long = remise à zéro)
sont aussi fournies par défaut.
Le knob 4 pilote la luminosité des écrans (rotation = réglage par pas,
appui = extinction/rallumage) et le knob 1 règle le VOLUME SYSTÈME Windows
(pycaw : niveau réel, appui = muet). Le bandeau tactile affiche les deux
en temps réel ("Vol 42%" et "Lum 60%" + barres), et se met à jour même si
le volume est changé depuis Windows (barre des tâches, clavier).
La zone 3 du bandeau affiche un VU-MÈTRE temps réel (niveau de crête du
son système via WASAPI/pycaw, marqueur de crête qui retombe lentement) —
désactivable via {"vu_meter": {"enabled": false}} dans la config."""

import json
import os
import queue
import re
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from collections import namedtuple

import pywinusb.hid as hid
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Volume système Windows (pycaw) : niveau réel, pas une simple touche média.
# Si pycaw est absent, l'action "sysvolume" retombe sur les touches média.
# ---------------------------------------------------------------------------
try:
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import (AudioUtilities, IAudioEndpointVolume,
                            IAudioMeterInformation)
    _HAS_PYCAW = True
    _PYCAW_IMPORT_ERR = None
except ImportError as e:
    _HAS_PYCAW = False
    _PYCAW_IMPORT_ERR = str(e)

def _com_init():
    """Initialise COM dans le thread appelant (indispensable : le polling
    de volume et les actions tournent dans des threads où COM n'est PAS
    initialisé automatiquement — sinon chaque appel échoue en silence)."""
    try:
        import comtypes
        comtypes.CoInitialize()
    except Exception:
        pass

_endpoint_vol = None
_endpoint_lock = threading.Lock()

def _get_endpoint():
    """Interface IAudioEndpointVolume du périphérique de sortie par défaut.
    Gère les DEUX générations de l'API pycaw :
      - ancienne (< 20240210) : AudioDevice a une méthode .Activate(...)
      - nouvelle (>= 20240210) : AudioDevice expose .EndpointVolume directement
    """
    global _endpoint_vol
    with _endpoint_lock:
        if _endpoint_vol is None:
            device = AudioUtilities.GetSpeakers()
            if hasattr(device, "Activate"):
                interface = device.Activate(IAudioEndpointVolume._iid_,
                                           CLSCTX_ALL, None)
                _endpoint_vol = interface.QueryInterface(IAudioEndpointVolume)
            else:
                _endpoint_vol = device.EndpointVolume
        return _endpoint_vol

def get_volume_pct():
    """Volume principal système, en pourcentage (0-100)."""
    _com_init()
    return int(round(_get_endpoint().GetMasterVolumeLevelScalar() * 100))

def set_volume_pct(pct):
    _com_init()
    _get_endpoint().SetMasterVolumeLevelScalar(
        max(0, min(100, pct)) / 100.0, None)

def get_mute():
    _com_init()
    return bool(_get_endpoint().GetMute())

def set_mute(muted):
    _get_endpoint().SetMute(bool(muted), None)

# --- VU-mètre : peak meter WASAPI (pycaw) ---------------------------------
_meter = None

def _get_meter():
    """Interface IAudioMeterInformation du périphérique de sortie par
    défaut (peak meter WASAPI). Gère les DEUX générations de pycaw :
      - ancienne : AudioDevice expose .Activate(...)
      - nouvelle (>= 2025) : l'IMMDevice brut est dans device._dev
    """
    global _meter
    with _endpoint_lock:
        if _meter is None:
            device = AudioUtilities.GetSpeakers()
            if hasattr(device, "Activate"):
                itf = device.Activate(IAudioMeterInformation._iid_,
                                      CLSCTX_ALL, None)
            else:
                imm = getattr(device, "_dev", None)
                if imm is None:
                    return None
                itf = imm.Activate(IAudioMeterInformation._iid_,
                                   CLSCTX_ALL, None)
            _meter = itf.QueryInterface(IAudioMeterInformation)
        return _meter

def vu_get_peak():
    """Niveau de crête instantané du son du système, entre 0.0 et 1.0.
    Retourne None si l'interface est indisponible."""
    _com_init()
    meter = _get_meter()
    if meter is None:
        return None
    peak = meter.GetPeakValue()
    if isinstance(peak, (int, float)):
        return max(0.0, min(1.0, float(peak)))
    return None

# ---------------------------------------------------------------------------
# HWiNFO64 (licence Pro) : températures et capteurs via la mémoire partagée.
# Activer « Shared Memory Support » dans les réglages HWiNFO ; liste des
# mesures disponibles : python akp05e_app.py --list-sensors
# ---------------------------------------------------------------------------
HWINFO_MAP_NAME = "Global\\HWiNFO_SENS_SM2"
HWINFO_MUTEX_NAME = "Global\\HWiNFO_SM2_MUTEX"
HWINFO_TYPES = {1: "temp", 2: "volt", 3: "fan", 4: "current", 5: "power",
               6: "clock", 7: "usage", 8: "other"}

def _read_cstr(buf):
    """Chaîne ANSI terminée par NUL -> str lisible."""
    return buf.split(b"\x00")[0].decode("cp1252", "replace").strip()

def hwinfo_readings():
    """Lit la mémoire partagée HWiNFO64. Retourne None si HWiNFO est absent
    ou si « Shared Memory Support » est désactivé, sinon la liste des mesures :
    sensor, label, type, unit, value, min, max, avg."""
    import ctypes
    import struct as _struct
    k32 = ctypes.windll.kernel32
    FILE_MAP_READ = 0x0004
    # Prototypes WinAPI STRICTS : sans eux, ctypes tronque les handles et
    # pointeurs 64 bits en int 32 bits (restype par défaut) — sous Windows
    # x64, MapViewOfFile retourne une adresse > 4 Go et chaque lecture
    # déclenche une "access violation". Indispensable !
    from ctypes import wintypes as _wt
    k32.OpenFileMappingW.restype = ctypes.c_void_p
    k32.OpenFileMappingW.argtypes = [ctypes.c_uint32, _wt.BOOL, _wt.LPCWSTR]
    k32.CreateMutexW.restype = ctypes.c_void_p
    k32.CreateMutexW.argtypes = [ctypes.c_void_p, _wt.BOOL, _wt.LPCWSTR]
    k32.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    k32.ReleaseMutex.argtypes = [ctypes.c_void_p]
    k32.MapViewOfFile.restype = ctypes.c_void_p
    k32.MapViewOfFile.argtypes = [ctypes.c_void_p, ctypes.c_uint32,
                                   ctypes.c_uint32, ctypes.c_uint32,
                                   ctypes.c_size_t]
    k32.UnmapViewOfFile.argtypes = [ctypes.c_void_p]
    k32.CloseHandle.argtypes = [ctypes.c_void_p]
    hmap = k32.OpenFileMappingW(FILE_MAP_READ, False, HWINFO_MAP_NAME)
    if not hmap:
        return None
    hmut = k32.CreateMutexW(None, False, HWINFO_MUTEX_NAME)
    locked = hmut and k32.WaitForSingleObject(hmut, 200) == 0
    base = 0
    try:
        base = k32.MapViewOfFile(hmap, FILE_MAP_READ, 0, 0, 0)
        if not base:
            return None
        head = ctypes.string_at(base, 44)
        (_sig, _ver, _rev, _poll, off_sens, size_sens, n_sens,
         off_read, size_read, n_read) = _struct.unpack("<IIIqIIIIII", head)
        # Garde-fous : signature "HWiS" (0x53695748, 'DEAD' si inactif) et
        # dimensions plausibles — on ne tente AUCUNE lecture dans une
        # mémoire dont la description ne colle pas au format documenté.
        if _sig != 0x53695748:  # "HWiS" ; 'DEAD' quand HWiNFO est inactif
            return None
        if (not 0 < size_sens <= 512 or not 0 < size_read <= 1024
                or n_sens > 4096 or n_read > 65536
                or off_sens + n_sens * size_sens > 0x40000000
                or off_read + n_read * size_read > 0x40000000):
            return None
        sensors = []
        for i in range(n_sens):
            el = ctypes.string_at(base + off_sens + i * size_sens, size_sens)
            name_u = _read_cstr(el[136:136 + 128])
            sensors.append(name_u or _read_cstr(el[8:8 + 128]))
        out = []
        for i in range(n_read):
            el = ctypes.string_at(base + off_read + i * size_read, size_read)
            # HWiNFO_SENSORS_READING_ELEMENT est #pragma pack(1) :
            # type(4) idx(4) id(4) | label_orig[128] @12 | label_user[128]
            # @140 | unit[16] @268 | Value/Min/Max/Avg (double) @284.
            rtype, sidx, rid = _struct.unpack_from("<III", el, 0)
            label_o = _read_cstr(el[12:12 + 128])
            label_u = _read_cstr(el[140:140 + 128])
            unit = _read_cstr(el[268:268 + 16])
            value, vmin, vmax, vavg = _struct.unpack_from("<dddd", el, 284)
            sname = sensors[sidx] if 0 <= sidx < len(sensors) else "?"
            out.append({"sensor": sname, "label": label_u or label_o,
                        "label_orig": label_o, "type": rtype, "unit": unit,
                        "value": value, "min": vmin, "max": vmax, "avg": vavg})
        return out
    finally:
        if base:
            k32.UnmapViewOfFile(base)
        if locked:
            k32.ReleaseMutex(hmut)
        if hmut:
            k32.CloseHandle(hmut)
        k32.CloseHandle(hmap)

def hw_match(readings, needle):
    """Cherche la mesure correspondant au motif : soit une sous-chaîne,
    soit une LISTE de sous-chaînes (toutes doivent alors correspondre —
    ex. ["C:]", "Drive Temperature"] pour la température du disque C:).
    Recherche insensible à la casse sur libellé + libellé d'origine +
    nom de capteur. Parmi les correspondances, privilégie une température
    (c'est le but des touches capteurs), puis le libellé le plus court."""
    if not readings or not needle:
        return None
    needles = needle if isinstance(needle, list) else [needle]
    needles = [str(n).lower().strip() for n in needles if str(n).strip()]
    if not needles:
        return None
    cands = []
    for r in readings:
        hay = (r["label"] + " " + r["label_orig"]
               + " " + r["sensor"]).lower()
        if all(n in hay for n in needles):
            cands.append(r)
    if not cands:
        return None
    # température d'abord (type 1), puis libellé le plus court
    cands.sort(key=lambda r: (r["type"] != 1, len(r["label"])))
    return cands[0]

def run_list_sensors():
    """Mode --list-sensors : affiche toutes les mesures HWiNFO disponibles."""
    print("Lecture de la mémoire partagée HWiNFO64…")
    readings = hwinfo_readings()
    if readings is None:
        print("Mémoire partagée introuvable. Vérifie :")
        print("  - HWiNFO64 est lancé et les capteurs sont actifs (fenêtre Sensors)")
        print('  - Settings → "Shared Memory Support" est activé')
        print("  - l\'application est lancée avec les mêmes droits qu\'HWiNFO")
        return
    if not readings:
        print("Aucune mesure publiée par HWiNFO.")
        return
    print(f"{len(readings)} mesures disponibles :\n")
    for r in readings:
        t = HWINFO_TYPES.get(r["type"], "?")
        print(f"  [{r['sensor']}] {r['label']} — {r['value']:.1f} {r['unit']} ({t})")
    print('\nExemple de bouton pour la page "hardware" de akp05e_config.json :')
    ex = readings[0]["label"]
    print(f'  "1": {{"hw": "{ex}", "label": "{ex[:8]}"}}')

# ---------------------------------------------------------------------------
# Constantes matérielles (confirmées sur matériel réel)
# ---------------------------------------------------------------------------
VENDOR_ID = 0x0300
PRODUCT_ID = 0x3004
PACKET_SIZE = 1024          # payload HID par rapport
TOTAL_LEN = 1 + PACKET_SIZE # report-ID 0x00 + payload
KEY_IDX, STATE_IDX = 10, 11 # positions dans les rapports d'entrée Windows

BUTTON_IMAGE_SIZE = (112, 112)
STRIP_IMAGE_SIZE = (800, 112)
STRIP_WIRE_KEY = 1
# Taille max du JPEG du bandeau : au-delà, le buffer du firmware boucle sur
# lui-même et l'image se corrompt (bandes brouillées). v2.14.3 : abaissé à
# 9000 — avec le bandeau enrichi (pilule zone 3, carrousel avec icône,
# noms de lecteur longs) le JPEG frôlait 12000 et le firmware perdait la
# fin du transfert : artefacts « carrés de pixels » sur la zone 1 puis 4.
STRIP_MAX_JPEG = 9000
STRIP_JPEG_QUALITIES = (80, 65, 50, 35, 25, 20)
DEFAULT_BRIGHTNESS = 30
APP_VERSION = "2.19.9"

# cache de la dernière image du bandeau SANS le VU-mètre : le fil poll_vu
# la recopie puis dessine la zone 3 par-dessus, sans tout recalculer
_strip_base = None
_strip_base_lock = threading.Lock()
_strip_last = None        # dernière image RÉELLEMENT affichée (avec le VU)
_strip_last_lock = threading.Lock()
_vu_active = False        # levé par main() quand le fil VU tourne
_strip_size_logged = False  # v2.14.3 : log one-shot taille JPEG bandeau
_strip_last_quality = 80    # v2.14.4 : qualité JPEG bandeau mémorisée
PC_RESUME_GAP_S = 30        # v2.15.0 : écart horloge => le PC a dormi

# Événements du bandeau tactile — mappage établi par calibration sur le
# matériel réel (v1.5.1) : 0x40..0x43 = tap zone 1..4 ; 0x39 = swipe gauche
# (page précédente) ; 0x38 = swipe droit (page suivante). 0x3A/0x3B restent
# inconnus (probables swipe haut/bas) et sont signalés s'ils surviennent.
STRIP_TAP_BASE = 0x40    # tap zone N -> code 0x40 + N - 1
STRIP_SWIPE_PREV = 0x39  # swipe gauche -> page précédente
STRIP_SWIPE_NEXT = 0x38  # swipe droit  -> page suivante

# mapping touche pressée (1-10) -> wire-key image
BUTTON_TO_WIRE_KEY = {1: 11, 2: 12, 3: 13, 4: 14, 5: 15,
                      6: 6, 7: 7, 8: 8, 9: 9, 10: 10}

# id d'événements d'entrée -> nom logique
ENCODERS = {
    0x37: "encoder_1_button", 0xA0: "encoder_1_ccw", 0xA1: "encoder_1_cw",
    0x35: "encoder_2_button", 0x50: "encoder_2_ccw", 0x51: "encoder_2_cw",
    0x33: "encoder_3_button", 0x90: "encoder_3_ccw", 0x91: "encoder_3_cw",
    0x36: "encoder_4_button", 0x70: "encoder_4_ccw", 0x71: "encoder_4_cw",
}
KEY_DOWN, KEY_UP = 1, 0

# ---------------------------------------------------------------------------
# Bibliothèque d'icônes Material Icons (Google, licence Apache 2.0)
# Téléchargée et mise en cache au premier usage dans .icons_cache/,
# puis totalement hors ligne. Noms disponibles : https://fonts.google.com/icons
# ---------------------------------------------------------------------------
# Dossier d'installation : à côté de l'EXE si compilé (PyInstaller met
# __file__ dans un dossier temporaire _MEIPASS), sinon à côté du script.
_APP_BASE = (os.path.dirname(sys.executable)
             if getattr(sys, "frozen", False)
             else os.path.dirname(os.path.abspath(__file__)))
ICON_CACHE = os.path.join(_APP_BASE, ".icons_cache")
ICON_FONT_URL = ("https://github.com/google/material-design-icons/"
                 "raw/master/font/MaterialIcons-Regular.ttf")
ICON_CODEPOINTS_URL = ("https://github.com/google/material-design-icons/"
                       "raw/master/font/MaterialIcons-Regular.codepoints")

def _download(url, dest):
    if os.path.exists(dest):
        return dest
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    import urllib.request
    tmp = dest + ".part"
    urllib.request.urlretrieve(url, tmp)
    os.replace(tmp, dest)
    return dest

def _icon_char(name):
    """Retourne le caractère du glyphe pour un nom d'icône (ex: 'play_arrow')."""
    cp_path = _download(ICON_CODEPOINTS_URL, os.path.join(ICON_CACHE, "codepoints"))
    with open(cp_path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.split()
            if len(parts) == 2 and parts[0] == name:
                return chr(int(parts[1], 16))
    raise ValueError(f"Icône inconnue : {name!r} — voir https://fonts.google.com/icons")

def parse_color(c, default=(240, 240, 240)):
    """'#4CAF50', '#f00', 'green' ou [r,g,b] -> tuple RGB."""
    if c is None:
        return default
    try:
        from PIL import ImageColor
        return ImageColor.getrgb(c)[:3]
    except Exception:
        return default

def set_icon(device, button, name, fg="#e0e0e0", bg="#101010", label=None):
    """Dessine une icône Material (couleur fg, fond bg) + libellé optionnel,
    et l'envoie sur la touche LCD. fg/bg acceptent n'importe quel format
    de couleur CSS (hex, noms, rgb())."""
    font_path = _download(ICON_FONT_URL, os.path.join(ICON_CACHE, "MaterialIcons-Regular.ttf"))
    fg_rgb, bg_rgb = parse_color(fg), parse_color(bg)
    img = Image.new("RGB", BUTTON_IMAGE_SIZE, bg_rgb)
    d = ImageDraw.Draw(img)
    # léger dégradé vertical pour un rendu plus moderne
    for y in range(BUTTON_IMAGE_SIZE[1]):
        mix = tuple(int(c * (1 - 0.25 * y / 112)) for c in bg_rgb)
        d.line([(0, y), (112, y)], fill=mix)
    icon_font = ImageFont.truetype(font_path, 60 if label else 78)
    d.text((56, 38 if label else 56), _icon_char(name),
           font=icon_font, fill=fg_rgb, anchor="mm")
    if label:
        try:
            text_font = ImageFont.truetype("arial.ttf", 14)
        except OSError:
            text_font = ImageFont.load_default()
        dim = tuple(int(c * 0.75 + 60) if c < 128 else int(c * 0.75 + 20)
                    for c in fg_rgb)
        d.text((56, 88), label, font=text_font, fill=dim, anchor="mm")
    device.set_image(button, img)

# ---------------------------------------------------------------------------
# Bandeau tactile (800x112) : une zone de 200px par encodeur
# ---------------------------------------------------------------------------
def draw_vu_zone(img, peak, hold, muted=False):
    """VU-mètre vertical segmenté dans la zone 3 du bandeau (x 400-600) :
    segments vert/ambre/rouge + marqueur de crête (peak-hold) qui
    retombe lentement, "Muet" si le son est coupé."""
    d = ImageDraw.Draw(img)
    d.rectangle([404, 6, 596, 106], fill=(16, 16, 16))  # efface la zone
    try:
        f_t = ImageFont.truetype("arial.ttf", 14)
    except OSError:
        f_t = ImageFont.load_default()
    d.text((500, 12), "VU", font=f_t, fill=(129, 212, 250), anchor="mm")
    n = 14                       # nombre de segments
    y_bot, y_top = 106, 24
    seg_h = (y_bot - y_top) / n
    for i in range(n):
        y0 = y_bot - (i + 1) * seg_h
        y1 = y_bot - i * seg_h - 1
        if i / n < 0.6:
            col = (129, 199, 132)                    # vert
        elif i / n < 0.85:
            col = (255, 213, 79)                     # ambre
        else:
            col = (239, 83, 80)                      # rouge
        lit = (i + 0.5) / n <= peak
        mark = (not muted and not lit and i / n <= hold < (i + 1) / n)
        if lit:
            fill = col
        elif mark:  # segment de crête éteint, en teinte sombre
            fill = (col[0] // 3, col[1] // 3, col[2] // 3)
        else:
            fill = (40, 42, 46)
        d.rectangle([470, y0, 530, y1], fill=fill)
    if muted:
        d.text((500, 64), "Muet", font=f_t, fill=(239, 154, 154), anchor="mm")

_Z3_DIAG = {"warned": False, "none": False, "err": False,
              "ntitle": False, "radio": False, "nopb": False}
# v2.19.1 : titre bandeau indisponible ; v2.19.2 : dump webradio
_Z3_CYCLE = [0]  # v2.19.2 : cycles du poll pour le re-poll radios
# v2.13.9/2.14.0 : diagnostics one-shot position zone 3


def _lms_dump_playing(lms, cand):
    """v2.19.6 : dump one-shot INCONDITIONNEL du lecteur qui joue —
    status brut + playing_track brut, tronqués. Renvoie True une fois
    affiché (pour le drapeau one-shot). Aucune condition de schéma
    d'URL ou de nombre de pistes : les hypothèses successives
    (http://, tout schéma, playlist mono-piste) n'ont jamais matché
    le serveur réel."""
    try:
        _raw = lms.request(cand["id"], ["status", "-", "1", "tags:uA"])
    except Exception as _e:
        _raw = repr(_e)
    try:
        _pt = lms.playing_track(cand["id"])
    except Exception as _e:
        _pt = repr(_e)
    print(f"[lms] bandeau : lecteur qui joue {cand.get('name')!r} — "
          f"status -> {str(_raw)[:500]!r} — "
          f"playing_track -> {str(_pt)[:300]!r} — copie ces lignes")
    return True


def _fit_text(d, text, font, max_w):
    """v2.19.0 : tronque un texte avec « … » pour tenir dans max_w px
    (bandeau) — jamais de débordement sur la zone voisine."""
    text = str(text or "")

    def _w(s):
        try:
            v = d.textlength(s, font=font)
            return v if isinstance(v, (int, float)) else 11 * len(s)
        except Exception:
            return 11 * len(s)

    if _w(text) <= max_w:
        return text
    while text:
        text = text[:-1].rstrip()
        if _w(text) <= max_w - 14:
            return text + "…"
    return "…"


def show_strip(device, brightness, volume=None, muted=None, extras=("K2", "K3"),
               pages=None, page_icon=None, page_color=None,
               vol_name="Vol"):
    """Redessine le bandeau sous les 4 knobs : zone 1 = volume système
    (temps réel, + barre + %, "Muet" si coupé), zone 4 = luminosité
    avec barre + %. Zone 2 = carrousel de pages si pages=(prev, cur, next) :
    pages précédente/suivante en grisé avec flèches, page courante dans
    une pilule arrondie colorée avec mini-icône Material (optionnelle).
    Sinon libellé libre. Zone 3 : libellé libre."""
    w, h = STRIP_IMAGE_SIZE
    img = Image.new("RGB", (w, h), (16, 16, 16))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 17)
        font_big = ImageFont.truetype("arial.ttf", 26)
        font_mid = ImageFont.truetype("arial.ttf", 20)
        font_small = ImageFont.truetype("arial.ttf", 15)
    except OSError:
        font = font_big = font_mid = font_small = ImageFont.load_default()

    def level_zone(x_center, name, pct, is_muted, name_color):
        d.text((x_center, 28), name, font=font, fill=name_color, anchor="mm")
        if is_muted:
            d.text((x_center, 66), "Muet", font=font_big,
                   fill=(239, 154, 154), anchor="mm")
        else:
            d.text((x_center, 66), f"{pct}%", font=font_big,
                   fill=(240, 240, 240), anchor="mm")
        bar_x0, bar_x1, bar_y = x_center - 90, x_center + 90, 92
        d.rounded_rectangle([bar_x0, bar_y, bar_x1, bar_y + 12], radius=6,
                            fill=(50, 50, 50))
        if is_muted:
            fill = (239, 154, 154)
        elif vol_name == "Vol":
            fill = (129, 212, 250)
        else:
            fill = (255, 213, 79)
        fill_w = int((bar_x1 - bar_x0 - 4) * max(0, min(100, pct)) / 100)
        if fill_w > 0:
            d.rounded_rectangle([bar_x0 + 2, bar_y + 2, bar_x0 + 2 + fill_w,
                                 bar_y + 10], radius=4, fill=fill)

    # zone 1 : volume système (ou libellé libre si pycaw absent)
    if volume is not None:
        level_zone(100, vol_name, volume, muted, (129, 212, 250))
    else:
        d.text((100, 34), "K1", font=font, fill=(120, 120, 120), anchor="mm")
    # zone 2 : carrousel de pages (◄ page préc. | PAGE COURANTE | page suiv. ►)
    x0 = 200
    if pages:
        prev_lab, cur_lab, next_lab = pages
        gray = (112, 117, 126)
        # rangée du haut : page précédente (grisée) à gauche
        d.polygon([(x0 + 8, 32), (x0 + 20, 24), (x0 + 20, 40)], fill=gray)
        d.text((x0 + 26, 32), prev_lab[:8], font=font_small,
               fill=gray, anchor="lm")
        # page suivante (grisée) à droite
        d.text((x0 + 174, 32), next_lab[:8], font=font_small,
               fill=gray, anchor="rm")
        d.polygon([(x0 + 192, 32), (x0 + 180, 24), (x0 + 180, 40)], fill=gray)
        # pilule arrondie : page courante (couleur d'accent + mini-icône)
        accent = tuple(page_color) if page_color else (129, 212, 250)
        glyph = None
        if page_icon:
            try:
                ifont = ImageFont.truetype(
                    os.path.join(ICON_CACHE, "MaterialIcons-Regular.ttf"), 24)
                glyph = _icon_char(page_icon)
            except Exception:
                glyph = None  # police d'icônes pas encore en cache : sans logo
        if glyph:
            d.rounded_rectangle([x0 + 40, 48, x0 + 162, 98], radius=14,
                                fill=(40, 44, 52), outline=accent, width=2)
            d.text((x0 + 62, 74), glyph, font=ifont, fill=accent, anchor="mm")
            d.text((x0 + 116, 73), cur_lab[:7], font=font_mid,
                   fill=(235, 238, 242), anchor="mm")
        else:
            d.rounded_rectangle([x0 + 48, 48, x0 + 152, 98], radius=14,
                                fill=(40, 44, 52), outline=accent, width=2)
            d.text((x0 + 100, 73), cur_lab[:9], font=font_mid,
                   fill=(235, 238, 242), anchor="mm")
    else:
        d.text((x0 + 100, 34), extras[0], font=font,
               fill=(120, 120, 120), anchor="mm")
    # zone 3 : VU-mètre — on recolle les pixels du dernier rendu affiché
    # (zéro scintillement quand un refresh volume/luminosité intervient,
    # et le fil VU n'a pas besoin de réenvoyer une frame juste après) —
    # sinon libellé libre
    if (isinstance(extras[1], tuple) and len(extras[1]) == 3
            and extras[1][0] == "TITLE"):
        # v2.19.0 : titre du morceau LMS (zone 3, à la place du VU-mètre)
        _t_title = _fit_text(d, extras[1][1], font_mid, 188)
        d.text((500, 42), _t_title, font=font_mid, fill=(129, 212, 250),
               anchor="mm")
        _t_artist = extras[1][2]
        if _t_artist:
            d.text((500, 82), _fit_text(d, _t_artist, font_small, 188),
                   font=font_small, fill=(176, 190, 197), anchor="mm")
    elif (_vu_active and extras[1] == "VU"
            and _strip_last is not None):
        # pages LMS : extras[1]=="K3" -> on NE recolle PAS
        # le VU en cache, on affiche le libellé libre
        with _strip_last_lock:
            img.paste(_strip_last.crop((400, 0, 600, h)), (400, 0))
    else:
        z3 = str(extras[1])
        # v2.13.8 : pilule avec liseret accent (même style que le
        # carrousel de la zone 2), centrée VERTICALEMENT dans la zone
        # (l'ancien libellé gris était perdu en haut) :
        #  - « i/N » : morceau en cours / total de la liste jouée ;
        #  - « ▶ … » : bouton actif (le glyphe U+25B6 est absent
        #    d'Arial/WGL4 -> triangle dessiné en polygone).
        if z3.startswith("\u25b6") or re.fullmatch(r"\d+/\d+", z3):
            d.rounded_rectangle([412, 36, 588, 76], radius=13,
                                fill=(40, 44, 52),
                                outline=(129, 212, 250), width=2)
            if z3.startswith("\u25b6"):
                label = z3[1:].strip()
                try:
                    tw = d.textlength(label, font=font_mid)
                except Exception:
                    tw = 11 * len(label)
                x0 = 500 - (18 + 8 + tw) / 2
                d.polygon([(x0, 47), (x0, 65), (x0 + 16, 56)],
                          fill=(129, 212, 250))
                d.text((x0 + 24, 57), label, font=font_mid,
                       fill=(129, 212, 250), anchor="lm")
            else:
                d.text((500, 57), z3, font=font_mid,
                       fill=(129, 212, 250), anchor="mm")
        else:
            d.text((500, 34), z3, font=font,
                   fill=(120, 120, 120), anchor="mm")
    # zone 4 : luminosité
    level_zone(700, "Lum", max(0, min(100, int(brightness))), False,
               (240, 220, 130))
    # séparateurs verticaux entre zones
    for i in (1, 2, 3):
        d.line([(i * 200, 10), (i * 200, h - 10)], fill=(45, 45, 45), width=2)
    global _strip_base  # le fil du VU-mètre redessinera la zone 3 par-dessus
    with _strip_base_lock:
        _strip_base = img.copy()
    device.set_strip(img)

def paint_hw_button(device, button, label, reading, thresholds=(70, 85)):
    """Dessine une touche de capteur : libellé en haut, grande valeur au
    centre, unité en bas ; la couleur suit les seuils pour les températures
    (vert < warn < orange < crit < rouge)."""
    img = Image.new("RGB", BUTTON_IMAGE_SIZE, (16, 16, 16))
    d = ImageDraw.Draw(img)
    try:
        f_small = ImageFont.truetype("arial.ttf", 15)
        f_big = ImageFont.truetype("arial.ttf", 34)
        f_unit = ImageFont.truetype("arial.ttf", 13)
    except OSError:
        f_small = f_big = f_unit = ImageFont.load_default()
    d.text((56, 22), (label or "?")[:10], font=f_small, fill=(150, 150, 150),
           anchor="mm")
    if reading is None:
        d.text((56, 66), "—", font=f_big, fill=(120, 120, 120), anchor="mm")
    else:
        v = reading["value"]
        col = (129, 212, 250)
        if reading["type"] == 1:  # température : code couleur
            if v < thresholds[0]:
                col = (165, 214, 129)
            elif v < thresholds[1]:
                col = (255, 213, 79)
            else:
                col = (239, 83, 80)
        # v2.14.6 : retour au format 2.14.4 (décimale seulement < 9,95)
        txt = f"{v:.0f}" if abs(v) >= 9.95 else f"{v:.1f}"
        d.text((56, 66), txt, font=f_big, fill=col, anchor="mm")
        if reading["unit"]:
            d.text((56, 98), reading["unit"], font=f_unit,
                   fill=(150, 150, 150), anchor="mm")
    device.set_image(button, img)

# ---------------------------------------------------------------------------
# Minuteurs : touches prédéfinies avec départ/pause (clic) et reset (clic long)
# ---------------------------------------------------------------------------
TIMER_STATUS_COLORS = {"idle": (176, 190, 197), "run": (129, 199, 132),
                       "pause": (255, 213, 79), "alarm": (239, 83, 80)}

def format_mmss(seconds):
    """Secondes -> 'm:ss' (zéro de gauche sur les secondes)."""
    s = max(0, int(seconds))
    return f"{s // 60}:{s % 60:02d}"

def paint_timer_button(device, button, label, remaining=None, total=300,
                       status="idle", idle_sub="min", label_fill=None):
    """Touche minuteur : libellé en haut, temps restant au centre, état
    en bas (idle = préréglage gris, run = vert, pause = ambre, alarm =
    rouge)."""
    img = Image.new("RGB", BUTTON_IMAGE_SIZE, (16, 16, 16))
    d = ImageDraw.Draw(img)
    try:
        f_small = ImageFont.truetype("arial.ttf", 15)
        f_big = ImageFont.truetype("arial.ttf", 31)
        f_unit = ImageFont.truetype("arial.ttf", 13)
    except OSError:
        f_small = f_big = f_unit = ImageFont.load_default()
    d.text((56, 20), (label or "?")[:10], font=f_small,
           fill=label_fill or (150, 150, 150), anchor="mm")
    txt = format_mmss(remaining if remaining is not None else total)
    d.text((56, 63), txt, font=f_big,
           fill=TIMER_STATUS_COLORS.get(status, (200, 200, 200)),
           anchor="mm")
    sub = {"idle": idle_sub, "run": "en cours", "pause": "pause",
           "alarm": "fini !"}[status]
    d.text((56, 98), sub, font=f_unit, fill=(150, 150, 150), anchor="mm")
    device.set_image(button, img)

def ring_alarm(times=3):
    """Alarme de fin de minuteur : carillon doux (winsound, stdlib Windows)
    — deux notes descendantes (Sol 5 puis Do 5, plus grave), répétées
    avec de longues pauses, au lieu de bips aigus en rafale."""
    try:
        import winsound
        for _ in range(times):
            winsound.Beep(784, 200)
            time.sleep(0.08)
            winsound.Beep(523, 300)
            time.sleep(0.9)
    except Exception as e:
        print(f"[minuteur] alarme silencieuse ({e}) — temps écoulé !")

# ---------------------------------------------------------------------------
# Couche protocole HID
# ---------------------------------------------------------------------------
Event = namedtuple("Event", ["name", "state"])  # state: True=down/cw|ccw one-shot

def crt_command(command: str, payload=(), total_len=TOTAL_LEN):
    """Construit un rapport de sortie cadré 'CRT'. Gère les commandes de
    3 lettres (DIS/LIG/CLE/STP/BAT) comme les longues (CONNECT)."""
    buf = [0] * total_len
    buf[1:4] = [ord(c) for c in "CRT"]
    cmd = [ord(c) for c in command]
    start = 6
    buf[start:start + len(cmd)] = cmd
    start += len(cmd)
    buf[start:start + len(payload)] = list(payload)
    return buf

class Akp05Device:
    def __init__(self, brightness=DEFAULT_BRIGHTNESS):
        self.brightness = brightness
        self.lock = threading.Lock()
        self.dev = None
        self._keepalive_stop = threading.Event()
        self._threads = []
        self._unknown_seen = set()  # codes d'entrée inconnus déjà signalés
        self.on_event = None          # callback(Event)
        self.on_disconnect = None
        self.on_reconnect = None   # v2.15.0 : callback après reconnexion
        self.on_brightness = None     # callback(pct) — rafraîchit le bandeau

    # -- connexion ---------------------------------------------------------
    def open(self):
        target = hid.HidDeviceFilter(vendor_id=VENDOR_ID,
                                     product_id=PRODUCT_ID).get_devices()
        if not target:
            raise IOError("AKP05E introuvable (VID 0300 / PID 3004). "
                          "Branche le deck (câble USB-C données, pas charge seule).")
        self.dev = target[0]
        self.dev.open()
        self.dev.set_raw_data_handler(self._on_raw_data)
        with self.lock:
            self._send(crt_command("DIS"))
            self._send(crt_command("LIG", [0, 0]))
            self._send(crt_command("LIG", [0, 0, self.brightness]))
            self._send(crt_command("CLE", [0, 0, 0, 0xFF]))  # efface tout
            self._send(crt_command("STP"))
        t = threading.Thread(target=self._keepalive_loop, daemon=True)
        t.start()
        self._threads.append(t)
        return self

    def close(self):
        self._keepalive_stop.set()
        if self.dev:
            try:
                self.dev.close()
            except Exception:
                pass
            self.dev = None

    def reconnect(self):
        """v2.15.0 : ferme et rouvre la connexion HID (PC sorti de veille,
        câble rebranché...). Renvoie True si le deck est de nouveau
        opérationnel (handshake complet + keepalive relancé)."""
        try:
            self.close()
        except Exception:
            pass
        self._keepalive_stop.clear()
        try:
            self.open()
            return True
        except Exception as e:
            print(f"[reconnexion] échec : {e}")
            return False

    def _send(self, data):
        if getattr(self, "dev", None) is None:
            return  # deck fermé (Ctrl+C) : no-op silencieux — les
            # threads démons (poll_lms…) peuvent encore peindre un
            # instant pendant le shutdown, sans erreur ni traceback
        reports = self.dev.find_output_reports()
        if not reports:
            raise IOError("Aucun rapport de sortie HID.")
        reports[0].send(data)

    def _on_raw_data(self, data):
        data = list(data)
        if len(data) < STATE_IDX + 1:
            return
        if data[1:4] != [ord("A"), ord("C"), ord("K")] or \
           data[6:8] != [ord("O"), ord("K")]:
            return  # pas un rapport d'événement
        key, state = data[KEY_IDX], data[STATE_IDX]
        if 1 <= key <= 10:
            name = f"button_{key}"
            ev = Event(name, state == KEY_DOWN)
        elif key in ENCODERS:
            name = ENCODERS[key]
            # twist = one-shot (state toujours 0) ; press = down/up
            ev = Event(name, True if name.endswith(("_cw", "_ccw"))
                       else state == KEY_DOWN)
        elif STRIP_TAP_BASE <= key <= STRIP_TAP_BASE + 3:
            # tap sur la zone tactile N (1..4), alignée sur l'encodeur N
            ev = Event(f"strip_tap_{key - STRIP_TAP_BASE + 1}", True)
        elif key == STRIP_SWIPE_PREV:
            ev = Event("strip_swipe_left", True)
        elif key == STRIP_SWIPE_NEXT:
            ev = Event("strip_swipe_right", True)
        elif 0x30 <= key <= 0x47:
            self._log_unknown(key)
            return
        else:
            self._log_unknown(key)
            return
        if self.on_event:
            try:
                self.on_event(ev)
            except Exception as e:
                print(f"[erreur handler] {e}")

    def _log_unknown(self, key):
        """Signale une fois par code les entrées non reconnues, pour affiner
        le mappage du protocole avec les retours réels du deck."""
        if key not in self._unknown_seen:
            self._unknown_seen.add(key)
            print(f"[protocole] entrée inconnue : 0x{key:02X} "
                  f"(merci de signaler ce message pour le débogage)")

    def _keepalive_loop(self):
        while not self._keepalive_stop.wait(10.0):
            try:
                with self.lock:
                    self._send(crt_command("DIS"))
                    self._send(crt_command("LIG", [0, 0, self.brightness]))
                    self._send(crt_command("CONNECT"))
            except Exception:
                # v2.15.0 : deck injoignable (PC réveillé, USB
                # réénuméré...) — on tente de rouvrir la connexion
                if self.reconnect():
                    print("[reconnexion] deck reconnecté")
                    if self.on_reconnect:
                        try:
                            self.on_reconnect()
                        except Exception:
                            pass
                    # reconnect() -> open() a déjà relancé un keepalive
                    # tout neuf : cette boucle s'arrête pour ne pas doubler
                    # le trafic HID toutes les 10 s
                    return
                if self.on_disconnect:
                    self.on_disconnect()
                return

    # -- affichage ---------------------------------------------------------
    def set_brightness(self, pct):
        self.brightness = max(0, min(100, int(pct)))
        with self.lock:
            self._send(crt_command("DIS"))
            self._send(crt_command("LIG", [0, 0, self.brightness]))
        if self.on_brightness:  # permet de rafraîchir le bandeau tactile
            try:
                self.on_brightness(self.brightness)
            except Exception as e:
                print(f"[erreur bandeau] {e}")

    def _upload_jpeg(self, wire_key, jpeg):
        """Envoi d'une image JPEG sur un wire-key (BAT + chunks + STP).
        Un mini-délai entre les paquets est indispensable : envoyés en
        rafale, le firmware du deck en perd certains en route et l'image
        se corrompt au milieu (zones brouillées)."""
        header = crt_command("BAT", [0, 0, (len(jpeg) >> 8) & 0xFF,
                                    len(jpeg) & 0xFF, wire_key])
        with self.lock:
            self._send(header)
            # v2.14.3 : gros transferts (bandeau) = délai doublé — le
            # firmware perd des paquets quand la trame est longue
            delay = 0.002 if len(jpeg) <= STRIP_MAX_JPEG else 0.004
            for i in range(0, len(jpeg), PACKET_SIZE):
                chunk = jpeg[i:i + PACKET_SIZE]
                packet = [0] * TOTAL_LEN
                packet[1:1 + len(chunk)] = list(chunk)
                self._send(packet)
                time.sleep(delay)  # laisse le firmware du deck absorber
            self._send(crt_command("STP"))

    @staticmethod
    def _pil_to_jpeg(img):
        import io
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        return buf.getvalue()

    @staticmethod
    def _pil_to_jpeg_capped(img, max_size=STRIP_MAX_JPEG):
        """Encode en JPEG en réduisant la qualité jusqu'à tenir sous
        max_size octets : un JPEG trop gros déborde du buffer du firmware
        (le milieu du bandeau se corrompt).
        v2.14.4 : repart de la dernière qualité qui a tenu sous le cap —
        en régime établi un SEUL encodage par repaint (au lieu de 2-4
        essais) et un rendu visuel stable (pas de saut de qualité)."""
        import io
        global _strip_last_quality
        start = (_strip_last_quality
                 if _strip_last_quality in STRIP_JPEG_QUALITIES
                 else STRIP_JPEG_QUALITIES[0])
        # la qualité mémorisée d'abord, puis les qualités INFÉRIEURES
        # dans l'ordre (si l'image redevient plus grosse, on redescend)
        order = [start] + [q for q in STRIP_JPEG_QUALITIES if q < start]
        for q in order:
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=q, optimize=True)
            jpeg = buf.getvalue()
            if len(jpeg) <= max_size:
                _strip_last_quality = q
                return jpeg
        return jpeg

    def set_image(self, button: int, img: Image.Image):
        """Upload une image PIL sur la touche (1-10), 112x112, rotation 180°."""
        if button not in BUTTON_TO_WIRE_KEY:
            raise ValueError("button doit être entre 1 et 10")
        img = img.convert("RGB").resize(BUTTON_IMAGE_SIZE).rotate(180)
        # v2.15.1 : veille étanche — l'horloge, les minuteurs, le VU...
        # repeignaient leurs touches par-dessus la veille ; les DEUX seuls
        # entonnoirs vers l'écran deviennent muets tant que le deck dort
        if getattr(self, "_sleeping", False):
            return
        self._upload_jpeg(BUTTON_TO_WIRE_KEY[button], self._pil_to_jpeg(img))

    def set_strip(self, img: Image.Image):
        if getattr(self, "_sleeping", False):
            return  # v2.15.1 : veille étanche, bandeau compris
        """Upload une image PIL sur le bandeau tactile (800x112, wire-key 1).
        JPEG compressé adaptativement pour rester sous la limite firmware.
        Mémorise le dernier rendu affiché : les refresh (volume, luminosité)
        recopient ensuite les pixels du VU au lieu de le faire scintiller."""
        img = img.convert("RGB").resize(STRIP_IMAGE_SIZE)
        global _strip_last
        with _strip_last_lock:
            _strip_last = img.copy()
        img = img.rotate(180)
        jpeg = self._pil_to_jpeg_capped(img)
        global _strip_size_logged
        if not _strip_size_logged:
            _strip_size_logged = True
            print(f"[bandeau] JPEG du bandeau : {len(jpeg)} octets "
                  f"(max {STRIP_MAX_JPEG}) — ligne de diagnostic, "
                  "à copier si des artefacts apparaissent")
        if len(jpeg) > STRIP_MAX_JPEG:
            print(f"[bandeau] JPEG encore gros ({len(jpeg)} octets), "
                  "risque de corruption possible")
        self._upload_jpeg(STRIP_WIRE_KEY, jpeg)

    def set_label(self, button: int, text: str, bg=(15, 15, 15),
                  fg=(240, 240, 240), sub: str = None, small: bool = False,
                  icon: str = None):
        """Touche texte HARMONISÉE (v2.7.0) : la MÊME police partout —
        la petite (20 px), la seule qui tient entière dans les 112 px des
        écrans de touches ; noms longs coupés sur deux lignes équilibrées,
        sous-titre 13 px. icon= : nom d'icône Material dessiné en petit
        en haut de la touche (alim, lecture, radio…). small= est accepté
        pour compatibilité mais la police est toujours la petite."""
        w_bt, h_bt = BUTTON_IMAGE_SIZE
        if (isinstance(bg, (tuple, list)) and len(bg) == 2
                and isinstance(bg[0], (tuple, list))
                and isinstance(bg[1], (tuple, list))):
            # dégradé vertical : couleur du HAUT vers celle du BAS
            (r1, g1, b1), (r2, g2, b2) = bg
            img = Image.new("RGB", BUTTON_IMAGE_SIZE, bg[0])
            d = ImageDraw.Draw(img)
            for y in range(h_bt):
                t = y / max(1, h_bt - 1)
                d.line([(0, y), (w_bt, y)],
                       fill=(int(r1 + (r2 - r1) * t),
                             int(g1 + (g2 - g1) * t),
                             int(b1 + (b2 - b1) * t)))
        else:
            img = Image.new("RGB", BUTTON_IMAGE_SIZE, bg)
            d = ImageDraw.Draw(img)
        try:
            font_big = ImageFont.truetype("arial.ttf", 20)
            font_small = ImageFont.truetype("arial.ttf", 13)
        except OSError:
            font_big = font_small = ImageFont.load_default()
        if icon:
            # petit logo Material en haut de la touche
            try:
                ipath = _download(
                    ICON_FONT_URL,
                    os.path.join(ICON_CACHE, "MaterialIcons-Regular.ttf"))
                ifont = ImageFont.truetype(ipath, 30)
                base = fg if isinstance(fg, (tuple, list)) \
                    else (240, 240, 240)
                dim = tuple(min(255, int(c * 0.75) + 45)
                            for c in tuple(base)[:3])
                d.text((56, 21), _icon_char(icon), font=ifont,
                       fill=dim, anchor="mm")
            except Exception:
                pass                      # hors ligne sans cache : texte seul
        # avec un logo le texte descend, le sous-titre aussi
        y0 = (60 if sub else 62) if icon else (44 if not sub else 38)
        # v2.9.2 : le texte ne doit JAMAIS déborder des 112 px —
        # découpage en 2 lignes équilibrées, puis police auto-ajustée
        # (20 -> 14 px) jusqu'à ce que la plus large ligne tienne.
        max_w = 100  # 6 px de marge de chaque côté

        def _fnt(sz):
            try:
                return ImageFont.truetype("arial.ttf", sz)
            except OSError:
                return ImageFont.load_default()

        def _tw(s, f):
            bb = d.textbbox((0, 0), s, font=f)
            return bb[2] - bb[0]

        lines = [text]
        if len(text) > 8 and " " in text:
            # coupe au plus près du milieu pour équilibrer les 2 lignes
            words = text.split(" ")
            best, best_d, acc = 0, 10 ** 9, 0
            for k in range(len(words) - 1):
                acc += len(words[k]) + 1
                dist = abs(acc - (len(text) + 1) / 2)
                if dist < best_d:
                    best_d, best = dist, acc
            lines = [text[:best].strip(), text[best:].strip()]
        elif _tw(text, font_big) > max_w:
            # mot unique trop long : coupe au milieu (jamais de débord)
            m = max(1, len(text) // 2)
            lines = [text[:m].strip(), text[m:].strip()]
        size = 20
        while True:
            too = [l for l in lines if _tw(l, _fnt(size)) > max_w]
            if not too:
                break
            if size > 11:
                size -= 1
                continue
            # au plancher de police : recoupe la ligne la plus large
            # au prorata de la place disponible (3 lignes max)
            l = max(too, key=lambda x: _tw(x, _fnt(size)))
            nchar = max(2, int(len(l) * max_w / _tw(l, _fnt(size))))
            i = lines.index(l)
            lines[i:i + 1] = [l[:nchar].strip(), l[nchar:].strip()]
            if len(lines) > 3:
                break
        font_txt = _fnt(size)
        if len(lines) == 1:
            d.text((56, y0), lines[0], font=font_txt, fill=fg,
                   anchor="mm")
        elif len(lines) == 2:
            d.text((56, y0 - 13), lines[0], font=font_txt, fill=fg,
                   anchor="mm")
            d.text((56, y0 + 13), lines[1], font=font_txt, fill=fg,
                   anchor="mm")
        else:
            for j, l in enumerate(lines):
                d.text((56, y0 - 16 + 16 * j), l, font=font_txt,
                       fill=fg, anchor="mm")
        if sub:
            d.text((56, 92 if icon else 84), sub, font=font_small,
                   fill=(160, 160, 160), anchor="mm")
        self.set_image(button, img)

# ---------------------------------------------------------------------------
# Actions Windows (SendInput via ctypes — pas de dépendance propriétaire)
# ---------------------------------------------------------------------------
import ctypes
from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)
shell32 = ctypes.WinDLL("shell32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
# codes virtuels / scan codes média (usage HID 0x7C+)
# touches média : codes virtuels Windows officiels (VK_MEDIA_* / VK_VOLUME_*)
# — seuls ces codes-là sont vus par les applications (Qobuz, Spotify, etc.)
MEDIA = {"volume_up": 0xAF, "volume_down": 0xAE, "volume_mute": 0xAD,
         "play_pause": 0xB3, "stop": 0xB2, "next": 0xB0, "prev": 0xB1}
MODIFIERS = {"ctrl": 0x11, "menu": 0x12, "alt": 0x12, "shift": 0x10,
             "win": 0x5B, "lwin": 0x5B, "rwin": 0x5C}

VKEY_ALIASES = {"enter": 0x0D, "esc": 0x1B, "tab": 0x09, "space": 0x20,
                "backspace": 0x08, "delete": 0x2E, "up": 0x26, "down": 0x28,
                "left": 0x25, "right": 0x27, "home": 0x24, "end": 0x23,
                "pageup": 0x21, "pagedown": 0x22, "f5": 0x74, "printscreen": 0x2C}

class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class _INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("ki", _KEYBDINPUT),
                ("padding", wintypes.BYTE * 8)]

def _key_event(vk, scan=0, flags=0):
    inp = _INPUT(type=INPUT_KEYBOARD)
    inp.ki = _KEYBDINPUT(vk, scan, flags, 0, None)
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(_INPUT))

def _keybd_names(keys):
    """Traduit une liste de noms en (modifieurs, touche finale, scan)."""
    mods, final, scan = [], None, 0
    for k in keys:
        k = k.lower().strip()
        if k in MODIFIERS:
            mods.append(MODIFIERS[k])
        elif k in MEDIA:
            final, scan = 0, MEDIA[k]
        elif k in VKEY_ALIASES:
            final = VKEY_ALIASES[k]
        elif len(k) == 1:
            final = ord(k.upper())
        else:
            raise ValueError(f"Touche inconnue : {k}")
    return mods, final, scan

def send_keys(keys):
    mods, final, scan = _keybd_names(keys)
    for m in mods:
        _key_event(m)
    if final:
        _key_event(final); _key_event(final, flags=KEYEVENTF_KEYUP)
    elif scan:  # touche média : VK direct down/up (VK_MEDIA_* / VK_VOLUME_*)
        _key_event(scan); _key_event(scan, flags=KEYEVENTF_KEYUP)
    for m in reversed(mods):
        _key_event(m, flags=KEYEVENTF_KEYUP)

def type_text(text):
    for line in text.split("\n"):
        for ch in line:
            vk = user32.VkKeyScanW(ord(ch))
            if vk == -1:
                continue
            vk = vk & 0xFF
            shift = bool(vk >> 8 & 1)
            if shift:
                _key_event(0x10)
            _key_event(vk); _key_event(vk, flags=KEYEVENTF_KEYUP)
            if shift:
                _key_event(0x10, flags=KEYEVENTF_KEYUP)
        send_keys(["enter"])

# --- Souris (SendInput) : molette pour le zoom Ctrl+molette du knob 3 -----
INPUT_MOUSE = 0
MOUSEEVENTF_WHEEL = 0x0800
WHEEL_DELTA = 120

class _MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class _INPUT_MOUSE(ctypes.Structure):
    # même empreinte que _INPUT (40 octets sur x64) : DWORD type + pad +
    # MOUSEINPUT — SendInput accepte les deux structures à taille égale.
    _fields_ = [("type", wintypes.DWORD), ("pad", wintypes.DWORD),
                ("mi", _MOUSEINPUT)]

def _mouse_wheel_event(notches):
    inp = _INPUT_MOUSE(type=INPUT_MOUSE)
    inp.mi = _MOUSEINPUT(0, 0, notches * WHEEL_DELTA, MOUSEEVENTF_WHEEL,
                          0, None)
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(_INPUT_MOUSE))

def zoom_wheel(direction, notches=2):
    """Ctrl+molette : zoom de la fenêtre ACTIVE (navigateurs, Office,
    PDF, Photoshop…). direction : 1 = grossir, -1 = réduire."""
    _key_event(MODIFIERS["ctrl"])
    _mouse_wheel_event(direction * notches)
    _key_event(MODIFIERS["ctrl"], flags=KEYEVENTF_KEYUP)

# ---------------------------------------------------------------------------
# Moteur d'actions piloté par akp05e_config.json
# ---------------------------------------------------------------------------
def lms_play_fav_entry(lms, player, fav):
    """Joue un favori ; id « url:<…> » = webradio manuelle (lecture par
    URL directe), sinon favori LMS (favorites play)."""
    fid = str(fav.get("id") or "")
    if fid.startswith("url:"):
        lms.play_url(player, fav.get("url") or fid[4:])
    else:
        lms.play_favorite(player, fid)


def _to_int(v, default=-1):
    """Conversion robuste (« "55" » -> 55, absent/illisible -> défaut)."""
    try:
        return int(float(str(v)))
    except (TypeError, ValueError):
        return default


def fav_base_name(name):
    """« FIP Rock (MP3) » -> « fip rock » : nom de radio normalisé pour
    la comparaison avec le titre en cours (suffixe de format retiré)."""
    return re.sub(r"\s*\([^)]*\)\s*$", "",
                 str(name or "")).strip().lower()


def lms_active_fav(title, favs):
    """Index du favori correspondant au titre en cours (-1 si aucun).
    Le current_title d'une webradio vaut le nom de la station, parfois
    étendu (métadonnées). Comparaison sur noms normalisés : égalité, ou
    le titre COMMENCE par le nom du favori — le nom le plus long gagne
    (pour ne pas confondre FIP et FIP Rock)."""
    t = fav_base_name(title)
    if not t:
        return -1
    best, blen = -1, 0
    for i, f in enumerate(favs):
        b = fav_base_name(f.get("name"))
        if b and (t == b or t.startswith(b)) and len(b) > blen:
            best, blen = i, len(b)
    return best


def _url_key(url):
    """Normalise une URL pour comparaison (schéma ignoré, minuscules)."""
    u = str(url or "").strip().lower()
    for pre in ("http://", "https://"):
        if u.startswith(pre):
            u = u[len(pre):]
    u = u.split("?", 1)[0]      # query string ignorée (?_=123…)
    return u.rstrip("/")


def lms_viewed_active_fav(vp, favs, launched_id=None, playing=None):
    """Index du favori actif pour le lecteur affiché, -1 si aucun.
    1. URL du flux en cours == URL du favori (query string ignorée) ;
    2. NOM DE STATION (« title » du status, ex. « FIP ») ;
    3. current_title (parfois la station, souvent la métadonnée) ;
    4. titre remonté par « players » ;
    5. dernière radio LANCÉE DEPUIS LE DECK."""
    if not vp or not vp.get("playing"):
        return -1
    playing = playing or {}
    pu = _url_key(playing.get("url"))
    if pu:
        for j, f in enumerate(favs):
            fu = _url_key(f.get("url"))
            if fu and fu == pu:
                return j
    for t in (playing.get("title"), playing.get("current_title"),
              vp.get("title")):
        i = lms_active_fav(t or "", favs)
        if i >= 0:
            return i
    if launched_id:
        for j, f in enumerate(favs):
            if f.get("id") == launched_id:
                return j
    return -1


def inject_home_lms_button(config):
    """v2.7.0 : quand LMS est configuré, ajoute une touche « LMS » sur la
    page d'accueil (premier emplacement libre de 1 à 10). Accueil
    complet -> message explicatif (remplacer une touche par l'action
    {"type": "page", "page": "lms"})."""
    if not (config.get("lms") or {}).get("host"):
        return None
    acc = config.get("buttons")
    # v2.11.0 : une touche « LMS » existe déjà -> ne pas en rajouter une
    # (sinon elle squatterait le premier slot libre, p.ex. une touche
    # d'accueil qu'on vient de retirer de la config)
    if isinstance(acc, dict) and any(
            ((e or {}).get("action") or {}).get("type") == "page"
            and ((e or {}).get("action") or {}).get("page") == "lms"
            for e in acc.values()):
        return None
    if not isinstance(acc, dict):
        return None
    for i in range(1, 11):
        if not acc.get(str(i)):
            acc[str(i)] = {"icon": "speaker", "color": "#A5D6A7",
                           "label": "LMS",
                           "action": {"type": "page", "page": "lms"}}
            print(f"[lms] touche LMS ajoutée sur l'accueil (touche {i})")
            return i
    print("[lms] aucune touche libre sur l'accueil : remplace une touche "
          'par {"type": "page", "page": "lms"} pour un accès direct')
    return None


def inject_home_sleep_button(config):
    """v2.14.7 : ajoute une touche « Veille » sur la page d'accueil
    (premier emplacement libre de 1 à 10) — mise en veille du deck,
    réveil par n'importe quel événement. Accueil complet -> message
    explicatif (remplacer une touche par {"type": "sleep"})."""
    acc = config.get("buttons")
    # une touche « sleep » existe déjà -> ne pas en rajouter
    if isinstance(acc, dict) and any(
            ((e or {}).get("action") or {}).get("type") == "sleep"
            for e in acc.values()):
        return None
    if not isinstance(acc, dict):
        return None
    for i in range(1, 11):
        if not acc.get(str(i)):
            acc[str(i)] = {"icon": "bedtime", "color": "#B39DDB",
                           "label": "Veille",
                           "action": {"type": "sleep"}}
            print(f"[veille] touche Veille ajoutée sur l'accueil (touche {i})")
            return i
    print("[veille] aucune touche libre sur l'accueil : remplace une touche "
          'par {"type": "sleep"} pour la mise en veille')
    return None


def lms_item_go(it):
    """(url, cmd[], params[], jouable) d'un élément de menu d'appli LMS.
    Gère le format PLAT (url / cmd / params) et le format « actions » du
    xmlbrowser JSON : {actions: {go: {cmd: [...], params: [...],
    itemsParams: [...]}}} — les commandes et paramètres y sont des
    LISTES qu'il faut transmettre telles quelles au CLI."""
    it = it or {}
    acts = it.get("actions") if isinstance(it.get("actions"), dict) else {}
    go = acts.get("go") if isinstance(acts.get("go"), dict) else {}

    def words(c):
        if isinstance(c, (list, tuple)):
            return [str(x) for x in c if str(x) != ""]
        return str(c or "").split()

    def plist(p):
        if p is None:
            return []
        if isinstance(p, (list, tuple)):
            return [str(x) for x in p if str(x) != ""]
        return [str(p)] if str(p) else []

    url = str(it.get("url") or it.get("weblink") or "")
    cmd = words(it.get("cmd") or go.get("cmd"))
    params = (plist(it.get("params") if it.get("params") is not None
                    else go.get("params"))
              + plist(go.get("itemsParams")))
    typ = str(it.get("type") or "").lower()
    playable = bool(url) and ("audio" in typ or typ in ("", "playlist",
                                                       "track")
                             or bool(it.get("isaudio")))
    return url, cmd, params, playable


def lms_album_view(items, diag=None):
    """Vue « album » d'une liste d'items de navigation : si TOUS les
    items sont des morceaux jouables (url qobuz://... ou autre), renvoie
    {"tracks": [...], "urls": [...]} ; sinon None (navigation normale).
    C'est ce qui transforme le clic sur un album en page album (v2.13.0)
    au lieu de continuer à descendre des répertoires.
    v2.13.4 : si `diag` est un dict, il reçoit l'index et l'item
    BLOQUANT (le premier non jouable hors en-têtes) pour le diagnostic."""
    tracks, urls = [], []
    for _pos, it in enumerate(items or []):
        typ = str(it.get("type") or "").lower()
        if typ in ("text", "header"):
            continue  # en-tête décoratif (xmlbrowser) : pas un morceau
        u, _c, _p, playable = lms_item_go(it)
        if not (playable and u):
            if isinstance(diag, dict):
                diag["index"] = _pos
                diag["item"] = it
            return None
        tracks.append(it)
        urls.append(u)
    return {"tracks": tracks, "urls": urls} if tracks else None


def lms_level_urls(items):
    """URLs de lecture des items jouables d'un niveau de navigation
    (v2.13.5 : « ▶ Jouer l'album » de la zone 3 sur la page morceaux —
    en-têtes ignorés comme dans la détection d'album)."""
    urls = []
    for x in (items or []):
        typ = str(x.get("type") or "").lower()
        if typ in ("text", "header"):
            continue
        u, _c, _p, playable = lms_item_go(x)
        if playable and u:
            urls.append(u)
    return urls


def lms_open_level(vp, it, cmd, params, url, lms, lms_state, lms_lock,
                   switch_page):
    """Ouvre le sous-niveau d'un élément de navigation LMS (v2.13.2) :
    page « album » si le sous-niveau est 100 % jouable ; lecture directe si
    le sous-niveau est VIDE mais que l'élément a une URL de lecture
    (« feuille » du menu, p.ex. un morceau hasitems d'un feed Qobuz) ;
    sinon navigation répertoires normale + diagnostic. Factorise les
    branches cmd/item_id de lms_item_press — testable isolément.
    lms/lms_state/lms_lock/switch_page sont des FERMETURES de run_action :
    ils sont passés explicitement (le helper est module-level)."""
    items = lms.app_items(vp["id"], cmd, params)
    title = str(it.get("name") or it.get("title") or "?")
    diag = {}
    av = lms_album_view(items, diag)
    if av:
        if len(av["tracks"]) == 1:
            # v2.13.4 : un « album » d'UN morceau = en fait un morceau
            # (feed Qobuz : chaque morceau est un dossier de 1 item) ->
            # on le JOUE, pas de page album d'un seul titre.
            lms.play_url(vp["id"], av["urls"][0])
            print(f"[lms] lecture : {title}")
            return True
        with lms_lock:
            lms_state["album"] = {"title": title, "tracks": av["tracks"],
                                  "urls": av["urls"], "sel": 0, "off": 0}
        print(f"[lms] album « {title} » : {len(av['tracks'])} morceaux")
        switch_page("lms_album")
        return True
    if not av and items:
        # v2.13.4 : niveaux « morceaux-répertoires » du feed Qobuz —
        # chaque morceau est un dossier (hasitems + id) contenant
        # exactement 1 item jouable ; l'url est soit directement sur
        # l'item (want_url), soit un cran plus bas (à résoudre).
        # SONDE : si le sous-niveau du 1er item drillable est 1 morceau
        # jouable, c'est une liste de morceaux -> page album complète.
        # Une liste d'ALBUMS (sous-niveau = plusieurs éléments, p.ex.
        # les 100 « Nouveautés ») échoue à la sonde -> navigation.
        cand = all(isinstance(x, dict)
                   and (x.get("hasitems") or (lms_item_go(x)[3]
                                              and lms_item_go(x)[0]))
                   and x.get("id") is not None for x in items)
        if cand and len(items) <= 200:
            def _sub(x):
                p = ([str(a) for a in (params or [])]
                     + [f"item_id:{x['id']}"])
                return lms.app_items(vp["id"], cmd, p)
            first_drill = next((x for x in items if x.get("hasitems")),
                               None)
            sav = (lms_album_view(_sub(first_drill))
                   if first_drill is not None else None)
            if sav and len(sav["tracks"]) == 1:
                urls, ok = [], True
                for x in items:
                    u, _c, _p, playable = lms_item_go(x)
                    if playable and u:
                        urls.append(u)  # url déjà là (want_url)
                        continue
                    s = lms_album_view(_sub(x))
                    if s and s["urls"]:
                        urls.append(s["urls"][0])
                    else:
                        ok = False
                        break
                if ok:
                    with lms_lock:
                        lms_state["album"] = {"title": title,
                                             "tracks": items,
                                             "urls": urls,
                                             "sel": 0, "off": 0}
                    print(f"[lms] album « {title} » : {len(urls)} morceaux "
                          "(URLs résolues)")
                    switch_page("lms_album")
                    return True
                print(f"[lms] album « {title} » : morceaux non résolus, "
                      "navigation normale")
    if not items and url:
        lms.play_url(vp["id"], url)
        print(f"[lms] lecture : {title}")
        return True
    _d = items[0] if items else None
    _b = diag.get("item")
    print("[lms] pas une page album : "
          f"{len(items or [])} él., 1er={str(_d)[:200]}")
    if _b is not None and _b is not _d:
        print(f"[lms] ... bloquant à l'index {diag.get('index')} : "
              f"{str(_b)[:200]}")
    with lms_lock:
        lms_state["browse"].append({"title": title, "items": items,
                                    "cmd": cmd, "params": params})
        lms_state["browse_offset"] = 0
    return True


def player_icon(player):
    """Logo d'un lecteur : tablet pour un Squeezebox Touch (écran tactile),
    radio pour un Squeezebox Radio, speaker sinon."""
    n = (player or {}).get("name", "").lower()
    if "touch" in n:
        return "tablet"
    if "radio" in n:
        return "radio"
    return "speaker"


def player_code(player):
    """Code court d'un lecteur pour le bandeau : « SBT Orange »
    (Squeezebox Touch), « SBR Cuisine » (Squeezebox Radio) — sinon
    le nom court tel quel."""
    n = short_player_name((player or {}).get("name") or "")
    for full, abbr in (("Touch", "SBT"), ("Radio", "SBR")):
        if n.startswith(full):
            rest = n[len(full):].strip()
            return abbr + (" " + rest if rest else "")
    return n


def short_player_name(name):
    """« Squeezebox Touch Orange » → « Touch Orange » (v2.7.0 : le
    préfixe « Touch » est conservé, comme « Radio »). Seuls les préfixes
    génériques « Squeezebox »/« Squeezelite » sont retirés."""
    for pref in ("Squeezebox ", "Squeezelite ", "Squeezelite-"):
        if name.startswith(pref):
            name = name[len(pref):]
            break
    return name.strip() or name


class LMSClient:
    """Client Lyrion Media Server (LMS) via l'API JSON-RPC
    (http://host:9000/jsonrpc.js) — stdlib urllib, aucune dépendance.
    host vide = intégration désactivée."""

    def __init__(self, host, port=9000, timeout=3.0):
        self.url = (f"http://{host}:{int(port)}/jsonrpc.js"
                    if host else None)
        self.timeout = timeout
        self._id = 0
        self._warned = False   # logs de diagnostic favoris déjà émis ?

    @property
    def enabled(self):
        return bool(self.url)

    def request(self, player, command, timeout=None):
        """Appel slim.request ; renvoie le dict 'result' (None si erreur
        ou LMS injoignable)."""
        if not self.url:
            return None
        self._id += 1
        payload = json.dumps({"id": self._id, "method": "slim.request",
                              "params": [player, command]})
        try:
            req = urllib.request.Request(
                self.url, data=payload.encode("utf-8"),
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(
                    req, timeout=timeout or self.timeout) as r:
                data = json.loads(r.read().decode("utf-8"))
            return data.get("result")
        except Exception as e:
            print(f"[lms] requête échouée ({e})")
            return None

    def players(self):
        """Liste des lecteurs : [{id, name, power, volume, playing,
        title, sync_master}] ({} vide si LMS injoignable)."""
        res = self.request("", ["players", 0, 50])
        if not res:
            return []
        out = []
        for p in res.get("players_loop") or []:
            out.append({
                "id": p.get("playerid"),
                "name": p.get("name") or "?",
                "power": bool(int(p.get("power", 0) or 0)),
                "volume": _to_int(p.get("mixer volume"), -1),
                "playing": bool(int(p.get("isplaying", 0) or 0)),
                "title": p.get("current_title") or "",
                "sync_master": bool(int(p.get("issyncmaster", 0) or 0)),
            })
        return out

    @staticmethod
    def _loop_of(res):
        """Boucle d'items d'une réponse favorites : selon la version du
        serveur LMS, la clé s'appelle favorites_loop, loop_loop, itemLoop
        ou items (cf. diagnostic v2.4.2 : certains serveurs renvoient
        loop_loop)."""
        if not isinstance(res, dict):
            return []
        for key in ("favorites_loop", "loop_loop", "itemLoop", "items"):
            v = res.get(key)
            if isinstance(v, list) and v:
                return v
        # boucle générique des navigateurs d'applis (xmlbrowser) :
        # la clé porte le nom de la commande + "_loop" (ex. "qobuz_loop")
        for key, v in (res or {}).items():
            if key.endswith("_loop") and isinstance(v, list) and v:
                return v
        return []

    def _favorites_level(self, folder_id=None):
        """Un niveau de l'arbre des favoris LMS."""
        cmd = ["favorites", "items", 0, 100, "want_url:1"]
        if folder_id:
            cmd.append(f"item_id:{folder_id}")
        res = self.request("", cmd)
        return self._loop_of(res)

    def _favorite_leaves(self, folder_id=None):
        """Feuilles de l'arbre des favoris (descend dans les dossiers)."""
        out = []
        for f in self._favorites_level(folder_id):
            if int(f.get("hasitems", 0) or 0):
                out.extend(self._favorite_leaves(f.get("id")))
            elif f.get("id"):
                out.append({"id": str(f["id"]), "name": f.get("name") or "?",
                            "url": f.get("url") or ""})
        return out

    def _favorites_feed(self):
        """Repli : feedMode=1 renvoie toute la hiérarchie imbriquée
        (chaque niveau porte ses sous-éléments dans « items »)."""
        res = self.request("", ["favorites", "items", 0, 100,
                                "want_url:1", "feedMode:1"])
        out = []

        def walk(items):
            for it in items or []:
                if it.get("items"):
                    walk(it["items"])
                elif it.get("id") and not it.get("hasitems"):
                    out.append({"id": str(it["id"]),
                                "name": it.get("name") or "?",
                                "url": it.get("url") or ""})

        walk(self._loop_of(res))
        return out

    def favorites(self, folder=None):
        """Radios des favoris LMS : [{id, name, url}].
        folder=None : toutes les feuilles de l'arbre (dossiers parcourus).
        folder="Nom" : uniquement le contenu du dossier de favoris « Nom »
        (comparaison insensible à la casse ; introuvable -> arbre complet)."""
        loop = self._favorites_level()
        if folder:
            want = str(folder).strip().lower()
            for f in loop:
                if (int(f.get("hasitems", 0) or 0)
                        and (f.get("name") or "").strip().lower() == want):
                    return self._favorite_leaves(f.get("id"))
            dirs = ", ".join(f.get("name", "?") for f in loop
                             if int(f.get("hasitems", 0) or 0)) or "aucun"
            if not self._warned:
                print(f"[lms] dossier de favoris {folder!r} introuvable "
                      f"(dossiers : {dirs}) — tout l'arbre est utilisé")
        leaves = self._favorite_leaves()
        if not leaves:
            # certains serveurs ne renvoient pas la liste plate : on tente
            # l'arborescence imbriquée (feedMode=1)
            leaves = self._favorites_feed()
        if not leaves and not self._warned:
            # plus rien à tenter : on logge UNE SEULE FOIS la réponse
            # BRUTE du serveur (favorites() est rappelé par le poll de
            # 2 s tant que la liste est vide — sans flag, log infini)
            self._warned = True
            try:
                res = self.request("", ["favorites", "items", 0, 100])
                print("[lms] diagnostic — réponse favorites items : "
                      + json.dumps(res, ensure_ascii=False)[:400])
            except Exception as e:
                print(f"[lms] diagnostic favoris impossible : {e}")
        return leaves

    def power_all(self, on):
        """Allume ou éteigne tous les lecteurs."""
        for p in self.players():
            self.request(p["id"], ["power", "1" if on else "0"])

    def power(self, player, on):
        self.request(player, ["power", "1" if on else "0"])

    def volume(self, player, delta):
        """Volume relatif (ex. +5 / -5) du lecteur."""
        self.request(player, ["mixer", "volume", f"{int(delta):+d}"])

    def mute_toggle(self, player):
        self.request(player, ["mixer", "muting", "toggle"])

    def volume_state(self, player):
        """Volume absolu du lecteur (0-100), None si LMS ne répond pas.
        La requête « players » ne renvoie PAS « mixer volume » : il faut
        interroger « mixer volume ? » (réponse {«_volume»: «55»})."""
        res = self.request(player, ["mixer", "volume", "?"])
        if isinstance(res, dict):
            if "_volume" in res:
                return _to_int(res["_volume"], None)
            for v in res.values():
                iv = _to_int(v, None)
                if iv is not None and 0 <= iv <= 100:
                    return iv
        return None

    def mute_state(self, player):
        """État muet du lecteur (False si LMS ne répond pas)."""
        res = self.request(player, ["mixer", "muting", "?"])
        if isinstance(res, dict):
            for v in res.values():
                if str(v) in ("0", "1"):
                    return str(v) == "1"
        return False

    def playing_info(self, player):
        """Champs du flux en cours sur le lecteur : {url, title,
        current_title}. Permet d'identifier la radio active MÊME AU
        DÉMARRAGE. On lit playlist_loop[0] ET les champs racine (selon
        la version du serveur, l'un ou l'autre est renseigné)."""
        res = self.request(player, ["status", "0", "1"])
        if not isinstance(res, dict):
            return None
        loop = res.get("playlist_loop") or []
        it = loop[0] if loop else {}
        return {"url": str(it.get("url") or res.get("url") or ""),
                "title": str(it.get("title") or res.get("title") or ""),
                "current_title": str(res.get("current_title")
                                     or it.get("current_title") or ""),
                # v2.13.8 : position dans la liste en cours (1-based) et
                # total des pistes — « 1/12 » sur la zone 3 du bandeau
                "cur": _to_int(res.get("playlist_cur"), -1) + 1,
                "tracks": _to_int(res.get("playlist_tracks"), 0),
                "mode": str(res.get("mode") or "")}

    def mode(self, player):
        """Mode du lecteur : 'play', 'pause' ou 'stop' ('' si injoignable)
        — v2.13.9 : tap zone 3 = pause/reprise pendant la lecture."""
        res = self.request(player, ["status", "0", "1"])
        return str(res.get("mode") or "") if isinstance(res, dict) else ""

    def playing_track(self, player):
        """v2.14.1 : piste EN COURS du lecteur : {url, title,
        current_title, cur (1-based), tracks, mode}. Différence avec
        playing_info : « status - 1 » part de la piste COURANTE (« - »)
        et non de la 1re de la liste, et demande l'URL (tags u) — sans
        ça, impossible de savoir si l'album affiché est celui qui joue.
        La position (playlist_cur) manque chez certains serveurs ->
        fallback « playlist index ? » (0-based)."""
        res = self.request(player, ["status", "-", "1", "tags:u"])
        if not isinstance(res, dict):
            return None
        loop = res.get("playlist_loop") or []
        it = loop[0] if loop else {}
        cur = _to_int(res.get("playlist_cur"), -1)
        if cur < 0:
            r2 = self.request(player, ["playlist", "index", "?"])
            if isinstance(r2, dict):
                for v in (r2.get("_index"), r2.get("index"),
                          r2.get("playlist_cur")):
                    cur = _to_int(v, -1)
                    if cur >= 0:
                        break
        return {"url": str(it.get("url") or res.get("url") or ""),
                "title": str(it.get("title") or res.get("title") or ""),
                "current_title": str(res.get("current_title") or ""),
                "cur": cur + 1,
                "tracks": _to_int(res.get("playlist_tracks"), 0),
                "mode": str(res.get("mode") or "")}

    def now_info(self, player):
        """v2.19.0 : titre + artiste de la piste en cours, pour le bandeau.
        Une seule requête « status - 1 » avec le tag artiste ; appelée
        UNIQUEMENT quand le titre change (une fois par morceau) pour ne
        pas alourdir le poll de 2 s."""
        res = self.request(player, ["status", "-", "1", "tags:uA"])
        if not isinstance(res, dict):
            return (None, None)
        loop = res.get("playlist_loop") or []
        it = loop[0] if loop else {}
        title = str(res.get("current_title")
                    or it.get("title") or res.get("title") or "")
        artist = str(it.get("artist")
                     or it.get("track_artist")
                     or res.get("artist") or "")
        # v2.19.2 : webradio — le « title » de la piste est le NOM DU FLUX
        # (ex. « FIP (MP3) ») ; les infos live (métadonnées ICY) arrivent
        # dans « current_title », souvent « Artiste - Titre ». On les
        # décode pour afficher le morceau réellement diffusé.
        _url = str(it.get("url") or res.get("url") or "")
        # v2.19.5 : un favori radio joué via un plugin n'a PAS une URL
        # http simple (schéma tunein/favoris, ou vide) — on élargit :
        # URL « :// » non-fichier, ou champ « remote » du status = 1
        _flux = (bool(_url) and "://" in _url
                 and not _url.startswith(("file://", "file:")))
        _flux = (_flux or _to_int(res.get("remote"), 0) == 1)
        if _flux:
            # v2.19.8 : ordre de priorité des sources live — certains
            # serveurs (dump réel v2.19.7 de David) mettent le NOM DE LA
            # STATION dans current_title et le morceau live dans
            # remoteMeta ; current_title ne doit plus écraser remoteMeta.
            # ① remoteMeta (title/track + artist)
            # ② current_title s'il diffère du titre de piste
            # ③ titre de piste
            _rm = res.get("remoteMeta")
            _rmt = ""
            if isinstance(_rm, dict):
                artist = (str(_rm.get("artist") or "").strip()
                          or artist)
                _rmt = str(_rm.get("title") or _rm.get("track")
                           or "").strip()
            _ct = str(res.get("current_title") or "").strip()
            _pt = str(it.get("title") or "").strip()
            # remoteMeta PRÉSENT = source live (le titre de piste peut
            # aussi porter le morceau live, comme current_title peut
            # porter le nom de station : seul remoteMeta est fiable ici)
            if _rmt:
                title = _rmt
            elif _ct and _ct != _pt:
                if " - " in _ct and not artist:
                    _a, _t = _ct.split(" - ", 1)
                    artist, title = _a.strip(), _t.strip()
                else:
                    title = _ct
            # v2.19.3 : « track » top-level = parfois le morceau live
            title = (str(res.get("track") or "").strip()
                     or title)
        return ((title.strip() or None) and title[:80],
                (artist.strip() or None) and artist[:60])

    def play_url(self, player, url):
        """Joue une URL (webradio) sur le lecteur (l'allume au passage)."""
        self.request(player, ["power", "1"])
        self.request(player, ["playlist", "play", url])

    def playpause(self, player, playing):
        """Pause si en lecture, reprise sinon."""
        self.request(player, ["pause", "1"] if playing else ["play"])

    def play_favorite(self, player, fav_id):
        """Joue un favori (radio) sur le lecteur (l'allume au passage)."""
        self.request(player, ["power", "1"])
        # commande LMS correcte : « favorites playlist play item_id:<id> »
        # (« favorites play » n'existe pas -> le serveur ferme la connexion ;
        #  sans le préfixe item_id:, l'id est ignoré et le PREMIER favori
        #  est joué à la place)
        self.request(player, ["favorites", "playlist", "play",
                              f"item_id:{fav_id}"])

    def apps(self, player=None):
        """Applis installées sur le serveur : interroge « apps » PUIS
        « radios » (certaines versions y rangent Radio Paradise), sans
        lecteur puis avec (certaines versions exigent un contexte
        lecteur) — [{cmd, name}] dédupliqué, analyse tolérante."""
        out, seen = [], set()

        def absorb(res):
            if isinstance(res, dict):
                loops = [v for k, v in res.items()
                         if (k.endswith("_loop") or k == "items")
                         and isinstance(v, list)]
            elif isinstance(res, list):
                loops = [res]
            else:
                return
            for loop in loops:
                for a in loop:
                    if not isinstance(a, dict):
                        continue
                    cmd = a.get("cmd") or a.get("go") or ""
                    if not cmd or cmd in seen:
                        continue
                    seen.add(cmd)
                    out.append({"cmd": str(cmd),
                                "name": str(a.get("name")
                                            or a.get("title") or cmd),
                                "params": a.get("params")})

        # contexte lecteur puis global (certaines versions exigent l'un
        # ou l'autre) — dédoublonné via `seen`
        for pl in (([player] if player else []) + [""]):
            for q in (["apps", 0, 100], ["radios", 0, 100]):
                absorb(self.request(pl, q))
                if out:
                    return out
        return out

    def apps_raw(self, player=""):
        """Réponse brute de « apps 0 100 » (diagnostic)."""
        return self.request(player, ["apps", 0, 100])

    def app_items(self, player, cmd, params=None, start=0, count=100):
        """Un niveau de navigation d'une appli LMS (xmlbrowser) :
        [player] <cmd...> items <start> <count> [params:...].
        Essaie AVEC les params de la découverte puis SANS (les plugins
        ne les interprètent pas tous) — délai allongé à 10 s (les
        plugins interrogent parfois des API distantes) + diagnostic si
        le niveau reste vide."""
        words = list(cmd) if isinstance(cmd, (list, tuple)) \
            else str(cmd).split()
        # LE mot-clé « items » est OBLIGATOIRE : sans lui la commande
        # est invalide et le serveur ferme la connexion (bug v2.8.0-2.8.2 :
        # ['radioparadise', '0', '100'] au lieu de [..., 'items', '0', '100'])
        if "items" not in words:
            words = words + ["items"]
        # want_url:1 (v2.13.2) : demande à LMS l'URL de LECTURE de chaque
        # item (playlist play <url>) — sans elle, les feeds Qobuz renvoient
        # des morceaux SANS url (isaudio=1 mais rien à jouer) ; les tags
        # inconnus sont ignorés par les plugins qui ne le gèrent pas.
        base = ([str(w) for w in words]
                + [str(start), str(count), "want_url:1"])
        if params is None:
            plist_ = []
        elif isinstance(params, (list, tuple)):
            plist_ = [str(p) for p in params if str(p) != ""]
        else:
            plist_ = [str(params)] if str(params) else []
        attempts = ([base + plist_] if plist_ else []) + [base]
        res = None
        for c in attempts:
            res = self.request(player, c, timeout=10.0)
            items = self._loop_of(res)
            if items:
                return items
        print(f"[lms] diagnostic navigation — {c!r} -> {str(res)[:400]}")
        return []

    def sync_all(self, master):
        """Synchronise tous les lecteurs sur <master>."""
        for p in self.players():
            if p["id"] != master:
                self.request(p["id"], ["sync", master])

    def desync_all(self):
        """Désynchronise tous les lecteurs."""
        for p in self.players():
            self.request(p["id"], ["sync", "-"])


def get_foreground_app():
    """Nom (minuscule) de l'exécutable de la fenêtre au premier plan.
    Windows uniquement, stdlib ctypes ; None si indisponible."""
    try:
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return None
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        kernel32 = ctypes.windll.kernel32
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        h = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION,
                                 False, pid)
        if not h:
            return None
        try:
            buf = ctypes.create_unicode_buffer(1024)
            size = wintypes.DWORD(len(buf))
            if not kernel32.QueryFullProcessImageNameW(h, 0, buf,
                                                       ctypes.byref(size)):
                return None
            return os.path.basename(buf.value or "").lower() or None
        finally:
            kernel32.CloseHandle(h)
    except Exception:
        return None


def run_action(action, device):
    if not action:
        return
    t = action.get("type")
    if t == "open":
        subprocess.Popen([action["path"]] + action.get("args", []))
    elif t == "url":
        webbrowser.open(action["url"])
    elif t == "keys":
        send_keys(action.get("keys", []))
    elif t == "text":
        type_text(action.get("text", ""))
    elif t == "run":
        subprocess.Popen([action["cmd"]] + action.get("args", []),
                         shell=action.get("shell", False))
    elif t == "volume":
        send_keys([{"up": "volume_up", "down": "volume_down",
                    "mute": "volume_mute"}[action["dir"]]])
    elif t == "mediaplay":
        send_keys(["play_pause"])
    elif t == "medianext":
        send_keys(["next"])
    elif t == "mediaprev":
        send_keys(["prev"])
    elif t == "mediastop":
        send_keys(["stop"])
    elif t == "clock":
        pass  # touche horloge : purement visuelle, rafraîchie par poll_clock
    elif t == "page":
        # bascule vers une autre page de profils (voir "pages" dans la config)
        cb = getattr(device, "on_page_change", None)
        if cb:
            cb(action.get("page"))
        else:
            print("Pas de \"pages\" dans la config : action page ignorée.")
    elif t == "sysvolume":
        # volume système Windows réel (pycaw) ; retombe sur les touches média
        d = action.get("dir", "up")
        if _HAS_PYCAW:
            try:
                if d == "mute":
                    set_mute(not get_mute())
                else:
                    step = action.get("step", 5)
                    set_volume_pct(get_volume_pct()
                                   + (step if d == "up" else -step))
            except Exception as e:
                print(f"Volume système indisponible : {e}")
        else:
            send_keys([{"up": "volume_up", "down": "volume_down",
                        "mute": "volume_mute"}[d]])
        refresh = getattr(device, "on_strip_refresh", None)
        if refresh:
            refresh()
    elif t == "brightness":
        step = action.get("step", 10)
        device.set_brightness(device.brightness
                              + (step if action["dir"] == "up" else -step))
    elif t == "brightness_toggle":
        # appui sur le knob : éteint tout / rallume au dernier niveau
        if device.brightness == 0:
            device.set_brightness(getattr(device, "_last_bright", DEFAULT_BRIGHTNESS))
        else:
            device._last_bright = device.brightness
            device.set_brightness(0)
    elif t == "sleep":
        # v2.14.7-2.14.9 : veille complète du deck — luminosité 0 (le
        # keepalive la maintient) + mémoires d'écran vidées (CLE) + AUCUN
        # repeint pendant la veille ; handle() réveille à la première
        # PRESSION (le relâchement de la touche Veille reste absorbé),
        # restaure la luminosité et repeint page + bandeau
        if device.brightness:
            device._last_bright = device.brightness
        device._sleeping = True
        device.set_brightness(0)
        # v2.14.9 : on vide AUSSI les mémoires d'écran (touches + bandeau
        # tactile) : rétroéclairage éteint ET écrans noirs, rien ne traîne
        try:
            with device.lock:
                device._send(crt_command("CLE", [0, 0, 0, 0xFF]))
                device._send(crt_command("STP"))
        except Exception:
            pass
        print("[veille] écrans éteints — appuie sur une touche "
              "pour réveiller le deck")
    elif t == "zoom":
        # zoom Ctrl+molette de la fenêtre active (knob 3 par défaut)
        d = action.get("dir", "in")
        if d == "reset":
            send_keys(["ctrl", "0"])
        else:
            zoom_wheel(1 if d == "in" else -1, action.get("step", 2))
    else:
        print(f"Type d'action inconnu : {t}")

DEFAULT_CONFIG = {
  "brightness": 30,
  "auto_pages": {
    "qobuz": "qobuz",
    "spotify": "qobuz",
    "vlc": "qobuz",
    "hwinfo64": "hardware"
  },
  "lms": {
    "host": "",
    "port": 9000,
    "folder": "",
    "radios": [],
    "radio_paradise_url": "http://stream.radioparadise.com/aac-320"
  },
  "vu_meter": {
    "enabled": True,
    "fps": 12
  },
  "buttons": {
    "1": {
      "icon": "terminal",
      "color": "#80CBC4",
      "label": "CMD",
      "action": {
        "type": "run",
        "cmd": "cmd"
      }
    },
    "2": {
      "icon": "description",
      "color": "#9FA8DA",
      "label": "Notepad",
      "action": {
        "type": "open",
        "path": "notepad.exe"
      }
    },
    "3": {
      "icon": "public",
      "color": "#90CAF9",
      "label": "Web",
      "action": {
        "type": "url",
        "url": "https://github.com"
      }
    },
    "5": {
      "action": {
        "type": "clock",
        "color": "#81D4FA"
      }
    }
  },
  "encoders": {
    "encoder_1_cw": {
      "action": {
        "type": "sysvolume",
        "dir": "up",
        "step": 5
      }
    },
    "encoder_1_ccw": {
      "action": {
        "type": "sysvolume",
        "dir": "down",
        "step": 5
      }
    },
    "encoder_1_button": {
      "action": {
        "type": "sysvolume",
        "dir": "mute"
      }
    },
    "encoder_4_cw": {
      "action": {
        "type": "brightness",
        "dir": "up",
        "step": 10
      }
    },
    "encoder_4_ccw": {
      "action": {
        "type": "brightness",
        "dir": "down",
        "step": 10
      }
    },
    "encoder_4_button": {
      "action": {
        "type": "brightness_toggle"
      }
    },
    "encoder_2_cw": {
      "action": {
        "type": "page",
        "page": "next"
      }
    },
    "encoder_2_ccw": {
      "action": {
        "type": "page",
        "page": "prev"
      }
    }
  },
  "pages": {
    "minuteurs": {
      "label": "Minuteur",
      "icon": "timer",
      "color": "#FFCC80",
      "buttons": {
        "1": {
          "label": "1 min",
          "action": {
            "type": "timer",
            "minutes": 1
          }
        },
        "2": {
          "label": "2 min",
          "action": {
            "type": "timer",
            "minutes": 2
          }
        },
        "3": {
          "label": "5 min",
          "action": {
            "type": "timer",
            "minutes": 5
          }
        },
        "4": {
          "label": "10 min",
          "action": {
            "type": "timer",
            "minutes": 10
          }
        },
        "5": {
          "label": "20 min",
          "action": {
            "type": "timer",
            "minutes": 20
          }
        },
        "6": {
          "label": "30 min",
          "action": {
            "type": "timer",
            "minutes": 30
          }
        },
        "7": {
          "label": "Régl.",
          "action": {
            "type": "timer",
            "minutes": 0
          }
        },
        "8": {
          "label": "Chrono",
          "action": {
            "type": "stopwatch"
          }
        }
      },
      "encoders": {
        "encoder_1_cw": {
          "action": {
            "type": "sysvolume",
            "dir": "up",
            "step": 5
          }
        },
        "encoder_1_ccw": {
          "action": {
            "type": "sysvolume",
            "dir": "down",
            "step": 5
          }
        },
        "encoder_1_button": {
          "action": {
            "type": "sysvolume",
            "dir": "mute"
          }
        },
        "encoder_4_cw": {
          "action": {
            "type": "brightness",
            "dir": "up",
            "step": 10
          }
        },
        "encoder_4_ccw": {
          "action": {
            "type": "brightness",
            "dir": "down",
            "step": 10
          }
        },
        "encoder_4_button": {
          "action": {
            "type": "brightness_toggle"
          }
        },
        "encoder_2_cw": {
          "action": {
            "type": "page",
            "page": "next"
          }
        },
        "encoder_2_ccw": {
          "action": {
            "type": "page",
            "page": "prev"
          }
        },
        "encoder_3_cw": {
          "action": {
            "type": "timer_adjust",
            "dir": "up"
          }
        },
        "encoder_3_ccw": {
          "action": {
            "type": "timer_adjust",
            "dir": "down"
          }
        },
        "encoder_3_button": {
          "action": {
            "type": "timer_start"
          }
        }
      }
    },
    "raccourcis": {
      "label": "Raccourcis",
      "icon": "keyboard",
      "color": "#9FA8DA",
      "buttons": {
        "1": {
          "icon": "content_copy",
          "color": "#90CAF9",
          "label": "Ctrl C",
          "action": {
            "type": "keys",
            "keys": ["ctrl", "c"]
          }
        },
        "2": {
          "icon": "content_paste",
          "color": "#90CAF9",
          "label": "Ctrl V",
          "action": {
            "type": "keys",
            "keys": ["ctrl", "v"]
          }
        },
        "3": {
          "icon": "content_cut",
          "color": "#90CAF9",
          "label": "Ctrl X",
          "action": {
            "type": "keys",
            "keys": ["ctrl", "x"]
          }
        },
        "4": {
          "icon": "select_all",
          "color": "#A5D6A7",
          "label": "Ctrl A",
          "action": {
            "type": "keys",
            "keys": ["ctrl", "a"]
          }
        },
        "5": {
          "icon": "format_bold",
          "color": "#FFF59D",
          "label": "Gras",
          "action": {
            "type": "keys",
            "keys": ["ctrl", "b"]
          }
        },
        "6": {
          "icon": "format_italic",
          "color": "#FFF59D",
          "label": "Italique",
          "action": {
            "type": "keys",
            "keys": ["ctrl", "i"]
          }
        },
        "7": {
          "icon": "format_underlined",
          "color": "#FFF59D",
          "label": "Souligné",
          "action": {
            "type": "keys",
            "keys": ["ctrl", "u"]
          }
        },
        "8": {
          "icon": "photo_camera",
          "color": "#CE93D8",
          "label": "Impr écr",
          "action": {
            "type": "keys",
            "keys": ["printscreen"]
          }
        },
        "9": {
          "icon": "cancel",
          "color": "#EF9A9A",
          "label": "Esc",
          "action": {
            "type": "keys",
            "keys": ["esc"]
          }
        },
        "10": {
          "icon": "undo",
          "color": "#80CBC4",
          "label": "Annuler",
          "action": {
            "type": "keys",
            "keys": ["ctrl", "z"]
          }
        }
      },
      "encoders": {
        "encoder_1_cw": {
          "action": {
            "type": "sysvolume",
            "dir": "up",
            "step": 5
          }
        },
        "encoder_1_ccw": {
          "action": {
            "type": "sysvolume",
            "dir": "down",
            "step": 5
          }
        },
        "encoder_1_button": {
          "action": {
            "type": "sysvolume",
            "dir": "mute"
          }
        },
        "encoder_4_cw": {
          "action": {
            "type": "brightness",
            "dir": "up",
            "step": 10
          }
        },
        "encoder_4_ccw": {
          "action": {
            "type": "brightness",
            "dir": "down",
            "step": 10
          }
        },
        "encoder_4_button": {
          "action": {
            "type": "brightness_toggle"
          }
        },
        "encoder_2_cw": {
          "action": {
            "type": "page",
            "page": "next"
          }
        },
        "encoder_2_ccw": {
          "action": {
            "type": "page",
            "page": "prev"
          }
        }
      }
    },
    "qobuz": {
      "label": "Qobuz",
      "buttons": {
        "1": {
          "icon": "play_arrow",
          "color": "#A5D6A7",
          "bg": "#1b2e1b",
          "label": "Play",
          "action": {
            "type": "mediaplay"
          }
        },
        "2": {
          "icon": "skip_next",
          "color": "#A5D6A7",
          "bg": "#1b2e1b",
          "label": "Suiv.",
          "action": {
            "type": "medianext"
          }
        },
        "3": {
          "icon": "skip_previous",
          "color": "#A5D6A7",
          "bg": "#1b2e1b",
          "label": "Prec.",
          "action": {
            "type": "mediaprev"
          }
        },
        "4": {
          "icon": "volume_off",
          "color": "#EF9A9A",
          "bg": "#331b1b",
          "label": "Mute",
          "action": {
            "type": "sysvolume",
            "dir": "mute"
          }
        }
      },
      "encoders": {
        "encoder_1_cw": {
          "action": {
            "type": "sysvolume",
            "dir": "up",
            "step": 5
          }
        },
        "encoder_1_ccw": {
          "action": {
            "type": "sysvolume",
            "dir": "down",
            "step": 5
          }
        },
        "encoder_1_button": {
          "action": {
            "type": "sysvolume",
            "dir": "mute"
          }
        },
        "encoder_4_cw": {
          "action": {
            "type": "brightness",
            "dir": "up",
            "step": 10
          }
        },
        "encoder_4_ccw": {
          "action": {
            "type": "brightness",
            "dir": "down",
            "step": 10
          }
        },
        "encoder_4_button": {
          "action": {
            "type": "brightness_toggle"
          }
        },
        "encoder_2_cw": {
          "action": {
            "type": "page",
            "page": "next"
          }
        },
        "encoder_2_ccw": {
          "action": {
            "type": "page",
            "page": "prev"
          }
        }
      },
      "icon": "music_note",
      "color": "#81D4FA"
    },
    "hardware": {
      "label": "Hardware",
      "icon": "monitor_heart",
      "color": "#FFB74D",
      "refresh": 2,
      "thresholds": [
        70,
        85
      ],
      "buttons": {
        "1": {
          "hw": "CPU Package",
          "label": "CPU",
          "icon": "device_thermostat",
          "color": "#FF8A65"
        },
        "2": {
          "hw": "GPU Core Temperature",
          "label": "iGPU",
          "icon": "device_thermostat",
          "color": "#CE93D8"
        },
        "3": {
          "hw": "GPU Temperature",
          "label": "dGPU",
          "icon": "device_thermostat",
          "color": "#B39DDB"
        },
        "4": {
          "hw": "PCH Temperature",
          "label": "PCH",
          "icon": "device_thermostat",
          "color": "#80DEEA"
        },
        "5": {
          "hw": "Total CPU Usage",
          "label": "CPU %",
          "icon": "speed",
          "color": "#90CAF9"
        },
        "6": {
          "hw": ["C:]", "Drive Temperature"],
          "label": "SSD C:",
          "icon": "save",
          "color": "#80DEEA"
        },
        "7": {
          "hw": ["E:", "Drive Temperature"],
          "label": "SSD E:",
          "icon": "save",
          "color": "#4DD0E1"
        }
      },
      "encoders": {
        "encoder_1_cw": {
          "action": {
            "type": "sysvolume",
            "dir": "up",
            "step": 5
          }
        },
        "encoder_1_ccw": {
          "action": {
            "type": "sysvolume",
            "dir": "down",
            "step": 5
          }
        },
        "encoder_1_button": {
          "action": {
            "type": "sysvolume",
            "dir": "mute"
          }
        },
        "encoder_4_cw": {
          "action": {
            "type": "brightness",
            "dir": "up",
            "step": 10
          }
        },
        "encoder_4_ccw": {
          "action": {
            "type": "brightness",
            "dir": "down",
            "step": 10
          }
        },
        "encoder_4_button": {
          "action": {
            "type": "brightness_toggle"
          }
        },
        "encoder_2_cw": {
          "action": {
            "type": "page",
            "page": "next"
          }
        },
        "encoder_2_ccw": {
          "action": {
            "type": "page",
            "page": "prev"
          }
        }
      }
    }
  },
  "label": "Accueil",
  "icon": "home",
  "color": "#80CBC4"
}

CONFIG_PATH = os.path.join(_APP_BASE, "akp05e_config.json")

def load_config():
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
        print(f"Config par défaut créée : {CONFIG_PATH}")
        return DEFAULT_CONFIG
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# ---------------------------------------------------------------------------
# Configuration assistée LMS (--setup-lms) — v2.12.0
# ---------------------------------------------------------------------------
_RE_LMS_IPAD = re.compile(r"IPAD:(\d{1,3}(?:\.\d{1,3}){3})")
_RE_LMS_JSONPORT = re.compile(r"JSON:(\d+)")

def lms_discover(timeout=3.0):
    """Découverte des serveurs Lyrion Media Server sur le réseau local.
    Protocole officiel Squeezebox : un datagramme « e » en broadcast UDP
    sur le port 3483 ; chaque serveur répond avec son adresse (IPAD:)
    et son port JSON (JSON:) — ou, pour les LMS modernes,
    un simple « E » dont l'adresse du serveur est l'IP émettrice du
    datagramme. Renvoie une liste [(ip, port)] uniques.
    Retour de secours : liste vide si aucun serveur ou pas de réseau.

    v2.12.1 : le broadcast général 255.255.255.255 est souvent filtré
    (box, pare-feu Windows) — on émet AUSSI en broadcast dirigé vers le
    sous-réseau local (p.ex. 192.168.1.255, calculé depuis l'IP locale),
    en 3 salves espacées, pour laisser le temps au serveur de répondre."""
    out, seen = [], set()
    sock = None
    try:
        # broadcast dirigé du sous-réseau local (aucun trafic réel envoyé :
        # connect() sur une adresse extérieure sert juste à déterminer
        # l'interface/adresse IP locale utilisée par défaut)
        bcast_subnet = None
        try:
            _s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            _s.connect(("10.255.255.255", 1))
            _ip = _s.getsockname()[0]
            _s.close()
            if _ip and not _ip.startswith("127."):
                bcast_subnet = _ip.rsplit(".", 1)[0] + ".255"
        except Exception:
            bcast_subnet = None
        targets = [("255.255.255.255", 3483)]
        if bcast_subnet and bcast_subnet not in ("0.0.0.255",
                                                 "255.255.255.255"):
            targets.append((bcast_subnet, 3483))
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(0.3)
        end = time.time() + timeout
        while time.time() < end:
            for tgt in targets:
                try:
                    sock.sendto(b"e", tgt)
                except Exception:
                    pass
            # écoute ~1 s (salves), puis on re-émet jusqu'au timeout
            sub_end = min(time.time() + 1.0, end)
            while time.time() < sub_end:
                try:
                    data, _addr = sock.recvfrom(2048)
                except socket.timeout:
                    break
                except OSError:
                    break
                txt = data.decode("latin-1", "ignore")
                mip = _RE_LMS_IPAD.search(txt)
                if mip:
                    ip = mip.group(1)
                else:
                    # LMS modernes : la réponse est un simple "E" (les "e"
                    # émis par les lecteurs sont ignorés) — l'adresse du
                    # serveur est l'IP ÉMETTRICE du datagramme.
                    if data[:1] != b"E":
                        continue
                    ip = _addr[0]
                mp = _RE_LMS_JSONPORT.search(txt)
                port = int(mp.group(1)) if mp else 9000
                if (ip, port) not in seen:
                    seen.add((ip, port))
                    out.append((ip, port))
            if out:
                break  # premier serveur trouvé : assez
    except Exception as e:
        print(f"[lms] découverte réseau impossible : {e}")
    finally:
        if sock:
            try:
                sock.close()
            except Exception:
                pass
    return out

def lms_check_server(host, port=9000):
    """Vérifie qu'un serveur LMS répond à cette adresse (compte les
    lecteurs). Renvoie (True, nb_lecteurs) si joignable, sinon
    (False, message)."""
    cli = LMSClient(host, port, timeout=3.0)
    res = cli.request("", ["players", 0, 50])
    if res is None:
        return False, "sans réponse"
    return True, len(res.get("players_loop") or [])

def run_setup_lms(config, _input=input):
    """Assistant --setup-lms : état actuel, découverte réseau, choix
    (Entrée = accepter le serveur détecté), vérification, puis
    enregistrement dans akp05e_config.json. L'application continue
    ensuite son démarrage avec la nouvelle configuration."""
    print("\n=== Configuration Lyrion Media Server (LMS) ===")
    lms_cfg = config.get("lms")
    if not isinstance(lms_cfg, dict):
        lms_cfg = dict(DEFAULT_CONFIG.get("lms") or {})
        config["lms"] = lms_cfg
    cur = lms_cfg.get("host") or ""
    if cur:
        ok, info = lms_check_server(cur, lms_cfg.get("port", 9000))
        st = f"OK ({info} lecteurs)" if ok else str(info)
        print(f"Serveur actuel : {cur}:{lms_cfg.get('port', 9000)} — {st}")
    print("Recherche d'un serveur Lyrion sur le réseau local (~3 s)...")
    found = lms_discover()
    valid = []
    for ip, port in found:
        ok, info = lms_check_server(ip, port)
        st = f"OK ({info} lecteurs)" if ok else str(info)
        print(f"  trouvé : {ip}:{port} — {st}")
        if ok:
            valid.append((ip, port))
    choice = ""
    if valid:
        d_ip, d_port = valid[0]
        raw = _input(f"Utiliser {d_ip}:{d_port} ? "
                     "(Entrée = oui, sinon autre IP ou IP:port) : ").strip()
        choice = raw or d_ip
    else:
        choice = _input("Aucun serveur détecté. Adresse IP du serveur LMS "
                        "(ex. 192.168.1.24 ou vide pour annuler) : ").strip()
    if not choice:
        print("Configuration inchangée.")
        return
    host = choice
    port = 9000
    if ":" in choice:
        host, _, ps = choice.partition(":")
        if ps.strip().isdigit():
            port = int(ps.strip())
    ok, info = lms_check_server(host, port)
    if not ok:
        print(f"  {host}:{port} ne répond pas ({info}) — configuration "
              "inchangée.")
        return
    lms_cfg["host"] = host
    lms_cfg["port"] = port
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"✔ Serveur Lyrion enregistré : {host}:{port} "
              f"({info} lecteurs) dans {os.path.basename(CONFIG_PATH)}")
    except Exception as e:
        print(f"Impossible d'enregistrer la config ({e}) — l'adresse "
              f"{host}:{port} reste active pour cette session.")

# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Icône systray (v2.16.0) — ctypes pur, zéro dépendance
# ---------------------------------------------------------------------------

_TRAY_MSG = 0x8000 + 1                      # message de rappel de l'icône
_NIM_ADD, _NIM_MODIFY, _NIM_DELETE = 0, 1, 2
_NIF_MESSAGE, _NIF_ICON, _NIF_TIP = 0x01, 0x02, 0x04
_TPM_RETURNCMD, _TPM_NONOTIFY, _TPM_RIGHTBUTTON = 0x0100, 0x0080, 0x0002
_WM_RBUTTONUP, _WM_LBUTTONDBLCLK = 0x0205, 0x0203
_WM_QUIT = 0x0012
_MENU_ID_BASE = 7000
_TRAY_SIZE = 32                             # icône 32x32 (32bpp BGRA)

# types Win32 locaux : certains wintypes ne définissent pas HCURSOR /
# HINSTANCE selon la plateforme ; on n'en dépend pas (app = Windows,
# tests = partout).
T_DWORD, T_UINT, T_LONG = ctypes.c_ulong, ctypes.c_uint, ctypes.c_long
T_HANDLE, T_HICON = ctypes.c_void_p, ctypes.c_void_p
T_LPCWSTR, T_BOOL = ctypes.c_wchar_p, ctypes.c_int
T_WPARAM, T_LPARAM = ctypes.c_size_t, ctypes.c_ssize_t
# WINFUNCTYPE n'existe que sur Windows : les tests hors Windows
# retombennent sur CFUNCTYPE (le callback n'y est jamais appelé)
WINFUNCTYPE = getattr(ctypes, "WINFUNCTYPE", ctypes.CFUNCTYPE)


def _tray_set_prototypes():
    """v2.16.3 : sans argtypes/restype, ctypes convertit tout en int 32
    bits — les lParam (pointeurs 64 bits) débordent (« int too long to
    convert ») et les handles retournés (HWND/HMENU/HICON) sont tronqués.
    On déclare les signatures réelles des APIs du tray."""
    try:
        user32.DefWindowProcW.argtypes = [T_HANDLE, T_UINT, T_WPARAM,
                                          T_LPARAM]
        user32.DefWindowProcW.restype = ctypes.c_ssize_t
        user32.CreateWindowExW.argtypes = [
            T_UINT, T_LPCWSTR, T_LPCWSTR, T_UINT,          # exStyle, class,
            ctypes.c_int, ctypes.c_int,                   # titre, style,
            ctypes.c_int, ctypes.c_int,                   # x, y, L, H,
            T_HANDLE, T_HANDLE, T_HANDLE, T_HANDLE]       # parent, menu,
        user32.CreateWindowExW.restype = T_HANDLE
        user32.CreatePopupMenu.restype = T_HANDLE
        user32.CreateIconIndirect.restype = T_HICON
        user32.RegisterWindowMessageW.restype = T_UINT
        user32.GetMessageW.restype = ctypes.c_int
        user32.TrackPopupMenu.argtypes = [T_HANDLE, T_UINT, ctypes.c_int,
                                          ctypes.c_int, ctypes.c_int,
                                          T_HANDLE, T_HANDLE]
        user32.TrackPopupMenu.restype = ctypes.c_int
        user32.AppendMenuW.argtypes = [T_HANDLE, T_UINT, T_WPARAM,
                                       T_LPCWSTR]
        user32.SetForegroundWindow.argtypes = [T_HANDLE]
        user32.PostMessageW.argtypes = [T_HANDLE, T_UINT, T_WPARAM,
                                       T_LPARAM]
        user32.DestroyMenu.argtypes = [T_HANDLE]
        kernel32.GetModuleHandleW.restype = T_HANDLE
        gdi32.CreateBitmap.restype = T_HANDLE
        shell32.Shell_NotifyIconW.argtypes = [ctypes.c_uint,
                                             ctypes.c_void_p]
        shell32.Shell_NotifyIconW.restype = ctypes.c_int
    except Exception:
        pass  # signatures déjà posées ou fakes de test : on continue


class _WndClassW(ctypes.Structure):
    _fields_ = [("style", T_UINT),
                ("lpfnWndProc", ctypes.c_void_p),
                ("cbClsExtra", ctypes.c_int),
                ("cbWndExtra", ctypes.c_int),
                ("hInstance", T_HANDLE),
                ("hIcon", T_HICON),
                ("hCursor", T_HANDLE),
                ("hbrBackground", T_HANDLE),
                ("lpszMenuName", T_LPCWSTR),
                ("lpszClassName", T_LPCWSTR)]


class _NotifyIconDataW(ctypes.Structure):
    """NOTIFYICONDATAW (champ union réduit à un UINT : pas de bulles)."""
    _fields_ = [("cbSize", T_DWORD),
                ("hWnd", T_HANDLE),
                ("uID", T_UINT),
                ("uFlags", T_UINT),
                ("uCallbackMessage", T_UINT),
                ("hIcon", T_HICON),
                ("szTip", ctypes.c_wchar * 128),
                ("dwState", T_DWORD),
                ("dwStateMask", T_DWORD),
                ("szInfo", ctypes.c_wchar * 256),
                ("uVersion", T_UINT),
                ("szInfoTitle", ctypes.c_wchar * 64),
                ("dwInfoFlags", T_DWORD),
                ("guidItem", ctypes.c_ubyte * 16),
                ("hBalloonIcon", T_HICON)]


class _IconInfo(ctypes.Structure):
    _fields_ = [("fIcon", T_BOOL),
                ("xHotspot", T_DWORD),
                ("yHotspot", T_DWORD),
                ("hbmMask", T_HANDLE),
                ("hbmColor", T_HANDLE)]


class _Msg(ctypes.Structure):
    _fields_ = [("hwnd", T_HANDLE), ("message", T_UINT),
                ("wParam", T_WPARAM), ("lParam", T_LPARAM),
                ("time", T_DWORD), ("ptx", T_LONG),
                ("pty", T_LONG)]


class _Point(ctypes.Structure):
    _fields_ = [("x", T_LONG), ("y", T_LONG)]


_tray_set_prototypes()


def _tray_icon_bits(state):
    """Génère les 32 lignes BGRA (haut->bas) de l'icône d'état.
    Plein carré (pas de coins transparents : l'AND-mask reste tout à
    zéro, aucun rendu noir résiduel selon les versions de Windows)."""
    fill, border = {
        "on":    ((67, 160, 71), (27, 94, 32)),
        "sleep": ((117, 117, 117), (33, 33, 33)),
        "off":   ((229, 57, 53), (136, 14, 79)),
    }.get(state, ((67, 160, 71), (27, 94, 32)))
    rows = []
    for y in range(_TRAY_SIZE):
        row = bytearray(_TRAY_SIZE * 4)
        for x in range(_TRAY_SIZE):
            edge = x < 2 or y < 2 or x >= _TRAY_SIZE - 2 or y >= _TRAY_SIZE - 2
            c = border if edge else fill
            # glyphe blanc au centre
            cx, cy = x - 16, y - 16
            if state == "on":
                # anneau (haut-parleur stylisé)
                if 9 * 9 <= cx * cx + cy * cy <= 36 or (-3 <= cx <= 6 and -3 <= cy <= 3 and cx <= 0):
                    c = (255, 255, 255)
            elif state == "sleep":
                # croissant de lune : cercle blanc moins cercle décalé
                if cx * cx + cy * cy <= 49 and (cx - 6) ** 2 + (cy + 6) ** 2 > 36:
                    c = (255, 255, 255)
            else:  # off : croix
                if (-9 <= cx <= 9) and (abs(cx - cy) <= 2 or abs(cx + cy) <= 2):
                    c = (255, 255, 255)
            o = x * 4
            row[o], row[o + 1], row[o + 2] = c[2], c[1], c[0]  # BGRA
            row[o + 3] = 255
        rows.append(bytes(row))
    return rows


class SystrayIcon:
    """Icône systray en ctypes pur (v2.16.0) : fenêtre cachée + menu.

    get_items() -> liste de (label, callable) ou None (séparateur) ;
    appelée à CHAQUE clic droit pour refléter l'état courant. Les
    callables s'exécutent dans le thread du menu : les actions qui
    touchent au deck doivent être marshalées vers la boucle principale
    par l'appelant. on_double (double-clic gauche) est optionnel."""

    def __init__(self, tooltip, get_items, on_double=None):
        self._tip = tooltip[:127]
        self._get_items = get_items
        self._on_double = on_double
        self._hwnd = None
        self._nid = None
        self._proc = None
        self._taskbar_msg = 0
        self._icons = {}
        self._state = "on"
        self._thread = None

    # -- cycle de vie ------------------------------------------------------
    def start(self):
        """Lance le thread du systray. Ne lève JAMAIS : en cas de panne
        l'app continue sans icône (v2.16.2 — un échec ici tuait l'app en
        silence sous pythonw, sans console pour le dire)."""
        try:
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
        except Exception as e:
            print(f"[systray] icône impossible : {e} — l'app continue.")

    def _run(self):
        """Crée la fenêtre, ajoute l'icône, POMPE les messages : tout
        dans CE thread (Windows exige que les messages d'une fenêtre
        soient traités par le thread qui l'a créée — v2.16.2)."""
        try:
            hinst = kernel32.GetModuleHandleW(None)
            self._taskbar_msg = user32.RegisterWindowMessageW("TaskbarCreated")
            self._proc = WINFUNCTYPE(
                ctypes.c_ssize_t, T_HANDLE, T_UINT, T_WPARAM,
                T_LPARAM)(self._wnd_proc)
            wc = _WndClassW()
            wc.style = 0
            wc.lpfnWndProc = ctypes.cast(self._proc, ctypes.c_void_p)
            wc.hInstance = hinst
            wc.lpszClassName = "AKP05ETrayWnd"
            user32.RegisterClassW(ctypes.byref(wc))
            self._hwnd = user32.CreateWindowExW(
                0, "AKP05ETrayWnd", "", 0, 0, 0, 0, 0,
                None, None, hinst, None)
            self._nid = _NotifyIconDataW()
            self._nid.cbSize = ctypes.sizeof(_NotifyIconDataW)
            self._nid.hWnd = self._hwnd
            self._nid.uID = 1
            self._nid.uFlags = _NIF_MESSAGE | _NIF_ICON | _NIF_TIP
            self._nid.uCallbackMessage = _TRAY_MSG
            self._nid.szTip = self._tip
            self._nid.hIcon = self._icon(self._state)
            shell32.Shell_NotifyIconW(_NIM_ADD, ctypes.byref(self._nid))
        except Exception as e:
            print(f"[systray] icône impossible : {e} — l'app continue.")
            return
        msg = _Msg()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

    def stop(self):
        try:
            if self._nid is not None:
                shell32.Shell_NotifyIconW(_NIM_DELETE, ctypes.byref(self._nid))
            if self._hwnd:
                user32.PostMessageW(self._hwnd, _WM_QUIT, 0, 0)
        except Exception:
            pass

    # -- fenêtre / icône ---------------------------------------------------
    def _wnd_proc(self, hwnd, uMsg, wParam, lParam):
        if uMsg == self._taskbar_msg and self._nid is not None:
            # explorer.exe a redémarré : l'icône doit être remise
            shell32.Shell_NotifyIconW(_NIM_ADD, ctypes.byref(self._nid))
            return 0
        if uMsg == _TRAY_MSG:
            mouse = lParam & 0xFFFF
            if mouse == _WM_RBUTTONUP:
                self._popup_menu()
            elif mouse == _WM_LBUTTONDBLCLK and self._on_double:
                try:
                    self._on_double()
                except Exception:
                    pass
            return 0
        return user32.DefWindowProcW(hwnd, uMsg, wParam, lParam)

    def _popup_menu(self):
        items = self._get_items() or []
        hmenu = user32.CreatePopupMenu()
        for i, it in enumerate(items):
            if it is None:
                user32.AppendMenuW(hmenu, 0x800, 0, None)   # séparateur
            else:
                user32.AppendMenuW(hmenu, 0, _MENU_ID_BASE + i, it[0])
        pt = _Point()
        user32.GetCursorPos(ctypes.byref(pt))
        user32.SetForegroundWindow(self._hwnd)
        cmd = user32.TrackPopupMenu(
            hmenu, _TPM_RETURNCMD | _TPM_NONOTIFY | _TPM_RIGHTBUTTON,
            pt.x, pt.y, 0, self._hwnd, None)
        user32.PostMessageW(self._hwnd, 0, 0, 0)  # WM_NULL : rend le focus
        user32.DestroyMenu(hmenu)
        idx = cmd - _MENU_ID_BASE
        if 0 <= idx < len(items) and items[idx]:
            try:
                items[idx][1]()
            except Exception as e:
                print(f"[systray] action du menu impossible : {e}")

    def set_state(self, state, tooltip=None):
        """state : 'on' (vert), 'sleep' (gris lune) ou 'off' (rouge)."""
        self._state = state
        if self._nid is None or not self._hwnd:
            return
        if tooltip:
            self._tip = tooltip[:127]
            self._nid.szTip = self._tip
        self._nid.hIcon = self._icon(state)
        try:
            shell32.Shell_NotifyIconW(_NIM_MODIFY, ctypes.byref(self._nid))
        except Exception:
            pass

    def _icon(self, state):
        if state not in self._icons:
            bits = b"".join(reversed(_tray_icon_bits(state)))  # bottom-up
            color = gdi32.CreateBitmap(_TRAY_SIZE, _TRAY_SIZE, 1, 32, bits)
            mask = gdi32.CreateBitmap(_TRAY_SIZE, _TRAY_SIZE, 1, 1,
                                       b"\x00" * 128)  # tout opaque
            ii = _IconInfo(1, 0, 0, mask, color)
            self._icons[state] = user32.CreateIconIndirect(ctypes.byref(ii))
        return self._icons[state]


# ---------------------------------------------------------------------------
# Autostart (v2.16.0) — Planificateur de tâches : à l'ouverture de
# session, avec un délai (l'USB et le réseau ont le temps d'arriver).
# ---------------------------------------------------------------------------

AUTOSTART_TASK = "AKP05E Interface"
AUTOSTART_LNK = "AKP05E Interface.lnk"  # repli dossier Démarrage


def _autostart_python():
    """pythonw.exe si disponible (pas de fenêtre console), sinon python."""
    exe = sys.executable
    pyw = os.path.join(os.path.dirname(exe), "pythonw.exe")
    if exe.lower().endswith("python.exe") and os.path.exists(pyw):
        return pyw
    return exe


def _startup_dir():
    """Dossier Démarrage de l'utilisateur (shell:startup), sans admin."""
    return os.path.join(os.environ.get("APPDATA", ""),
                        "Microsoft", "Windows", "Start Menu",
                        "Programs", "Startup")


def _install_autostart_shortcut(delay_s):
    """v2.16.1 : repli sans droits admin — raccourci .lnk dans le
    dossier Démarrage, créé via PowerShell + WScript.Shell. Le délai est
    assuré par l'app elle-même (option --startup, voir main())."""
    lnk = os.path.join(_startup_dir(), AUTOSTART_LNK)
    exe = _autostart_python()
    app = os.path.abspath(__file__)
    wd = os.path.dirname(app)
    cmd = ("$s=(New-Object -ComObject WScript.Shell)"
           ".CreateShortcut('%s');$s.TargetPath='%s';"
           "$s.Arguments='\"%s\" --startup';$s.WorkingDirectory='%s';"
           "$s.Description='AKP05E Interface';$s.Save()" % (lnk, exe, app, wd))
    r = subprocess.run(
        ["powershell", "-NoProfile", "-Command", cmd],
        capture_output=True, text=True)
    if r.returncode == 0 and os.path.exists(lnk):
        print(f"Autostart installé (raccourci Démarrage, sans admin) : "
              f"lancement à l'ouverture de session, "
              f"l'app patiente {delay_s} s avant d'ouvrir le deck.")
        return True
    print("Échec du repli raccourci Démarrage : "
          + (r.stderr or r.stdout or "?").strip())
    return False


def install_autostart(delay_s=30):
    tr = '"%s" "%s"' % (_autostart_python(), os.path.abspath(__file__))
    r = subprocess.run(
        ["schtasks", "/Create", "/TN", AUTOSTART_TASK, "/SC", "ONLOGON",
         "/DELAY", "0000:%02d" % max(0, int(delay_s)), "/TR", tr, "/F"],
        capture_output=True, text=True)
    if r.returncode == 0:
        print(f"Autostart installé ({AUTOSTART_TASK}) : lancement à "
              f"l'ouverture de session, après {delay_s} s.")
        print("Commande : " + tr)
        return True
    # v2.16.1 : /SC ONLOGON exige des droits admin (« Accès refusé ») ->
    # repli automatique : raccourci dans le dossier Démarrage
    print("Planificateur refusé (admin requis : "
          + (r.stderr or r.stdout or "?").strip()[:120] + ")")
    print("Repli : raccourci dans le dossier Démarrage…")
    return _install_autostart_shortcut(delay_s)


def uninstall_autostart():
    """Retire les deux formes d'autostart (tâche planifiée OU raccourci)."""
    removed = False
    r = subprocess.run(["schtasks", "/Delete", "/TN", AUTOSTART_TASK, "/F"],
                       capture_output=True, text=True)
    if r.returncode == 0:
        print(f"Autostart retiré ({AUTOSTART_TASK}).")
        removed = True
    lnk = os.path.join(_startup_dir(), AUTOSTART_LNK)
    if os.path.exists(lnk):
        try:
            os.remove(lnk)
            print(f"Raccourci Démarrage retiré ({AUTOSTART_LNK}).")
            removed = True
        except Exception as e:
            print("Impossible de retirer le raccourci Démarrage : " + str(e))
    if not removed:
        print("Aucun autostart à retirer.")
    return removed


def autostart_installed():
    """True si la tâche planifiée OU le raccourci Démarrage est présent."""
    try:
        r = subprocess.run(["schtasks", "/Query", "/TN", AUTOSTART_TASK],
                           capture_output=True)
        if r.returncode == 0:
            return True
    except Exception:
        pass
    return os.path.exists(os.path.join(_startup_dir(), AUTOSTART_LNK))


# ---------------------------------------------------------------------------
# Calibration du bandeau tactile (--calibrate-strip) — v2.17.0
# David a constaté que le logo de boot AJAZZ occupe plus de pixels que nos
# images 800x112 : la résolution native du bandeau est probablement
# supérieure. Ce mode envoie successivement des motifs gradués à
# différentes résolutions candidates ; une PHOTO du bandeau suffit ensuite
# à déduire la vraie résolution (le cadre rouge au bord EXACT de l'image
# est-il entier ? jusqu'à quel repère chiffré voit-on les colonnes ?).
# ---------------------------------------------------------------------------

CALIB_STRIP_PROBES = [
    # (titre console, largeur, hauteur) — v2.17.1 : gros chiffres lisibles
    ("grille 800x112 (taille actuelle de l'app)", 800, 112),
    ("sonde HAUTEUR 800x128 (candidat natif, limite 112 en jaune)", 800, 128),
    ("sonde LARGEUR 1024x128 (repères de colonnes jusqu'à 1000)", 1024, 128),
    ("sonde LARGEUR 1024x112 (repères de colonnes jusqu'à 1000)", 1024, 112),
]


def _calib_strip_image(w, h):
    """Grille graduée de calibration : repères de colonnes tous les 100 px
    (chiffres blancs), lignes tous les 14 px (chiffres jaunes), limites des
    4 zones tactiles en bleu pointillé, cadre rouge au bord EXACT de
    l'image — sur la photo : cadre entier = l'image occupe toute la zone
    affichée ; repère chiffré le plus haut visible = largeur/hauteur
    réellement affichée (si < w ou h, le firmware recadre)."""
    img = Image.new("RGB", (w, h), (16, 18, 22))
    d = ImageDraw.Draw(img)
    for x in range(0, w, 10):
        col = (70, 74, 82) if x % 100 == 0 else (46, 50, 56)
        d.line([(x, 0), (x, h)], fill=col)
    step = 14 if h <= 112 else 16
    for y in range(0, h, step):
        col = (255, 213, 79) if y % (step * 4) == 0 else (60, 64, 70)
        d.line([(0, y), (w, y)], fill=col)
    # limites des 4 zones tactiles (x = 200/400/600), bleu pointillé
    for zx in (200, 400, 600):
        if zx < w:
            y = 0
            while y < h:
                d.line([(zx, y), (zx, min(y + 4, h - 1))],
                       fill=(129, 212, 250))
                y += 8
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except OSError:
        font = ImageFont.load_default()
    # repère "0" dessiné UNE fois à l'origine ; colonnes à partir de 100,
    # lignes numérotées selon le pas (14 px pour 112 de haut, 16 pour 128)
    step = 14 if h <= 112 else 16
    d.text((6, 6), "0,0", font=font, fill=(255, 255, 255), anchor="la")
    for x in range(100, w, 100):
        d.text((min(x + 5, w - 4), 2), str(x), font=font,
               fill=(255, 255, 255), anchor="la")
    for y in range(step, h, step):
        d.text((4, min(y + 3, h - 6)), str(y), font=font,
               fill=(255, 255, 255), anchor="la")
    # v2.17.1 : sur les sondes plus hautes que 112, marque la limite
    # actuelle de l'app en JAUNE VIF — si tu vois du contenu SOUS la
    # ligne 112, le panneau est plus haut que ce que l'app utilise
    if h > 112:
        d.line([(0, 112), (w, 112)], fill=(255, 213, 79))
        d.text((w - 8, 116), "112", font=font, fill=(255, 213, 79),
               anchor="ra")
    # cadre rouge au bord EXACT de l'image
    d.rectangle([0, 0, w - 1, h - 1], outline=(255, 64, 64), width=3)
    return img


def run_calibrate_strip():
    """Mode --calibrate-strip : affiche les sondes graduées sur le bandeau.
    Knob 1 : sonde suivante / précédente ; appui knob 1 ou n'importe
    quelle touche : quitte. Photographie chaque sonde puis envoie les
    photos : on en déduira la résolution native du bandeau."""
    print("=== Calibration du bandeau tactile — v%s ===" % APP_VERSION)
    print("Knob 1 (gauche) : sonde suivante/précédente ; appui knob 1")
    print("ou n'importe quelle touche : quitter. Photographie chaque sonde")
    print("et note : cadre ROUGE entier ? dernier repère de colonne ?")
    print("dernier repère de ligne ?")
    device = Akp05Device(brightness=DEFAULT_BRIGHTNESS)
    device.open()
    n = len(CALIB_STRIP_PROBES)
    idx = [0]
    quit_ev = threading.Event()

    def show():
        title, w, h = CALIB_STRIP_PROBES[idx[0]]
        img = _calib_strip_image(w, h)
        # même chemin d'envoi que set_strip : rotation 180° + JPEG plafonné
        jpeg = device._pil_to_jpeg_capped(img.rotate(180))
        device._upload_jpeg(STRIP_WIRE_KEY, jpeg)
        print("[calibration] sonde %d/%d : %s (%dx%d) — JPEG %d octets"
              % (idx[0] + 1, n, title, w, h, len(jpeg)))

    def on_ev(ev):
        if ev.name == "encoder_1_cw":
            idx[0] = (idx[0] + 1) % n
            show()
        elif ev.name == "encoder_1_ccw":
            idx[0] = (idx[0] - 1) % n
            show()
        elif ev.state and (ev.name == "encoder_1_button"
                           or ev.name.startswith("button_")):
            quit_ev.set()

    device.on_event = on_ev
    show()
    try:
        while not quit_ev.wait(0.25):
            pass
    except KeyboardInterrupt:
        pass
    finally:
        device.close()
        print("[calibration] terminé — envoie les photos des sondes.")


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Identification du matériel (--identify) — v2.18.0 / v2.18.2
# L'AKP05E est un rebrand AJAZZ du matériel Mirabox/HOTSPOTEK ; AJAZZ ne
# publie aucune doc. Ce mode affiche VID/PID, chaînes USB et interroge le
# firmware : feature report HID (GET_REPORT — le seul chemin qui répond sur
# ce matériel) puis commandes CRT VER en cascade. À copier-coller dans tout
# rapport de bug.
# ---------------------------------------------------------------------------

_HID_DIRECT_DLL = None


def _hidd_get_feature(handle, report_id, size):
    """GET_REPORT direct : HidD_GetFeature (hid.dll), sans passer par
    pywinusb.find_feature_reports — le descripteur HID de l'AKP05E ne
    déclare AUCUN item Feature (test réel v2.18.2 : liste vide), mais le
    firmware répond au GET_REPORT : DeckBridge/mirajazz lisent le feature
    report id 0x01 (~20 octets) via hid_get_feature_report, qui appelle
    HidD_GetFeature sous le capot. Renvoie les octets lus ou None."""
    return _hid_call("HidD_GetFeature", handle, report_id, size)


def _hidd_get_input_report(handle, report_id, size):
    """GET_REPORT sur le report INPUT : HidD_GetInputReport — dernière
    piste documentée (ajazz-control-center : « the VER response is pulled
    via GET_REPORT (HIDIOCGINPUT/HIDIOCGFEATURE) »). Renvoie les octets
    lus ou None."""
    return _hid_call("HidD_GetInputReport", handle, report_id, size)


def _hid_call(api, handle, report_id, size):
    """Appel direct d'une API GET_REPORT de hid.dll (sans passer par le
    descripteur HID). Renvoie les octets lus ou None."""
    global _HID_DIRECT_DLL
    if not handle:
        return None
    try:
        if _HID_DIRECT_DLL is None:
            _HID_DIRECT_DLL = ctypes.WinDLL("hid.dll")
        fn = getattr(_HID_DIRECT_DLL, api)
        fn.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong]
        fn.restype = ctypes.c_int
    except Exception:
        return None
    try:
        buf = ctypes.create_string_buffer(size)
        buf[0] = bytes([report_id])
        if fn(handle, buf, size):
            return bytes(buf.raw)
    except Exception:
        pass
    return None


def run_identify():
    """Mode --identify : énumère les appareils AJAZZ/Mirabox branchés (VID
    0x0300), affiche leurs chaînes USB et interroge le firmware du AKP05E
    (feature report GET_REPORT, puis CRT VER). Aucune écriture sur les
    écrans."""
    print("=== Identification du matériel — v%s ===" % APP_VERSION)
    found = []
    try:
        found = hid.HidDeviceFilter(vendor_id=VENDOR_ID).get_devices()
    except Exception as e:
        print("Énumération impossible : %s" % e)
    if not found:
        print("Aucun appareil détecté avec le VID AJAZZ/Mirabox 0x%04X."
              % VENDOR_ID)
        print("Branche le deck (câble USB-C DONNÉES, pas charge seule), puis :")
        print('  powershell -Command "Get-PnpDevice -PresentOnly | \\')
        print("    Where-Object InstanceId -match 'VID_0300' | \\")
        print('    Format-List FriendlyName, InstanceId"')
        return
    target = None
    for i, d in enumerate(found):
        vid = getattr(d, "vendor_id", 0) or 0
        pid = getattr(d, "product_id", 0) or 0
        is_ours = (vid, pid) == (VENDOR_ID, PRODUCT_ID)
        print("Appareil %d : VID 0x%04X / PID 0x%04X%s"
              % (i + 1, vid, pid, "  <- AKP05E (cible de l'app)"
                 if is_ours else ""))
        for attr, label in (("vendor_name", "  Fabricant USB"),
                            ("product_name", "  Produit USB"),
                            ("serial_number", "  N° de série"),
                            ("version", "  Version USB (bcdDevice)")):
            try:
                val = getattr(d, attr, None)
            except Exception:
                val = None
            if val:
                print("%s : %s" % (label, val))
        if is_ours and target is None:
            target = d
    if target is None:
        print("AKP05E (PID 0x%04X) absent : impossible d'interroger le "
              "firmware." % PRODUCT_ID)
        return

    # interrogation du firmware : réponses brutes du endpoint IN
    reports = []

    def on_raw(data):
        try:
            reports.append(list(data))
        except Exception:
            pass

    try:
        target.open()
        target.set_raw_data_handler(on_raw)
    except Exception as e:
        print("Ouverture impossible : %s — ferme le logiciel AJAZZ/Mirabox "
              "officiel (accès HID exclusif) et réessaie." % e)
        return

    def probe_feature_reports(stage):
        """v2.18.2 : lit les feature reports HID (GET_REPORT). Sur ce
        firmware, la réponse CRT VER n'arrive JAMAIS sur le endpoint IN ;
        la version se lit ici (DeckBridge : « The CRT VER reply never
        arrives on V3.AKP05E.02.007, but feature report 0x01 returns the
        version text »)."""
        results = []
        try:
            reps = list(target.find_feature_reports())
        except Exception as e:
            print("Feature reports inaccessibles (%s) : %s" % (stage, e))
            return results
        for rep in reps:
            try:
                rep.get()
                raw = bytes(bytearray(rep.get_raw_data()))
            except Exception:
                continue
            if raw:
                results.append(raw)
        # v2.18.3 : GET_REPORT direct même si le descripteur ne déclare
        # aucun item Feature (HidD_GetFeature). On essaie le report id
        # 0x01 (DeckBridge/mirajazz), puis 0x00, avec des tailles
        # croissantes (la longueur exacte est imposée par HidD_GetFeature).
        if not results:
            # v2.18.4 : handle robuste (nom d'attribut selon la version de
            # pywinusb), puis GET_REPORT Feature, puis GET_REPORT Input
            # (dernière piste documentée : HIDIOCGINPUT), et diagnostic
            # d'échec pour que le test réel tranche définitivement.
            handle = None
            for attr in ("hid_handle", "_hid_handle", "handle"):
                v = getattr(target, attr, None)
                if v:
                    handle = v
                    break
            caps = getattr(target, "capabilities", None)
            frbl = int(getattr(caps, "FeatureReportByteLength", 0) or 0)
            irbl = int(getattr(caps, "InputReportByteLength", 0) or 0)
            sizes_f, sizes_i = [], []
            for s in (frbl, frbl + 1, 21, 33, 65, 129, 257, 513):
                if 1 <= s and s not in sizes_f:
                    sizes_f.append(s)
            for s in (irbl, irbl + 1, 33, 65, 129, 257, 513, 1025):
                if 1 <= s and s not in sizes_i:
                    sizes_i.append(s)
            seen = set()
            tried = 0
            for rid in (0x01, 0x00):
                for size in sizes_f:
                    tried += 1
                    raw = _hidd_get_feature(handle, rid, size)
                    if raw and raw not in seen:
                        seen.add(raw)
                        results.append(raw)
                if seen:
                    break
            if not results:
                for rid in (0x00, 0x01):
                    for size in sizes_i:
                        tried += 1
                        raw = _hidd_get_input_report(handle, rid, size)
                        if raw and raw not in seen:
                            seen.add(raw)
                            results.append(raw)
                    if seen:
                        break
            if not results:
                print("GET_REPORT direct : aucune réponse sur %d essais "
                      "(handle=%s, FeatureReportByteLength=%d, "
                      "InputReportByteLength=%d)." %
                      (tried, "OK" if handle else "ABSENT", frbl, irbl))
        if results:
            print("Feature report(s) lu(s) (%s) — COPIE CES LIGNES :"
                  % stage)
            for raw in results:
                printable = "".join(chr(b) if 32 <= b < 127 else "."
                                    for b in raw)
                print("  hex  : %s"
                      % " ".join("%02X" % b for b in raw))
                print("  ascii: |%s|" % printable)
        return results

    def find_fw_version(raws):
        """Cherche 'V' + chiffre + [alnum . -] (ex. V3.AKP05E.02.007)."""
        for raw in raws:
            text = "".join(chr(b) if 32 <= b < 127 else " " for b in raw)
            m = re.search(r"V\d[A-Za-z0-9.\-]+", text)
            if m:
                return m.group(0)
        return None

    fw_version = None
    try:
        # ① feature reports SANS commande : le chemin DeckBridge/mirajazz.
        fw_version = find_fw_version(probe_feature_reports("lecture directe"))
        if fw_version:
            print("VERSION FIRMWARE (feature report) : %s" % fw_version)
            print("(Handshakes CRT VER ignorés : version déjà obtenue.)")
        else:
            # ② handshakes VER (v2.18.1) ; après chaque essai muet on
            # relit les feature reports — ajazz-control-center : « the
            # VER response is pulled via GET_REPORT, not delivered
            # unsolicited on the interrupt-IN endpoint ».
            dev = Akp05Device(brightness=DEFAULT_BRIGHTNESS)
            dev.dev = target
            attempts = [("VER direct (boot)", None),
                        ("DIS puis VER (apres initialisation)", "DIS"),
                        ("CONNECT puis VER (apres keepalive)", "CONNECT")]
            print("Interrogation du firmware (commande VER, 3 handshakes)…")
            answered = False
            for label, pre in attempts:
                reports.clear()
                try:
                    if pre:
                        with dev.lock:
                            dev._send(crt_command(pre))
                        time.sleep(0.4)
                    with dev.lock:
                        dev._send(crt_command("VER"))
                    time.sleep(2.0)
                except Exception as e:
                    print("Envoi échoué : %s" % e)
                    continue
                if reports:
                    answered = True
                    print("Réponse(s) firmware (essai « %s ») — COPIE CES "
                          "LIGNES :" % label)
                    for r in reports[:5]:
                        printable = "".join(chr(b) if 32 <= b < 127 else "."
                                            for b in r[:48])
                        print("  " + " ".join("%02X" % (b if isinstance(b, int)
                                                          else 0)
                                             for b in r[:48]))
                        print("  |%s|" % printable)
                    break
                fw_version = find_fw_version(
                    probe_feature_reports("après « %s »" % label))
                if fw_version:
                    answered = True
                    print("VERSION FIRMWARE (feature report) : %s"
                          % fw_version)
                    break
                print("Essai « %s » : aucune réponse." % label)
            if not answered:
                print("Réponse firmware : AUCUNE sur les 3 essais (ce "
                      "firmware n'expose pas VER, ou il est muet — copie "
                      "quand même les lignes ci-dessus).")
    finally:
        try:
            target.close()
        except Exception:
            pass
    print("— identification terminée : copie tout ce qui précède dans un "
          "rapport de bug.")


def main():
    if "--install-autostart" in sys.argv:
        install_autostart()
        return
    if "--uninstall-autostart" in sys.argv:
        uninstall_autostart()
        return
    if "--list-sensors" in sys.argv:
        run_list_sensors()
        return
    if "--calibrate-strip" in sys.argv:
        # v2.17.0 : calibration du bandeau tactile (grilles graduées)
        run_calibrate_strip()
        return
    if "--identify" in sys.argv:
        # v2.18.0 : matériel + firmware exacts (VID/PID, chaînes USB, VER)
        run_identify()
        return
    config = load_config()
    if "--startup" in sys.argv:
        # v2.16.1 : lancé par le raccourci Démarrage — on laisse USB et
        # réseau arriver avant d'ouvrir le deck (délai de 30 s par défaut)
        delay = config.get("startup_delay", 30)
        print(f"[autostart] démarrage différé : {delay} s…")
        time.sleep(max(0, int(delay)))
    if "--setup-lms" in sys.argv:
        # assistant : détecte le serveur Lyrion, l'enregistre dans la
        # config, puis le démarrage continue normalement avec (v2.12.0)
        run_setup_lms(config)
    device = Akp05Device(brightness=config.get("brightness", DEFAULT_BRIGHTNESS))

    # --- pages de profils : "accueil" = la config classique, les pages
    #     supplémentaires sont définies dans la clé "pages" de la config.
    pages = config.get("pages") or {}

    # Pages LMS générées par le code (v2.4.0) : elles remplacent une
    # éventuelle définition « lms » de la config pour piloter chaque
    # Squeezebox individuellement (6 boutons = 6 lecteurs).
    def _enc_pages():
        return {
            "encoder_2_cw": {"action": {"type": "page", "page": "next"}},
            "encoder_2_ccw": {"action": {"type": "page", "page": "prev"}},
            "encoder_4_cw": {"action": {"type": "brightness", "dir": "up",
                                         "step": 10}},
            "encoder_4_ccw": {"action": {"type": "brightness", "dir": "down",
                                         "step": 10}},
            "encoder_4_button": {"action": {"type": "brightness_toggle"}},
        }

    _lms_cfg = config.get("lms") or {}
    inject_home_lms_button(config)
    inject_home_sleep_button(config)
    pages["lms"] = {
        "label": "LMS", "icon": "speaker", "color": "#A5D6A7",
        "buttons": {str(i + 1): {"action": {"type": "lms_open_player",
                                            "index": i}} for i in range(6)},
        # v2.10.4 : page principale LMS = knob 1 en volume SYSTÈME,
        # comme à l'accueil (le lecteur n'est attaché qu'en sous-pages)
        "encoders": {
            "encoder_1_cw": {"action": {"type": "sysvolume", "dir": "up"}},
            "encoder_1_ccw": {"action": {"type": "sysvolume",
                                        "dir": "down"}},
            "encoder_1_button": {"action": {"type": "sysvolume",
                                           "dir": "mute"}},
            **_enc_pages(),
        },
    }
    pages["lms_player"] = {
        "label": "Lecteur", "icon": "speaker", "color": "#81C784",
        "buttons": {
            "1": {"action": {"type": "lms_player_id"}},
            "2": {"action": {"type": "lms_player_power"}},
            "3": {"action": {"type": "lms_player_playpause"}},
            "4": {"icon": "favorite", "color": "#FF8A80",
                  "label": "Favoris",
                  "action": {"type": "lms_open_favs"}},
            "5": {"icon": "grid_view", "color": "#90CAF9",
                  "label": "Applis",
                  "action": {"type": "lms_open_apps"}},
            "6": {"icon": "undo", "color": "#FFFFFF", "bg": "#000000",
                  "label": "Retour",
                  "action": {"type": "lms_back"}},
        },
        # v2.10.4 : pas d'encoder_1 ici — l'interception dans handle()
        # capte le knob 1 sur les sous-pages LMS (volume du lecteur affiché)
        "encoders": _enc_pages(),
    }
    pages["lms_favs"] = {
        "label": "Favoris", "icon": "favorite", "color": "#FFF59D",
        "buttons": {
            **{str(i): {"action": {"type": "lms_fav_press", "slot": i - 1}}
               for i in range(1, 10)},
            "10": {"icon": "undo", "color": "#FFFFFF", "bg": "#000000",
                   "label": "Retour",
                   "action": {"type": "lms_back_player"}},
        },
        "encoders": {
            "encoder_3_cw": {"action": {"type": "lms_favs_scroll"}},
            "encoder_3_ccw": {"action": {"type": "lms_favs_scroll",
                                         "dir": "prev"}},
            "encoder_3_button": {"action": {"type": "lms_back_player"}},
            **_enc_pages(),
        },
    }
    pages["lms_apps"] = {
        "label": "Applis", "icon": "grid_view", "color": "#90CAF9",
        "buttons": {
            **{str(i): {"action": {"type": "lms_app_press",
                                   "slot": i - 1}}
               for i in range(1, 10)},
            "10": {"icon": "undo", "color": "#FFFFFF", "bg": "#000000",
                   "label": "Retour",
                   "action": {"type": "lms_back_player"}},
        },
        "encoders": {
            "encoder_3_cw": {"action": {"type": "lms_apps_scroll"}},
            "encoder_3_ccw": {"action": {"type": "lms_apps_scroll",
                                         "dir": "prev"}},
            "encoder_3_button": {"action": {"type": "lms_back_player"}},
            **_enc_pages(),
        },
    }
    # navigateur générique : niveau courant de l'appli ouverte (Qobuz,
    # Radio Paradise...) — touches 1-9 = éléments, retour = niveau/ampli
    pages["lms_browse"] = {
        "label": "Appli", "icon": "extension", "color": "#90CAF9",
        "buttons": {
            **{str(i): {"action": {"type": "lms_item_press",
                                   "slot": i - 1}}
               for i in range(1, 10)},
            "10": {"icon": "undo", "color": "#FFFFFF", "bg": "#000000",
                   "label": "Retour",
                   "action": {"type": "lms_browse_back"}},
        },
        "encoders": {
            "encoder_3_cw": {"action": {"type": "lms_browse_scroll"}},
            "encoder_3_ccw": {"action": {"type": "lms_browse_scroll",
                                         "dir": "prev"}},
            # v2.13.5 : tap zone 3 du bandeau (ou appui knob 3) =
            # lecture COMPLÈTE du niveau affiché (l'album) ; le retour
            # reste sur la touche 10
            "encoder_3_button": {"action": {"type": "lms_play_level"}},
            **_enc_pages(),
        },
    }
    # page « album » (v2.13.0) : touche 1 = jouer l'album ENTIER,
    # touches 2-9 = morceaux (« 01 Artiste - Titre »), knob 3 = sélection
    # (la touche sélectionnée est mise en évidence, la liste défile),
    # appui knob 3 = lecture du morceau sélectionné, touche 10 = retour.
    pages["lms_album"] = {
        "label": "Album", "icon": "album", "color": "#90CAF9",
        "buttons": {
            "1": {"action": {"type": "lms_album_play"}},
            **{str(i): {"action": {"type": "lms_album_press",
                                   "slot": i - 2}}
               for i in range(2, 10)},
            "10": {"icon": "undo", "color": "#FFFFFF", "bg": "#000000",
                   "label": "Retour",
                   "action": {"type": "lms_album_back"}},
        },
        "encoders": {
            "encoder_3_cw": {"action": {"type": "lms_album_scroll"}},
            "encoder_3_ccw": {"action": {"type": "lms_album_scroll",
                                         "dir": "prev"}},
            "encoder_3_button": {"action": {"type": "lms_album_play_sel"}},
            **_enc_pages(),
        },
    }
    LMS_PAGE_NAMES = ("lms", "lms_player", "lms_favs", "lms_apps",
                      "lms_browse", "lms_album")

    # carrousel / knob 2 : le raccourci « lms » (page d'accueil LMS) y
    # figure quand LMS est configuré ; les sous-pages (lecteur, favoris,
    # applis, navigation) restent en accès direct par navigation interne.
    page_names = (["accueil"] + [n for n in pages
                                 if n != "accueil"
                                 and n not in LMS_PAGE_NAMES]
                  + (["lms"] if _lms_cfg.get("host") else []))
    current = {"name": config.get("page", "accueil")}
    # Génération de peinture : incrémentée à chaque changement de page.
    # Les threads de rafraîchissement (LMS, minuteurs, hardware, bandeau)
    # capturent la génération avant de peindre et ABANDONNENT si la page
    # a changé entre-temps — sinon des touches gardent des icônes de
    # l'ancienne page (race peinture vs switch).
    page_paint = {"gen": 0}
    vu_cfg = config.get("vu_meter") or {}
    vu_on = _HAS_PYCAW and bool(vu_cfg.get("enabled", True))
    global _vu_active
    _vu_active = vu_on
    # v2.19.0 : titre du morceau LMS sur la zone 3 du bandeau (remplace
    # le VU-mètre quand un lecteur LMS joue) ; "strip_title":
    # {"enabled": false} pour garder le VU-mètre en permanence.
    strip_title_cfg = config.get("strip_title") or {}
    strip_title_on = bool(strip_title_cfg.get("enabled", True))

    def page_cfg():
        if current["name"] == "accueil" or current["name"] not in pages:
            return config
        return pages.get(current["name"], {})

    def paint_page():
        """(Re)peint les 10 touches et le bandeau pour la page courante."""
        if getattr(device, "_sleeping", False):
            return  # v2.14.8 : veille complète — rien ne se repeint
        buttons = page_cfg().get("buttons") or {}
        gen = page_paint["gen"]
        for n in range(1, 11):
            if page_paint["gen"] != gen:
                return  # page changée pendant la peinture : abandon
            entry = buttons.get(str(n))
            try:
                if not entry:
                    device.set_image(n, Image.new("RGB", BUTTON_IMAGE_SIZE,
                                                  (12, 12, 12)))
                    continue
                if (entry.get("action") or {}).get("type") == "timer":
                    # touche minuteur : rendu selon l'état du minuteur actif
                    paint_timer_state(n, entry)
                    continue
                if (entry.get("action") or {}).get("type") == "stopwatch":
                    # touche chronomètre : rendu selon l'état du chrono
                    paint_chrono_state(n, entry)
                    continue
                if (entry.get("action") or {}).get("type") == "clock":
                    # touche horloge : heure + date, rafraîchie par poll_clock
                    paint_clock_button(n, entry)
                    continue
                if str((entry.get("action") or {}).get("type")
                       or "").startswith("lms"):
                    # touche LMS : libellés dynamiques
                    paint_lms_button(n, entry)
                    continue
                icon = entry.get("icon")
                if icon and os.path.exists(icon):
                    # chemin vers une image perso (png/jpg)
                    device.set_image(n, Image.open(icon))
                elif icon:
                    # nom d'icône Material (+ couleurs CSS)
                    set_icon(device, n, icon,
                             fg=entry.get("color", "#e0e0e0"),
                             bg=entry.get("bg", "#101010"),
                             label=entry.get("label"))
                elif "hw" in entry:
                    # touche capteur : dessinée en attente puis remplie
                    # par poll_hardware dès la première lecture HWiNFO
                    paint_hw_button(device, n, entry.get("label") or entry["hw"],
                                    None, page_cfg().get("thresholds", [70, 85]))
                elif "label" in entry:
                    device.set_label(n, entry["label"], sub=entry.get("sub"))
            except Exception as e:
                print(f"Icône touche {n} ignorée : {e}")

    def switch_page(name):
        if not name:
            return
        # "next" / "prev" : fait défiler les pages (knob 2)
        if name in ("next", "prev"):
            i = (page_names.index(current["name"])
                 if current["name"] in page_names else 0)
            name = page_names[(i + (1 if name == "next" else -1))
                               % len(page_names)]
        if name == "accueil" or name in pages:
            page_paint["gen"] += 1  # invalide les peintures en cours
            current["name"] = name
            print(f"[page] {name}")
            device._page_label = (page_cfg().get("label") or name)[:9]
            paint_page()
            refresh_strip()
        else:
            print(f"Page inconnue : {name} (disponibles : {page_names})")

    device.on_page_change = switch_page

    def _handle_strip(name):
        """Gestes du bandeau tactile : swipe = page précédente/suivante,
        tap sur une zone = action de l'encodeur correspondant (par défaut,
        tap sur la zone 2 du carrousel = page suivante)."""
        if name in ("strip_swipe_left", "strip_swipe_right"):
            way = "prev" if name.endswith("left") else "next"
            print(f"[tactile] swipe {'gauche' if way == 'prev' else 'droit'} → page {way}")
            switch_page(way)
            return
        zone = int(name.rsplit("_", 1)[1])
        print(f"[tactile] tap zone {zone}")
        enc = f"encoder_{zone}_button"
        action = page_cfg().get("encoders", {}).get(enc, {}).get("action")
        if action:
            # v2.13.6 : les actions lms_* sont gérées par lms_action, pas
            # par run_action (qui ne les connaît pas) — le tap tactile
            # suit le même routage que l'appui physique sur l'encodeur.
            if str(action.get("type") or "").startswith("lms"):
                lms_action(action)  # déjà dans un thread dédié
            else:
                run_action(action, device)
        elif zone == 2:
            switch_page("next")  # zone du carrousel sans action dédiée

    def handle(ev):
        # v2.14.7 : deck en veille -> n'importe quel événement le réveille
        # (l'événement est consommé : son action ne s'exécute pas, pour
        # éviter les clics accidentels au réveil)
        if getattr(device, "_sleeping", False):
            if not ev.state:
                # v2.14.8 : relâchement de la touche « Veille » (ou de
                # n'importe quel encodeur) -> on reste endormi, sinon le
                # deck se rallumait aussitôt à la fin de la pression
                return
            # v2.14.8 : seule une nouvelle PRESSION réveille
            device._sleeping = False
            device.set_brightness(getattr(device, "_last_bright",
                                          DEFAULT_BRIGHTNESS))
            try:
                paint_page()
                refresh_strip()
            except Exception:
                pass
            print("[veille] deck réveillé")
            return
        # minuteurs : gèrent eux-mêmes l'appui ET le relâchement
        # (clic court = départ/pause/reprise, clic long = réinitialise)
        if ev.name.startswith("button_"):
            entry = page_cfg().get("buttons", {}).get(ev.name.split("_")[1])
            t_act = entry and entry.get("action")
            if t_act and t_act.get("type") == "timer":
                try:
                    timer_event(ev.name.split("_")[1], t_act, ev.state)
                except Exception as e:
                    print(f"[erreur minuteur] {e}")
                return
            if t_act and t_act.get("type") == "stopwatch":
                try:
                    chrono_event(ev.name.split("_")[1], t_act, ev.state)
                except Exception as e:
                    print(f"[erreur chronomètre] {e}")
                return
            if t_act and t_act.get("type") == "clock":
                # v2.11.0 : appui = écran d'infos version (easter egg),
                # retour automatique à l'horloge après ~8 s
                if ev.state:
                    clock_show_info(ev.name.split("_")[1])
                return
        if not ev.state:
            return  # ignore les relâchements (sauf besoin spécifique)
        # appui sur le knob 2 : RETOUR ACCUEIL, partout (v2.10.0)
        if ev.name == "encoder_2_button":
            switch_page("accueil")
            return
        # knob 1 : sur les SOUS-PAGES LMS uniquement (lecteur, favoris,
        # applis, navigation), la rotation règle le volume du lecteur
        # AFFICHÉ et l'appui le muet. Partout ailleurs (accueil, page
        # principale LMS, autres pages) : volume système (v2.10.2)
        if (ev.name.startswith("encoder_1") and lms.enabled
                and current["name"] in LMS_PAGE_NAMES[1:]
                and lms_viewed() is not None):
            a1 = {"encoder_1_cw": {"type": "lms_volume", "dir": "up"},
                  "encoder_1_ccw": {"type": "lms_volume", "dir": "down"},
                  "encoder_1_button": {"type": "lms_mute"}}.get(ev.name)
            if a1:
                threading.Thread(target=lms_action, args=(a1,),
                                 daemon=True).start()
                return
        if ev.name.startswith("strip_"):
            threading.Thread(target=_handle_strip, args=(ev.name,),
                             daemon=True).start()
            return
        cfg = page_cfg()
        action = None
        if ev.name.startswith("button_"):
            entry = cfg.get("buttons", {}).get(ev.name.split("_")[1])
            action = entry and entry.get("action")
        else:
            action = cfg.get("encoders", {}).get(ev.name, {}).get("action")
            if action is None and ev.name.startswith("encoder_3"):
                # knob 3 sans action configurée : zoom universel par défaut
                action = {"type": "zoom", "dir": {
                    "encoder_3_cw": "in", "encoder_3_ccw": "out",
                    "encoder_3_button": "reset"}[ev.name]}
        if action and str(action.get("type") or "").startswith("lms"):
            # actions Lyrion Media Server (page « lms ») — en thread
            threading.Thread(target=lms_action, args=(action,),
                             daemon=True).start()
            return
        if action and action.get("type") in ("timer_adjust", "timer_start"):
            # knob 3 (page minuteurs) : durée réglable / départ direct
            try:
                if action.get("type") == "timer_adjust":
                    timer_adjust(action.get("dir") == "up")
                else:
                    timer_start_custom()
            except Exception as e:
                print(f"[erreur minuteur réglable] {e}")
            return
        if action:
            print(f"[action] {ev.name} -> {action.get('type')}")
            threading.Thread(target=run_action, args=(action, device),
                             daemon=True).start()

    device.on_event = handle
    device.on_disconnect = lambda: print("Deck débranché — relance l'application.")

    def _repaint_all():
        try:
            paint_page()
            refresh_strip()
            return True
        except Exception as e:
            print(f"[reconnexion] repeint impossible : {e}")
            return False

    # v2.15.0 : après une reconnexion automatique, on repeint tout
    device.on_reconnect = lambda: _repaint_all()

    def refresh_strip():
        """Redessine le bandeau : volume système + luminosité en direct,
        et nom de la page courante dans la zone 2."""
        if getattr(device, "_sleeping", False):
            return  # v2.14.8 : veille complète — le bandeau reste éteint
        gen = page_paint["gen"]
        vol, muted, vol_name = None, None, "Vol"
        # Squeezebox attachée UNIQUEMENT sur les sous-pages LMS (v2.10.2) ;
        # ailleurs (accueil, page principale LMS...) : volume système
        vp = (lms_viewed()
              if current["name"] in LMS_PAGE_NAMES[1:] else None)
        if vp:
            # Squeezebox affichée : SON volume sur le bandeau, sous-pages LMS
            with lms_lock:
                vol = vp["volume"]
                muted = lms_state["viewed_muted"]
            vol_name = "Vol " + player_code(vp)
        if vol is None and _HAS_PYCAW:
            try:
                vol, muted = get_volume_pct(), get_mute()
            except Exception:
                pass
        if current["name"] in LMS_PAGE_NAMES:
            z3 = "K3"
            # v2.13.9 : morceau en cours « i/N » si le lecteur affiché
            # lit (ou met en pause) une liste d'au moins 2 pistes —
            # sinon bouton Jouer l'album / Sélect.
            with lms_lock:
                _pl = lms_state.get("playing")
            _pos = ""
            if _pl and _pl.get("tracks", 0) >= 2:
                if 1 <= _pl.get("cur", 0) <= _pl["tracks"]:
                    _pos = f"{_pl['cur']}/{_pl['tracks']}"
                elif not _Z3_DIAG["warned"]:
                    # v2.13.9 : pourquoi pas de position ? one-shot
                    _Z3_DIAG["warned"] = True
                    print(f"[lms] bandeau : position indisponible "
                          f"(cur={_pl.get('cur')!r}, "
                          f"tracks={_pl.get('tracks')!r}, "
                          f"mode={_pl.get('mode')!r}, "
                          f"url={str(_pl.get('url'))[:60]!r}) — "
                          "copie cette ligne")
            if (_pl is None and vp and vp.get("playing")
                    and not _Z3_DIAG["none"]):
                # v2.14.0 : le lecteur joue mais pas d'info -> one-shot
                _Z3_DIAG["none"] = True
                print(f"[lms] bandeau : pas d'info de lecture "
                      f"(playing=None) pour {vp['name']!r} — "
                      "copie cette ligne")
            if _pos:
                z3 = _pos
            elif current["name"] == "lms_browse":
                with lms_lock:
                    lvl = (lms_state["browse"][-1]
                           if lms_state["browse"] else None)
                    items = lvl["items"] if lvl else []
                if len(lms_level_urls(items)) >= 2:
                    z3 = "▶ Album"
            elif current["name"] == "lms_album":
                z3 = "▶ Sélect."
            # v2.19.9 : rien d'utile en zone 3 ("K3") -> le morceau en
            # cours, comme sur l'accueil ; les boutons i/N / ▶ Album /
            # ▶ Sélect. (zones tactiles) gardent la priorité
            if (z3 == "K3" and strip_title_on and lms.enabled):
                with lms_lock:
                    _nt3 = lms_state.get("now_title")
                    _na3 = lms_state.get("now_artist")
                if _nt3:
                    z3 = ("TITLE", _nt3, _na3)
        else:
            if strip_title_on and lms.enabled:
                with lms_lock:
                    _nt = lms_state.get("now_title")
                    _na = lms_state.get("now_artist")
                if _nt:
                    z3 = ("TITLE", _nt, _na)
                else:
                    z3 = "VU" if vu_on else "K3"
            else:
                z3 = "VU" if vu_on else "K3"
        extras = (getattr(device, "_page_label", None) or "K2", z3)
        # carrousel : pages précédente / courante / suivante (zone 2)
        def _plabel(n):
            return (pages.get(n, {}).get("label")
                    or ("Accueil" if n == "accueil" else n))[:9]
        # v2.14.2 : les sous-pages LMS (lms_player, lms_browse...) ne
        # figurent pas dans le cycle du carrousel ; l'index retombait
        # à 0 et la pilule affichait « Accueil » avec l'icône de la
        # sous-page réelle. La pilule montre maintenant la page ou la
        # sous-page COURANTE ; les voisines grises restent celles de
        # l'ancre « lms » (ou de l'accueil hors LMS).
        cur_name = current["name"]
        if cur_name in page_names:
            i = page_names.index(cur_name)
        else:
            i = (page_names.index("lms")
                 if "lms" in page_names else 0)
        pages_tri = (
            _plabel(page_names[(i - 1) % len(page_names)]),
            _plabel(cur_name),
            _plabel(page_names[(i + 1) % len(page_names)]),
        )
        # icône + couleur d'accent de la page courante
        meta = (pages.get(current["name"])
                if current["name"] in pages else config)
        p_icon = meta.get("icon")
        p_color = parse_color(meta.get("color"), default=(129, 212, 250))
        if page_paint["gen"] != gen:
            return  # page changée : bandeau déjà repeint par le switch
        try:
            show_strip(device, device.brightness, volume=vol, muted=muted,
                       extras=extras, pages=pages_tri,
                       page_icon=p_icon, page_color=p_color,
                       vol_name=vol_name)
        except Exception as e:
            print(f"Bandeau non redessiné : {e}")

    def poll_volume():
        """Met à jour le bandeau dès que le volume change (deck, clavier,
        barre des tâches...) — vérification toutes les 0,5 s."""
        _com_init()
        last = None
        err_shown = False
        while True:
            state = None
            if _HAS_PYCAW:
                try:
                    state = (get_volume_pct(), get_mute())
                    err_shown = False
                except Exception as e:
                    state = None
                    if not err_shown:
                        print(f"[volume] lecture du volume système impossible : {e}")
                        err_shown = True
            if state != last:
                last = state
                refresh_strip()
            time.sleep(0.5)

    def poll_vu():
        """VU-mètre temps réel sur la zone 3 du bandeau : niveau de crête
        du son système (peak meter WASAPI), ~fps rafraîchissements/s avec
        marqueur de crête qui retombe lentement. Ne dessine que si le
        niveau a changé (le bandeau est lent : ~15-17 FPS max)."""
        _com_init()
        fps = max(2, min(30, int(vu_cfg.get("fps", 12))))
        period = 1.0 / fps
        hold, hold_t = 0.0, 0.0
        drawn = None
        err_shown = False
        while True:
            t0 = time.time()
            peak, muted = None, False
            try:
                peak = vu_get_peak()
                muted = get_mute()
            except Exception as e:
                if not err_shown:
                    err_shown = True
                    print(f"[vu] niveau audio indisponible : {e}")
            if (current["name"] in LMS_PAGE_NAMES
                    or (strip_title_on and lms.enabled
                        and lms_state.get("now_title"))):
                # pages LMS : pas de VU (v2.10.0) ; v2.19.0 : titre du
                # morceau sur la zone 3 -> pas de VU non plus ;
                # drawn=None force le repaint complet au retour
                drawn = None
                time.sleep(period)
                continue
            base = _strip_base
            if peak is not None and base is not None:
                if peak >= hold - 0.004:
                    hold, hold_t = peak, t0
                elif t0 - hold_t > 0.04:
                    hold = max(0.0, hold - 0.055)  # décroissance du marqueur
                state = (int(peak * 14), int(hold * 14), muted)
                if state != drawn:
                    drawn = state
                    img = base.copy()
                    draw_vu_zone(img, peak, hold, muted)
                    try:
                        device.set_strip(img)
                    except Exception:
                        pass
            time.sleep(max(0.02, period - (time.time() - t0)))

    # --- MINUTEURS -------------------------------------------------------
    timer_state = {"btn": None,        # touche du minuteur actif (str)
                  "remaining": 0,      # secondes restantes (fiable si pause)
                  "end_ts": None,     # fin en time.monotonic() si en marche
                  "running": False,
                  "alarm": False}
    timer_lock = threading.RLock()
    _timer_press = [None]              # (numéro de touche, instant d'appui)
    custom_minutes = [5]               # minuteur réglable (knob 3, 1-99 min)
    chrono_state = {"running": False,  # chronomètre
                    "elapsed": 0.0, "start_ts": None}
    _chrono_press = [None]             # (touche, instant d'appui) chrono

    def timer_minutes(action):
        """Minutes d'une action timer ; "minutes": 0 = durée réglable
        (ajustée au knob 3 sur la page minuteurs)."""
        try:
            m = int(action.get("minutes", 5))
        except (TypeError, ValueError):
            m = 5
        if m <= 0:
            m = custom_minutes[0]
        return m

    def timer_remaining():
        with timer_lock:
            if timer_state["running"]:
                return max(0.0, timer_state["end_ts"] - time.monotonic())
            return float(timer_state["remaining"])

    def paint_timer_state(n, entry, status_override=None):
        act = entry.get("action") or {}
        m = int(act.get("minutes", 5) or 0)
        if m <= 0:
            # touche « Régl. » : durée réglable, libellé dynamique
            total = custom_minutes[0] * 60
            label = f"{custom_minutes[0]} min"
        else:
            total = m * 60
            label = entry.get("label")
        if status_override:
            paint_timer_button(device, n, label, 0, total,
                               status_override)
            return
        with timer_lock:
            active = timer_state["btn"] == str(n)
            running = timer_state["running"]
            alarm = timer_state["alarm"]
            remaining = timer_state["remaining"]
        if not active:
            paint_timer_button(device, n, label, None, total)
        else:
            if alarm:
                status = "alarm"
            elif running:
                status = "run"
            elif remaining > 0:
                status = "pause"
            else:
                status = "idle"
            paint_timer_button(device, n, label,
                               timer_remaining(), total, status)

    def timer_event(n, action, down):
        """Clic court : départ / pause / reprise (ou acquitte l'alarme).
        Clic long (> 0,6 s) : réinitialise le minuteur (sans le lancer)."""
        try:
            total = timer_minutes(action) * 60
        except (TypeError, ValueError):
            total = 300
        if down:
            # conserve l'instant INITIAL d'appui : si le deck renvoie des
            # événements "down" répétés pendant un appui maintenu, ne pas
            # les ignorer ferait paraître le relâchement court (held < 0,6)
            # et relancerait le minuteur juste après une réinitialisation.
            if _timer_press[0] is None or _timer_press[0][0] != n:
                _timer_press[0] = (n, time.monotonic())
            return
        press = _timer_press[0]
        _timer_press[0] = None
        if not press or press[0] != n:
            return
        held = time.monotonic() - press[1]
        with timer_lock:
            old_btn = timer_state["btn"]
            active = old_btn == n
            if held >= 0.6:
                # clic long : réinitialise complètement (coupe l'alarme,
                # touche retour au préréglage gris) — ne lance JAMAIS
                # le minuteur, quel que soit l'état précédent
                if active:
                    timer_state.update(btn=None, remaining=0, end_ts=None,
                                       running=False, alarm=False)
            elif active and timer_state["alarm"]:
                # clic pendant l'alarme : acquitte et repositionne
                timer_state.update(remaining=total, end_ts=None,
                                   running=False, alarm=False)
            elif active and timer_state["running"]:
                # pause
                timer_state["remaining"] = max(
                    0, timer_state["end_ts"] - time.monotonic())
                timer_state["running"] = False
            elif active and timer_state["remaining"] > 0:
                # reprise
                timer_state["end_ts"] = (time.monotonic()
                                         + timer_state["remaining"])
                timer_state["running"] = True
            else:
                # départ (nouveau minuteur ou redémarre un minuteur fini)
                timer_state.update(btn=n, remaining=total,
                                   end_ts=time.monotonic() + total,
                                   running=True, alarm=False)
        # repeint la touche (et l'ancienne active si on vient d'en changer)
        entry = (page_cfg().get("buttons") or {}).get(n)
        if entry:
            paint_timer_state(int(n), entry)
        if old_btn and old_btn != n:
            old_entry = (page_cfg().get("buttons") or {}).get(old_btn)
            if old_entry:
                paint_timer_state(int(old_btn), old_entry)

    def timer_adjust(up):
        """Knob 3 (page minuteurs) : ajuste la durée réglable (1 à 99 min)."""
        with timer_lock:
            custom_minutes[0] = max(1, min(99,
                                          custom_minutes[0] + (1 if up else -1)))
        print(f"[minuteur] durée réglable : {custom_minutes[0]} min")
        for bn, e in (page_cfg().get("buttons") or {}).items():
            ea = e.get("action") or {}
            if ea.get("type") == "timer" and int(ea.get("minutes", 5) or 0) <= 0:
                paint_timer_state(int(bn), e)

    def timer_start_custom():
        """Appui sur le knob 3 (page minuteurs) : démarre le minuteur
        réglable sur sa touche « Régl. »."""
        btn = None
        for bn, e in (page_cfg().get("buttons") or {}).items():
            ea = e.get("action") or {}
            if ea.get("type") == "timer" and int(ea.get("minutes", 5) or 0) <= 0:
                btn = bn
                break
        if not btn:
            print("[minuteur] pas de touche « Régl. » sur cette page")
            return
        with timer_lock:
            old_btn = timer_state["btn"]
            total = custom_minutes[0] * 60
            timer_state.update(btn=btn, remaining=total,
                               end_ts=time.monotonic() + total,
                               running=True, alarm=False)
        for b in (old_btn, btn):
            if b:
                e = (page_cfg().get("buttons") or {}).get(b)
                if e:
                    paint_timer_state(int(b), e)

    def chrono_elapsed():
        """Temps mesuré par le chronomètre, en secondes."""
        with timer_lock:
            el = float(chrono_state["elapsed"])
            if chrono_state["running"]:
                el += max(0.0, time.monotonic() - chrono_state["start_ts"])
            return el

    def paint_chrono_state(n, entry):
        with timer_lock:
            running = chrono_state["running"]
        elapsed = chrono_elapsed()
        status = ("run" if running
                  else ("pause" if elapsed > 0 else "idle"))
        # libellé violet : distingue le chrono des préréglages minuteur
        paint_timer_button(device, n, entry.get("label") or "Chrono",
                           elapsed, 0, status, idle_sub="chrono",
                           label_fill=(179, 157, 219))

    def chrono_event(n, action, down):
        """Chronomètre : clic court = départ / pause / reprise, clic long
        (> 0,6 s) = remise à zéro."""
        if down:
            if _chrono_press[0] is None or _chrono_press[0][0] != n:
                _chrono_press[0] = (n, time.monotonic())
            return
        press = _chrono_press[0]
        _chrono_press[0] = None
        if not press or press[0] != n:
            return
        held = time.monotonic() - press[1]
        with timer_lock:
            if held >= 0.6:
                chrono_state.update(running=False, elapsed=0.0,
                                   start_ts=None)
            elif chrono_state["running"]:
                chrono_state["elapsed"] += max(
                    0.0, time.monotonic() - chrono_state["start_ts"])
                chrono_state.update(running=False, start_ts=None)
            elif chrono_state["elapsed"] > 0:
                chrono_state.update(start_ts=time.monotonic(),
                                    running=True)
            else:
                chrono_state.update(start_ts=time.monotonic(),
                                     running=True)
        entry = (page_cfg().get("buttons") or {}).get(n)
        if entry:
            paint_chrono_state(int(n), entry)

    _chrono_last = [None]             # pour le rafraîchissement du chrono

    def poll_timers():
        """Rafraîchit chaque seconde la touche du minuteur actif, déclenche
        l'alarme à la fin (bips + clignotement rouge). Le minuteur poursuit
        même si on quitte la page (seul le rafraîchissement visuel s'arrête)."""
        last_sig = None
        while True:
            try:
                gen = page_paint["gen"]
                with timer_lock:
                    btn = timer_state["btn"]
                    running = timer_state["running"]
                    alarm = timer_state["alarm"]
                if btn is not None:
                    rem = timer_remaining()
                    if running and rem <= 0:
                        with timer_lock:
                            timer_state["running"] = False
                            timer_state["alarm"] = True
                            alarm = True
                        print(f"[minuteur] temps écoulé (touche {btn}) !")
                        threading.Thread(target=ring_alarm,
                                         daemon=True).start()
                    entry = (page_cfg().get("buttons") or {}).get(btn)
                    if entry and (entry.get("action") or {}).get("type") == "timer":
                        blink = int(time.time() * 2) % 2 == 0
                        sig = (int(rem), alarm, blink if alarm else 0)
                        if sig != last_sig:
                            last_sig = sig
                            if page_paint["gen"] != gen:
                                continue  # page changée : ne pas écraser
                            if alarm and not blink:
                                paint_timer_state(int(btn), entry,
                                                  status_override="idle")
                            else:
                                paint_timer_state(int(btn), entry)
                    # chronomètre : rafraîchit la touche s'il tourne
                    for bn, e2 in (page_cfg().get("buttons") or {}).items():
                        ea = e2.get("action") or {}
                        if ea.get("type") == "stopwatch":
                            with timer_lock:
                                crun = chrono_state["running"]
                            if crun:
                                csig = int(chrono_elapsed() * 2)
                                if csig != _chrono_last[0]:
                                    _chrono_last[0] = csig
                                    if page_paint["gen"] == gen:
                                        paint_chrono_state(int(bn), e2)
                            break
            except Exception as e:
                print(f"[erreur minuteur] {e}")
            time.sleep(0.25)

    def paint_clock_button(n, entry):
        """Touche horloge : liseré coloré double, heure HH:MM en grand,
        date en français dessous — repeinte par poll_clock si nécessaire."""
        col = parse_color(entry.get("color") or "#81D4FA",
                          default=(129, 212, 250))
        img = Image.new("RGB", BUTTON_IMAGE_SIZE, (16, 18, 24))
        d = ImageDraw.Draw(img)
        # fond : léger dégradé vertical
        for y in range(BUTTON_IMAGE_SIZE[1]):
            mix = tuple(int(c * (1 - 0.22 * y / 112))
                        for c in (16, 18, 24))
            d.line([(0, y), (112, y)], fill=mix)
        # liseré : cadre arrondi vif + halo discret en retrait
        d.rounded_rectangle([3, 3, 108, 108], radius=16, outline=col,
                            width=2)
        d.rounded_rectangle([7, 7, 104, 104], radius=12,
                            outline=tuple(int(c * 0.35) for c in col),
                            width=1)
        now = time.localtime()
        try:
            f_big = ImageFont.truetype("arial.ttf", 30)
            f_date = ImageFont.truetype("arial.ttf", 13)
        except OSError:
            f_big = f_date = ImageFont.load_default()
        d.text((56, 44), time.strftime("%H:%M", now), font=f_big,
               fill=(240, 243, 248), anchor="mm")
        jours = ("lun", "mar", "mer", "jeu", "ven", "sam", "dim")
        mois = ("janv", "févr", "mars", "avr", "mai", "juin", "juil",
                "août", "sept", "oct", "nov", "déc")
        dstr = (f"{jours[now.tm_wday]}. {now.tm_mday} "
                f"{mois[now.tm_mon - 1]}")
        d.text((56, 84), dstr, font=f_date, fill=col, anchor="mm")
        device.set_image(n, img)

    def paint_clock_info(n):
        """Écran d'infos affiché quand on appuie sur la touche horloge
        (v2.11.0) : version de l'application, licence, crédit — la touche
        revient à l'horloge toute seule après ~8 s (poll_clock)."""
        img = Image.new("RGB", BUTTON_IMAGE_SIZE, (16, 18, 24))
        d = ImageDraw.Draw(img)
        for y in range(BUTTON_IMAGE_SIZE[1]):
            mix = tuple(int(c * (1 - 0.22 * y / 112))
                        for c in (16, 18, 24))
            d.line([(0, y), (112, y)], fill=mix)
        d.rounded_rectangle([3, 3, 108, 108], radius=16,
                            outline=(129, 212, 250), width=2)
        try:
            f_tiny = ImageFont.truetype("arial.ttf", 11)
            f_big = ImageFont.truetype("arial.ttf", 26)
            f_small = ImageFont.truetype("arial.ttf", 12)
        except OSError:
            f_tiny = f_big = f_small = ImageFont.load_default()
        d.text((56, 18), "AKP05E", font=f_small,
               fill=(129, 212, 250), anchor="mm")
        d.text((56, 44), f"v{APP_VERSION}", font=f_big,
               fill=(240, 243, 248), anchor="mm")
        d.text((56, 68), "open source - MIT", font=f_tiny,
               fill=(176, 182, 192), anchor="mm")
        d.text((56, 88), "avec Mistral AI", font=f_small,
               fill=(129, 212, 250), anchor="mm")
        device.set_image(n, img)

    # état de l'écran d'infos horloge : touche, échéance, génération page
    clock_info = {"btn": None, "until": 0.0, "gen": -1}

    def clock_show_info(n_str):
        """Appui sur la touche horloge : affiche l'écran d'infos version."""
        try:
            clock_info["gen"] = page_paint["gen"]
            clock_info["btn"] = n_str
            clock_info["until"] = time.monotonic() + 8.0
            paint_clock_info(int(n_str))
        except Exception as e:
            print(f"[erreur infos horloge] {e}")

    def poll_pc_resume():
        """v2.15.0 : détecte la sortie de veille du PC. Pendant la veille
        l'USB se suspend et le firmware du deck redémarre : il affiche son
        logo de démarrage. Cette boucle (1 s) mesure l'écart d'horloge
        murale : > PC_RESUME_GAP_S = le PC vient de se réveiller. On
        attend resume_repaint_delay s (défaut 3) que l'USB se stabilise,
        puis re-handshake + repaint complet (l'affichage repart où il
        en était)."""
        delay = config.get("resume_repaint_delay", 3)
        last = time.time()
        while True:
            time.sleep(1.0)
            now = time.time()
            gap = now - last
            last = now
            if gap < PC_RESUME_GAP_S:
                continue  # simple battement de 1 s : le PC n'a pas dormi
            print(f"[resume] sortie de veille du PC détectée "
                  f"(pause de {int(gap)} s)")

            def repaint_after_resume():
                time.sleep(delay)
                try:
                    with device.lock:
                        device._send(crt_command("DIS"))
                        device._send(crt_command("LIG", [0, 0,
                                                         device.brightness]))
                        device._send(crt_command("CLE", [0, 0, 0, 0xFF]))
                        device._send(crt_command("STP"))
                    if _repaint_all():
                        print("[resume] deck repeint après le réveil du PC")
                    return
                except Exception:
                    pass
                # liaison HID morte : reconnexion complète puis repaint
                if not device.reconnect():
                    print("[resume] deck injoignable — relance "
                          "l'application si besoin")
                    return
                if _repaint_all():
                    print("[resume] deck reconnecté et repeint")

            threading.Thread(target=repaint_after_resume,
                             daemon=True).start()

    def poll_clock():
        """Rafraîchit la touche horloge de la page courante quand le
        texte change (début de minute) — pas de trafic HID inutile."""
        last_sig = None
        while True:
            try:
                gen = page_paint["gen"]
                page = page_cfg()
                # écran d'infos (easter egg horloge) : retour auto
                # à l'horloge après ~8 s, abandonné si la page a changé
                if clock_info["btn"] is not None:
                    expired = time.monotonic() >= clock_info["until"]
                    if expired or page_paint["gen"] != clock_info["gen"]:
                        if (expired and page_paint["gen"] == clock_info["gen"]
                                and clock_info["btn"] in (page.get("buttons")
                                                          or {})):
                            entry = page["buttons"][clock_info["btn"]]
                            if (entry.get("action") or {}).get("type") == "clock":
                                paint_clock_button(int(clock_info["btn"]),
                                                   entry)
                        clock_info["btn"] = None
                for bn, entry in (page.get("buttons") or {}).items():
                    if (entry.get("action") or {}).get("type") != "clock":
                        continue
                    if bn == clock_info["btn"]:
                        continue  # écran d'infos affiché : ne pas écraser
                    if page_paint["gen"] != gen:
                        break  # page changée : ne pas écraser
                    now = time.localtime()
                    sig = (now.tm_hour, now.tm_min,
                           now.tm_wday, now.tm_mday, now.tm_mon)
                    if sig != last_sig:
                        last_sig = sig
                        paint_clock_button(int(bn), entry)
            except Exception as e:
                print(f"[erreur horloge] {e}")
            time.sleep(1.0)

    device.on_brightness = lambda pct: refresh_strip()
    device.on_strip_refresh = refresh_strip

    # --- LYRION MEDIA SERVER (LMS / Squeezebox) --------------------------
    lms = LMSClient((config.get("lms") or {}).get("host", ""),
                    (config.get("lms") or {}).get("port", 9000))
    if not lms.enabled:
        print("[lms] LMS non configuré — pour détecter votre serveur "
              "Lyrion :  python akp05e_app.py --setup-lms")
    lms_state = {"players": [],       # lecteurs découverts (poll)
                 "favorites": [],     # favoris radios LMS
                 "selected": 0,       # index du lecteur sélectionné
                 "viewed": None,      # id du lecteur affiché (page détail)
                 "fav_offset": 0,     # décalage de la page favoris
                 "viewed_muted": False,  # état muet du lecteur affiché
                 "favs_logged": False,   # découverte des favoris loggée ?
                 "loaded": False,     # première découverte faite ?
                 "launched_fav": {},  # lecteur -> id favori lancé depuis le deck
                 "playing": None,     # status du flux en cours (lecteur affiché)
                 "active_diag": False,  # diagnostic radio active déjà loggé ?
                 "apps": [],           # applis LMS découvertes (poll)
                 "apps_offset": 0,     # décalage de la page applis
                 "apps_tries": 0,      # tentatives de découverte des applis
                 "browse": [],         # pile de navigation appli courante
                 "browse_offset": 0,   # décalage de la page navigation
                 "album": None,        # album affiché (page lms_album)
                 "now_title": None,   # v2.19.0 : titre affiché sur le bandeau
                 "now_artist": None}  # v2.19.0 : artiste affiché
    lms_lock = threading.RLock()

    def lms_selected():
        with lms_lock:
            ps = lms_state["players"]
            if not ps:
                return None
            return ps[min(lms_state["selected"], len(ps) - 1)]

    def lms_viewed():
        """Lecteur affiché sur la page détail (None si aucun)."""
        with lms_lock:
            vid = lms_state["viewed"]
            for p in lms_state["players"]:
                if p["id"] == vid:
                    return p
        return None

    def lms_refresh_viewed():
        """Met à jour le volume % et l'état muet RÉELS du lecteur affiché :
        la requête « players » de LMS ne renvoie pas « mixer volume », on
        interroge donc explicitement « mixer volume ? » (et muting ?)."""
        vp = lms_viewed()
        if not vp:
            return
        with lms_lock:
            v = lms.volume_state(vp["id"])
            if v is not None:
                vp["volume"] = v
            lms_state["viewed_muted"] = lms.mute_state(vp["id"])
            try:
                # v2.13.9 : info maintenue aussi EN PAUSE (lecteur
                # allumé) -> la zone 3 garde la position « i/N »
                lms_state["playing"] = (lms.playing_track(vp["id"])
                                         if vp.get("power") else None)
            except Exception as e:
                lms_state["playing"] = None
                if not _Z3_DIAG["err"]:
                    _Z3_DIAG["err"] = True
                    print(f"[lms] playing_info a échoué : {e!r} — "
                          "copie cette ligne")

    def paint_lms_button(n, entry):
        """Touche LMS : libellés dynamiques (lecteurs, favoris, états)
        rafraîchis par poll_lms."""
        t = (entry.get("action") or {}).get("type") or ""
        label = entry.get("label") or ""
        btn_player = None  # lecteur représenté (pour le logo Touch/Radio)
        btn_audio = False  # élément de navigation jouable (morceau) ?
        empty = False       # touche de liste sans contenu -> éteinte
        sub = ""
        bg, fg = (15, 15, 15), (240, 240, 240)
        with lms_lock:
            players = list(lms_state["players"])
            favs = list(lms_state["favorites"])
            fav_off = lms_state["fav_offset"]
            launched = dict(lms_state["launched_fav"])
            playing = lms_state["playing"]
            active_diag = lms_state["active_diag"]
            apps_l = list(lms_state["apps"])
            apps_off = lms_state["apps_offset"]
            browse_l = list(lms_state["browse"])
            browse_off = lms_state["browse_offset"]
            album = lms_state["album"]
        sel = lms_selected()
        vp = lms_viewed()
        if not lms.enabled:
            sub = "config off"
        elif not players and t not in ("lms_open_favs", "lms_open_apps",
                                       "lms_back", "lms_back_player",
                                       "lms_play_url", "lms_browse_back",
                                       "lms_album_back",
                                       "lms_album_scroll"):
            sub = "LMS ?"
        elif t == "lms_open_player":
            i = int((entry.get("action") or {}).get("index", 0))
            if 0 <= i < len(players):
                p = players[i]
                label = short_player_name(p["name"])
                btn_player = p
                if p["power"]:
                    bg = ((26, 80, 38), (5, 11, 7))  # dégradé vert->noir
                    sub = (">> " + p["title"][:8]) if p["playing"] else "allumé"
                else:
                    sub = "veille"
            else:
                label, sub = "", ""
                empty = True
        elif t == "lms_player_id":
            btn_player = vp
            if vp:
                label = short_player_name(vp["name"])
                sub = "Lyrion"
                if vp["power"]:
                    bg = ((30, 92, 40), (6, 13, 9))  # dégradé vert->noir
            else:
                label, sub = "Lecteur", "LMS ?"
        elif t == "lms_player_power":
            label = "Alim"
            sub = "allumé" if vp and vp["power"] else "éteint"
        elif t == "lms_player_playpause":
            label = "Lecture"
            if vp and vp["playing"]:
                sub = ">> " + (vp["title"] or "?")[:8]
            else:
                sub = "|| pause"
        elif t == "lms_fav_press":
            i = fav_off + int((entry.get("action") or {}).get("slot", 0))
            if 0 <= i < len(favs):
                label = favs[i]["name"][:16]
                lid = launched.get(vp["id"]) if vp else None
                ai = lms_viewed_active_fav(vp, favs, lid, playing)
                if ai < 0 and vp and vp.get("playing") and not active_diag:
                    # DIAGNOSTIC (une seule fois) : le lecteur joue mais
                    # aucun favori ne correspond -> on montre ce que le
                    # serveur renvoie pour identifier le bon champ
                    with lms_lock:
                        lms_state["active_diag"] = True
                    p = playing or {}
                    print("[lms] diagnostic radio active — station="
                          f"{p.get('title')!r}, titre="
                          f"{p.get('current_title')!r}, "
                          f"url={p.get('url')!r} ; favoris : "
                          + ", ".join(f"{f['name']}={f.get('url')!r}"
                                      for f in favs[:7]))
                if ai == i:
                    # dégradé bleu (haut) -> noir (bas) : radio active
                    bg = ((24, 72, 190), (6, 10, 26))
                    fg = (255, 255, 255)
                    sub = ">> en cours"
                else:
                    sub = "radio"
            else:
                label, sub = "", ""
                empty = True
        elif t == "lms_app_press":
            i = apps_off + int((entry.get("action") or {}).get("slot", 0))
            if 0 <= i < len(apps_l):
                label = apps_l[i]["name"]
                sub = "appli"
            else:
                label, sub = "", ""
                empty = True
        elif t == "lms_item_press":
            lvl = browse_l[-1] if browse_l else None
            i = browse_off + int((entry.get("action") or {}).get("slot", 0))
            if lvl and 0 <= i < len(lvl["items"]):
                it = lvl["items"][i]
                label = str(it.get("name") or it.get("title") or "?")
                btn_audio = lms_item_go(it)[3]
                sub = "lecture" if btn_audio else "dossier"
            else:
                label, sub = "", ""
                empty = True
        elif t == "lms_album_play":
            if album:
                label = "Jouer l'album"
                sub = f"{len(album['tracks'])} morceaux"
            else:
                label, sub = "", ""
                empty = True
        elif t == "lms_album_press":
            if album:
                i = album["off"] + int((entry.get("action") or {})
                                       .get("slot", 0))
                if 0 <= i < len(album["tracks"]):
                    it = album["tracks"][i]
                    label = str(it.get("name") or it.get("title") or "?")
                    if i == album["sel"]:
                        # morceau sélectionné : dégradé bleu (comme la
                        # radio active) pour montrer la sélection knob 3
                        bg = ((24, 72, 190), (6, 10, 26))
                        fg = (255, 255, 255)
                        sub = ">> sélection"
                    else:
                        sub = "morceau"
                else:
                    label, sub = "", ""
                    empty = True
            else:
                label, sub = "", ""
                empty = True
        elif t == "lms_power_all":
            on = sum(1 for q in players if q["power"])
            sub = f"{on}/{len(players)} allumés"
        elif t == "lms_select_player":
            sub = (sel["name"] if sel else "-")[:10]
        elif t == "lms_playpause":
            if sel and sel["playing"]:
                sub = ">> " + (sel["title"] or "?")[:8]
            elif sel:
                sub = "|| pause"
        elif t == "lms_sync":
            sub = ("synchro" if any(q["sync_master"] for q in players)
                   else "indep.")
        elif t == "lms_favorite":
            i = int((entry.get("action") or {}).get("index", 0))
            if 0 <= i < len(favs):
                label = favs[i]["name"][:16]
                lid = launched.get(sel["id"]) if sel else None
                if (lms_viewed_active_fav(sel, favs, lid, playing) == i):
                    # dégradé bleu (haut) -> noir (bas) : radio active
                    bg = ((24, 72, 190), (6, 10, 26))
                    fg = (255, 255, 255)
                    sub = ">> en cours"
                else:
                    sub = "radio"
            else:
                sub = "(vide)"
        if not label:
            label = "LMS"
        # petits logos d'action (v2.7.0) — play/pause suit l'état réel
        icons_lms = {
            "lms_open_player": "speaker",
            "lms_player_id": "speaker",
            "lms_player_power": "power_settings_new",
            "lms_player_playpause": ("pause" if vp and vp.get("playing")
                                    else "play_arrow"),
            "lms_fav_press": "radio",
            "lms_power_all": "power_settings_new",
            "lms_select_player": "swap_horiz",
            "lms_playpause": ("pause" if sel and sel.get("playing")
                              else "play_arrow"),
            "lms_sync": "sync",
            "lms_favorite": "radio",
        }
        icon = icons_lms.get(t)
        if t in ("lms_open_player", "lms_player_id"):
            icon = player_icon(btn_player)
        elif t == "lms_app_press":
            i = apps_off + int((entry.get("action") or {}).get("slot", 0))
            c = (apps_l[i]["cmd"].lower() if 0 <= i < len(apps_l) else "")
            icon = ("library_music" if "qobuz" in c
                    else "radio" if ("paradise" in c or "radio" in c)
                    else "extension")
        elif t == "lms_item_press":
            icon = "music_note" if btn_audio else "folder_open"
        elif t == "lms_album_play":
            icon = "album"
        elif t == "lms_album_press":
            icon = "music_note"
        if empty:
            # liste épuisée : touche éteinte, propre (pas de « (vide) »)
            device.set_image(n, Image.new("RGB", BUTTON_IMAGE_SIZE,
                                          (12, 12, 12)))
            return
        # boutons de navigation/applis : on garde leur icône statique
        if (t in ("lms_open_favs", "lms_open_apps", "lms_back",
                  "lms_back_player", "lms_play_url", "lms_browse_back",
                  "lms_album_back")
                and entry.get("icon")):
            set_icon(device, n, entry["icon"],
                     fg=entry.get("color", "#e0e0e0"),
                     bg=entry.get("bg", "#101010"),
                     label=entry.get("label"))
            return
        device.set_label(n, label, bg=bg, fg=fg, sub=sub, small=True,
                         icon=icon)

    def paint_lms_page():
        """Repeint toutes les touches LMS de la page courante."""
        buttons = page_cfg().get("buttons") or {}
        gen = page_paint["gen"]
        for bn, entry in buttons.items():
            if page_paint["gen"] != gen:
                return  # page changée pendant la peinture : abandon
            if str((entry.get("action") or {}).get("type")
                   or "").startswith("lms"):
                try:
                    paint_lms_button(int(bn), entry)
                except Exception as e:
                    print(f"[erreur lms peinture] {e}")

    def lms_play_fav(player, fav):
        """Joue un favori (id « url: » = webradio manuelle)."""
        lms_play_fav_entry(lms, player, fav)

    def lms_action(action):
        """Exécutée dans un thread : commande LMS puis rafraîchissement."""
        if not lms.enabled:
            print('[lms] non configuré : renseigne "lms": {"host": ...} '
                  'dans akp05e_config.json')
            return
        t = action.get("type")
        sel = lms_selected()
        vp = lms_viewed()
        # sur les pages détail/favoris/applis, volume et muet visent le
        # lecteur AFFICHÉ, pas le « sélectionné »
        tgt = (vp or sel) if current["name"] in LMS_PAGE_NAMES[1:] else sel
        if t == "lms_volume" and tgt:
            step = int(action.get("step", 5))
            d = step if action.get("dir") == "up" else -step
            lms.volume(tgt["id"], d)
            # v2.14.4 : le bandeau suivait le knob avec jusqu'à 2 s de
            # retard (refresh seulement au cycle poll_lms) -> mise à
            # jour OPTIMISTE + repaint immédiat ; le poll resynchronise
            # le volume réel du serveur (lms_refresh_viewed)
            with lms_lock:
                tgt["volume"] = max(0, min(100, int(tgt.get("volume", 50)) + d))
            if current["name"] in LMS_PAGE_NAMES[1:]:
                refresh_strip()
        elif t == "lms_mute" and tgt:
            lms.mute_toggle(tgt["id"])
            # v2.14.4 : idem, repaint immédiat de l'état muet
            with lms_lock:
                lms_state["viewed_muted"] = not lms_state["viewed_muted"]
            if current["name"] in LMS_PAGE_NAMES[1:]:
                refresh_strip()
        elif t == "lms_power_all":
            with lms_lock:
                players = list(lms_state["players"])
            on = any(q["power"] for q in players)
            lms.power_all(not on)
        elif t == "lms_power_selected" and sel:
            lms.power(sel["id"], not sel["power"])
        elif t == "lms_select_player":
            with lms_lock:
                n = len(lms_state["players"])
                if n:
                    d = -1 if action.get("dir") == "prev" else 1
                    lms_state["selected"] = ((lms_state["selected"] + d)
                                             % n)
        elif t == "lms_playpause" and sel:
            lms.playpause(sel["id"], sel["playing"])
        elif t == "lms_sync" and sel:
            with lms_lock:
                players = list(lms_state["players"])
            if any(q["sync_master"] for q in players):
                lms.desync_all()
            else:
                lms.sync_all(sel["id"])
        elif t == "lms_favorite" and sel:
            with lms_lock:
                favs = list(lms_state["favorites"])
            i = int(action.get("index", 0))
            if 0 <= i < len(favs):
                lms_play_fav(sel["id"], favs[i])
        elif t == "lms_open_player":
            with lms_lock:
                ps = list(lms_state["players"])
            i = int(action.get("index", 0))
            if 0 <= i < len(ps):
                with lms_lock:
                    lms_state["viewed"] = ps[i]["id"]
                    lms_state["fav_offset"] = 0
                switch_page("lms_player")
        elif t == "lms_player_power" and vp:
            lms.power(vp["id"], not vp["power"])
        elif t == "lms_player_playpause" and vp:
            lms.playpause(vp["id"], vp["playing"])
        elif t == "lms_open_favs":
            with lms_lock:
                lms_state["fav_offset"] = 0
            switch_page("lms_favs")
        elif t == "lms_fav_press" and vp:
            with lms_lock:
                favs = list(lms_state["favorites"])
                i = lms_state["fav_offset"] + int(action.get("slot", 0))
            if 0 <= i < len(favs):
                lms_play_fav(vp["id"], favs[i])
                with lms_lock:
                    lms_state["launched_fav"][vp["id"]] = favs[i]["id"]
        elif t == "lms_favs_scroll":
            with lms_lock:
                nf = len(lms_state["favorites"])
                d = -9 if action.get("dir") == "prev" else 9
                lms_state["fav_offset"] = max(0, min(
                    lms_state["fav_offset"] + d, max(0, nf - 9)))
        elif t == "lms_open_apps":
            with lms_lock:
                lms_state["apps_offset"] = 0
            switch_page("lms_apps")
        elif t == "lms_app_press" and vp:
            with lms_lock:
                apps_l = list(lms_state["apps"])
                i = lms_state["apps_offset"] + int(action.get("slot", 0))
            if apps_l and 0 <= i < len(apps_l):
                items = lms.app_items(vp["id"], apps_l[i]["cmd"],
                                      apps_l[i].get("params"))
                appcmd = (list(apps_l[i]["cmd"])
                          if isinstance(apps_l[i]["cmd"], (list, tuple))
                          else str(apps_l[i]["cmd"]).split())
                with lms_lock:
                    lms_state["browse"] = [{"title": apps_l[i]["name"],
                                            "items": items,
                                            "cmd": appcmd,
                                            "params": []}]
                    lms_state["browse_offset"] = 0
                print(f"[lms] appli {apps_l[i]['name']} : "
                      f"{len(items)} éléments")
                switch_page("lms_browse")
        elif t == "lms_apps_scroll":
            with lms_lock:
                na = len(lms_state["apps"])
                d = -9 if action.get("dir") == "prev" else 9
                lms_state["apps_offset"] = max(0, min(
                    lms_state["apps_offset"] + d, max(0, na - 9)))
        elif t == "lms_item_press" and vp:
            with lms_lock:
                lvl = (lms_state["browse"][-1]
                       if lms_state["browse"] else None)
                i = lms_state["browse_offset"] + int(action.get("slot", 0))
            it = (lvl["items"][i]
                  if lvl and 0 <= i < len(lvl["items"]) else None)
            if it:
                url, cmd, params, playable = lms_item_go(it)
                # v2.13.2 : un item « hasitems » (drillable) n'est pas joué
                # en direct même s'il a une URL — sinon le clic sur un ALBUM
                # (qobuz renvoie des URLs d'album avec want_url) lirait
                # l'album sans jamais ouvrir la page « album ».
                if playable and url and not it.get("hasitems"):
                    lms.play_url(vp["id"], url)
                    print(f"[lms] lecture : "
                          f"{it.get('name') or it.get('title') or url}")
                elif cmd:
                    lms_open_level(vp, it, cmd, params, url,
                                   lms, lms_state, lms_lock, switch_page)
                elif lvl and it.get("id") is not None:
                    # dossier SANS cmd (diagnostic David : Main Mix,
                    # clés=[hasitems, id, isaudio, name, type]) :
                    # protocole CLI strict — on RENVOIE la commande du
                    # niveau courant + item_id:<id> (comme les favoris)
                    dcmd = [str(w) for w in (lvl.get("cmd") or [])]
                    if dcmd:
                        dparams = ([str(p) for p in (lvl.get("params") or [])]
                                   + [f"item_id:{it['id']}"])
                        lms_open_level(vp, it, dcmd, dparams, url,
                                       lms, lms_state, lms_lock, switch_page)
                else:
                    # diagnostic (comme les favoris v2.4) : à copier dans
                    # une conversation pour identifier le format du serveur
                    print(f"[lms] élément non jouable — nom="
                          f"{(it.get('name') or it.get('title'))!r}, "
                          f"type={it.get('type')!r}, "
                          f"clés={sorted(it.keys())}, "
                          f"actions={str(it.get('actions'))[:250]}")
        elif t == "lms_browse_scroll":
            with lms_lock:
                lvl = (lms_state["browse"][-1]
                       if lms_state["browse"] else None)
                ni = len(lvl["items"]) if lvl else 0
                d = -9 if action.get("dir") == "prev" else 9
                lms_state["browse_offset"] = max(0, min(
                    lms_state["browse_offset"] + d, max(0, ni - 9)))
        elif t == "lms_browse_back":
            with lms_lock:
                if lms_state["browse"]:
                    lms_state["browse"].pop()
                lms_state["browse_offset"] = 0
                empty = not lms_state["browse"]
            if empty:
                switch_page("lms_apps")
        elif t == "lms_album_play" and vp:
            with lms_lock:
                album = lms_state["album"]
                urls = list(album["urls"]) if album else []
            if urls:
                # album entier : power on (via play_url du 1er morceau)
                # puis les suivants en file — LMS joue le 1er immédiatement
                lms.play_url(vp["id"], urls[0])
                for u in urls[1:]:
                    lms.request(vp["id"], ["playlist", "add", u])
                print(f"[lms] album entier : {len(urls)} morceaux "
                      f"sur {vp['name']}")
        elif t == "lms_play_level" and vp:
            # v2.14.0 : zone 3 — pause/reprise UNIQUEMENT si la piste en
            # cours appartient au NIVEAU AFFICHÉ (sinon album2 lance
            # album2 même si album1 joue) ; autre contenu ou lecteur
            # arrêté -> lancement du niveau complet (v2.13.5)
            with lms_lock:
                lvl = (lms_state["browse"][-1]
                       if lms_state["browse"] else None)
                items = list(lvl["items"]) if lvl else []
                title = lvl["title"] if lvl else "?"
                _pl = lms_state.get("playing")
            urls = lms_level_urls(items)
            if _pl and _pl.get("url"):
                _pu = _url_key(_pl.get("url"))
            else:
                _pi = lms.playing_track(vp["id"]) if lms.enabled else None
                _pu = _url_key(_pi.get("url")) if _pi else ""
            _in = bool(urls and _pu
                       and _pu in {_url_key(u) for u in urls})
            m = lms.mode(vp["id"])
            if _in and m == "play":
                lms.playpause(vp["id"], True)
                print(f"[lms] pause ({vp['name']})")
                return
            if _in and m == "pause":
                lms.playpause(vp["id"], False)
                print(f"[lms] reprise ({vp['name']})")
                return
            if len(urls) >= 2:
                lms.play_url(vp["id"], urls[0])
                for u in urls[1:]:
                    lms.request(vp["id"], ["playlist", "add", u])
                print(f"[lms] album entier « {title} » : {len(urls)} "
                      f"morceaux sur {vp['name']}")
            elif len(urls) == 1:
                lms.play_url(vp["id"], urls[0])
                print(f"[lms] lecture : {title} (1 morceau jouable)")
            else:
                print("[lms] rien à jouer sur cette page "
                      "(pas de morceau avec URL)")
        elif t == "lms_album_press" and vp:
            with lms_lock:
                album = lms_state["album"]
                i = (album["off"] + int(action.get("slot", 0))
                     if album else -1)
                url = album["urls"][i] if album and 0 <= i < len(
                    album["urls"]) else None
            if url:
                lms.play_url(vp["id"], url)
        elif t == "lms_album_scroll":
            d = -1 if action.get("dir") == "prev" else 1
            with lms_lock:
                album = lms_state["album"]
                if album:
                    n = len(album["tracks"])
                    album["sel"] = max(0, min(album["sel"] + d, n - 1))
                    # garde la sélection visible dans la fenêtre 2-9
                    if album["sel"] < album["off"]:
                        album["off"] = album["sel"]
                    elif album["sel"] > album["off"] + 7:
                        album["off"] = album["sel"] - 7
        elif t == "lms_album_play_sel" and vp:
            with lms_lock:
                album = lms_state["album"]
                url = (album["urls"][album["sel"]]
                       if album and album["urls"] else None)
            if url:
                lms.play_url(vp["id"], url)
        elif t == "lms_album_back":
            switch_page("lms_browse")
        elif t == "lms_play_url" and vp:
            lms.play_url(vp["id"], action.get("url") or "")
        elif t == "lms_back":
            with lms_lock:
                lms_state["viewed"] = None  # quitte la squeezebox :
            switch_page("lms")            # knob 1 -> volume système
        elif t == "lms_back_player":
            switch_page("lms_player")
        # rafraîchit l'état (et l'affichage si on est sur une page LMS)
        with lms_lock:
            players = lms.players()
            if players:
                lms_state["players"] = players
        lms_refresh_viewed()
        if current["name"] in LMS_PAGE_NAMES:
            paint_lms_page()
            refresh_strip()

    def poll_lms():
        """Découvre les lecteurs/favoris, rafraîchit la page LMS (2 s)."""
        while True:
            try:
                if lms.enabled:
                    # découverte des applis LMS (Qobuz, Radio Paradise...)
                    # — réessayée tant que rien n'est trouvé (5 max)
                    found_apps = None
                    with lms_lock:
                        if (not lms_state["apps"]
                                and lms_state["apps_tries"] < 5):
                            lms_state["apps_tries"] += 1
                            tries = lms_state["apps_tries"]
                        else:
                            tries = 99
                    if tries < 99:
                        with lms_lock:
                            ps0 = (lms_state["players"] or [{}])[0]
                        found_apps = lms.apps(ps0.get("id"))
                        if found_apps:
                            with lms_lock:
                                lms_state["apps"] = found_apps
                            names = ", ".join(a["name"]
                                              for a in found_apps[:6])
                            more = ("…" if len(found_apps) > 6 else "")
                            print(f"[lms] {len(found_apps)} applis — "
                                  f"{names}{more}")
                        elif tries >= 5:
                            print("[lms] aucune appli trouvée (apps 0 100, "
                                  "radios 0 100, avec/sans lecteur) — "
                                  "vérifie que les plugins sont activés "
                                  "dans les réglages LMS")
                            raw = lms.apps_raw()
                            print("[lms] diagnostic apps — réponse brute : "
                                  f"{str(raw)[:600]}")
                    with lms_lock:
                        players = lms.players()
                        if players:
                            lms_state["players"] = players
                            if not lms_state["favorites"]:
                                manual = []
                                for r in (_lms_cfg.get("radios") or []):
                                    if (isinstance(r, dict)
                                            and r.get("name")
                                            and r.get("url")):
                                        manual.append({
                                            "id": "url:" + str(r["url"]),
                                            "name": str(r["name"]),
                                            "url": str(r["url"])})
                                found = lms.favorites(
                                    (config.get("lms") or {}).get("folder"))
                                known = {f["name"].strip().lower()
                                         for f in manual}
                                favs = manual + [
                                    f for f in found
                                    if (f["name"] or "").strip().lower()
                                    not in known]
                                lms_state["favorites"] = favs
                                if not lms_state["favs_logged"]:
                                    lms_state["favs_logged"] = True
                                    if favs:
                                        names = ", ".join(
                                            f["name"] for f in favs[:6])
                                        more = "…" if len(favs) > 6 else ""
                                        src = (""
                                               + (f"{len(manual)} manuelle(s)"
                                                  if manual else "")
                                               + (" + " if manual
                                                  and len(found) else "")
                                               + (f"{len(found)} favoris"
                                                  if found else ""))
                                        print(f"[lms] {len(favs)} radios "
                                              f"({src}) — {names}{more}")
                                    elif manual:
                                        pass
                                    else:
                                        print("[lms] aucun favori trouvé "
                                              "sur le serveur — ajoute tes "
                                              "radios dans la config "
                                              '("lms": {"radios": [{"name": '
                                              '"FIP", "url": "http://…"}]}), '
                                              "ou vérifie l'écran Favoris "
                                              "de LMS (Radios Internet, "
                                              "TuneIn…)")
                            if not lms_state["loaded"]:
                                lms_state["loaded"] = True
                                print(f"[lms] connecté : {len(players)} "
                                      "lecteurs — "
                                      + ", ".join(q["name"] for q in players))
                    lms_refresh_viewed()
                    # v2.19.0 : titre du morceau pour le bandeau (zone 3)
                    # — lecteur affiché s'il joue, sinon 1er lecteur actif ;
                    # l'artiste n'est demandé qu'AU CHANGEMENT de titre
                    # (une requête par morceau, pas par cycle de 2 s).
                    with lms_lock:
                        _cand = None
                        for _p in ((lms_viewed(),)
                                   + tuple(lms_state["players"])):
                            if (_p and _p.get("playing")
                                    and _p.get("id")):
                                _cand = _p
                                break
                        _prev = lms_state.get("now_title")
                        _prev_na = lms_state.get("now_artist")
                        _viewed = lms_viewed()
                        _pl = lms_state.get("playing")
                        # v2.19.4 : « isplaying » du poll « players »
                        # n'est pas fiable chez certains serveurs/modèles
                        # (Squeezebox Radio : jamais isplaying=1 alors que
                        # le status dit mode=play) -> le lecteur AFFICHÉ
                        # dont le status dit « play » devient le candidat
                        if (not _cand and _viewed and _viewed.get("id")
                                and _pl
                                and str(_pl.get("mode") or "") == "play"):
                            _cand = _viewed
                            if not _Z3_DIAG["nopb"]:
                                _Z3_DIAG["nopb"] = True
                                try:
                                    _raw = lms.request("", ["players", 0, 50])
                                except Exception as _e:
                                    _raw = repr(_e)
                                print(f"[lms] bandeau : isplaying=0 dans "
                                      f"le poll players pour "
                                      f"{_viewed.get('name')!r} alors que "
                                      f"mode={_pl.get('mode')!r} — "
                                      f"players -> {str(_raw)[:500]!r} — "
                                      "copie cette ligne")
                    _nt = str((_cand or {}).get("title") or "").strip()
                    _na = None
                    # v2.19.1 : le champ « title » du poll « players » est
                    # souvent VIDE -> on privilégie le « status » du lecteur
                    # AFFICHÉ, déjà interrogé chaque cycle par
                    # lms_refresh_viewed (zéro requête supplémentaire).
                    if (_cand and _viewed and _pl
                            and _cand.get("id") == _viewed.get("id")):
                        # v2.19.8 : titre prioritaire sur current_title —
                        # chez les serveurs « remoteMeta », current_title
                        # est le NOM DE LA STATION et title le morceau live
                        _nt = str(_pl.get("title")
                                  or _pl.get("current_title")
                                  or "").strip() or _nt
                    if _cand and not _nt:
                        # toujours rien -> requête « status » dédiée
                        # (une par cycle tant qu'on n'a pas le titre)
                        try:
                            _t2, _na = lms.now_info(_cand["id"])
                        except Exception:
                            _t2, _na = None, None
                        if _t2:
                            _nt = str(_t2).strip()
                        elif not _Z3_DIAG["ntitle"]:
                            _Z3_DIAG["ntitle"] = True
                            try:
                                _raw = lms.request(
                                    _cand["id"],
                                    ["status", "-", "1", "tags:uA"])
                            except Exception as _e:
                                _raw = repr(_e)
                            print(f"[lms] bandeau : titre indisponible "
                                  f"pour {_cand.get('name')!r} — status -> "
                                  f"{str(_raw)[:200]!r} — copie cette ligne")
                        # v2.19.7 : cette branche (titre absent du poll
                        # players ET lecteur affiché != candidat) tourne à
                        # CHAQUE cycle — le dump one-shot y manquait, il ne
                        # pouvait jamais tirer depuis les autres branches
                        if (_cand and not _Z3_DIAG["radio"]):
                            try:
                                _Z3_DIAG["radio"] = _lms_dump_playing(
                                    lms, _cand)
                            except Exception:
                                _Z3_DIAG["radio"] = True
                    elif _nt and _nt != _prev:
                        # titre connu mais changé -> artiste une seule fois
                        try:
                            _t2, _na = lms.now_info(_cand["id"])
                        except Exception:
                            _t2, _na = None, None
                        if _t2:
                            _nt = str(_t2).strip() or _nt
                        # v2.19.6 : dump one-shot INCONDITIONNEL (les
                        # conditions de détection de flux n'ont jamais
                        # matché le serveur réel de David) — status brut
                        # + playing_track brut, une fois par lancement
                        if (_cand and not _Z3_DIAG["radio"]):
                            try:
                                _Z3_DIAG["radio"] = _lms_dump_playing(
                                    lms, _cand)
                            except Exception:
                                _Z3_DIAG["radio"] = True
                    elif _nt:
                        _na = _prev_na
                        # v2.19.2 : webradio — le titre du flux ne change
                        # jamais (« FIP (MP3) ») mais le morceau diffusé si ;
                        # re-poll de now_info toutes les ~20 s (10 cycles)
                        # pour suivre les infos live de la radio
                        _Z3_CYCLE[0] += 1
                        if _Z3_CYCLE[0] >= 10:
                            _Z3_CYCLE[0] = 0
                            try:
                                _t2, _na2 = lms.now_info(_cand["id"])
                            except Exception:
                                _t2, _na2 = None, None
                            # v2.19.3 : titre et artiste mis à jour
                            # INDEPENDAMMENT — avant, l'artiste restait
                            # figé tant que le titre n'était pas trouvé
                            if _t2:
                                _nt = str(_t2).strip()
                            if _na2:
                                _na = _na2
                            # v2.19.6 : dump one-shot INCONDITIONNEL si
                            # jamais tombé (re-poll ~20 s)
                            if (_cand and not _Z3_DIAG["radio"]):
                                try:
                                    _Z3_DIAG["radio"] = _lms_dump_playing(
                                        lms, _cand)
                                except Exception:
                                    _Z3_DIAG["radio"] = True
                    with lms_lock:
                        lms_state["now_title"] = _nt or None
                        lms_state["now_artist"] = _na
                        _changed = ((_nt or None) != (_prev or None))
                    if _changed and current["name"] not in LMS_PAGE_NAMES:
                        refresh_strip()
                    if current["name"] in LMS_PAGE_NAMES:
                        paint_lms_page()
                        refresh_strip()
            except Exception as e:
                print(f"[erreur lms] {e}")
            time.sleep(2.0)

    # --- PAGES AUTOMATIQUES (application au premier plan) ---------------
    auto_state = {"match": None,          # (clé, page) de l'app active
                  "return_page": None,    # page à restaurer en quittant
                  "manual": False}        # navigation manuelle récente
    auto_lock = threading.RLock()

    def poll_auto_pages():
        """Bascule vers la page associée à l'application au premier plan
        (clé "auto_pages" : nom d'exe -> page). Revient à la page
        précédente quand on la quitte ; une navigation manuelle est
        respectée tant que l'application active ne change pas."""
        while True:
            try:
                cfg_auto = config.get("auto_pages") or {}
                if not cfg_auto:
                    time.sleep(1.5)
                    continue
                exe = get_foreground_app()
                match = None
                if exe:
                    for key, page in cfg_auto.items():
                        if key.lower() in exe:
                            match = (key, page)
                            break
                with auto_lock:
                    if match != auto_state["match"]:
                        was_manual = auto_state["manual"]
                        auto_state["match"] = match
                        auto_state["manual"] = False
                        if match:
                            target = match[1]
                            if target == "accueil" or target in pages:
                                if current["name"] == target:
                                    auto_state["return_page"] = None
                                else:
                                    auto_state["return_page"] = current["name"]
                                    print(f"[auto] {match[0]} -> page {target}")
                                    switch_page(target)
                        else:
                            ret = auto_state["return_page"]
                            auto_state["return_page"] = None
                            if (ret and not was_manual
                                    and (ret == "accueil" or ret in pages)
                                    and current["name"] != ret):
                                print(f"[auto] retour -> page {ret}")
                                switch_page(ret)
                    elif match and not auto_state["manual"]:
                        # même application mais page changée manuellement :
                        # on ne force pas le retour
                        if current["name"] != match[1]:
                            auto_state["manual"] = True
            except Exception as e:
                print(f"[erreur pages auto] {e}")
            time.sleep(1.0)

    def poll_hardware():
        """Met à jour les touches capteurs de la page courante toutes les
        `refresh` secondes (défaut 2). Ne fait rien si HWiNFO est absent."""
        warned_off, warned_missing = False, set()
        while True:
            try:
                page = page_cfg()
                gen = page_paint["gen"]
                hw_btns = {n: e for n, e in (page.get("buttons") or {}).items()
                           if "hw" in e}
                if not hw_btns:
                    time.sleep(2)
                    continue
                readings = hwinfo_readings()
                if readings is None:
                    if not warned_off:
                        warned_off = True
                        print("[hardware] HWiNFO64 introuvable (mémoire partagée "
                              "absente) — relance avec HWiNFO64 ouvert, "
                              "« Shared Memory Support » activé.")
                else:
                    warned_off = False
                    thresholds = page.get("thresholds", [70, 85])
                    for n, entry in hw_btns.items():
                        if page_paint["gen"] != gen:
                            break  # page changée : ne pas écraser
                        r = hw_match(readings, entry["hw"])
                        if r is None and n not in warned_missing:
                            warned_missing.add(n)
                            print(f"[hardware] capteur introuvable : {entry['hw']!r} "
                                  "(cf. --list-sensors)")
                        paint_hw_button(device, int(n),
                                        entry.get("label") or entry["hw"], r,
                                        thresholds)
                time.sleep(page.get("refresh", 2) or 2)
            except Exception as e:
                print(f"[erreur hardware] {e}")
                time.sleep(3)

    threading.Thread(target=poll_pc_resume, daemon=True).start()
    threading.Thread(target=poll_hardware, daemon=True).start()
    threading.Thread(target=poll_timers, daemon=True).start()
    threading.Thread(target=poll_clock, daemon=True).start()
    threading.Thread(target=poll_auto_pages, daemon=True).start()
    threading.Thread(target=poll_lms, daemon=True).start()
    if vu_on:
        threading.Thread(target=poll_vu, daemon=True).start()
    if _HAS_PYCAW:
        threading.Thread(target=poll_volume, daemon=True).start()
    else:
        print(f"pycaw/comtypes introuvable ({_PYCAW_IMPORT_ERR}) : le volume "
              "système réel est indisponible. Installe-le avec le MÊME "
              "interpréteur que celui qui lance le script :\n"
              "    python -m pip install pycaw\n"
              "Retour aux touches média.")

    device.open()
    print(f"AKP05E Interface v{APP_VERSION} — connecté. Ctrl+C pour quitter.")

    # bandeau tactile : zones Vol (temps réel), page courante (zone 2) et Lum
    device._page_label = (page_cfg().get("label") or current["name"])[:9]
    refresh_strip()

    # peint les icônes de la page courante
    paint_page()

    # v2.16.0 : le menu systray envoie ses actions dans une file ; la
    # boucle principale les exécute (rien ne touche le deck depuis le
    # thread du menu) et s'arrête proprement sur Quitter ou Ctrl+C.
    _ui_queue = queue.Queue()
    _quit = threading.Event()

    def _ui(fn):
        _ui_queue.put(fn)

    def _about():
        label = page_cfg().get("label") or current["name"]
        ok = "installé" if autostart_installed() else "non installé"
        user32.MessageBoxW(
            None, f"AKP05E Interface v{APP_VERSION}\n\n"
                  f"Page : {label}\nLuminosité : {device.brightness}%\n"
                  f"Autostart : {ok}\n\n"
                  f"Menu systray ou Ctrl+C pour quitter.",
            "AKP05E Interface", 0)

    def toggle_sleep():
        if getattr(device, "_sleeping", False):
            device._sleeping = False
            device.set_brightness(getattr(device, "_last_bright",
                                          DEFAULT_BRIGHTNESS))
            try:
                paint_page()
                refresh_strip()
            except Exception:
                pass
            print("[veille] deck réveillé")
        else:
            run_action({"type": "sleep"}, device)

    def _tray_state():
        if getattr(device, "_sleeping", False):
            st = "sleep"
        elif getattr(device, "dev", None) is None:
            st = "off"
        else:
            st = "on"
        label = page_cfg().get("label") or current["name"]
        tray.set_state(st, f"AKP05E v{APP_VERSION} — {label}")

    def _tray_items():
        asleep = getattr(device, "_sleeping", False)
        return [
            ("Réveiller le deck" if asleep else "Veille du deck",
             lambda: _ui(lambda: (toggle_sleep(), _tray_state()))),
            None,
            ("Luminosité +10",
             lambda: _ui(lambda: device.set_brightness(device.brightness + 10))),
            ("Luminosité -10",
             lambda: _ui(lambda: device.set_brightness(device.brightness - 10))),
            ("Luminosité par défaut (%d%%)" % DEFAULT_BRIGHTNESS,
             lambda: _ui(lambda: device.set_brightness(DEFAULT_BRIGHTNESS))),
            None,
            ("Page suivante", lambda: _ui(lambda: switch_page("next"))),
            ("Page précédente", lambda: _ui(lambda: switch_page("prev"))),
            None,
            ("À propos", lambda: _ui(_about)),
            ("Quitter", lambda: _quit.set()),
        ]

    tray = SystrayIcon(f"AKP05E v{APP_VERSION}", _tray_items,
                       on_double=lambda: _ui(_about))
    tray.start()

    # déconnexion/reconnexion : l'icône reflète l'état
    device.on_disconnect = lambda: (print("Deck débranché — relance "
                                          "l'application."), _tray_state())
    device.on_reconnect = lambda: (_repaint_all(), _tray_state())

    try:
        while not _quit.is_set():
            try:
                while True:
                    _ui_queue.get_nowait()()
            except queue.Empty:
                pass
            _quit.wait(0.25)
    except KeyboardInterrupt:
        pass
    finally:
        tray.stop()
        device.close()
        print("Au revoir.")
        # Anti-crash au shutdown : les threads démons (poll_lms, poll_volume…)
        # peuvent encore écrire sur stdout/stderr pendant la finalisation de
        # l'interpréteur -> « Fatal Python error: _enter_buffered_busy »
        # (CPython < 3.13). On détourne les flux vers /dev/null APRÈS le
        # dernier message utile : plus rien à verrouiller, plus de fatal error.
        try:
            import os as _os
            _devnull = open(_os.devnull, "w")
            sys.stdout = _devnull
            sys.stderr = _devnull
        except Exception:
            pass

if __name__ == "__main__":
    main()
