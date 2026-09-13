const API_BASE = "http://127.0.0.1:8000";
const CACHE_KEY_RISK = "bhromonsathi_last_risk";

function setStatus(msg, isError = false) {
  const el = document.getElementById("statusMsg");
  el.textContent = msg;
  el.className = "status-msg" + (isError ? " error" : "");
}

function riskBarWidth(level) {
  if (!level) return 0;
  const map = { Low: 28, Medium: 55, Moderate: 55, High: 88 };
  return map[level] || 40;
}

// checking for offline/online status
window.addEventListener('offline', () => {
  setStatus("You appear to be offline — showing last saved data if available.", true);
});

window.addEventListener('online', () => {
  setStatus("Back online.");
});

async function runAssessment() {
  const zone = document.getElementById("zoneSelect").value.trim();
  const month = document.getElementById("monthSelect").value.trim();

  if (!zone || !month) {
    setStatus("Please enter both Zone and Month.", true);
    return;
  }

  setStatus("Loading risk data...");

  try {
    const url = `${API_BASE}/risk-assessment?zone=${encodeURIComponent(zone)}&month=${encodeURIComponent(month)}`;
    const res = await fetch(url);

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }

    const data = await res.json();
    const cachePayload = {
      zone: data.zone,
      month: data.month,
      combined_risk: data.combined_risk,
      avg_rainfall: data.avg_rainfall,
      avg_wind_speed: data.avg_wind_speed,
      timestamp: new Date().toISOString(),
      savedAt: new Date().toLocaleString(),
      data: data
    };


    localStorage.setItem(CACHE_KEY_RISK, JSON.stringify(cachePayload));
    renderRisk(data);
    setStatus(data.notice || `Loaded data for ${data.zone} · ${data.month}`);

    document.getElementById("chatZoneLabel").textContent = `Zone: ${data.zone}`;
    await loadPrecautions(data.zone);
  } catch (err) {
    console.warn("Live risk assessment failed, trying to load cached data...", err);
    // Try to load cached data
    const cachedRaw = localStorage.getItem(CACHE_KEY_RISK);
    if (cachedRaw) {
      try {
        const cachedData = JSON.parse(cachedRaw);
        renderRisk(cachedData.data);
        setStatus(cachedData.data.notice || `Loaded cached data for ${cachedData.zone} · ${cachedData.month} (Last saved: ${cachedData.savedAt})`, true);
        document.getElementById("chatZoneLabel").textContent = `Zone: ${cachedData.zone}`;
        await loadPrecautions(cachedData.zone);
        return;
      }catch (parseErr) {
        console.error("Failed to load cached data:", parseErr);
      }
    }
  // If no cache was ever saved
  setStatus("Could not load risk data. Please check your internet connection and try again.", true);
  }
}

function renderRisk(data) {
  document.getElementById("heroRiskZone").textContent =
    `${data.zone} · ${data.combined_risk || "—"}`;
  document.getElementById("heroRiskBar").style.width =
    riskBarWidth(data.combined_risk) + "%";
  document.getElementById("heroWeather").textContent =
    `Rain ${data.avg_rainfall ?? "—"} mm · Wind ${data.avg_wind_speed ?? "—"} km/h`;
  document.getElementById("heroCombined").textContent =
    data.combined_risk || "—";

  document.getElementById("dashCombined").textContent = data.combined_risk || "—";
  document.getElementById("dashDetail").textContent = `${data.zone} · ${data.month}`;
  document.getElementById("tagRain").textContent = `Rainfall: ${data.rainfall_risk || "—"}`;
  document.getElementById("tagWind").textContent = `Wind: ${data.wind_risk || "—"}`;

  document.getElementById("dashRainfall").textContent =
    data.avg_rainfall != null ? data.avg_rainfall + " mm" : "—";
  document.getElementById("dashWind").textContent =
    `Avg wind ${data.avg_wind_speed ?? "—"} · ${data.month}`;
  document.getElementById("tagYears").textContent =
    `Years of data: ${data.years_of_data ?? "—"}`;

  document.getElementById("dashZone").textContent = data.zone || "—";
  document.getElementById("dashMonth").textContent = data.month || "—";
  document.getElementById("tagNotice").textContent =
    data.match_type ? data.match_type : "Exact match";
}

async function loadPrecautions(zone) {
  const list = document.getElementById("precautionsList");
  list.innerHTML = `<p class="placeholder">Loading precautions...</p>`;

  try {
    const url = `${API_BASE}/precautions?zone=${encodeURIComponent(zone)}`;
    const res = await fetch(url);

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }

    const items = await res.json();

    if (!items.length) {
      list.innerHTML = `<p class="placeholder">No precautions found for this zone.</p>`;
      return;
    }

    list.innerHTML = items
      .map(
        (p) => `
      <div class="precaution-item">
        <span class="phase">${escapeHtml(p.phase || "General")}</span>
        <div>
          <div class="desc">${escapeHtml(p.description || "")}</div>
          <div class="cat">${escapeHtml(p.category || "")} · ${escapeHtml(p.scope_type || "")}</div>
        </div>
      </div>`
      )
      .join("");
  } catch (err) {
    console.error(err);
    list.innerHTML = `<p class="placeholder">Could not load precautions: ${escapeHtml(err.message)}</p>`;
  }
}

async function loadEmergency() {
  const list = document.getElementById("emergencyList");
  list.innerHTML = `<p class="placeholder">Loading emergency centers...</p>`;
  setStatus("Loading emergency centers...");

  try {
    const res = await fetch(`${API_BASE}/emergency-centers`);

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }

    const items = await res.json();

    if (!items.length) {
      list.innerHTML = `<p class="placeholder">No emergency centers found.</p>`;
      setStatus("No emergency data returned.");
      return;
    }

    list.innerHTML = items
      .map(
        (c) => `
      <div class="emergency-item">
        <div>
          <h4>${escapeHtml(c.center_name || "Unknown")}</h4>
          <div class="type">${escapeHtml(c.center_type || "")}</div>
        </div>
        <span class="near">${escapeHtml(c.nearest_location_name || "—")}</span>
      </div>`
      )
      .join("");

    setStatus(`Loaded ${items.length} emergency centers.`);
    document.getElementById("emergency").scrollIntoView({ behavior: "smooth" });
  } catch (err) {
    console.error(err);
    list.innerHTML = `<p class="placeholder">Error: ${escapeHtml(err.message)}</p>`;
    setStatus("Error loading emergency data: " + err.message, true);
  }
}

function escapeHtml(str) {
  if (str == null) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

document.querySelectorAll(".nav-link").forEach((link) => {
  link.addEventListener("click", () => {
    document.querySelectorAll(".nav-link").forEach((l) => l.classList.remove("active"));
    link.classList.add("active");
  });
});

document.addEventListener("DOMContentLoaded", () => {
  loadEmergency();
});

let chatHistory = [];

function getCurrentZone() {
  const zoneInput = document.getElementById("zoneSelect");
  return zoneInput && zoneInput.value.trim() ? zoneInput.value.trim() : null;
}

function appendChatMessage(text, sender) {
  const messagesEl = document.getElementById("chatMessages");
  const msgEl = document.createElement("div");
  msgEl.className = `chat-msg ${sender}`;
  msgEl.textContent = text;
  messagesEl.appendChild(msgEl);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return msgEl;
}

async function sendChatMessage() {
  const input = document.getElementById("chatInput");
  const query = input.value.trim();
  if (!query) return;

  const zone = getCurrentZone();
  document.getElementById("chatZoneLabel").textContent = zone
    ? `Zone: ${zone}`
    : "Zone: not selected";

  if (!zone) {
    appendChatMessage("Please enter a zone above first.", "bot");
    return;
  }

  appendChatMessage(query, "user");
  input.value = "";
  const loadingEl = appendChatMessage("Thinking...", "bot loading");

  try {
    const res = await fetch(`${API_BASE}/hazards`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ zone, query, history: chatHistory }),
    });
    const data = await res.json();
    loadingEl.remove();

    if (!res.ok) {
      appendChatMessage(data.detail || "Something went wrong.", "bot");
      return;
    }

    appendChatMessage(data.answer, "bot");
    chatHistory = data.history.map((h) => ({ role: h.role, content: h.content }));
  } catch (err) {
    loadingEl.remove();
    appendChatMessage("Could not reach the backend. Is the server running?", "bot");
  }
}


    // 4) build PDF
    // ===== OFFLINE KIT GENERATION (PDF) =====
async function downloadOfflineKit() {
  const zone = document.getElementById("zoneSelect").value.trim();
  const month = document.getElementById("monthSelect").value.trim();

  if (!zone) {
    setStatus("Please enter a zone first.", true);
    return;
  }

  setStatus("Building your offline kit...");

  try {
    const [riskRes, precRes, emgRes] = await Promise.all([
      month ? fetch(`${API_BASE}/risk-assessment?zone=${encodeURIComponent(zone)}&month=${encodeURIComponent(month)}`) : Promise.resolve(null),
      fetch(`${API_BASE}/precautions?zone=${encodeURIComponent(zone)}`),
      fetch(`${API_BASE}/emergency-centers`),
    ]);

    const risk = riskRes && riskRes.ok ? await riskRes.json() : null;
    const precautions = precRes.ok ? await precRes.json() : [];
    const emergencies = emgRes.ok ? await emgRes.json() : [];

    const resolvedZone = risk ? risk.zone : zone;

    // Build the content into a hidden container in the actual page
    const container = document.createElement("div");
    container.id = "pdfKitContent";
    container.innerHTML = buildOfflineKitInnerHtml(resolvedZone, month, risk, precautions, emergencies);
    document.body.appendChild(container);

    setStatus("Generating PDF...");

    await html2pdf()
      .set({
        margin: 0.4,
        filename: `${resolvedZone.toLowerCase().replace(/\s+/g, "-")}-safety-kit.pdf`,
        html2canvas: { scale: 2 },
        jsPDF: { unit: "in", format: "a4", orientation: "portrait" },
      })
      .from(container)
      .save();

    document.body.removeChild(container);
    setStatus(`Offline kit PDF downloaded for ${resolvedZone}.`);
  } catch (err) {
    console.error(err);
    setStatus("Could not build offline kit: " + err.message, true);
  }
}

function buildOfflineKitInnerHtml(zone, month, risk, precautions, emergencies) {
  const precautionRows = precautions.map(p => `
    <div style="border-left:3px solid #2dd4a0; background:#f3f6f2; border-radius:6px; padding:8px 12px; margin-bottom:8px;">
      <span style="font-size:10px; text-transform:uppercase; color:#1a6b45; font-weight:600;">${escapeHtml(p.phase)}</span>
      <div><strong>${escapeHtml(p.category)}</strong></div>
      <p style="font-size:13px; margin:2px 0 0;">${escapeHtml(p.description)}</p>
    </div>`).join("");

  const emergencyRows = emergencies.map(e => `
    <div style="border-left:3px solid #3b82f6; background:#f3f6f2; border-radius:6px; padding:8px 12px; margin-bottom:8px;">
      <strong>${escapeHtml(e.center_name)}</strong>
      <p style="font-size:13px; margin:2px 0 0;">${escapeHtml(e.center_type)}${e.nearest_location_name ? " · " + escapeHtml(e.nearest_location_name) : ""}</p>
    </div>`).join("");

  const riskBlock = risk ? `
    <div style="background:#e6f7f0; border-radius:8px; padding:14px; margin-bottom:10px;">
      <h3 style="margin:0 0 6px;">${escapeHtml(risk.zone)} — ${escapeHtml(risk.month)}</h3>
      <p style="margin:2px 0;"><strong>Combined Risk:</strong> ${escapeHtml(risk.combined_risk)}</p>
      <p style="margin:2px 0;">Rainfall: ${escapeHtml(String(risk.avg_rainfall))} mm/day (${escapeHtml(risk.rainfall_risk)})</p>
      <p style="margin:2px 0;">Wind: ${escapeHtml(String(risk.avg_wind_speed))} km/h (${escapeHtml(risk.wind_risk)})</p>
      <p style="font-size:11px; color:#666; margin:6px 0 0;">Based on ${escapeHtml(String(risk.years_of_data))} years of historical data.</p>
    </div>` : `<p style="color:#666;">No month-specific risk data selected.</p>`;

  return `
    <div style="font-family: Arial, sans-serif; color:#111; max-width:650px;">
      <h1 style="color:#1a6b45; font-size:22px; margin-bottom:4px;">🛡️ ${escapeHtml(zone)} — Offline Safety Kit</h1>
      <p style="font-size:11px; color:#666;">Generated ${new Date().toLocaleString()}</p>

      <h2 style="font-size:15px; color:#1a6b45; border-bottom:1px solid #ccc; padding-bottom:4px; margin-top:18px;">Risk Summary</h2>
      ${riskBlock}

      <h2 style="font-size:15px; color:#1a6b45; border-bottom:1px solid #ccc; padding-bottom:4px; margin-top:18px;">Safety Precautions</h2>
      ${precautionRows || '<p style="color:#666;">No precautions loaded.</p>'}

      <h2 style="font-size:15px; color:#1a6b45; border-bottom:1px solid #ccc; padding-bottom:4px; margin-top:18px;">Emergency Centers</h2>
      ${emergencyRows || '<p style="color:#666;">No emergency centers loaded.</p>'}

      <div style="background:#ef4444; color:white; padding:12px; border-radius:8px; text-align:center; font-weight:700; font-size:18px; margin-top:16px;">
        Police: 100 &nbsp;|&nbsp; Ambulance: 108
      </div>

      <p style="font-size:10px; color:#999; text-align:center; margin-top:18px;">Sundarban Sentinel · Offline kit · Not an official emergency service</p>
    </div>`;
}

// Add a last cached risk assesment with a clear timestamp to the local storage for offline use
