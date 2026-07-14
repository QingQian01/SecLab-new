import { C, addBg, title, footer, text, card, table, quote } from "./shared.mjs";

export async function slide07(presentation, ctx) {
  const slide = presentation.slides.add();
  addBg(slide, ctx, "#fbfcff");
  title(slide, ctx, 7, "实用案例一：课程报告资料整理", "Case 1");

  card(slide, ctx, 74, 145, 1060, 82, { fill: "#edf6ff", stroke: "#b8cff5" });
  await ctx.addLucideIcon(slide, { icon: "Presentation", x: 98, y: 163, w: 42, h: 42, color: C.blue, strokeWidth: 2.1 });
  text(slide, ctx, 160, 162, 960, 44, "老师要求做一个关于“AI Agent 应用现状”的课程展示，需要查资料、找案例、整理观点。", { size: 22, bold: true, color: C.ink, valign: "middle" });

  table(slide, ctx, 78, 270, [260, 360, 360], 62, [
    ["环节", "传统方式", "Agent 辅助方式"],
    ["找资料", "人搜索关键词", "Agent 初步检索相关网页"],
    ["处理内容", "人复制粘贴", "Agent 提取核心观点"],
    ["整理结构", "人从零开始", "Agent 生成表格和初稿"],
    ["最终判断", "边找边改，耗时长", "人负责审核、改写和引用"],
  ], { size: 15, headFill: C.teal });

  quote(slide, ctx, 152, 580, 915, 72, "最终效果：从“人工复制资料”变成“人工审核和改写资料”。", C.teal);
  footer(slide, ctx, 7);
  return slide;
}

export default slide07;
