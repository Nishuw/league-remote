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

let currentPhase = null;
async function leaveQueue() {
  const dodge = currentPhase === "ChampSelect";
  const msg = dodge
    ? "Sair do campeao select agora? Isso conta como dodge e pode dar punicao."
    : "Sair da fila?";
  if (!confirm(msg)) return;
  const btn = document.getElementById("leavebtn");
  const original = btn.textContent;
  btn.textContent = "saindo...";
  try {
    const j = await (await fetch("/leave", { method: "POST" })).json();
    if (!j.ok) btn.textContent = "falhou - tentar de novo";
    else setTimeout(() => { btn.textContent = original; }, 1500);
  } catch (e) {
    btn.textContent = "erro - tentar de novo";
  }
}

// ---- Filas: criar lobby / iniciar busca pelo celular ----
const QUEUES = [
  { id: 450, name: "ARAM" },
  { id: 2400, name: "ARAM: Desordem" },
  { id: 400, name: "Normal (Seleção)" },
  { id: 430, name: "Normal (Às Cegas)" },
  { id: 420, name: "Ranqueada Solo/Duo" },
  { id: 440, name: "Ranqueada Flex" },
  { id: 1700, name: "Arena" },
];
let lastLobbyLoad = 0;
async function renderQueuePanel(force) {
  const el = document.getElementById("queue-panel");
  if (!el) return;
  const now = Date.now();
  if (!force && now - lastLobbyLoad < 2500) return;
  lastLobbyLoad = now;
  let lob = { in_lobby: false };
  try { lob = await (await fetch("/lobby")).json(); } catch (e) {}
  if (lob.in_lobby) {
    const q = QUEUES.find(x => x.id === lob.queue_id);
    const qname = q ? q.name : ("Fila " + (lob.queue_id || "?"));
    el.innerHTML =
      '<div class="qp-head">Lobby: ' + qname + '</div>' +
      '<div class="qp-actions">' +
        '<button class="qp-start" onclick="startSearch()">Encontrar Partida</button>' +
        '<button class="qp-leave" onclick="leaveLobby()">Sair do lobby</button>' +
      '</div>';
  } else {
    el.innerHTML =
      '<div class="qp-head">Criar fila</div>' +
      '<div class="qp-grid">' +
      QUEUES.map(q => '<button class="qp-btn" onclick="createLobby(' + q.id + ')">' + q.name + '</button>').join("") +
      '</div>';
  }
}
async function createLobby(id) {
  const q = QUEUES.find(x => x.id === id);
  try {
    const r = await fetch("/lobby", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ queueId: id })
    });
    const j = await r.json();
    toast(j.ok ? ("Lobby: " + (q ? q.name : id)) : "Falha ao criar lobby", j.ok);
  } catch (e) { toast("erro de conexão", false); }
  renderQueuePanel(true); tick();
}
async function startSearch() {
  try {
    const j = await (await fetch("/queue/start", { method: "POST" })).json();
    toast(j.ok ? "Procurando partida..." : "Falha ao iniciar fila", j.ok);
  } catch (e) { toast("erro de conexão", false); }
  tick();
}
async function leaveLobby() {
  try { await fetch("/lobby", { method: "DELETE" }); toast("Saiu do lobby"); } catch (e) {}
  renderQueuePanel(true); tick();
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
  if (p.champion) name = '<span class="cname">' + p.champion + '</span>';
  else if (p.picking) name = '<span class="cname empty">escolhendo...</span>';
  else name = '<span class="cname empty">--</span>';
  const tag = p.is_local ? '<span class="metag">VOCE</span>' : '';
  let sub = "";
  if (p.position) sub += '<span class="posb">' + (POS_PT[p.position] || p.position) + '</span>';
  if (p.name) sub += '<span class="sname">' + p.name + '</span>';
  return '<div class="' + cls + '">' +
    '<div class="ava">' + icon + '</div>' +
    '<div class="info">' +
      '<div class="cline">' + name + tag + '</div>' +
      (sub ? '<div class="pos">' + sub + '</div>' : '') +
    '</div></div>';
}

function turnBanner(cs) {
  let cls = "turnbanner", txt = "";
  if (cs.current_actor_cell != null) {
    const mine = cs.current_actor_cell === cs.local_cell;
    const isBan = cs.current_action_type === "ban";
    cls += (mine ? " mine" : "") + (isBan ? " ban" : "");
    txt = mine ? "SUA VEZ DE " + (isBan ? "BANIR" : "ESCOLHER") : "Vez de " + (isBan ? "banir" : "escolher") + "...";
  } else if (cs.time_left) {
    txt = "Selecao de campeao";
  }
  if (!txt) return "";
  const timer = cs.time_left ? '<span class="turntimer">' + cs.time_left + 's</span>' : "";
  return '<div class="' + cls + '"><span>' + txt + '</span>' + timer + '</div>';
}

function bansBar(cs) {
  const slot = b => '<div class="banslot filled"><img src="' + champIcon(b.champion_id) +
    '" title="' + (b.champion || "") + '" onerror="this.style.visibility=\'hidden\'"></div>';
  const side = (label, bans, cls) =>
    '<div class="banside ' + cls + '"><span class="banlbl">' + label + '</span>' +
    '<div class="banrow">' + (bans.length ? bans.map(slot).join("") : '<span class="noban">nenhum</span>') + '</div></div>';
  return '<div class="bansbar">' + side("Bans aliados", cs.my_bans, "ally") + side("Bans inimigos", cs.their_bans, "enemy") + '</div>';
}

function teamsHtml(cs) {
  return '<div class="teams">' +
    '<div class="team ally"><h3>Seu time</h3>' + cs.my_team.map(rowHtml).join("") + '</div>' +
    '<div class="team enemy"><h3>Inimigos</h3>' + cs.their_team.map(rowHtml).join("") + '</div>' +
  '</div>';
}

// ---- ARAM: banco de reserva e trocas ----
// Toast: feedback rapido na propria tela (sucesso/erro de cada acao).
let toastTimer = null;
function toast(msg, ok) {
  const el = document.getElementById("toast");
  if (!el) return;
  el.textContent = msg;
  el.className = "toast " + (ok === false ? "err" : "ok");
  el.hidden = false;
  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { el.hidden = true; }, 2600);
}

async function benchSwap(id) {
  try {
    const r = await fetch("/aram/swap", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ championId: id })
    });
    const j = await r.json();
    toast(j.msg || (j.ok ? "ok" : "falhou"), j.ok);
    tick();  // refresh imediato pra "seu campeao" aparecer na hora
  } catch (e) { toast("erro de conexão", false); }
}
async function tradeAction(id, action) {
  try {
    await fetch("/aram/trade", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id, action })
    });
    tick();
  } catch (e) {}
}

function tradeButtons(t) {
  if (t.state === "RECEIVED") {
    return '<button class="tradebtn ok" onclick="tradeAction(' + t.id + ',\'accept\')">Aceitar</button>' +
           '<button class="tradebtn no" onclick="tradeAction(' + t.id + ',\'decline\')">Recusar</button>';
  }
  if (t.state === "SENT") return '<span class="trade-state">enviado...</span>';
  if (t.state === "AVAILABLE") return '<button class="tradebtn" onclick="tradeAction(' + t.id + ',\'request\')">Pedir troca</button>';
  return '<span class="trade-state">' + String(t.state || "").toLowerCase() + '</span>';
}

// ---- Seletor (bottom-sheet) de feiticos e skin ----
// Modal separado do #champ-info: nao e reconstruido a cada tick, entao nao pisca.
function closePicker() {
  const m = document.getElementById("picker-modal");
  if (m) m.hidden = true;
}
async function openSpellPicker(slot) {
  const body = document.getElementById("picker-body");
  document.getElementById("picker-modal").hidden = false;
  body.innerHTML = '<div class="sheet-title">carregando...</div>';
  let d = { options: [] };
  try { d = await (await fetch("/champ-select/spells")).json(); } catch (e) {}
  const cur1 = d.spell1Id, cur2 = d.spell2Id;
  const atual = slot === 1 ? cur1 : cur2;
  body.innerHTML =
    '<div class="sheet-title">Feitiço ' + slot + '</div>' +
    '<div class="spell-grid">' +
    d.options.map(o =>
      '<button class="spellopt' + (o.id === atual ? ' sel' : '') + '" onclick="pickSpell(' + slot + ',' + o.id + ',' + cur1 + ',' + cur2 + ')">' +
        '<img src="' + (o.icon || "") + '" onerror="this.style.visibility=\'hidden\'"><span>' + (o.name || "") + '</span>' +
      '</button>'
    ).join("") + '</div>';
}
async function pickSpell(slot, id, cur1, cur2) {
  let s1 = cur1, s2 = cur2;
  // Se escolher um feitico que ja esta no outro slot, troca os dois (swap).
  if (slot === 1) { if (id === cur2) s2 = cur1; s1 = id; }
  else { if (id === cur1) s1 = cur2; s2 = id; }
  try {
    const r = await fetch("/champ-select/spells", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ spell1Id: s1, spell2Id: s2 })
    });
    const j = await r.json();
    toast(j.ok ? "Feitiços atualizados" : "Falha nos feitiços", j.ok);
  } catch (e) { toast("erro de conexão", false); }
  closePicker(); tick();
}
async function openSkinPicker() {
  const body = document.getElementById("picker-body");
  document.getElementById("picker-modal").hidden = false;
  body.innerHTML = '<div class="sheet-title">carregando skins...</div>';
  let d = { skins: [] };
  try { d = await (await fetch("/champ-select/skins")).json(); } catch (e) {}
  const sel = d.selectedSkinId;
  if (!d.skins.length) { body.innerHTML = '<div class="sheet-title">sem skins disponíveis</div>'; return; }
  body.innerHTML =
    '<div class="sheet-title">Escolher skin</div>' +
    '<div class="skin-grid">' +
    d.skins.map(s =>
      '<button class="skinopt' + (s.id === sel ? ' sel' : '') + (s.owned ? '' : ' locked') + '" onclick="pickSkin(' + s.id + ')">' +
        '<img src="' + (s.tile || "") + '" onerror="this.style.visibility=\'hidden\'"><span>' + (s.name || "") + '</span>' +
      '</button>'
    ).join("") + '</div>';
}
async function pickSkin(id) {
  try {
    const r = await fetch("/champ-select/skin", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ skinId: id })
    });
    const j = await r.json();
    toast(j.ok ? "Skin trocada" : "Falha ao trocar skin", j.ok);
  } catch (e) { toast("erro de conexão", false); }
  closePicker(); tick();
}

function renderAram(cs) {
  // ARAM (e ARAM: Desordem) sao todos aleatorios: nao existe grade de pick.
  // Voce recebe um campeao sorteado e troca pelo BANCO (as "cartas" que
  // aparecem) ou trocando com aliados.
  const secs = cs.time_left ? Math.max(0, cs.time_left) : 0;
  const timeTag = secs ? ' <span class="aram-time' + (secs <= 5 ? ' urgent' : '') + '">' + secs + 's</span>' : '';
  let h = '<div class="aram-head">campeões' + timeTag + '</div>';

  const hasChamp = !!cs.my_champion_id;
  const hasBench = cs.bench && cs.bench.length;
  const subset = cs.subset || [];
  const hasSubset = subset.length > 0;

  // Campeao atual (depois de escolher / sortear)
  if (hasChamp) {
    h += '<div class="aram-current">' +
      '<img class="aram-champ" src="' + champIcon(cs.my_champion_id) + '" onerror="this.style.visibility=\'hidden\'">' +
      '<div class="aram-meta">' +
        '<div class="aram-lbl">seu campeao</div>' +
        '<div class="aram-name">' + (cs.my_champion || "") + '</div>' +
      '</div></div>';
  }

  // Feitiços (sempre tocáveis) + botão de skin (só quando já há campeão).
  if (cs.my_spells && cs.my_spells.length === 2) {
    h += '<div class="aram-spells">' +
      cs.my_spells.map((sp, i) =>
        '<button class="spellbtn" onclick="openSpellPicker(' + (i + 1) + ')" title="trocar feitiço">' +
          '<img src="' + (sp.icon || "") + '" onerror="this.style.visibility=\'hidden\'">' +
        '</button>'
      ).join("") +
      (hasChamp ? '<button class="skinbtn" onclick="openSkinPicker()">Skin</button>' : '') +
    '</div>';
  }

  // Carta tocavel (escolha inicial ou roleta). Tocar -> /aram/swap, que decide
  // pelo estado: sem campeao completa o PICK; com campeao troca pelo banco.
  const card = b =>
    '<div class="benchitem" onclick="benchSwap(' + b.champion_id + ')">' +
      '<img src="' + champIcon(b.champion_id) + '" onerror="this.style.visibility=\'hidden\'">' +
      '<span>' + (b.champion || "?") + '</span>' +
    '</div>';

  // ESCOLHA INICIAL (subset pessoal): 2-3 campeoes oferecidos na chegada,
  // disponiveis ANTES da roleta popular. So enquanto voce ainda nao tem campeao.
  if (!hasChamp && hasSubset) {
    h += '<div class="aram-sec">Escolha seu campeão (toque)</div>' +
      '<div class="bench-grid cards">' + subset.map(card).join("") + '</div>';
  }

  // ROLETA (banco): os demais campeoes disponiveis para pegar/trocar. Evito
  // repetir os que ja estao na escolha inicial acima.
  const subsetIds = new Set(subset.map(b => b.champion_id));
  const benchOnly = hasBench ? cs.bench.filter(b => hasChamp || !subsetIds.has(b.champion_id)) : [];
  if (benchOnly.length) {
    const title = hasChamp ? "Roleta (toque para trocar)" : "Roleta (toque para pegar)";
    h += '<div class="aram-sec">' + title + '</div>' +
      '<div class="bench-grid cards">' + benchOnly.map(card).join("") + '</div>';
  } else if (!hasChamp && !hasSubset && !hasBench) {
    // Primeiros instantes: nem subset nem roleta ainda. A LCU leva um tico.
    h += '<div class="aram-wait">sorteando campeoes... aguarde os campeoes aparecerem</div>';
  }

  // Trocas com aliados (quando o modo permite)
  if (cs.trades && cs.trades.length) {
    h += '<div class="aram-sec">Trocas com aliados</div>' +
      cs.trades.map(t =>
        '<div class="traderow">' +
          '<img src="' + champIcon(t.champion_id) + '" onerror="this.style.visibility=\'hidden\'">' +
          '<span class="tradewho">' + (t.champion || "?") + (t.name ? ' (' + t.name + ')' : '') + '</span>' +
          tradeButtons(t) +
        '</div>'
      ).join("");
  }

  return h;
}

function renderChamp(cs) {
  if (cs.mode === "bench") return renderAram(cs);
  return turnBanner(cs) + bansBar(cs);
}

let csActionId = undefined;
let csSelected = null;

function ensureChampLayout() {
  const champ = document.getElementById("champ");
  if (!document.getElementById("champ-info")) {
    champ.innerHTML =
      '<div id="champ-info"></div>' +
      '<div id="champ-controls"></div>' +
      '<div id="champ-teams"></div>';
  }
}

// Painel de runas acessivel a qualquer momento (fila, menu, champ select).
function toggleRunesPanel() {
  const panel = document.getElementById("runes-panel");
  if (panel.hidden) {
    panel.hidden = false;
    if (!panel.dataset.init) {
      panel.dataset.init = "1";
      panel.innerHTML = '<div id="runes-area"></div>';
      loadRunes();
    }
  } else {
    panel.hidden = true;
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
      '<div class="pickhead">' + (isBan ? "Quem voce quer banir?" : "Escolha seu campeao") + '</div>' +
      '<input id="champ-search" placeholder="buscar campeao..." oninput="filterChamps()">' +
      '<div class="grid" id="champ-grid">' +
        data.champions.map(c =>
          '<div class="gitem" data-name="' + c.name.toLowerCase() + '" data-id="' + c.id + '" onclick="selectChamp(' + c.id + ')">' +
            '<img loading="lazy" src="' + champIcon(c.id) + '" onerror="this.style.visibility=\'hidden\'">' +
            '<span>' + c.name + '</span>' +
          '</div>'
        ).join("") +
      '</div>' +
      '<button class="lockbtn ' + (isBan ? "ban" : "") + ' lockfull" id="lockbtn" onclick="doLock()">' + verb + '</button>';
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
let lastFeedSig = "";
function ensureLiveLayout() {
  const live = document.getElementById("live");
  if (!document.getElementById("live-stats")) {
    live.innerHTML = '<div id="live-stats"></div><div id="live-feed"></div>';
    lastFeedSig = "";
  }
}
// A Live Client Data API do jogo atualiza ~1x/s; 1000ms mantem os numeros
// frescos sem martelar o endpoint local.
const LIVE_POLL_MS = 1000;
let liveLoading = false;
async function loadLive() {
  // Trava por requisicao em andamento (em vez de janela de tempo): o poller
  // dispara a cada 1s e cada chamada sempre busca, a menos que a anterior
  // ainda nao tenha respondido. Evita o CS/KDA "travarem" por corrida de tempo.
  if (liveLoading) return;
  liveLoading = true;
  try {
    const d = await (await fetch("/live")).json();
    const live = document.getElementById("live");
    if (!d.in_game) {
      live.innerHTML = '<div class="loading">carregando dados da partida...</div>';
      lastFeedSig = "";
      return;
    }
    ensureLiveLayout();
    const mins = Math.floor(d.game_time / 60), secs = d.game_time % 60;
    const teams = { ORDER: [], CHAOS: [] };
    d.players.forEach(p => { (teams[p.team] || (teams[p.team] = [])).push(p); });
    const obj = d.objectives || {};
    const tk = d.team_kills || {};

    const objLine = (t) => {
      const o = obj[t] || {};
      let s = '<span class="ob k">' + (tk[t] || 0) + ' abates</span>' +
              '<span class="ob">' + (o.towers || 0) + ' torres</span>' +
              '<span class="ob">' + (o.dragons || 0) + ' dragoes</span>';
      if (o.barons) s += '<span class="ob">' + o.barons + ' barao</span>';
      return s;
    };

    const prow = (p) => {
      const icon = p.champion_id
        ? '<img src="' + champIcon(p.champion_id) + '" onerror="this.style.visibility=\'hidden\'">'
        : '';
      const status = p.dead
        ? '<span class="ldead">morto ' + p.respawn + 's</span>'
        : '';
      return '<div class="lprow' + (p.dead ? ' isdead' : '') + '">' +
        '<div class="lpava">' + icon + '<span class="llvl">' + (p.level || 0) + '</span></div>' +
        '<span class="lc">' + (p.champion || p.name || "?") + status + '</span>' +
        '<span class="lk">' + p.k + '/' + p.d + '/' + p.a + '</span>' +
        '<span class="lcs">' + p.cs + ' cs</span>' +
        '</div>';
    };

    const teamBlock = (arr, cls, title, tkey) =>
      '<div class="lteam ' + cls + '">' +
        '<div class="lthead"><h4>' + title + '</h4><div class="lobj">' + objLine(tkey) + '</div></div>' +
        arr.map(prow).join("") +
      '</div>';

    let h = '<div class="lhead"><span class="gt">' + mins + ':' + String(secs).padStart(2, "0") + '</span>';
    if (d.map) h += '<span class="lmode">' + d.map + '</span>';
    if (d.your_gold != null) h += '<span class="lgold">' + d.your_gold + ' ouro</span>';
    h += '</div>';
    h += teamBlock(teams.ORDER || [], "ally", "Time Azul", "ORDER");
    h += teamBlock(teams.CHAOS || [], "enemy", "Time Vermelho", "CHAOS");
    document.getElementById("live-stats").innerHTML = h;

    // Feed: so redesenha quando ha evento novo, para nao ficar piscando.
    const feed = Array.isArray(d.feed) ? d.feed : [];
    const sig = feed.map(e => (e.t || 0) + e.txt).join("|");
    if (sig !== lastFeedSig) {
      lastFeedSig = sig;
      const fe = document.getElementById("live-feed");
      if (!feed.length) {
        fe.innerHTML = "";
      } else {
        fe.innerHTML = '<div class="lfeed"><div class="lfeed-t">Eventos</div>' +
          feed.slice().reverse().map(e => {
            const m = Math.floor((e.t || 0) / 60), s = Math.floor((e.t || 0) % 60);
            const cls = "lfeed-row" + (e.team === "ORDER" ? " ally" : (e.team === "CHAOS" ? " enemy" : ""));
            const ic = e.cid ? '<img class="lfeed-ic" src="' + champIcon(e.cid) + '" onerror="this.style.display=\'none\'">' : "";
            return '<div class="' + cls + '">' +
              '<span class="lfeed-time">' + m + ':' + String(s).padStart(2, "0") + '</span>' +
              ic + '<span class="lfeed-txt">' + e.txt + '</span></div>';
          }).join("") + '</div>';
      }
    }
  } catch (e) {
    document.getElementById("live").innerHTML = '<div class="loading">sem dados ao vivo (ative a API no jogo)</div>';
    lastFeedSig = "";
  } finally {
    liveLoading = false;
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

const PRIORITY_LABELS = ["1a opcao", "2a opcao", "3a opcao"];

function prioritySelects(prefix, list) {
  list = list || [];
  let h = "";
  for (let i = 0; i < PRIORITY_LABELS.length; i++) {
    h += '<div class="cfg-prio-row"><span class="cfg-prio-n">' + PRIORITY_LABELS[i] + '</span>' +
      '<select id="' + prefix + '-' + i + '" onchange="saveConfig()">' + champOptions(list[i] != null ? list[i] : null) + '</select></div>';
  }
  return h;
}

function collectPriority(prefix) {
  const out = [];
  for (let i = 0; i < PRIORITY_LABELS.length; i++) {
    const el = document.getElementById(prefix + "-" + i);
    const v = el && el.value ? parseInt(el.value) : null;
    if (v && !out.includes(v)) out.push(v);
  }
  return out;
}

function renderConfig(cfg) {
  const panel = document.getElementById("cfg-panel");
  panel.innerHTML =
    '<div class="cfg-row"><label>Auto-pick</label>' +
      '<label class="switch"><input type="checkbox" id="cfg-pick-on" ' + (cfg.auto_pick_enabled ? "checked" : "") + ' onchange="saveConfig()"><span class="slider"></span></label></div>' +
    '<div class="cfg-sub">Campeoes (ordem de prioridade)</div>' +
    '<div class="cfg-priority">' + prioritySelects("cfg-pick", cfg.auto_pick_champs) + '</div>' +
    '<div class="cfg-row"><label>Auto-ban</label>' +
      '<label class="switch"><input type="checkbox" id="cfg-ban-on" ' + (cfg.auto_ban_enabled ? "checked" : "") + ' onchange="saveConfig()"><span class="slider"></span></label></div>' +
    '<div class="cfg-sub">Campeoes (ordem de prioridade)</div>' +
    '<div class="cfg-priority">' + prioritySelects("cfg-ban", cfg.auto_ban_champs) + '</div>' +
    '<div class="cfg-row"><label>Nao banir pick de aliado</label>' +
      '<label class="switch"><input type="checkbox" id="cfg-protect" ' + (cfg.ban_protect_allies ? "checked" : "") + ' onchange="saveConfig()"><span class="slider"></span></label></div>' +
    '<div class="muted" style="font-size:11px;margin-top:6px">Tenta na ordem e pula quem ja foi banido/escolhido. Se nenhum estiver disponivel, a selecao manual aparece na sua vez.</div>';
}

async function saveConfig() {
  const body = {
    auto_pick_enabled: document.getElementById("cfg-pick-on").checked,
    auto_ban_enabled: document.getElementById("cfg-ban-on").checked,
    ban_protect_allies: document.getElementById("cfg-protect").checked,
    auto_pick_champs: collectPriority("cfg-pick"),
    auto_ban_champs: collectPriority("cfg-ban"),
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
    currentPhase = s.phase;

    document.getElementById("conn").textContent = s.connected ? "cliente conectado" : "cliente do LoL fechado";
    document.getElementById("conn-dot").className = "dot " + (s.connected ? "on" : "off");

    const phaseEl = document.getElementById("phase");
    let phaseTxt = PHASE_PT[s.phase] || (s.phase || "--");
    if (s.mode_name && ["Matchmaking", "ReadyCheck", "ChampSelect", "InProgress"].includes(s.phase)) {
      phaseTxt += " — " + s.mode_name;
    }
    phaseEl.textContent = phaseTxt;

    // Em jogo a tela e so leitura: esconde Auto-pick/ban e Runas.
    // ARAM: Desordem tambem nao tem runas (usa aprimoramentos).
    const inGame = s.phase === "InProgress";
    const cfgBtn = document.getElementById("cfgbtn");
    if (cfgBtn) {
      cfgBtn.style.display = inGame ? "none" : "";
      if (inGame) { const cp = document.getElementById("cfg-panel"); if (cp) cp.hidden = true; }
    }
    const runesBtn = document.getElementById("runesbtn");
    if (runesBtn) {
      const hideRunes = inGame || s.runes_enabled === false;
      runesBtn.style.display = hideRunes ? "none" : "";
      if (hideRunes) { const rp = document.getElementById("runes-panel"); if (rp) rp.hidden = true; }
    }

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
      leave.style.display = "none";
    };

    // Mantem o poller ao vivo so durante a partida; startLivePoll e idempotente.
    if (s.phase !== "InProgress") stopLivePoll();

    if (s.phase === "ReadyCheck" && s.ready_check && s.player_response === "None") {
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
      const cs = s.champ_select;
      document.getElementById("champ-info").innerHTML = renderChamp(cs);
      // Grade com todos os campeoes so no draft normal (pick/ban por vez).
      // No ARAM/Desordem a escolha e as trocas acontecem pelas cartas do banco
      // (renderAram), entao nunca mostramos a grade completa.
      const ctr = document.getElementById("champ-controls");
      if (cs.mode === "draft" && cs.is_my_turn) {
        loadChampControls(cs);
      } else if (ctr && ctr.innerHTML !== "") {
        ctr.innerHTML = ""; csActionId = undefined; csSelected = null;
      }
      document.getElementById("champ-teams").innerHTML = teamsHtml(cs);
      leave.style.display = "block";
      leave.textContent = "Sair (dodge)";
      phaseEl.classList.remove("flash");
    } else if (s.phase === "InProgress") {
      stopAlarm();
      hideAll();
      card.classList.add("wide");
      live.style.display = "block";
      startLivePoll();
      phaseEl.classList.remove("flash");
    } else if (s.player_response === "Accepted") {
      stopAlarm();
      hideAll();
      resetChampLayout();
      card.classList.remove("wide");
      content.style.display = "block";
      leave.style.display = "none";
      idleExtra.innerHTML = "";
      { const qp = document.getElementById("queue-panel"); if (qp) qp.innerHTML = ""; }
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
      const queuePanel = document.getElementById("queue-panel");
      if (s.phase === "Matchmaking") {
        queue.style.display = "";
        label.style.display = "";
        queue.textContent = fmt(s.time_in_queue);
        label.textContent = "tempo de fila";
        leave.style.display = "block";
        leave.textContent = "Sair da fila";
        idleExtra.innerHTML = "";
        if (queuePanel) queuePanel.innerHTML = "";  // em fila nao mostra o seletor
      } else {
        queue.style.display = "none";
        label.style.display = "none";
        leave.style.display = "none";
        renderQueuePanel();  // criar fila / encontrar partida pelo celular
        loadIdleExtra();
      }
    }
    document.getElementById("foot").textContent = s.last_action || "";
  } catch (e) {
    document.getElementById("conn").textContent = "servidor offline";
    document.getElementById("conn-dot").className = "dot off";
  }
}

// Poller dedicado do painel ao vivo: roda em ~1s (independente do tick de UI
// de 700ms) enquanto a partida esta em andamento, mantendo os numeros frescos.
let liveTimer = null;
function startLivePoll() {
  if (liveTimer) return;
  loadLive(); // busca imediata ao entrar na partida
  liveTimer = setInterval(loadLive, LIVE_POLL_MS);
}
function stopLivePoll() {
  if (liveTimer) { clearInterval(liveTimer); liveTimer = null; }
}

// Tick adaptativo: o backend ja recebe os eventos da LCU em tempo real (via
// WebSocket), entao nas fases sensiveis (ready-check, champ select / roleta do
// ARAM) buscamos o /status mais rapido para a tela acompanhar sem lag.
const FAST_TICK_PHASES = ["ReadyCheck", "ChampSelect"];
function scheduleTick() {
  const delay = FAST_TICK_PHASES.includes(currentPhase) ? 350 : 700;
  setTimeout(async () => { try { await tick(); } finally { scheduleTick(); } }, delay);
}
tick();
scheduleTick();
