"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const {
  buildSnapshotModel,
  formatNumber,
  snapshotDimensions,
} = require("../frontend/snapshot.js");

function result(name, {
  dps = 100,
  burst = 180,
  damage = 500,
  remainingHp = 500,
} = {}) {
  return {
    build_name: name,
    items: ["nashors_tooth"],
    total_damage: damage,
    dps,
    burst_damage_1s: burst,
    totals: { physical: 120, magic: 350, true: 30 },
    duration: 5,
    attack_count: 6,
    kill_time: null,
    gold_cost: 3000,
    stats: {
      attack_speed_final: 1.25,
      total_ad: 100,
      ap: 200,
      crit_chance: 25,
      crit_damage: 175,
    },
    enemy: {
      max_hp: 1000,
      remaining_hp: remainingHp,
      killed: remainingHp === 0,
    },
  };
}

const payload = {
  level: 11,
  ability_ranks: { Q: 3, W: 1, E: 5, R: 2 },
  builds: [{
    name: "AP build",
    items: ["nashors_tooth"],
    runes: {
      primary: "precision",
      secondary: "sorcery",
      selected: ["lethal_tempo"],
      shards: ["attack_speed", "adaptive", "health_scaling"],
    },
  }],
  enemy: {
    hp: 1000,
    current_hp: 1000,
    armor: 50,
    mr: 40,
  },
  combo: [
    { type: "AA" },
    { type: "ITEM_ACTIVE", item: "hextech_gunblade" },
    { type: "WAIT", duration: 0.5 },
    { type: "E" },
  ],
  options: {
    game_time_min: 25,
    kayle_hp_pct: 100,
    legend_stacks: 10,
    dark_seal_stacks: 0,
    dh_souls: 0,
    use_e_for_aa_cancel: true,
  },
};

test("snapshot model contains readable setup and build results", () => {
  const model = buildSnapshotModel({
    results: [result("AP build")],
    payload,
    itemByKey: {
      nashors_tooth: {
        name: "Nashor's Tooth",
        icon: "icons/items/nashors_tooth.png",
        icon_fallback: "fallback.png",
      },
      hextech_gunblade: { name: "Hextech Gunblade" },
    },
  });

  assert.equal(model.level, 11);
  assert.equal(model.ranks, "Q3 · W1 · E5 · R2");
  assert.match(model.target, /1,000 \/ 1,000 HP/);
  assert.equal(
    model.combo,
    "AA → Hextech Gunblade active → Wait 0.5s → E",
  );
  assert.deepEqual(model.cards[0].items, [{
    key: "nashors_tooth",
    name: "Nashor's Tooth",
    icon: "icons/items/nashors_tooth.png",
    iconFallback: "fallback.png",
  }]);
  assert.equal(model.cards[0].remainingHpPct, 50);
});

test("comparison leaders and multi-row image dimensions are deterministic", () => {
  const results = [
    result("A", { dps: 120, burst: 180 }),
    result("B", { dps: 100, burst: 220 }),
    result("C", { dps: 90, burst: 170 }),
  ];
  const builds = results.map(({ build_name: name }) => ({
    name,
    items: [],
    runes: { selected: [] },
  }));
  const model = buildSnapshotModel({
    results,
    payload: { ...payload, builds },
  });

  assert.equal(model.cards[0].topDps, true);
  assert.equal(model.cards[1].topBurst, true);
  assert.equal(model.cards[2].topDps, false);
  assert.deepEqual(snapshotDimensions(3), {
    width: 1400,
    height: 986,
    columns: 2,
  });
});

test("snapshot helpers reject missing results and format safely", () => {
  assert.throws(
    () => buildSnapshotModel({ results: [], payload }),
    /Calculate at least one build/,
  );
  assert.equal(formatNumber(1234.567), "1,234.57");
  assert.equal(formatNumber("not-a-number"), "0");
});
