const $ = (id) => document.getElementById(id);
const colors = ["#65e4a3", "#64b9ff", "#ffc857"];
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
  $("profile-description").textContent = `${profile.description} ${mapProfile?.description || ""} ${scenario?.description || ""} ${profile.evidence_status} ${mapProfile?.evidence_status || ""} Maximum evaluation time: ${Math.round(profile.duration_s)} s.`;
  $("map-label").textContent = `${mapProfile?.label || "Warehouse"} · ${profile.label}`;
  drawMap(selectedProfile(), latest?.planner?.waypoint_index || 0);
}

async function loadProfiles() {
  const data = await api("/api/profiles");
  profiles = data.routes;
  mapProfiles = data.maps;
  scenarioProfiles = data.scenarios;
  const select = $("route-profile");
  Object.entries(profiles).forEach(([key, value]) => {
    const option = document.createElement("option");
    option.value = key;
    option.textContent = `${value.label} · ${value.waypoint_count} goals`;
    if (key === "wide") option.selected = true;
    select.append(option);
  });
  populateSelect("map-profile", mapProfiles, "sparse");
  populateSelect("scenario-profile", scenarioProfiles, "nominal");
  describeProfile();
}

async function startRun() {
  $("message").textContent = "Starting validated ROS 2 launch…";
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
    $("message").textContent = "Experiment started. Gazebo and Nav2 may take several seconds to initialize.";
  } catch (error) {
    $("message").textContent = error.message;
  }
}

async function stopRun() {
  $("message").textContent = "Requesting a controlled shutdown…";
  try {
    await api("/api/stop", {method: "POST", body: "{}"});
    $("message").textContent = "Run stopped. Partial logs remain in the displayed output directory.";
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

function updateOverview(data) {
  const running = data.process.running;
  const badge = $("run-badge");
  badge.className = `badge ${running ? "running" : data.process.last_exit_code ? "failed" : "idle"}`;
  badge.querySelector("strong").textContent = running ? "RUNNING" : data.process.last_exit_code ? "EXITED WITH ERROR" : "IDLE";
  $("start").disabled = running;
  $("stop").disabled = !running;
  $("follower-count").disabled = running;
  $("route-profile").disabled = running;
  $("map-profile").disabled = running;
  $("scenario-profile").disabled = running;
  $("show-gazebo").disabled = running;

  $("mission-state").textContent = data.mission_state;
  const planner = data.planner || {};
  $("route-progress").textContent = planner.waypoint_count
    ? `Goal ${Math.min(planner.waypoint_index + 1, planner.waypoint_count)} of ${planner.waypoint_count} · ${planner.route_profile}`
    : "Waiting for route planner";
  $("planner-name").textContent = planner.algorithm || "—";
  $("controller-name").textContent = planner.controller || "Waiting for Nav2";
  const governor = data.governor || {};
  $("governor-mode").textContent = governor.mode || "—";
  $("governor-reason").textContent = governor.reason || "Waiting for follower health";
  const resources = data.resources || {};
  $("memory").textContent = fmt(resources.container_memory_mib, 0, " MiB");
  $("load-average").textContent = Number.isFinite(resources.load_average_1m) ? `1-minute system load: ${resources.load_average_1m}` : "System load unavailable";
  $("gpu-memory").textContent = Number.isFinite(resources.gpu_memory_used_mib) ? `${resources.gpu_memory_used_mib.toFixed(0)} / ${resources.gpu_memory_total_mib.toFixed(0)} MiB` : "—";
  $("gpu-utilization").textContent = Number.isFinite(resources.gpu_utilization_percent) ? `GPU utilization: ${resources.gpu_utilization_percent.toFixed(0)}%` : "GPU telemetry unavailable";
  const leaderResources = resources.components?.leader_navigation;
  const followerResources = resources.components?.follower_perception_control;
  $("component-memory").textContent = leaderResources && followerResources
    ? `Leader ${fmt(leaderResources.memory_mib, 0, " MiB")} · Followers ${fmt(followerResources.memory_mib, 0, " MiB")}`
    : "—";
  $("component-cpu").textContent = leaderResources && followerResources
    ? `CPU: leader ${fmt(leaderResources.cpu_percent, 1, "%")} · followers ${fmt(followerResources.cpu_percent, 1, "%")}`
    : "Waiting for process attribution";
  $("metric-boundary").textContent = data.metric_boundary;
  const profile = data.process.config?.route_profile || selectedProfile();
  const mapProfile = data.process.config?.map_profile || $("map-profile").value;
  const mapLabel = mapProfiles[mapProfile]?.label || mapProfile;
  $("map-label").textContent = `${mapLabel} · ${profiles[profile]?.label || profile}`;
  $("output-dir").textContent = data.process.output_dir ? `Result directory: ${data.process.output_dir}` : "";
  if (data.planner?.failure) $("message").textContent = `Experiment failure: ${data.planner.failure}`;
  drawMap(profile, planner.waypoint_index || 0);
}

function updateFollowers(data) {
  const body = $("follower-rows");
  body.replaceChildren();
  [1,2,3].forEach(index => {
    const f = data.followers[String(index)];
    const row = document.createElement("tr");
    if (!f.active) row.className = "inactive";
    const stateClass = String(f.state).toLowerCase().replace("_", "-");
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
  ctx.clearRect(0,0,width,height);
  const px = x => 32 + (x + 19) / 38 * (width - 64);
  const py = y => height - 28 - (y + 12) / 24 * (height - 56);
  ctx.strokeStyle = "#2a4138"; ctx.lineWidth = 1;
  [-6,-1,4.75,10].forEach(y => { ctx.beginPath(); ctx.moveTo(px(-18),py(y)); ctx.lineTo(px(18),py(y)); ctx.stroke(); });
  ctx.fillStyle = "#293a34";
  const mapProfile = latest?.process?.config?.map_profile || $("map-profile").value || "standard";
  const shelfX = mapProfile === "sparse" ? [-4.5,4.5] : [-3,0,3];
  [-3.5,2,7.5].forEach(y => shelfX.forEach(x => ctx.fillRect(px(x-1.98),py(y+0.48),px(x+1.98)-px(x-1.98),py(y-0.48)-py(y+0.48))));
  ctx.fillStyle = "#248acb"; ctx.fillRect(px(-11),py(-5.55),px(-9)-px(-11),py(-6.45)-py(-5.55));
  ctx.fillStyle = "#34a85f"; ctx.fillRect(px(-11),py(-.55),px(-9)-px(-11),py(-1.45)-py(-.55));
  const points = routes[profile] || routes.standard;
  ctx.strokeStyle = "#65e4a3"; ctx.lineWidth = 3; ctx.setLineDash([8,6]); ctx.beginPath();
  points.forEach(([x,y], i) => i ? ctx.lineTo(px(x),py(y)) : ctx.moveTo(px(x),py(y)));
  ctx.stroke(); ctx.setLineDash([]);
  points.slice(1).forEach(([x,y], index) => {
    ctx.beginPath(); ctx.fillStyle = index === waypointIndex ? "#ffc857" : "#64b9ff"; ctx.arc(px(x),py(y),index === waypointIndex ? 6 : 4,0,Math.PI*2); ctx.fill();
  });
  ctx.fillStyle = "#b5c9c0"; ctx.font = "12px system-ui";
  ctx.fillText("Receiving", px(-11), py(-6) - 10); ctx.fillText("Dispatch", px(-11), py(-1) - 10);
}

function drawChart() {
  const {ctx, width, height} = canvasSetup($("error-canvas"));
  ctx.clearRect(0,0,width,height);
  const left=48, right=18, top=25, bottom=36;
  const yMax=.45;
  const py = y => top + (yMax-y)/(2*yMax)*(height-top-bottom);
  ctx.strokeStyle="#23372f"; ctx.lineWidth=1;
  [-.4,-.2,0,.2,.4].forEach(y => {ctx.beginPath();ctx.moveTo(left,py(y));ctx.lineTo(width-right,py(y));ctx.stroke();ctx.fillStyle="#8ba197";ctx.font="11px system-ui";ctx.fillText(`${y.toFixed(1)} m`,5,py(y)+4);});
  ctx.strokeStyle="#678377";ctx.beginPath();ctx.moveTo(left,py(0));ctx.lineTo(width-right,py(0));ctx.stroke();
  const timestamps = Object.values(history).flat().map(p=>p.t);
  const minT = timestamps.length ? Math.min(...timestamps) : Date.now()-120000;
  const maxT = timestamps.length ? Math.max(...timestamps) : Date.now();
  [1,2,3].forEach(index => {
    const values=history[index]; if (!values.length) return;
    ctx.strokeStyle=colors[index-1];ctx.lineWidth=2;ctx.beginPath();
    values.forEach((p,i)=>{const x=left+(p.t-minT)/Math.max(1000,maxT-minT)*(width-left-right);i?ctx.lineTo(x,py(Math.max(-yMax,Math.min(yMax,p.y)))):ctx.moveTo(x,py(p.y));});ctx.stroke();
    ctx.fillStyle=colors[index-1];ctx.fillRect(left+(index-1)*110,7,10,3);ctx.fillStyle="#b8ccc3";ctx.fillText(`Follower ${index}`,left+15+(index-1)*110,12);
  });
}

async function poll() {
  try {
    latest = await api("/api/telemetry");
    updateHistory(latest); updateOverview(latest); updateFollowers(latest); drawChart();
  } catch (error) {
    $("message").textContent = `Telemetry unavailable: ${error.message}`;
  }
}

function exportSnapshot() {
  if (!latest) return;
  const blob = new Blob([JSON.stringify(latest,null,2)], {type:"application/json"});
  const link = document.createElement("a"); link.href=URL.createObjectURL(blob); link.download=`ee616-telemetry-${new Date().toISOString().replaceAll(":","-")}.json`; link.click(); URL.revokeObjectURL(link.href);
}

$("start").addEventListener("click", startRun);
$("stop").addEventListener("click", stopRun);
$("export").addEventListener("click", exportSnapshot);
$("route-profile").addEventListener("change", describeProfile);
$("map-profile").addEventListener("change", describeProfile);
$("scenario-profile").addEventListener("change", describeProfile);
window.addEventListener("resize", () => {describeProfile(); drawChart();});
loadProfiles().then(poll);
setInterval(poll, 500);
