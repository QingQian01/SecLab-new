import { C, addBg, title, footer, table, quote } from "./shared.mjs";

export async function slide02(presentation, ctx) {
  const slide = presentation.slides.add();
  addBg(slide, ctx);
  title(slide, ctx, 2, "过去的痛点：AI 只能“说”，不能“做”", "Pain Points");
  table(slide, ctx, 72, 150, [170, 820], 70, [
    ["场景", "过去的问题"],
    ["查资料", "AI 只能给搜索建议，网页还要自己一个个打开"],
    ["写报告", "资料复制、筛选、整理都要手动完成"],
    ["做网页项目", "AI 看不到真实页面效果，只能根据描述猜问题"],
    ["登录后网页", "AI 无法处理需要登录状态的页面"],
    ["多网页对比", "人工切换页面、复制信息，效率低"],
  ], { size: 17 });
  quote(slide, ctx, 72, 585, 990, 72, "传统 AI 更像“文字顾问”，但不能真正参与网页操作流程。", C.orange);
  await ctx.addLucideIcon(slide, { icon: "MessageSquareText", x: 1110, y: 160, w: 80, h: 80, color: C.blue, strokeWidth: 1.7 });
  await ctx.addLucideIcon(slide, { icon: "Hand", x: 1110, y: 284, w: 80, h: 80, color: "#b8c0cc", strokeWidth: 1.7 });
  await ctx.addLucideIcon(slide, { icon: "CircleSlash", x: 1134, y: 306, w: 38, h: 38, color: C.red, strokeWidth: 2.4 });
  footer(slide, ctx, 2);
  return slide;
}

export default slide02;
