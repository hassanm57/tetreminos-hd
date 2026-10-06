/**
 * ============================================================================
 * TETREMINOS HD: NEON RESONANCE - GLOBAL LEADERBOARD BACKEND
 * Free Serverless Backend powered by Google Sheets & Google Apps Script
 * Creator & Champion: hassanm57
 * ============================================================================
 * 
 * QUICK SETUP INSTRUCTIONS (Takes < 1 minute):
 * 1. Open Google Sheets (https://sheets.new) in your browser.
 * 2. Rename the spreadsheet to: "Tetreminos HD Leaderboard".
 * 3. In the menu, click: Extensions > Apps Script.
 * 4. Delete any code in the script editor and paste this ENTIRE file.
 * 5. Click "Deploy" (blue button at top right) > "New deployment".
 * 6. Under "Select type", choose: "Web app".
 * 7. Set configuration:
 *    - Description: "Tetreminos HD Leaderboard API"
 *    - Execute as: "Me" (your email)
 *    - Who has access: "Anyone" (crucial so all players can read/write scores!)
 * 8. Click "Deploy", authorize access with your Google account.
 * 9. Copy the "Web app URL" (it looks like: https://script.google.com/macros/s/.../exec).
 * 10. Paste that Web app URL into `GOOGLE_SHEET_LEADERBOARD_URL` inside `leaderboard.js`!
 * ============================================================================
 */

const SPREADSHEET_ROGUE = "RogueLeaderboard";
const SPREADSHEET_CLASSIC = "ClassicLeaderboard";
const CREATOR_NAME = "hassanm57";

// High scores for the Creator & Champion
const CREATOR_ROGUE_SCORE = 102521;   // High Score Record
const CREATOR_CLASSIC_SCORE = 102521; // High Score Record

/**
 * Handles GET requests: returns top 50 scores for the requested mode.
 * Example: ?mode=ROGUE or ?mode=CLASSIC
 */
function doGet(e) {
  try {
    initSheetsIfNeeded();
    const mode = (e && e.parameter && e.parameter.mode) ? String(e.parameter.mode).toUpperCase() : "ROGUE";
    const sheetName = (mode === "CLASSIC") ? SPREADSHEET_CLASSIC : SPREADSHEET_ROGUE;
    
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const sheet = ss.getSheetByName(sheetName);
    const data = sheet.getDataRange().getValues();
    
    if (data.length <= 1) {
      return jsonResponse({ status: "success", mode: mode, count: 0, data: [] });
    }
    
    // Skip header row [PilotID, Callsign, Score, Stage, Lines, Date]
    const rows = data.slice(1);
    
    // Sort descending by Score (column index 2)
    rows.sort(function(a, b) {
      return Number(b[2]) - Number(a[2]);
    });
    
    // Map to clean JSON response (top 50)
    const leaderboard = rows.slice(0, 50).map(function(row, index) {
      const callsign = String(row[1]);
      const isCreator = (callsign.toLowerCase() === CREATOR_NAME.toLowerCase());
      return {
        rank: index + 1,
        name: callsign,
        score: Number(row[2]),
        stage: String(row[3]),
        lines: Number(row[4]),
        date: String(row[5]),
        isCreator: isCreator
      };
    });
    
    return jsonResponse({
      status: "success",
      mode: mode,
      count: leaderboard.length,
      data: leaderboard
    });
    
  } catch (err) {
    return jsonResponse({ status: "error", message: err.toString() });
  }
}

/**
 * Handles POST requests: records or updates a player's high score.
 * Enforces unique callsigns (prevents duplicate player names) and reserves hassanm57.
 */
function doPost(e) {
  try {
    initSheetsIfNeeded();
    
    if (!e || !e.postData || !e.postData.contents) {
      return jsonResponse({ status: "error", message: "Missing request body payload." });
    }
    
    const body = JSON.parse(e.postData.contents);
    const pilotId = String(body.pilotId || "").trim();
    let name = String(body.name || "").trim().slice(0, 15);
    const score = Math.floor(Number(body.score || 0));
    const mode = String(body.mode || "ROGUE").toUpperCase();
    const stage = String(body.stage || (mode === "ROGUE" ? "Sector 1" : "Level 1"));
    const lines = Math.floor(Number(body.lines || 0));
    const date = new Date().toISOString().split("T")[0];
    
    // 1. Validation
    if (!name || name.length < 2) {
      return jsonResponse({ status: "error", message: "Callsign must be at least 2 characters." });
    }
    if (score <= 0) {
      return jsonResponse({ status: "error", message: "Score must be greater than zero." });
    }
    
    // 2. Strict protection of Creator Callsign
    if (name.toLowerCase() === CREATOR_NAME.toLowerCase()) {
      const passcode = String(body.passcode || "").trim();
      if (passcode !== "Palaahassan") {
        return jsonResponse({
          status: "error",
          code: "RESERVED_NAME",
          message: "👑 'hassanm57' is the reserved Creator & Matrix Champion identifier. Please choose your own callsign!"
        });
      }
    }
    
    const sheetName = (mode === "CLASSIC") ? SPREADSHEET_CLASSIC : SPREADSHEET_ROGUE;
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const sheet = ss.getSheetByName(sheetName);
    const data = sheet.getDataRange().getValues();
    
    let existingRowIndex = -1;
    let existingScore = 0;
    
    // 3. Unique name check: verify if name is already claimed by another pilotId
    for (let i = 1; i < data.length; i++) {
      const rowPilotId = String(data[i][0]).trim();
      const rowName = String(data[i][1]).trim();
      
      if (rowName.toLowerCase() === name.toLowerCase()) {
        if (rowPilotId && pilotId && rowPilotId !== pilotId) {
          return jsonResponse({
            status: "error",
            code: "NAME_TAKEN",
            message: "⚠️ Callsign '" + name + "' is already claimed by another pilot! Please choose a unique name."
          });
        }
        existingRowIndex = i + 1; // 1-indexed for SpreadsheetApp
        existingScore = Number(data[i][2]);
        break;
      } else if (rowPilotId && pilotId && rowPilotId === pilotId) {
        // Same pilot updating their score or renaming
        existingRowIndex = i + 1;
        existingScore = Number(data[i][2]);
        break;
      }
    }
    
    // 4. Update or Insert
    if (existingRowIndex > 0) {
      // Only overwrite if new score beats personal best record
      if (score > existingScore) {
        sheet.getRange(existingRowIndex, 1, 1, 6).setValues([[pilotId, name, score, stage, lines, date]]);
        return jsonResponse({
          status: "success",
          updated: true,
          message: "🎉 New personal high score recorded on the Global Matrix!"
        });
      } else {
        return jsonResponse({
          status: "success",
          updated: false,
          message: "Score submitted, but previous record was higher (" + existingScore + " pts)."
        });
      }
    } else {
      // Append new pilot record
      sheet.appendRow([pilotId, name, score, stage, lines, date]);
      return jsonResponse({
        status: "success",
        updated: true,
        message: "⚡ New pilot callsign immortalized on the Global Matrix!"
      });
    }
    
  } catch (err) {
    return jsonResponse({ status: "error", message: err.toString() });
  }
}

/**
 * Initializes sheets with seed data and puts hassanm57 at #1 with a formidable score.
 */
function initSheetsIfNeeded() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  
  ensureSheetWithSeed(ss, SPREADSHEET_ROGUE, [
    ["creator_root", "hassanm57", CREATOR_ROGUE_SCORE, "SECTOR 4", 58, "2026-10-02"]
  ]);
  
  ensureSheetWithSeed(ss, SPREADSHEET_CLASSIC, [
    ["creator_root", "hassanm57", CREATOR_CLASSIC_SCORE, "LEVEL 11", 104, "2026-10-02"]
  ]);
}

function ensureSheetWithSeed(ss, sheetName, seedRows) {
  let sheet = ss.getSheetByName(sheetName);
  if (!sheet) {
    sheet = ss.insertSheet(sheetName);
    sheet.appendRow(["PilotID", "Callsign", "Score", "Stage", "Lines", "Date"]);
    
    // Style header row
    const headerRange = sheet.getRange(1, 1, 1, 6);
    headerRange.setBackground("#050814");
    headerRange.setFontColor("#00f0ff");
    headerRange.setFontWeight("bold");
    
    // Append seed rows
    for (let i = 0; i < seedRows.length; i++) {
      sheet.appendRow(seedRows[i]);
    }
  }
}

function jsonResponse(data) {
  return ContentService
    .createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}
