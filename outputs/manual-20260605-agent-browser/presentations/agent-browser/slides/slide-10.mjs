import { C, addBg, title, footer, text, card, bullet, quote } from "./shared.mjs";

export async function slide10(presentation, ctx) {
  const slide = presentation.slides.add();
  addBg(slide, ctx);
  title(slide, ctx, 10, "风险与使用边界", "Boundaries");

  card(slide, ctx, 78, 150, 760, 410, { fill: C.white, stroke: "#ffd6a3", strokeWidth: 2 });
  text(slide, ctx, 108, 176, 400, 30, "注意事项", { size: 26, bold: true, color: C.orange });
  bullet(slide, ctx, 116, 238, "不要把账号密码直接交给不可信插件", C.orange, 19, 650);
  bullet(slide, ctx, 116, 294, "不要让 Agent 自动提交重要表单", C.orange, 19, 650);
  bullet(slide, ctx, 116, 350, "涉及隐私、学校系统、个人账号时要谨慎授权", C.orange, 19, 650);
  bullet(slide, ctx, 116, 406, "生成内容不能直接照搬，需要人工复核", C.orange, 19, 650);
  bullet(slide, ctx, 116, 462, "资料引用要标明来源，避免学术不规范", C.orange, 19, 650);

  card(slide, ctx, 900, 170, 210, 210, { fill: C.orangeSoft, stroke: "#ffd6a3" });
  await ctx.addLucideIcon(slide, { icon: "ShieldAlert", x: 955, y: 214, w: 100, h: 100, color: C.orange, strokeWidth: 1.8 });
  text(slide, ctx, 928, 332, 154, 36, "效率提升\n不等于责任转移", { size: 19, bold: true, color: C.ink, align: "center" });

  quote(slide, ctx, 150, 610, 930, 60, "Agent 可以提高效率，但不能代替人的判断、责任和最终审核。", C.orange);
  footer(slide, ctx, 10);
  return slide;
}

export default slide10;
