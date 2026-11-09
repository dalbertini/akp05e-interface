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
  {"type": "page", "page": "qobuz"}                         # changer de page
  {"type": "page", "page": "next"}                          # ou "prev" : défiler
(Par défaut, le knob 2 fait défiler les pages : CW = suivante, CCW = précédente.)
PAGES DE PROFILS : la config classique ("buttons"/"encoders") forme la page
"accueil". Des pages supplémentaires se définissent dans la clé "pages" :
  {"pages": {"qobuz": {"label": "Qobuz", "buttons": {...}, "encoders": {...}}}}
Chaque page a ses touches et encodeurs propres ; la zone 2 du bandeau affiche
le nom de la page courante. Bascule via l'action {"type": "page", ...}.
Une page supplémentaire est fournie par défaut : "qobuz" (play/stop/suiv./
prec./mute + retour accueil), pilotée par les touches média système (SMTC) —
fonctionne avec Qobuz, Spotify, VLC, etc.
Le knob 4 pilote la luminosité des écrans (rotation = réglage par pas,
appui = extinction/rallumage) et le knob 1 règle le VOLUME SYSTÈME Windows
(pycaw : niveau réel, appui = muet). Le bandeau tactile affiche les deux
en temps réel ("Vol 42%" et "Lum 60%" + barres), et se met à jour même si
le volume est changé depuis Windows (barre des tâches, clavier).
"""

import json
import os
import subprocess
import sys
import threading
import time
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
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
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
    """Cherche la mesure correspondant au motif (sous-chaîne, insensible à
    la casse, sur libellé + libellé d'origine + nom de capteur). En cas de
    correspondances multiples, privilégie le libellé le plus court."""
    if not readings:
        return None
    n = (needle or "").lower().strip()
    cands = [r for r in readings
             if n and n in (r["label"] + " " + r["label_orig"]
                            + " " + r["sensor"]).lower()]
    if not cands:
        return None
    cands.sort(key=lambda r: len(r["label"]))
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
DEFAULT_BRIGHTNESS = 60
APP_VERSION = "1.6.2"

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
    # zone 3 : libellé libre
    d.text((500, 34), extras[1], font=font,
           fill=(120, 120, 120), anchor="mm")
    # zone 4 : luminosité
    level_zone(700, "Lum", max(0, min(100, int(brightness))), False,
               (240, 220, 130))
    # séparateurs verticaux entre zones
    for i in (1, 2, 3):
        d.line([(i * 200, 10), (i * 200, h - 10)], fill=(45, 45, 45), width=2)
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
        JPEG compressé adaptativement pour rester sous la limite firmware."""
        img = img.convert("RGB").resize(STRIP_IMAGE_SIZE).rotate(180)
        jpeg = self._pil_to_jpeg_capped(img)
        if len(jpeg) > STRIP_MAX_JPEG:
            print(f"[bandeau] JPEG encore gros ({len(jpeg)} octets), "
                  "risque de corruption possible")
        self._upload_jpeg(STRIP_WIRE_KEY, jpeg)

    def set_label(self, button: int, text: str, bg=(15, 15, 15),
                  fg=(240, 240, 240), sub: str = None):
        """Dessine une icône texte simple et l'envoie sur la touche."""
        img = Image.new("RGB", BUTTON_IMAGE_SIZE, bg)
        d = ImageDraw.Draw(img)
        try:
            font_big = ImageFont.truetype("arial.ttf", 30)
            font_small = ImageFont.truetype("arial.ttf", 16)
        except OSError:
            font_big = font_small = ImageFont.load_default()
        d.text((56, 40 if sub else 56), text, font=font_big,
               fill=fg, anchor="mm")
        if sub:
            d.text((56, 78), sub, font=font_small, fill=(160, 160, 160),
                   anchor="mm")
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

# ---------------------------------------------------------------------------
# Moteur d'actions piloté par akp05e_config.json
# ---------------------------------------------------------------------------
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
    else:
        print(f"Type d'action inconnu : {t}")

DEFAULT_CONFIG = {
  "brightness": 60,
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
      "icon": "content_copy",
      "color": "#CE93D8",
      "label": "Copie",
      "action": {
        "type": "text",
        "text": "Bonjour !"
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
    },
    "9": {
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
  "pages": {
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
          "hw": "C:]",
          "label": "SSD C:",
          "icon": "save",
          "color": "#80DEEA"
        },
        "7": {
          "hw": "E:",
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
    page_names = ["accueil"] + [n for n in pages if n != "accueil"]
    current = {"name": config.get("page", "accueil")}

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
        if _HAS_PYCAW:
            try:
                vol, muted = get_volume_pct(), get_mute()
            except Exception:
                pass
        extras = (getattr(device, "_page_label", None) or "K2", "K3")
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

    device.on_brightness = lambda pct: refresh_strip()
    device.on_strip_refresh = refresh_strip

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
