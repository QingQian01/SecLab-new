import { C, addBg, title, footer, text, card, iconLabel, quote } from "./shared.mjs";

export async function slide05(presentation, ctx) {
  const slide = presentation.slides.add();
  addBg(slide, ctx, "#fbfcff");
  title(slide, ctx, 5, "方式二：Codex 浏览器接入", "Codex Browser");

  card(slide, ctx, 72, 150, 520, 370, { fill: C.white, stroke: "#b8cff5", strokeWidth: 2 });
  text(slide, ctx, 102, 176, 420, 34, "1. Codex in-app browser", { size: 25, bold: true, color: C.blueDark });
  text(slide, ctx, 102, 222, 438, 70, "可在同一个 Codex 线程里查看渲染后的网页，适合构建或调试 Web 应用时预览页面，并添加视觉评论。", { size: 18, color: C.ink });
  await iconLabel(slide, ctx, "MonitorSmartphone", 105, 330, "前端页面调试", "布局、按钮、颜色、间距", C.blue);
  await iconLabel(slide, ctx, "Eye", 105, 420, "效果验证", "代码修改后再预览检查", C.teal);

  card(slide, ctx, 670, 150, 520, 370, { fill: C.white, stroke: "#ffd6a3", strokeWidth: 2 });
  text(slide, ctx, 700, 176, 430, 34, "2. Codex Chrome extension", { size: 25, bold: true, color: C.orange });
  text(slide, ctx, 700, 222, 438, 70, "用于需要登录状态的浏览器任务，例如读取或操作用户已经登录的网站，并把浏览器上下文带给 Codex。", { size: 18, color: C.ink });
  await iconLabel(slide, ctx, "KeyRound", 702, 330, "登录后网页", "课程平台、后台页面、私有文档", C.orange);
  await iconLabel(slide, ctx, "Code2", 702, 420, "结合代码上下文", "更适合 Web 项目测试与调试", C.purple);

  quote(slide, ctx, 142, 555, 980, 76, "一句话总结：Kimi WebBridge 更偏通用网页任务，Codex 浏览器接入更偏代码开发和网页调试。", C.teal);
  footer(slide, ctx, 5, "参考：OpenAI Codex 官方文档中关于 in-app browser 与 Chrome extension 的说明。");
  return slide;
}

export default slide05;
