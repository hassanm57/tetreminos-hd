/**
 * ============================================================================
 * Vercel Serverless Function: Global Matrix Leaderboard API
 * Zero-setup, server-side secure bridge for worldwide cross-device syncing
 * ============================================================================
 */

const DREAMLO_CONFIG = {
  ROGUE: {
    private: "rMLNpB699UyHXcnJBQXiJwHslnVqBxcEuhpvZw0_cnhg",
    public: "6ac4ce858f40bb15a8cefc05",
    defaultStage: "SECTOR 4",
    defaultLines: 58
  },
  CLASSIC: {
    private: "QCzk9sBphUG-huM3Q2wNnQfg12gD2T0kGUkxPhI4IG6g",
    public: "6ac5d71f8f40bb15a8d26c64",
    defaultStage: "LEVEL 11",
    defaultLines: 104
  }
};

const CREATOR_NAME = "hassanm57";
const CREATOR_PASSCODE = "Palaahassan";
const CREATOR_SCORE = 102521;

module.exports = async function handler(req, res) {
  // Set CORS headers so API is globally accessible
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  res.setHeader("Cache-Control", "no-cache, no-store, must-revalidate");

  if (req.method === "OPTIONS") {
    return res.status(200).end();
  }

  const query = req.query || {};
  let body = req.body || {};
  if (typeof body === "string") {
    try {
      body = JSON.parse(body);
    } catch (e) {
      body = {};
    }
  }

  const mode = String(query.mode || body.mode || "ROGUE").toUpperCase();
  const config = (mode === "CLASSIC") ? DREAMLO_CONFIG.CLASSIC : DREAMLO_CONFIG.ROGUE;

  // --------------------------------------------------------------------------
  // GET: Fetch top global scores
  // --------------------------------------------------------------------------
  if (req.method === "GET") {
    try {
      const dreamloUrl = `http://dreamlo.com/lb/${config.public}/json`;
      const response = await fetch(dreamloUrl);
      const json = await response.json();

      let entries = [];
      if (json && json.dreamlo && json.dreamlo.leaderboard && json.dreamlo.leaderboard.entry) {
        const rawEntry = json.dreamlo.leaderboard.entry;
        entries = Array.isArray(rawEntry) ? rawEntry : [rawEntry];
      }

      // Map to standardized format
      let list = entries.map(e => {
        const name = String(e.name || "").trim();
        const score = parseInt(e.score, 10) || 0;
        const lines = parseInt(e.seconds, 10) || 0;
        const stage = String(e.text || "").replace(/_/g, " ") || (mode === "ROGUE" ? "Sector 1" : "Level 1");
        const date = e.date ? String(e.date).split(" ")[0] : new Date().toISOString().split("T")[0];
        const isCreator = (name.toLowerCase() === CREATOR_NAME.toLowerCase());
        return { name, score, lines, stage, date, isCreator };
      });

      // Always guarantee creator hassanm57 is present
      const creatorIndex = list.findIndex(item => item.name.toLowerCase() === CREATOR_NAME.toLowerCase());
      if (creatorIndex === -1) {
        list.push({
          name: CREATOR_NAME,
          score: CREATOR_SCORE,
          lines: config.defaultLines,
          stage: config.defaultStage,
          date: "2026-10-07",
          isCreator: true
        });
      } else {
        list[creatorIndex].isCreator = true;
        if (list[creatorIndex].score < CREATOR_SCORE) {
          list[creatorIndex].score = CREATOR_SCORE;
        }
      }

      // Sort descending by score
      list.sort((a, b) => b.score - a.score);

      // Assign ranks (1, 2, 3...)
      list = list.map((item, idx) => ({
        rank: idx + 1,
        ...item
      }));

      return res.status(200).json({
        status: "success",
        mode: mode,
        count: list.length,
        data: list
      });
    } catch (err) {
      console.error("Leaderboard GET error:", err);
      // Fallback response with creator seed
      return res.status(200).json({
        status: "success",
        mode: mode,
        count: 1,
        data: [
          {
            rank: 1,
            name: CREATOR_NAME,
            score: CREATOR_SCORE,
            lines: config.defaultLines,
            stage: config.defaultStage,
            date: "2026-10-07",
            isCreator: true
          }
        ]
      });
    }
  }

  // --------------------------------------------------------------------------
  // POST: Record new player score
  // --------------------------------------------------------------------------
  if (req.method === "POST") {
    try {

      let name = String(body.name || "").trim().slice(0, 15);
      const score = Math.floor(Number(body.score || 0));
      const lines = Math.floor(Number(body.lines || 0));
      let stage = String(body.stage || (mode === "ROGUE" ? "Sector 1" : "Level 1")).trim().replace(/\s+/g, "_");
      const passcode = String(body.passcode || "").trim();

      // Validate name
      if (!name || name.length < 2) {
        return res.status(400).json({ status: "error", message: "Callsign must be at least 2 characters." });
      }
      if (!/^[a-zA-Z0-9_\-]+$/.test(name)) {
        return res.status(400).json({ status: "error", message: "Callsign contains invalid characters." });
      }
      if (score <= 0) {
        return res.status(400).json({ status: "error", message: "Score must be greater than zero." });
      }

      // Creator reserve protection
      if (name.toLowerCase() === CREATOR_NAME.toLowerCase()) {
        if (passcode !== CREATOR_PASSCODE) {
          return res.status(403).json({
            status: "error",
            message: "👑 'hassanm57' is the reserved Creator identifier."
          });
        }
      }

      // Push to Dreamlo via HTTP GET
      const addUrl = `http://dreamlo.com/lb/${config.private}/add/${encodeURIComponent(name)}/${score}/${lines}/${encodeURIComponent(stage)}`;
      const addResp = await fetch(addUrl);
      const addText = await addResp.text();

      if (addText.trim() === "OK") {
        return res.status(200).json({ status: "success", message: "Score submitted successfully." });
      } else {
        console.warn("Dreamlo add response:", addText);
        return res.status(200).json({ status: "success", message: "Score accepted." });
      }
    } catch (err) {
      console.error("Leaderboard POST error:", err);
      return res.status(500).json({ status: "error", message: err.toString() });
    }
  }

  return res.status(405).json({ status: "error", message: "Method not allowed." });
};
