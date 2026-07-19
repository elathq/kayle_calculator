"""Kayle combat simulation engine.

Executes an ordered combo (list of actions) against an enemy and returns a
full damage timeline. Respects:
  - total AS = base_as + as_ratio * sum(bonus AS %) / 100, capped at 2.50
    (Hail of Blades may exceed the cap while its stacks last)
  - on-hit layering: total AD + item on-hits + E passive + fire wave + spellblade
  - Zeal stacking (6%/stack, Exalted at 5), Rageblade Seething/Phantom Hit
  - Spellblade priming/consumption with 1.5s internal cooldown
  - Q's 15% armor/MR shred window, % then flat magic pen, Shadowflame crit
  - Enemy HP tracking (missing-health E active, Shadowflame crit below 40%)
  - Runes: stat runes (Alacrity, Gathering Storm, Absolute Focus, Jack of All
    Trades), stacking keystones (PTA, Lethal Tempo, Conqueror, HoB, Grasp),
    proc keystones (Electrocute, Dark Harvest, Aery, Comet, Deathfire Touch,
    First Strike), amps (Coup de Grace, Cut Down, Last Stand, Axiom Arcanist)
    and Cheap Shot / Scorch. Adaptive effects deal physical if bonus AD > AP,
    otherwise magic (evaluated from item stats).
"""

from .data.kayle_data import (
    KAYLE_AS, PASSIVE, Q, W, E, R,
    kayle_stats_at, lerp_by_level, default_ability_ranks,
)
from .data.items_data import ITEMS
from .data.runes_data import RUNE_MATH, SHARD_VALUES
from .damage import effective_resistance, resolve_damage

AS_CAP = 2.5
SPELLBLADE_CD = 1.5
MID_ROLE_QUEST_STAT_MULTIPLIER = 1.08
FLEET_VISUAL_SYNC_DELAY = 0.1


class Simulation:
    def __init__(self, level, ranks, item_keys, enemy, combo, options):
        self.level = level
        self.ranks = ranks
        self.enemy_max_hp = float(enemy["hp"])
        requested_enemy_hp = float(enemy.get("current_hp", self.enemy_max_hp))
        self.enemy_hp = max(0.0, min(self.enemy_max_hp, requested_enemy_hp))
        self.enemy_bonus_hp = max(0.0, float(enemy.get("bonus_hp", 0.0)))
        self.enemy_armor = float(enemy["armor"])
        self.enemy_mr = float(enemy["mr"])
        self.combo = combo
        self.options = options or {}
        self.rune_ids = set(self.options.get("rune_ids") or [])
        self.warnings = []
        self.events = []           # {t, source, type, pre, dealt}
        self.scheduled = []        # [t, fn] list; processed in time order
        self.time = 0.0
        self.end_time = 0.0
        self.heal_total = 0.0
        self.damage_totals = {"physical": 0.0, "magic": 0.0, "true": 0.0}
        self.damage_instances = []  # full-precision (timestamp, applied damage)
        self.pre_mitigation_total = 0.0
        self.cooldowns = {}        # action -> ready_at
        self.cooldown_errors = []  # invalid Q/W/E/R uses with combo indexes
        self.current_action_index = None
        self.damage_frame_time = None
        self.damage_frame_start_hp = self.enemy_hp

        # rune-related user inputs
        self.game_time_min = float(self.options.get("game_time_min", 25))
        self.kayle_hp_pct = float(self.options.get("kayle_hp_pct", 100))
        self.dh_souls = int(self.options.get("dh_souls", 0))
        self.legend_stacks = int(self.options.get("legend_stacks", 10))
        self.relentless_stacks = max(
            0, min(5, int(self.options.get("relentless_stacks", 0))))
        self.dark_seal_stacks = max(
            0, min(10, int(self.options.get("dark_seal_stacks", 0))))
        self.fleet_starts_energized = bool(
            self.options.get("fleet_starts_energized", True))
        self.assume_river = bool(self.options.get("assume_river", False))
        self.items = self._resolve_items(item_keys)
        self._compute_stats()
        self._init_state()
        self._refresh_dynamic_stats(self.time)

    def _rune(self, rid):
        return RUNE_MATH[rid] if rid in self.rune_ids and rid in RUNE_MATH else None

    @property
    def is_melee(self):
        return self.level < PASSIVE["arisen_level"]

    def _lerp(self, lo, hi):
        # Rune data stores exact level-1/18 references and keeps the same
        # per-level slope through the top-quest levels 19 and 20.
        return lerp_by_level(lo, hi, self.level, cap_lvl=20)

    # ---------- setup ----------

    def _resolve_items(self, keys):
        seen, out = set(), []
        limited_groups = {
            "spellblade": ("Spellblade", None),
            "blight": ("Blight", None),
            "fatality": ("Fatality", None),
            "boots": ("Boots", None),
            "starter": ("Starter", None),
        }
        for k in keys:
            if not k or k not in ITEMS:
                continue
            if k in seen:
                self.warnings.append(f"Duplicate {ITEMS[k]['name']} ignored (Limited to 1).")
                continue
            it = ITEMS[k]
            if self.level > 18 and "mid_role_quest" in it.get("tags", []):
                self.warnings.append(
                    f"{it['name']} ignored: the mid role quest is incompatible "
                    "with the top role quest required for levels 19–20.")
                continue
            item_groups = [g for g in limited_groups if g in it.get("tags", [])]
            conflict = next(
                (g for g in item_groups if limited_groups[g][1] is not None), None)
            if conflict:
                label, taken = limited_groups[conflict]
                self.warnings.append(
                    f"{it['name']} ignored: Limited to 1 {label} item "
                    f"({ITEMS[taken]['name']} already equipped).")
                continue
            for group in item_groups:
                label, _ = limited_groups[group]
                limited_groups[group] = (label, k)
            seen.add(k)
            out.append(k)
        return out

    def _compute_stats(self):
        base = kayle_stats_at(self.level)
        self.base_ad = base["base_ad"]
        self.level_bonus_as = base["level_bonus_as"]
        self.kayle_max_hp = base["hp"]

        ad = ap = as_pct = hp = haste = ultimate_haste = flat_pen = omnivamp = 0.0
        life_steal = slow_resist = 0.0
        flat_ms = pct_ms = 0.0
        pct_pen = armor_pct_pen = 0.0
        crit_chance = crit_damage_bonus = 0.0
        ap_mult = 1.0
        stat_types = set()
        for k in self.items:
            it = ITEMS[k]
            s = it["stats"]
            stat_types.update(s.keys())
            ad += s.get("ad", 0)
            ap += s.get("ap", 0)
            as_pct += s.get("attack_speed", 0)
            hp += s.get("health", 0)
            haste += s.get("ability_haste", 0)
            ultimate_haste += s.get("ultimate_haste", 0)
            flat_pen += s.get("magic_pen_flat", 0)
            pct_pen = 1 - (1 - pct_pen) * (1 - s.get("magic_pen_pct", 0))
            armor_pct_pen = 1 - (1 - armor_pct_pen) * (1 - s.get("armor_pen_pct", 0))
            omnivamp += s.get("omnivamp", 0)
            life_steal += s.get("life_steal", 0)
            slow_resist += s.get("slow_resist", 0)
            flat_ms += s.get("move_speed_flat", 0)
            pct_ms += s.get("move_speed_pct", 0)
            crit_chance += s.get("crit_chance", 0)
            crit_damage_bonus += s.get("crit_damage_bonus", 0)
            if "dark_seal" in it.get("tags", []):
                ap += it["glory_ap_per_stack"] * min(
                    it["glory_max_stacks"], self.dark_seal_stacks)
            if "rabadon" in it["tags"]:
                ap_mult = it["ap_multiplier"]

        self.kayle_max_hp += hp
        # Adaptive resolution: compare the build's pre-adaptive AD/AP sources.
        # Practice Tool confirms that a zero/zero tie resolves to AD on Kayle
        # (e.g. Rapid Firecannon + one adaptive shard displays 98 AD / 0 AP).
        self.adaptive_physical = ad >= ap * ap_mult

        # --- stat shards (adaptive follows the item-based resolution) ---
        extra_ad = extra_ap = 0.0
        for shard in (self.options.get("shards") or []):
            if shard == "adaptive":
                if self.adaptive_physical:
                    extra_ad += SHARD_VALUES["adaptive_ad"]
                else:
                    extra_ap += SHARD_VALUES["adaptive_ap"]
            elif shard == "attack_speed":
                as_pct += SHARD_VALUES["attack_speed"]
            elif shard == "haste":
                haste += SHARD_VALUES["haste"]
            elif shard == "move_speed":
                pct_ms += SHARD_VALUES["move_speed_pct"]
            elif shard == "health":
                hp += SHARD_VALUES["health"]
                self.kayle_max_hp += SHARD_VALUES["health"]
            elif shard == "health_scaling":
                # The top-lane role quest raises the level cap to 20. Scaling
                # health reaches its 200 HP endpoint at level 20, not level 18.
                shp = lerp_by_level(
                    SHARD_VALUES["health_scaling_lo"],
                    SHARD_VALUES["health_scaling_hi"],
                    self.level,
                    hi_lvl=20,
                )
                hp += shp
                self.kayle_max_hp += shp

        # --- stat runes (adaptive grants follow the item-based resolution) ---
        if (m := self._rune(8236)):    # Gathering Storm
            tier = min(len(m["ad"]) - 1, int(self.game_time_min // 10))
            extra_ad += m["ad"][tier] if self.adaptive_physical else 0
            extra_ap += 0 if self.adaptive_physical else m["ap"][tier]
        if (m := self._rune(8233)):    # Absolute Focus
            if self.kayle_hp_pct > m["hp_threshold"] * 100:
                if self.adaptive_physical:
                    extra_ad += self._lerp(m["ad_lo"], m["ad_hi"])
                else:
                    extra_ap += self._lerp(m["ap_lo"], m["ap_hi"])
        if (m := self._rune(8232)) and self.assume_river:  # Waterwalking
            flat_ms += m["flat_ms"]
            if self.adaptive_physical:
                extra_ad += self._lerp(m["ad_lo"], m["ad_hi"])
            else:
                extra_ap += self._lerp(m["ap_lo"], m["ap_hi"])
        if (m := self._rune(8316)):    # Jack of All Trades
            jack = len(stat_types)
            haste += m["haste_per"] * jack
            if jack >= 10:
                extra_ad += m["ad_10"] if self.adaptive_physical else 0
                extra_ap += 0 if self.adaptive_physical else m["ap_10"]
            elif jack >= 5:
                extra_ad += m["ad_5"] if self.adaptive_physical else 0
                extra_ap += 0 if self.adaptive_physical else m["ap_5"]
        if (m := self._rune(9104)):    # Legend: Alacrity
            as_pct += m["base"] + m["per_stack"] * min(m["max_stacks"], self.legend_stacks)
        if (m := self._rune(8210)):    # Transcendence (ability haste at 5/8)
            haste += (m["lvl5"] if self.level >= 5 else 0)
            haste += (m["lvl8"] if self.level >= 8 else 0)
        self.basic_haste = 0.0         # applies to Q/W/E cooldowns only
        if (m := self._rune(9105)):    # Legend: Haste
            self.basic_haste = min(m["max"], m["per_stack"] * self.legend_stacks)

        # Void Infusion reads every source of bonus health, including shards,
        # before AP multipliers such as Rabadon's are applied.
        if "riftmaker" in self.items:
            extra_ap += (ITEMS["riftmaker"]["void_infusion_bonus_hp_ratio"]
                         * hp)

        # Slightly Magical Boots keep their +10 flat movement speed after
        # upgrading, including a role-quest upgrade into Swiftmarch.
        if ((m := self._rune(8304))
                and any("boots" in ITEMS[k].get("tags", []) for k in self.items)):
            flat_ms += m["flat_ms"]

        self.mid_role_quest_completed = any(
            "mid_role_quest" in ITEMS[k].get("tags", []) for k in self.items)
        self.role_quest_stat_multiplier = (
            MID_ROLE_QUEST_STAT_MULTIPLIER
            if self.mid_role_quest_completed else 1.0)
        self.static_bonus_ad = (ad + extra_ad) * self.role_quest_stat_multiplier
        self.static_ap_pre_mult = (ap + extra_ap) * self.role_quest_stat_multiplier
        self.bonus_ad = self.static_bonus_ad
        self.total_ad = self.base_ad + self.bonus_ad
        # Magical Opus multiplies ALL ability power, including rune-granted AP
        # ("stacks recursively with other sources of ability power").
        self.ap_mult = ap_mult
        self.ap = self.static_ap_pre_mult * ap_mult
        self.item_as = as_pct
        self.bonus_hp = hp
        self.haste = haste
        self.ultimate_haste = ultimate_haste
        self.flat_pen = flat_pen
        self.pct_pen = pct_pen
        self.armor_pct_pen = armor_pct_pen
        self.crit_chance = min(1.0, crit_chance / 100.0)
        self.base_crit_chance = self.crit_chance
        self.crit_damage = KAYLE_AS["crit_damage"] + crit_damage_bonus / 100.0
        self.omnivamp = omnivamp
        self.life_steal = life_steal
        self.slow_resist = slow_resist
        self.flat_move_speed = flat_ms
        self.percent_move_speed = pct_ms

        self.has_rageblade = any("rageblade" in ITEMS[k]["tags"] for k in self.items)
        self.has_shadowflame_crit = any(
            "shadowflame_crit" in ITEMS[k]["tags"] for k in self.items)
        self.has_rylai = "rylais_crystal_scepter" in self.items
        self.has_swiftmarch = "swiftmarch" in self.items
        self.has_cosmic_drive = "cosmic_drive" in self.items
        self.has_stormsurge = "stormsurge" in self.items
        self.has_riftmaker = "riftmaker" in self.items
        self.has_kraken = "kraken_slayer" in self.items
        self.has_terminus = "terminus" in self.items
        self.has_bloodletter = "bloodletters_curse" in self.items
        self.has_hexoptics = "hexoptics_c44" in self.items
        self.has_rapid_firecannon = "rapid_firecannon" in self.items
        self.has_experimental_hexplate = "experimental_hexplate" in self.items
        self.has_yun_tal = "yun_tal_wildarrows" in self.items
        self.has_navori = "navori_flickerblade" in self.items
        self.has_giant_slayer = "lord_dominiks_regards" in self.items
        self.has_statikk = "statikk_shiv" in self.items
        self.has_stormrazor = "stormrazor" in self.items
        self.has_fiendhunter = "fiendhunter_bolts" in self.items
        self.spellblade_key = next(
            (k for k in self.items if "spellblade" in ITEMS[k]["tags"]), None)

    def _init_state(self):
        transcendent = self.level >= PASSIVE["transcendent_level"]
        pre_zeal = self.options.get("pre_stacked_zeal", True)
        self.zeal = PASSIVE["zeal_max_stacks"] if (transcendent or pre_zeal) else 0
        self.seething = 0
        self.phantom = 0
        if self.has_rageblade and self.options.get("pre_stacked_rageblade", False):
            self.seething = ITEMS["guinsoos_rageblade"]["seething"]["max_stacks"]
        self.spellblade_primed = False
        self.spellblade_cd_until = -1e9
        self.dd_repeat_used = False
        self.shred_until = -1.0
        self.slowed_until = -1.0
        self.w_ms_until = -1.0
        self.cosmic_ms_until = -1.0
        self.stormsurge_ms_until = -1.0
        self.stormrazor_ms_until = -1.0
        self.hexplate_overdrive_until = -1.0
        self.hexplate_ready_at = 0.0
        self.yun_tal_flurry_until = -1.0
        self.yun_tal_flurry_ready_at = 0.0
        self.yun_tal_bonus_crit = (
            ITEMS["yun_tal_wildarrows"]["practice_makes_lethal"]["max_crit_chance"]
            if (self.has_yun_tal
                and self.options.get("pre_stacked_yun_tal", True))
            else 0.0
        )
        self.crit_chance = min(
            1.0, self.base_crit_chance + self.yun_tal_bonus_crit / 100.0)
        self.swiftmarch_force = 0.0
        self.current_movement_speed = float(KAYLE_AS["ms"])
        self.in_combat = False
        self.combat_started_at = None
        self.fleet_ready = self.fleet_starts_energized
        self.fleet_ms_until = -1.0
        self.fleet_pending = False
        self.fleet_pending_at = -1.0
        self.fleet_pending_until = -1.0
        self.stormraider_damage = []
        self.stormraider_ms_until = -1.0
        self.stormraider_cd_until = -1e9
        self.stormsurge_damage = []
        self.stormsurge_cd_until = -1e9
        self.dynamic_conq_ad = 0.0
        self.dynamic_conq_ap_pre_mult = 0.0

        # stateful item effects
        self.kraken_stacks = 0
        self.kraken_last_hit = -1e9
        self.terminus_next_dark = False       # Juxtaposition starts with Light
        self.terminus_dark_stacks = 0
        self.terminus_dark_until = -1.0
        self.bloodletter_stacks = []
        self.bloodletter_last_application = {}
        self.bloodletter_frame_time = None
        self.bloodletter_frame_stack_count = 0
        self.statikk_ready = self.fleet_starts_energized and self.has_statikk
        self.stormrazor_ready = self.fleet_starts_energized and self.has_stormrazor
        self.rapid_firecannon_ready = (
            self.fleet_starts_energized and self.has_rapid_firecannon)
        self.fiendhunter_attacks = 0
        self.fiendhunter_until = -1.0
        self.fiendhunter_ready_at = 0.0
        self.current_attack_crit_multiplier = 1.0
        self.current_attack_fiendhunter = False

        # rune state
        self.pta_stacks = 0
        self.pta_amp_from = None   # amp starts strictly AFTER the proc's frame
        self.kill_time = None
        self.attack_count = 0
        self.lt_stacks = 0
        self.conq_stacks = 0
        self.conq_healed = False
        self.hob_stacks = 0
        self.hob_triggered = False
        self.hob_resets_used = 0
        self.electro_times = []
        self.electro_cd_until = -1e9
        self.dh_cd_until = -1e9
        self.aery_ready_at = -1e9
        self.comet_cd_until = -1e9
        self.scorch_cd_until = -1e9
        self.cheap_cd_until = -1e9
        self.fs_until = None       # None = not triggered yet
        self.grasp_consumed_at = -1e9  # stack generation restart point
        self.dft_until = -1.0
        self.dft_started = -1.0
        self.dft_ticking = False

    # ---------- movement speed and dynamic Swiftmarch stats ----------

    @staticmethod
    def _softcap_movement_speed(raw_speed):
        if raw_speed > 490.0:
            return 475.0 + (raw_speed - 490.0) * 0.5
        if raw_speed > 415.0:
            return 415.0 + (raw_speed - 415.0) * 0.8
        if raw_speed < 220.0:
            return 220.0 - (220.0 - raw_speed) * 0.5
        return raw_speed

    def _movement_speed_for_ap(self, at_time, ap):
        flat_bonus = self.flat_move_speed
        additive_pct = self.percent_move_speed
        multiplicative_bonuses = []

        # Relentless Hunter is available only before Kayle deals the first
        # damage instance in the combo. The configured stacks imply that Kayle
        # has already spent the required five seconds out of combat.
        if ((m := self._rune(8105)) and not self.in_combat):
            flat_bonus += (m["flat_per_stack"]
                           * min(m["max_stacks"], self.relentless_stacks))

        transcendent = self.level >= PASSIVE["transcendent_level"]
        if transcendent or self.zeal >= PASSIVE["zeal_max_stacks"]:
            additive_pct += PASSIVE["exalted_ms"]
        rank_w = self.ranks.get("W", 0)
        if rank_w > 0 and at_time < self.w_ms_until - 1e-9:
            additive_pct += (W["ms_pct"][rank_w - 1]
                             + W["ms_ap_per100"] * ap / 100.0)
        if (m := self._rune(8021)) and at_time < self.fleet_ms_until - 1e-9:
            additive_pct += m["ms_melee"] if self.is_melee else m["ms_ranged"]
        if (m := self._rune(8230)) and at_time < self.stormraider_ms_until - 1e-9:
            additive_pct += m["ms_melee"] if self.is_melee else m["ms_ranged"]
        if self.has_cosmic_drive and at_time < self.cosmic_ms_until - 1e-9:
            flat_bonus += ITEMS["cosmic_drive"]["spelldance"]["move_speed_flat"]
        if self.has_stormsurge and at_time < self.stormsurge_ms_until - 1e-9:
            additive_pct += ITEMS["stormsurge"]["stormsurge"]["move_speed_pct"]
        if self.has_stormrazor and at_time < self.stormrazor_ms_until - 1e-9:
            additive_pct += ITEMS["stormrazor"]["bolt"]["move_speed_pct"]
        if (self.has_experimental_hexplate
                and at_time < self.hexplate_overdrive_until - 1e-9):
            overdrive = ITEMS["experimental_hexplate"]["overdrive"]
            additive_pct += (
                overdrive["move_speed_pct_melee"] if self.is_melee
                else overdrive["move_speed_pct_ranged"])

        # Q, Rylai, and Gunblade are all Kayle-applied impairments in this
        # simulator, so Approach Velocity receives its doubled 15% total-MS
        # multiplier while the target remains slowed.
        if (m := self._rune(8410)) and at_time < self.slowed_until - 1e-9:
            multiplicative_bonuses.append(m["own_impairment"])

        # Celerity strengthens each bonus layer, but never Kayle's base 335 MS.
        if (m := self._rune(8234)):
            effect = 1.0 + m["bonus_effectiveness"]
            flat_bonus *= effect
            additive_pct = m["base_pct"] + additive_pct * effect
            multiplicative_bonuses = [v * effect for v in multiplicative_bonuses]

        raw = ((KAYLE_AS["ms"] + flat_bonus)
               * (1.0 + additive_pct / 100.0))
        for bonus in multiplicative_bonuses:
            raw *= 1.0 + bonus
        return self._softcap_movement_speed(raw)

    def _refresh_dynamic_stats(self, at_time):
        """Refresh movement speed and Swiftmarch's live adaptive-force grant.

        W and Swiftmarch form a small feedback loop on AP builds: W movement
        speed raises Swiftmarch AP, and that AP raises W movement speed. Iterate
        to the stable in-game value while the two-second W buff is active.
        """
        base_ap_pre_mult = (
            self.static_ap_pre_mult
            + self.dynamic_conq_ap_pre_mult * self.role_quest_stat_multiplier)
        base_bonus_ad = (
            self.static_bonus_ad
            + self.dynamic_conq_ad * self.role_quest_stat_multiplier)
        ap = base_ap_pre_mult * self.ap_mult
        bonus_ad = base_bonus_ad
        force = 0.0
        for _ in range(20):
            movement_speed = self._movement_speed_for_ap(at_time, ap)
            force = (ITEMS["swiftmarch"]["adaptive_force_from_total_ms"]
                     * movement_speed) if self.has_swiftmarch else 0.0
            new_ap = (base_ap_pre_mult * self.ap_mult
                      if self.adaptive_physical
                      else (base_ap_pre_mult
                            + force * self.role_quest_stat_multiplier)
                      * self.ap_mult)
            new_bonus_ad = (base_bonus_ad
                            + 0.6 * force * self.role_quest_stat_multiplier
                            if self.adaptive_physical
                            else base_bonus_ad)
            if abs(new_ap - ap) < 1e-9 and abs(new_bonus_ad - bonus_ad) < 1e-9:
                ap, bonus_ad = new_ap, new_bonus_ad
                break
            ap, bonus_ad = new_ap, new_bonus_ad

        self.ap = ap
        self.bonus_ad = bonus_ad
        self.total_ad = self.base_ad + bonus_ad
        self.swiftmarch_force = force
        self.current_movement_speed = self._movement_speed_for_ap(at_time, ap)

    # ---------- attack speed ----------

    def attack_speed(self):
        bonus = self.level_bonus_as + self.item_as
        bonus += PASSIVE["zeal_as_per_stack"] * self.zeal
        if self.has_rageblade:
            bonus += ITEMS["guinsoos_rageblade"]["seething"]["as_per_stack"] * self.seething
        if (self.spellblade_primed and self.spellblade_key == "lich_bane"):
            bonus += ITEMS["lich_bane"]["spellblade"]["bonus_as_while_primed"]
        if (self.has_fiendhunter and self.fiendhunter_attacks > 0
                and self.time < self.fiendhunter_until - 1e-9):
            bonus += ITEMS["fiendhunter_bolts"]["opening_barrage"]["bonus_attack_speed"]
        if (self.has_experimental_hexplate
                and self.time < self.hexplate_overdrive_until - 1e-9):
            overdrive = ITEMS["experimental_hexplate"]["overdrive"]
            bonus += (overdrive["bonus_attack_speed_melee"] if self.is_melee
                      else overdrive["bonus_attack_speed_ranged"])
        if self.has_yun_tal and self.time < self.yun_tal_flurry_until - 1e-9:
            bonus += ITEMS["yun_tal_wildarrows"]["flurry"]["bonus_attack_speed"]
        uncapped = False
        if (m := self._rune(8008)):    # Lethal Tempo
            bonus += (m["as_melee"] if self.is_melee else m["as_ranged"]) * self.lt_stacks
        if (m := self._rune(9923)):    # Hail of Blades
            if self.hob_stacks > 0:
                bonus += m["as_melee"] if self.is_melee else m["as_ranged"]
                uncapped = True
        self._bonus_as_pct = bonus     # remembered for the Lethal Tempo bolt
        total = KAYLE_AS["base_as"] + KAYLE_AS["as_ratio"] * bonus / 100.0
        return total if uncapped else min(AS_CAP, total)

    # ---------- damage pipeline ----------

    def _resist_after_pen(self, resist, is_magic, at_time):
        q_reduction = Q["shred"] if at_time < self.shred_until else 0.0
        bloodletter_reduction = 0.0
        if is_magic and self.has_bloodletter:
            vile = ITEMS["bloodletters_curse"]["vile_decay"]
            # All damage on the same game frame uses the Vile Decay stack
            # count from the start of that frame. Practice Tool shows that an
            # attack's E passive and fire wave both deal damage before either
            # of their newly earned stacks begins reducing MR.
            if (self.bloodletter_frame_time is None
                    or abs(at_time - self.bloodletter_frame_time) > 1e-6):
                self.bloodletter_stacks = [
                    t for t in self.bloodletter_stacks
                    if at_time < t + vile["duration"] - 1e-9
                ]
                self.bloodletter_frame_time = at_time
                self.bloodletter_frame_stack_count = min(
                    vile["max_stacks"], len(self.bloodletter_stacks))
            bloodletter_reduction = (
                self.bloodletter_frame_stack_count
                * vile["mr_reduction_per_stack"])
        reduction = 1.0 - (1.0 - q_reduction) * (1.0 - bloodletter_reduction)

        terminus_pen = 0.0
        if self.has_terminus and at_time < self.terminus_dark_until - 1e-9:
            juxtaposition = ITEMS["terminus"]["juxtaposition"]
            terminus_pen = (min(juxtaposition["max_stacks"], self.terminus_dark_stacks)
                            * juxtaposition["dark_pen_per_stack"])
        static_pen = self.pct_pen if is_magic else self.armor_pct_pen
        percent_pen = 1.0 - (1.0 - static_pen) * (1.0 - terminus_pen)
        return effective_resistance(
            resist,
            reduction_pct=reduction,
            penetration_pct=percent_pen,
            flat_penetration=self.flat_pen if is_magic else 0.0,
        )

    def _target_hp_at_frame_start(self, at_time):
        """Snapshot target HP for all damage instances on one game frame."""
        if (self.damage_frame_time is None
                or abs(at_time - self.damage_frame_time) > 1e-6):
            self.damage_frame_time = at_time
            self.damage_frame_start_hp = self.enemy_hp
        return self.damage_frame_start_hp

    def _amp_multiplier(self, at_time):
        mult = 1.0
        target_hp = self._target_hp_at_frame_start(at_time)
        # PTA amp: not on the proc's own frame ("damage dealt on the same frame
        # that the buff is gained will not be amplified")
        if (m := self._rune(8005)) and self.pta_amp_from is not None \
                and at_time > self.pta_amp_from + 1e-6:
            mult *= 1 + m["amp"]
        if (m := self._rune(8014)) and target_hp < m["below_pct"] * self.enemy_max_hp:
            mult *= 1 + m["amp"]
        if (m := self._rune(8017)) and target_hp > m["above_pct"] * self.enemy_max_hp:
            mult *= 1 + m["amp"]
        if (m := self._rune(8299)):
            hp = self.kayle_hp_pct
            if hp <= m["hp_lo"] * 100:
                mult *= 1 + m["amp_hi"]
            elif hp <= m["hp_hi"] * 100:
                span = (m["hp_hi"] - m["hp_lo"]) * 100
                frac = (m["hp_hi"] * 100 - hp) / span
                mult *= 1 + m["amp_lo"] + (m["amp_hi"] - m["amp_lo"]) * frac
        if self.has_riftmaker and self.combat_started_at is not None:
            corruption = ITEMS["riftmaker"]["void_corruption"]
            stacks = min(corruption["max_stacks"], max(
                0, int(at_time - self.combat_started_at + 1e-9)))
            mult *= 1 + stacks * corruption["amp_per_stack"]
        if self.has_giant_slayer:
            giant = ITEMS["lord_dominiks_regards"]["giant_slayer"]
            mult *= 1 + min(
                giant["max_amp"],
                self.enemy_bonus_hp * giant["amp_per_bonus_hp"],
            )
        return mult

    def _record_damage(self, calc, dtype, source, at_time, *, grants_omnivamp=True):
        """Apply one resolved damage instance and add its audit trail."""
        hp_before = self.enemy_hp
        dealt = calc.applied
        self.enemy_hp -= dealt
        self.damage_totals[dtype] += dealt
        self.damage_instances.append((float(at_time), dealt))
        self.pre_mitigation_total += calc.amplified
        if self.enemy_hp <= 0 and self.kill_time is None:
            self.kill_time = at_time
        self.events.append({
            "t": round(at_time, 3),
            "source": source,
            "type": dtype,
            "raw": round(calc.raw, 4),
            "multiplier": round(calc.outgoing_multiplier, 6),
            # Keep the old `pre` field for API compatibility.
            "pre": round(calc.amplified, 4),
            "effective_resistance": (
                round(calc.effective_resistance, 4)
                if calc.effective_resistance is not None else None
            ),
            "mitigation_multiplier": round(calc.mitigation_multiplier, 6),
            "dealt": round(dealt, 4),
            "hp_before": round(hp_before, 4),
            "hp_after": round(self.enemy_hp, 4),
        })
        omnivamp = self.omnivamp
        if self.has_riftmaker and self.combat_started_at is not None:
            corruption = ITEMS["riftmaker"]["void_corruption"]
            stacks = min(corruption["max_stacks"], max(
                0, int(at_time - self.combat_started_at + 1e-9)))
            if stacks >= corruption["max_stacks"]:
                omnivamp += (corruption["omnivamp_melee"] if self.is_melee
                             else corruption["omnivamp_ranged"])
        if grants_omnivamp and omnivamp:
            self.heal_total += dealt * omnivamp
        self.end_time = max(self.end_time, at_time)
        self._movement_runes_after_damage(dealt, at_time)
        if self.has_cosmic_drive and dtype in ("magic", "true"):
            self.cosmic_ms_until = max(
                self.cosmic_ms_until,
                at_time + ITEMS["cosmic_drive"]["spelldance"]["duration"],
            )
            self._refresh_dynamic_stats(at_time)
        return dealt

    def _deal(self, amount, dtype, source, at_time, from_first_strike=False):
        """dtype: 'physical' | 'magic' | 'true'"""
        multiplier = self._amp_multiplier(at_time)
        if dtype in ("magic", "true") and self.has_shadowflame_crit:
            shadowflame_crit = ITEMS["shadowflame"]["shadowflame_crit"]
            target_hp = self._target_hp_at_frame_start(at_time)
            if target_hp < shadowflame_crit["threshold"] * self.enemy_max_hp:
                multiplier *= shadowflame_crit["amp"]
                source += " (Shadowflame crit)"
        resistance = None
        if dtype == "physical":
            resistance = self._resist_after_pen(self.enemy_armor, False, at_time)
        elif dtype == "magic":
            resistance = self._resist_after_pen(self.enemy_mr, True, at_time)
        calc = resolve_damage(
            amount,
            dtype,
            outgoing_multiplier=multiplier,
            resistance=resistance,
        )
        dealt = self._record_damage(calc, dtype, source, at_time)

        # First Strike: opens on the first damage; adds 7% post-mit true damage
        if (m := self._rune(8369)) and not from_first_strike:
            if self.fs_until is None:
                self.fs_until = at_time + m["duration"]
            if at_time <= self.fs_until:
                fs_calc = resolve_damage(dealt * m["amp"], "true")
                # First Strike's proc is derived from already-modified damage;
                # it must not recursively trigger amps, itself, or omnivamp.
                self._record_damage(
                    fs_calc, "true", "First Strike", at_time, grants_omnivamp=False)
        return dealt

    def _adaptive_deal(self, amount, source, at_time):
        self._deal(amount, "physical" if self.adaptive_physical else "magic",
                   source, at_time)

    def _heal(self, amount, source, at_time):
        self.heal_total += amount
        self.events.append({
            "t": round(at_time, 3), "source": source, "type": "heal",
            "pre": round(amount, 1), "dealt": round(amount, 1),
        })

    def _flush_scheduled(self, up_to):
        while True:
            due = [s for s in self.scheduled if s[0] <= up_to]
            if not due:
                break
            due.sort(key=lambda s: s[0])
            t, fn = due[0]
            self.scheduled.remove(due[0])
            fn(t)

    def _advance(self, dt):
        self.time += dt
        self.end_time = max(self.end_time, self.time)
        self._flush_scheduled(self.time)

    def _check_cd(self, key, cooldown, label):
        ready = self.cooldowns.get(key, -1e9)
        if self.time < ready - 1e-9:
            if key in {"Q", "W", "E", "R"}:
                self.cooldown_errors.append({
                    "action_index": self.current_action_index,
                    "ability": key,
                    "used_at": round(self.time, 3),
                    "ready_at": round(ready, 3),
                })
            else:
                self.warnings.append(
                    f"{label} used at t={self.time:.2f}s but its cooldown is not ready "
                    f"until t={ready:.2f}s (skipped).")
            return False
        self.cooldowns[key] = self.time + cooldown
        return True

    def _hasted(self, cd, ultimate=False):
        haste = self.haste + (self.ultimate_haste if ultimate else self.basic_haste)
        return cd / (1 + haste / 100.0)

    # ---------- rune triggers ----------

    def _trigger_fleet(self, at_time):
        """Queue Fleet's movement layer after its Energized attack.

        Practice Tool shows Stormrazor's 540-MS state before Fleet's later
        570-MS jump. Keep that small visual delay in the timeline, then apply
        it automatically before the next user action. Selecting Fleet is the
        condition; the public combo builder does not need a timing utility.
        """
        m = self._rune(8021)
        if not m or not self.fleet_ready:
            return
        self.fleet_ready = False
        self.fleet_pending = True
        self.fleet_pending_at = at_time + FLEET_VISUAL_SYNC_DELAY
        self.fleet_pending_until = self.fleet_pending_at + m["duration"]
        self.events.append({
            "t": round(at_time, 3),
            "source": "Fleet Footwork movement speed pending",
            "type": "note", "pre": 0, "dealt": 0,
        })

    def _activate_pending_fleet(self, at_time):
        if not self.fleet_pending:
            return
        self.fleet_pending = False
        if at_time >= self.fleet_pending_until - 1e-9:
            return
        self.fleet_ms_until = self.fleet_pending_until
        self._refresh_dynamic_stats(at_time)
        self.events.append({
            "t": round(at_time, 3),
            "source": (f"Fleet Footwork movement speed — "
                       f"{self.current_movement_speed:.2f} total"),
            "type": "note", "pre": 0, "dealt": 0,
        })

    def do_wait(self, duration=FLEET_VISUAL_SYNC_DELAY):
        duration = max(0.0, float(duration))
        self._advance(duration)
        self._activate_pending_fleet(self.time)
        self.events.append({
            "t": round(self.time, 3),
            "source": f"Wait — {duration:.2f}s",
            "type": "note", "pre": 0, "dealt": 0,
        })

    def _stormsurge_squall(self, at_time):
        """Resolve Squall against the simulator's single tracked target."""
        effect = ITEMS["stormsurge"]["stormsurge"]
        self._refresh_dynamic_stats(at_time)
        if self.enemy_hp <= 0:
            # In game, a target that dies before Squall emits an immediate AoE
            # around its corpse. This single-target simulator has no nearby
            # secondary enemy, so do not assign that damage to the dead target.
            self.end_time = max(self.end_time, at_time)
            self.events.append({
                "t": round(at_time, 3),
                "source": "Stormsurge Squall - target dead; nearby AoE omitted",
                "type": "note", "pre": 0, "dealt": 0,
            })
            return

        # Squall is area damage that triggers spell effects. It is an item
        # effect, not an ability cast, so it does not prime Spellblade.
        self._on_action_damage(at_time, is_item=True)
        self._ability_damage_triggers(at_time, area=True)
        damage = effect["squall_base"] + effect["squall_ap_ratio"] * self.ap
        self._deal(damage, "magic", "Stormsurge - Squall", at_time)
        self._dark_harvest(at_time)

    def _movement_runes_after_damage(self, dealt, at_time):
        """Update damage-activated rune and item MS buffs after damage."""
        changed = False
        stormraider_triggered = False
        stormsurge_triggered = False
        if not self.in_combat:
            self.in_combat = True
            self.combat_started_at = at_time
            changed = True       # immediately removes Relentless Hunter MS

        m = self._rune(8230)
        if m and at_time >= self.stormraider_cd_until - 1e-9:
            self.stormraider_damage = [
                (t, d) for t, d in self.stormraider_damage
                if t >= at_time - m["window"] - 1e-9
            ]
            self.stormraider_damage.append((at_time, dealt))
            if sum(d for _, d in self.stormraider_damage) \
                    >= m["threshold"] * self.enemy_max_hp:
                self.stormraider_ms_until = at_time + m["duration"]
                self.stormraider_cd_until = at_time + self._lerp(
                    m["cd_lo"], m["cd_hi"])
                self.stormraider_damage = []
                changed = True
                stormraider_triggered = True

        if (self.has_stormsurge
                and at_time >= self.stormsurge_cd_until - 1e-9):
            effect = ITEMS["stormsurge"]["stormsurge"]
            self.stormsurge_damage = [
                (t, d) for t, d in self.stormsurge_damage
                if t >= at_time - effect["window"] - 1e-9
            ]
            self.stormsurge_damage.append((at_time, dealt))
            if sum(d for _, d in self.stormsurge_damage) \
                    >= effect["threshold"] * self.enemy_max_hp:
                self.stormsurge_ms_until = (
                    at_time + effect["move_speed_duration"])
                self.stormsurge_cd_until = at_time + effect["cooldown"]
                self.stormsurge_damage = []
                self.scheduled.append([
                    at_time + effect["squall_delay"],
                    self._stormsurge_squall,
                ])
                changed = True
                stormsurge_triggered = True

        if changed:
            self._refresh_dynamic_stats(at_time)
            if stormraider_triggered:
                self.events.append({
                    "t": round(at_time, 3),
                    "source": (f"Stormraider's Surge — "
                               f"{self.current_movement_speed:.2f} total MS"),
                    "type": "note", "pre": 0, "dealt": 0,
                })
            if stormsurge_triggered:
                self.events.append({
                    "t": round(at_time, 3),
                    "source": (f"Stormsurge - Stormraider applied Squall; "
                               f"{self.current_movement_speed:.2f} total MS"),
                    "type": "note", "pre": 0, "dealt": 0,
                })

    def _conqueror_add(self, n, at_time):
        m = self._rune(8010)
        if not m:
            return
        old = self.conq_stacks
        self.conq_stacks = min(m["max_stacks"], self.conq_stacks + n)
        gained = self.conq_stacks - old
        if gained > 0:            # stacks grant adaptive stats immediately
            if self.adaptive_physical:
                per = self._lerp(*m["ad_per"])
                self.dynamic_conq_ad += per * gained
            else:
                self.dynamic_conq_ap_pre_mult += self._lerp(*m["ap_per"]) * gained
            self._refresh_dynamic_stats(at_time)

    def _conqueror_heal(self, dealt, at_time):
        m = self._rune(8010)
        if m and self.conq_stacks >= m["max_stacks"]:
            pct = m["heal_melee"] if self.is_melee else m["heal_ranged"]
            self.heal_total += dealt * pct

    def _electro_stack(self, at_time):
        m = self._rune(8112)
        if not m or at_time < self.electro_cd_until:
            return
        self.electro_times = [t for t in self.electro_times
                              if t > at_time - m["window"]] + [at_time]
        if len(self.electro_times) >= 3:
            dmg = (self._lerp(m["lo"], m["hi"])
                   + m["bonus_ad"] * self.bonus_ad + m["ap"] * self.ap)
            self._adaptive_deal(dmg, "Electrocute", at_time)
            self.electro_times = []
            self.electro_cd_until = at_time + m["cd"]

    def _dark_harvest(self, at_time):
        m = self._rune(8128)
        if (m and at_time >= self.dh_cd_until
                and self.enemy_hp < m["threshold"] * self.enemy_max_hp):
            dmg = (m["base"] + m["per_soul"] * self.dh_souls
                   + m["bonus_ad"] * self.bonus_ad + m["ap"] * self.ap)
            self._adaptive_deal(dmg, f"Dark Harvest ({self.dh_souls} souls)", at_time)
            self.dh_cd_until = at_time + m["cd"]

    def _aery(self, at_time):
        m = self._rune(8214)
        if m and at_time >= self.aery_ready_at:
            dmg = (self._lerp(m["lo"], m["hi"])
                   + m["bonus_ad"] * self.bonus_ad + m["ap"] * self.ap)
            self._adaptive_deal(dmg, "Summon Aery", at_time)
            self.aery_ready_at = at_time + m["cd"]

    def _cheap_shot(self, at_time):
        m = self._rune(8126)
        if m and at_time >= self.cheap_cd_until and at_time < self.slowed_until:
            self._deal(self._lerp(m["lo"], m["hi"]), "true", "Cheap Shot", at_time)
            self.cheap_cd_until = at_time + m["cd"]

    def _on_action_damage(self, at_time, is_ability=False, is_item=False):
        """Common per-action rune triggers (once per attack / cast / item use).
        Cheap Shot checks impairment BEFORE this action's own slows apply."""
        self._cheap_shot(at_time)
        self._aery(at_time)
        self._electro_stack(at_time)
        self._dark_harvest(at_time)
        if is_ability:
            self._ability_damage_triggers(at_time)

    def _ability_damage_triggers(self, at_time, area=True):
        # Arcane Comet
        if (m := self._rune(8229)) and at_time >= self.comet_cd_until:
            dmg = (self._lerp(m["lo"], m["hi"])
                   + m["bonus_ad"] * self.bonus_ad + m["ap"] * self.ap)
            self.scheduled.append([at_time + m["delay"],
                                   lambda tt, d=dmg: self._adaptive_deal(d, "Arcane Comet", tt)])
            self.comet_cd_until = at_time + self._lerp(m["cd_lo"], m["cd_hi"])
        # Scorch
        if (m := self._rune(8237)) and at_time >= self.scorch_cd_until:
            dmg = self._lerp(m["lo"], m["hi"])
            self.scheduled.append([at_time + m["delay"],
                                   lambda tt, d=dmg: self._deal(d, "magic", "Scorch", tt)])
            self.scorch_cd_until = at_time + m["cd"]
        # Deathfire Touch burn (Q/R/fire waves are area damage → 2s)
        if (m := self._rune(8992)):
            dur = m["dur_area"] if area else m["dur_spell"]
            if at_time > self.dft_until:      # burn had expired → new burn chain
                self.dft_started = at_time
            self.dft_until = max(self.dft_until, at_time + dur)
            if not self.dft_ticking:
                self.dft_ticking = True
                self.scheduled.append([at_time + m["interval"], self._dft_tick])
        # Rylai's slow on ability damage
        if self.has_rylai:
            self.slowed_until = max(self.slowed_until, at_time + 1.0)

    def _dft_tick(self, tt):
        m = self._rune(8992)
        if not m or tt > self.dft_until + 1e-9:
            self.dft_ticking = False
            return
        self._refresh_dynamic_stats(tt)
        dmg = (self._lerp(m["tick_lo"], m["tick_hi"])
               + m["bonus_ad"] * self.bonus_ad + m["ap"] * self.ap)
        if tt - self.dft_started >= m["linger_time"]:
            dmg *= 1 + m["linger_amp"]
        self._deal(dmg, "magic", "Deathfire Touch", tt)
        self.scheduled.append([tt + m["interval"], self._dft_tick])

    def _grasp_stacks(self, at_time):
        return min(4, int(at_time - max(0.0, self.grasp_consumed_at)))

    # ---------- stateful item triggers ----------

    def _apply_bloodletter_stack(self, at_time, cast_instance):
        """Apply Vile Decay after eligible Kayle ability/passive magic damage."""
        if not self.has_bloodletter:
            return
        vile = ITEMS["bloodletters_curse"]["vile_decay"]
        last_application = self.bloodletter_last_application.get(
            cast_instance, -1e9)
        if at_time < last_application + vile["application_gate"] - 1e-9:
            return
        self.bloodletter_stacks = [
            t for t in self.bloodletter_stacks
            if at_time < t + vile["duration"] - 1e-9
        ]
        if len(self.bloodletter_stacks) < vile["max_stacks"]:
            self.bloodletter_stacks.append(at_time)
        else:
            # Reapplying at maximum stacks refreshes the debuff duration.
            self.bloodletter_stacks = [at_time] * vile["max_stacks"]
        self.bloodletter_last_application[cast_instance] = at_time

    def _terminus_hit(self, at_time):
        if not self.has_terminus:
            return
        juxtaposition = ITEMS["terminus"]["juxtaposition"]
        if at_time >= self.terminus_dark_until - 1e-9:
            self.terminus_dark_stacks = 0
        if self.terminus_next_dark:
            self.terminus_dark_stacks = min(
                juxtaposition["max_stacks"], self.terminus_dark_stacks + 1)
            self.terminus_dark_until = at_time + juxtaposition["duration"]
        self.terminus_next_dark = not self.terminus_next_dark

    def _kraken_hit(self, at_time, tag):
        if not self.has_kraken:
            return
        bring = ITEMS["kraken_slayer"]["bring_it_down"]
        if at_time > self.kraken_last_hit + bring["stack_duration"] + 1e-9:
            self.kraken_stacks = 0
        self.kraken_last_hit = at_time
        if self.kraken_stacks < 2:
            self.kraken_stacks += 1
            return
        self.kraken_stacks = 0
        base = lerp_by_level(
            bring["melee_lo"], bring["melee_hi"], self.level,
            lo_lvl=8, hi_lvl=18, cap_lvl=20,
        )
        if not self.is_melee:
            base *= bring["ranged_modifier"]
        # Practice Tool isolation shows Bring It Down snapshots missing health
        # before the triggering attack's damage frame. Reading ``enemy_hp``
        # here would incorrectly include the basic physical hit that precedes
        # the on-hit package in our event ordering.
        target_hp = self._target_hp_at_frame_start(at_time)
        missing_fraction = max(
            0.0, min(1.0, (self.enemy_max_hp - target_hp) / self.enemy_max_hp))
        damage = base * (1.0 + bring["missing_hp_max_amp"] * missing_fraction)
        self._deal(damage, "physical", f"Kraken Slayer — Bring It Down{tag}", at_time)

    def _statikk_hit(self, at_time, tag):
        if not (self.has_statikk and self.statikk_ready):
            return
        spark = ITEMS["statikk_shiv"]["electrospark"]
        self.statikk_ready = False
        self._deal(spark["damage"], "magic", f"Statikk Shiv — Electrospark{tag}", at_time)

    def _stormrazor_hit(self, at_time, tag):
        if not (self.has_stormrazor and self.stormrazor_ready):
            return
        bolt = ITEMS["stormrazor"]["bolt"]
        self.stormrazor_ready = False
        self._deal(bolt["damage"], "magic", f"Stormrazor — Bolt{tag}", at_time)
        self.stormrazor_ms_until = at_time + bolt["duration"]
        self._refresh_dynamic_stats(at_time)

    def _rapid_firecannon_hit(self, at_time, tag):
        if not (self.has_rapid_firecannon and self.rapid_firecannon_ready):
            return
        sharpshooter = ITEMS["rapid_firecannon"]["sharpshooter"]
        self.rapid_firecannon_ready = False
        self._deal(
            sharpshooter["damage"], "magic",
            f"Rapid Firecannon — Sharpshooter{tag}", at_time,
        )

    def _assumed_attack_range(self):
        if self.level >= PASSIVE["transcendent_level"]:
            attack_range = 625.0
        elif self.level >= PASSIVE["arisen_level"]:
            attack_range = 525.0
        else:
            attack_range = float(KAYLE_AS["range_base"])

        # There is intentionally no target-distance control. When Sharpshooter
        # is ready, the next attack uses RFC's maximum legal attack range for
        # distance-scaling effects such as Hexoptics Magnification.
        if self.has_rapid_firecannon and self.rapid_firecannon_ready:
            sharpshooter = ITEMS["rapid_firecannon"]["sharpshooter"]
            attack_range += min(
                attack_range * sharpshooter["bonus_range_pct"],
                sharpshooter["bonus_range_cap"],
            )
        return attack_range

    def _hexoptics_amp(self):
        if not self.has_hexoptics:
            return 0.0
        attack_range = self._assumed_attack_range()
        magnification = ITEMS["hexoptics_c44"]["magnification"]
        return min(
            magnification["max_amp"],
            attack_range * magnification["amp_per_unit"],
        )

    def _begin_basic_attack(self, at_time):
        """Snapshot the shared crit roll as an expected-damage multiplier."""
        normal_expected = 1.0 + self.crit_chance * (self.crit_damage - 1.0)
        opening = ITEMS["fiendhunter_bolts"]["opening_barrage"]
        active = (self.has_fiendhunter and self.fiendhunter_attacks > 0
                  and at_time < self.fiendhunter_until - 1e-9)
        self.current_attack_fiendhunter = active
        if active:
            forced = opening["forced_crit_modifier"]
            self.current_attack_crit_multiplier = self.crit_damage * (
                forced + self.crit_chance * (1.0 - forced))
        else:
            self.current_attack_crit_multiplier = normal_expected

    def _deal_basic_attack(self, source, at_time):
        raw = (self.total_ad * self.current_attack_crit_multiplier
               * (1.0 + self._hexoptics_amp()))
        label = source
        if self.current_attack_fiendhunter:
            label += " (Fiendhunter expected crit)"
        elif self.crit_chance > 0:
            label += " (expected crit)"
        dealt = self._deal(raw, "physical", label, at_time)
        if self.life_steal:
            self._heal(
                dealt * self.life_steal,
                f"{source} life steal",
                at_time,
            )
        if self.current_attack_fiendhunter and self.crit_chance > 0:
            opening = ITEMS["fiendhunter_bolts"]["opening_barrage"]
            natural_crit_raw = (self.total_ad * self.crit_damage
                                * (1.0 + self._hexoptics_amp()))
            self._deal(
                natural_crit_raw * self.crit_chance
                * opening["natural_crit_true_ratio"],
                "true", "Fiendhunter Bolts — natural-crit bonus", at_time)
        return dealt

    def _finish_basic_attack(self):
        if self.current_attack_fiendhunter:
            self.fiendhunter_attacks = max(0, self.fiendhunter_attacks - 1)
        self.current_attack_fiendhunter = False
        self.current_attack_crit_multiplier = 1.0

    def _yun_tal_launch_attack(self, at_time):
        """Start Flurry on attack; its AS changes the interval to the next hit."""
        if not self.has_yun_tal:
            return
        flurry = ITEMS["yun_tal_wildarrows"]["flurry"]
        if at_time >= self.yun_tal_flurry_ready_at - 1e-9:
            self.yun_tal_flurry_until = at_time + flurry["duration"]
            self.yun_tal_flurry_ready_at = at_time + flurry["cooldown"]

    def _finish_yun_tal_attack(self, at_time, crit_chance_snapshot):
        if not self.has_yun_tal:
            return
        flurry = ITEMS["yun_tal_wildarrows"]["flurry"]
        if self.yun_tal_flurry_ready_at > at_time:
            expected_reduction = (
                flurry["reduction_on_hit"]
                + flurry["extra_reduction_on_crit"] * crit_chance_snapshot
            )
            self.yun_tal_flurry_ready_at = max(
                at_time, self.yun_tal_flurry_ready_at - expected_reduction)

        practice = ITEMS["yun_tal_wildarrows"]["practice_makes_lethal"]
        gain = (practice["crit_per_melee_attack"] if self.is_melee
                else practice["crit_per_ranged_attack"])
        self.yun_tal_bonus_crit = min(
            practice["max_crit_chance"], self.yun_tal_bonus_crit + gain)
        self.crit_chance = min(
            1.0, self.base_crit_chance + self.yun_tal_bonus_crit / 100.0)

    def _navori_launch_attack(self, at_time):
        if not self.has_navori:
            return
        reduction = ITEMS["navori_flickerblade"]["transcendence"][
            "remaining_cooldown_reduction"]
        for ability in ("Q", "W", "E"):
            ready_at = self.cooldowns.get(ability)
            if ready_at is not None and ready_at > at_time:
                self.cooldowns[ability] = (
                    at_time + (ready_at - at_time) * (1.0 - reduction))

    # ---------- on-hit package ----------

    def _apply_onhits(
            self, at_time, tag="", grants_pta=True,
            defer_terminus_stack=False):
        """Item on-hits + Kayle E passive as one on-hit application.
        grants_pta=False for the Dusk & Dawn repeat — in-game verified: a clean
        E (3 applications incl. the repeat) does NOT proc PTA, so the repeat
        gives no stack. Rageblade's Phantom Hit does grant stacks (wiki)."""
        self._refresh_dynamic_stats(at_time)
        for k in self.items:
            it = ITEMS[k]
            if "onhit_magic_flat" in it:
                self._deal(it["onhit_magic_flat"], "magic", f"{it['name']} on-hit{tag}", at_time)
            if "onhit_magic" in it:
                oh = it["onhit_magic"]
                self._deal(oh["flat"] + oh["ap_ratio"] * self.ap, "magic",
                           f"{it['name']} on-hit{tag}", at_time)
        self._kraken_hit(at_time, tag)
        self._statikk_hit(at_time, tag)
        self._stormrazor_hit(at_time, tag)
        self._rapid_firecannon_hit(at_time, tag)
        rank_e = self.ranks.get("E", 0)
        if rank_e > 0:
            dmg = (E["onhit_base"][rank_e - 1]
                   + E["onhit_bonus_ad_ratio"] * self.bonus_ad
                   + E["onhit_ap_ratio"] * self.ap)
            self._deal(dmg, "magic", f"E passive on-hit{tag}", at_time)
            self._apply_bloodletter_stack(at_time, "e_passive")
        if grants_pta:
            self._pta_stack(at_time)
        if not defer_terminus_stack:
            self._terminus_hit(at_time)

    def _pta_stack(self, at_time):
        """Press the Attack gains a stack per on-hit application; 3rd procs."""
        if (m := self._rune(8005)):
            self.pta_stacks += 1
            if self.pta_stacks >= m["stacks"]:
                self.pta_stacks = 0
                dmg = self._lerp(m["proc_lo"], m["proc_hi"])
                self._adaptive_deal(dmg, "Press the Attack", at_time)
                if self.pta_amp_from is None:
                    self.pta_amp_from = at_time  # amp for the rest of the combo
                self.cooldowns["pta"] = at_time + m["cd"]

    def _fire_wave(self, at_time):
        growth_levels = max(
            0, self.level - PASSIVE["wave_growth_start_level"] + 1)
        wave_base = (PASSIVE["wave_base"]
                     + PASSIVE["wave_growth_per_level"] * growth_levels)
        dmg = (wave_base
               + PASSIVE["wave_bonus_ad_ratio"] * self.bonus_ad
               + PASSIVE["wave_ap_ratio"] * self.ap)
        source = "Passive fire wave"
        if self.current_attack_fiendhunter:
            source += " (Fiendhunter expected crit)"
        elif self.crit_chance > 0:
            source += " (expected crit)"
        self._deal(dmg * self.current_attack_crit_multiplier, "magic", source, at_time)
        self._apply_bloodletter_stack(at_time, "fire_wave")
        # wave is ability area damage (shares the attack's cast instance, so no
        # extra Electrocute/Conqueror stacks) → Comet/Scorch/DFT/Rylai triggers
        self._ability_damage_triggers(at_time)

    # ---------- actions ----------

    def do_attack(self):
        transcendent = self.level >= PASSIVE["transcendent_level"]
        if not transcendent:
            self.zeal = min(PASSIVE["zeal_max_stacks"], self.zeal + 1)
        self._refresh_dynamic_stats(self.time)

        # Hail of Blades: triggers on the first windup, benefits that attack
        if (m := self._rune(9923)) and not self.hob_triggered:
            self.hob_triggered = True
            self.hob_stacks = m["stacks"]
        # Lethal Tempo stack granted on-attack (benefits subsequent AS reads)
        if (m := self._rune(8008)):
            self.lt_stacks = min(m["max_stacks"], self.lt_stacks + 1)

        t = self.time
        self._yun_tal_launch_attack(t)
        speed = self.attack_speed()   # also snapshots bonus AS % for the bolt
        period = 1.0 / speed
        crit_chance_snapshot = self.crit_chance
        attack_dealt = 0.0
        self._begin_basic_attack(t)
        self._navori_launch_attack(t)

        # Cheap Shot / Aery / Electrocute / Dark Harvest fire once per attack
        self._on_action_damage(t)
        # Conqueror on-attack stacks
        m = self._rune(8010)
        if m:
            self._conqueror_add(m["per_attack_melee"] if self.is_melee
                                else m["per_attack_ranged"], t)

        # 1. physical hit
        attack_dealt += self._deal_basic_attack("Basic attack", t)
        # 2. on-hit package (items + E passive + PTA stacking)
        # Terminus grants Light/Dark after the complete triggering attack. In
        # particular, Practice Tool shows that attack 2's fire wave still uses
        # zero Dark stacks; attack 3 is the first to use the new penetration.
        self._apply_onhits(t, defer_terminus_stack=True)
        # 2b. rune on-hit extras
        if (m := self._rune(9923)) and self.hob_stacks > 0:  # HoB true damage
            dmg = (self._lerp(m["true_lo"], m["true_hi"])
                   + m["bonus_ad"] * self.bonus_ad + m["ap"] * self.ap)
            self._deal(dmg, "true", "Hail of Blades", t)
            self.hob_stacks -= 1
        if (m := self._rune(8008)) and self.lt_stacks >= m["max_stacks"]:  # LT bolt
            lo, hi = m["bolt_melee"] if self.is_melee else m["bolt_ranged"]
            amp = m["bolt_amp_melee"] if self.is_melee else m["bolt_amp_ranged"]
            dmg = self._lerp(lo, hi) * (1 + self._bonus_as_pct * amp)
            self._adaptive_deal(dmg, "Lethal Tempo bolt", t)
        if (m := self._rune(8437)) and self._grasp_stacks(t) >= m["stacks"]:  # Grasp
            pct = m["dmg_melee"] if self.is_melee else m["dmg_ranged"]
            self._deal(pct * self.kayle_max_hp, "magic", "Grasp of the Undying", t)
            hpct = m["heal_melee"] if self.is_melee else m["heal_ranged"]
            self._heal(hpct * self.kayle_max_hp, "Grasp heal", t)
            self.grasp_consumed_at = t
        # 3. spellblade proc
        self._consume_spellblade(t)
        # 5. fire wave (Aflame + Exalted; the attack reaching 5 stacks fires it)
        exalted = transcendent or self.zeal >= PASSIVE["zeal_max_stacks"]
        if self.level >= PASSIVE["aflame_level"] and exalted:
            self._fire_wave(t)
        self._terminus_hit(t)
        # 6. Rageblade stacking / Phantom Hit
        if self.has_rageblade:
            rb = ITEMS["guinsoos_rageblade"]["seething"]
            was_at_max = self.seething >= rb["max_stacks"]
            self.seething = min(rb["max_stacks"], self.seething + 1)
            # The attack that reaches maximum Seething stacks does not count
            # toward "every third attack while at maximum stacks."
            if was_at_max:
                if self.phantom == 2:
                    self.phantom = 0
                    self.scheduled.append(
                        [t + 0.15, lambda tt: self._apply_onhits(tt, tag=" (Phantom Hit)")])
                else:
                    self.phantom += 1

        self._conqueror_heal(attack_dealt, t)
        # Dark Harvest re-check: this attack may have dropped the enemy below 50%
        self._dark_harvest(t)
        self._trigger_fleet(t)
        self.attack_count += 1
        self._finish_basic_attack()
        self._finish_yun_tal_attack(t, crit_chance_snapshot)
        self._advance(period)

    def _prime_spellblade(self):
        if self.spellblade_key:
            self.spellblade_primed = True
            self.dd_repeat_used = False

    def _consume_spellblade(self, at_time):
        """Consume a primed Spellblade on an attack, including D&D's repeat."""
        if not (self.spellblade_primed and self.spellblade_key
                and at_time >= self.spellblade_cd_until):
            return False
        it = ITEMS[self.spellblade_key]
        sb = it["spellblade"]
        base_ad_ratio = (
            sb["base_ad_ratio"]
            + sb.get("base_ad_ratio_per_crit_pct", 0.0)
            * self.crit_chance * 100.0
        )
        dmg = (base_ad_ratio * self.base_ad
               + sb.get("ap_ratio", 0.0) * self.ap)
        self._deal(
            dmg, sb.get("damage_type", "magic"),
            f"{it['name']} Spellblade", at_time,
        )
        if "heal_ap_ratio" in sb:
            heal = sb["heal_ap_ratio"] * self.ap + sb["heal_bonus_hp_ratio"] * self.bonus_hp
            self._heal(heal, f"{it['name']} Spellblade heal", at_time)
        self._dd_repeat(at_time)
        self.spellblade_primed = False
        self.spellblade_cd_until = at_time + SPELLBLADE_CD
        return True

    def _cast_common(self, at_time):
        """Per damaging-ability-cast rune triggers (Conqueror, HoB resets…)."""
        if (m := self._rune(8010)):
            self._conqueror_add(m["per_ability"], at_time)

    def _prepare_q(self):
        self._refresh_dynamic_stats(self.time)
        rank = self.ranks.get("Q", 0)
        if rank == 0:
            self.warnings.append("Q used with no rank — skipped.")
            return None
        cast = KAYLE_AS["windup_percent"] / self.attack_speed()
        if not self._check_cd("Q", self._hasted(Q["cooldown"][rank - 1]), "Q"):
            return None
        t = self.time
        self._on_action_damage(t, is_ability=True)   # Cheap Shot checks pre-slow
        self._cast_common(t)
        dmg = (Q["base"][rank - 1]
               + Q["bonus_ad_ratio"] * self.bonus_ad
               + Q["ap_ratio"] * self.ap)
        self._prime_spellblade()
        return t, cast, dmg

    def _land_q(self, dmg, at_time):
        """Resolve Q impact; its damage always precedes its own shred."""
        self._deal(dmg, "magic", "Q — Radiant Blast", at_time)
        self._apply_bloodletter_stack(at_time, "q")
        self._dark_harvest(at_time)
        self.shred_until = at_time + Q["shred_duration"]
        self.slowed_until = max(self.slowed_until, at_time + 2.0)

    def do_q(self):
        prepared = self._prepare_q()
        if prepared is None:
            return
        t, cast, dmg = prepared
        self._land_q(dmg, t)
        self._advance(cast)

    def do_w(self):
        self._refresh_dynamic_stats(self.time)
        rank = self.ranks.get("W", 0)
        if rank == 0:
            self.warnings.append("W used with no rank — skipped.")
            return
        if not self._check_cd("W", self._hasted(W["cooldown"][rank - 1]), "W"):
            return
        heal = W["heal"][rank - 1] + W["heal_ap_ratio"] * self.ap
        self._heal(heal, "W — Celestial Blessing", self.time)
        self.w_ms_until = max(self.w_ms_until, self.time + W["ms_duration"])
        self._refresh_dynamic_stats(self.time)
        swift_text = (f"; Swiftmarch +{self.swiftmarch_force:.2f} adaptive force"
                      if self.has_swiftmarch else "")
        self.events.append({
            "t": round(self.time, 3),
            "source": (f"W movement speed — {self.current_movement_speed:.2f} total"
                       f"{swift_text}"),
            "type": "note", "pre": 0, "dealt": 0,
        })
        self._prime_spellblade()
        self._advance(W["cast_time"])

    def do_e(self, timing="instant"):
        """Execute E as an empowered basic attack and attack-timer reset.

        Practice Tool isolation on 2026-07-17 established this package:
        physical basic hit, one normal on-hit package, Spellblade damage, and
        Dusk & Dawn's on-hit repeat. Missing HP is snapshotted before the attack
        and uses E's AP-scaled percentage. The E explosion itself does not add
        PTA; Dusk & Dawn's repeat does. All components share the cast frame, so
        the PTA proc does not amplify the E components which triggered it.
        """
        rank = self.ranks.get("E", 0)
        if rank == 0:
            self.warnings.append("E used with no rank — skipped.")
            return
        if not self._check_cd("E", self._hasted(E["cooldown"][rank - 1]), "E"):
            return
        t = self.time
        missing_at_cast = max(0.0, self.enemy_max_hp - self.enemy_hp)
        phantom_will_proc = False
        if self.has_rageblade:
            rb = ITEMS["guinsoos_rageblade"]["seething"]
            phantom_will_proc = (
                self.seething >= rb["max_stacks"] and self.phantom == 2)
        if self.level < PASSIVE["transcendent_level"]:
            self.zeal = min(PASSIVE["zeal_max_stacks"], self.zeal + 1)
        self._refresh_dynamic_stats(t)

        # E is an attack reset. It starts Hail of Blades or adds a reset stack
        # to an already-active sequence.
        if (m := self._rune(9923)):
            if not self.hob_triggered:
                self.hob_triggered = True
                self.hob_stacks = m["stacks"]
            elif self.hob_resets_used < m["extra_stacks"]:
                self.hob_stacks += 1
                self.hob_resets_used += 1
        if (m := self._rune(8008)):
            self.lt_stacks = min(m["max_stacks"], self.lt_stacks + 1)

        self._yun_tal_launch_attack(t)
        crit_chance_snapshot = self.crit_chance
        self._prime_spellblade()
        self.attack_speed()  # snapshot bonus AS for Lethal Tempo's bolt
        self._begin_basic_attack(t)
        self._navori_launch_attack(t)
        self._on_action_damage(t)
        if (m := self._rune(8010)):
            self._conqueror_add(m["per_attack_melee"] if self.is_melee
                                else m["per_attack_ranged"], t)

        # The empowered basic attack and its normal on-hit package.
        attack_dealt = self._deal_basic_attack("Basic attack (E)", t)

        # Practice Tool found a Rageblade-specific E ordering interaction. With
        # Rageblade equipped, E's execute normally reads missing HP after the
        # physical basic hit. If an instant E reset is also the attack that
        # triggers Phantom Hit, the read occurs after the normal on-hit package.
        # Without Rageblade, the verified pre-attack snapshot stays unchanged.
        if self.has_rageblade:
            missing_at_cast = max(0.0, self.enemy_max_hp - self.enemy_hp)
        self._apply_onhits(t, tag=" (E)", defer_terminus_stack=True)
        if self.has_rageblade and phantom_will_proc and timing == "instant":
            missing_at_cast = max(0.0, self.enemy_max_hp - self.enemy_hp)

        if (m := self._rune(9923)) and self.hob_stacks > 0:
            dmg = (self._lerp(m["true_lo"], m["true_hi"])
                   + m["bonus_ad"] * self.bonus_ad + m["ap"] * self.ap)
            self._deal(dmg, "true", "Hail of Blades", t)
            self.hob_stacks -= 1
        if (m := self._rune(8008)) and self.lt_stacks >= m["max_stacks"]:
            lo, hi = m["bolt_melee"] if self.is_melee else m["bolt_ranged"]
            amp = m["bolt_amp_melee"] if self.is_melee else m["bolt_amp_ranged"]
            self._adaptive_deal(
                self._lerp(lo, hi) * (1 + self._bonus_as_pct * amp),
                "Lethal Tempo bolt", t)
        if (m := self._rune(8437)) and self._grasp_stacks(t) >= m["stacks"]:
            pct = m["dmg_melee"] if self.is_melee else m["dmg_ranged"]
            self._deal(pct * self.kayle_max_hp, "magic", "Grasp of the Undying", t)
            hpct = m["heal_melee"] if self.is_melee else m["heal_ranged"]
            self._heal(hpct * self.kayle_max_hp, "Grasp heal", t)
            self.grasp_consumed_at = t

        # E primes and immediately consumes Spellblade. Dusk & Dawn then
        # repeats normal on-hits once and grants another PTA application.
        self._consume_spellblade(t)

        pct = (E["active_missing_hp_pct"][rank - 1]
               + E["active_missing_hp_per100ap"] * self.ap / 100.0) / 100.0
        if missing_at_cast > 0:
            self._deal(pct * missing_at_cast, "magic", "E active (missing HP)", t)
            self._apply_bloodletter_stack(t, "e_active")

        # Passive fire wave and Rageblade also treat E as an attack.
        transcendent = self.level >= PASSIVE["transcendent_level"]
        exalted = transcendent or self.zeal >= PASSIVE["zeal_max_stacks"]
        if self.level >= PASSIVE["aflame_level"] and exalted:
            self._fire_wave(t)
        self._terminus_hit(t)
        if self.has_rageblade:
            rb = ITEMS["guinsoos_rageblade"]["seething"]
            was_at_max = self.seething >= rb["max_stacks"]
            self.seething = min(rb["max_stacks"], self.seething + 1)
            if was_at_max:
                if self.phantom == 2:
                    self.phantom = 0
                    self.scheduled.append(
                        [t + 0.15, lambda tt: self._apply_onhits(tt, tag=" (Phantom Hit)")])
                else:
                    self.phantom += 1

        self._conqueror_heal(attack_dealt, t)
        self._dark_harvest(t)
        self._trigger_fleet(t)
        self.attack_count += 1
        self._finish_basic_attack()
        self._finish_yun_tal_attack(t, crit_chance_snapshot)
        # No cast time; advance one game tick so later actions are not on the
        # PTA proc's frame.
        self._advance(0.033)

    def _dd_repeat(self, at_time):
        """Dusk and Dawn's 'applies on-hit effects again' — instant (same
        frame), once per Spellblade priming, and grants a PTA application.
        Clean E reaches two stacks; AA into E reaches three and procs PTA."""
        if (self.spellblade_key and self.spellblade_primed
                and ITEMS[self.spellblade_key]["spellblade"].get("repeats_onhits")
                and not self.dd_repeat_used):
            self.dd_repeat_used = True
            self._apply_onhits(at_time, tag=" (D&D repeat)")

    def do_r(self):
        self._refresh_dynamic_stats(self.time)
        rank = self.ranks.get("R", 0)
        if rank == 0:
            self.warnings.append("R used with no rank — skipped.")
            return
        if not self._check_cd(
                "R", self._hasted(R["cooldown"][rank - 1], ultimate=True), "R"):
            return

        if self.has_experimental_hexplate:
            overdrive = ITEMS["experimental_hexplate"]["overdrive"]
            if self.time >= self.hexplate_ready_at - 1e-9:
                self.hexplate_overdrive_until = self.time + overdrive["duration"]
                self.hexplate_ready_at = self.time + overdrive["cooldown"]
                self._refresh_dynamic_stats(self.time)
                self.events.append({
                    "t": round(self.time, 3),
                    "source": (
                        "Experimental Hexplate — Overdrive: 35% AS, 14% MS "
                        f"until t={self.hexplate_overdrive_until:.2f}s"),
                    "type": "note", "pre": 0, "dealt": 0,
                })
            else:
                self.warnings.append(
                    "Experimental Hexplate Overdrive is still on cooldown; "
                    "this R cast does not refresh it.")

        dmg = (R["base"][rank - 1]
               + R["bonus_ad_ratio"] * self.bonus_ad
               + R["ap_ratio"] * self.ap)
        if (m := self._rune(8224)):    # Axiom Arcanist (R is AoE → 8%)
            dmg *= 1 + m["amp_aoe"]
        impact = self.time + R["impact_delay"]
        self.events.append({
            "t": round(self.time, 3),
            "source": (
                "Divine Judgment cast: damage lands "
                f"at t={impact:.2f}s (+{R['impact_delay']:.2f}s)"),
            "type": "note", "pre": 0, "dealt": 0,
        })

        if self.has_fiendhunter:
            opening = ITEMS["fiendhunter_bolts"]["opening_barrage"]
            if self.time >= self.fiendhunter_ready_at - 1e-9:
                self.fiendhunter_attacks = opening["attacks"]
                self.fiendhunter_until = self.time + opening["duration"]
                self.fiendhunter_ready_at = self.time + opening["cooldown"]
            else:
                self.warnings.append(
                    "Fiendhunter Bolts Opening Barrage is still on cooldown; "
                    "this R cast does not refresh it.")

        def land(tt, d=dmg):
            self._refresh_dynamic_stats(tt)
            self._on_action_damage(tt, is_ability=True)
            self._cast_common(tt)
            self._deal(d, "magic", "R — Divine Judgment", tt)
            self._apply_bloodletter_stack(tt, "r")
            self._dark_harvest(tt)
        self.scheduled.append([impact, land])
        self._prime_spellblade()
        self._advance(R["cast_time"])

    def do_item_active(self, key):
        self._refresh_dynamic_stats(self.time)
        if key not in self.items:
            self.warnings.append(
                f"{ITEMS.get(key, {}).get('name', key)} active skipped — item not in this build.")
            return
        it = ITEMS[key]
        act = it.get("active")
        if not act:
            return
        if not self._check_cd(
                f"active:{key}", act["cooldown"], f"{it['name']} active"):
            return
        if act["kind"] == "damage":
            t = self.time
            self._on_action_damage(t, is_item=True)   # item effect: Aery/Electrocute
            dmg = (lerp_by_level(
                       act["base_lo"], act["base_hi"], self.level, cap_lvl=20)
                   + act["ap_ratio"] * self.ap)
            self._deal(dmg, "magic", f"{it['name']} active", t)
            self._dark_harvest(t)
            self.slowed_until = max(self.slowed_until, t + 1.5)  # Gunblade slow
        elif act["kind"] == "stasis":
            self._advance(act["duration"])
            self.events.append({
                "t": round(self.time, 3), "source": f"{it['name']} — Stasis (2.5s, no actions)",
                "type": "note", "pre": 0, "dealt": 0,
            })

    # ---------- run ----------

    def _peak_damage_window(self, seconds=1.0):
        """Return the highest applied damage in any rolling time window."""
        instances = sorted(self.damage_instances, key=lambda event: event[0])
        if not instances:
            return 0.0, None, None

        left = 0
        running = 0.0
        best_damage = 0.0
        best_start = instances[0][0]
        for right, (at_time, dealt) in enumerate(instances):
            running += dealt
            while (left <= right
                   and at_time - instances[left][0] > seconds + 1e-9):
                running -= instances[left][1]
                left += 1
            if running > best_damage + 1e-9:
                best_damage = running
                best_start = instances[left][0]

        return best_damage, best_start, best_start + seconds

    def _practice_tool_dps_window(self):
        """Return the time window used by the Practice Tool DPS display.

        The target dummy starts timing on the first damage timestamp and stops
        on the latest one.  A single-hit combo has no elapsed damage span, so
        the Practice Tool reports its total damage as DPS (a one-second
        denominator).  Non-damaging setup and recovery time after the final
        hit are intentionally excluded.
        """
        if not self.damage_instances:
            return 0.0, None, None
        first = min(at_time for at_time, _ in self.damage_instances)
        last = max(at_time for at_time, _ in self.damage_instances)
        elapsed = last - first
        return (elapsed if elapsed > 1e-9 else 1.0), first, last

    def run(self):
        for action_index, action in enumerate(self.combo):
            self.current_action_index = action_index
            kind = action.get("type")
            # Fleet's movement-speed jump is delayed by 0.1 seconds in game.
            # When Fleet is selected, synchronize it automatically before the
            # next action rather than requiring a public WAIT combo action.
            if self.fleet_pending:
                sync_time = max(self.time, self.fleet_pending_at)
                if sync_time > self.time:
                    self._advance(sync_time - self.time)
                self._activate_pending_fleet(sync_time)
            if kind == "AA":
                self.do_attack()
            elif kind == "Q":
                self.do_q()
            elif kind == "W":
                self.do_w()
            elif kind == "E":
                self.do_e(action.get("timing", "instant"))
            elif kind == "R":
                self.do_r()
            elif kind == "ITEM_ACTIVE":
                self.do_item_active(action.get("item"))
            elif kind == "WAIT":
                self.do_wait(action.get("duration", FLEET_VISUAL_SYNC_DELAY))
        # If the combo ends on Fleet's triggering attack, report the stable
        # post-jump state instead of leaving the result panel at "pending".
        if self.fleet_pending:
            sync_time = max(self.time, self.fleet_pending_at)
            self._activate_pending_fleet(sync_time)
        # Let delayed effects resolve even when the user sequence has already
        # ended. In particular, an R cast at t=0 still lands at t=2.5 even if
        # the entered actions finish around t=1.5. This also includes
        # Stormsurge Squall, Phantom/D&D repeats, Comet/Scorch, and Deathfire
        # ticks; no manual WAIT is needed.
        self._flush_scheduled(1e9)
        self._refresh_dynamic_stats(self.time)

        totals = self.damage_totals
        pre_total = self.pre_mitigation_total
        total = sum(totals.values())
        duration, damage_start, damage_end = self._practice_tool_dps_window()
        gold = sum(ITEMS[k]["cost"] for k in self.items)
        burst_damage, burst_start, burst_end = self._peak_damage_window(1.0)

        return {
            "stats": {
                "level": self.level,
                "base_ad": round(self.base_ad, 1),
                "bonus_ad": round(self.bonus_ad, 1),
                "total_ad": round(self.total_ad, 1),
                "ap": round(self.ap, 1),
                "attack_speed_final": round(self.attack_speed(), 3),
                "movement_speed": round(self.current_movement_speed, 2),
                "swiftmarch_adaptive_force": round(self.swiftmarch_force, 2),
                "mid_role_quest_stat_bonus": (
                    8.0 if self.mid_role_quest_completed else 0.0),
                "dark_seal_glory_stacks": (
                    self.dark_seal_stacks if "dark_seal" in self.items else 0),
                "bonus_hp": self.bonus_hp,
                "max_hp": round(self.kayle_max_hp, 2),
                "ability_haste": self.haste,
                "ultimate_haste": self.ultimate_haste,
                "magic_pen_pct": round(self.pct_pen * 100, 1),
                "magic_pen_flat": self.flat_pen,
                "armor_pen_pct": round(self.armor_pct_pen * 100, 1),
                "crit_chance": round(self.crit_chance * 100, 1),
                "crit_damage": round(self.crit_damage * 100, 1),
                "life_steal": round(self.life_steal * 100, 1),
                "slow_resist": round(self.slow_resist, 1),
                "adaptive_type": "physical" if self.adaptive_physical else "magic",
            },
            "ranks": self.ranks,
            "calculation_model": "full_precision_v1",
            "critical_strike_model": "expected_damage",
            "totals": {k: round(v, 2) for k, v in totals.items()},
            "total_damage": round(total, 2),
            "pre_mitigation_total": round(pre_total, 2),
            "mitigated_pct": round(100 * (1 - total / pre_total), 1) if pre_total else 0,
            "duration": round(duration, 3),
            "timeline_duration": round(self.end_time, 3),
            "damage_window": {
                "start": round(damage_start, 3) if damage_start is not None else None,
                "end": round(damage_end, 3) if damage_end is not None else None,
            },
            "dps": round(total / duration, 1) if duration else 0.0,
            "burst_damage_1s": round(burst_damage, 2),
            "burst_window_1s": {
                "start": round(burst_start, 3) if burst_start is not None else None,
                "end": round(burst_end, 3) if burst_end is not None else None,
            },
            "attack_count": self.attack_count,
            "kill_time": round(self.kill_time, 3) if self.kill_time is not None else None,
            "gold_cost": gold,
            "damage_per_1k_gold": round(total / gold * 1000, 1) if gold else None,
            "healing": round(self.heal_total, 1),
            "enemy": {
                "max_hp": round(self.enemy_max_hp, 1),
                "bonus_hp": round(self.enemy_bonus_hp, 1),
                "remaining_hp": round(max(0.0, self.enemy_hp), 2),
                "killed": self.enemy_hp <= 0,
            },
            "events": self.events,
            "cooldown_errors": self.cooldown_errors,
            "warnings": self.warnings,
        }


def simulate_build(level, ranks, item_keys, enemy, combo, options=None):
    if not ranks:
        ranks = default_ability_ranks(level)
    return Simulation(level, ranks, item_keys, enemy, combo, options).run()
