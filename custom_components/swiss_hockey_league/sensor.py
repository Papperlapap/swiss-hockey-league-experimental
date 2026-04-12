"""Sensor platform for Swiss Hockey League."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_TEAMS, DOMAIN, TEAMS, TEAM_COLORS
from .coordinator import SwissHockeyDataCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Swiss Hockey League sensors from a config entry."""
    coordinator: SwissHockeyDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    tracked_teams = entry.data.get(CONF_TEAMS, [])

    entities = []
    for team_id in tracked_teams:
        entities.append(SwissHockeyTeamSensor(coordinator, team_id, entry))

    async_add_entities(entities)


class SwissHockeyTeamSensor(CoordinatorEntity[SwissHockeyDataCoordinator], SensorEntity):
    """Sensor representing a tracked team's current game."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SwissHockeyDataCoordinator,
        team_id: str,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._team_id = team_id
        team_info = TEAMS.get(team_id, {})
        self._team_name = team_info.get("name", "Unknown")
        self._team_short = team_info.get("short", "???")

        self._attr_unique_id = f"{DOMAIN}_{team_id}"
        self._attr_name = f"{self._team_name}"
        self._attr_icon = "mdi:hockey-sticks"
        self._attr_translation_key = "team_sensor"

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        if self.coordinator.data and self._team_id in self.coordinator.data:
            return self.coordinator.data[self._team_id].get("state", "no_game")
        return "no_game"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        if not self.coordinator.data or self._team_id not in self.coordinator.data:
            return {}

        data = self.coordinator.data[self._team_id]
        team_colors = TEAM_COLORS.get(self._team_id, {})
        opponent_colors = TEAM_COLORS.get(data.get("opponent_id", ""), {})
        home_colors = TEAM_COLORS.get(data.get("home_id", ""), {})
        away_colors = TEAM_COLORS.get(data.get("away_id", ""), {})

        return {
            "team_id": data.get("team_id"),
            "team_name": data.get("team_name"),
            "team_short": data.get("team_short"),
            "team_score": data.get("team_score"),
            "team_color_primary": team_colors.get("primary", "#333333"),
            "team_color_secondary": team_colors.get("secondary", "#FFFFFF"),
            "opponent_id": data.get("opponent_id"),
            "opponent_name": data.get("opponent_name"),
            "opponent_short": data.get("opponent_short"),
            "opponent_score": data.get("opponent_score"),
            "opponent_color_primary": opponent_colors.get("primary", "#333333"),
            "opponent_color_secondary": opponent_colors.get("secondary", "#FFFFFF"),
            "is_home": data.get("is_home"),
            "home_team": data.get("home_team"),
            "home_short": data.get("home_short"),
            "home_id": data.get("home_id"),
            "home_score": data.get("home_score"),
            "home_color_primary": home_colors.get("primary", "#333333"),
            "home_color_secondary": home_colors.get("secondary", "#FFFFFF"),
            "away_team": data.get("away_team"),
            "away_short": data.get("away_short"),
            "away_id": data.get("away_id"),
            "away_score": data.get("away_score"),
            "away_color_primary": away_colors.get("primary", "#333333"),
            "away_color_secondary": away_colors.get("secondary", "#FFFFFF"),
            "is_overtime": data.get("is_overtime"),
            "is_shootout": data.get("is_shootout"),
            "arena": data.get("arena"),
            "spectators": data.get("spectators"),
            "game_id": data.get("game_id"),
            "game_date": data.get("game_date"),
            "game_time": data.get("game_time"),
            "show_game_time": data.get("show_game_time"),
            "api_status": data.get("api_status"),
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success
