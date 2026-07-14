import { C, FONT, text, card, pill } from "./shared.mjs";

export async function slide01(presentation, ctx) {
  const slide = presentation.slides.add();
  ctx.addShape(slide, { x: 0, y: 0, w: ctx.W, h: ctx.H, fill: "#f7fbff" });
  ctx.addShape(slide, { x: 0, y: 0, w: 430, h: ctx.H, fill: C.blueDark });
  ctx.addShape(slide, { x: 430, y: 0, w: 10, h: ctx.H, fill: C.teal });
  text(slide, ctx, 58, 66, 330, 30, "课程展示", { size: 18, color: "#b9d6ff", bold: true });
  text(slide, ctx, 58, 132, 350, 130, "Agent 连接\n浏览器", { size: 47, bold: true, color: C.white, face: FONT.title });
  text(slide, ctx, 58, 282, 355, 122, "让 AI 从回答问题\n变成执行网页任务", { size: 36, bold: true, color: C.white, face: FONT.title });
  text(slide, ctx, 62, 430, 340, 60, "以 Kimi WebBridge、\nCodex 浏览器接入为例", { size: 20, color: "#d9e8ff" });
  pill(slide, ctx, 62, 520, 146, 42, "AI Agent", C.teal, C.white);
  pill(slide, ctx, 225, 520, 160, 42, "Browser", C.orange, C.white);
  pill(slide, ctx, 62, 578, 220, 42, "网页任务执行", "#e5efff", C.blueDark);

  card(slide, ctx, 545, 92, 620, 410, { fill: C.white, stroke: "#b7c6d9", strokeWidth: 2 });
  ctx.addShape(slide, { x: 545, y: 92, w: 620, h: 48, fill: "#e9eef6", line: ctx.line("#b7c6d9", 2) });
  ctx.addShape(slide, { geometry: "ellipse", x: 566, y: 110, w: 14, h: 14, fill: C.red, line: ctx.line() });
  ctx.addShape(slide, { geometry: "ellipse", x: 588, y: 110, w: 14, h: 14, fill: C.orange, line: ctx.line() });
  ctx.addShape(slide, { geometry: "ellipse", x: 610, y: 110, w: 14, h: 14, fill: C.green, line: ctx.line() });
  card(slide, ctx, 650, 107, 470, 18, { fill: C.white, stroke: "#cbd5e1" });
  text(slide, ctx, 670, 104, 260, 24, "https://course.example/task", { size: 12, color: C.muted });

  card(slide, ctx, 595, 190, 242, 120, { fill: "#edf6ff", stroke: "#a7c7ff" });
  await ctx.addLucideIcon(slide, { icon: "Bot", x: 620, y: 218, w: 46, h: 46, color: C.blue, strokeWidth: 2.2 });
  text(slide, ctx, 682, 215, 120, 32, "Agent", { size: 26, bold: true, color: C.blueDark });
  text(slide, ctx, 682, 253, 118, 46, "理解目标\n规划操作", { size: 15, color: C.muted });

  card(slide, ctx, 895, 190, 232, 120, { fill: C.tealSoft, stroke: "#94d8ce" });
  await ctx.addLucideIcon(slide, { icon: "MousePointerClick", x: 922, y: 220, w: 46, h: 46, color: C.teal, strokeWidth: 2.2 });
  text(slide, ctx, 982, 215, 98, 32, "浏览器", { size: 26, bold: true, color: C.teal });
  text(slide, ctx, 982, 253, 105, 46, "打开、点击\n读取、输入", { size: 15, color: C.muted });

  ctx.addShape(slide, { x: 823, y: 246, w: 58, h: 5, fill: C.orange, line: ctx.line() });
  ctx.addShape(slide, { geometry: "triangle", x: 874, y: 236, w: 22, h: 22, fill: C.orange, line: ctx.line() });

  card(slide, ctx, 640, 355, 465, 66, { fill: "#fff8ec", stroke: "#ffd6a3" });
  await ctx.addLucideIcon(slide, { icon: "FileCheck", x: 662, y: 371, w: 30, h: 30, color: C.orange, strokeWidth: 2.2 });
  text(slide, ctx, 710, 368, 355, 34, "输出整理后的资料、代码建议或网页结果", { size: 19, bold: true, color: C.ink });
  text(slide, ctx, 545, 590, 640, 28, "核心变化：AI 不再只生成答案，而是参与网页任务执行。", { size: 23, bold: true, color: C.ink, align: "center" });
  return slide;
}

export default slide01;
