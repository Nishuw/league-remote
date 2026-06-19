"use strict";

let accepting = false;

function fmt(s) {
  s = Math.max(0, parseInt(s) || 0);
  const m = Math.floor(s / 60), r = s % 60;
  return m + ":" + String(r).padStart(2, "0");
}

// ---- Acoes do ready-check ----
async function accept() {
  if (accepting) return;
  accepting = true;
  stopAlarm();
  const btn = document.getElementById("accept");
  btn.textContent = "ACEITANDO...";
  try {
    const r = await fetch("/accept", { method: "POST" });
    const j = await r.json();
    btn.textContent = j.ok ? "ACEITO!" : "FALHOU - tentar de novo";
  } catch (e) {
    btn.textContent = "ERRO - tentar de novo";
  }
  setTimeout(() => { accepting = false; }, 1500);
}

async function decline() {
  stopAlarm();
  try { await fetch("/decline", { method: "POST" }); } catch (e) {}
}

async function leaveQueue() {
  if (!confirm("Sair da fila?")) return;
  try { await fetch("/leave-queue", { method: "POST" }); } catch (e) {}
}

// ---- Alarme (vibrar + som) ----
let audioCtx = null;
let alarmTimer = null;
function beep() {
  try {
    if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    if (audioCtx.state === "suspended") audioCtx.resume();
    const o = audioCtx.createOscillator(), g = audioCtx.createGain();
    o.type = "square"; o.frequency.value = 880;
    o.connect(g); g.connect(audioCtx.destination);
    g.gain.setValueAtTime(0.001, audioCtx.currentTime);
    g.gain.exponentialRampToValueAtTime(0.3, audioCtx.currentTime + 0.02);
    g.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.4);
    o.start(); o.stop(audioCtx.currentTime + 0.45);
  } catch (e) {}
}
function startAlarm() {
  if (alarmTimer) return;
  const fire = () => { beep(); if (navigator.vibrate) navigator.vibrate([300, 150, 300]); };
  fire();
  alarmTimer = setInterval(fire, 1200);
}
function stopAlarm() {
  if (alarmTimer) { clearInterval(alarmTimer); alarmTimer = null; }
  if (navigator.vibrate) navigator.vibrate(0);
}

const PHASE_PT = {
  None: "No menu", Lobby: "No lobby", Matchmaking: "Na fila",
  ReadyCheck: "Partida encontrada!", ChampSelect: "Selecao de campeao",
  InProgress: "Em partida", PreEndOfGame: "Fim de jogo", EndOfGame: "Fim de jogo",
};

const POS_PT = {
  top: "Top", jungle: "Jungle", middle: "Mid", bottom: "ADC", utility: "Suporte",
};

function champIcon(id) {
  return "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/champion-icons/" + id + ".png";
}

function rowHtml(p) {
  const cls = "row" + (p.is_local ? " me" : "") + (p.picking ? " turn-now" : "");
  const icon = p.champion_id
    ? '<img src="' + champIcon(p.champion_id) + '" onerror="this.style.visibility=\'hidden\'">'
    : '<div class="noimg"></div>';
  let name;
  if (p.champion) name = '<div class="cname">' + p.champion + '</div>';
  else if (p.picking) name = '<div class="cname empty">escolhendo...</div>';
  else name = '<div class="cname empty">--</div>';
  let sub = "";
  if (p.name) sub = '<div class="pos">' + p.name + '</div>';
  else if (p.position) sub = '<div class="pos">' + (POS_PT[p.position] || p.position) + '</div>';
  return '<div class="' + cls + '">' + icon + '<div class="info">' + name + sub + '</div></div>';
}

function bansHtml(label, bans) {
  let imgs = bans.map(b => '<img src="' + champIcon(b.champion_id) + '" title="' + (b.champion || '') + '" onerror="this.style.display=\'none\'">').join("");
  if (!imgs) imgs = '<span class="pos">nenhum</span>';
  return '<div class="bans"><span class="lbl">' + label + '</span>' + imgs + '</div>';
}

function renderChamp(cs) {
  let turn = "";
  if (cs.current_actor_cell != null) {
    const mine = cs.current_actor_cell === cs.local_cell;
    const act = cs.current_action_type === "ban" ? "banir" : "escolher";
    turn = mine
      ? '<b>SUA VEZ</b> de ' + act + '! (' + cs.time_left + 's)'
      : 'Vez de ' + act + '... (' + cs.time_left + 's)';
  } else if (cs.time_left) {
    turn = 'Tempo: ' + cs.time_left + 's';
  }
  return (
    '<div class="turn">' + turn + '</div>' +
    '<div class="teams">' +
      '<div class="team ally"><h3>Seu time</h3>' + cs.my_team.map(rowHtml).join("") + '</div>' +
      '<div class="team enemy"><h3>Inimigos</h3>' + cs.their_team.map(rowHtml).join("") + '</div>' +
    '</div>' +
    bansHtml("Bans aliados", cs.my_bans) +
    bansHtml("Bans inimigos", cs.their_bans)
  );
}

let csActionId = undefined;
let csSelected = null;

function ensureChampLayout() {
  const champ = document.getElementById("champ");
  if (!document.getElementById("champ-info")) {
    champ.innerHTML =
      '<div id="champ-info"></div>' +
      '<div id="champ-controls"></div>' +
      '<div id="runes-area"></div>';
    loadRunes();
  }
}

function resetChampLayout() {
  const champ = document.getElementById("champ");
  if (champ.innerHTML !== "") champ.innerHTML = "";
  csActionId = undefined;
  csSelected = null;
}

async function loadChampControls(cs) {
  const ctr = document.getElementById("champ-controls");
  if (!ctr) return;
  if (!cs.is_my_turn) {
    if (csActionId !== undefined) { ctr.innerHTML = ""; csActionId = undefined; csSelected = null; }
    return;
  }
  if (cs.my_action_id === csActionId) return;
  csActionId = cs.my_action_id;
  csSelected = null;
  ctr.innerHTML = '<div class="loading">carregando campeoes...</div>';
  try {
    const data = await (await fetch("/champ-options")).json();
    const isBan = data.type === "ban";
    const verb = isBan ? "BANIR" : "TRAVAR";
    ctr.innerHTML =
      '<div class="pickbar">' +
        '<input id="champ-search" placeholder="buscar campeao..." oninput="filterChamps()">' +
        '<button class="lockbtn ' + (isBan ? "ban" : "") + '" id="lockbtn" onclick="doLock()">' + verb + '</button>' +
      '</div>' +
      '<div class="grid" id="champ-grid">' +
        data.champions.map(c =>
          '<div class="gitem" data-name="' + c.name.toLowerCase() + '" data-id="' + c.id + '" onclick="selectChamp(' + c.id + ')">' +
            '<img loading="lazy" src="' + champIcon(c.id) + '" onerror="this.style.visibility=\'hidden\'">' +
            '<span>' + c.name + '</span>' +
          '</div>'
        ).join("") +
      '</div>';
  } catch (e) {
    ctr.innerHTML = '<div class="loading">erro ao carregar campeoes</div>';
    csActionId = undefined;
  }
}

function filterChamps() {
  const q = document.getElementById("champ-search").value.toLowerCase();
  document.querySelectorAll("#champ-grid .gitem").forEach(el => {
    el.style.display = el.dataset.name.includes(q) ? "" : "none";
  });
}

async function selectChamp(id) {
  csSelected = id;
  document.querySelectorAll("#champ-grid .gitem").forEach(el => {
    el.classList.toggle("sel", parseInt(el.dataset.id) === id);
  });
  try {
    await fetch("/champ-action", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ championId: id, complete: false })
    });
  } catch (e) {}
}

async function doLock() {
  if (!csSelected) return;
  const btn = document.getElementById("lockbtn");
  const original = btn.textContent;
  btn.textContent = "...";
  try {
    const j = await (await fetch("/champ-action", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ championId: csSelected, complete: true })
    })).json();
    btn.textContent = j.ok ? "OK!" : "FALHOU";
  } catch (e) { btn.textContent = "ERRO"; }
  setTimeout(() => { if (btn) btn.textContent = original; }, 1500);
}

function loadRunes() {
  const area = document.getElementById("runes-area");
  if (!area || area.dataset.init) return;
  area.dataset.init = "1";
  area.innerHTML =
    '<button class="runebtn" onclick="toggleRunes()">Paginas de runa salvas</button>' +
    '<div id="rune-list" hidden></div>' +
    '<button class="runebtn" onclick="toggleRuneEditor()">Montar runa</button>' +
    '<div id="rune-editor" hidden></div>';
}

async function renderRuneList() {
  const list = document.getElementById("rune-list");
  const pages = await (await fetch("/runes")).json();
  list.innerHTML = pages.map(p =>
    '<div class="runepage' + (p.current ? " cur" : "") + '" onclick="selectRune(' + p.id + ')">' +
      p.name + (p.current ? " &#10003;" : "") +
    '</div>'
  ).join("") || '<div class="loading">nenhuma pagina salva</div>';
}

async function toggleRunes() {
  const list = document.getElementById("rune-list");
  if (list.hidden) {
    list.hidden = false;
    await renderRuneList();
  } else {
    list.hidden = true;
  }
}

async function selectRune(id) {
  try {
    await fetch("/runes/select", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id })
    });
    await renderRuneList();
  } catch (e) {}
}

// ---- Editor de runas ----
let runeData = null;
let runeSel = { primary: null, keystone: null, minors: [null, null, null], sub: null, secondary: [null, null, null], shards: [null, null, null] };

async function toggleRuneEditor() {
  const ed = document.getElementById("rune-editor");
  if (ed.hidden) {
    ed.hidden = false;
    if (!runeData) {
      ed.innerHTML = '<div class="loading">carregando runas...</div>';
      try { runeData = await (await fetch("/rune-data")).json(); prefillRunes(); }
      catch (e) { ed.innerHTML = '<div class="loading">erro ao carregar runas</div>'; return; }
    }
    renderRuneEditor();
  } else {
    ed.hidden = true;
  }
}

function styleById(id) { return runeData.styles.find(s => s.id === id); }

function prefillRunes() {
  const c = runeData.current || {};
  const ids = c.selectedPerkIds || [];
  if (c.primaryStyleId) runeSel.primary = c.primaryStyleId;
  if (c.subStyleId) runeSel.sub = c.subStyleId;
  if (ids.length === 9) {
    runeSel.keystone = ids[0];
    runeSel.minors = [ids[1], ids[2], ids[3]];
    // mapeia as 2 secundarias para as linhas da arvore secundaria
    const sub = styleById(runeSel.sub);
    runeSel.secondary = [null, null, null];
    if (sub) {
      [ids[4], ids[5]].forEach(pid => {
        sub.rows.forEach((row, r) => { if (row.some(p => p.id === pid)) runeSel.secondary[r] = pid; });
      });
    }
    runeSel.shards = [ids[6], ids[7], ids[8]];
  }
}

function renderRuneEditor() {
  const ed = document.getElementById("rune-editor");
  const prim = runeSel.primary ? styleById(runeSel.primary) : null;
  const sub = runeSel.sub ? styleById(runeSel.sub) : null;
  let h = "";

  h += '<div class="rune-sec-title">Arvore primaria</div><div class="rune-styles">';
  runeData.styles.forEach(s => {
    h += '<div class="rstyle' + (s.id === runeSel.primary ? " sel" : "") + '" onclick="pickPrimary(' + s.id + ')">' +
      '<img src="' + s.icon + '" onerror="this.style.visibility=\'hidden\'"><span>' + s.name + '</span></div>';
  });
  h += '</div>';

  if (prim) {
    h += '<div class="rune-sec-title">Runa principal</div><div class="rune-row">';
    prim.keystones.forEach(p => {
      h += '<img class="rperk key' + (p.id === runeSel.keystone ? " sel" : "") + '" src="' + p.icon +
        '" title="' + p.name + '" onerror="this.style.visibility=\'hidden\'" onclick="pickKeystone(' + p.id + ')">';
    });
    h += '</div>';
    prim.rows.forEach((row, r) => {
      h += '<div class="rune-row">';
      row.forEach(p => {
        h += '<img class="rperk' + (p.id === runeSel.minors[r] ? " sel" : "") + '" src="' + p.icon +
          '" title="' + p.name + '" onerror="this.style.visibility=\'hidden\'" onclick="pickMinor(' + r + ',' + p.id + ')">';
      });
      h += '</div>';
    });

    h += '<div class="rune-sec-title">Arvore secundaria</div><div class="rune-styles">';
    runeData.styles.filter(s => s.id !== runeSel.primary).forEach(s => {
      h += '<div class="rstyle' + (s.id === runeSel.sub ? " sel" : "") + '" onclick="pickSub(' + s.id + ')">' +
        '<img src="' + s.icon + '" onerror="this.style.visibility=\'hidden\'"><span>' + s.name + '</span></div>';
    });
    h += '</div>';

    if (sub) {
      h += '<div class="rune-sec-title">Runas secundarias (escolha 2)</div>';
      sub.rows.forEach((row, r) => {
        h += '<div class="rune-row">';
        row.forEach(p => {
          h += '<img class="rperk' + (p.id === runeSel.secondary[r] ? " sel" : "") + '" src="' + p.icon +
            '" title="' + p.name + '" onerror="this.style.visibility=\'hidden\'" onclick="pickSecondary(' + r + ',' + p.id + ')">';
        });
        h += '</div>';
      });
    }
  }

  if (runeData.shards.length) {
    h += '<div class="rune-sec-title">Fragmentos</div>';
    runeData.shards.forEach((row, r) => {
      h += '<div class="rune-row">';
      row.forEach(p => {
        h += '<img class="rperk shard' + (p.id === runeSel.shards[r] ? " sel" : "") + '" src="' + p.icon +
          '" title="' + p.name + '" onerror="this.style.visibility=\'hidden\'" onclick="pickShard(' + r + ',' + p.id + ')">';
      });
      h += '</div>';
    });
  }

  const valid = runeValid();
  h += '<button class="applybtn" id="applybtn" ' + (valid ? "" : "disabled") + ' onclick="applyRunes()">APLICAR RUNA</button>';
  h += '<div class="saverow"><input id="rune-save-name" placeholder="nome da nova pagina"><button class="savebtn" onclick="saveRunePage()">Salvar</button></div>';
  ed.innerHTML = h;
}

async function saveRunePage() {
  if (!runeValid()) { alert("Monte a runa completa antes de salvar."); return; }
  const name = (document.getElementById("rune-save-name").value || "").trim();
  if (!name) { alert("Digite um nome para a pagina."); return; }
  try {
    const j = await (await fetch("/rune-save", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, primaryStyleId: runeSel.primary, subStyleId: runeSel.sub, selectedPerkIds: buildPerkIds() })
    })).json();
    alert(j.ok ? "Pagina '" + name + "' salva!" : "Falha ao salvar.");
  } catch (e) { alert("Erro ao salvar."); }
}

function pickPrimary(id) {
  if (runeSel.primary === id) return;
  runeSel.primary = id;
  runeSel.keystone = null; runeSel.minors = [null, null, null];
  if (runeSel.sub === id) { runeSel.sub = null; runeSel.secondary = [null, null, null]; }
  renderRuneEditor();
}
function pickKeystone(id) { runeSel.keystone = id; renderRuneEditor(); }
function pickMinor(r, id) { runeSel.minors[r] = id; renderRuneEditor(); }
function pickSub(id) {
  if (runeSel.sub === id) return;
  runeSel.sub = id; runeSel.secondary = [null, null, null];
  renderRuneEditor();
}
function pickSecondary(r, id) {
  if (runeSel.secondary[r] === id) { runeSel.secondary[r] = null; renderRuneEditor(); return; }
  const count = runeSel.secondary.filter(x => x !== null).length;
  if (runeSel.secondary[r] === null && count >= 2) return; // ja tem 2
  runeSel.secondary[r] = id;
  renderRuneEditor();
}
function pickShard(r, id) { runeSel.shards[r] = id; renderRuneEditor(); }

function runeValid() {
  const s = runeSel;
  return s.primary && s.keystone && s.minors.every(x => x) &&
    s.sub && s.secondary.filter(x => x !== null).length === 2 &&
    s.shards.every(x => x);
}

function buildPerkIds() {
  const s = runeSel;
  const sec = [];
  s.secondary.forEach(x => { if (x !== null) sec.push(x); });
  return [s.keystone, s.minors[0], s.minors[1], s.minors[2], sec[0], sec[1], s.shards[0], s.shards[1], s.shards[2]];
}

async function applyRunes() {
  if (!runeValid()) return;
  const btn = document.getElementById("applybtn");
  btn.textContent = "APLICANDO...";
  try {
    const j = await (await fetch("/rune-apply", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ primaryStyleId: runeSel.primary, subStyleId: runeSel.sub, selectedPerkIds: buildPerkIds() })
    })).json();
    btn.textContent = j.ok ? "RUNA APLICADA!" : "FALHOU";
  } catch (e) { btn.textContent = "ERRO"; }
  setTimeout(() => { const b = document.getElementById("applybtn"); if (b) b.textContent = "APLICAR RUNA"; }, 1800);
}

// ---- Painel ao vivo ----
let lastLiveLoad = 0;
async function loadLive() {
  const now = Date.now();
  if (now - lastLiveLoad < 2000) return;
  lastLiveLoad = now;
  try {
    const d = await (await fetch("/live")).json();
    const live = document.getElementById("live");
    if (!d.in_game) { live.innerHTML = '<div class="loading">carregando dados da partida...</div>'; return; }
    const mins = Math.floor(d.game_time / 60), secs = d.game_time % 60;
    const teams = { ORDER: [], CHAOS: [] };
    d.players.forEach(p => { (teams[p.team] || (teams[p.team] = [])).push(p); });
    const teamHtml = (arr, cls, title) =>
      '<div class="lteam ' + cls + '"><h4>' + title + '</h4>' +
      arr.map(p =>
        '<div class="lprow"><span class="lc">' + (p.champion || p.name || "?") + '</span>' +
        '<span class="lk">' + p.k + '/' + p.d + '/' + p.a + '</span>' +
        '<span class="lcs">' + p.cs + ' cs</span></div>'
      ).join("") + '</div>';
    live.innerHTML =
      '<div class="gt">' + mins + ':' + String(secs).padStart(2, "0") + '</div>' +
      teamHtml(teams.ORDER || [], "ally", "Time Azul") +
      teamHtml(teams.CHAOS || [], "enemy", "Time Vermelho");
  } catch (e) {
    document.getElementById("live").innerHTML = '<div class="loading">sem dados ao vivo (ative a API no jogo)</div>';
  }
}

// ---- Elo + historico (tela ociosa) ----
let lastIdleLoad = 0;
async function loadIdleExtra() {
  const now = Date.now();
  if (now - lastIdleLoad < 20000) return;
  lastIdleLoad = now;
  const el = document.getElementById("idle-extra");
  try {
    const [rk, hist] = await Promise.all([
      (await fetch("/rank")).json(),
      (await fetch("/history")).json(),
    ]);
    let h = "";
    const card = (q, lbl) => q ?
      '<div class="rank-card"><div class="q">' + lbl + '</div><div class="t">' + q.tier + '</div>' +
      '<div class="wl">' + q.lp + ' PDL &middot; ' + q.wins + 'V/' + q.losses + 'D</div></div>' : "";
    if (rk.solo || rk.flex) h += '<div class="rank-box">' + card(rk.solo, "Solo/Duo") + card(rk.flex, "Flex") + '</div>';
    if (Array.isArray(hist) && hist.length) {
      h += '<div class="hist"><div class="htitle">Ultimas partidas</div>' +
        hist.map(g => {
          return '<div class="hrow ' + (g.win ? "win" : "loss") + '">' +
            '<img src="' + champIcon(g.champion_id) + '" onerror="this.style.visibility=\'hidden\'">' +
            '<span class="hc">' + (g.champion || "?") + '</span>' +
            '<span class="hkda">' + g.k + '/' + g.d + '/' + g.a + '</span>' +
            '<span class="hres">' + (g.win ? "VITORIA" : "DERROTA") + '</span></div>';
        }).join("") + '</div>';
    }
    el.innerHTML = h || '<div class="muted">aguardando fila</div>';
  } catch (e) {
    el.innerHTML = "";
  }
}

// ---- Config auto-pick/ban ----
let champListCache = null;
async function toggleConfig() {
  const panel = document.getElementById("cfg-panel");
  if (panel.hidden) {
    panel.hidden = false;
    if (!champListCache) champListCache = await (await fetch("/champ-list")).json();
    const cfg = await (await fetch("/config")).json();
    renderConfig(cfg);
  } else {
    panel.hidden = true;
  }
}

function champOptions(selected) {
  return '<option value="">-- nenhum --</option>' +
    champListCache.map(c => '<option value="' + c.id + '"' + (c.id === selected ? " selected" : "") + '>' + c.name + '</option>').join("");
}

function renderConfig(cfg) {
  const panel = document.getElementById("cfg-panel");
  panel.innerHTML =
    '<div class="cfg-row"><label>Auto-pick</label>' +
      '<label class="switch"><input type="checkbox" id="cfg-pick-on" ' + (cfg.auto_pick_enabled ? "checked" : "") + ' onchange="saveConfig()"><span class="slider"></span></label></div>' +
    '<div class="cfg-row"><label>Campeao</label><select id="cfg-pick-champ" onchange="saveConfig()">' + champOptions(cfg.auto_pick_champ) + '</select></div>' +
    '<div class="cfg-row"><label>Auto-ban</label>' +
      '<label class="switch"><input type="checkbox" id="cfg-ban-on" ' + (cfg.auto_ban_enabled ? "checked" : "") + ' onchange="saveConfig()"><span class="slider"></span></label></div>' +
    '<div class="cfg-row"><label>Campeao</label><select id="cfg-ban-champ" onchange="saveConfig()">' + champOptions(cfg.auto_ban_champ) + '</select></div>' +
    '<div class="muted" style="font-size:11px;margin-top:6px">Trava automaticamente na sua vez. O alarme/aceitar continua valendo.</div>';
}

async function saveConfig() {
  const body = {
    auto_pick_enabled: document.getElementById("cfg-pick-on").checked,
    auto_ban_enabled: document.getElementById("cfg-ban-on").checked,
    auto_pick_champ: document.getElementById("cfg-pick-champ").value || null,
    auto_ban_champ: document.getElementById("cfg-ban-champ").value || null,
  };
  try { await fetch("/config", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }); } catch (e) {}
}

// ---- Loop principal de UI ----
function setActionBar(visible) {
  const bar = document.getElementById("actionbar");
  if (bar.hidden === !visible) return;
  bar.hidden = !visible;
}

async function tick() {
  try {
    const r = await fetch("/status");
    const s = await r.json();

    document.getElementById("conn").textContent = s.connected ? "cliente conectado" : "cliente do LoL fechado";
    document.getElementById("conn-dot").className = "dot " + (s.connected ? "on" : "off");

    const phaseEl = document.getElementById("phase");
    phaseEl.textContent = PHASE_PT[s.phase] || (s.phase || "--");

    const btn = document.getElementById("accept");
    const content = document.getElementById("content");
    const champ = document.getElementById("champ");
    const live = document.getElementById("live");
    const card = document.getElementById("card");
    const queue = document.getElementById("queue");
    const label = document.getElementById("queue-label");
    const leave = document.getElementById("leavebtn");
    const idleExtra = document.getElementById("idle-extra");

    const hideAll = () => {
      setActionBar(false);
      content.style.display = "none";
      champ.style.display = "none";
      live.style.display = "none";
    };

    if (s.ready_check && s.player_response === "None") {
      hideAll();
      resetChampLayout();
      card.classList.remove("wide");
      setActionBar(true);
      phaseEl.classList.add("flash");
      if (!accepting) btn.textContent = "ACEITAR";
      startAlarm();
    } else if (s.phase === "ChampSelect" && s.champ_select) {
      stopAlarm();
      hideAll();
      card.classList.add("wide");
      champ.style.display = "block";
      ensureChampLayout();
      document.getElementById("champ-info").innerHTML = renderChamp(s.champ_select);
      loadChampControls(s.champ_select);
      phaseEl.classList.remove("flash");
    } else if (s.phase === "InProgress") {
      stopAlarm();
      hideAll();
      card.classList.add("wide");
      live.style.display = "block";
      loadLive();
      phaseEl.classList.remove("flash");
    } else if (s.player_response === "Accepted") {
      stopAlarm();
      hideAll();
      resetChampLayout();
      card.classList.remove("wide");
      content.style.display = "block";
      leave.style.display = "none";
      idleExtra.innerHTML = "";
      phaseEl.classList.remove("flash");
      queue.textContent = "OK";
      label.textContent = "partida aceita";
    } else {
      stopAlarm();
      hideAll();
      resetChampLayout();
      card.classList.remove("wide");
      content.style.display = "block";
      phaseEl.classList.remove("flash");
      if (s.phase === "Matchmaking") {
        queue.style.display = "";
        label.style.display = "";
        queue.textContent = fmt(s.time_in_queue);
        label.textContent = "tempo de fila";
        leave.style.display = "block";
        idleExtra.innerHTML = "";
      } else {
        queue.style.display = "none";
        label.style.display = "none";
        leave.style.display = "none";
        loadIdleExtra();
      }
    }
    document.getElementById("foot").textContent = s.last_action || "";
  } catch (e) {
    document.getElementById("conn").textContent = "servidor offline";
    document.getElementById("conn-dot").className = "dot off";
  }
}

setInterval(tick, 700);
tick();
