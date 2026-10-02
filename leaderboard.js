/**
 * ============================================================================
 * TETREMINOS HD: NEON RESONANCE - CLIENT LEADERBOARD & CALLSIGN SYSTEM
 * Free Serverless Global Matrix Leaderboard (Google Sheets Web App Integration)
 * Creator & Champion: hassanm57 (Gold Glow + Crown at #1)
 * ============================================================================
 */

// Paste your deployed Google Apps Script Web App URL below:
// (Leave as empty string "" to use local storage & built-in matrix records until deployed)
const GOOGLE_SHEET_LEADERBOARD_URL = "";

const CREATOR_CALLSIGN = "hassanm57";

// Default Matrix High Scores: Only #1 Creator & Champion hassanm57
const DEFAULT_LEADERBOARDS = {
  ROGUE: [
    { rank: 1, name: "hassanm57", score: 9412, stage: "SECTOR 3", lines: 28, date: "2026-10-02", isCreator: true }
  ],
  CLASSIC: [
    { rank: 1, name: "hassanm57", score: 9412, stage: "LEVEL 5", lines: 28, date: "2026-10-02", isCreator: true }
  ]
};

// State
let currentLeaderboardMode = "ROGUE";
let cachedLeaderboardData = {
  ROGUE: null,
  CLASSIC: null
};

/**
 * Retrieves or generates a persistent Pilot ID (UUID token) to guarantee unique name ownership.
 */
function getOrCreatePilotId() {
  try {
    let id = localStorage.getItem("tetremino_pilot_id");
    if (!id) {
      id = "pilot_" + Math.random().toString(36).substring(2, 9) + Date.now().toString(36);
      localStorage.setItem("tetremino_pilot_id", id);
    }
    return id;
  } catch (e) {
    return "guest_" + Math.random().toString(36).substring(2, 8);
  }
}

/**
 * Retrieves the current player's confirmed callsign.
 */
function getPilotCallsign() {
  try {
    const saved = localStorage.getItem("tetremino_callsign");
    if (saved && saved.trim()) {
      return saved.trim();
    }
  } catch (e) {}
  const id = getOrCreatePilotId();
  return "PILOT_" + id.slice(-4).toUpperCase();
}

/**
 * Validates whether a callsign is allowed and available.
 */
function validateCallsign(name) {
  if (!name) {
    return { valid: false, message: "Callsign cannot be empty." };
  }
  const clean = name.trim();
  if (clean.length < 2) {
    return { valid: false, message: "Callsign must be at least 2 characters." };
  }
  if (clean.length > 15) {
    return { valid: false, message: "Callsign maximum length is 15 characters." };
  }
  if (!/^[a-zA-Z0-9_\-]+$/.test(clean)) {
    return { valid: false, message: "Only letters, numbers, hyphens, and underscores allowed." };
  }

  // 1. Strict creator protection: No one can claim hassanm57 without passcode
  if (clean.toLowerCase() === CREATOR_CALLSIGN.toLowerCase()) {
    const isActuallyCreator = (localStorage.getItem("tetremino_is_creator") === "true");
    if (!isActuallyCreator) {
      const pass = prompt("👑 Enter Creator Passcode to authenticate as hassanm57 (or Cancel):");
      if (pass && (pass === "hm57" || pass.toLowerCase() === "hassan" || pass.toLowerCase() === "hassanm57" || pass.toLowerCase() === "creator")) {
        localStorage.setItem("tetremino_is_creator", "true");
        return { valid: true, cleanName: CREATOR_CALLSIGN };
      }
      return {
        valid: false,
        message: "👑 'hassanm57' is the reserved Creator & Matrix Champion identifier. Please choose your own callsign!"
      };
    }
  }

  // 2. Check cached leaderboard to prevent duplicates
  const myId = getOrCreatePilotId();
  for (const m of ["ROGUE", "CLASSIC"]) {
    const list = cachedLeaderboardData[m] || DEFAULT_LEADERBOARDS[m];
    for (const item of list) {
      if (item.name && item.name.toLowerCase() === clean.toLowerCase()) {
        if (item.pilotId && item.pilotId !== myId) {
          return {
            valid: false,
            message: `⚠️ Callsign '${clean}' is already claimed by another pilot!`
          };
        }
      }
    }
  }

  return { valid: true, cleanName: clean };
}

/**
 * Sets and persists the player's callsign.
 */
function setPilotCallsign(name) {
  const result = validateCallsign(name);
  if (!result.valid) {
    return result;
  }
  try {
    localStorage.setItem("tetremino_callsign", result.cleanName);
    updateCallsignUI();
  } catch (e) {}
  return { valid: true, callsign: result.cleanName };
}

/**
 * Fetches the leaderboard for the specified mode (ROGUE or CLASSIC).
 */
async function fetchLeaderboardData(mode) {
  mode = (mode || currentLeaderboardMode).toUpperCase();

  // If Google Sheet Web App URL is provided, fetch live scores
  if (GOOGLE_SHEET_LEADERBOARD_URL && GOOGLE_SHEET_LEADERBOARD_URL.trim() !== "") {
    try {
      const resp = await fetch(`${GOOGLE_SHEET_LEADERBOARD_URL}?mode=${mode}&t=${Date.now()}`);
      if (resp.ok) {
        const json = await resp.json();
        if (json.status === "success" && Array.isArray(json.data) && json.data.length > 0) {
          cachedLeaderboardData[mode] = json.data;
          saveLocalCache(mode, json.data);
          return json.data;
        }
      }
    } catch (err) {
      console.warn("Live leaderboard fetch error (falling back to cache):", err);
    }
  }

  // Fallback to local storage or default seed data
  const local = loadLocalCache(mode);
  if (local && local.length > 0) {
    cachedLeaderboardData[mode] = local;
    return local;
  }

  cachedLeaderboardData[mode] = DEFAULT_LEADERBOARDS[mode];
  return DEFAULT_LEADERBOARDS[mode];
}

/**
 * Submits a new score to the leaderboard.
 */
async function submitScoreToLeaderboard(score, mode, lines, stage) {
  if (score <= 0) return;
  mode = (mode || "ROGUE").toUpperCase();
  const pilotId = getOrCreatePilotId();
  const name = getPilotCallsign();
  const date = new Date().toISOString().split("T")[0];

  const payload = {
    pilotId: pilotId,
    name: name,
    score: Math.floor(score),
    mode: mode,
    lines: Math.floor(lines || 0),
    stage: stage || (mode === "ROGUE" ? "Sector 1" : "Level 1")
  };

  // 1. Submit to Google Sheets if connected
  if (GOOGLE_SHEET_LEADERBOARD_URL && GOOGLE_SHEET_LEADERBOARD_URL.trim() !== "") {
    try {
      fetch(GOOGLE_SHEET_LEADERBOARD_URL, {
        method: "POST",
        mode: "no-cors", // Standard for Google Apps Script Web Apps
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      }).catch(e => console.warn("Background sheet sync notice:", e));
    } catch (e) {}
  }

  // 2. Always update local offline storage immediately
  let list = cachedLeaderboardData[mode] || loadLocalCache(mode) || [...DEFAULT_LEADERBOARDS[mode]];
  
  // Find if current pilot already has an entry
  let foundIdx = -1;
  for (let i = 0; i < list.length; i++) {
    if (list[i].name.toLowerCase() === name.toLowerCase()) {
      foundIdx = i;
      break;
    }
  }

  if (foundIdx >= 0) {
    if (score > list[foundIdx].score) {
      list[foundIdx].score = score;
      list[foundIdx].lines = lines;
      list[foundIdx].stage = payload.stage;
      list[foundIdx].date = date;
    }
  } else {
    list.push({
      pilotId: pilotId,
      name: name,
      score: score,
      lines: lines,
      stage: payload.stage,
      date: date,
      isCreator: false
    });
  }

  // Re-sort descending
  list.sort((a, b) => b.score - a.score);

  // Re-rank
  list.forEach((item, idx) => {
    item.rank = idx + 1;
  });

  cachedLeaderboardData[mode] = list;
  saveLocalCache(mode, list);

  return { success: true, rank: list.findIndex(item => item.name.toLowerCase() === name.toLowerCase()) + 1 };
}

const LB_CACHE_KEY_VERSION = "v3";

// Clean obsolete legacy leaderboard caches and sync high score to 9412
try {
  localStorage.removeItem("tetremino_lb_rogue");
  localStorage.removeItem("tetremino_lb_classic");
  localStorage.removeItem("tetremino_lb_v2_rogue");
  localStorage.removeItem("tetremino_lb_v2_classic");
  const curHigh = parseInt(localStorage.getItem("tetremino_high_score") || "0", 10);
  if (curHigh < 9412) {
    localStorage.setItem("tetremino_high_score", "9412");
  }
} catch (e) {}

function saveLocalCache(mode, data) {
  try {
    localStorage.setItem(`tetremino_lb_${LB_CACHE_KEY_VERSION}_${mode.toLowerCase()}`, JSON.stringify(data));
  } catch (e) {}
}

function loadLocalCache(mode) {
  try {
    const raw = localStorage.getItem(`tetremino_lb_${LB_CACHE_KEY_VERSION}_${mode.toLowerCase()}`);
    if (raw) return JSON.parse(raw);
  } catch (e) {}
  return null;
}

/**
 * UI Rendering and Modal Coordinators
 */
function openLeaderboardModal(mode) {
  currentLeaderboardMode = (mode || currentLeaderboardMode || "ROGUE").toUpperCase();
  const modal = document.getElementById("leaderboardModal");
  if (!modal) return;

  modal.style.display = "flex";
  updateCallsignUI();
  updateLeaderboardTabs();
  renderLeaderboardTable(currentLeaderboardMode);
}

function closeLeaderboardModal() {
  const modal = document.getElementById("leaderboardModal");
  if (modal) {
    modal.style.display = "none";
  }
}

function updateLeaderboardTabs() {
  const tabRogue = document.getElementById("lb-tab-rogue");
  const tabClassic = document.getElementById("lb-tab-classic");
  if (tabRogue && tabClassic) {
    if (currentLeaderboardMode === "ROGUE") {
      tabRogue.classList.add("active");
      tabClassic.classList.remove("active");
    } else {
      tabClassic.classList.add("active");
      tabRogue.classList.remove("active");
    }
  }
}

async function renderLeaderboardTable(mode) {
  mode = (mode || currentLeaderboardMode).toUpperCase();
  const tbody = document.getElementById("lbTableBody");
  const loading = document.getElementById("lbLoadingIndicator");
  const currentPilotName = getPilotCallsign();

  if (loading) loading.style.display = "flex";
  if (tbody) tbody.innerHTML = "";

  const data = await fetchLeaderboardData(mode);

  if (loading) loading.style.display = "none";
  if (!tbody) return;

  if (!data || data.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" class="lb-empty">NO PILOT RECORDS DETECTED IN THIS SECTOR</td></tr>`;
    return;
  }

  let userBestScore = 0;
  let rowsHtml = "";

  data.forEach((item, index) => {
    const rank = index + 1;
    const isHassan = (item.name.toLowerCase() === CREATOR_CALLSIGN.toLowerCase());
    const isMe = (item.name.toLowerCase() === currentPilotName.toLowerCase());

    if (isMe) {
      userBestScore = Math.max(userBestScore, item.score);
    }

    let rankBadge = `${rank}`;
    if (rank === 1) rankBadge = `<span class="rank-badge gold">🥇 #1</span>`;
    else if (rank === 2) rankBadge = `<span class="rank-badge silver">🥈 #2</span>`;
    else if (rank === 3) rankBadge = `<span class="rank-badge bronze">🥉 #3</span>`;
    else rankBadge = `<span class="rank-badge standard">#${rank}</span>`;

    // Callsign styling
    let nameHtml = `<span class="pilot-regular">${escapeHtml(item.name)}</span>`;
    if (isHassan) {
      // Creator hassanm57: Gold glowy color with crown
      nameHtml = `<span class="pilot-creator"><span class="crown-icon">👑</span> ${escapeHtml(item.name)} <span class="creator-tag">CREATOR</span></span>`;
    } else if (isMe) {
      nameHtml = `<span class="pilot-me">${escapeHtml(item.name)} <span class="you-tag">(YOU)</span></span>`;
    }

    let rowClass = "lb-row";
    if (isHassan) rowClass += " lb-row-creator";
    else if (isMe) rowClass += " lb-row-me";

    rowsHtml += `
      <tr class="${rowClass}">
        <td class="col-rank">${rankBadge}</td>
        <td class="col-pilot">${nameHtml}</td>
        <td class="col-score"><strong class="score-num">${Number(item.score).toLocaleString()}</strong></td>
        <td class="col-stage"><span class="stage-pill">${escapeHtml(item.stage || "-")}</span></td>
        <td class="col-lines">${Number(item.lines || 0)}</td>
        <td class="col-date">${escapeHtml(item.date || "-")}</td>
      </tr>
    `;
  });

  tbody.innerHTML = rowsHtml;

  // Update pilot card banner
  const pilotBestEl = document.getElementById("lbCurrentPilotBest");
  if (pilotBestEl) {
    pilotBestEl.innerText = `${userBestScore.toLocaleString()} PTS`;
  }
}

function updateCallsignUI() {
  const currentName = getPilotCallsign();
  const inputEl = document.getElementById("playerCallsignInput");
  const lbPilotEl = document.getElementById("lbCurrentPilotName");

  if (inputEl && document.activeElement !== inputEl) {
    inputEl.value = currentName;
  }
  if (lbPilotEl) {
    lbPilotEl.innerText = currentName;
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// Global Game Over Handler (Invoked from Python WebAssembly engine)
window.onTetrisGameOver = function(score, mode, lines, sector) {
  try {
    const stageStr = (mode === "ROGUE") ? `SECTOR ${sector || 1}` : `LEVEL ${Math.floor((lines || 0) / 10) + 1}`;
    submitScoreToLeaderboard(score, mode, lines, stageStr);
  } catch (err) {
    console.error("Game over leaderboard submission notice:", err);
  }
};

// Wire Event Listeners on DOM Load
document.addEventListener("DOMContentLoaded", () => {
  updateCallsignUI();

  // 1. Callsign input listener
  const callsignInput = document.getElementById("playerCallsignInput");
  const callsignFeedback = document.getElementById("callsignFeedback");

  if (callsignInput) {
    // Isolate input element from game engine keyboard listeners
    const stopPropagation = (e) => {
      e.stopPropagation();
    };

    callsignInput.addEventListener("keydown", (e) => {
      e.stopPropagation();
      if (e.key === "Enter") {
        e.preventDefault();
        const res = setPilotCallsign(e.target.value);
        if (callsignFeedback) {
          if (!res.valid) {
            callsignFeedback.innerText = res.message;
            callsignFeedback.className = "callsign-feedback error";
          } else {
            callsignFeedback.innerText = `✓ Callsign set to: ${res.callsign}`;
            callsignFeedback.className = "callsign-feedback success";
          }
        }
        callsignInput.blur();
      }
    });

    callsignInput.addEventListener("keyup", stopPropagation);
    callsignInput.addEventListener("keypress", stopPropagation);

    callsignInput.addEventListener("input", (e) => {
      const val = e.target.value.trim();
      if (!val) {
        if (callsignFeedback) callsignFeedback.innerText = "";
        return;
      }
      const res = validateCallsign(val);
      if (!res.valid) {
        if (callsignFeedback) {
          callsignFeedback.innerText = res.message;
          callsignFeedback.className = "callsign-feedback error";
        }
      } else {
        if (callsignFeedback) {
          callsignFeedback.innerText = "✓ Callsign valid and available";
          callsignFeedback.className = "callsign-feedback success";
        }
      }
    });

    callsignInput.addEventListener("change", (e) => {
      const res = setPilotCallsign(e.target.value);
      if (callsignFeedback) {
        if (!res.valid) {
          callsignFeedback.innerText = res.message;
          callsignFeedback.className = "callsign-feedback error";
        } else {
          callsignFeedback.innerText = `✓ Callsign set to: ${res.callsign}`;
          callsignFeedback.className = "callsign-feedback success";
        }
      }
    });
  }

  // 2. Leaderboard button listeners
  const btnWelcomeLb = document.getElementById("btn-welcome-leaderboard");
  const btnHeaderLb = document.getElementById("btn-leaderboard");
  const btnMobileLb = document.getElementById("btn-mobile-leaderboard");
  const btnPauseLb = document.getElementById("btn-pause-leaderboard");
  const btnCloseLb = document.getElementById("btn-close-leaderboard");
  const btnRefreshLb = document.getElementById("btn-refresh-leaderboard");
  const tabRogue = document.getElementById("lb-tab-rogue");
  const tabClassic = document.getElementById("lb-tab-classic");

  if (btnWelcomeLb) {
    btnWelcomeLb.addEventListener("click", () => openLeaderboardModal(currentLeaderboardMode));
  }
  if (btnHeaderLb) {
    btnHeaderLb.addEventListener("click", () => openLeaderboardModal(currentLeaderboardMode));
  }
  if (btnMobileLb) {
    btnMobileLb.addEventListener("click", (e) => {
      e.stopPropagation();
      openLeaderboardModal(currentLeaderboardMode);
    });
  }
  if (btnPauseLb) {
    btnPauseLb.addEventListener("click", () => openLeaderboardModal(currentLeaderboardMode));
  }
  if (btnCloseLb) {
    btnCloseLb.addEventListener("click", closeLeaderboardModal);
  }
  if (btnRefreshLb) {
    btnRefreshLb.addEventListener("click", () => renderLeaderboardTable(currentLeaderboardMode));
  }
  if (tabRogue) {
    tabRogue.addEventListener("click", () => {
      currentLeaderboardMode = "ROGUE";
      updateLeaderboardTabs();
      renderLeaderboardTable("ROGUE");
    });
  }
  if (tabClassic) {
    tabClassic.addEventListener("click", () => {
      currentLeaderboardMode = "CLASSIC";
      updateLeaderboardTabs();
      renderLeaderboardTable("CLASSIC");
    });
  }

  const lbModal = document.getElementById("leaderboardModal");
  if (lbModal) {
    lbModal.addEventListener("click", (e) => {
      if (e.target === lbModal) {
        closeLeaderboardModal();
      }
    });
  }
});
