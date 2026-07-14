import { C, addBg, title, footer, text, card, table, bullet } from "./shared.mjs";

export async function slide04(presentation, ctx) {
  const slide = presentation.slides.add();
  addBg(slide, ctx);
  title(slide, ctx, 4, "方式一：Kimi WebBridge", "Kimi WebBridge");
  card(slide, ctx, 72, 145, 665, 110, { fill: "#f7fbff", stroke: "#b8cff5" });
  text(slide, ctx, 100, 168, 610, 62, "Kimi WebBridge 是面向 AI Agent 的浏览器扩展，可辅助打开网页、点击按钮、填写表单、提取信息，从而自动化繁琐网页操作。", { size: 20, color: C.ink });
  await ctx.addLucideIcon(slide, { icon: "Puzzle", x: 790, y: 154, w: 86, h: 86, color: C.teal, strokeWidth: 1.8 });
  text(slide, ctx, 902, 162, 235, 32, "更适合", { size: 22, bold: true, color: C.teal });
  text(slide, ctx, 902, 205, 260, 58, "资料型、信息型、\n网页操作型任务", { size: 22, bold: true, color: C.ink });

  text(slide, ctx, 78, 300, 260, 28, "适合任务", { size: 23, bold: true, color: C.blueDark });
  const tasks = ["网页资料检索", "多网页信息整理", "表单内容辅助填写", "网页内容提取", "比赛、课程、调研资料收集"];
  tasks.forEach((item, i) => bullet(slide, ctx, 88, 348 + i * 42, item, i % 2 ? C.blue : C.teal, 18, 420));

  table(slide, ctx, 565, 315, [165, 410], 62, [
    ["特点", "说明"],
    ["形式", "浏览器扩展插件"],
    ["使用对象", "普通学生、办公用户、资料整理场景"],
    ["核心价值", "让 AI 直接参与网页浏览和信息提取"],
  ], { size: 16, headFill: C.teal });

  footer(slide, ctx, 4, "参考：Kimi WebBridge 官方/项目介绍对浏览器打开、点击、填写与信息提取能力的描述。");
  return slide;
}

export default slide04;
