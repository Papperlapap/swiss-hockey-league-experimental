"""Swiss Hockey National League Live Results integration."""
from __future__ import annotations

import logging
import os
from pathlib import Path

from homeassistant.components.frontend import async_register_built_in_panel
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_TEAMS, DOMAIN
from .coordinator import SwissHockeyDataCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]

# Path to the Lovelace card JS file
CARD_JS = "swiss-hockey-card.js"
CARD_URL = f"/{DOMAIN}/{CARD_JS}"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Swiss Hockey League from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    tracked_teams = entry.data.get(CONF_TEAMS, [])
    if not tracked_teams:
        _LOGGER.warning("No teams configured for Swiss Hockey League")
        return False

    coordinator = SwissHockeyDataCoordinator(hass, tracked_teams)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register the Lovelace card JS file as a static path
    await _async_register_card(hass)

    # Listen for options updates to reload with new teams
    entry.async_on_unload(entry.add_update_listener(_async_update_options))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok


async def _async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update — reload the entry."""
    await hass.config_entries.async_reload(entry.entry_id)


async def _async_register_card(hass: HomeAssistant) -> None:
    """Serve the card JS so users can add it as a Lovelace resource."""
    card_file = Path(__file__).parent / CARD_JS
    if not card_file.is_file():
        _LOGGER.error("Card file not found at %s", card_file)
        return

    # Only register once
    if CARD_URL in (hass.data.get("_swiss_hockey_registered") or ""):
        return

    hass.http.async_register_static_paths([(CARD_URL, str(card_file))])
    hass.data["_swiss_hockey_registered"] = CARD_URL

    _LOGGER.info(
        "Swiss Hockey League card served at %s — add it as a Lovelace resource", CARD_URL
    )
