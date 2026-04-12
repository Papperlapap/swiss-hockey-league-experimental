"""Config flow for Swiss Hockey League integration."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import CONF_TEAMS, DOMAIN, TEAMS


def _team_selector(default: list[str] | None = None) -> vol.Schema:
    """Build a team multi-select schema."""
    team_options = [
        SelectOptionDict(value=team_id, label=f"{info['short']} – {info['name']}")
        for team_id, info in sorted(TEAMS.items(), key=lambda x: x[1]["name"])
    ]

    selector = SelectSelector(
        SelectSelectorConfig(
            options=team_options,
            multiple=True,
            mode=SelectSelectorMode.LIST,
        )
    )

    if default is not None:
        return vol.Schema(
            {vol.Required(CONF_TEAMS, default=default): selector}
        )
    return vol.Schema({vol.Required(CONF_TEAMS): selector})


class SwissHockeyLeagueConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Swiss Hockey League."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            selected_teams = user_input.get(CONF_TEAMS, [])
            if not selected_teams:
                errors["base"] = "no_team_selected"
            else:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title="Swiss Hockey League",
                    data={CONF_TEAMS: selected_teams},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_team_selector(),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow."""
        return SwissHockeyOptionsFlow(config_entry)


class SwissHockeyOptionsFlow(config_entries.OptionsFlow):
    """Handle options for Swiss Hockey League."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        errors = {}

        if user_input is not None:
            selected_teams = user_input.get(CONF_TEAMS, [])
            if not selected_teams:
                errors["base"] = "no_team_selected"
            else:
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data={**self.config_entry.data, CONF_TEAMS: selected_teams},
                )
                return self.async_create_entry(title="", data={})

        current_teams = self.config_entry.data.get(CONF_TEAMS, [])

        return self.async_show_form(
            step_id="init",
            data_schema=_team_selector(default=current_teams),
            errors=errors,
        )
