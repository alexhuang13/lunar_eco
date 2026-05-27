7:version7
界面风格化（方案一 · Streamlit CSS 套皮）设计文档

# 天外家园 · 界面风格化设计草案 v7

> 目标：在**不改动任何游戏逻辑**的前提下，通过注入自定义 CSS，把现有 Streamlit 界面套上 LIFE BEYOND 那种「深色背景 + 毛玻璃 + 青绿科幻」皮肤。
> 方案一 = 最省力、零逻辑风险，预期还原度约 **60%**。

---

## 一、为什么选方案一

现有 `game.py` 的游戏逻辑已经完整（电力、净水、科研、天赋、健康、初始化锁定，做到 v6），界面用的是标准 Streamlit 组件：`st.columns` + `st.metric`、`st.sidebar`、`st.expander`、`st.table`、`st.pyplot`。

方案一只在文件顶部注入一段 CSS，**不碰任何 `step_system` 或数据逻辑**：
- 改动量：约 60–100 行 CSS，集中在一处；
- 风险：零逻辑风险（纯样式）；
- 见效：半天内能看到套皮效果。

代价是还原度有天花板（见第四节「做得到 / 做不到」）。

---

## 二、实现方式

在 `game.py` 的 `st.set_page_config(...)` 之后、其他 UI 代码之前，插入一个注入函数并调用：

```python
def inject_style():
    st.markdown("""
    <style>
    /* 见第三节的完整 CSS */
    </style>
    """, unsafe_allow_html=True)

inject_style()
```

CSS 通过 Streamlit 容器的类名和 `data-testid` 属性来选中组件。**所有颜色集中在 `:root` 变量**，方便统一调色。

---

## 三、CSS 套皮内容（按组件对应）

针对你实际用到的组件，逐一套皮：

| 现有组件 | 套皮目标 | CSS 手段 |
|---------|---------|---------|
| 整体背景 `.stApp` | 深色科幻背景（渐变或图片） | `background` + 暗角 |
| 指标卡 `st.metric` | 半透明毛玻璃圆角胶囊 | `backdrop-filter: blur()` + `rgba` + `border-radius` |
| 侧边栏 `st.sidebar` | 深色半透明面板 | 背景色 + 右边框发光 |
| 按钮 `st.button` | 青绿描边发光按钮 | `border` + `box-shadow` + hover |
| 折叠块 `st.expander` | 毛玻璃卡片 | 半透明背景 + 圆角 |
| 表格 `st.table` | 深色行 + 青绿表头 | 背景 + 文字色 |
| 标题/文字 | 浅色 + 青绿高光 | `color` + `text-shadow` |
| 分隔线 `---` | 青绿渐隐细线 | `border-image` |

### 设计变量（配色）

```css
:root {
  --bg-deep: #08161c;            /* 最底色 深蓝黑 */
  --glass: rgba(12, 20, 28, 0.55);   /* 毛玻璃面板底 */
  --glass-border: rgba(120, 200, 210, 0.18);  /* 青绿细边 */
  --glow: rgba(60, 200, 200, 0.30);  /* 青绿发光 */
  --accent: #4fd1c5;             /* 青绿高光 */
  --accent-warn: #f0b860;        /* 暖光告警 */
  --text-main: #e8f4f4;
  --blur: 14px;
}
```

### 关键 CSS 片段（示意，实装时给完整版）

```css
/* 全屏深色背景 */
.stApp {
  background: radial-gradient(ellipse at 30% 20%, rgba(40,90,80,.35), transparent 50%),
              linear-gradient(160deg, #0a1820, #0d2228 40%, #08161c);
}
/* metric 卡 → 毛玻璃胶囊 */
[data-testid="stMetric"] {
  background: var(--glass);
  backdrop-filter: blur(var(--blur));
  border: 1px solid var(--glass-border);
  border-radius: 16px;
  padding: 12px 16px;
  box-shadow: 0 4px 24px rgba(0,0,0,.3);
}
[data-testid="stMetricValue"] { color: var(--text-main); }
[data-testid="stMetricLabel"] { color: rgba(200,220,220,.6); }
/* 按钮发光 */
.stButton > button {
  background: var(--glass);
  border: 1px solid var(--glass-border);
  border-radius: 14px;
  color: var(--text-main);
  transition: all .25s;
}
.stButton > button:hover {
  border-color: var(--accent);
  box-shadow: 0 4px 24px var(--glow);
}
/* 侧边栏深色 */
[data-testid="stSidebar"] {
  background: rgba(8,18,24,.85);
  backdrop-filter: blur(var(--blur));
}
```

### 背景图替换

默认用 CSS 渐变。若要换成真实科幻图：

```css
.stApp {
  background: url('https://你的图床/greenhouse.jpg') center/cover fixed;
}
```

> 注意：Streamlit 本地图片需放进可访问路径或用图床 URL；最简单是用在线图床或 base64 内嵌。实装时说明具体做法。

---

## 四、做得到 / 做不到（诚实预期）

### ✅ 做得到（约 60%）
- 全屏深色科幻背景（渐变或图片）；
- metric 卡片变毛玻璃圆角胶囊；
- 侧边栏深色半透明 + 发光边；
- 按钮青绿描边 + hover 发光；
- 整体冷调配色、浅色文字、青绿高光。

### ❌ 做不到（方案一的天花板）
- **顶部状态条无法像截图那样自由精确排布**——Streamlit 的 `st.columns` 布局是框架定的，做不到截图里那种紧凑横排胶囊条；
- **自定义图标**——metric 里仍是文字标签，难塞进精致矢量图标（emoji 可以，SVG 很难）；
- **入场动画、错峰淡入**——Streamlit 每次 rerun 重绘，CSS 动画会反复触发，体验不佳；
- **左侧那种悬浮发光菜单**——Streamlit 侧边栏结构固定，只能套色，做不出截图的悬浮胶囊菜单。

> 这些正是方案二（HTML 组件嵌入）才能补上的部分。建议方案一调好后，若顶部状态条的观感不满意，再针对性地用方案二单独重做状态条。

---

## 五、风险与注意事项

1. **Streamlit 类名不稳定**：CSS 靠 `data-testid` 和类名选中组件，**Streamlit 版本升级可能改变这些选择器**，导致样式失效。应对：尽量用较稳定的 `data-testid`（如 `stMetric`、`stSidebar`），少依赖随机 hash 类名；锁定 Streamlit 版本。
2. **不影响逻辑**：纯 CSS 注入，不动 `step_system`、不动任何 state，游戏行为完全不变。
3. **深色模式文字对比**：套深色背景后，注意所有文字颜色要够亮，避免 Streamlit 默认深色文字在深背景上看不清。
4. **matplotlib 图表**：`st.pyplot` 的图表是图片，CSS 套不进去。若要图表也变深色风，需改 matplotlib 的 `facecolor`/样式（这属于逻辑层小改，可选）。

---

## 六、实装清单

1. 在 `st.set_page_config` 后插入 `inject_style()` 函数与调用；
2. 写入完整 CSS（约 60–100 行，含背景、metric、按钮、侧边栏、expander、表格、文字）；
3. 调 `:root` 配色到满意；
4. （可选）替换背景图；
5. （可选）把 matplotlib 图表也改成深色风格，与整体一致。

> 全程不改任何游戏逻辑。CSS 是独立一段，随时可删除还原。

---

## 待确认事项

1. **背景**：先用 CSS 深色渐变，还是你已有一张科幻温室图要放进去？
2. **matplotlib 图表**：要不要顺带改成深色风（与整体一致）？还是先只套 UI、图表保持原样？
3. **配色**：青绿科幻（贴合截图）确认，还是想换主色调？
4. **下一步**：方案一套皮后，若顶部状态条不够还原，是否要追加方案二单独重做状态条？

—— 确认后我直接基于你的 game.py 写出完整 CSS 注入代码，你贴进文件顶部即可。
