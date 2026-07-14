import { C, addBg, title, footer, text, card, bullet, quote } from "./shared.mjs";

export async function slide08(presentation, ctx) {
  const slide = presentation.slides.add();
  addBg(slide, ctx);
  title(slide, ctx, 8, "实用案例二：前端课程设计与项目调试", "Case 2");

  card(slide, ctx, 72, 145, 505, 390, { fill: C.white, stroke: "#ffd6a3", strokeWidth: 2 });
  text(slide, ctx, 102, 175, 240, 30, "过去的问题", { size: 25, bold: true, color: C.orange });
  bullet(slide, ctx, 108, 238, "AI 看不到页面，只能根据代码猜", C.orange, 18, 395);
  bullet(slide, ctx, 108, 292, "学生需要截图描述问题", C.orange, 18, 395);
  bullet(slide, ctx, 108, 346, "修改后还要反复刷新页面", C.orange, 18, 395);
  bullet(slide, ctx, 108, 400, "页面问题和代码位置不容易对应", C.orange, 18, 395);
  await ctx.addLucideIcon(slide, { icon: "ImageOff", x: 442, y: 176, w: 58, h: 58, color: "#c7a06f", strokeWidth: 1.8 });

  card(slide, ctx, 660, 145, 505, 390, { fill: C.white, stroke: "#9ddbd3", strokeWidth: 2 });
  text(slide, ctx, 690, 175, 330, 34, "Codex 浏览器接入后的作用", { size: 25, bold: true, color: C.teal });
  bullet(slide, ctx, 696, 238, "打开本地网页", C.teal, 18, 395);
  bullet(slide, ctx, 696, 292, "观察真实页面效果", C.teal, 18, 395);
  bullet(slide, ctx, 696, 346, "判断按钮、布局、样式问题", C.teal, 18, 395);
  bullet(slide, ctx, 696, 400, "修改对应代码，再预览验证结果", C.teal, 18, 395);
  await ctx.addLucideIcon(slide, { icon: "Code2", x: 1034, y: 176, w: 58, h: 58, color: C.teal, strokeWidth: 1.8 });

  quote(slide, ctx, 100, 575, 1060, 68, "对软件工程、计算机类学生来说，最直接的价值就是提高 Web 项目调试效率。", C.orange);
  footer(slide, ctx, 8);
  return slide;
}

export default slide08;
