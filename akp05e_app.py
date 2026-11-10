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
import re
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
# lui-même et le milieu de l'image se corrompt (bandes brouillées).
STRIP_MAX_JPEG = 12000
STRIP_JPEG_QUALITIES = (80, 65, 50, 35)
DEFAULT_BRIGHTNESS = 30
APP_VERSION = "2.5.1"

# cache de la dernière image du bandeau SANS le VU-mètre : le fil poll_vu
# la recopie puis dessine la zone 3 par-dessus, sans tout recalculer
_strip_base = None
_strip_base_lock = threading.Lock()
_strip_last = None        # dernière image RÉELLEMENT affichée (avec le VU)
_strip_last_lock = threading.Lock()
_vu_active = False        # levé par main() quand le fil VU tourne

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
ICON_CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".icons_cache")
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

def show_strip(device, brightness, volume=None, muted=None, extras=("K2", "K3"),
               pages=None, page_icon=None, page_color=None):
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
        elif name == "Vol":
            fill = (129, 212, 250)
        else:
            fill = (255, 213, 79)
        fill_w = int((bar_x1 - bar_x0 - 4) * max(0, min(100, pct)) / 100)
        if fill_w > 0:
            d.rounded_rectangle([bar_x0 + 2, bar_y + 2, bar_x0 + 2 + fill_w,
                                 bar_y + 10], radius=4, fill=fill)

    # zone 1 : volume système (ou libellé libre si pycaw absent)
    if volume is not None:
        level_zone(100, "Vol", volume, muted, (129, 212, 250))
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
    if _vu_active and _strip_last is not None:
        with _strip_last_lock:
            img.paste(_strip_last.crop((400, 0, 600, h)), (400, 0))
    else:
        d.text((500, 34), extras[1], font=font,
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

    def _send(self, data):
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
            for i in range(0, len(jpeg), PACKET_SIZE):
                chunk = jpeg[i:i + PACKET_SIZE]
                packet = [0] * TOTAL_LEN
                packet[1:1 + len(chunk)] = list(chunk)
                self._send(packet)
                time.sleep(0.002)  # laisse le firmware du deck absorber
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
        (le milieu du bandeau se corrompt)."""
        import io
        jpeg = None
        for q in STRIP_JPEG_QUALITIES:
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=q, optimize=True)
            jpeg = buf.getvalue()
            if len(jpeg) <= max_size:
                break
        return jpeg

    def set_image(self, button: int, img: Image.Image):
        """Upload une image PIL sur la touche (1-10), 112x112, rotation 180°."""
        if button not in BUTTON_TO_WIRE_KEY:
            raise ValueError("button doit être entre 1 et 10")
        img = img.convert("RGB").resize(BUTTON_IMAGE_SIZE).rotate(180)
        self._upload_jpeg(BUTTON_TO_WIRE_KEY[button], self._pil_to_jpeg(img))

    def set_strip(self, img: Image.Image):
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
        if len(jpeg) > STRIP_MAX_JPEG:
            print(f"[bandeau] JPEG encore gros ({len(jpeg)} octets), "
                  "risque de corruption possible")
        self._upload_jpeg(STRIP_WIRE_KEY, jpeg)

    def set_label(self, button: int, text: str, bg=(15, 15, 15),
                  fg=(240, 240, 240), sub: str = None, small: bool = False):
        """Dessine une icône texte simple et l'envoie sur la touche.
        small=True : police réduite et nom coupé sur DEUX lignes pour
        afficher les noms longs (Squeezebox, radios) en entier."""
        img = Image.new("RGB", BUTTON_IMAGE_SIZE, bg)
        d = ImageDraw.Draw(img)
        try:
            if small:
                font_big = ImageFont.truetype("arial.ttf", 20)
                font_small = ImageFont.truetype("arial.ttf", 13)
            else:
                font_big = ImageFont.truetype("arial.ttf", 30)
                font_small = ImageFont.truetype("arial.ttf", 16)
        except OSError:
            font_big = font_small = ImageFont.load_default()
        y0 = 44 if not sub else 38
        if small and len(text) > 8 and " " in text:
            # coupe au plus près du milieu pour équilibrer les 2 lignes
            words = text.split(" ")
            best, best_d, acc = 0, 10 ** 9, 0
            for k in range(len(words) - 1):
                acc += len(words[k]) + 1
                dist = abs(acc - (len(text) + 1) / 2)
                if dist < best_d:
                    best_d, best = dist, acc
            l1, l2 = text[:best].strip(), text[best:].strip()
            d.text((56, y0 - 13), l1, font=font_big, fill=fg, anchor="mm")
            d.text((56, y0 + 13), l2, font=font_big, fill=fg, anchor="mm")
        else:
            if small:
                y0 = 44 if not sub else 38
            else:
                y0 = 56 if not sub else 40
            d.text((56, y0), text, font=font_big, fill=fg, anchor="mm")
        if sub:
            d.text((56, 84 if small else 78), sub, font=font_small,
                   fill=(160, 160, 160), anchor="mm")
        self.set_image(button, img)

# ---------------------------------------------------------------------------
# Actions Windows (SendInput via ctypes — pas de dépendance propriétaire)
# ---------------------------------------------------------------------------
import ctypes
from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)

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


def lms_viewed_active_fav(vp, favs, launched_id=None):
    """Index du favori actif pour le lecteur affiché : titre en cours si
    le flux le dit (lms_active_fav), sinon la dernière radio LANCÉE DEPUIS
    LE DECK (le current_title d'une webradio est souvent la métadonnée du
    morceau en cours, pas le nom de la station). -1 si aucun/lecteur éteint."""
    if not vp or not vp.get("playing"):
        return -1
    i = lms_active_fav(vp.get("title") or "", favs)
    if i >= 0:
        return i
    if launched_id:
        for j, f in enumerate(favs):
            if f.get("id") == launched_id:
                return j
    return -1


def short_player_name(name):
    """« Squeezebox Touch Orange » → « Orange » : les touches sont
    carrées, on retire les préfixes génériques des Squeezebox. Le préfixe
    « Radio » est conservé : David a un Touch « Orange » ET un Radio
    « Orange » (idem Vanille), il faut pouvoir les distinguer."""
    for pref in ("Squeezebox Touch ", "Squeezebox ", "Squeezelite ",
                 "Squeezelite-"):
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
    "4": {
      "icon": "timer",
      "color": "#FFCC80",
      "label": "Minut.",
      "action": {
        "type": "page",
        "page": "minuteurs"
      }
    },
    "5": {
      "icon": "refresh",
      "color": "#FFF59D",
      "label": "F5",
      "action": {
        "type": "keys",
        "keys": [
          "f5"
        ]
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

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "akp05e_config.json")

def load_config():
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
        print(f"Config par défaut créée : {CONFIG_PATH}")
        return DEFAULT_CONFIG
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------
def main():
    if "--list-sensors" in sys.argv:
        run_list_sensors()
        return
    config = load_config()
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
    pages["lms"] = {
        "label": "LMS", "icon": "speaker", "color": "#A5D6A7",
        "buttons": {str(i + 1): {"action": {"type": "lms_open_player",
                                            "index": i}} for i in range(6)},
        "encoders": _enc_pages(),
    }
    pages["lms_player"] = {
        "label": "Lecteur", "icon": "speaker", "color": "#81C784",
        "buttons": {
            "1": {"action": {"type": "lms_player_id"}},
            "2": {"action": {"type": "lms_player_power"}},
            "3": {"action": {"type": "lms_player_playpause"}},
            "4": {"label": "Favoris",
                  "action": {"type": "lms_open_favs"}},
            "5": {"label": "Applis",
                  "action": {"type": "lms_open_apps"}},
            "6": {"label": "Retour",
                  "action": {"type": "lms_back"}},
        },
        "encoders": {
            "encoder_1_cw": {"action": {"type": "lms_volume", "dir": "up",
                                        "step": 5}},
            "encoder_1_ccw": {"action": {"type": "lms_volume", "dir": "down",
                                        "step": 5}},
            "encoder_1_button": {"action": {"type": "lms_mute"}},
            **_enc_pages(),
        },
    }
    pages["lms_favs"] = {
        "label": "Favoris", "icon": "star", "color": "#FFF59D",
        "buttons": {
            **{str(i): {"action": {"type": "lms_fav_press", "slot": i - 1}}
               for i in range(1, 10)},
            "10": {"label": "Retour",
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
        "label": "Applis", "icon": "apps", "color": "#90CAF9",
        "buttons": {
            "1": {"icon": "library_music", "color": "#90CAF9",
                  "label": "Qobuz",
                  "action": {"type": "page", "page": "qobuz"}},
            "2": {"icon": "radio", "color": "#CE93D8",
                  "label": "Radio Par.",
                  "action": {"type": "lms_play_url",
                             "url": (_lms_cfg.get("radio_paradise_url")
                                     or "http://stream.radioparadise.com/"
                                        "aac-320")}},
            "10": {"icon": "undo", "color": "#EF9A9A", "label": "Retour",
                   "action": {"type": "lms_back_player"}},
        },
        "encoders": _enc_pages(),
    }
    LMS_PAGE_NAMES = ("lms", "lms_player", "lms_favs", "lms_apps")

    page_names = ["accueil"] + [n for n in pages if n != "accueil"]
    current = {"name": config.get("page", "accueil")}
    vu_cfg = config.get("vu_meter") or {}
    vu_on = _HAS_PYCAW and bool(vu_cfg.get("enabled", True))
    global _vu_active
    _vu_active = vu_on

    def page_cfg():
        if current["name"] == "accueil" or current["name"] not in pages:
            return config
        return pages.get(current["name"], {})

    def paint_page():
        """(Re)peint les 10 touches et le bandeau pour la page courante."""
        buttons = page_cfg().get("buttons") or {}
        for n in range(1, 11):
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
            run_action(action, device)
        elif zone == 2:
            switch_page("next")  # zone du carrousel sans action dédiée

    def handle(ev):
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
        if not ev.state:
            return  # ignore les relâchements (sauf besoin spécifique)
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

    def refresh_strip():
        """Redessine le bandeau : volume système + luminosité en direct,
        et nom de la page courante dans la zone 2."""
        vol, muted = None, None
        if current["name"] == "lms_player":
            vp = lms_viewed()
            if vp:
                with lms_lock:
                    vol = vp["volume"]
                    muted = lms_state["viewed_muted"]
        if vol is None and _HAS_PYCAW:
            try:
                vol, muted = get_volume_pct(), get_mute()
            except Exception:
                pass
        extras = (getattr(device, "_page_label", None) or "K2",
                  "VU" if vu_on else "K3")
        # carrousel : pages précédente / courante / suivante (zone 2)
        i = (page_names.index(current["name"])
             if current["name"] in page_names else 0)
        def _plabel(n):
            return (pages.get(n, {}).get("label")
                    or ("Accueil" if n == "accueil" else n))[:9]
        pages_tri = (
            _plabel(page_names[(i - 1) % len(page_names)]),
            _plabel(page_names[i]),
            _plabel(page_names[(i + 1) % len(page_names)]),
        )
        # icône + couleur d'accent de la page courante
        meta = (pages.get(current["name"])
                if current["name"] in pages else config)
        p_icon = meta.get("icon")
        p_color = parse_color(meta.get("color"), default=(129, 212, 250))
        try:
            show_strip(device, device.brightness, volume=vol, muted=muted,
                       extras=extras, pages=pages_tri,
                       page_icon=p_icon, page_color=p_color)
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
                                    paint_chrono_state(int(bn), e2)
                            break
            except Exception as e:
                print(f"[erreur minuteur] {e}")
            time.sleep(0.25)

    device.on_brightness = lambda pct: refresh_strip()
    device.on_strip_refresh = refresh_strip

    # --- LYRION MEDIA SERVER (LMS / Squeezebox) --------------------------
    lms = LMSClient((config.get("lms") or {}).get("host", ""),
                    (config.get("lms") or {}).get("port", 9000))
    lms_state = {"players": [],       # lecteurs découverts (poll)
                 "favorites": [],     # favoris radios LMS
                 "selected": 0,       # index du lecteur sélectionné
                 "viewed": None,      # id du lecteur affiché (page détail)
                 "fav_offset": 0,     # décalage de la page favoris
                 "viewed_muted": False,  # état muet du lecteur affiché
                 "favs_logged": False,   # découverte des favoris loggée ?
                 "loaded": False,     # première découverte faite ?
                 "launched_fav": {}}  # lecteur -> id favori lancé depuis le deck
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

    def paint_lms_button(n, entry):
        """Touche LMS : libellés dynamiques (lecteurs, favoris, états)
        rafraîchis par poll_lms."""
        t = (entry.get("action") or {}).get("type") or ""
        label = entry.get("label") or ""
        sub = ""
        bg, fg = (15, 15, 15), (240, 240, 240)
        with lms_lock:
            players = list(lms_state["players"])
            favs = list(lms_state["favorites"])
            fav_off = lms_state["fav_offset"]
            launched = dict(lms_state["launched_fav"])
        sel = lms_selected()
        vp = lms_viewed()
        if not lms.enabled:
            sub = "config off"
        elif not players and t not in ("lms_open_favs", "lms_open_apps",
                                       "lms_back", "lms_back_player",
                                       "lms_play_url"):
            sub = "LMS ?"
        elif t == "lms_open_player":
            i = int((entry.get("action") or {}).get("index", 0))
            if 0 <= i < len(players):
                p = players[i]
                label = short_player_name(p["name"])
                if p["power"]:
                    bg = (24, 68, 32)  # vert Lyrion si allumé
                    sub = (">> " + p["title"][:8]) if p["playing"] else "allumé"
                else:
                    sub = "veille"
            else:
                label, sub = "-", "(vide)"
        elif t == "lms_player_id":
            if vp:
                label = short_player_name(vp["name"])
                sub = "Lyrion"
                if vp["power"]:
                    bg = (30, 92, 40)  # fond vert Lyrion si allumé
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
                if (lms_viewed_active_fav(vp, favs, lid) == i):
                    bg = (22, 76, 200)  # bleu vif : cette radio est active
                    fg = (255, 255, 255)
                    sub = ">> en cours"
                else:
                    sub = "radio"
            else:
                label, sub = "-", "(vide)"
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
                if (lms_viewed_active_fav(sel, favs, lid) == i):
                    bg = (22, 76, 200)  # bleu vif : cette radio est active
                    fg = (255, 255, 255)
                    sub = ">> en cours"
                else:
                    sub = "radio"
            else:
                sub = "(vide)"
        if not label:
            label = "LMS"
        small = t in ("lms_open_player", "lms_player_id", "lms_fav_press",
                     "lms_favorite")
        # boutons de navigation/applis : on garde leur icône statique
        if (t in ("lms_open_favs", "lms_open_apps", "lms_back",
                  "lms_back_player", "lms_play_url")
                and entry.get("icon")):
            set_icon(device, n, entry["icon"],
                     fg=entry.get("color", "#e0e0e0"),
                     bg=entry.get("bg", "#101010"),
                     label=entry.get("label"))
            return
        device.set_label(n, label, bg=bg, fg=fg, sub=sub, small=small)

    def paint_lms_page():
        """Repeint toutes les touches LMS de la page courante."""
        buttons = page_cfg().get("buttons") or {}
        for bn, entry in buttons.items():
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
            lms.volume(tgt["id"], step if action.get("dir") == "up" else -step)
        elif t == "lms_mute" and tgt:
            lms.mute_toggle(tgt["id"])
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
            switch_page("lms_apps")
        elif t == "lms_play_url" and vp:
            lms.play_url(vp["id"], action.get("url") or "")
        elif t == "lms_back":
            switch_page("lms")
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

    threading.Thread(target=poll_hardware, daemon=True).start()
    threading.Thread(target=poll_timers, daemon=True).start()
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

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        device.close()
        print("Au revoir.")

if __name__ == "__main__":
    main()
