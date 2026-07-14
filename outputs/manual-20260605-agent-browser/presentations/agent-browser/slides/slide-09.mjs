import { C, addBg, title, footer, table, quote } from "./shared.mjs";

export async function slide09(presentation, ctx) {
  const slide = presentation.slides.add();
  addBg(slide, ctx, "#fbfcff");
  title(slide, ctx, 9, "大学生使用这个功能能达到什么效果", "Outcomes");
  table(slide, ctx, 88, 150, [230, 820], 72, [
    ["能力方向", "具体效果"],
    ["学习效率", "快速查找、整理、归纳课程资料"],
    ["作业完成", "辅助生成报告结构、表格、案例说明"],
    ["项目开发", "协助调试网页、检查页面效果"],
    ["竞赛准备", "整理竞品、政策、案例、技术资料"],
    ["信息判断", "把重复检索交给 Agent，把判断和修改留给自己"],
  ], { size: 17, headFill: C.blueDark });
  quote(slide, ctx, 116, 600, 1010, 68, "主要工作不再是机械搜索和复制，而是判断资料是否可靠、结构是否合理、结果是否符合任务要求。", C.teal);
  footer(slide, ctx, 9);
  return slide;
}

export default slide09;
