"""
╔══════════════════════════════════════════════════════════════════╗
║   NOTRUF HAMBURG RP – Polizei Terminal v5.0                      ║
║   Vollständiger Bot – Eine Datei                                 ║
║   Autor: grinsevogel                                              ║
║   GitHub: github.com/grinsevogel/notruf-hamburg-bot                ║
╚══════════════════════════════════════════════════════════════════╝

EINRICHTUNG:
  1. pip install discord.py python-dotenv
  2. .env Datei erstellen (siehe README / Anleitung unten)
  3. python bot.py

.env Datei Inhalt:
  TOKEN=dein_token_hier
  LOG_CHANNEL_ID=123456789
  POLIZEI_ROLLE_ID=123456789

"""

# ══════════════════════════════════════════════════════════════════
#  IMPORTS
# ══════════════════════════════════════════════════════════════════
import discord
from discord.ext import commands
import sqlite3
import math
import os
import time
from datetime import datetime

# .env laden – pip install python-dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ .env Datei geladen")
except ImportError:
    print("⚠️  python-dotenv nicht installiert – nutze Umgebungsvariablen direkt")

# ══════════════════════════════════════════════════════════════════
#  KONFIGURATION
#  Werte kommen aus der .env Datei – NIEMALS Token in den Code!
# ══════════════════════════════════════════════════════════════════
TOKEN            = os.getenv("TOKEN",            "KEIN_TOKEN_GESETZT")
LOG_CHANNEL_ID   = int(os.getenv("LOG_CHANNEL_ID",   "0"))
POLIZEI_ROLLE_ID = int(os.getenv("POLIZEI_ROLLE_ID",  "0"))

STRAFEN_PRO_SEITE = 8
BOT_START_TIME    = time.time()

# ══════════════════════════════════════════════════════════════════
#  FARBEN & DESIGN-KONSTANTEN
# ══════════════════════════════════════════════════════════════════
C_BLAU    = 0x1a237e   # Polizeiblau
C_GRUEN   = 0x2e7d32   # Erfolg / Unbescholten
C_ROT     = 0xb71c1c   # Gefahr / Vorbestraft
C_ORANGE  = 0xe65100   # Warnung / Strafe
C_GRAU    = 0x424242   # Neutral
C_CYAN    = 0x006064   # Info
C_GOLD    = 0xf57f17   # Highlight

BANNER = (
    "```ansi\n"
    "\u001b[1;34m┌──────────────────────────────────────────┐\n"
    "│   \u001b[1;37mHAMBURGER POLIZEI  ·  DIGITALES SYSTEM\u001b[1;34m   │\n"
    "│   \u001b[1;32mSTATUS: ONLINE  ████████████████  100%\u001b[1;34m   │\n"
    "│   \u001b[1;33mZUGRIFF: NUR AUTORISIERTES PERSONAL\u001b[1;34m      │\n"
    "└──────────────────────────────────────────┘\u001b[0m\n"
    "```"
)

# ══════════════════════════════════════════════════════════════════
#  STRAFENKATALOG (125 Einträge)
#  Format: (Kategorie, Name, Betrag_€, Zusatz)
# ══════════════════════════════════════════════════════════════════
STANDARD_STRAFEN = [

    # ── 🚗 VERKEHR: Geschwindigkeit ─────────────────────────
    ("🚗 Verkehr", "Geschwindigkeitsüberschreitung bis 10 km/h innerorts",          30,   ""),
    ("🚗 Verkehr", "Geschwindigkeitsüberschreitung 11–15 km/h innerorts",           50,   "1 Punkt"),
    ("🚗 Verkehr", "Geschwindigkeitsüberschreitung 16–20 km/h innerorts",           70,   "1 Punkt"),
    ("🚗 Verkehr", "Geschwindigkeitsüberschreitung 21–25 km/h innerorts",          115,   "1 Punkt"),
    ("🚗 Verkehr", "Geschwindigkeitsüberschreitung 26–30 km/h innerorts",          180,   "1 Punkt, 1 Monat Fahrverbot"),
    ("🚗 Verkehr", "Geschwindigkeitsüberschreitung 31–40 km/h innerorts",          260,   "2 Punkte, 1 Monat Fahrverbot"),
    ("🚗 Verkehr", "Geschwindigkeitsüberschreitung 41–50 km/h innerorts",          400,   "2 Punkte, 1 Monat Fahrverbot"),
    ("🚗 Verkehr", "Geschwindigkeitsüberschreitung über 50 km/h innerorts",        600,   "2 Punkte, 2 Monate Fahrverbot"),
    ("🚗 Verkehr", "Geschwindigkeitsüberschreitung bis 10 km/h außerorts",          20,   ""),
    ("🚗 Verkehr", "Geschwindigkeitsüberschreitung 11–20 km/h außerorts",           40,   "1 Punkt"),
    ("🚗 Verkehr", "Geschwindigkeitsüberschreitung 21–30 km/h außerorts",           80,   "1 Punkt"),
    ("🚗 Verkehr", "Geschwindigkeitsüberschreitung 31–40 km/h außerorts",          120,   "1 Punkt"),
    ("🚗 Verkehr", "Geschwindigkeitsüberschreitung 41–50 km/h außerorts",          200,   "2 Punkte, 1 Monat Fahrverbot"),
    ("🚗 Verkehr", "Geschwindigkeitsüberschreitung über 50 km/h außerorts",        440,   "2 Punkte, 2 Monate Fahrverbot"),
    ("🚗 Verkehr", "Rasen auf der Autobahn (über 150 km/h zu schnell)",            800,   "2 Punkte, 3 Monate Fahrverbot"),

    # ── 🚗 VERKEHR: Alkohol & Drogen ─────────────────────────
    ("🚗 Verkehr", "Fahren mit 0,5–0,79 Promille (§ 24a StVG)",                   500,   "1 Punkt, 1 Monat Fahrverbot"),
    ("🚗 Verkehr", "Fahren mit 0,8–1,59 Promille (§ 316 StGB)",                  1500,   "3 Punkte, 6 Monate Fahrverbot"),
    ("🚗 Verkehr", "Fahren mit über 1,6 Promille – absolute Fahruntüchtigkeit",   3000,   "3 Punkte, MPU, Führerscheinentzug"),
    ("🚗 Verkehr", "Fahren unter Drogeneinfluss",                                 1500,   "3 Punkte, Führerscheinentzug möglich"),
    ("🚗 Verkehr", "Fahren ohne Führerschein (§ 21 StVG)",                        1000,   "3 Punkte, Strafanzeige"),
    ("🚗 Verkehr", "Fahren mit abgelaufenem Führerschein",                         500,   "1 Punkt"),

    # ── 🚗 VERKEHR: Vorfahrt & Ampeln ─────────────────────────
    ("🚗 Verkehr", "Missachten der Vorfahrt",                                      200,   "1 Punkt"),
    ("🚗 Verkehr", "Rotlichtverstoß – Ampel unter 1 Sekunde rot",                 200,   "1 Punkt"),
    ("🚗 Verkehr", "Qualifizierter Rotlichtverstoß – über 1 Sekunde rot",         320,   "2 Punkte, 1 Monat Fahrverbot"),
    ("🚗 Verkehr", "Stoppschild nicht beachtet",                                  100,   "1 Punkt"),
    ("🚗 Verkehr", "Vorfahrt an Kreuzung missachtet",                             150,   "1 Punkt"),
    ("🚗 Verkehr", "Einbiegen ohne Beachten des Gegenverkehrs",                   200,   "1 Punkt"),

    # ── 🚗 VERKEHR: Parken & Halten ───────────────────────────
    ("🚗 Verkehr", "Parken im Halteverbot",                                        25,   ""),
    ("🚗 Verkehr", "Parken auf Behindertenstellplatz ohne Ausweis",               200,   ""),
    ("🚗 Verkehr", "Parken auf Gehweg oder Radweg",                                55,   ""),
    ("🚗 Verkehr", "Halten in zweiter Reihe – Verkehrsbehinderung",                55,   ""),
    ("🚗 Verkehr", "Parken vor Ausfahrt oder Einfahrt",                            55,   ""),
    ("🚗 Verkehr", "Parken an Kreuzung – unter 5 m Abstand",                       35,   ""),
    ("🚗 Verkehr", "Parken auf Rettungsweg oder Feuerwehrzufahrt",               1000,   "Sofortabschleppen"),
    ("🚗 Verkehr", "Parken vor Hydrant",                                          200,   ""),
    ("🚗 Verkehr", "Halteverbot vor Schule oder Kindergarten",                    100,   ""),

    # ── 🚗 VERKEHR: Sicherheit & Pflichten ────────────────────
    ("🚗 Verkehr", "Fahren ohne Sicherheitsgurt – Fahrer",                         30,   ""),
    ("🚗 Verkehr", "Fahren ohne Sicherheitsgurt – Beifahrer, Verantwortung Fahrer",30,   ""),
    ("🚗 Verkehr", "Kind ohne Kindersitz befördert",                              100,   ""),
    ("🚗 Verkehr", "Handy am Steuer (§ 23 Abs. 1a StVO)",                        200,   "1 Punkt"),
    ("🚗 Verkehr", "Ablenkung durch Bildschirm oder Navigation am Steuer",        200,   "1 Punkt"),
    ("🚗 Verkehr", "Fahrzeug nicht fahrtauglich – defekte Bremsen, Licht etc.",   150,   "Fahrzeug stillgelegt"),
    ("🚗 Verkehr", "Hauptuntersuchung (TÜV) überfällig über 2 Monate",            60,   ""),
    ("🚗 Verkehr", "Kein Warndreieck oder Warnweste im Fahrzeug",                  15,   ""),
    ("🚗 Verkehr", "Fahren ohne Kfz-Haftpflichtversicherung",                   1000,   "Fahrzeugstilllegung"),
    ("🚗 Verkehr", "Fahrzeug ohne gültige Zulassung",                             500,   "Fahrzeugstilllegung"),
    ("🚗 Verkehr", "Überladen des Fahrzeugs",                                     200,   ""),
    ("🚗 Verkehr", "Ungesicherte Ladung",                                         150,   "1 Punkt"),
    ("🚗 Verkehr", "Fahrerflucht nach Unfall (§ 142 StGB)",                      3000,   "3 Punkte, Führerscheinentzug, Anzeige"),
    ("🚗 Verkehr", "Nötigung im Straßenverkehr (§ 240 StGB)",                    1000,   "2 Punkte"),
    ("🚗 Verkehr", "Unerlaubtes Wenden auf der Autobahn",                         200,   "1 Punkt"),
    ("🚗 Verkehr", "Falsches Überholen oder Überholen mit Gefährdung",            300,   "2 Punkte"),
    ("🚗 Verkehr", "Reißverschlussverfahren nicht beachtet",                       80,   ""),
    ("🚗 Verkehr", "Missachten von Bahnübergangssignalen",                        700,   "3 Punkte"),
    ("🚗 Verkehr", "Benutzung Standspur ohne Berechtigung",                       200,   "1 Punkt"),
    ("🚗 Verkehr", "Rückwärtsfahren auf Autobahn oder Seitenstreifen als Fahrspur",200,  "1 Punkt"),
    ("🚗 Verkehr", "Einsatzfahrzeug nicht Platz gemacht (§ 38 StVO)",             240,   "1 Punkt"),
    ("🚗 Verkehr", "Rettungsgasse nicht gebildet (§ 11 Abs. 2 StVO)",            320,   "2 Punkte, 1 Monat Fahrverbot"),
    ("🚗 Verkehr", "Gaffen an Unfallstelle",                                      200,   ""),
    ("🚗 Verkehr", "Unerlaubtes Überholen bei Gegenverkehr",                      150,   "1 Punkt"),
    ("🚗 Verkehr", "Zu geringer Sicherheitsabstand auf Autobahn",                 160,   "1 Punkt"),

    # ── 📋 ORDNUNGSWIDRIGKEITEN ────────────────────────────────
    ("📋 Ordnung",  "Ruhestörung (§ 117 OWiG) – tagsüber",                       100,   ""),
    ("📋 Ordnung",  "Ruhestörung (§ 117 OWiG) – nächtlich",                      250,   ""),
    ("📋 Ordnung",  "Lärmerregung durch Kraftfahrzeug – Tuning, laute Auspüffe",  350,   ""),
    ("📋 Ordnung",  "Unangemessenes Verhalten gegenüber Beamten",                 500,   ""),
    ("📋 Ordnung",  "Vermüllung öffentlicher Plätze oder Wegwerfen von Müll",     100,   ""),
    ("📋 Ordnung",  "Betreten einer gesperrten Grünanlage",                        50,   ""),
    ("📋 Ordnung",  "Lagern oder Campen auf öff. Flächen ohne Genehmigung",       250,   ""),
    ("📋 Ordnung",  "Alkohol trinken in der Öffentlichkeit – Verbotszone",        100,   ""),
    ("📋 Ordnung",  "Alkohol in öffentlichen Verkehrsmitteln",                     40,   ""),
    ("📋 Ordnung",  "Verstoß gegen die Leinenpflicht – Hund",                     100,   ""),
    ("📋 Ordnung",  "Hund verunreinigt öffentliche Wege – nicht entfernt",         50,   ""),
    ("📋 Ordnung",  "Graffiti oder Sachbeschädigung kleines Ausmaß",              500,   "Anzeige"),
    ("📋 Ordnung",  "Rauchen in Nichtraucherbereichen",                            50,   ""),
    ("📋 Ordnung",  "Feuerwerk außerhalb erlaubter Zeiten",                       500,   ""),
    ("📋 Ordnung",  "Wildplakatieren oder unerlaubte Werbung",                    200,   ""),
    ("📋 Ordnung",  "Unbefugtes Betreten privaten Grundstücks",                   250,   ""),
    ("📋 Ordnung",  "Verstoß gegen Benutzungsordnung – Park, Bad etc.",           100,   ""),
    ("📋 Ordnung",  "Falsche Identitätsangabe gegenüber Beamten",                 500,   "Strafanzeige möglich"),
    ("📋 Ordnung",  "Nichtmitführen des Personalausweises bei Pflicht",            50,   ""),
    ("📋 Ordnung",  "Behinderung einer Polizeikontrolle",                         500,   ""),
    ("📋 Ordnung",  "Verstoß gegen Ausgangssperre oder Sperrzeit",                250,   ""),

    # ── ⚖️ STRAFTATEN ──────────────────────────────────────────
    ("⚖️ Straftat", "Körperverletzung (§ 223 StGB) – leicht",                   1500,   "Anzeige, bis 3 Jahre Haft"),
    ("⚖️ Straftat", "Körperverletzung (§ 224 StGB) – gefährlich",               3000,   "Anzeige, bis 10 Jahre Haft"),
    ("⚖️ Straftat", "Schwere Körperverletzung (§ 226 StGB)",                    5000,   "Anzeige, bis 15 Jahre Haft"),
    ("⚖️ Straftat", "Bedrohung (§ 241 StGB)",                                    750,   "Anzeige"),
    ("⚖️ Straftat", "Beleidigung (§ 185 StGB)",                                  500,   "Anzeige"),
    ("⚖️ Straftat", "Üble Nachrede (§ 186 StGB)",                                750,   "Anzeige"),
    ("⚖️ Straftat", "Diebstahl (§ 242 StGB) – einfach",                         2000,   "Anzeige, bis 5 Jahre Haft"),
    ("⚖️ Straftat", "Schwerer Diebstahl (§ 243 StGB)",                          4000,   "Anzeige, bis 10 Jahre Haft"),
    ("⚖️ Straftat", "Raub (§ 249 StGB)",                                        5000,   "Anzeige, mind. 1 Jahr Haft"),
    ("⚖️ Straftat", "Schwerer Raub (§ 250 StGB)",                               8000,   "Anzeige, mind. 3 Jahre Haft"),
    ("⚖️ Straftat", "Erpressung (§ 253 StGB)",                                  5000,   "Anzeige, bis 5 Jahre Haft"),
    ("⚖️ Straftat", "Betrug (§ 263 StGB)",                                      3000,   "Anzeige, bis 5 Jahre Haft"),
    ("⚖️ Straftat", "Sachbeschädigung (§ 303 StGB)",                            1000,   "Anzeige, Schadensersatz"),
    ("⚖️ Straftat", "Hausfriedensbruch (§ 123 StGB)",                            750,   "Anzeige"),
    ("⚖️ Straftat", "Widerstand gegen Vollstreckungsbeamte (§ 113 StGB)",       2000,   "Anzeige, bis 3 Jahre Haft"),
    ("⚖️ Straftat", "Angriff auf Vollstreckungsbeamte (§ 114 StGB)",            3000,   "Anzeige, bis 5 Jahre Haft"),
    ("⚖️ Straftat", "Gefangenenbefreiung (§ 120 StGB)",                         3000,   "Anzeige"),
    ("⚖️ Straftat", "Hehlerei (§ 259 StGB)",                                    2000,   "Anzeige"),
    ("⚖️ Straftat", "Unerlaubter Waffenbesitz (§ 51 WaffG)",                    5000,   "Waffe beschlagnahmt, Anzeige"),
    ("⚖️ Straftat", "Führen einer verbotenen Waffe in der Öffentlichkeit",      2000,   "Waffe beschlagnahmt, Anzeige"),
    ("⚖️ Straftat", "Drogenbesitz (§ 29 BtMG) – geringe Menge",                1000,   "Anzeige, Drogen beschlagnahmt"),
    ("⚖️ Straftat", "Drogenbesitz (§ 29 BtMG) – größere Menge",                5000,   "Anzeige, Strafverfolgung"),
    ("⚖️ Straftat", "Drogenhandel (§ 29a BtMG)",                              10000,   "Anzeige, Freiheitsstrafe"),
    ("⚖️ Straftat", "Brandstiftung (§ 306 StGB)",                               8000,   "Anzeige, bis 10 Jahre Haft"),
    ("⚖️ Straftat", "Schwere Brandstiftung (§ 306a StGB)",                     15000,   "Anzeige, Freiheitsstrafe"),
    ("⚖️ Straftat", "Gefährliche Eingriffe in den Straßenverkehr (§ 315b StGB)",5000,   "Anzeige"),
    ("⚖️ Straftat", "Urkundenfälschung (§ 267 StGB)",                           3000,   "Anzeige"),
    ("⚖️ Straftat", "Geldwäsche (§ 261 StGB)",                                  8000,   "Anzeige"),
    ("⚖️ Straftat", "Amtsanmaßung (§ 132 StGB)",                               2000,   "Anzeige"),
    ("⚖️ Straftat", "Erpressung mit Waffe (§ 255 StGB)",                       10000,   "Anzeige, Freiheitsstrafe"),
    ("⚖️ Straftat", "Stalking (§ 238 StGB)",                                    2500,   "Anzeige"),
    ("⚖️ Straftat", "Nötigung (§ 240 StGB)",                                    1500,   "Anzeige"),
    ("⚖️ Straftat", "Freiheitsberaubung (§ 239 StGB)",                          4000,   "Anzeige, bis 10 Jahre Haft"),

    # ── 🚔 EINSATZ / POLIZEI ──────────────────────────────────
    ("🚔 Einsatz",  "Behinderung eines Rettungseinsatzes",                        750,   "Anzeige möglich"),
    ("🚔 Einsatz",  "Missbrauch des Notruf 110 oder 112",                         350,   "Strafanzeige"),
    ("🚔 Einsatz",  "Falsche Verdächtigung (§ 164 StGB)",                        1500,   "Anzeige"),
    ("🚔 Einsatz",  "Falsche Unfallanzeige oder Vortäuschung einer Straftat",    2000,   "Anzeige"),
    ("🚔 Einsatz",  "Nicht Folgen einer polizeilichen Anweisung",                 500,   ""),
    ("🚔 Einsatz",  "Aufenthalt in Sperrzone – Absperrung missachtet",            250,   ""),
    ("🚔 Einsatz",  "Behinderung durch Fotografieren von Polizeimaßnahmen",       200,   ""),
    ("🚔 Einsatz",  "Nicht anhalten bei polizeilichem Haltezeichen",             1000,   "2 Punkte, Anzeige"),
    ("🚔 Einsatz",  "Flucht vor der Polizei zu Fuß",                              500,   "Anzeige"),
    ("🚔 Einsatz",  "Flucht vor der Polizei mit Fahrzeug",                       3000,   "2 Punkte, Führerscheinentzug, Anzeige"),

    # ── 🔫 WAFFEN ─────────────────────────────────────────────
    ("🔫 Waffen",   "Mitführen eines Messers – Klingenlänge über 12 cm",          500,   "Messer beschlagnahmt"),
    ("🔫 Waffen",   "Mitführen von Schlagringen, Nunchaku oder ähnlichem",       1000,   "Waffe beschlagnahmt, Anzeige"),
    ("🔫 Waffen",   "Unerlaubtes Führen einer Schusswaffe",                      5000,   "Waffe beschlagnahmt, Anzeige"),
    ("🔫 Waffen",   "Unerlaubtes Führen einer halbautomatischen Waffe",          8000,   "Waffe beschlagnahmt, Anzeige"),
    ("🔫 Waffen",   "Schießen in der Öffentlichkeit ohne Erlaubnis",            10000,   "Anzeige, Verhaftung"),
    ("🔫 Waffen",   "Bedrohung mit Schusswaffe",                                 5000,   "Anzeige, Verhaftung"),
    ("🔫 Waffen",   "Unerlaubter Erwerb von Waffen oder Munition",               6000,   "Anzeige"),
]

# ══════════════════════════════════════════════════════════════════
#  DATENBANK
# ══════════════════════════════════════════════════════════════════
class Database:
    def __init__(self):
        self.conn = sqlite3.connect("polizei.db", check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._tables()
        self._seed()

    def _tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS personen (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                name           TEXT NOT NULL UNIQUE,
                geburtsdatum   TEXT DEFAULT '',
                adresse        TEXT DEFAULT '',
                beruf          TEXT DEFAULT '',
                status         TEXT DEFAULT 'Unbescholten',
                fahndung       INTEGER DEFAULT 0,
                fahndung_grund TEXT DEFAULT '',
                notizen        TEXT DEFAULT '',
                erstellt_am    TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS fahrzeuge (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                kennzeichen    TEXT NOT NULL UNIQUE,
                besitzer       TEXT DEFAULT '',
                marke          TEXT DEFAULT '',
                farbe          TEXT DEFAULT '',
                status         TEXT DEFAULT 'Unauffällig',
                fahndung       INTEGER DEFAULT 0,
                fahndung_grund TEXT DEFAULT '',
                notizen        TEXT DEFAULT '',
                erstellt_am    TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS vergebene_strafen (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                person_name    TEXT NOT NULL,
                katalog_id     INTEGER DEFAULT NULL,
                grund          TEXT NOT NULL,
                betrag         INTEGER NOT NULL,
                zusatz         TEXT DEFAULT '',
                beamter        TEXT NOT NULL,
                datum          TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS strafenkatalog (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                kategorie      TEXT NOT NULL,
                name           TEXT NOT NULL,
                betrag         INTEGER NOT NULL,
                zusatz         TEXT DEFAULT '',
                aktiv          INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS dienst (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_id     TEXT NOT NULL UNIQUE,
                name           TEXT NOT NULL,
                beginn         
            );
            """)

import os

TOKEN = os.getenv("TOKEN")
bot.run(TOKEN)