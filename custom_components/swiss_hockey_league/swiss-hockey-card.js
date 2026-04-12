/**
 * Swiss Hockey National League Live Results Card
 * Custom Lovelace card for Home Assistant
 * Version 1.0.0
 */

const TEAM_LOGOS_BASE = '/local/swiss_hockey_league/logos/';

const TEAM_META = {
  '101152': { short: 'HCAP', name: 'HC Ambri-Piotta', primary: '#003DA5', secondary: '#FFD100' },
  '101151': { short: 'HCD', name: 'HC Davos', primary: '#003DA5', secondary: '#FFD700' },
  '103138': { short: 'FRI', name: 'Fribourg-Gottéron', primary: '#CE1126', secondary: '#000000' },
  '103140': { short: 'GSHC', name: 'Genève-Servette HC', primary: '#6F263D', secondary: '#FFB81C' },
  '101060': { short: 'SCRJ', name: 'SC Rapperswil-Jona Lakers', primary: '#003DA5', secondary: '#C8C9C7' },
  '101139': { short: 'ZSC', name: 'ZSC Lions', primary: '#003DA5', secondary: '#FFFFFF' },
  '101144': { short: 'EVZ', name: 'EV Zug', primary: '#003DA5', secondary: '#FFFFFF' },
  '102128': { short: 'EHCB', name: 'EHC Biel-Bienne', primary: '#CE1126', secondary: '#000000' },
  '101150': { short: 'HCL', name: 'HC Lugano', primary: '#000000', secondary: '#FFFFFF' },
  '103141': { short: 'LHC', name: 'Lausanne HC', primary: '#003DA5', secondary: '#FFFFFF' },
  '102127': { short: 'SCL', name: 'SCL Tigers', primary: '#F7A600', secondary: '#000000' },
  '102126': { short: 'SCB', name: 'SC Bern', primary: '#FFD700', secondary: '#000000' },
  '101149': { short: 'EHCK', name: 'EHC Kloten', primary: '#003DA5', secondary: '#FF0000' },
  '103144': { short: 'HCA', name: 'HC Ajoie', primary: '#FFD100', secondary: '#000000' },
};

const STATE_LABELS = {
  'pre_game': 'Vorschau',
  'in_progress': 'LIVE',
  'intermission': 'Pause',
  'final': 'Beendet',
  'final_ot': 'Beendet (V)',
  'final_so': 'Beendet (PS)',
  'overtime': 'Verlängerung',
  'shootout': 'Penaltyschiessen',
  'canceled': 'Abgesagt',
  'no_game': 'Kein Spiel',
  'scheduled': 'Geplant',
};

class SwissHockeyCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._prevScores = {};
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error('Please define an entity');
    }
    this._config = {
      show_arena: true,
      show_spectators: false,
      show_date: true,
      compact: false,
      ...config,
    };
  }

  getCardSize() {
    return this._config?.compact ? 2 : 3;
  }

  static getConfigElement() {
    return document.createElement('swiss-hockey-card-editor');
  }

  static getStubConfig() {
    return { entity: '' };
  }

  _render() {
    if (!this._hass || !this._config) return;

    const entityId = this._config.entity;
    const stateObj = this._hass.states[entityId];

    if (!stateObj) {
      this.shadowRoot.innerHTML = `
        <ha-card>
          <div style="padding:16px;text-align:center;color:var(--secondary-text-color)">
            Entity nicht gefunden: ${entityId}
          </div>
        </ha-card>`;
      return;
    }

    const attrs = stateObj.attributes;
    const state = stateObj.state;
    const homeId = attrs.home_id || '';
    const awayId = attrs.away_id || '';
    const homeShort = attrs.home_short || '???';
    const awayShort = attrs.away_short || '???';
    const homeName = attrs.home_team || '';
    const awayName = attrs.away_team || '';
    const homeScore = attrs.home_score ?? 0;
    const awayScore = attrs.away_score ?? 0;
    const arena = attrs.arena || '';
    const spectators = attrs.spectators || '';
    const gameDate = attrs.game_date || '';
    const isOT = attrs.is_overtime || false;
    const isSO = attrs.is_shootout || false;
    const gameTime = attrs.game_time || 0;
    const showGameTime = attrs.show_game_time || false;

    const homeMeta = TEAM_META[homeId] || { short: homeShort, primary: '#444', secondary: '#aaa' };
    const awayMeta = TEAM_META[awayId] || { short: awayShort, primary: '#444', secondary: '#aaa' };

    const isLive = ['in_progress', 'overtime', 'shootout'].includes(state);
    const isIntermission = state === 'intermission';
    const isFinal = state.startsWith('final');
    const isPreGame = state === 'pre_game';
    const noGame = state === 'no_game';

    // Detect goal for animation
    const gameId = attrs.game_id || '';
    let homeGoalAnim = false;
    let awayGoalAnim = false;
    if (this._prevScores[gameId]) {
      if (homeScore > this._prevScores[gameId].home) homeGoalAnim = true;
      if (awayScore > this._prevScores[gameId].away) awayGoalAnim = true;
    }
    this._prevScores[gameId] = { home: homeScore, away: awayScore };

    // Format game date
    let dateStr = '';
    if (gameDate) {
      try {
        const d = new Date(gameDate);
        const weekdays = ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa'];
        dateStr = `${weekdays[d.getDay()]}, ${d.getDate()}.${d.getMonth() + 1}. ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
      } catch (e) {
        dateStr = '';
      }
    }

    // Status label
    let statusLabel = STATE_LABELS[state] || state;
    let statusClass = state;
    if (isLive && showGameTime && gameTime > 0) {
      const mins = Math.floor(gameTime / 60);
      const secs = gameTime % 60;
      statusLabel = `${mins}:${String(secs).padStart(2, '0')}`;
    }

    // Suffix for final
    let finalSuffix = '';
    if (state === 'final_ot') finalSuffix = 'n.V.';
    if (state === 'final_so') finalSuffix = 'n.PS.';

    const compact = this._config.compact;

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          --card-bg: var(--ha-card-background, var(--card-background-color, #1c1c1e));
          --text-primary: var(--primary-text-color, #e5e5e7);
          --text-secondary: var(--secondary-text-color, #8e8e93);
          --text-dim: var(--disabled-text-color, #636366);
          --divider: var(--divider-color, rgba(255,255,255,0.08));
          --live-red: #ff3b30;
          --live-glow: rgba(255, 59, 48, 0.3);
          --goal-flash: rgba(255, 215, 0, 0.6);
        }

        ha-card {
          overflow: hidden;
          border-radius: 16px;
          background: var(--card-bg);
          color: var(--text-primary);
          font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', sans-serif;
          position: relative;
        }

        .card-content {
          padding: ${compact ? '12px 16px' : '16px 20px 14px'};
        }

        /* --- Status Bar --- */
        .status-bar {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: ${compact ? '8px' : '12px'};
          font-size: 11px;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.8px;
          color: var(--text-dim);
        }

        .status-badge {
          display: inline-flex;
          align-items: center;
          gap: 5px;
          padding: 3px 8px;
          border-radius: 6px;
          font-size: 11px;
          font-weight: 700;
          letter-spacing: 0.5px;
        }

        .status-badge.in_progress,
        .status-badge.intermission,
        .status-badge.overtime,
        .status-badge.shootout {
          background: rgba(255, 59, 48, 0.15);
          color: var(--live-red);
        }

        .status-badge.in_progress::before,
        .status-badge.overtime::before,
        .status-badge.shootout::before {
          content: '';
          display: inline-block;
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: var(--live-red);
          animation: pulse-dot 1.5s ease-in-out infinite;
        }

        .status-badge.final, .status-badge.final_ot, .status-badge.final_so {
          background: rgba(142, 142, 147, 0.15);
          color: var(--text-secondary);
        }

        .status-badge.pre_game, .status-badge.scheduled {
          background: rgba(52, 199, 89, 0.12);
          color: #34c759;
        }

        .status-badge.no_game, .status-badge.canceled {
          background: rgba(142, 142, 147, 0.08);
          color: var(--text-dim);
        }

        /* --- Matchup Row --- */
        .matchup {
          display: grid;
          grid-template-columns: 1fr auto 1fr;
          align-items: center;
          gap: ${compact ? '8px' : '12px'};
        }

        .team {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: ${compact ? '4px' : '6px'};
          min-width: 0;
        }

        .team.home { justify-self: end; }
        .team.away { justify-self: start; }

        .team-logo-wrap {
          width: ${compact ? '40px' : '52px'};
          height: ${compact ? '40px' : '52px'};
          border-radius: 14px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 800;
          font-size: ${compact ? '13px' : '15px'};
          letter-spacing: -0.3px;
          position: relative;
          transition: transform 0.2s ease;
          overflow: hidden;
        }

        .team-logo-wrap img {
          width: 100%;
          height: 100%;
          object-fit: contain;
        }

        .team-logo-wrap.goal-flash {
          animation: goal-pop 0.6s cubic-bezier(0.36, 0.07, 0.19, 0.97);
        }

        .team-name {
          font-size: ${compact ? '11px' : '12px'};
          font-weight: 600;
          color: var(--text-secondary);
          text-align: center;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          max-width: 90px;
        }

        /* --- Score Block --- */
        .score-block {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 2px;
          min-width: ${compact ? '70px' : '90px'};
        }

        .score-display {
          display: flex;
          align-items: center;
          gap: ${compact ? '6px' : '10px'};
          font-variant-numeric: tabular-nums;
        }

        .score-num {
          font-size: ${compact ? '32px' : '42px'};
          font-weight: 800;
          line-height: 1;
          letter-spacing: -1.5px;
          transition: all 0.3s ease;
          min-width: ${compact ? '28px' : '36px'};
          text-align: center;
        }

        .score-num.goal-scored {
          animation: score-bump 0.5s cubic-bezier(0.36, 0.07, 0.19, 0.97);
          color: #FFD700;
        }

        .score-sep {
          font-size: ${compact ? '20px' : '26px'};
          font-weight: 300;
          color: var(--text-dim);
          line-height: 1;
        }

        .final-suffix {
          font-size: 10px;
          font-weight: 600;
          color: var(--text-dim);
          text-transform: uppercase;
          letter-spacing: 0.5px;
          margin-top: 2px;
        }

        /* Score dimmed for pre-game */
        .score-display.pre-game .score-num {
          color: var(--text-dim);
          font-size: ${compact ? '20px' : '24px'};
        }

        .vs-text {
          font-size: 14px;
          font-weight: 700;
          color: var(--text-dim);
          letter-spacing: 1px;
        }

        /* --- Meta Bar --- */
        .meta-bar {
          display: flex;
          justify-content: center;
          align-items: center;
          gap: 12px;
          margin-top: ${compact ? '6px' : '10px'};
          font-size: 10px;
          color: var(--text-dim);
          letter-spacing: 0.3px;
        }

        .meta-bar .meta-item {
          display: flex;
          align-items: center;
          gap: 3px;
        }

        .meta-bar .meta-icon {
          font-size: 12px;
          opacity: 0.7;
        }

        /* --- No Game State --- */
        .no-game {
          text-align: center;
          padding: 20px 0;
          color: var(--text-dim);
          font-size: 13px;
        }

        .no-game .team-short {
          font-size: 18px;
          font-weight: 800;
          color: var(--text-secondary);
          margin-bottom: 4px;
        }

        /* --- Live accent line --- */
        .live-accent {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          height: 3px;
          background: linear-gradient(90deg, transparent, var(--live-red), transparent);
          opacity: 0;
          transition: opacity 0.3s ease;
        }

        .live-accent.active {
          opacity: 1;
          animation: accent-pulse 2s ease-in-out infinite;
        }

        /* --- Animations --- */
        @keyframes pulse-dot {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.4; transform: scale(0.8); }
        }

        @keyframes score-bump {
          0% { transform: scale(1); }
          30% { transform: scale(1.3); color: #FFD700; }
          100% { transform: scale(1); }
        }

        @keyframes goal-pop {
          0% { transform: scale(1); box-shadow: 0 0 0 0 var(--goal-flash); }
          40% { transform: scale(1.15); box-shadow: 0 0 20px 5px var(--goal-flash); }
          100% { transform: scale(1); box-shadow: 0 0 0 0 transparent; }
        }

        @keyframes accent-pulse {
          0%, 100% { opacity: 0.6; }
          50% { opacity: 1; }
        }
      </style>

      <ha-card>
        <div class="live-accent ${isLive || isIntermission ? 'active' : ''}"></div>
        <div class="card-content">
          ${noGame ? this._renderNoGame(attrs) : this._renderGame({
            homeShort, awayShort, homeName, awayName,
            homeId, awayId, homeMeta, awayMeta,
            homeScore, awayScore, statusLabel, statusClass,
            dateStr, arena, spectators, finalSuffix,
            isPreGame, isLive, compact, homeGoalAnim, awayGoalAnim,
          })}
        </div>
      </ha-card>
    `;
  }

  _renderNoGame(attrs) {
    const teamShort = attrs.team_short || '???';
    const teamName = attrs.team_name || 'Unbekannt';
    return `
      <div class="no-game">
        <div class="team-short">${teamShort}</div>
        <div>Aktuell kein Spiel geplant</div>
      </div>
    `;
  }

  _renderGame(d) {
    const showArena = this._config.show_arena;
    const showSpectators = this._config.show_spectators;
    const showDate = this._config.show_date;

    return `
      <div class="status-bar">
        <span class="status-badge ${d.statusClass}">${d.statusLabel}</span>
        ${showDate && d.dateStr ? `<span>${d.dateStr}</span>` : ''}
      </div>

      <div class="matchup">
        <div class="team home">
          <div class="team-logo-wrap ${d.homeGoalAnim ? 'goal-flash' : ''}"
               style="background:${d.homeMeta.primary}; color:${d.homeMeta.secondary}">
            <img src="${TEAM_LOGOS_BASE}${d.homeId}.png"
                 onerror="this.style.display='none'; this.parentElement.textContent='${d.homeShort}'"
                 alt="${d.homeShort}">
          </div>
          <span class="team-name">${d.homeShort}</span>
        </div>

        <div class="score-block">
          ${d.isPreGame ? `
            <div class="score-display pre-game">
              <span class="vs-text">VS</span>
            </div>
          ` : `
            <div class="score-display">
              <span class="score-num ${d.homeGoalAnim ? 'goal-scored' : ''}">${d.homeScore}</span>
              <span class="score-sep">:</span>
              <span class="score-num ${d.awayGoalAnim ? 'goal-scored' : ''}">${d.awayScore}</span>
            </div>
            ${d.finalSuffix ? `<span class="final-suffix">${d.finalSuffix}</span>` : ''}
          `}
        </div>

        <div class="team away">
          <div class="team-logo-wrap ${d.awayGoalAnim ? 'goal-flash' : ''}"
               style="background:${d.awayMeta.primary}; color:${d.awayMeta.secondary}">
            <img src="${TEAM_LOGOS_BASE}${d.awayId}.png"
                 onerror="this.style.display='none'; this.parentElement.textContent='${d.awayShort}'"
                 alt="${d.awayShort}">
          </div>
          <span class="team-name">${d.awayShort}</span>
        </div>
      </div>

      ${(showArena && d.arena) || (showSpectators && d.spectators) ? `
        <div class="meta-bar">
          ${showArena && d.arena ? `
            <span class="meta-item">
              <span class="meta-icon">🏟</span>
              <span>${d.arena}</span>
            </span>
          ` : ''}
          ${showSpectators && d.spectators && d.spectators !== '-' ? `
            <span class="meta-item">
              <span class="meta-icon">👥</span>
              <span>${d.spectators}</span>
            </span>
          ` : ''}
        </div>
      ` : ''}
    `;
  }
}

// --- Card Editor ---
class SwissHockeyCardEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._rendered) this._render();
  }

  setConfig(config) {
    this._config = { ...config };
    this._render();
  }

  _render() {
    if (!this._hass) return;
    this._rendered = true;

    // Find all swiss hockey entities
    const entities = Object.keys(this._hass.states)
      .filter(e => e.startsWith('sensor.') &&
        this._hass.states[e].attributes.game_id !== undefined &&
        this._hass.states[e].attributes.team_id !== undefined
      );

    this.shadowRoot.innerHTML = `
      <style>
        .editor {
          padding: 16px;
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        label {
          font-weight: 500;
          font-size: 14px;
          color: var(--primary-text-color);
          display: block;
          margin-bottom: 4px;
        }
        select, input[type="checkbox"] {
          font-size: 14px;
        }
        select {
          width: 100%;
          padding: 8px;
          border-radius: 8px;
          border: 1px solid var(--divider-color);
          background: var(--card-background-color);
          color: var(--primary-text-color);
        }
        .checkbox-row {
          display: flex;
          align-items: center;
          gap: 8px;
        }
      </style>
      <div class="editor">
        <div>
          <label>Entity</label>
          <select id="entity">
            <option value="">-- Wähle ein Team --</option>
            ${entities.map(e => `
              <option value="${e}" ${this._config?.entity === e ? 'selected' : ''}>
                ${this._hass.states[e].attributes.friendly_name || e}
              </option>
            `).join('')}
          </select>
        </div>
        <div class="checkbox-row">
          <input type="checkbox" id="show_arena" ${this._config?.show_arena !== false ? 'checked' : ''}>
          <label for="show_arena" style="margin:0">Arena anzeigen</label>
        </div>
        <div class="checkbox-row">
          <input type="checkbox" id="show_spectators" ${this._config?.show_spectators ? 'checked' : ''}>
          <label for="show_spectators" style="margin:0">Zuschauerzahl anzeigen</label>
        </div>
        <div class="checkbox-row">
          <input type="checkbox" id="show_date" ${this._config?.show_date !== false ? 'checked' : ''}>
          <label for="show_date" style="margin:0">Datum anzeigen</label>
        </div>
        <div class="checkbox-row">
          <input type="checkbox" id="compact" ${this._config?.compact ? 'checked' : ''}>
          <label for="compact" style="margin:0">Kompakte Ansicht</label>
        </div>
      </div>
    `;

    this.shadowRoot.getElementById('entity').addEventListener('change', (e) => {
      this._config = { ...this._config, entity: e.target.value };
      this._fireChange();
    });

    ['show_arena', 'show_spectators', 'show_date', 'compact'].forEach(id => {
      this.shadowRoot.getElementById(id).addEventListener('change', (e) => {
        this._config = { ...this._config, [id]: e.target.checked };
        this._fireChange();
      });
    });
  }

  _fireChange() {
    this.dispatchEvent(new CustomEvent('config-changed', {
      detail: { config: this._config },
    }));
  }
}

// Register elements
customElements.define('swiss-hockey-card', SwissHockeyCard);
customElements.define('swiss-hockey-card-editor', SwissHockeyCardEditor);

// Register card in Lovelace
window.customCards = window.customCards || [];
window.customCards.push({
  type: 'swiss-hockey-card',
  name: 'Swiss Hockey League',
  description: 'Live-Resultate der National League',
  preview: true,
  documentationURL: 'https://github.com/cyman/swiss-hockey-league',
});

console.info(
  '%c SWISS-HOCKEY-CARD %c v1.0.0 ',
  'color: white; background: #003DA5; font-weight: bold; padding: 2px 6px; border-radius: 4px 0 0 4px;',
  'color: #003DA5; background: #FFD700; font-weight: bold; padding: 2px 6px; border-radius: 0 4px 4px 0;'
);
