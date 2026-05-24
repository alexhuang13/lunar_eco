# 天外家园 · 视频脚本素材清单 — 资料 / 数据 / 实现对照

> 本文档为视频/演讲准备:把游戏里每一项数值的**现实依据 → 可查证链接 → 游戏内对应实现**串到一起,便于"边讲边演示"。
> 内容综合自 `version1.md` ~ `version4.md` 的设计文档与 `app.py` 的最终代码。

---

## 一、科研系统(v2) — 9 个课题的真实依据

每个课题的实验周期天数都是把现实研究的时间尺度**等比缩放**到游戏内的几十~一百天量级,并保留「微生物 < 工程材料 < 作物育种」的相对快慢关系。

### 课题 1:🦠 高效螺旋藻菌株筛选

**现实依据**:欧空局 MELiSSA 闭环生命支持系统的 C4a 舱用螺旋藻(Limnospira indica PCC 8005)产氧。ISS 上 ARTHROSPIRA-B 实验在微重力下运行了约 **4 周(28 天)** 的光生物反应器批次培养。

- ISS 螺旋藻 4 周批次培养:https://www.frontiersin.org/journals/astronomy-and-space-sciences/articles/10.3389/fspas.2021.700277/full
- 生长建模与 ISS/地面对比:https://www.sciencedirect.com/science/article/abs/pii/S2214552420300158
- ESA MELiSSA 总览:https://www.esa.int/Enabling_Support/Space_Engineering_Technology/MELiSSA_life_support_project_an_innovation_network_in_support_to_space_exploration

**游戏映射**
- `RESEARCH_LIBRARY["algae_strain"]`: `cycle = 30` 天
- 完成回调 `_research_algae(m)`: `m["algae_o2"] = 1.20`, `m["algae_co2"] = 1.20`
- 作用点:`step_system §9` 微藻段,`alg_co2_abs *= m["algae_co2"]`,`产 O2 *= m["algae_o2"]`

---

### 课题 2:🧫 堆肥高效微生物选育

**现实依据**:MELiSSA 的废物降解链由液化舱、硝化舱等多个微生物舱组成,菌株与基因稳定性研究贯穿数十年。

- MELiSSA 闭环 5 舱结构:https://www.science.gov/topicpages/m/melissa+closed+loop
- MELiSSA 综述(含降解子系统):https://webs.uab.cat/melissapilotplant/wp-content/uploads/sites/397/2023/11/Melissa_The_European_project_of_a_closed_life_supp-1.pdf

**游戏映射**
- `RESEARCH_LIBRARY["compost_microbes"]`: `cycle = 35` 天
- `_research_compost(m)`: `m["compost"] = 1.25`
- 作用点:`step_system §6` 堆肥段,处理上限 `COMPOST_MAX_SW/WW × compost × m["compost"]`

---

### 课题 3:🌾 加速作物育种(Speed Breeding)

**现实依据**:传统作物育种 8–15 年;NASA 1980 年代为太空种植提出的「speed breeding」可压 2.5–5 倍,光不敏感作物每年 **6 代**;CGIAR/IRRI 把周期缩到 **2 年**。

- Speed breeding 综述(Nature 方法,6代/年):https://www.biorxiv.org/content/10.1101/161182.full.pdf
- 传统育种 10–15 年与加速策略:https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9723045/
- CGIAR/IRRI 2 年:https://www.cgiar.org/news-events/news/irri-scientists-introduce-speed-breeding-3-0-to-accelerate-climate-resilient-crop-innovation-with-onecgiar
- 基因组辅助 speed breeding:https://www.frontiersin.org/journals/sustainable-food-systems/articles/10.3389/fsufs.2024.1383302/full

**游戏映射**
- `RESEARCH_LIBRARY["crop_breeding"]`: `cycle = 80` 天(最慢的一档)
- `_research_crops(m)`: `m["crop_yield"] = 1.20`
- 作用点:`step_system §10` 农作物段,`s["Food_kg"] += amt × yield_food × health_penalty × m["crop_yield"]`;`§10.5` 温室段 `gh_factor *= m["crop_yield"]`

---

### 课题 4:🧱 ISRU 月壤+水墙复合材料

**现实依据**:月壤本身屏蔽有限;月壤中添加 **2 wt% 水** 可使屏蔽效果提升约 **6%**;月壤砖中掺 **30–50 wt% 聚乙烯** 才显著优于纯月壤墙;约 **45 g/cm² 月壤** 可有效衰减重离子。

- 月壤/聚乙烯/水复合屏蔽(NASA,2 wt% 水提升 6%):https://ntrs.nasa.gov/citations/20110012713
- 月壤+聚乙烯墙体定量分析(30–50% PE):https://link.springer.com/article/10.1007/s12567-024-00540-4
- 月壤穹顶屏蔽与器官剂量评估:https://www.sciencedirect.com/science/article/pii/S0032063325000832
- NASA 月面/火星 3D 打印建造:https://www.nasa.gov/directorates/stmd/nasa-enables-construction-technology-for-moon-and-mars-exploration/

**游戏映射**
- `RESEARCH_LIBRARY["isru_wall"]`: `cycle = 50` 天
- `_research_isru(m)`: `m["hull_durability"] = 1.50`
- 作用点:`step_system._process_events._run_with_hull_wrap` — 事件造成的 hull 伤害被 `÷ hull_durability` 缩小,等效抗损 +50%

---

### 课题 5:☀️ 坑外太阳能阵列升级

**现实依据**:月面太阳能受 ~14 天月夜与低太阳高度角制约,NASA Artemis 推进「垂直太阳能阵列」「坑缘部署」等方案;裂变表面电源也在研发中作为月夜备份。

> 未做单一权威链接精确对标,以工程合理范围设定。同电力系统下面的链接共享。

**游戏映射**
- `RESEARCH_LIBRARY["solar_upgrade"]`: `cycle = 45` 天
- `_research_solar(m)`: `m["solar_efficiency"] = 1.30`
- 作用点:`step_system §1` 电力段,`gen_solar = solar_panel_m2 × SOLAR_KWH_PER_M2_HOUR × day_light × m["solar_efficiency"]`

---

### 课题 6:💧 闭环水回收升级

**现实依据**:ISS 的 ECLSS 水回收率已达 **~98%**;MELiSSA 以接近 100% 闭合为目标。

- ISS 冷凝水回收占比(63% 饮用水,2000–2020 累计 16155 升):https://ttu-ir.tdl.org/server/api/core/bitstreams/ac8532e0-75f2-4268-81ab-c1bc2f5f817a/content
- 混合系统 90% 回收率:https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12298372/

**游戏映射**
- `RESEARCH_LIBRARY["water_loop"]`: `cycle = 40` 天
- `_research_water_loop(m)`: `m["water_recycle"] = 1.20`、`m["maintenance"] *= 0.7`
- 作用点:`step_system §3` 维护段(水耗 ×0.7);`§9/§10/§10.5` 所有蒸腾/净化回水点都 `× water_recycle`

---

### 课题 7:💊 辐射医学 / 乘组健康协议

**现实依据**:封闭舱内辐射防护与作息制度研究(ESA / NASA 长期任务前向研究)。

> 设计文档以「经过筛选的乘组」为设定,无单一引用。

**游戏映射**
- `RESEARCH_LIBRARY["radiation_med"]`: `cycle = 40` 天
- `_research_radiation(m)`: `m["radiation_mood"] = 0.5`
- 作用点:`_solar_particle_impact()` — `ctx["mood_shock"](-25.0 × exposure × rad_mood)`,SPE 心情冲击直接减半

---

### 课题 8:⚗️ Sabatier CO₂ 再利用反应器

**现实依据**:ISS 用 Sabatier 反应器将 CO₂ 转甲烷与水(覆盖在 ECLSS 综述中)。

- ISS ECLSS 综述:https://en.wikipedia.org/wiki/ISS_ECLSS

**游戏映射**
- `RESEARCH_LIBRARY["sabatier"]`: `cycle = 55` 天
- `_research_sabatier(m)`: `m["co2_to_water"] = True`(布尔开关)
- 作用点:`step_system §11` — 当 CO₂ > 0.3% 阈值时每天最多转 2 kg CO₂ → 1 kg 净水

---

### 课题 9:🤖 自动化机器人维护

**现实依据**:封闭基地的自动化运维设想(对应"无限扩张的代价"机制)。

> 设计层面的平衡阀,无单一引用。

**游戏映射**
- `RESEARCH_LIBRARY["automation"]`: `cycle = 60` 天
- `_research_automation(m)`: `m["maintenance"] *= 0.5`
- 作用点:`step_system §3` 模块维护水耗 ×0.5

---

## 二、电力系统(v2)

### 2.1 太阳能发电

**现实依据**
- 月面太阳辐照 ~**1.37 kW/m²**(无大气衰减,高于地球地表)
- 光伏效率:当前基准 ~15%,最佳 ~30%,聚光技术未来可达 ~50%
- ISS 单个太阳翼(35m × 12m)发约 **31 kW** 直流电

**链接**
- 月球南极可用太阳能量化:https://www.sciencedirect.com/science/article/abs/pii/S0094576523003399
- 月面光伏发电建模(PV 热模型):https://arxiv.org/pdf/2402.14783
- 月面 PV/T 系统:https://www.sciencedirect.com/science/article/abs/pii/S0360544225016470
- ISS 电力系统(单翼 31 kW):https://en.wikipedia.org/wiki/Electrical_system_of_the_International_Space_Station

**游戏映射**
- `SOLAR_KWH_PER_M2_HOUR = 0.066`(取 0.3 kW/m² × 22% 效率)
- `SOLAR_PANEL_M2_DEFAULT = 100`(初始坑外阵列面积)
- 代码:`gen_solar = solar_panel_m2 × SOLAR_KWH_PER_M2_HOUR × day_light × m["solar_efficiency"]`

---

### 2.2 焚烧发电

**现实依据**:现代垃圾焚烧发电厂每吨垃圾约发 **550 kWh**(典型 500–600 kWh/吨,约 **0.55 kWh/kg**),热电转换效率约 **20–22%**。

**链接**
- EPA 垃圾发电(550 kWh/吨):https://www.epa.gov/smm/energy-recovery-combustion-municipal-solid-waste-msw
- 垃圾发电厂概述(500–600 kWh/吨):https://en.wikipedia.org/wiki/Waste-to-energy_plant
- 焚烧炉能效实验(22% 算例):https://www.researchgate.net/post/How_can_I_calculate_how_much_electricity_can_be_generated_from_waste

**游戏映射**
- `INCINERATOR_KWH_PER_KG = 0.4`(太空小型炉效率打折)
- 代码:`step_system §7` 焚化段 — `s["Power_Battery_kWh"] += act_inc × INCINERATOR_KWH_PER_KG`

---

### 2.3 蓄电池 / 热控

**现实依据**:ISS 在轨道阴影期完全靠蓄电池;TCS/ETCS 与 ECLSS 是持续耗电的关键负载。

**链接**
- ISS 电力系统:https://en.wikipedia.org/wiki/Electrical_system_of_the_International_Space_Station
- ISS ECLSS:https://en.wikipedia.org/wiki/ISS_ECLSS
- ECLSS / ETCS 热管理:https://www.1-act.com/resources/blog/thermal-management-in-eclss-and-etcs-systems/

**游戏映射**
- `BATTERY_CAP_DEFAULT = 200 kWh`
- 各舱日耗(基于工程合理量级):

| 舱型 | kWh/天/舱 | 常量 |
|------|----------|------|
| 居住 | 8 | `POWER_PER_HABITAT` |
| 种植(LED 补光) | 25 | `POWER_PER_PLANT` |
| 堆肥 | 3 | `POWER_PER_COMPOST` |
| 实验室待机/运行 | 5 / 15 | `POWER_PER_LAB_IDLE/ACTIVE` |
| 温室 | 25 | `POWER_PER_GREENHOUSE` |

- 缺电时:`hull_integrity -= 0.5`、作物补光 ×0.5、实验室停摆、采集打折

---

## 三、净水流量指标(v3)

### 3.1 ISS 冷凝水回收

**现实依据**:ISS 俄罗斯舱段的 SRV-K 系统从 **2000–2020 年回收了 16155 升水**,约占乘组饮用水需求的 **63%**、总需水量的 **37%**。

**链接**:https://ttu-ir.tdl.org/server/api/core/bitstreams/ac8532e0-75f2-4268-81ab-c1bc2f5f817a/content

### 3.2 膜生物反应器 + RO 系统

**现实依据**:地面研究中,膜生物反应器 + 反渗透对湿气冷凝水可达 **~90% 回收率**。

**链接**:https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12298372/

**游戏映射**
- 累加器 `daily_water_reclaimed` 汇总 6 条产水路径:
  1. 微藻净化废水(`§9` `alg_pur_clean`)
  2. 种植舱基础蒸腾(`§10` `base_evap_clean`)
  3. 各批次作物蒸腾(`§10` `act_cw`)
  4. 温室舱蒸腾→冷凝(`§10.5` `gh_water`)
  5. Sabatier 反应器(`§11` `sabatier_water`)
  6. 采集出舱(v4 `§2.5` `explore_water`)
- 累加器 `daily_water_consumed` 汇总 2 条耗水路径:模块维护(`§3`)、乘组代谢(`§6`)
- 仪表盘 4 卡片(产量 / 消耗 / 净流量 / 存量)+ 图 2 右轴双蓝色曲线

---

## 四、温室舱(v3) — EDEN ISS

**现实依据**:EDEN ISS(DLR 在南极的太空温室)运行经验:
- 温室是**半闭环**系统,植物大量蒸腾水分,需循环再利用
- 专设「冷凝水回收子系统」处理蒸腾水
- 理想生长温度 20–25 ℃,热量主要来自 LED 光源 — 印证「高耗电(补光)+ 产净水(蒸腾冷凝)」的双重特征

**链接**
- EDEN ISS 温室 FAQ(蒸腾、湿度控制、水回收):https://eden-iss.net/wp-content/uploads/4_EDENISS_FAQ.pdf
- EDEN ISS 冷凝水回收子系统(DLR):https://elib.dlr.de/186911/
- 太空植物栽培白皮书(蒸腾维持湿度平衡):https://www.sciencedirect.com/science/article/pii/S221455242400066X
- EDEN ISS 植物健康监测(南极实验阶段):https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2019.01457/full

**游戏映射**(取设计建议表的中间值)
| 参数 | 常量 | 值 |
|------|------|-----|
| 体积 / 构造水 | `VOL_GREENHOUSE / WATER_PER_GREENHOUSE` | 60 m³ / 120 kg |
| 日耗肥 | `GH_FERT_PER_DAY` | 1.5 kg/舱 |
| 日耗废水(灌溉) | `GH_WW_PER_DAY` | 12 kg/舱 |
| 日耗 CO₂ | `GH_CO2_PER_DAY` | 0.75 kg/舱 |
| 日耗电 | `POWER_PER_GREENHOUSE` | 25 kWh/舱 |
| 日产 O₂ | `GH_O2_PER_DAY` | 0.4 kg/舱 |
| 日产净水(蒸腾→冷凝) | `GH_WATER_RECLAIM_PER_DAY` | 7 kg/舱 |
| 心情加成 | `GH_MOOD_BONUS_PER_UNIT` | 3.0/舱/人/天 |

代码:`step_system §10.5` 段,产出受 `min(供应比) × 光照系数 × crop_yield 倍率` 调制。

---

## 五、批次农业 — NASA 真实太空作物数据库

**现实依据**:CROP_DATA 字典里的数据按 NASA / 太空农业研究的实测代谢系数整理:
- **Apogee 矮秆小麦**:NASA 为太空种植专门育种的矮秆品种,生长周期 65 天
- **VEG-01 气雾生菜**:ISS Veggie 实验首批正式作物,33 天速生
- **Quantum 微型土豆**:微型 / 速生马铃薯研究,80 天周期

> 这些品种数据散落于 NASA Veggie 系列项目报告 / Advanced Life Support Baseline Values and Assumptions 等公开材料;游戏代码注释为「极其硬核的 NASA 真实太空农业数据库」。

**游戏映射**(单位:kg / 天 / kg 预期产量)
| 字段 | 小麦 | 生菜 | 土豆 |
|------|------|------|------|
| `daily_ww`(灌溉/废水) | 0.615 | 1.818 | 0.562 |
| `daily_cw`(蒸腾回收净水) | 0.600 | 1.787 | 0.550 |
| `daily_co2` | 0.057 | 0.054 | 0.026 |
| `daily_fert` | 0.0038 | 0.0030 | 0.0018 |
| `daily_o2`(产氧) | 0.046 | 0.042 | 0.021 |
| `yield_sw`(收获固废) | 1.50 | 0.25 | 0.40 |
| `cycle` | 65 | 33 | 80 |

代码:`step_system §10` 段,供应短板触发批次健康度下降,健康归零烂掉变固废。

---

## 六、突发事件系统(v1) — 设计原则与耦合点

> v1 文档无外部链接;事件机制是基于「精确打击对应 state 参数 + 沿系统耦合关系级联」的设计原则。每个事件直接修改具体状态参数,而不是抽象扣血。

### 三类时间尺度

| 类别 | 时间尺度 | 应对模式 | 例子 |
|------|---------|---------|------|
| `instant` | 秒-分 | 自动反射 | 微流星撞击 / SPE / 电源中断 |
| `ongoing` | 分-小时 | 人工应急 | 热控泄漏 / ECLSS 故障 / 尘暴 |
| `creeping` | 天-周月 | 趋势预警 | 缓慢泄漏 / 菌膜暴发 / 辐照脆化 |

### 关键耦合点

- `hull_integrity`:撞击、辐射、脆化都叠加在此 — **归零即"舱体解体失压"死亡**
- `Regolith_Shield_m2`:SPE 伤害随护甲厚度递减,**≥250 m² 基本免疫**;v4 后又能被「修复」工作消耗换 hull
- **断电不直接扣资源**,而是关闭光合与 CDRA,通过既有逻辑自然级联出缺氧/CO₂ 失控

### 游戏映射

- `EVENT_LIBRARY` 9 个事件,每个的 `impact` / `tick` 都是 lambda 直接 mutate `state`
- `_process_events` 在每日循环开头调用;`_run_with_hull_wrap` 把 hull 伤害按 `hull_durability` 课题倍率缩小
- 触发概率:侧边栏 `event_chance` 字典 `关闭/低/中/高 = 0/4/10/20%`

---

## 七、心情 / 健康系统(v1 心情 + v4 健康双轨)

> 同样属于设计层(无外部文献),核心思路是把"逐人独立 + 命名"的心理建模做出来,健康单独建模身体损耗。

### 心情公式(v1 设计 + v4 工作影响)

```
每日心情变化量 = 基础随机衰减(-0.1~-0.5)
              + 温室加成(plant × 0.6)
              + 绿色生活空间(greenhouse × 3.0)        ← v3 新增
              + 总人数互助(total_crew × 0.20)
              − 单舱拥挤(people_per_room × 0.7)
              + 护甲安全感(min 5.0, shield × 0.02)
              − 资源压力(food/O2/CO2/废水/固废 stress)
              + 事件冲击(SPE/热控/etc)
              + 工作影响(rest +5 / research -2 / repair -1.5 / explore -1.5)   ← v4
```

### 健康公式(v4 新增)

```
每日健康变化 = 工作基础(rest +5 / 其他 0~-0.5)
            − 缺氧扣 1(O2 < 19.5%)
            − CO2 中毒扣 1(CO2 > 0.5%)
            − 出舱辐射扣(max 1.5, 8 - shield × 0.02)   ← 仅 explore 工作者
```

代码定位:`step_system §5` 段 per-crew 循环。

---

## 八、月壤微生物固结 / MICP

> 把化肥和废水排到月壤外,通过类似 MICP(Microbially Induced Calcium Carbonate Precipitation)的固结过程生成屏蔽护甲,真实文献参考方向是 NASA 的月壤生物砖研究(沿用 v2 ISRU 课题的链接族)。

**游戏映射**
- `BIO_PARAMS["MICP_SHIELD_PER_FERT"] = 2.5`(每 kg 化肥 → 2.5 m² 护甲)
- `BIO_PARAMS["MICP_SHIELD_PER_WW"] = 0.5`(每 kg 废水 → 0.5 m² 护甲)
- 代码:`step_system §8`

---

## 九、CDRA(智能气压保护)

**现实依据**:ISS 的 Carbon Dioxide Removal Assembly(CDRA)负责持续洗涤 CO₂ 与平衡氧气,与 Sabatier 反应器组合形成大气循环闭环。

**链接**(共享 §1.6 / §2.3)
- ISS ECLSS:https://en.wikipedia.org/wiki/ISS_ECLSS

**游戏映射**
- `step_system §12`:O₂ > 24% → 入罐;< 19.5% → 出罐(上限 = 初始携带的高压氧瓶)
- CO₂ > 0.3% → 入碳源罐(上限 `MAX_CO2_TANK_CAPACITY = 100 kg`);< 0.05% → 释放
- ECLSS 故障事件持续期间 `ev_ctx["scrubber_off"] = True`,洗涤被关闭

---

## 十、角色 / 工作分配系统(v4)

> 无外部文献。是把游戏当前的「资源管理」抽象成「人 → 当日工作 → 产出」的决策结构。

### 4 项工作 + 双轨成本

| 工作 | 产出 | 心情/天 | 健康/天 |
|------|------|---------|---------|
| 😴 休息 | 唯一恢复手段 | +5 | +5 |
| 🔬 科研 | 推进所在实验室课题 | -2 | 0 |
| 🔧 修复 | 月壤护甲 → hull | -1.5 | -0.5 |
| ⛏️ 采集 | 净水(月壤冰) + 月壤 + 耗电 + 辐射 | -1.5 | -(8~1.5) |

### 有效人力(边际递减)

复用 v2 科研的表:`EFFECTIVE_CREW_TABLE = [0.0, 1.0, 1.7, 2.2, 2.5]`,4 人封顶。

代码定位:`step_system §1.5 / §2 / §2.5 / §5`,以及主面板「👥 乘组工作分配」UI。

---

## 十一、UI 三阶段(v4)

> 无外部文献。设计原则:**初始决策一旦确认就锁死**,运营期只能动「今天做什么」。

- **阶段 1 任务初始化**:`game_started = False` 时全屏显示开局配置,`st.stop()` 阻止其余渲染
- **阶段 2 每日运营**:侧边栏的可改项是「建/拆 / 播种 / 微藻 / 应急 / 科研立项 / 工作分配」
- **阶段 3 锁定参数(只读)**:`locked_initial` 字典在侧边栏顶端只读展示

代码定位:`_initialize_game()` 函数 + `app.py` 的 `if not st.session_state.game_started:` 分支。

---

## 十二、链接汇总(按访问频率排序)

| 链接 | 用途 |
|------|------|
| https://en.wikipedia.org/wiki/Electrical_system_of_the_International_Space_Station | 电力(太阳能 + 蓄电池) |
| https://en.wikipedia.org/wiki/ISS_ECLSS | ECLSS / CDRA / Sabatier |
| https://www.esa.int/Enabling_Support/Space_Engineering_Technology/MELiSSA_life_support_project_an_innovation_network_in_support_to_space_exploration | MELiSSA(微藻、堆肥菌) |
| https://www.frontiersin.org/journals/astronomy-and-space-sciences/articles/10.3389/fspas.2021.700277/full | ISS 螺旋藻 4 周批次 |
| https://www.sciencedirect.com/science/article/abs/pii/S2214552420300158 | 螺旋藻生长建模 |
| https://www.science.gov/topicpages/m/melissa+closed+loop | MELiSSA 5 舱结构 |
| https://webs.uab.cat/melissapilotplant/wp-content/uploads/sites/397/2023/11/Melissa_The_European_project_of_a_closed_life_supp-1.pdf | MELiSSA 综述 |
| https://www.biorxiv.org/content/10.1101/161182.full.pdf | Speed breeding(6 代/年) |
| https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9723045/ | 传统育种 10–15 年 |
| https://www.cgiar.org/news-events/news/irri-scientists-introduce-speed-breeding-3-0-to-accelerate-climate-resilient-crop-innovation-with-onecgiar | IRRI Speed breeding 3.0 |
| https://www.frontiersin.org/journals/sustainable-food-systems/articles/10.3389/fsufs.2024.1383302/full | 基因组辅助 speed breeding |
| https://ntrs.nasa.gov/citations/20110012713 | 月壤+2% 水复合屏蔽 +6% |
| https://link.springer.com/article/10.1007/s12567-024-00540-4 | 月壤+聚乙烯墙体(30–50% PE) |
| https://www.sciencedirect.com/science/article/pii/S0032063325000832 | 月壤穹顶屏蔽 / 器官剂量 |
| https://www.nasa.gov/directorates/stmd/nasa-enables-construction-technology-for-moon-and-mars-exploration/ | NASA 月面 3D 打印 |
| https://www.sciencedirect.com/science/article/abs/pii/S0094576523003399 | 月球南极太阳能 |
| https://arxiv.org/pdf/2402.14783 | 月面光伏建模(PV 热模型) |
| https://www.sciencedirect.com/science/article/abs/pii/S0360544225016470 | 月面 PV/T 系统 |
| https://www.epa.gov/smm/energy-recovery-combustion-municipal-solid-waste-msw | EPA 垃圾发电 550 kWh/吨 |
| https://en.wikipedia.org/wiki/Waste-to-energy_plant | 垃圾发电厂概述 |
| https://www.researchgate.net/post/How_can_I_calculate_how_much_electricity_can_be_generated_from_waste | 焚烧炉能效 22% 算例 |
| https://www.1-act.com/resources/blog/thermal-management-in-eclss-and-etcs-systems/ | ECLSS / ETCS 热管理 |
| https://ttu-ir.tdl.org/server/api/core/bitstreams/ac8532e0-75f2-4268-81ab-c1bc2f5f817a/content | ISS SRV-K 冷凝水回收(63%) |
| https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12298372/ | 膜生物反应器 90% |
| https://eden-iss.net/wp-content/uploads/4_EDENISS_FAQ.pdf | EDEN ISS 温室 FAQ |
| https://elib.dlr.de/186911/ | EDEN ISS 冷凝水回收子系统 |
| https://www.sciencedirect.com/science/article/pii/S221455242400066X | 太空植物栽培白皮书 |
| https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2019.01457/full | EDEN ISS 植物健康监测 |

---

## 十三、推荐叙事顺序(视频脚本建议)

1. **打开页面 / 初始化** — 演示 v4 三阶段流程的开局界面
2. **大气与生命保障** — 链接 ISS ECLSS / CDRA 现实
3. **批次农业 + 温室** — 用 EDEN ISS FAQ 引出蒸腾→冷凝的双重特征
4. **微藻** — MELiSSA + ISS ARTHROSPIRA-B 4 周批次的现实图
5. **净水流量指标** — ISS SRV-K 63% 数据,演示仪表盘的流量卡片
6. **电力系统** — 月面光伏 + ISS 太阳翼 31 kW,加上焚化补电
7. **科研系统 9 课题** — 把每个课题的现实链接快速过一遍,演示加成倍率
8. **突发事件** — 撞击 / SPE / 尘暴 → 演示耦合(护甲 → 减伤 → 失温 → 心情)
9. **乘组工作分配** — 演示 4 工作 + 双轨健康/心情,以及科研 lab 派员锁定
10. **死亡条件** — 演示 7 种死法,引出资源/角色/结构三轴的张力

---

## 附:文档版本对照

| 文档 | 涵盖系统 | 链接数 |
|------|---------|--------|
| version1.md | 突发事件 + 心情精细化 | 0(纯设计) |
| version2.md | 实验室 / 电力 / 9 科研课题 | 18 |
| version3.md | 净水指标 + 温室舱 | 6 |
| version4.md | 工作分配 + UI 重构 + 健康双轨 | 0(纯设计) |
| readme2.md | 当前实现整体说明 | — |
| video.md(本文档) | 现实依据 ↔ 游戏实现的全索引 | 28(去重) |
