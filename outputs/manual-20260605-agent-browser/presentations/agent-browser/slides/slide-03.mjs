import { C, addBg, title, footer, text, card, quote } from "./shared.mjs";

export async function slide03(presentation, ctx) {
  const slide = presentation.slides.add();
  addBg(slide, ctx, "#fbfcff");
  title(slide, ctx, 3, "什么是 Agent 连接浏览器", "Concept");
  text(slide, ctx, 72, 140, 1060, 58, "Agent 连接浏览器，是指 AI 在用户授权下，能够读取网页内容、点击页面、填写信息、观察结果，并根据网页反馈继续完成任务。", { size: 22, color: C.ink });

  const steps = [
    ["UserRound", "用户提出任务"],
    ["Brain", "Agent 理解目标"],
    ["MousePointerClick", "浏览器执行"],
    ["PanelTopOpen", "网页返回结果"],
    ["FileText", "Agent 整理输出"],
  ];
  let x = 82;
  for (let i = 0; i < steps.length; i += 1) {
    const [icon, label] = steps[i];
    card(slide, ctx, x, 270, 190, 116, { fill: i % 2 === 0 ? C.tealSoft : "#edf3ff", stroke: i % 2 === 0 ? "#9ddbd3" : "#aac4ff" });
    await ctx.addLucideIcon(slide, { icon, x: x + 72, y: 288, w: 44, h: 44, color: i % 2 === 0 ? C.teal : C.blue, strokeWidth: 2.1 });
    text(slide, ctx, x + 16, 343, 158, 28, label, { size: 18, bold: true, align: "center" });
    if (i < steps.length - 1) {
      ctx.addShape(slide, { x: x + 200, y: 326, w: 36, h: 4, fill: C.orange, line: ctx.line() });
      ctx.addShape(slide, { geometry: "triangle", x: x + 230, y: 316, w: 20, h: 20, fill: C.orange, line: ctx.line() });
    }
    x += 236;
  }

  card(slide, ctx, 164, 440, 920, 72, { fill: C.white, stroke: C.line });
  text(slide, ctx, 200, 459, 860, 30, "打开网页、点击按钮、填写表单、读取内容、观察反馈、继续执行", { size: 24, bold: true, color: C.blueDark, align: "center" });
  quote(slide, ctx, 145, 570, 950, 70, "核心变化：AI 不再只生成答案，而是能参与网页任务执行。", C.teal);
  footer(slide, ctx, 3);
  return slide;
}

export default slide03;
