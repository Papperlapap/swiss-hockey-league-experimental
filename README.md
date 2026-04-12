# 🏒 Swiss Hockey National League Live Results

Eine Home Assistant Custom Integration für Live-Resultate der Schweizer National League (Eishockey).

## Features

- **Live-Resultate** aller National League Spiele
- **Lieblingsteam(s)** auswählen – Sensor pro Team
- **Lovelace Card** mit Team-Logos, Scores, Spielstatus und Animationen
- **Automations-Events** bei Goals, Spielstart und Spielende
- **Adaptive Polling**: 30s während Live-Spielen, 5min im Leerlauf
- **HACS-kompatibel**

## Installation

### HACS (empfohlen)

1. HACS öffnen → Integrationen → Custom Repositories
2. URL: `https://github.com/cyman/swiss-hockey-league`
3. Kategorie: Integration
4. Installieren und HA neustarten

### Manuell

1. Ordner `custom_components/swiss_hockey_league` nach `config/custom_components/swiss_hockey_league` kopieren
2. `www/swiss-hockey-card.js` nach `config/www/swiss-hockey-card.js` kopieren
3. Home Assistant neustarten

## Konfiguration

### Integration einrichten

1. Einstellungen → Geräte & Dienste → Integration hinzufügen
2. **Swiss Hockey National League** suchen
3. Teams auswählen die du verfolgen möchtest
4. Fertig! Pro Team wird ein Sensor erstellt.

### Lovelace Card einrichten

#### Frontend-Resource registrieren

Unter **Einstellungen → Dashboards → Ressourcen** (3-Punkte-Menü) hinzufügen:

```
URL:  /swiss_hockey_league/swiss-hockey-card.js
Typ:  JavaScript-Modul
```

Oder falls du die Datei manuell nach `www/` kopiert hast:

```
URL:  /local/swiss-hockey-card.js
Typ:  JavaScript-Modul
```

#### Card zum Dashboard hinzufügen

```yaml
type: custom:swiss-hockey-card
entity: sensor.ev_zug
show_arena: true
show_spectators: false
show_date: true
compact: false
```

### Card-Optionen

| Option           | Typ     | Standard | Beschreibung                   |
|-----------------|---------|----------|--------------------------------|
| `entity`        | string  | *nötig*  | Sensor-Entity des Teams        |
| `show_arena`    | boolean | `true`   | Arena-Name anzeigen            |
| `show_spectators`| boolean | `false`  | Zuschauerzahl anzeigen         |
| `show_date`     | boolean | `true`   | Spieldatum/-zeit anzeigen      |
| `compact`       | boolean | `false`  | Kompakte Darstellung           |

## Team-Logos

Für die beste Darstellung, lege die Team-Logos als PNG-Dateien ab:

```
config/www/swiss_hockey_league/logos/
├── 101139.png  (ZSC Lions)
├── 101144.png  (EV Zug)
├── 101149.png  (EHC Kloten)
├── 101150.png  (HC Lugano)
├── 101151.png  (HC Davos)
├── 101152.png  (HC Ambri-Piotta)
├── 101060.png  (SC Rapperswil-Jona Lakers)
├── 102126.png  (SC Bern)
├── 102127.png  (SCL Tigers)
├── 102128.png  (EHC Biel-Bienne)
├── 103138.png  (Fribourg-Gottéron)
├── 103140.png  (Genève-Servette HC)
├── 103141.png  (Lausanne HC)
└── 103144.png  (HC Ajoie)
```

Ohne Logos werden die Teamkürzel in den Teamfarben angezeigt.

## Sensor-Attribute

Jeder Team-Sensor hat folgende Attribute:

| Attribut               | Beschreibung                    |
|-----------------------|----------------------------------|
| `team_name`           | Vollständiger Teamname           |
| `team_short`          | Teamkürzel (z.B. EVZ)           |
| `team_score`          | Aktuelle Tore deines Teams       |
| `opponent_name`       | Name des Gegners                 |
| `opponent_short`      | Kürzel des Gegners               |
| `opponent_score`      | Tore des Gegners                 |
| `is_home`             | Heimspiel? (true/false)          |
| `home_team` / `away_team` | Heim-/Auswärtsteam          |
| `home_score` / `away_score` | Tore Heim/Auswärts          |
| `is_overtime`         | Verlängerung                     |
| `is_shootout`         | Penaltyschiessen                 |
| `arena`               | Spielort                         |
| `spectators`          | Zuschauerzahl                    |
| `game_date`           | Spielzeitpunkt (ISO)             |
| `game_id`             | Eindeutige Spiel-ID              |

### Sensor-States

| State          | Beschreibung            |
|----------------|------------------------|
| `pre_game`     | Spiel noch nicht gestartet |
| `in_progress`  | Spiel läuft (LIVE)     |
| `intermission` | Drittelpause            |
| `final`        | Beendet (regulär)       |
| `final_ot`     | Beendet nach Verlängerung |
| `final_so`     | Beendet nach Penaltyschiessen |
| `canceled`     | Abgesagt                |
| `no_game`      | Kein Spiel geplant      |

## Automationen

### Events

Die Integration feuert folgende Events:

#### `swiss_hockey_league_goal`
```yaml
automation:
  - alias: "EVZ Goal!"
    triggers:
      - trigger: event
        event_type: swiss_hockey_league_goal
        event_data:
          tracked_team_id: "101144"
          is_tracked_team_goal: true
    actions:
      - action: light.turn_on
        target:
          entity_id: light.wohnzimmer
        data:
          color_name: blue
          brightness: 255
      - delay: "00:00:05"
      - action: light.turn_off
        target:
          entity_id: light.wohnzimmer
```

#### `swiss_hockey_league_game_start`
```yaml
automation:
  - alias: "Spiel startet"
    triggers:
      - trigger: event
        event_type: swiss_hockey_league_game_start
        event_data:
          team_id: "101144"
    actions:
      - action: notify.mobile_app
        data:
          title: "🏒 Anpfiff!"
          message: "{{ trigger.event.data.home_team }} vs {{ trigger.event.data.away_team }}"
```

#### `swiss_hockey_league_game_end`
```yaml
automation:
  - alias: "Spiel beendet"
    triggers:
      - trigger: event
        event_type: swiss_hockey_league_game_end
        event_data:
          team_id: "101144"
    actions:
      - action: notify.mobile_app
        data:
          title: "🏒 Schluss!"
          message: >
            {{ trigger.event.data.home_team }} {{ trigger.event.data.home_score }}
            : {{ trigger.event.data.away_score }} {{ trigger.event.data.away_team }}
            {% if trigger.event.data.is_shootout %}(n.PS.){% elif trigger.event.data.is_overtime %}(n.V.){% endif %}
```

### State-basierte Automationen

```yaml
automation:
  - alias: "TV einschalten wenn EVZ spielt"
    triggers:
      - trigger: state
        entity_id: sensor.ev_zug
        to: "in_progress"
    actions:
      - action: media_player.turn_on
        target:
          entity_id: media_player.tv_wohnzimmer
```

## Datenquelle

Die Daten werden von der offiziellen National League API bezogen:
`https://www.nationalleague.ch/api/games?lang=de-CH`

## Lizenz

MIT License

## Credits

Erstellt mit ❤️ für die beste Hockey-Liga der Welt.
