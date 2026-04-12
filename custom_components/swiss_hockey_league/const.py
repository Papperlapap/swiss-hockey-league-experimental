"""Constants for the Swiss Hockey League integration."""
from __future__ import annotations

DOMAIN = "swiss_hockey_league"
CONF_TEAMS = "teams"
CONF_SCAN_INTERVAL_LIVE = "scan_interval_live"
CONF_SCAN_INTERVAL_IDLE = "scan_interval_idle"

DEFAULT_SCAN_INTERVAL_LIVE = 30  # seconds during live games
DEFAULT_SCAN_INTERVAL_IDLE = 300  # seconds when no live games

API_URL = "https://www.nationalleague.ch/api/games?lang=de-CH"

EVENT_GOAL = f"{DOMAIN}_goal"
EVENT_GAME_START = f"{DOMAIN}_game_start"
EVENT_GAME_END = f"{DOMAIN}_game_end"
EVENT_PERIOD_START = f"{DOMAIN}_period_start"
EVENT_PERIOD_END = f"{DOMAIN}_period_end"

# All National League teams
TEAMS: dict[str, dict[str, str]] = {
    "101152": {"name": "HC Ambri-Piotta", "short": "HCAP", "city": "Ambri"},
    "101151": {"name": "HC Davos", "short": "HCD", "city": "Davos"},
    "103138": {"name": "Fribourg-Gottéron", "short": "FRI", "city": "Fribourg"},
    "103140": {"name": "Genève-Servette HC", "short": "GSHC", "city": "Genève"},
    "101060": {"name": "SC Rapperswil-Jona Lakers", "short": "SCRJ", "city": "Rapperswil"},
    "101139": {"name": "ZSC Lions", "short": "ZSC", "city": "Zürich"},
    "101144": {"name": "EV Zug", "short": "EVZ", "city": "Zug"},
    "102128": {"name": "EHC Biel-Bienne", "short": "EHCB", "city": "Biel"},
    "101150": {"name": "HC Lugano", "short": "HCL", "city": "Lugano"},
    "103141": {"name": "Lausanne HC", "short": "LHC", "city": "Lausanne"},
    "102127": {"name": "SCL Tigers", "short": "SCL", "city": "Langnau"},
    "102126": {"name": "SC Bern", "short": "SCB", "city": "Bern"},
    "101149": {"name": "EHC Kloten", "short": "EHCK", "city": "Kloten"},
    "103144": {"name": "HC Ajoie", "short": "HCA", "city": "Porrentruy"},
}

# Team colors for the frontend card
TEAM_COLORS: dict[str, dict[str, str]] = {
    "101152": {"primary": "#003DA5", "secondary": "#FFD100"},  # Ambri
    "101151": {"primary": "#003DA5", "secondary": "#FFD700"},  # Davos
    "103138": {"primary": "#CE1126", "secondary": "#000000"},  # Fribourg
    "103140": {"primary": "#6F263D", "secondary": "#FFB81C"},  # Genève
    "101060": {"primary": "#003DA5", "secondary": "#C8C9C7"},  # Rapperswil
    "101139": {"primary": "#003DA5", "secondary": "#FFFFFF"},  # ZSC
    "101144": {"primary": "#003DA5", "secondary": "#FFFFFF"},  # Zug
    "102128": {"primary": "#CE1126", "secondary": "#000000"},  # Biel
    "101150": {"primary": "#000000", "secondary": "#FFFFFF"},  # Lugano
    "103141": {"primary": "#003DA5", "secondary": "#FFFFFF"},  # Lausanne
    "102127": {"primary": "#F7A600", "secondary": "#000000"},  # SCL Tigers
    "102126": {"primary": "#FFD700", "secondary": "#000000"},  # Bern
    "101149": {"primary": "#003DA5", "secondary": "#FF0000"},  # Kloten
    "103144": {"primary": "#FFD100", "secondary": "#000000"},  # Ajoie
}

# Game statuses from the API
STATUS_FINISHED = "finished"
STATUS_BEFORE_START = "beforeStartOfPlay"
STATUS_PLAYING = "playing"
STATUS_INTERMISSION = "intermission"
STATUS_CANCELED = "canceled"
STATUS_AFTER_PERIOD = "afterPeriod"

# Mapped states for the sensor
STATE_PRE_GAME = "pre_game"
STATE_IN_PROGRESS = "in_progress"
STATE_INTERMISSION = "intermission"
STATE_FINAL = "final"
STATE_OVERTIME = "overtime"
STATE_SHOOTOUT = "shootout"
STATE_CANCELED = "canceled"
STATE_NO_GAME = "no_game"
STATE_SCHEDULED = "scheduled"
