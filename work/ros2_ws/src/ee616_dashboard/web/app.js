const $ = (id) => document.getElementById(id);
let profiles = {};
let mapProfiles = {};
let scenarioProfiles = {};
let latest = null;
let lastHistoryAt = 0;
const history = {1: [], 2: [], 3: []};

const routes = {
  wide: [[-10,-6],[10,-6],[10,-1],[-10,-1]],
  standard: [[-10,-6],[7,-6],[10.5,-2.5],[7,-1],[-10,-1]],
  turn_dense: [[-10,-6],[10,-6],[10,-1],[-10,-1],[-10,4.75],[10,4.75],[10,10],[-10,10],[-10,-1]],
};

function cssColor(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

function palette() {
  return {
    accent: cssColor("--accent"), blue: cssColor("--blue"), yellow: cssColor("--yellow"),
    line: cssColor("--line"), lineSoft: cssColor("--line-soft"), muted: cssColor("--muted"), text: cssColor("--text"),
  };
}

function fmt(value, digits=2, suffix="") {
  return Number.isFinite(value) ? `${value.toFixed(digits)}${suffix}` : "—";
}

async function api(path, options={}) {
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || `Request failed: ${response.status}`);
  return data;
}

function selectedProfile() {
  return $("route-profile").value || "wide";
}

function populateSelect(id, values, defaultKey) {
  const select = $(id);
  Object.entries(values).forEach(([key, value]) => {
    const option = document.createElement("option");
    option.value = key;
    option.textContent = value.label;
    if (key === defaultKey) option.selected = true;
    select.append(option);
  });
}

function describeProfile() {
  const profile = profiles[selectedProfile()];
  if (!profile) return;
  const mapProfile = mapProfiles[$("map-profile").value];
  const scenario = scenarioProfiles[$("scenario-profile").value];
  const notes = [profile.description, mapProfile?.description, scenario?.description, profile.evidence_status, mapProfile?.evidence_status]
    .filter(Boolean).join(" ");
  $("profile-description").textContent = `${notes} Maximum evaluation time: ${Math.round(profile.duration_s)} s.`;
  $("map-label").textContent = `${mapProfile?.label || "Warehouse"} / ${profile.label}`;
  drawMap(selectedProfile(), latest?.planner?.waypoint_index || 0);
}

async function loadProfiles() {
  const data = await api("/api/profiles");
  profiles = data.routes;
  mapProfiles = data.maps;
  scenarioProfiles = data.scenarios;
  Object.entries(profiles).forEach(([key, value]) => {
    const option = document.createElement("option");
    option.value = key;
    option.textContent = `${value.label} / ${value.waypoint_count} goals`;
    if (key === "wide") option.selected = true;
    $("route-profile").append(option);
  });
  populateSelect("map-profile", mapProfiles, "sparse");
  populateSelect("scenario-profile", scenarioProfiles, "nominal");
  describeProfile();
}

async function startRun() {
  $("message").textContent = "Starting bounded ROS 2 launch…";
  try {
    await api("/api/start", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        follower_count: Number($("follower-count").value),
        route_profile: selectedProfile(),
        map_profile: $("map-profile").value,
        scenario_profile: $("scenario-profile").value,
        gui: $("show-gazebo").checked,
      }),
    });
    Object.values(history).forEach(values => values.length = 0);
    $("result-panel").hidden = true;
    $("message").textContent = "Experiment started. Gazebo and Nav2 may take several seconds to initialize.";
  } catch (error) {
    $("message").textContent = error.message;
  }
}

async function stopRun() {
  $("message").textContent = "Requesting controlled shutdown…";
  try {
    await api("/api/stop", {method: "POST", body: "{}"});
    $("message").textContent = "Run stopped. Partial logs remain in the displayed result directory.";
  } catch (error) {
    $("message").textContent = error.message;
  }
}

function updateHistory(data) {
  const now = Date.now();
  if (!data.process.running || now - lastHistoryAt < 500) return;
  lastHistoryAt = now;
  [1,2,3].forEach(index => {
    const follower = data.followers[String(index)];
    if (follower.active && Number.isFinite(follower.estimated_spacing_error_m)) {
      history[index].push({t: now, y: follower.estimated_spacing_error_m});
      if (history[index].length > 240) history[index].shift();
    }
  });
}

function componentText(components, metric, digits, suffix) {
  const leader = components?.leader_navigation?.[metric];
  const followers = components?.follower_perception_control?.[metric];
  const simulation = components?.simulation_evaluation?.[metric];
  if (![leader, followers, simulation].some(Number.isFinite)) return "—";
  return `Leader ${fmt(leader, digits, suffix)} / Followers ${fmt(followers, digits, suffix)} / Sim ${fmt(simulation, digits, suffix)}`;
}

function totalCollisionSamples(postRun) {
  const obstacle = Object.values(postRun?.warehouse_obstacle_collision_samples || {});
  const followers = Object.values(postRun?.followers || {}).map(value => value?.collision_samples || 0);
  return [...obstacle, ...followers].reduce((sum, value) => sum + (Number(value) || 0), 0);
}

function updatePostRun(postRun) {
  const panel = $("result-panel");
  if (!postRun) {
    panel.hidden = true;
    return;
  }
  panel.hidden = false;
  const outcome = String(postRun.outcome || "UNKNOWN").toUpperCase();
  panel.className = `panel result-panel ${outcome.toLowerCase()}`;
  $("result-mark").textContent = outcome;
  const titles = {
    PASS: "Mission completed within the defined checks",
    LIMITED: "Route completed, but one or more acceptance checks failed",
    CONTAINED: "Mission stopped, but the safety governor contained motion",
    FAILED: "Mission did not satisfy the defined checks",
  };
  $("result-title").textContent = titles[outcome] || `Recorded outcome: ${outcome}`;
  $("result-explanation").textContent = postRun.failure_explanation || postRun.failure || "Evaluator summary loaded from the result directory.";
  $("result-route").textContent = postRun.route_complete ? "YES" : "NO";
  $("result-collisions").textContent = String(totalCollisionSamples(postRun));
  $("result-rtf").textContent = fmt(postRun.real_time_factor, 2);
  $("result-governor").textContent = postRun.governor_final_state?.mode || "—";
}

function updateOverview(data) {
  const running = data.process.running;
  const postRun = data.post_run;
  const outcome = postRun?.outcome?.toLowerCase();
  const badge = $("run-badge");
  const exitFailed = data.process.last_exit_code !== null && data.process.last_exit_code !== 0;
  badge.className = `badge ${running ? "running" : outcome === "contained" ? "contained" : exitFailed ? "failed" : "idle"}`;
  badge.querySelector("strong").textContent = running ? "RUNNING" : postRun?.outcome || (exitFailed ? "EXITED WITH ERROR" : "IDLE");
  ["follower-count", "route-profile", "map-profile", "scenario-profile", "show-gazebo"].forEach(id => { $(id).disabled = running; });
  $("start").disabled = running;
  $("stop").disabled = !running;

  $("mission-state").textContent = data.mission_state;
  const planner = data.planner || {};
  $("route-progress").textContent = planner.waypoint_count
    ? `Goal ${Math.min(planner.waypoint_index + 1, planner.waypoint_count)} of ${planner.waypoint_count} / ${planner.route_profile}`
    : "Waiting for route planner";
  $("planner-name").textContent = planner.algorithm || "—";
  $("controller-name").textContent = planner.controller || "Waiting for Nav2";
  const governor = data.governor || {};
  $("governor-mode").textContent = governor.mode || "—";
  $("governor-reason").textContent = governor.reason || "Waiting for follower health";

  const resources = data.resources || {};
  const peaks = resources.peaks || {};
  $("memory").textContent = fmt(resources.container_memory_mib, 0, " MiB");
  $("memory-peak").textContent = Number.isFinite(peaks.container_memory_mib) ? `Run peak ${fmt(peaks.container_memory_mib, 0, " MiB")}` : "Run peak unavailable";
  $("load-average").textContent = Number.isFinite(resources.load_average_1m) ? `Host 1-minute load ${resources.load_average_1m}` : "System load unavailable";
  $("gpu-name").textContent = resources.gpu_name || "GPU unavailable";
  $("gpu-memory").textContent = Number.isFinite(resources.gpu_memory_used_mib) ? `${fmt(resources.gpu_memory_used_mib, 0)} / ${fmt(resources.gpu_memory_total_mib, 0)} MiB` : "—";
  $("gpu-utilization").textContent = Number.isFinite(resources.gpu_utilization_percent) ? `${fmt(resources.gpu_utilization_percent, 0, "%")} utilization / current` : "GPU telemetry unavailable";
  $("gpu-peak").textContent = Number.isFinite(peaks.gpu_utilization_percent) ? `Run peak ${fmt(peaks.gpu_utilization_percent, 0, "%")} / ${fmt(peaks.gpu_memory_used_mib, 0, " MiB")}` : "Run peak unavailable";
  $("gpu-diagnostic").textContent = resources.gpu_status === "available" ? `Source ${resources.gpu_provider}` : (resources.gpu_diagnostic || "GPU telemetry unavailable");

  const components = resources.components || {};
  const componentPeaks = peaks.components || {};
  $("component-memory").textContent = resources.mission_processes_active ? componentText(components, "memory_mib", 0, " MiB") : "Mission processes stopped";
  $("component-cpu").textContent = resources.mission_processes_active ? `CPU / ${componentText(components, "cpu_percent", 1, "%")}` : "No live per-process values are claimed while idle";
  $("component-peak").textContent = Object.keys(componentPeaks).length ? `Peak memory / ${componentText(componentPeaks, "memory_mib", 0, " MiB")}` : "Run peak unavailable";

  $("metric-boundary").textContent = data.metric_boundary;
  const profile = data.process.config?.route_profile || selectedProfile();
  const mapProfile = data.process.config?.map_profile || $("map-profile").value;
  $("map-label").textContent = `${mapProfiles[mapProfile]?.label || mapProfile} / ${profiles[profile]?.label || profile}`;
  $("output-dir").textContent = data.process.output_dir ? `RESULT PATH / ${data.process.output_dir}` : "";
  if (running && planner.failure) $("message").textContent = `Planner record / ${planner.failure}`;
  updatePostRun(postRun);
  drawMap(profile, planner.waypoint_index || 0);
}

function updateFollowers(data) {
  const body = $("follower-rows");
  body.replaceChildren();
  [1,2,3].forEach(index => {
    const f = data.followers[String(index)];
    const row = document.createElement("tr");
    if (!f.active) row.className = "inactive";
    const stateClass = String(f.state).toLowerCase().replaceAll("_", "-");
    const values = [
      `Follower ${index}`,
      f.active ? f.state : "DISABLED",
      fmt(f.estimated_range_m, 3, " m"),
      fmt(f.estimated_bearing_deg, 2, "°"),
      fmt(f.estimated_spacing_error_m, 3, " m"),
      fmt(f.estimated_rmse_m, 3, " m"),
      fmt(f.measurement_age_s, 3, " s"),
      `${fmt(f.linear_cmd_mps, 2)} / ${fmt(f.angular_cmd_rps, 2)}`,
      `${fmt(f.inference_ms, 1, " ms")} / ${fmt(f.detection_confidence, 2)}`,
    ];
    values.forEach((value, cellIndex) => {
      const cell = document.createElement("td");
      if (cellIndex === 1) {
        const chip = document.createElement("span");
        chip.className = `state ${stateClass}`;
        chip.textContent = value;
        cell.append(chip);
      } else {
        cell.textContent = value;
      }
      row.append(cell);
    });
    body.append(row);
  });
}

function canvasSetup(canvas) {
  const ratio = window.devicePixelRatio || 1;
  const width = canvas.clientWidth;
  const height = width * 420 / 760;
  if (canvas.width !== Math.round(width * ratio)) {
    canvas.width = Math.round(width * ratio);
    canvas.height = Math.round(height * ratio);
  }
  const ctx = canvas.getContext("2d");
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  return {ctx, width, height};
}

function drawMap(profile, waypointIndex) {
  const {ctx, width, height} = canvasSetup($("map-canvas"));
  const c = palette();
  ctx.clearRect(0,0,width,height);
  const px = x => 32 + (x + 19) / 38 * (width - 64);
  const py = y => height - 28 - (y + 12) / 24 * (height - 56);
  ctx.strokeStyle = c.lineSoft; ctx.lineWidth = 1;
  [-6,-1,4.75,10].forEach(y => { ctx.beginPath(); ctx.moveTo(px(-18),py(y)); ctx.lineTo(px(18),py(y)); ctx.stroke(); });
  ctx.fillStyle = c.line;
  const mapProfile = latest?.process?.config?.map_profile || $("map-profile").value || "standard";
  const shelfX = mapProfile === "sparse" ? [-4.5,4.5] : [-3,0,3];
  [-3.5,2,7.5].forEach(y => shelfX.forEach(x => ctx.fillRect(px(x-1.98),py(y+0.48),px(x+1.98)-px(x-1.98),py(y-0.48)-py(y+0.48))));
  ctx.fillStyle = c.blue; ctx.fillRect(px(-11),py(-5.55),px(-9)-px(-11),py(-6.45)-py(-5.55));
  ctx.fillStyle = c.accent; ctx.fillRect(px(-11),py(-.55),px(-9)-px(-11),py(-1.45)-py(-.55));
  const points = routes[profile] || routes.standard;
  ctx.strokeStyle = c.accent; ctx.lineWidth = 2; ctx.setLineDash([8,6]); ctx.beginPath();
  points.forEach(([x,y], i) => i ? ctx.lineTo(px(x),py(y)) : ctx.moveTo(px(x),py(y)));
  ctx.stroke(); ctx.setLineDash([]);
  points.slice(1).forEach(([x,y], index) => {
    ctx.beginPath(); ctx.fillStyle = index === waypointIndex ? c.yellow : c.blue; ctx.arc(px(x),py(y),index === waypointIndex ? 6 : 4,0,Math.PI*2); ctx.fill();
  });
  ctx.fillStyle = c.muted; ctx.font = "11px monospace";
  ctx.fillText("RECEIVING", px(-11), py(-6) - 10); ctx.fillText("DISPATCH", px(-11), py(-1) - 10);
}

function drawChart() {
  const {ctx, width, height} = canvasSetup($("error-canvas"));
  const c = palette();
  const colors = [c.accent, c.blue, c.yellow];
  ctx.clearRect(0,0,width,height);
  const left=48, right=18, top=25, bottom=36;
  const yMax=.45;
  const py = y => top + (yMax-y)/(2*yMax)*(height-top-bottom);
  ctx.strokeStyle=c.lineSoft; ctx.lineWidth=1;
  [-.4,-.2,0,.2,.4].forEach(y => {ctx.beginPath();ctx.moveTo(left,py(y));ctx.lineTo(width-right,py(y));ctx.stroke();ctx.fillStyle=c.muted;ctx.font="10px monospace";ctx.fillText(`${y.toFixed(1)} m`,5,py(y)+4);});
  ctx.strokeStyle=c.line;ctx.beginPath();ctx.moveTo(left,py(0));ctx.lineTo(width-right,py(0));ctx.stroke();
  const timestamps = Object.values(history).flat().map(point => point.t);
  const minT = timestamps.length ? Math.min(...timestamps) : Date.now()-120000;
  const maxT = timestamps.length ? Math.max(...timestamps) : Date.now();
  [1,2,3].forEach(index => {
    const values=history[index]; if (!values.length) return;
    ctx.strokeStyle=colors[index-1];ctx.lineWidth=2;ctx.beginPath();
    values.forEach((point,i)=>{const x=left+(point.t-minT)/Math.max(1000,maxT-minT)*(width-left-right);const y=Math.max(-yMax,Math.min(yMax,point.y));i?ctx.lineTo(x,py(y)):ctx.moveTo(x,py(y));});ctx.stroke();
    ctx.fillStyle=colors[index-1];ctx.fillRect(left+(index-1)*110,7,10,3);ctx.fillStyle=c.muted;ctx.font="10px monospace";ctx.fillText(`FOLLOWER ${index}`,left+15+(index-1)*110,12);
  });
}

async function poll() {
  try {
    latest = await api("/api/telemetry");
    updateHistory(latest); updateOverview(latest); updateFollowers(latest); drawChart();
  } catch (error) {
    $("message").textContent = `Telemetry unavailable / ${error.message}`;
  }
}

function exportSnapshot() {
  if (!latest) return;
  const blob = new Blob([JSON.stringify(latest,null,2)], {type:"application/json"});
  const link = document.createElement("a");
  link.href=URL.createObjectURL(blob);
  link.download=`ee616-telemetry-${new Date().toISOString().replaceAll(":","-")}.json`;
  link.click();
  URL.revokeObjectURL(link.href);
}

function toggleTheme() {
  const root = document.documentElement;
  const paper = root.dataset.theme !== "paper";
  root.dataset.theme = paper ? "paper" : "nocturne";
  $("theme-toggle").textContent = paper ? "NOCTURNE MODE" : "PAPER MODE";
  localStorage.setItem("ee616-theme", root.dataset.theme);
  describeProfile(); drawChart();
}

const savedTheme = localStorage.getItem("ee616-theme");
if (savedTheme === "paper") {
  document.documentElement.dataset.theme = "paper";
  $("theme-toggle").textContent = "NOCTURNE MODE";
}
$("theme-toggle").addEventListener("click", toggleTheme);
$("start").addEventListener("click", startRun);
$("stop").addEventListener("click", stopRun);
$("export").addEventListener("click", exportSnapshot);
$("route-profile").addEventListener("change", describeProfile);
$("map-profile").addEventListener("change", describeProfile);
$("scenario-profile").addEventListener("change", describeProfile);
window.addEventListener("resize", () => {describeProfile(); drawChart();});
loadProfiles().then(poll);
setInterval(poll, 500);
