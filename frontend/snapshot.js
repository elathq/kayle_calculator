/* Downloadable build-comparison images (dependency-free Canvas renderer). */
"use strict";

(function exposeSnapshotRenderer(root) {
  const WIDTH = 1400;
  const PAGE_PADDING = 28;
  const CARD_GAP = 16;
  const CARD_HEIGHT = 398;
  const HEADER_HEIGHT = 130;
  const FOOTER_HEIGHT = 44;
  const FONT = "Inter, Segoe UI, Arial, sans-serif";

  // Keep these aligned with the result-card variables in frontend/style.css.
  const COLORS = Object.freeze({
    background: "#0a0f14",
    surface: "#10171e",
    surfaceSoft: "#0c1218",
    line: "#25313b",
    lineBright: "#394752",
    text: "#e5e9ec",
    textSoft: "#b2bcc4",
    muted: "#74828d",
    gold: "#d4bd8b",
    goldFill: "#1c1c1a",
    purple: "#c8a4f0",
    purpleFill: "#1c1724",
    physical: "#e48b49",
    magic: "#62a6e8",
    trueDamage: "#e8edf0",
    health: "#d26969",
  });

  function finiteNumber(value, fallback = 0) {
    const number = Number(value);
    return Number.isFinite(number) ? number : fallback;
  }

  function formatNumber(value, maximumFractionDigits = 2) {
    return finiteNumber(value).toLocaleString("en-US", {
      minimumFractionDigits: 0,
      maximumFractionDigits,
    });
  }

  function itemFor(catalog, key) {
    const item = catalog[key] || {};
    return {
      key,
      name: item.name || key || "Unknown item",
      icon: item.icon || "",
      iconFallback: item.icon_fallback || "",
    };
  }

  function comboActionLabel(action, itemByKey) {
    if (action.type === "ITEM_ACTIVE") {
      return `${itemFor(itemByKey, action.item).name} active`;
    }
    if (action.type === "WAIT") {
      return `Wait ${formatNumber(action.duration)}s`;
    }
    return String(action.type || "?");
  }

  function buildSnapshotModel({ results, payload, itemByKey = {} }) {
    if (!Array.isArray(results) || results.length === 0) {
      throw new Error("Calculate at least one build before creating an image.");
    }
    if (!payload || typeof payload !== "object") {
      throw new Error("The calculated setup is unavailable.");
    }

    const bestDps = Math.max(...results.map((result) =>
      finiteNumber(result.dps)));
    const bestBurst = Math.max(...results.map((result) =>
      finiteNumber(result.burst_damage_1s)));
    const builds = Array.isArray(payload.builds) ? payload.builds : [];
    const enemy = payload.enemy || {};
    const ranks = payload.ability_ranks || {};
    const combo = Array.isArray(payload.combo) ? payload.combo : [];

    return {
      level: finiteNumber(payload.level, 1),
      ranks: ["Q", "W", "E", "R"]
        .map((ability) => `${ability}${finiteNumber(ranks[ability])}`)
        .join(" · "),
      target: [
        `${formatNumber(enemy.current_hp ?? enemy.hp)} / ${formatNumber(enemy.hp)} HP`,
        `${formatNumber(enemy.armor)} armor`,
        `${formatNumber(enemy.mr)} MR`,
      ].join(" · "),
      combo: combo.length
        ? combo.map((action) => comboActionLabel(action, itemByKey)).join(" → ")
        : "No combo actions",
      cards: results.map((result, index) => {
        const build = builds[index] || {};
        const itemKeys = Array.isArray(result.items)
          ? result.items
          : (build.items || []);
        const maxHp = Math.max(finiteNumber(result.enemy?.max_hp, enemy.hp), 1);
        const remainingHp = finiteNumber(result.enemy?.remaining_hp);
        const totals = result.totals || {};

        return {
          name: String(result.build_name || build.name || `Build ${index + 1}`),
          items: itemKeys.map((key) => itemFor(itemByKey, key)),
          totalDamage: finiteNumber(result.total_damage),
          dps: finiteNumber(result.dps),
          burst: finiteNumber(result.burst_damage_1s),
          physical: finiteNumber(totals.physical),
          magic: finiteNumber(totals.magic),
          trueDamage: finiteNumber(totals.true),
          duration: finiteNumber(result.duration),
          attacks: finiteNumber(result.attack_count),
          killTime: result.kill_time === null || result.kill_time === undefined
            ? null : finiteNumber(result.kill_time),
          attackSpeed: finiteNumber(result.stats?.attack_speed_final),
          ad: finiteNumber(result.stats?.total_ad),
          ap: finiteNumber(result.stats?.ap),
          critChance: finiteNumber(result.stats?.crit_chance),
          critDamage: finiteNumber(result.stats?.crit_damage),
          remainingHp,
          remainingHpPct: Math.max(0, Math.min(100, 100 * remainingHp / maxHp)),
          killed: Boolean(result.enemy?.killed),
          topDps: results.length > 1 && finiteNumber(result.dps) === bestDps,
          topBurst: results.length > 1
            && finiteNumber(result.burst_damage_1s) === bestBurst,
        };
      }),
    };
  }

  function snapshotDimensions(cardCount) {
    const columns = cardCount === 1 ? 1 : 2;
    const rows = Math.ceil(cardCount / columns);
    return {
      width: WIDTH,
      height: HEADER_HEIGHT
        + rows * CARD_HEIGHT
        + Math.max(0, rows - 1) * CARD_GAP
        + FOOTER_HEIGHT,
      columns,
    };
  }

  function roundedRect(ctx, x, y, width, height, radius) {
    const r = Math.min(radius, width / 2, height / 2);
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + width - r, y);
    ctx.quadraticCurveTo(x + width, y, x + width, y + r);
    ctx.lineTo(x + width, y + height - r);
    ctx.quadraticCurveTo(x + width, y + height, x + width - r, y + height);
    ctx.lineTo(x + r, y + height);
    ctx.quadraticCurveTo(x, y + height, x, y + height - r);
    ctx.lineTo(x, y + r);
    ctx.quadraticCurveTo(x, y, x + r, y);
    ctx.closePath();
  }

  function fillRoundedRect(ctx, x, y, width, height, radius, fill) {
    roundedRect(ctx, x, y, width, height, radius);
    ctx.fillStyle = fill;
    ctx.fill();
  }

  function strokeRoundedRect(ctx, x, y, width, height, radius, stroke) {
    roundedRect(ctx, x, y, width, height, radius);
    ctx.strokeStyle = stroke;
    ctx.lineWidth = 1;
    ctx.stroke();
  }

  function fitText(ctx, text, maxWidth) {
    const value = String(text);
    if (ctx.measureText(value).width <= maxWidth) return value;
    let shortened = value;
    while (shortened.length > 1
        && ctx.measureText(`${shortened}…`).width > maxWidth) {
      shortened = shortened.slice(0, -1);
    }
    return `${shortened}…`;
  }

  function drawText(ctx, text, x, y, {
    color = COLORS.text,
    font = `16px ${FONT}`,
    maxWidth,
    align = "left",
  } = {}) {
    ctx.fillStyle = color;
    ctx.font = font;
    ctx.textAlign = align;
    ctx.textBaseline = "alphabetic";
    const rendered = maxWidth ? fitText(ctx, text, maxWidth) : String(text);
    ctx.fillText(rendered, x, y);
  }

  function drawMetric(ctx, x, y, width, label, value) {
    fillRoundedRect(ctx, x, y, width, 72, 8, COLORS.surfaceSoft);
    strokeRoundedRect(ctx, x, y, width, 72, 8, "#20313e");
    drawText(ctx, label, x + 13, y + 25, {
      color: COLORS.muted,
      font: `600 12px ${FONT}`,
      maxWidth: width - 26,
    });
    drawText(ctx, value, x + 13, y + 57, {
      font: `600 25px ${FONT}`,
      maxWidth: width - 26,
    });
  }

  function drawPill(ctx, label, rightX, y, {
    border,
    fill,
    color,
  }) {
    ctx.font = `800 10px ${FONT}`;
    const width = Math.ceil(ctx.measureText(label).width) + 18;
    fillRoundedRect(ctx, rightX - width, y, width, 23, 12, fill);
    strokeRoundedRect(ctx, rightX - width, y, width, 23, 12, border);
    drawText(ctx, label, rightX - width / 2, y + 16, {
      color,
      font: `800 10px ${FONT}`,
      align: "center",
    });
    return rightX - width - 7;
  }

  function drawBadges(ctx, card, rightX, y) {
    let cursor = rightX;
    if (card.topBurst) {
      cursor = drawPill(ctx, "TOP BURST", cursor, y, {
        border: "#6f4f8d",
        fill: COLORS.purpleFill,
        color: COLORS.purple,
      });
    }
    if (card.topDps) {
      drawPill(ctx, "TOP DPS", cursor, y, {
        border: "#756744",
        fill: COLORS.goldFill,
        color: COLORS.gold,
      });
    }
  }

  function drawLegendEntry(ctx, x, y, color, label, value) {
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(x + 4, y - 4, 4, 0, Math.PI * 2);
    ctx.fill();
    drawText(ctx, `${label} ${formatNumber(value)}`, x + 14, y, {
      color: COLORS.muted,
      font: `12px ${FONT}`,
    });
  }

  function drawStatRow(ctx, x, y, width, label, value, strong = false) {
    drawText(ctx, label, x, y, {
      color: COLORS.muted,
      font: `13px ${FONT}`,
      maxWidth: width * 0.54,
    });
    drawText(ctx, value, x + width, y, {
      color: strong ? COLORS.text : COLORS.textSoft,
      font: `${strong ? "600" : "400"} 13px ${FONT}`,
      maxWidth: width * 0.46,
      align: "right",
    });
  }

  function drawItemIcons(ctx, card, iconImages, x, y, maxWidth) {
    if (!card.items.length) {
      drawText(ctx, "No items", x, y + 20, {
        color: COLORS.muted,
        font: `13px ${FONT}`,
      });
      return;
    }
    const size = 29;
    const gap = 6;
    card.items.slice(0, 6).forEach((item, index) => {
      const iconX = x + index * (size + gap);
      if (iconX + size > x + maxWidth) return;
      fillRoundedRect(ctx, iconX, y, size, size, 5, COLORS.surfaceSoft);
      const image = iconImages.get(item.key);
      if (image) {
        ctx.save();
        roundedRect(ctx, iconX, y, size, size, 5);
        ctx.clip();
        ctx.drawImage(image, iconX, y, size, size);
        ctx.restore();
      } else {
        drawText(ctx, item.name.slice(0, 1), iconX + size / 2, y + 20, {
          color: COLORS.muted,
          font: `700 13px ${FONT}`,
          align: "center",
        });
      }
      strokeRoundedRect(ctx, iconX, y, size, size, 5, COLORS.line);
    });
  }

  function drawCard(ctx, card, iconImages, x, y, width) {
    fillRoundedRect(ctx, x, y, width, CARD_HEIGHT, 10, COLORS.surface);
    const border = card.topDps
      ? "#786c4d"
      : card.topBurst
        ? "#69507d"
        : COLORS.line;
    strokeRoundedRect(ctx, x, y, width, CARD_HEIGHT, 10, border);
    const innerX = x + 18;
    const innerWidth = width - 36;

    drawText(ctx, card.name, innerX, y + 31, {
      font: `700 18px ${FONT}`,
      maxWidth: innerWidth - 190,
    });
    drawBadges(ctx, card, x + width - 18, y + 13);
    drawItemIcons(ctx, card, iconImages, innerX, y + 44, innerWidth);

    const metricGap = 8;
    const metricWidth = (innerWidth - metricGap * 2) / 3;
    drawMetric(
      ctx, innerX, y + 84, metricWidth,
      "TOTAL DAMAGE", formatNumber(card.totalDamage),
    );
    drawMetric(
      ctx, innerX + metricWidth + metricGap, y + 84, metricWidth,
      "DPS", `≈${formatNumber(card.dps)}`,
    );
    drawMetric(
      ctx, innerX + (metricWidth + metricGap) * 2, y + 84, metricWidth,
      "1S BURST", formatNumber(card.burst),
    );

    const barY = y + 173;
    const damageTotal = Math.max(
      card.physical + card.magic + card.trueDamage,
      0.001,
    );
    const physicalWidth = innerWidth * card.physical / damageTotal;
    const magicWidth = innerWidth * card.magic / damageTotal;
    fillRoundedRect(ctx, innerX, barY, innerWidth, 8, 4, COLORS.surfaceSoft);
    ctx.save();
    roundedRect(ctx, innerX, barY, innerWidth, 8, 4);
    ctx.clip();
    ctx.fillStyle = COLORS.physical;
    ctx.fillRect(innerX, barY, physicalWidth, 8);
    ctx.fillStyle = COLORS.magic;
    ctx.fillRect(innerX + physicalWidth, barY, magicWidth, 8);
    ctx.fillStyle = COLORS.trueDamage;
    ctx.fillRect(
      innerX + physicalWidth + magicWidth,
      barY,
      innerWidth - physicalWidth - magicWidth,
      8,
    );
    ctx.restore();

    const legendY = y + 204;
    drawLegendEntry(ctx, innerX, legendY, COLORS.physical, "Physical", card.physical);
    drawLegendEntry(
      ctx, innerX + innerWidth / 3, legendY,
      COLORS.magic, "Magic", card.magic,
    );
    drawLegendEntry(
      ctx, innerX + innerWidth * 2 / 3, legendY,
      COLORS.trueDamage, "True", card.trueDamage,
    );

    const rows = [
      ["Attacks / DPS window",
        `${formatNumber(card.attacks, 0)} in ${formatNumber(card.duration)}s`],
      ["Attack speed", formatNumber(card.attackSpeed, 3)],
      ["AD / AP", `${formatNumber(card.ad)} / ${formatNumber(card.ap)}`],
      ["Critical strikes",
        `${formatNumber(card.critChance)}% at ${formatNumber(card.critDamage)}%`],
      ["Kill time",
        card.killTime === null ? "—" : `${formatNumber(card.killTime)}s`],
      ["Enemy HP left",
        card.killed
          ? "DEAD"
          : `${formatNumber(card.remainingHp)} (${formatNumber(card.remainingHpPct, 1)}%)`],
    ];
    rows.forEach(([label, value], index) => {
      drawStatRow(
        ctx,
        innerX,
        y + 239 + index * 23,
        innerWidth,
        label,
        value,
        label === "Enemy HP left",
      );
    });

    fillRoundedRect(ctx, innerX, y + 378, innerWidth, 5, 3, COLORS.surfaceSoft);
    if (!card.killed && card.remainingHpPct > 0) {
      fillRoundedRect(
        ctx,
        innerX,
        y + 378,
        innerWidth * card.remainingHpPct / 100,
        5,
        3,
        COLORS.health,
      );
    }
  }

  async function loadImage(candidates) {
    for (const source of candidates.filter(Boolean)) {
      const image = new Image();
      image.decoding = "async";
      const loaded = await new Promise((resolve) => {
        image.addEventListener("load", () => resolve(true), { once: true });
        image.addEventListener("error", () => resolve(false), { once: true });
        image.src = source;
      });
      if (loaded) return image;
    }
    return null;
  }

  async function loadItemIcons(model) {
    const uniqueItems = new Map();
    model.cards.forEach((card) => card.items.forEach((item) => {
      if (!uniqueItems.has(item.key)) uniqueItems.set(item.key, item);
    }));
    const loaded = await Promise.all([...uniqueItems.values()].map(
      async (item) => [
        item.key,
        await loadImage([item.icon, item.iconFallback]),
      ],
    ));
    return new Map(loaded);
  }

  function drawImage(canvas, model, iconImages, createdAt) {
    const { width, height, columns } = snapshotDimensions(model.cards.length);
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext("2d");
    if (!ctx) throw new Error("This browser cannot create a sharing canvas.");

    ctx.fillStyle = COLORS.background;
    ctx.fillRect(0, 0, width, height);

    drawText(ctx, "Kayle Calculator", PAGE_PADDING, 42, {
      font: `700 32px ${FONT}`,
    });
    drawText(
      ctx,
      `BUILD COMPARISON  ·  LEVEL ${model.level}  ·  ${model.ranks}`,
      PAGE_PADDING,
      70,
      {
        color: COLORS.gold,
        font: `700 12px ${FONT}`,
        maxWidth: width - PAGE_PADDING * 2,
      },
    );
    drawText(ctx, `Target: ${model.target}`, PAGE_PADDING, 98, {
      color: COLORS.textSoft,
      font: `14px ${FONT}`,
      maxWidth: width * 0.48,
    });
    drawText(ctx, `Combo: ${model.combo}`, width - PAGE_PADDING, 98, {
      color: COLORS.muted,
      font: `14px ${FONT}`,
      maxWidth: width * 0.48,
      align: "right",
    });

    ctx.strokeStyle = COLORS.line;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(PAGE_PADDING, 115);
    ctx.lineTo(width - PAGE_PADDING, 115);
    ctx.stroke();

    const cardWidth = columns === 1
      ? width - PAGE_PADDING * 2
      : (width - PAGE_PADDING * 2 - CARD_GAP) / 2;
    model.cards.forEach((card, index) => {
      const column = index % columns;
      const row = Math.floor(index / columns);
      drawCard(
        ctx,
        card,
        iconImages,
        PAGE_PADDING + column * (cardWidth + CARD_GAP),
        HEADER_HEIGHT + row * (CARD_HEIGHT + CARD_GAP),
        cardWidth,
      );
    });

    const footerY = height - 17;
    drawText(ctx, "Kayle Calculator", PAGE_PADDING, footerY, {
      color: COLORS.muted,
      font: `12px ${FONT}`,
    });
    drawText(ctx, createdAt.toLocaleString(), width - PAGE_PADDING, footerY, {
      color: COLORS.muted,
      font: `12px ${FONT}`,
      align: "right",
    });
  }

  async function createComparisonSnapshot(options) {
    if (typeof document === "undefined" || typeof Image === "undefined") {
      throw new Error("Image rendering requires a browser.");
    }
    const model = buildSnapshotModel(options);
    const iconImages = await loadItemIcons(model);
    const canvas = document.createElement("canvas");
    drawImage(canvas, model, iconImages, options.createdAt || new Date());
    return new Promise((resolve, reject) => {
      canvas.toBlob((blob) => {
        if (blob) resolve(blob);
        else reject(new Error("The browser could not encode the image."));
      }, "image/png");
    });
  }

  const api = Object.freeze({
    buildSnapshotModel,
    createComparisonSnapshot,
    formatNumber,
    snapshotDimensions,
  });

  root.ComparisonSnapshot = api;
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
}(typeof globalThis !== "undefined" ? globalThis : window));
