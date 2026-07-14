export const C = {
  ink: "#172033",
  muted: "#5b6475",
  pale: "#f6f8fb",
  line: "#d9e1ea",
  blue: "#2156d9",
  blueDark: "#12357f",
  teal: "#0f9f8f",
  tealSoft: "#e7f7f4",
  orange: "#f28c28",
  orangeSoft: "#fff2e3",
  red: "#d94d4d",
  green: "#28a66a",
  purple: "#7c5cc4",
  white: "#ffffff",
};

export const FONT = {
  title: "Microsoft YaHei",
  body: "Microsoft YaHei",
};

export function addBg(slide, ctx, fill = C.white) {
  ctx.addShape(slide, { x: 0, y: 0, w: ctx.W, h: ctx.H, fill });
  ctx.addShape(slide, { x: 0, y: 0, w: 12, h: ctx.H, fill: C.blue });
  ctx.addShape(slide, { x: 12, y: 0, w: 5, h: ctx.H, fill: C.teal });
}

export function title(slide, ctx, page, text, kicker = "Agent + Browser") {
  ctx.addText(slide, {
    x: 58,
    y: 34,
    w: 30,
    h: 24,
    text: `0${page}`.slice(-2),
    fontSize: 16,
    bold: true,
    color: C.teal,
    typeface: FONT.body,
  });
  ctx.addText(slide, {
    x: 98,
    y: 30,
    w: 240,
    h: 28,
    text: kicker,
    fontSize: 15,
    color: C.muted,
    typeface: FONT.body,
  });
  ctx.addText(slide, {
    x: 58,
    y: 66,
    w: 900,
    h: 58,
    text,
    fontSize: 34,
    bold: true,
    color: C.ink,
    typeface: FONT.title,
  });
}

export function footer(slide, ctx, page, source = "") {
  ctx.addShape(slide, { x: 58, y: 675, w: 1060, h: 1, fill: C.line });
  ctx.addText(slide, {
    x: 58,
    y: 688,
    w: 900,
    h: 20,
    text: source,
    fontSize: 10,
    color: "#8a94a6",
    typeface: FONT.body,
  });
  ctx.addText(slide, {
    x: 1160,
    y: 686,
    w: 60,
    h: 20,
    text: String(page).padStart(2, "0"),
    fontSize: 12,
    bold: true,
    color: C.muted,
    align: "right",
    typeface: FONT.body,
  });
}

export function text(slide, ctx, x, y, w, h, content, opts = {}) {
  return ctx.addText(slide, {
    x, y, w, h,
    text: content,
    fontSize: opts.size ?? 20,
    bold: opts.bold ?? false,
    color: opts.color ?? C.ink,
    fill: opts.fill ?? "#00000000",
    line: opts.line ?? ctx.line(),
    align: opts.align ?? "left",
    valign: opts.valign ?? "top",
    insets: opts.insets ?? { left: 0, right: 0, top: 0, bottom: 0 },
    typeface: opts.face ?? FONT.body,
  });
}

export function card(slide, ctx, x, y, w, h, opts = {}) {
  return ctx.addShape(slide, {
    x, y, w, h,
    fill: opts.fill ?? C.white,
    line: opts.line ?? ctx.line(opts.stroke ?? C.line, opts.strokeWidth ?? 1),
  });
}

export async function iconLabel(slide, ctx, icon, x, y, titleText, bodyText, color = C.blue) {
  ctx.addShape(slide, { x, y, w: 54, h: 54, fill: color, line: ctx.line() });
  await ctx.addLucideIcon(slide, { icon, x: x + 13, y: y + 13, w: 28, h: 28, color: C.white, strokeWidth: 2.3 });
  text(slide, ctx, x + 72, y + 3, 300, 26, titleText, { size: 20, bold: true });
  text(slide, ctx, x + 72, y + 32, 340, 50, bodyText, { size: 15, color: C.muted });
}

export function bullet(slide, ctx, x, y, content, color = C.teal, size = 18, w = 420) {
  ctx.addShape(slide, { geometry: "ellipse", x, y: y + 7, w: 8, h: 8, fill: color, line: ctx.line() });
  text(slide, ctx, x + 18, y, w, 34, content, { size, color: C.ink });
}

export function pill(slide, ctx, x, y, w, h, label, fill, color = C.ink) {
  card(slide, ctx, x, y, w, h, { fill, stroke: "#00000000", strokeWidth: 0 });
  text(slide, ctx, x + 14, y + 8, w - 28, h - 10, label, { size: 15, bold: true, color, align: "center" });
}

export function table(slide, ctx, x, y, widths, rowH, rows, opts = {}) {
  let cy = y;
  rows.forEach((row, r) => {
    let cx = x;
    row.forEach((cell, c) => {
      const isHead = r === 0;
      const fill = isHead ? (opts.headFill ?? C.blueDark) : (r % 2 ? C.white : C.pale);
      const color = isHead ? C.white : C.ink;
      card(slide, ctx, cx, cy, widths[c], rowH, { fill, stroke: C.line });
      text(slide, ctx, cx + 12, cy + 9, widths[c] - 24, rowH - 12, cell, {
        size: isHead ? 15 : (opts.size ?? 14),
        bold: isHead,
        color,
        valign: "middle",
      });
      cx += widths[c];
    });
    cy += rowH;
  });
}

export function arrow(slide, ctx, x1, y1, x2, y2, color = C.teal) {
  const w = x2 - x1;
  const h = y2 - y1;
  ctx.addShape(slide, { x: x1, y: y1 - 2, w: w, h: 4, fill: color, line: ctx.line() });
  ctx.addShape(slide, { geometry: "triangle", x: x2 - 3, y: y2 - 11, w: 20, h: 20, fill: color, line: ctx.line() });
}

export function quote(slide, ctx, x, y, w, h, content, color = C.teal) {
  card(slide, ctx, x, y, w, h, { fill: color === C.orange ? C.orangeSoft : C.tealSoft, stroke: "#00000000" });
  ctx.addShape(slide, { x, y, w: 6, h, fill: color, line: ctx.line() });
  text(slide, ctx, x + 24, y + 18, w - 48, h - 28, content, { size: 21, bold: true, color: C.ink, valign: "middle" });
}
