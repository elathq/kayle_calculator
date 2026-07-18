/* Kayle Damage Simulator — frontend logic (vanilla JS) */
"use strict";

const API = "";
let ITEMS = [];                 // catalog from backend
let ITEM_BY_KEY = {};
let RUNES = [];                 // rune paths from backend
let SHARDS = [];                // shard slots from backend
let RUNE_BY_ID = {};
let PATH_BY_ID = {};
let buildSeq = 0;

const state = {
  level: 18,
  ranks: { Q: 5, W: 5, E: 5, R: 3 },
  ranksTouched: false,
  builds: [],                   // {id, name, items:[key|null x6], collapsed}
  combo: [],                    // {type, item?}
  enemyPreset: "dummy",
};

const $ = (id) => document.getElementById(id);

/* ================= init ================= */

async function init() {
  // One compressed request replaces the five serial requests needed for the
  // initial catalog, runes, champion progression, and enemy preset.
  const bootstrap = await (await fetch(
    `${API}/api/bootstrap?level=${state.level}&preset=${state.enemyPreset}`)).json();

  ITEMS = bootstrap.items;
  ITEMS.forEach((it) => (ITEM_BY_KEY[it.key] = it));

  const runeData = bootstrap.runes;
  RUNES = runeData.paths;
  SHARDS = runeData.shards;
  for (const p of RUNES) {
    PATH_BY_ID[p.id] = p;
    p.slots.forEach((slot, row) =>
      slot.forEach((r) => (RUNE_BY_ID[r.id] = { ...r, pathId: p.id, row })));
  }

  const presets = bootstrap.enemy_presets;
  const sel = $("enemyPreset");
  presets.forEach((p) => {
    const o = document.createElement("option");
    o.value = p.key;
    o.textContent = p.name;
    sel.appendChild(o);
  });
  sel.value = state.enemyPreset;

  state.ranks = bootstrap.champion.default_ranks;
  buildRankSelects();
  for (const ab of ["Q", "W", "E", "R"]) $("rank" + ab).value = state.ranks[ab];
  applyEnemyData(bootstrap.enemy);
  addBuild();                   // start with one build
  renderPalette();
  renderCombo();
  updatePassiveBadge();

  // events
  $("levelSlider").addEventListener("input", onLevelChange);
  $("autoRanksBtn").addEventListener("click", async () => {
    state.ranksTouched = false;
    await applyAutoRanks();
  });
  ["rankQ", "rankW", "rankE", "rankR"].forEach((id) =>
    $(id).addEventListener("change", () => {
      state.ranksTouched = true;
      state.ranks = readRanks();
    })
  );
  $("enemyPreset").addEventListener("change", onPresetChange);
  $("addBuildBtn").addEventListener("click", () => { addBuild(); });
  $("clearComboBtn").addEventListener("click", () => { state.combo = []; renderCombo(); });
  $("simulateBtn").addEventListener("click", simulate);
  $("closeOverlayBtn").addEventListener("click", closeOverlay);
  $("clearSlotBtn").addEventListener("click", () => { setSlot(null); });
  $("itemOverlay").addEventListener("click", (e) => {
    if (e.target === $("itemOverlay")) closeOverlay();
  });
  $("closeRunesBtn").addEventListener("click", closeRuneEditor);
  $("clearRunesBtn").addEventListener("click", clearRunes);
  $("runeOverlay").addEventListener("click", (e) => {
    if (e.target === $("runeOverlay")) closeRuneEditor();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    if (!$("itemOverlay").classList.contains("hidden")) closeOverlay();
    if (!$("runeOverlay").classList.contains("hidden")) closeRuneEditor();
  });
}

/* ================= config ================= */

function rankCap(ability, level) {
  if (ability === "R") return level >= 16 ? 3 : level >= 11 ? 2 : level >= 6 ? 1 : 0;
  return Math.min(5, Math.floor((level + 1) / 2));
}

function buildRankSelects() {
  for (const ab of ["Q", "W", "E", "R"]) {
    const sel = $("rank" + ab);
    sel.innerHTML = "";
    const cap = rankCap(ab, state.level);
    for (let i = 0; i <= cap; i++) {
      const o = document.createElement("option");
      o.value = i;
      o.textContent = i;
      sel.appendChild(o);
    }
  }
}

function readRanks() {
  return {
    Q: +$("rankQ").value, W: +$("rankW").value,
    E: +$("rankE").value, R: +$("rankR").value,
  };
}

async function applyAutoRanks() {
  const data = await (await fetch(`${API}/api/champion?level=${state.level}`)).json();
  state.ranks = data.default_ranks;
  buildRankSelects();
  for (const ab of ["Q", "W", "E", "R"]) $("rank" + ab).value = state.ranks[ab];
}

async function onLevelChange() {
  state.level = +$("levelSlider").value;
  $("levelValue").textContent = state.level;
  updatePassiveBadge();
  if (!state.ranksTouched) {
    await applyAutoRanks();
  } else {
    // clamp manual ranks to new caps
    buildRankSelects();
    for (const ab of ["Q", "W", "E", "R"]) {
      state.ranks[ab] = Math.min(state.ranks[ab], rankCap(ab, state.level));
      $("rank" + ab).value = state.ranks[ab];
    }
  }
  await onPresetChange();       // enemy scales with game state
}

function updatePassiveBadge() {
  const l = state.level;
  const form =
    l >= 16 ? "Transcendent — permanently Exalted, 625 range, fire waves" :
    l >= 11 ? "Aflame — fire waves while Exalted (5 Zeal stacks)" :
    l >= 6  ? "Arisen — ranged, 525 range" :
              "Zealous — stacking 6% AS per Zeal stack";
  $("passiveBadge").textContent = `Divine Ascent: ${form}`;
  // At 16+ Kayle is permanently Exalted — the Zeal pre-stack option is moot
  const zeal = $("optZeal");
  zeal.disabled = l >= 16;
  zeal.parentElement.title = l >= 16
    ? "Level 16+: Transcendent grants the full effects of Zealous permanently"
    : "";
  zeal.parentElement.style.opacity = l >= 16 ? ".45" : "1";
}

async function onPresetChange() {
  state.enemyPreset = $("enemyPreset").value;
  const data = await (await fetch(
    `${API}/api/enemy_preset?preset=${state.enemyPreset}&level=${state.level}`)).json();
  applyEnemyData(data);
}

function applyEnemyData(data) {
  $("enemyHp").value = data.hp;
  $("enemyCurrentHp").value = data.hp;
  $("enemyBonusHp").value = data.bonus_hp || 0;
  $("enemyArmor").value = data.armor;
  $("enemyMr").value = data.mr;
}

/* ================= builds ================= */

function defaultRunes() {
  return {
    primary: 8000,               // Precision
    secondary: 8200,             // Sorcery
    keystone: null,
    primarySlots: [null, null, null],
    secondarySlots: [],          // up to 2 of {row, id}, different rows
    shards: ["adaptive", "adaptive", "health"],
  };
}

function addBuild() {
  buildSeq += 1;
  state.builds.push({
    id: buildSeq,
    name: `Build ${buildSeq}`,
    items: [null, null, null, null, null, null],
    collapsed: false,
    runes: defaultRunes(),
  });
  renderBuilds();
  renderPalette();
}

function removeBuild(id) {
  state.builds = state.builds.filter((b) => b.id !== id);
  renderBuilds();
  renderPalette();
}

function buildCost(b) {
  return b.items.reduce((s, k) => s + (k ? ITEM_BY_KEY[k].cost : 0), 0);
}

function renderBuilds() {
  const box = $("buildsContainer");
  box.innerHTML = "";
  updateConditionalControls();
  if (!state.builds.length) {
    box.innerHTML = `<div class="empty-inline">No builds yet. Add a build to begin.</div>`;
    return;
  }
  for (const b of state.builds) {
    const card = document.createElement("div");
    card.className = "build-card" + (b.collapsed ? " collapsed" : "");

    const head = document.createElement("div");
    head.className = "build-header";
    head.innerHTML = `<span class="chev" aria-hidden="true">▼</span>`;
    const nameInput = document.createElement("input");
    nameInput.className = "build-name";
    nameInput.value = b.name;
    nameInput.addEventListener("click", (e) => e.stopPropagation());
    nameInput.addEventListener("input", () => (b.name = nameInput.value));
    const runeBtn = document.createElement("button");
    runeBtn.className = "rune-btn";
    runeBtn.title = "Edit runes";
    runeBtn.type = "button";
    const ks = b.runes && b.runes.keystone ? RUNE_BY_ID[b.runes.keystone] : null;
    const primIcon = b.runes ? PATH_BY_ID[b.runes.primary].icon : "";
    const secIcon = b.runes ? PATH_BY_ID[b.runes.secondary].icon : "";
    runeBtn.innerHTML = ks
      ? `<img src="${ks.icon}" decoding="async"><img src="${secIcon}" decoding="async" style="width:16px;height:16px">`
      : `<img src="${primIcon}" decoding="async"><span>Runes</span>`;
    runeBtn.addEventListener("click", (e) => { e.stopPropagation(); openRuneEditor(b.id); });

    const cost = document.createElement("span");
    cost.className = "build-cost";
    cost.textContent = `${buildCost(b).toLocaleString()} g`;
    const rm = document.createElement("button");
    rm.className = "remove-build";
    rm.type = "button";
    rm.textContent = "×";
    rm.title = "Remove build";
    rm.setAttribute("aria-label", `Remove ${b.name}`);
    rm.addEventListener("click", (e) => { e.stopPropagation(); removeBuild(b.id); });
    head.append(nameInput, runeBtn, cost, rm);
    head.addEventListener("click", () => { b.collapsed = !b.collapsed; renderBuilds(); });

    const body = document.createElement("div");
    body.className = "build-body";
    const slots = document.createElement("div");
    slots.className = "slots";
    b.items.forEach((key, idx) => {
      const slot = document.createElement("button");
      slot.type = "button";
      slot.className = "slot" + (key ? " filled" : "");
      slot.title = key ? ITEM_BY_KEY[key].name : "Add item";
      slot.innerHTML = key
        ? `<img src="${ITEM_BY_KEY[key].icon}" alt="${ITEM_BY_KEY[key].name}" decoding="async"
              onerror="if(!this.dataset.fallback){this.dataset.fallback='1';this.src='${ITEM_BY_KEY[key].icon_fallback}'}else{this.replaceWith(Object.assign(document.createElement('span'),{textContent:'${ITEM_BY_KEY[key].name.slice(0, 2)}',className:'plus'}))}">`
        : `<span class="plus">+</span>`;
      slot.addEventListener("click", () => openOverlay(b.id, idx));
      slots.appendChild(slot);
    });
    body.appendChild(slots);
    card.append(head, body);
    box.appendChild(card);
  }
}

function updateConditionalControls() {
  const darkSealField = $("darkSealStacksField");
  if (!darkSealField) return;
  const hasDarkSeal = state.builds.some((build) =>
    build.items.includes("dark_seal"));
  darkSealField.classList.toggle("hidden", !hasDarkSeal);
}

/* ================= item overlay ================= */

let overlayTarget = null;       // {buildId, slotIdx}

function openOverlay(buildId, slotIdx) {
  overlayTarget = { buildId, slotIdx };
  const grid = $("itemGrid");
  grid.innerHTML = "";
  for (const it of ITEMS) {
    const tile = document.createElement("button");
    tile.type = "button";
    tile.className = "item-tile";
    const statBits = Object.entries(it.stats).map(([k, v]) => {
      const label = { ad: "AD", ap: "AP", attack_speed: "AS%", ability_haste: "AH",
        ultimate_haste: "Ult AH", crit_chance: "Crit%", crit_damage_bonus: "Crit dmg%",
        health: "HP", armor: "Armor", mr: "MR", magic_pen_flat: "MPen",
        magic_pen_pct: "MPen%", armor_pen_pct: "Armor pen%", move_speed_flat: "MS",
        move_speed_pct: "MS%", tenacity: "Tenacity%", omnivamp: "Omnivamp" }[k] || k;
      const val = ["magic_pen_pct", "armor_pen_pct", "omnivamp"].includes(k)
        ? `${v * 100}%` : v;
      return `${val} ${label}`;
    }).join(" · ");
    tile.innerHTML = `
      <img src="${it.icon}" alt="${it.name}" loading="lazy" decoding="async"
        onerror="if(!this.dataset.fallback){this.dataset.fallback='1';this.src='${it.icon_fallback}'}else{this.style.visibility='hidden'}">
      <span class="iname">${it.name}</span>
      <span class="icost">${it.cost.toLocaleString()} g</span>
      <span class="istats">${statBits}</span>`;
    tile.title = it.passive_text;
    tile.addEventListener("click", () => setSlot(it.key));
    grid.appendChild(tile);
  }
  $("itemOverlay").classList.remove("hidden");
}

function setSlot(key) {
  if (!overlayTarget) return;
  const b = state.builds.find((x) => x.id === overlayTarget.buildId);
  if (b) b.items[overlayTarget.slotIdx] = key;
  closeOverlay();
  renderBuilds();
  renderPalette();
}

function closeOverlay() {
  overlayTarget = null;
  $("itemOverlay").classList.add("hidden");
}

/* ================= rune editor ================= */

let runeTarget = null;          // build id being edited

function openRuneEditor(buildId) {
  runeTarget = buildId;
  const b = state.builds.find((x) => x.id === buildId);
  if (!b.runes) b.runes = defaultRunes();
  $("runeOverlayTitle").textContent = `Runes — ${b.name}`;
  renderRuneEditor();
  $("runeOverlay").classList.remove("hidden");
}

function closeRuneEditor() {
  runeTarget = null;
  $("runeOverlay").classList.add("hidden");
  renderBuilds();
}

function clearRunes() {
  const b = state.builds.find((x) => x.id === runeTarget);
  if (b) b.runes = defaultRunes();
  renderRuneEditor();
}

function runeOptEl(r, selected, onClick) {
  const el = document.createElement("button");
  el.type = "button";
  el.className = "rune-opt" + (selected ? " selected" : "") + (r.dmg ? "" : " visual-only");
  el.title = r.note + (r.dmg && !r.has_math ? " — math pending" : "");
  el.setAttribute("aria-pressed", selected ? "true" : "false");
  el.setAttribute("aria-label", `${r.name}${selected ? ", selected" : ", not selected"}`);
  el.innerHTML = `<img src="${r.icon}" alt="${r.name}" loading="lazy" decoding="async">
    ${r.dmg ? '<span class="dmg-dot"></span>' : ""}<span>${r.name}</span>`;
  el.addEventListener("click", onClick);
  return el;
}

function renderRuneEditor() {
  const b = state.builds.find((x) => x.id === runeTarget);
  if (!b) return;
  const R = b.runes;
  const box = $("runeEditor");
  box.innerHTML = "";

  // ----- primary side -----
  const prim = document.createElement("div");
  prim.className = "rune-column primary-side";
  prim.innerHTML = `<div class="rune-side-title">Primary Path</div>`;
  const primTabs = document.createElement("div");
  primTabs.className = "path-tabs";
  for (const p of RUNES) {
    const tab = document.createElement("button");
    tab.type = "button";
    tab.className = "path-tab" + (p.id === R.primary ? " active" : "");
    tab.title = p.name;
    tab.setAttribute("aria-label", `${p.name} primary path`);
    tab.setAttribute("aria-pressed", p.id === R.primary ? "true" : "false");
    tab.innerHTML = `<img src="${p.icon}" alt="" loading="lazy" decoding="async">`;
    tab.addEventListener("click", () => {
      if (R.primary === p.id) return;
      R.primary = p.id;
      R.keystone = null;
      R.primarySlots = [null, null, null];
      if (R.secondary === p.id) {
        R.secondary = RUNES.find((x) => x.id !== p.id).id;
        R.secondarySlots = [];
      }
      renderRuneEditor();
    });
    primTabs.appendChild(tab);
  }
  prim.appendChild(primTabs);

  const primPath = PATH_BY_ID[R.primary];
  primPath.slots.forEach((slot, row) => {
    const rowEl = document.createElement("div");
    rowEl.className = "rune-row" + (row === 0 ? " keystone-row" : "");
    for (const r of slot) {
      const selected = row === 0 ? R.keystone === r.id : R.primarySlots[row - 1] === r.id;
      rowEl.appendChild(runeOptEl(r, selected, () => {
        if (row === 0) R.keystone = R.keystone === r.id ? null : r.id;
        else R.primarySlots[row - 1] = R.primarySlots[row - 1] === r.id ? null : r.id;
        renderRuneEditor();
      }));
    }
    prim.appendChild(rowEl);
  });

  // ----- secondary side -----
  const sec = document.createElement("div");
  sec.className = "rune-column secondary-side";
  sec.innerHTML = `<div class="rune-side-title">Secondary Path (pick 2, different rows)</div>`;
  const secTabs = document.createElement("div");
  secTabs.className = "path-tabs";
  for (const p of RUNES) {
    if (p.id === R.primary) continue;
    const tab = document.createElement("button");
    tab.type = "button";
    tab.className = "path-tab" + (p.id === R.secondary ? " active" : "");
    tab.title = p.name;
    tab.setAttribute("aria-label", `${p.name} secondary path`);
    tab.setAttribute("aria-pressed", p.id === R.secondary ? "true" : "false");
    tab.innerHTML = `<img src="${p.icon}" alt="" loading="lazy" decoding="async">`;
    tab.addEventListener("click", () => {
      if (R.secondary === p.id) return;
      R.secondary = p.id;
      R.secondarySlots = [];
      renderRuneEditor();
    });
    secTabs.appendChild(tab);
  }
  sec.appendChild(secTabs);

  const secPath = PATH_BY_ID[R.secondary];
  secPath.slots.forEach((slot, row) => {
    if (row === 0) return;       // no keystones in secondary
    const rowEl = document.createElement("div");
    rowEl.className = "rune-row";
    for (const r of slot) {
      const selected = R.secondarySlots.some((s) => s.id === r.id);
      rowEl.appendChild(runeOptEl(r, selected, () => {
        if (selected) {
          R.secondarySlots = R.secondarySlots.filter((s) => s.id !== r.id);
        } else {
          R.secondarySlots = R.secondarySlots.filter((s) => s.row !== row);
          if (R.secondarySlots.length >= 2) R.secondarySlots.shift();
          R.secondarySlots.push({ row, id: r.id });
        }
        renderRuneEditor();
      }));
    }
    sec.appendChild(rowEl);
  });

  // ----- stat shards -----
  if (!R.shards) R.shards = ["adaptive", "adaptive", "health"];
  const shardTitle = document.createElement("div");
  shardTitle.className = "rune-side-title shard-title";
  shardTitle.textContent = "Stat Shards";
  sec.appendChild(shardTitle);
  SHARDS.forEach((slot, row) => {
    const rowEl = document.createElement("div");
    rowEl.className = "rune-row shard-row";
    for (const opt of slot.options) {
      const el = document.createElement("button");
      el.type = "button";
      el.className = "rune-opt shard-opt"
        + (R.shards[row] === opt.key ? " selected" : "")
        + (opt.combat ? "" : " visual-only");
      el.title = opt.text;
      el.setAttribute("aria-pressed", R.shards[row] === opt.key ? "true" : "false");
      el.setAttribute("aria-label", `${opt.name}${R.shards[row] === opt.key ? ", selected" : ", not selected"}`);
      el.innerHTML = `<img src="${opt.icon}" alt="${opt.name}" loading="lazy" decoding="async">
        ${opt.combat ? '<span class="dmg-dot"></span>' : ""}<span>${opt.name}</span>`;
      el.addEventListener("click", () => { R.shards[row] = opt.key; renderRuneEditor(); });
      rowEl.appendChild(el);
    }
    sec.appendChild(rowEl);
  });

  box.append(prim, sec);
}

function selectedRuneIds(b) {
  if (!b.runes) return [];
  return [
    b.runes.keystone,
    ...b.runes.primarySlots,
    ...b.runes.secondarySlots.map((s) => s.id),
  ].filter(Boolean);
}

/* ================= combo ================= */

const BASE_ACTIONS = [
  { type: "AA", label: "AA", cls: "aa" },
  { type: "Q", label: "Q — Radiant Blast", cls: "q" },
  { type: "W", label: "W — Blessing", cls: "w" },
  { type: "E", label: "E — Starfire Spellblade", cls: "e" },
  { type: "R", label: "R — Judgment", cls: "r" },
];

function activeItemsInBuilds() {
  const keys = new Set();
  for (const b of state.builds) for (const k of b.items) if (k) keys.add(k);
  return [...keys].map((k) => ITEM_BY_KEY[k]).filter((it) => it.has_active);
}

function chipLabel(action) {
  if (action.type === "ITEM_ACTIVE") return ITEM_BY_KEY[action.item].name + " ⚡";
  return baseActionDef(action).label;
}

function chipClass(action) {
  if (action.type === "ITEM_ACTIVE") return "item-active";
  return baseActionDef(action).cls;
}

function baseActionDef(action) {
  return BASE_ACTIONS.find((a) =>
    a.type === action.type &&
    (a.timing || "instant") === (action.timing || "instant")
  );
}

function renderPalette() {
  const pal = $("comboPalette");
  pal.innerHTML = "";
  const actions = [
    ...BASE_ACTIONS.map((a) => ({
      type: a.type,
      ...(a.timing ? { timing: a.timing } : {}),
    })),
    ...activeItemsInBuilds().map((it) => ({ type: "ITEM_ACTIVE", item: it.key })),
  ];
  for (const action of actions) {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = `chip palette-chip ${chipClass(action)}`;
    chip.draggable = true;
    if (action.type === "ITEM_ACTIVE") {
      const img = document.createElement("img");
      img.src = ITEM_BY_KEY[action.item].icon;
      img.loading = "lazy";
      img.decoding = "async";
      img.onerror = () => (img.style.display = "none");
      chip.appendChild(img);
    }
    chip.append(chipLabel(action));
    chip.title = "Click to append · drag into the sequence";
    chip.addEventListener("click", () => { state.combo.push({ ...action }); renderCombo(); });
    chip.addEventListener("dragstart", (e) => {
      e.dataTransfer.setData("text/plain", JSON.stringify({ from: "palette", action }));
    });
    pal.appendChild(chip);
  }
}

function renderCombo() {
  const track = $("comboTrack");
  track.innerHTML = "";
  if (!state.combo.length) {
    track.innerHTML = `<span class="combo-empty">Add an action to begin the combo.</span>`;
  }
  state.combo.forEach((action, idx) => {
    const chip = document.createElement("span");
    chip.className = `chip ${chipClass(action)}`;
    chip.draggable = true;
    if (action.type === "ITEM_ACTIVE") {
      const img = document.createElement("img");
      img.src = ITEM_BY_KEY[action.item].icon;
      img.loading = "lazy";
      img.decoding = "async";
      img.onerror = () => (img.style.display = "none");
      chip.appendChild(img);
    }
    chip.append(shortLabel(action));
    const x = document.createElement("span");
    x.className = "x";
    x.textContent = "✕";
    x.addEventListener("click", (e) => {
      e.stopPropagation();
      state.combo.splice(idx, 1);
      renderCombo();
    });
    chip.appendChild(x);

    chip.addEventListener("dragstart", (e) => {
      e.dataTransfer.setData("text/plain", JSON.stringify({ from: "track", index: idx }));
    });
    chip.addEventListener("dragover", (e) => { e.preventDefault(); chip.classList.add("drag-over"); });
    chip.addEventListener("dragleave", () => chip.classList.remove("drag-over"));
    chip.addEventListener("drop", (e) => {
      e.preventDefault();
      e.stopPropagation();
      chip.classList.remove("drag-over");
      handleDrop(e, idx);
    });
    track.appendChild(chip);
  });

  // `renderCombo()` runs after every edit. Assigning these handlers replaces
  // the previous pair; addEventListener would accumulate another drop handler
  // on the persistent track element every time and duplicate dragged actions.
  track.ondragover = (e) => e.preventDefault();
  track.ondrop = (e) => {
    e.preventDefault();
    handleDrop(e, state.combo.length);
  };
}

function shortLabel(action) {
  if (action.type === "ITEM_ACTIVE") {
    const name = ITEM_BY_KEY[action.item].name;
    return name.split(" ")[0] + " ⚡";
  }
  if (action.type === "E" && action.timing === "delayed") return "E wait";
  return action.type;
}

function handleDrop(e, targetIdx) {
  let data;
  try { data = JSON.parse(e.dataTransfer.getData("text/plain")); } catch { return; }
  if (data.from === "palette") {
    state.combo.splice(targetIdx, 0, { ...data.action });
  } else if (data.from === "track") {
    const [moved] = state.combo.splice(data.index, 1);
    if (data.index < targetIdx) targetIdx -= 1;
    state.combo.splice(targetIdx, 0, moved);
  }
  renderCombo();
}

/* ================= simulate & results ================= */

async function simulate() {
  const btn = $("simulateBtn");
  btn.disabled = true;
  btn.textContent = "Calculating…";
  try {
    const payload = {
      level: state.level,
      ability_ranks: state.ranks,
      builds: state.builds.map((b) => ({
        name: b.name,
        items: b.items.filter(Boolean),
        runes: {
          primary: b.runes.primary,
          secondary: b.runes.secondary,
          selected: selectedRuneIds(b),
          shards: b.runes.shards || [],
        },
      })),
      enemy: {
        hp: +$("enemyHp").value || 1,
        current_hp: $("enemyCurrentHp").value === ""
          ? (+$("enemyHp").value || 1)
          : +$("enemyCurrentHp").value,
        bonus_hp: +$("enemyBonusHp").value || 0,
        armor: +$("enemyArmor").value || 0,
        mr: +$("enemyMr").value || 0,
      },
      combo: state.combo,
      options: {
        pre_stacked_zeal: $("optZeal").checked,
        pre_stacked_rageblade: $("optRageblade").checked,
        pre_stacked_yun_tal: $("optYunTal").checked,
        game_time_min: +$("gameTime").value || 0,
        kayle_hp_pct: +$("kayleHp").value || 100,
        dh_souls: +$("dhSouls").value || 0,
        dark_seal_stacks: +$("darkSealStacks").value || 0,
        legend_stacks: +$("legendStacks").value || 0,
        relentless_stacks: +$("relentlessStacks").value || 0,
        fleet_starts_energized: $("fleetEnergized").checked,
        assume_river: $("assumeRiver").checked,
      },
    };
    const res = await fetch(`${API}/api/simulate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    renderResults(data.results);
  } catch (err) {
    $("resultsContainer").innerHTML = `<p class="warn">Simulation failed: ${err.message}</p>`;
  } finally {
    btn.disabled = false;
    btn.textContent = "Calculate damage";
  }
}

function renderResults(results) {
  const box = $("resultsContainer");
  box.innerHTML = "";
  if (!results.length) {
    box.innerHTML = `<div class="empty-state"><span class="empty-icon" aria-hidden="true">◇</span><strong>No builds to compare</strong><span>Add at least one build and calculate again.</span></div>`;
    return;
  }
  const bestDps = Math.max(...results.map((r) => r.dps));
  const fmtDamage = (value) => Number(value).toLocaleString(undefined, {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  });

  for (const r of results) {
    const card = document.createElement("div");
    const isBest = r.dps === bestDps && results.length > 1;
    card.className = "result-card" + (isBest ? " is-best" : "");

    const icons = r.items.map((k) =>
      `<img src="${ITEM_BY_KEY[k].icon}" title="${ITEM_BY_KEY[k].name}" loading="lazy" decoding="async"
        onerror="if(!this.dataset.fallback){this.dataset.fallback='1';this.src='${ITEM_BY_KEY[k].icon_fallback}'}else{this.style.visibility='hidden'}">`).join("");

    const t = r.totals;
    const total = Math.max(r.total_damage, 0.001);
    const pct = (x) => (100 * x / total).toFixed(1);

    const hpPct = (100 * r.enemy.remaining_hp / r.enemy.max_hp).toFixed(1);

    const bySource = {};
    for (const e of r.events) {
      if (e.type === "note") continue;
      const k = `${e.source}|${e.type}`;
      bySource[k] = bySource[k] || { source: e.source, type: e.type, dealt: 0, hits: 0 };
      bySource[k].dealt += e.dealt;
      bySource[k].hits += 1;
    }
    const rows = Object.values(bySource).sort((a, b) => b.dealt - a.dealt).map((s) => `
      <tr>
        <td class="type-${s.type}">${s.source}</td>
        <td>${s.hits}</td>
        <td>${fmtDamage(s.dealt)}</td>
        <td>${s.type === "heal" ? "—" : pct(s.dealt) + "%"}</td>
      </tr>`).join("");

    // execution-order timeline (events arrive chronologically; stable sort by t)
    const timeline = r.events
      .map((e, i) => ({ ...e, i }))
      .sort((a, b) => (a.t - b.t) || (a.i - b.i))
      .map((e) => e.type === "note"
        ? `<tr><td>${e.t.toFixed(2)}s</td><td colspan="5" class="type-heal">${e.source}</td></tr>`
        : `<tr>
            <td>${e.t.toFixed(2)}s</td>
            <td class="type-${e.type}">${e.source}</td>
            <td>${e.type}</td>
            <td>${e.raw === undefined ? "—" : fmtDamage(e.raw)}</td>
            <td>${e.effective_resistance === undefined || e.effective_resistance === null
              ? "—" : fmtDamage(e.effective_resistance)}</td>
            <td>${fmtDamage(e.dealt)}</td>
          </tr>`).join("");

    card.innerHTML = `
      <div class="result-card-head">
        <div class="result-title">
          <h3>${r.build_name}</h3>
          <span class="result-icons">${icons}</span>
        </div>
        ${isBest ? '<span class="best-badge">Top DPS</span>' : ""}
      </div>
      <div class="result-metrics">
        <div class="result-metric"><span>Total damage</span><strong>${fmtDamage(r.total_damage)}</strong></div>
        <div class="result-metric"><span>DPS</span><strong>${fmtDamage(r.dps)}</strong></div>
        <div class="result-metric" title="Highest applied damage in any rolling one-second interval"><span>1s burst</span><strong>${fmtDamage(r.burst_damage_1s)}</strong></div>
      </div>
      <div class="damage-composition">
        <div class="bar" title="Physical ${pct(t.physical)}% · Magic ${pct(t.magic)}% · True ${pct(t.true)}%">
          <div class="seg-physical" style="width:${pct(t.physical)}%"></div>
          <div class="seg-magic" style="width:${pct(t.magic)}%"></div>
          <div class="seg-true" style="width:${pct(t.true)}%"></div>
        </div>
        <div class="bar-legend">
          <span><span class="dot" style="background:var(--physical)"></span>Physical ${fmtDamage(t.physical)}</span>
          <span><span class="dot" style="background:var(--magic)"></span>Magic ${fmtDamage(t.magic)}</span>
          <span><span class="dot" style="background:var(--true)"></span>True ${fmtDamage(t.true)}</span>
        </div>
      </div>
      <div class="stat-rows">
        <span class="k">Pre-mitigation</span><span class="v">${fmtDamage(r.pre_mitigation_total)} (−${r.mitigated_pct}%)</span>
        <span class="k">Damage model</span><span class="v">Full precision</span>
        <span class="k">Attacks / duration</span><span class="v">${r.attack_count} in ${r.duration.toFixed(2)}s</span>
        <span class="k">Peak 1s window</span>
        <span class="v">${r.burst_window_1s.start !== null
          ? r.burst_window_1s.start.toFixed(2) + "–" + r.burst_window_1s.end.toFixed(2) + "s"
          : "—"}</span>
        <span class="k">Kill time</span><span class="v">${r.kill_time !== null ? r.kill_time.toFixed(2) + "s" : "—"}</span>
        <span class="k">Dmg per 1k gold</span>
        <span class="v">${r.damage_per_1k_gold !== null ? r.damage_per_1k_gold.toLocaleString() : "—"} (${r.gold_cost.toLocaleString()} g)</span>
        <span class="k">Healing</span><span class="v type-heal">${r.healing.toLocaleString()}</span>
        <span class="k">Attack speed</span><span class="v">${r.stats.attack_speed_final}</span>
        <span class="k">AD / AP</span><span class="v">${r.stats.total_ad} / ${r.stats.ap}</span>
        <span class="k">Movement speed</span><span class="v">${r.stats.movement_speed ?? "—"}</span>
        ${r.stats.swiftmarch_adaptive_force > 0
          ? `<span class="k">Swiftmarch force</span><span class="v">${r.stats.swiftmarch_adaptive_force} adaptive</span>`
          : ""}
        <span class="k">Magic pen</span><span class="v">${r.stats.magic_pen_pct}% + ${r.stats.magic_pen_flat}</span>
        <span class="k">Armor pen</span><span class="v">${r.stats.armor_pen_pct}%</span>
        <span class="k">Crit model</span><span class="v">${r.stats.crit_chance}% at ${r.stats.crit_damage}% damage (expected)</span>
        <span class="k">Enemy HP left</span>
        <span class="v">${r.enemy.killed ? "DEAD" : fmtDamage(r.enemy.remaining_hp) + ` (${hpPct}%)`}</span>
      </div>
      <div class="hp-bar"><div class="hp-fill" style="width:${hpPct}%"></div></div>
      ${r.warnings.map((w) => `<p class="warn">Warning: ${w}</p>`).join("")}
      <details class="breakdown" open>
        <summary>Damage timeline (execution order)</summary>
        <div class="timeline-scroll">
        <table>
          <tr><th>Time</th><th>Source</th><th>Type</th><th>Raw</th><th>Eff. resist</th><th>Applied</th></tr>
          ${timeline}
        </table>
        </div>
      </details>
      <details class="breakdown">
        <summary>Totals by source</summary>
        <table>
          <tr><th>Source</th><th>Hits</th><th>Amount</th><th>Share</th></tr>
          ${rows}
        </table>
      </details>`;
    box.appendChild(card);
  }
}

init();
