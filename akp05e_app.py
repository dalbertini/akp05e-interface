#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AKP05E Deck — application de contrôle open source pour l'Ajazz AKP05E / AKP05
(VID 0x0300 / PID 0x3004) sous Windows.

Licence MIT. Aucun logiciel propriétaire requis : uniquement `pywinusb`
(HID natif Windows) et `Pillow` (génération des icônes JPEG).

    pip install pywinusb pillow

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
  {"type": "mediaplay"} {"type": "medianext"} {"type": "mediaprev"} {"type": "mediastop"}
  {"type": "brightness", "dir": "up"}                     # luminosité du deck
  {"type": "brightness_toggle"}                            # knob 4 : on/off
Le knob 4 pilote la luminosité des écrans (rotation = réglage par pas,
appui = extinction/rallumage) et le bandeau tactile affiche le niveau
en temps réel ("Lum 60%" + barre), avec une zone par encodeur.
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
DEFAULT_BRIGHTNESS = 60

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
def show_strip(device, brightness, volume_label="Vol", extras=("K2", "K3")):
    """Redessine le bandeau sous les 4 knobs : libellé de chaque encodeur,
    et pour le knob 4 une barre + % de luminosité en temps réel."""
    w, h = STRIP_IMAGE_SIZE
    img = Image.new("RGB", (w, h), (16, 16, 16))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 17)
        font_big = ImageFont.truetype("arial.ttf", 26)
    except OSError:
        font = font_big = ImageFont.load_default()
    # libellés des zones 1..3 (volume + 2 libres)
    labels = [volume_label, extras[0], extras[1]]
    for i, lab in enumerate(labels):
        x = i * 200
        d.text((x + 100, 34), lab, font=font, fill=(120, 120, 120), anchor="mm")
    # zone 4 : luminosité avec barre de niveau
    d.text((700, 28), "Lum", font=font, fill=(240, 220, 130), anchor="mm")
    pct = max(0, min(100, int(brightness)))
    d.text((700, 66), f"{pct}%", font=font_big, fill=(240, 240, 240), anchor="mm")
    bar_x0, bar_x1, bar_y = 610, 790, 92
    d.rounded_rectangle([bar_x0, bar_y, bar_x1, bar_y + 12], radius=6,
                        fill=(50, 50, 50))
    if pct > 0:
        fill_w = int((bar_x1 - bar_x0 - 4) * pct / 100)
        d.rounded_rectangle([bar_x0 + 2, bar_y + 2, bar_x0 + 2 + fill_w,
                            bar_y + 10], radius=4, fill=(255, 213, 79))
    # séparateurs verticaux entre zones
    for i in (1, 2, 3):
        d.line([(i * 200, 10), (i * 200, h - 10)], fill=(45, 45, 45), width=2)
    device.set_strip(img)

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
        else:
            return
        if self.on_event:
            try:
                self.on_event(ev)
            except Exception as e:
                print(f"[erreur handler] {e}")

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
        """Envoi d'une image JPEG sur un wire-key (BAT + chunks + STP)."""
        header = crt_command("BAT", [0, 0, (len(jpeg) >> 8) & 0xFF,
                                    len(jpeg) & 0xFF, wire_key])
        with self.lock:
            self._send(header)
            for i in range(0, len(jpeg), PACKET_SIZE):
                chunk = jpeg[i:i + PACKET_SIZE]
                packet = [0] * TOTAL_LEN
                packet[1:1 + len(chunk)] = list(chunk)
                self._send(packet)
            self._send(crt_command("STP"))

    @staticmethod
    def _pil_to_jpeg(img):
        import io
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        return buf.getvalue()

    def set_image(self, button: int, img: Image.Image):
        """Upload une image PIL sur la touche (1-10), 112x112, rotation 180°."""
        if button not in BUTTON_TO_WIRE_KEY:
            raise ValueError("button doit être entre 1 et 10")
        img = img.convert("RGB").resize(BUTTON_IMAGE_SIZE).rotate(180)
        self._upload_jpeg(BUTTON_TO_WIRE_KEY[button], self._pil_to_jpeg(img))

    def set_strip(self, img: Image.Image):
        """Upload une image PIL sur le bandeau tactile (800x112, wire-key 1)."""
        img = img.convert("RGB").resize(STRIP_IMAGE_SIZE).rotate(180)
        self._upload_jpeg(STRIP_WIRE_KEY, self._pil_to_jpeg(img))

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
MEDIA = {"volume_up": 0xED, "volume_down": 0xEE, "volume_mute": 0xE2,
         "play_pause": 0xE8, "stop": 0xE9, "next": 0xEA, "prev": 0xEB}
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
    elif scan:  # touche média : scan code + KEYEVENTF_EXTENDEDKEY
        _key_event(0, scan, 0x0001); _key_event(0, scan, 0x0001 | KEYEVENTF_KEYUP)
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
    "brightness": DEFAULT_BRIGHTNESS,
    "buttons": {
        "1": {"icon": "terminal", "color": "#80CBC4", "label": "CMD",
              "action": {"type": "run", "cmd": "cmd"}},
        "2": {"icon": "description", "color": "#9FA8DA", "label": "Notepad",
              "action": {"type": "open", "path": "notepad.exe"}},
        "3": {"icon": "public", "color": "#90CAF9", "label": "Web",
              "action": {"type": "url", "url": "https://github.com"}},
        "4": {"icon": "content_copy", "color": "#CE93D8", "label": "Copie",
              "action": {"type": "text", "text": "Bonjour !"}},
        "5": {"icon": "refresh", "color": "#FFF59D", "label": "F5",
              "action": {"type": "keys", "keys": ["f5"]}},
        "6": {"icon": "play_arrow", "color": "#A5D6A7", "bg": "#1b2e1b", "label": "Play",
              "action": {"type": "mediaplay"}},
        "7": {"icon": "skip_next", "color": "#A5D6A7", "bg": "#1b2e1b", "label": "Suiv.",
              "action": {"type": "medianext"}},
        "8": {"icon": "skip_previous", "color": "#A5D6A7", "bg": "#1b2e1b", "label": "Prec.",
              "action": {"type": "mediaprev"}},
        "9": {"icon": "volume_off", "color": "#EF9A9A", "bg": "#331b1b", "label": "Mute",
              "action": {"type": "volume", "dir": "mute"}},
        "10": {"icon": "stop", "color": "#EF9A9A", "bg": "#331b1b", "label": "Stop",
              "action": {"type": "mediastop"}}
    },
    "encoders": {
        "encoder_1_cw":   {"action": {"type": "volume", "dir": "up"}},
        "encoder_1_ccw":  {"action": {"type": "volume", "dir": "down"}},
        "encoder_1_button": {"action": {"type": "volume", "dir": "mute"}},
        "encoder_4_cw":   {"action": {"type": "brightness", "dir": "up", "step": 10}},
        "encoder_4_ccw":  {"action": {"type": "brightness", "dir": "down", "step": 10}},
        "encoder_4_button": {"action": {"type": "brightness_toggle"}}
    }
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
    config = load_config()
    device = Akp05Device(brightness=config.get("brightness", DEFAULT_BRIGHTNESS))

    def handle(ev):
        if not ev.state:
            return  # ignore les relâchements (sauf besoin spécifique)
        action = None
        if ev.name.startswith("button_"):
            entry = config.get("buttons", {}).get(ev.name.split("_")[1])
            action = entry and entry.get("action")
        else:
            action = config.get("encoders", {}).get(ev.name, {}).get("action")
        if action:
            print(f"[action] {ev.name} -> {action.get('type')}")
            threading.Thread(target=run_action, args=(action, device),
                             daemon=True).start()

    device.on_event = handle
    device.on_disconnect = lambda: print("Deck débranché — relance l'application.")
    device.on_brightness = lambda pct: show_strip(device, pct)

    device.open()
    print("AKP05E connecté. Ctrl+C pour quitter.")

    # bandeau tactile : affiche les zones des 4 knobs (luminosité en direct)
    show_strip(device, device.brightness)

    # peint les icônes configurées
    for n, entry in (config.get("buttons") or {}).items():
        try:
            n = int(n)
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
            elif "label" in entry:
                device.set_label(n, entry["label"], sub=entry.get("sub"))
        except Exception as e:
            print(f"Icône touche {n} ignorée : {e}")

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
