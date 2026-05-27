# 🌙 天外家园 · 5 分钟路演 Slide Prompt 指南

> 本文档**不生成 slide 本身**，只提供每一页的 prompt。可以直接把每一节复制进 Gamma / Beautiful.AI / Tome / Manus 等 AI slide 工具，或作为人工制图的参考稿。
> 路演总时长 **5 min**，共 **10 页**，三段式结构：① 问题/证据/参数（3 页）→ ② 方案与原型（4 页）→ ③ 路演价值说明（3 页）。
> 全部数据/参数来源见 `video.md`；原型实现见 `game.py`、`readme.md`。

---

## 📐 全局风格 prompt（套在每页 prompt 前）

```
风格：硬核工程 × 月球科幻，主色 #0B132B（深空蓝）+ #5BC0BE（青）+ #FFB400（警示黄）。
排版：左侧大标题（汉黑/Inter Bold），右侧 70% 视觉区。每页最多 1 个核心数据点 + 1 张配图 + 3 条要点。
配图统一：月球南极地形、ISS/EDEN ISS 真实照片、或游戏 UI 截图，禁用通用 stock 插画。
字号：标题 ≥ 36 pt，正文 ≥ 18 pt，数据点 ≥ 60 pt。
中英混排时，英文用 Inter / Source Code Pro，中文用思源黑体。
```

---

# 第一段 · 问题、证据与参数（3 页 / 90 秒）

## Slide 1 — 封面

**Prompt：**
```
生成一张全屏封面 slide。
标题（中）："天外家园 · LunarEco"
副标题（英）："A Closed-Loop Lunar Base Sandbox · Hackathon 2026"
左下角：团队名 / 成员 / 日期 2026-05-27 占位
右下角：版本号 v6 · Streamlit Single-file
背景图 prompt（交给 Midjourney / DALL·E）：
"Photorealistic lunar south pole base at twilight, regolith dust, vertical solar arrays
on crater rim, transparent geodesic greenhouse glowing green inside, Earth half-lit on
horizon, cinematic wide shot, 16:9, low noise, ESA concept art style."
左上角放一句 hook（22 pt 引言）：
"当 ISS 的 ECLSS 把水回收做到 98%，月球基地凭什么能维持 200 天？"
```

---

## Slide 2 — 真实月球难题：闭环生命保障的"系统耦合脆性"

**Prompt：**
```
标题："我们要解决的真实难题：月球基地的多回路耦合脆性"
副标题：Coupled Life-Support Fragility on Lunar Surface

正文 3 条要点（每条左侧配 emoji 大图标）：
1. 🌫️  大气-水-碳-肥-电 5 个回路相互嵌套，一处断链立刻级联崩溃。
   （Apollo 13 是单点故障；月球基地是数十个慢变量同时漂移。）
2. ⏱️  时间尺度跨度从"秒级电源中断"到"周级 14 天月夜"再到"月级菌膜暴发"，
       人无法靠直觉调度。
3. 🧠  封闭乘组的心理 / 健康 / 生理参数与物理资源耦合 —— 拥挤 / 缺氧 / 辐射
       都会同时打击「人」和「系统」。

右侧视觉：一张"系统耦合图"——
节点 = {O2, CO2, 净水, 废水, 固废, 肥料, 电力, 心情, 健康, 护甲, hull}
箭头展示 5 个回路 + 3 个跨域耦合。
画风：白底科研图 / Sankey-like 流网，箭头粗细按 game.py 里的 daily flow 权重。

底注（10 pt）：参考 ESA MELiSSA 五舱结构 / ISS ECLSS。
```

---

## Slide 3 — 为什么这个问题至今"未充分解决"

**Prompt：**
```
标题："现状证据：所有现役系统都是'局部最优'，没有人验证过完整闭环"
副标题：Real-world LSS achievements are partial loops, not a full ecosystem.

左侧表格（4 行 × 3 列：系统 / 现实成绩 / 缺什么）：
| 系统 | 现实成绩 | 仍缺什么 |
| --- | --- | --- |
| ISS ECLSS | 水回收 ~98%、SRV-K 20 年回收 16,155 L | 无作物种植、无 ISRU、无月夜电力 |
| MELiSSA(地面) | 5 舱闭环、L. indica 产 O₂ | 仅地面、未与月面突发事件耦合 |
| EDEN ISS(南极) | 蒸腾→冷凝水回收子系统验证 | 半闭环、未含微藻 / 焚化 / 月壤护甲 |
| NASA Artemis | 月面 PV / 月壤 3D 打印示意 | 还在 RFP / 概念阶段 |

右侧上：一张 ISS Sabatier 反应器照片或 EDEN ISS 温室真实照片，加引用条形码。
右侧下：一句结论（28 pt 黄色高亮）：
"完整的'人 + 物理 + 心理'闭环还从未在月面运行过 1 天。
 → 我们需要一个能跑 200 天、暴露所有耦合断点的「数字孪生沙盒」。"

底注（10 pt）：
- ttu-ir.tdl.org / SRV-K paper
- frontiersin / ARTHROSPIRA-B 4 周批次
- eden-iss.net / FAQ
- nasa.gov / lunar 3D printing
```

---

## Slide 4 — 关键参数与来源（一图打尽）

**Prompt：**
```
标题："本作品 28 个参数全部锚定真实文献"
副标题：Every coefficient maps to a published source.

中央放一张"参数雷达"或"分类热力表"：
列：参数家族（大气 / 农业 / 微藻 / 电力 / 水 / ISRU / 辐射 / 心理）
行：3 列 — [常量值] [来源] [假设/适用范围]

挑 8 个最有冲击力的填进去（其它写"+20 more"）：
1. 乘组代谢 O₂ 0.84 kg/人/天 → ALS Baseline (NASA)
2. 螺旋藻 4 周批次 → ISS ARTHROSPIRA-B (Frontiers 2021)
3. 月壤+2 wt% 水 → 屏蔽 +6% (NTRS 20110012713)
4. 月面光伏 SOLAR_KWH_PER_M2_HOUR = 0.066 → 0.3 kW/m² × 22% (ScienceDirect)
5. 焚烧发电 0.4 kWh/kg → EPA 550 kWh/吨 × 太空打折
6. ISS 冷凝水回收 63% → SRV-K 20 年数据
7. Speed breeding 6 代/年 → bioRxiv 161182
8. EDEN ISS 温室 7 kg/舱/天 冷凝水 → DLR elib

右侧加一行 disclaimer（14 pt）：
"假设：① 重力按月面 1/6 g；② 月夜固定 14 天；③ 单一南极坑外阵列；
 ④ 乘组经过医学筛选；⑤ 微重力代谢差异已在系数中等比缩放。
 适用范围：30–365 天量级闭环演化，不适合单舱秒级流体仿真。"

底注：详见 video.md §1–§9 28 条引用链接。
```

---

# 第二段 · 方案与原型（4 页 / 150 秒）

## Slide 5 — 解决方案：把"月球基地"变成可玩、可微调、可崩溃的沙盒

**Prompt：**
```
标题："Solution · 让所有耦合断点 5 分钟内被亲手按出来"
副标题：A single-file Streamlit sandbox that simulates 12 sub-systems in real time.

三栏 layout：
[左] 设计原则（带图标）
  · 🔗 闭环优先 — 不抽象"扣血"，每个事件直接 mutate 物理 state。
  · 🧪 参数透明 — 所有常量在 game.py 文件顶部一屏可见。
  · 🧠 双轨人因 — 心情公式 / 健康公式独立，工作×天赋×边际递减叠乘。
[中] 系统拓扑图（重画一张比 Slide 2 更细的版本，标出 12 个子系统编号）：
  §1 电力 §3 维护 §5 心情/健康 §6 堆肥 §7 焚化
  §8 MICP §9 微藻 §10 批次农业 §10.5 温室 §11 Sabatier §12 CDRA
[右] "为什么是游戏？"
  · 5 分钟内能在一个 dashboard 看见 200 天 × 12 系统的 emergent behavior
  · 玩家通过"播种 / 派工 / 立项"做决策，比写工程报告更有 ownership
  · 自动暴露 7 种死法 = 7 个真实故障模式

底部一行（黄色高亮）：
"From spreadsheet to sandbox: 每一行 csv 都对应屏幕上能死人的事件。"
```

---

## Slide 6 — 原型展示：开局 → 运营 → 崩溃 / 续命

**Prompt：**
```
标题："Prototype · 天外家园 v6（Streamlit single-file, 1,900 行）"
副标题：Live playable at: `streamlit run game.py`

布局：4 张 UI 截图拼成 2×2，每张配 1 行说明（≤ 18 字）。
请从已运行的 game.py 中截：

① 开局任务初始化页（4 个部长选择 + 高压氧瓶 + 初始舱）
   caption："Phase 1 · 一次性战略锁定"
② 主面板 — 乘组工作分配卡片 + 实时生态雷达图
   caption："Phase 2 · 每日决策只动'今天做什么'"
③ 三联图（大气动力学 / 净水流量 / 战略物资）
   caption："Phase 3 · 长时序耦合 emergent 行为"
④ 事件 + 医疗日志（撞击 → SPE → 心情扣分 → 派人修理 → hull 回升）
   caption："Phase 4 · 突发事件级联可视化"

底部贴 5 个关键 KPI（白底卡片）：
- 12 子系统 · 9 + 1 可重复科研课题
- 9 类突发事件 × 3 时间尺度
- 4 种作物（含 v6 药用植物）+ 5 类舱室
- 4 项工作 × 4 类天赋 × 4 级倍率
- 7 种死法 / 双轨健康-心情建模

底注：UI 框架 Streamlit + matplotlib；约 1,899 行单文件，无外部数据库。
```

---

## Slide 7 — 核心创新 1：可重复科研 × 天赋 × 双轨人因

**Prompt：**
```
标题："Innovation 1 · 把工程参数和'人'真正绑在一起"
副标题：Talents × Research × Twin-track (Mood + Health)

左半边：天赋系统流程图（v6 替代职业系统）
  「30%/50%/20% 抽 0/1/2 天赋」→「4 类工作 × 4 级倍率」→「队伍 = 平均倍率 × 边际递减表」
  四部长照片占位（Annie / 黄 / 罗 / 郭）+ ×3 顶级倍率徽章

右半边：双轨公式卡（两张并排）
  ┌─ 心情 ─────────────────────────┐  ┌─ 健康 ─────────────────────────┐
  │ + 温室加成 plant × 0.6        │  │ + 休息 +5                       │
  │ + 绿色生活空间 GH × 3.0       │  │ − 缺氧扣 1 (O2 < 19.5%)         │
  │ + 总人数互助 × 0.20           │  │ − CO2 中毒扣 1 (CO2 > 0.5%)     │
  │ − 单舱拥挤 × 0.7              │  │ − 出舱辐射 max(1.5, 8 − shield) │
  │ + 护甲安全感 shield × 0.02    │  │ − 工作疲劳（探索/修理 -0.5）    │
  │ + 工作影响 / 事件冲击         │  │                                 │
  └────────────────────────────────┘  └────────────────────────────────┘

底部一句话（28 pt）：
"心情 → 0 = 叛逃 ；健康 → 0 = 死亡。两条独立轴，逼玩家从'最大化产出'切到'养人'。"

底注：v6 新增；详见 game.py § 5 (per-crew loop) 与 readme.md §7–§9。
```

---

## Slide 8 — 核心创新 2：医疗 / 药物生产链 + 9 课题 emergent 协同

**Prompt：**
```
标题："Innovation 2 · 真实科研协同的链式涌现"
副标题：Medicine Production Chain + 9 Research Topics in Synergy.

上半：制药生产链横向流程图（v6 新）
  🌿 药用植物（70 天） → 🌾 收获药材
                            ↓
                     💉 制药课题（25 天 · 实验室 · 可重复）
                            ↓
                     💊 药物 → 治疗：疾病加重 60% 好转率
                                    / 重伤 50% → 轻伤

下半：9 课题 + 1 制药 网络图（雷达或环形）
  课题节点按"加成倍率类型"着色：
    🟦 资源开源（algae / sabatier / water_loop / solar）
    🟩 资源节流（automation / compost）
    🟧 防御（isru_wall / radiation_med）
    🟨 产出（crop_breeding / pharma）
  连线表示"协同"：
    isru_wall ↔ radiation_med（SPE 双重防御）
    sabatier ↔ water_loop（净水双回路）
    crop_breeding ↔ compost（农业增产 ↔ 肥料）
    pharma ↔ crop_breeding(药用植物)

右下角小卡片（黄底）：
"一个 200 天周期内，玩家平均完成 5–7 个课题；
 选择哪条研究路线 = 选择哪种死法不会发生。"

底注：所有课题真实依据见 video.md §1，含 ESA MELiSSA / NASA Veggie / DLR EDEN ISS。
```

---

# 第三段 · 路演与价值说明（3 页 / 60 秒）

## Slide 9 — 创新点 / 改进点 / 启发性

**Prompt：**
```
标题："Why it matters · 我们做了三件别人没做的事"
副标题：Innovation · Improvement · Inspiration

三栏卡片（每栏 30 字以内）：

[💡 创新点]
  · 把 28 个真实文献参数全部裸露在单文件源码顶部 —— 任何研究员可以
    一行覆盖、一秒看效果。
  · 把"心情 / 健康 / 天赋 / 医疗"和物理回路放在同一 step_system 时间循环里，
    使心理参数第一次能"反向调节"工程参数。

[🔧 改进点（相对 v1–v5 hackathon 原型）]
  · v6 用天赋系统替代 v5 职业，使乘组生成不再 2-的-N-次方爆炸。
  · v6 新增排队建造 / 招募 / 医疗链 / 永久移除，闭环完整度由 9 系统 → 12 系统。
  · 突发事件不再"抽象扣血"，全部精确耦合到 state，可被科研课题倍率调节。

[🚀 启发性]
  · 任何 LSS 子系统（火星 / 极地 / 海底 / 灾备）都能用同一 step_system 模板
    挂载 → 即"闭环沙盒框架"。
  · 决策者 5 分钟即可获得对"参数 → 系统行为"的直觉，远低于建模学习曲线。

底部一行（黄色高亮）：
"From hackathon toy → research-grade open scaffold。"
```

---

## Slide 10 — 资源来源 / 往届进展声明 / 现场演示 Call

**Prompt：**
```
标题："Credits · Progress · Live Demo"

三栏：

[📚 数据 / 文献来源（左）]
  · ESA MELiSSA · NASA Veggie · ISS ECLSS · DLR EDEN ISS
  · NASA NTRS 月壤屏蔽 · EPA 焚烧发电 · CGIAR speed breeding
  · 完整 28 条引用在 video.md §12 链接汇总

[🛠️ 工具 / 框架（中）]
  · Streamlit · matplotlib · pandas · numpy
  · Claude Code / GPT-5 / Kimi K2 协同开发（kimi2.py 留有调用样例）
  · 配图：Midjourney（封面）+ 真实 NASA / ESA / DLR 公开图（其余）

[📈 往届迭代说明（右）— 重要！必填，否则影响评分]
  · 本作品基于 [前次 hackathon 原型名称 / 链接] 改编
    （如：v1 闭环大气-水四回路 prototype，于 2025-XX 提交）
  · 本届 hackathon 新增工作（占代码量 ≥ 60%）：
    - v5 职业系统 → v6 天赋系统 重写
    - 新增医疗 / 受伤 / 药物链 / 永久移除 / 招募 / 排队建造
    - 系统数 9 → 12，参数引用数 18 → 28，UI 重构为 3 阶段
  · 如为完全原创首作，把此栏改为："本作品为本届 Hackathon 全新原创"

底部全宽 Call-to-Action（36 pt 黄色）：
"现在 → 现场扫码 → 5 分钟内你会亲手让一座基地崩溃。
 streamlit run game.py · QR 码占位"
```

---

# 📊 5 分钟时间分配建议

| 时间 | 页码 | 重点动作 |
| --- | --- | --- |
| 0:00–0:20 | 1 | 自我介绍 + 一句 hook |
| 0:20–1:20 | 2–3 | 讲"耦合脆性"问题，引 ISS / MELiSSA 现状 |
| 1:20–1:50 | 4 | 参数表 + disclaimer，30 秒带过 |
| 1:50–2:20 | 5 | 解决方案三原则 + 拓扑图 |
| 2:20–3:50 | 6 | **现场跑 game.py，演示开局 + 触发一次撞击事件** |
| 3:50–4:20 | 7–8 | 双轨 + 制药链 + 9 课题 emergent |
| 4:20–4:50 | 9 | 创新 / 改进 / 启发 三栏 |
| 4:50–5:00 | 10 | Credits + 往届声明 + QR 码 |

---

# ✅ 评分对照清单（提交前自检）

- [ ] 第 1 段 3 页：真实难题陈述 ✅ 未解决证据 ✅ 参数+来源+假设+适用范围 ✅
- [ ] 第 2 段 4 页：解决方案路径 ✅ 可展示原型（Streamlit）✅ 现场演示 ✅
- [ ] 第 3 段 3 页：5 分钟 PPT ✅ Demo Call ✅ 创新/改进/启发 ✅
- [ ] Slide 10 已注明：AI 工具（Claude / GPT / Kimi）+ 素材库（NASA/ESA/DLR）+ 往届迭代进展
- [ ] 每页字号、配色、配图遵循"全局风格 prompt"
- [ ] video.md 28 条引用作为附录可调阅

---

## 附 · 如果要喂给 AI slide 工具（如 Gamma）

直接把每个 Slide 节（从"## Slide N"到下一个"## Slide"前一行）整段复制为一个 prompt 提交即可。
建议先提交"全局风格 prompt"作为系统提示，再逐页提交。
配图部分（带 Midjourney/DALL·E 提示词的）单独拿去图像模型生成后插入。
