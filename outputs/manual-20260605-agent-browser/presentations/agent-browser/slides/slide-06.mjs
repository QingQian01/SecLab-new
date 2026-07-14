import { C, addBg, title, footer, table, quote } from "./shared.mjs";

export async function slide06(presentation, ctx) {
  const slide = presentation.slides.add();
  addBg(slide, ctx);
  title(slide, ctx, 6, "两种方式对比", "Comparison");
  table(slide, ctx, 60, 150, [220, 460, 460], 72, [
    ["对比维度", "Kimi WebBridge", "Codex 浏览器接入"],
    ["主要定位", "通用网页任务", "编程与 Web 项目开发"],
    ["典型场景", "查资料、提取信息、整理网页内容", "前端调试、页面预览、项目测试"],
    ["使用难度", "相对低", "更适合有代码基础的用户"],
    ["大学生适用场景", "报告、调研、比赛资料整理", "课程设计、前端作业、项目开发"],
    ["核心优势", "减少网页重复操作", "结合代码和页面效果进行修改"],
  ], { size: 15, headFill: C.blueDark });
  quote(slide, ctx, 170, 600, 900, 68, "一个偏“信息处理”，一个偏“开发调试”。", C.orange);
  footer(slide, ctx, 6);
  return slide;
}

export default slide06;
