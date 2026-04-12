"""Data coordinator for Swiss Hockey League."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    API_URL,
    DEFAULT_SCAN_INTERVAL_IDLE,
    DEFAULT_SCAN_INTERVAL_LIVE,
    DOMAIN,
    EVENT_GAME_END,
    EVENT_GAME_START,
    EVENT_GOAL,
    STATUS_BEFORE_START,
    STATUS_CANCELED,
    STATUS_FINISHED,
    TEAMS,
)

_LOGGER = logging.getLogger(__name__)


class SwissHockeyDataCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to fetch data from the National League API."""

    def __init__(self, hass: HomeAssistant, tracked_teams: list[str]) -> None:
        """Initialize the coordinator."""
        self.tracked_teams = tracked_teams
        self._previous_scores: dict[str, dict[str, int]] = {}
        self._previous_statuses: dict[str, str] = {}
        self._has_live_game = False

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL_IDLE),
        )

    def _get_update_interval(self) -> timedelta:
        """Determine update interval based on whether games are live."""
        if self._has_live_game:
            return timedelta(seconds=DEFAULT_SCAN_INTERVAL_LIVE)
        return timedelta(seconds=DEFAULT_SCAN_INTERVAL_IDLE)

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the National League API."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(API_URL, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status != 200:
                        raise UpdateFailed(f"API returned status {resp.status}")
                    games_data = await resp.json()
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err

        result: dict[str, Any] = {}
        has_live = False

        now = datetime.now(timezone.utc)
        today = now.date()

        for team_id in self.tracked_teams:
            team_game = self._find_current_game(games_data, team_id, today, now)
            if team_game:
                game_data = self._process_game(team_game, team_id)
                result[team_id] = game_data

                # Check if game is live
                status = team_game.get("status", "")
                if status not in (STATUS_FINISHED, STATUS_BEFORE_START, STATUS_CANCELED):
                    has_live = True

                # Fire events for state changes
                self._check_and_fire_events(team_id, game_data, team_game)
            else:
                result[team_id] = self._no_game_data(team_id)

        self._has_live_game = has_live
        self.update_interval = self._get_update_interval()

        return result

    def _find_current_game(
        self, games: list[dict], team_id: str, today, now: datetime
    ) -> dict | None:
        """Find the most relevant game for a team (today's or next upcoming)."""
        team_games = []
        for game in games:
            if game.get("isExhibition", False):
                continue
            if game.get("homeTeamId") == team_id or game.get("awayTeamId") == team_id:
                team_games.append(game)

        if not team_games:
            return None

        # First priority: currently live game
        for game in team_games:
            status = game.get("status", "")
            if status not in (STATUS_FINISHED, STATUS_BEFORE_START, STATUS_CANCELED):
                return game

        # Second priority: today's game (not yet started or just finished)
        todays_games = []
        for game in team_games:
            try:
                game_date = datetime.fromisoformat(game["date"]).date()
                if game_date == today:
                    todays_games.append(game)
            except (ValueError, KeyError):
                continue

        if todays_games:
            # Prefer unfinished, then most recent
            for game in todays_games:
                if game.get("status") == STATUS_BEFORE_START:
                    return game
            # Return the latest finished today
            return todays_games[-1]

        # Third priority: next upcoming game
        upcoming = []
        for game in team_games:
            try:
                game_dt = datetime.fromisoformat(game["date"])
                if game_dt > now and game.get("status") == STATUS_BEFORE_START:
                    upcoming.append((game_dt, game))
            except (ValueError, KeyError):
                continue

        if upcoming:
            upcoming.sort(key=lambda x: x[0])
            return upcoming[0][1]

        # Fourth priority: most recent finished game
        finished = []
        for game in team_games:
            if game.get("status") == STATUS_FINISHED:
                try:
                    game_dt = datetime.fromisoformat(game["date"])
                    finished.append((game_dt, game))
                except (ValueError, KeyError):
                    continue

        if finished:
            finished.sort(key=lambda x: x[0], reverse=True)
            return finished[0][1]

        return None

    def _process_game(self, game: dict, team_id: str) -> dict[str, Any]:
        """Process a game into sensor-friendly data."""
        is_home = game.get("homeTeamId") == team_id
        status = game.get("status", "")

        if is_home:
            team_score = game.get("homeTeamResult", 0)
            opponent_score = game.get("awayTeamResult", 0)
            team_name = game.get("homeTeamName", "")
            team_short = game.get("homeTeamShortName", "")
            opponent_name = game.get("awayTeamName", "")
            opponent_short = game.get("awayTeamShortName", "")
            opponent_id = game.get("awayTeamId", "")
        else:
            team_score = game.get("awayTeamResult", 0)
            opponent_score = game.get("homeTeamResult", 0)
            team_name = game.get("awayTeamName", "")
            team_short = game.get("awayTeamShortName", "")
            opponent_name = game.get("homeTeamName", "")
            opponent_short = game.get("homeTeamShortName", "")
            opponent_id = game.get("homeTeamId", "")

        # Map API status to our states
        # Known API statuses: finished, beforeStartOfPlay, canceled,
        # playing, period1, period2, period3, overtime, shootout,
        # intermission, afterPeriod, endOfPeriod, overTimeBreak
        status_lower = status.lower()

        if status == STATUS_FINISHED:
            if game.get("isShootout"):
                state = "final_so"
            elif game.get("isOvertime"):
                state = "final_ot"
            else:
                state = "final"
        elif status == STATUS_BEFORE_START:
            state = "pre_game"
        elif status == STATUS_CANCELED:
            state = "canceled"
        elif any(kw in status_lower for kw in ("intermission", "afterperiod", "endofperiod", "overtimebreak", "break")):
            state = "intermission"
        elif "shootout" in status_lower:
            state = "shootout"
        elif "overtime" in status_lower:
            state = "overtime"
        elif any(kw in status_lower for kw in ("playing", "period", "live")):
            state = "in_progress"
        elif status_lower in ("", "unknown"):
            state = "no_game"
        else:
            # Fallback: if score > 0, assume in_progress
            if (game.get("homeTeamResult", 0) + game.get("awayTeamResult", 0)) > 0:
                state = "in_progress"
            else:
                state = "pre_game"

        try:
            game_date = datetime.fromisoformat(game["date"])
        except (ValueError, KeyError):
            game_date = None

        return {
            "state": state,
            "team_id": team_id,
            "team_name": team_name,
            "team_short": team_short,
            "team_score": team_score,
            "opponent_id": opponent_id,
            "opponent_name": opponent_name,
            "opponent_short": opponent_short,
            "opponent_score": opponent_score,
            "is_home": is_home,
            "home_team": game.get("homeTeamName", ""),
            "home_short": game.get("homeTeamShortName", ""),
            "home_id": game.get("homeTeamId", ""),
            "home_score": game.get("homeTeamResult", 0),
            "away_team": game.get("awayTeamName", ""),
            "away_short": game.get("awayTeamShortName", ""),
            "away_id": game.get("awayTeamId", ""),
            "away_score": game.get("awayTeamResult", 0),
            "is_overtime": game.get("isOvertime", False),
            "is_shootout": game.get("isShootout", False),
            "arena": game.get("arena", ""),
            "spectators": game.get("spectators", ""),
            "game_id": game.get("gameId", ""),
            "game_date": game_date.isoformat() if game_date else None,
            "game_time": game.get("gameTime", 0),
            "show_game_time": game.get("showGameTime", False),
            "api_status": status,
        }

    def _no_game_data(self, team_id: str) -> dict[str, Any]:
        """Return empty data when no game is found."""
        team_info = TEAMS.get(team_id, {})
        return {
            "state": "no_game",
            "team_id": team_id,
            "team_name": team_info.get("name", "Unknown"),
            "team_short": team_info.get("short", "???"),
            "team_score": 0,
            "opponent_id": "",
            "opponent_name": "",
            "opponent_short": "",
            "opponent_score": 0,
            "is_home": False,
            "home_team": "",
            "home_short": "",
            "home_id": "",
            "home_score": 0,
            "away_team": "",
            "away_short": "",
            "away_id": "",
            "away_score": 0,
            "is_overtime": False,
            "is_shootout": False,
            "arena": "",
            "spectators": "",
            "game_id": "",
            "game_date": None,
            "game_time": 0,
            "show_game_time": False,
            "api_status": "",
        }

    def _check_and_fire_events(
        self, team_id: str, game_data: dict[str, Any], raw_game: dict
    ) -> None:
        """Check for state changes and fire events."""
        game_id = game_data.get("game_id", "")
        if not game_id:
            return

        current_home_score = raw_game.get("homeTeamResult", 0)
        current_away_score = raw_game.get("awayTeamResult", 0)
        current_status = raw_game.get("status", "")

        prev_scores = self._previous_scores.get(game_id)
        prev_status = self._previous_statuses.get(game_id)

        # Detect goals
        if prev_scores is not None:
            prev_home = prev_scores.get("home", 0)
            prev_away = prev_scores.get("away", 0)

            if current_home_score > prev_home:
                self._fire_goal_event(
                    team_id,
                    game_data,
                    scoring_team_id=raw_game.get("homeTeamId", ""),
                    scoring_team_name=raw_game.get("homeTeamName", ""),
                    scoring_team_short=raw_game.get("homeTeamShortName", ""),
                    new_home_score=current_home_score,
                    new_away_score=current_away_score,
                )

            if current_away_score > prev_away:
                self._fire_goal_event(
                    team_id,
                    game_data,
                    scoring_team_id=raw_game.get("awayTeamId", ""),
                    scoring_team_name=raw_game.get("awayTeamName", ""),
                    scoring_team_short=raw_game.get("awayTeamShortName", ""),
                    new_home_score=current_home_score,
                    new_away_score=current_away_score,
                )

        # Detect game start
        if prev_status == STATUS_BEFORE_START and current_status not in (
            STATUS_BEFORE_START,
            STATUS_CANCELED,
        ):
            self.hass.bus.async_fire(
                EVENT_GAME_START,
                {
                    "team_id": team_id,
                    "game_id": game_id,
                    "home_team": raw_game.get("homeTeamName", ""),
                    "away_team": raw_game.get("awayTeamName", ""),
                    "arena": raw_game.get("arena", ""),
                },
            )

        # Detect game end
        if prev_status and prev_status != STATUS_FINISHED and current_status == STATUS_FINISHED:
            self.hass.bus.async_fire(
                EVENT_GAME_END,
                {
                    "team_id": team_id,
                    "game_id": game_id,
                    "home_team": raw_game.get("homeTeamName", ""),
                    "away_team": raw_game.get("awayTeamName", ""),
                    "home_score": current_home_score,
                    "away_score": current_away_score,
                    "is_overtime": raw_game.get("isOvertime", False),
                    "is_shootout": raw_game.get("isShootout", False),
                },
            )

        # Update previous state
        self._previous_scores[game_id] = {
            "home": current_home_score,
            "away": current_away_score,
        }
        self._previous_statuses[game_id] = current_status

    def _fire_goal_event(
        self,
        tracked_team_id: str,
        game_data: dict[str, Any],
        scoring_team_id: str,
        scoring_team_name: str,
        scoring_team_short: str,
        new_home_score: int,
        new_away_score: int,
    ) -> None:
        """Fire a goal event."""
        is_tracked_team_goal = scoring_team_id == tracked_team_id

        self.hass.bus.async_fire(
            EVENT_GOAL,
            {
                "tracked_team_id": tracked_team_id,
                "game_id": game_data.get("game_id", ""),
                "scoring_team_id": scoring_team_id,
                "scoring_team_name": scoring_team_name,
                "scoring_team_short": scoring_team_short,
                "is_tracked_team_goal": is_tracked_team_goal,
                "home_team": game_data.get("home_team", ""),
                "away_team": game_data.get("away_team", ""),
                "home_score": new_home_score,
                "away_score": new_away_score,
            },
        )
        _LOGGER.info(
            "Goal! %s scored. Score: %s %d - %d %s",
            scoring_team_name,
            game_data.get("home_team", ""),
            new_home_score,
            new_away_score,
            game_data.get("away_team", ""),
        )
