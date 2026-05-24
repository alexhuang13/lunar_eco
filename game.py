import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Mac 推荐字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'PingFang HK', 'Heiti TC', 'STHeiti']
plt.rcParams['axes.unicode_minus'] = False   # 正常显示负号

# ==========================================
# 航天物理与生物工程参数 (真实对标版 & 无限扩展支持)
# ==========================================
DENSITY_O2 = 1.429
DENSITY_CO2 = 1.977
VOL_HABITAT, VOL_PLANT, VOL_COMPOST = 50.0, 80.0, 20.0
WATER_PER_HABITAT, WATER_PER_PLANT, WATER_PER_COMPOST = 100.0, 150.0, 50.0
O2_TANK_CAPACITY_PER_UNIT = 10.0
MAX_CO2_TANK_CAPACITY = 100.0  # 高压储碳罐最大容量

# 无限扩张的代价：每个舱室每天的基础资源维护损耗
MAINTENANCE_COST_PER_MODULE = 0.05

META = {"O2_CONS": 0.84, "CO2_PROD": 1.0, "WATER_USE": 14.5, "SOLID_WASTE": 0.2, "FOOD_CONS": 0.25}
BIO_PARAMS = {
    "ALGAE_CO2_ABS_KG": 0.25, "ALGAE_O2_PROD_KG": 0.20, "ALGAE_WATER_PUR_KG": 0.8,
    "COMPOST_MAX_SW_PER_UNIT": 3.0, "COMPOST_MAX_WW_PER_UNIT": 10.0,
    "MICP_SHIELD_PER_FERT": 2.5, "MICP_SHIELD_PER_WW": 0.5,
    "PLANT_BASE_EVAPORATION": 15.0
}

# ============================================================
# 【突发事件系统】事件定义库
# 事件分三类,对应三种时间尺度与应对模式:
#   "instant"  秒-分级 / 自动反射:一次性冲击参数
#   "ongoing"  分-小时级 / 人工应急:持续 duration 天的减益
#   "creeping" 天-周月级 / 趋势预警:慢变量漂移,初期不易察觉
# 每个事件的 impact / tick 接收 state 字典 s 和当日上下文 ctx,直接修改 s。
# ============================================================

def _solar_particle_impact(s, ctx):
    shield = s.get("Regolith_Shield_m2", 0.0)
    # 护甲每 m² 抵消一点冲击,护甲足够厚时几乎免疫 (>=250m² 基本免疫)
    exposure = max(0.0, 1.0 - shield * 0.004)
    # 🆕 v2:辐射医学课题完成后心情冲击 ×0.5
    rad_mood = s.get("research_multipliers", {}).get("radiation_mood", 1.0)
    ctx["mood_shock"](-25.0 * exposure * rad_mood)            # 士气暴跌(辐射焦虑)
    s["hull_integrity"] = max(0.0, s["hull_integrity"] - 3.0 * exposure)
    # 注:hull 损伤会由 _process_events 的 hull_durability wrap 进一步缩放


def _apply_mood(s, ctx, delta):
    ctx["mood_shock"](delta)


EVENT_LIBRARY = {
    # ---------- 秒-分级:自动反射类 ----------
    "micrometeoroid": {
        "name": "☄️ 微流星体撞击穿孔",
        "category": "instant",
        "weight": 1.0,
        "desc": "壳体被击穿,舱内大气向真空急速泄漏。同时打击结构完整性与大气(σ + A 耦合)。",
        "impact": lambda s, ctx: s.update({
            "O2_kg": s["O2_kg"] * 0.85,                        # A:失压跑气
            "CO2_kg": s["CO2_kg"] * 0.85,
            "hull_integrity": max(0.0, s["hull_integrity"] - 12.0),  # σ:结构受损
        }),
    },
    "solar_particle": {
        "name": "🌟 太阳高能粒子事件 (SPE)",
        "category": "instant",
        "weight": 1.2,
        "desc": "强辐射暴。月壤护甲薄则乘组士气暴跌(辐射焦虑),并损伤壳体。",
        "impact": lambda s, ctx: _solar_particle_impact(s, ctx),
    },
    "power_outage": {
        "name": "⚡ 主电源中断",
        "category": "instant",
        "weight": 0.9,
        "desc": "供电骤停,当日微藻与作物光合停摆,CDRA 气压调节失效一日。",
        "impact": lambda s, ctx: ctx["add_status"]("power_down", 1),
    },

    # ---------- 分-小时级:人工应急类 ----------
    "coolant_loss": {
        "name": "🌡️ 热控回路泄漏",
        "category": "ongoing",
        "duration": 4,
        "weight": 1.0,
        "desc": "散热能力下降,舱内升温,乘组每日承受热应激(士气持续下滑)。",
        "tick": lambda s, ctx: _apply_mood(s, ctx, -3.0),
    },
    "eclss_fault": {
        "name": "🔧 ECLSS 净化部件故障",
        "category": "ongoing",
        "duration": 5,
        "weight": 1.0,
        "desc": "CO2 洗涤效率下降,期间储碳罐无法吸收 CO2,毒性更易堆积。",
        "tick": lambda s, ctx: ctx["disable_scrubber"](),
    },
    "dust_storm": {
        "name": "🌪️ 火星/月面尘暴",
        "category": "ongoing",
        "duration": 7,
        "weight": 0.8,
        "desc": "遮蔽阳光,持续一周内光照效率大幅衰减(影响微藻与作物)。",
        "tick": lambda s, ctx: ctx["scale_light"](0.4),
    },

    # ---------- 天-周月级:趋势预警类 ----------
    "slow_leak": {
        "name": "🫧 密封件缓慢泄漏",
        "category": "creeping",
        "duration": 25,
        "weight": 0.9,
        "desc": "几乎察觉不到的微泄漏,每天悄悄损失少量大气,长期累积才致命。",
        "tick": lambda s, ctx: s.update({
            "O2_kg": s["O2_kg"] * 0.992,
            "CO2_kg": s["CO2_kg"] * 0.992,
        }),
    },
    "microbial_bloom": {
        "name": "🦠 杂菌生物膜暴发",
        "category": "creeping",
        "duration": 15,
        "weight": 0.8,
        "desc": "管路滋生杂菌,持续污染净水并与微藻争夺养分。",
        "tick": lambda s, ctx: s.update({
            "Clean_Water_kg": s["Clean_Water_kg"] - 3.0,
            "Waste_Water_kg": s["Waste_Water_kg"] + 3.0,
            "Algae_Biomass_kg": max(0.1, s["Algae_Biomass_kg"] * 0.98),
        }),
    },
    "embrittlement": {
        "name": "🧱 结构辐照脆化",
        "category": "creeping",
        "duration": 30,
        "weight": 0.7,
        "desc": "壳体材料缓慢脆化,结构完整性持续下滑——临界前几乎无征兆。",
        "tick": lambda s, ctx: s.update({
            "hull_integrity": max(0.0, s["hull_integrity"] - 0.8),
        }),
    },
}

# 🚀 极其硬核的 NASA 真实太空农业数据库
CROP_DATA = {
    "Wheat":   {"name": "Apogee 矮秆小麦 🌾", "cycle": 65, "daily_ww": 0.615, "daily_co2": 0.057, "daily_fert": 0.0038, "daily_cw": 0.600, "daily_o2": 0.046, "yield_food": 1.0, "yield_sw": 1.50},
    "Lettuce": {"name": "VEG-01 气雾生菜 🥬", "cycle": 33, "daily_ww": 1.818, "daily_co2": 0.054, "daily_fert": 0.0030, "daily_cw": 1.787, "daily_o2": 0.042, "yield_food": 1.0, "yield_sw": 0.25},
    "Potato":  {"name": "Quantum 微型土豆 🥔", "cycle": 80, "daily_ww": 0.562, "daily_co2": 0.026, "daily_fert": 0.0018, "daily_cw": 0.550, "daily_o2": 0.021, "yield_food": 1.0, "yield_sw": 0.40}
}
# 温室最大同时容纳承载量
PLANT_CAPACITY_PER_UNIT = 80.0

# ==========================================
# 🆕 v2 实验室 + 电力 + 科研系统常量
# ==========================================
# --- 实验室舱 (Lab) ---
VOL_LAB = 30.0                    # 实验室体积 m³
WATER_PER_LAB = 80.0              # 实验室构造水

# --- 电力系统 (Power) ---
# 太阳能:坑外独立收集器,与舱数解耦。极昼场景下日照接近恒满,受尘暴/断电压低
SOLAR_KWH_PER_M2_HOUR = 0.066     # 0.3 kW/m² × 22% 效率 → 0.066 kWh/m²/h
INCINERATOR_KWH_PER_KG = 0.4      # 焚化炉电效率 (EPA 550 kWh/吨 → 太空打折)
BATTERY_CAP_DEFAULT = 200.0       # 默认蓄电池容量 kWh
SOLAR_PANEL_M2_DEFAULT = 100.0    # 初始坑外光伏面积 m²

POWER_PER_HABITAT = 8.0           # 居住舱热维护 kWh/天/舱
POWER_PER_PLANT = 25.0            # 种植舱 (含 LED 补光) kWh/天/舱
POWER_PER_COMPOST = 3.0           # 堆肥舱 (微生物保温) kWh/天/舱
POWER_PER_LAB_IDLE = 5.0          # 实验室待机 kWh/天/舱
POWER_PER_LAB_ACTIVE = 15.0       # 实验室运行课题 kWh/天/舱

# 🆕 v3 温室舱 (Greenhouse) — 居住 + 种植 复合舱
# 数值依据 version3.md 的建议量级,取中间值。温室同时提供住宿(影响拥挤)和植物收支。
VOL_GREENHOUSE = 60.0             # 比居住舱稍大,含内部植物区 m³
WATER_PER_GREENHOUSE = 120.0      # 构造水 kg
POWER_PER_GREENHOUSE = 25.0       # LED 补光是大头 kWh/天/舱
GH_FERT_PER_DAY = 1.5             # 每舱每天耗肥 kg
GH_WW_PER_DAY = 12.0              # 每舱每天耗废水 kg(灌溉)
GH_CO2_PER_DAY = 0.75             # 每舱每天耗 CO2 kg
GH_O2_PER_DAY = 0.4               # 每舱每天产 O2 kg
GH_WATER_RECLAIM_PER_DAY = 7.0    # 每舱每天蒸腾冷凝产净水 kg(EDEN ISS 冷凝水回收)
GH_MOOD_BONUS_PER_UNIT = 3.0      # 每舱给每人每天心情加成(显著高于普通种植舱的 0.6)

# --- 科研系统 (Research) ---
RESEARCH_BASE_RATE = 1.0          # 每"有效人力单位"每天推进 1 天进度
RESEARCH_MOOD_PENALTY = -0.5      # 参与课题的乘员每日额外心情扣减
# 有效人力系数:idx = 参与人数, ≥4 封顶 2.5 (边际递减,真实科研规律)
EFFECTIVE_CREW_TABLE = [0.0, 1.0, 1.7, 2.2, 2.5]


# ============================================================
# 🆕 v2 【科研系统】课题库
# cycle 天数依据 version2.md 真实研究时间尺度等比缩放。
# on_complete 永久修改 state["research_multipliers"]。
# ============================================================

def _research_algae(m):
    m["algae_o2"] = 1.20
    m["algae_co2"] = 1.20

def _research_compost(m):
    m["compost"] = 1.25

def _research_crops(m):
    m["crop_yield"] = 1.20

def _research_isru(m):
    m["hull_durability"] = 1.50

def _research_solar(m):
    m["solar_efficiency"] = 1.30

def _research_water_loop(m):
    m["water_recycle"] = 1.20
    m["maintenance"] *= 0.7

def _research_radiation(m):
    m["radiation_mood"] = 0.5

def _research_sabatier(m):
    m["co2_to_water"] = True

def _research_automation(m):
    m["maintenance"] *= 0.5


RESEARCH_LIBRARY = {
    # ---------- 5 个基础课题 ----------
    "algae_strain": {
        "name": "🦠 高效螺旋藻菌株筛选",
        "cycle": 30,
        "desc": "ISS 4 周批次培养 → 优化菌株。完成后微藻产氧/吸碳系数 +20%。",
        "on_complete": _research_algae,
    },
    "compost_microbes": {
        "name": "🧫 堆肥高效微生物选育",
        "cycle": 35,
        "desc": "MELiSSA 降解菌选育。堆肥处理上限/产肥率 +25%。",
        "on_complete": _research_compost,
    },
    "crop_breeding": {
        "name": "🌾 加速作物育种 (Speed Breeding)",
        "cycle": 80,
        "desc": "NASA speed breeding。所有作物收获产量 +20%。",
        "on_complete": _research_crops,
    },
    "isru_wall": {
        "name": "🧱 ISRU 月壤+水墙复合材料",
        "cycle": 50,
        "desc": "月壤+2%水复合屏蔽。壳体抗冲击/抗辐射 +50% (事件 hull 损伤 ÷1.5)。",
        "on_complete": _research_isru,
    },
    "solar_upgrade": {
        "name": "☀️ 坑外太阳能阵列升级",
        "cycle": 45,
        "desc": "Artemis 垂直阵列+聚光。太阳能发电效率 +30%。",
        "on_complete": _research_solar,
    },
    # ---------- 4 个额外课题 (经你确认) ----------
    "water_loop": {
        "name": "💧 闭环水回收升级",
        "cycle": 40,
        "desc": "ISS ECLSS 水回收 98%→100%。净水回收 +20%,模块维护水耗 -30%。",
        "on_complete": _research_water_loop,
    },
    "radiation_med": {
        "name": "💊 辐射医学/乘组健康协议",
        "cycle": 40,
        "desc": "抗辐射防护+作息制度。SPE 等辐射事件心情冲击减半。",
        "on_complete": _research_radiation,
    },
    "sabatier": {
        "name": "⚗️ Sabatier CO₂ 再利用反应器",
        "cycle": 55,
        "desc": "ISS Sabatier 反应器。每日把过量 CO₂ 转化为水,缓解大气毒性。",
        "on_complete": _research_sabatier,
    },
    "automation": {
        "name": "🤖 自动化机器人维护",
        "cycle": 60,
        "desc": "降低每模块维护水耗 50%,大规模基地更可持续。",
        "on_complete": _research_automation,
    },
}


def _default_research_multipliers():
    """所有 mult 初始为 1.0 (无加成);课题完成后逐项修改。co2_to_water 是开关。"""
    return {
        "algae_o2": 1.0, "algae_co2": 1.0,
        "compost": 1.0, "crop_yield": 1.0,
        "hull_durability": 1.0, "solar_efficiency": 1.0,
        "water_recycle": 1.0, "radiation_mood": 1.0,
        "maintenance": 1.0,
        "co2_to_water": False,
    }


# ============================================================
# 🆕 v4 【角色工作分配系统】
# 每个角色每天只能选 1 项工作;耕作完全自动(不占工作位)。
# 工作产出按"边际递减"(复用 EFFECTIVE_CREW_TABLE)。
# 心情/健康双轨:心情=心理,健康=身体,分别可致崩溃。
# ============================================================
JOBS = {
    "rest":     {"name": "😴 休息",  "desc": "回复心情与健康(唯一恢复手段)"},
    "research": {"name": "🔬 科研",  "desc": "推进所在实验室课题进度"},
    "repair":   {"name": "🔧 修复",  "desc": "消耗月壤护甲材料,恢复壳体完整性"},
    "explore":  {"name": "⛏️ 采集",  "desc": "出舱采净水/月壤;辐射暴露扣健康,护甲可减免"},
}
JOB_DEFAULT = "rest"

# ============================================================
# 🆕 v5 【职业系统】每个角色一个固定职业,与"专长工作"匹配时效率 ×3
# 职业开局分配,游戏中不可改;工作每天可选,可与职业不匹配(只是没加成)。
# 同一队伍里专长人员越多 → 整体加成越高,但仍受 EFFECTIVE_CREW_TABLE 边际递减约束。
# ============================================================
PROFESSIONS = {
    "scientist": {"name": "🔬 科学家",  "specialty": "research", "desc": "科研效率 ×3"},
    "engineer":  {"name": "🔧 工程师",  "specialty": "repair",   "desc": "维修效率 ×3"},
    "explorer":  {"name": "⛏️ 探险家",  "specialty": "explore",  "desc": "采集效率 ×3"},
    "student":   {"name": "🎓 大学生",  "specialty": "rest",     "desc": "休息恢复 ×3"},
}
PROFESSION_DEFAULT = "student"
PROFESSION_BONUS = 3.0

def _team_prof_bonus(specialists, total):
    """队伍中 specialists 个"专长匹配者", total 个总人数;返回平均职业系数。
    匹配者 ×3, 其余 ×1, 平均后乘到团队产出上(满足"叠加+边际递减"约束)。"""
    if total <= 0:
        return 1.0
    return (specialists * PROFESSION_BONUS + (total - specialists)) / total

# 每项工作每人每天的心情/健康基础增减
JOB_MOOD_DELTA = {"rest": +5.0, "research": -2.0, "repair": -1.5, "explore": -1.5}
JOB_HEALTH_DELTA = {"rest": +5.0, "research": 0.0, "repair": -0.5, "explore": 0.0}  # 采集的辐射扣健康单独算

# 修复:每"有效人力单位"消耗 10 m² 月壤护甲 → 恢复 5 hull
REPAIR_SHIELD_COST_PER_EFF = 10.0
REPAIR_HULL_GAIN_PER_EFF = 5.0
# 采集:每"有效人力单位"产 20 kg 净水(月壤冰) + 5 m² 月壤;每人耗 5 kWh
EXPLORE_WATER_PER_EFF = 20.0
EXPLORE_REGOLITH_PER_EFF = 5.0
EXPLORE_POWER_PER_CREW = 5.0
# 采集辐射暴露:每人每天基础 -8 健康,被护甲线性减免(每 100 m² 减 2 点),最低保留 1.5
EXPLORE_RAD_BASE = 8.0
EXPLORE_RAD_MIN = 1.5

CREW_NAMES_POOL = ["林指挥", "郭工", "安妮", "张医生", "王飞行", "刘地质", "陈物理", "杨机械", "赵安全", "黄电工"]

st.set_page_config(page_title="天外家园：无限扩展生态沙盒", layout="wide")

# ==========================================
# 🆕 v4 状态机:game_started 区分"开局配置(可改)"与"运营中(锁定)"
# ==========================================
def _initialize_game(o2_tanks, crew_size, hab, plant, compost, professions=None):
    """玩家在开局界面点击"确认配置"后调用,设定锁定参数并初始化世界状态。
    🆕 v5: professions 是长度 crew_size 的职业 key 列表,缺省按 4 类轮转。"""
    professions = professions or [list(PROFESSIONS.keys())[i % len(PROFESSIONS)] for i in range(crew_size)]
    st.session_state.day = 0
    st.session_state.is_alive = True
    st.session_state.death_reason = ""
    st.session_state.last_hab = hab
    st.session_state.last_plant = plant
    st.session_state.last_compost = compost
    st.session_state.last_lab = 0
    st.session_state.last_greenhouse = 0
    st.session_state.init_tanks = o2_tanks
    st.session_state.locked_crew_size = crew_size                # 🆕 v4 初始锁定值(展示用)
    st.session_state.locked_initial = {                          # 🆕 v4 初始锁定配置快照
        "tanks": o2_tanks, "crew": crew_size,
        "hab": hab, "plant": plant, "compost": compost,
    }
    st.session_state.crew_list = [
        {"name": CREW_NAMES_POOL[i % len(CREW_NAMES_POOL)],
         "mood": 100.0, "health": 100.0, "job": JOB_DEFAULT,
         "profession": professions[i] if i < len(professions) else PROFESSION_DEFAULT}    # 🆕 v5
        for i in range(crew_size)
    ]
    st.session_state.crop_batches = []
    st.session_state.active_events = []
    st.session_state.event_log = []
    st.session_state.lab_projects = []
    st.session_state.solar_panel_m2 = SOLAR_PANEL_M2_DEFAULT

    start_vol = hab * VOL_HABITAT + plant * VOL_PLANT + compost * VOL_COMPOST
    st.session_state.state = {
        "O2_kg": start_vol * 0.21 * DENSITY_O2,
        "CO2_kg": start_vol * 0.0020 * DENSITY_CO2,
        "O2_Tank_kg": o2_tanks * O2_TANK_CAPACITY_PER_UNIT,
        "CO2_Tank_kg": 50.0,
        "Clean_Water_kg": 800.0,
        "Structural_Water_kg": hab * WATER_PER_HABITAT + plant * WATER_PER_PLANT + compost * WATER_PER_COMPOST,
        "Waste_Water_kg": 60.0,
        "Solid_Waste_kg": 2.0,
        "Fertilizer_kg": 10.0,
        "Food_kg": 80.0,
        "Algae_Biomass_kg": 10.0,
        "Regolith_Shield_m2": 0.0,
        "hull_integrity": 100.0,
        "Power_Battery_kWh": BATTERY_CAP_DEFAULT,
        "Power_Battery_Cap_kWh": BATTERY_CAP_DEFAULT,
        "research_multipliers": _default_research_multipliers(),
        "completed_research": [],
    }
    st.session_state.history = pd.DataFrame()
    st.session_state.game_started = True


if "game_started" not in st.session_state:
    st.session_state.game_started = False

# ---------- 🆕 v4 阶段 1:开局配置界面 ----------
if not st.session_state.game_started:
    st.title("🌙 天外家园 · 月球生态沙盒")
    st.markdown("---")
    st.header("🚀 任务初始化")
    st.caption("以下设定一旦确认将永久锁定,游戏中不可修改。请慎重决策——每一项都对应「带多少补给,选多少人,从多大基地开始」。")
    col_l, col_r = st.columns(2)
    with col_l:
        init_tanks_in = st.number_input("初始高压氧气瓶 (10kg/瓶)", min_value=0, value=10, step=1,
                                        help="着陆即可用的备用氧气储罐数量,游戏中无法补充。")
        init_crew_in = st.number_input("初始乘组规模 (人)", min_value=1, max_value=len(CREW_NAMES_POOL),
                                       value=4, step=1, help="任务开始时携带的乘员数。游戏中只能通过正面突发事件增加,不能自由调整。")
    with col_r:
        init_hab_in = st.number_input("初始居住舱数量", min_value=1, value=2, step=1)
        init_plant_in = st.number_input("初始种植舱数量", min_value=0, value=1, step=1)
        init_compost_in = st.number_input("初始堆肥舱数量", min_value=0, value=1, step=1)

    # 🆕 v5 职业分配
    st.markdown("---")
    st.subheader("👥 乘组职业分配")
    st.caption("每个角色一个固定职业;匹配工作时效率 ×3(科学家→科研 / 工程师→修复 / 探险家→采集 / 大学生→休息)。"
               "职业一旦确认全程不可改 —— 「带谁上月球」就是开局策略本身。")
    _prof_keys = list(PROFESSIONS.keys())
    _profs_chosen = []
    _prof_cols_per_row = 4
    for _i in range(init_crew_in):
        if _i % _prof_cols_per_row == 0:
            _prof_cols = st.columns(_prof_cols_per_row)
        with _prof_cols[_i % _prof_cols_per_row]:
            st.markdown(f"**{CREW_NAMES_POOL[_i % len(CREW_NAMES_POOL)]}**")
            _p = st.selectbox(
                f"职业 #{_i + 1}", _prof_keys,
                index=_i % len(_prof_keys),                                # 默认轮转:科/工/探/学
                format_func=lambda k: PROFESSIONS[k]["name"],
                key=f"init_profession_{_i}",
            )
            st.caption(PROFESSIONS[_p]["desc"])
            _profs_chosen.append(_p)

    st.info("游戏开始后,你可以继续扩建/拆除舱室(包括实验室、温室),并为每个角色分配每日工作:科研 / 休息 / 修复 / 采集。")
    if st.button("🚀 确认配置,开始任务", type="primary", use_container_width=True):
        _initialize_game(init_tanks_in, init_crew_in, init_hab_in, init_plant_in, init_compost_in,
                         professions=_profs_chosen)
        st.rerun()
    st.stop()

# ---------- 🆕 v4 阶段 2/3:运营中 — 旧存档兼容 ----------
for _k, _v in [
    ("last_lab", 0),
    ("lab_projects", []),
    ("solar_panel_m2", SOLAR_PANEL_M2_DEFAULT),
    ("last_greenhouse", 0),                      # 🆕 v3
    ("locked_crew_size", len(st.session_state.get("crew_list", []))),  # 🆕 v4
    ("locked_initial", {                                                # 🆕 v4
        "tanks": st.session_state.get("init_tanks", 10),
        "crew": len(st.session_state.get("crew_list", [])),
        "hab": st.session_state.get("last_hab", 2),
        "plant": st.session_state.get("last_plant", 1),
        "compost": st.session_state.get("last_compost", 1),
    }),
]:
    if _k not in st.session_state:
        st.session_state[_k] = _v
for _k, _v in [
    ("Power_Battery_kWh", BATTERY_CAP_DEFAULT),
    ("Power_Battery_Cap_kWh", BATTERY_CAP_DEFAULT),
    ("completed_research", []),
]:
    if _k not in st.session_state.state:
        st.session_state.state[_k] = _v
if "research_multipliers" not in st.session_state.state:
    st.session_state.state["research_multipliers"] = _default_research_multipliers()

# 🆕 v4 旧存档兼容:为缺 health/job 字段的成员补默认值
# 🆕 v5 旧存档兼容:为缺 profession 字段的成员补默认值(轮转分配)
for _idx, _c in enumerate(st.session_state.crew_list):
    _c.setdefault("health", 100.0)
    _c.setdefault("job", JOB_DEFAULT)
    _c.setdefault("profession", list(PROFESSIONS.keys())[_idx % len(PROFESSIONS)])

# 🆕 v4.1 旧存档兼容:为每个实验室项目补 assigned_crew 字段(显式人员指派)
for _p in st.session_state.lab_projects:
    _p.setdefault("assigned_crew", [])


def sync_crew_count(target_count):
    """仅在内部使用 — v4 起乘组规模初始锁定,只通过正面事件(未来)增长,不再支持自由调整。"""
    current_count = len(st.session_state.crew_list)
    if target_count > current_count:
        for i in range(current_count, target_count):
            name = CREW_NAMES_POOL[i] if i < len(CREW_NAMES_POOL) else f"后备梯队-{i+1}"
            st.session_state.crew_list.append({"name": name, "mood": 100.0, "health": 100.0, "job": JOB_DEFAULT})
    elif target_count < current_count:
        st.session_state.crew_list = st.session_state.crew_list[:target_count]


# ==========================================
# 🆕 突发事件处理引擎 (在 step_system 每日循环开头调用)
# ==========================================
def _process_events(s, day_index, hab, plant, compost, base_light, event_chance):
    """
    返回 ctx_flags 告知主循环本日修正:
      light_mult   光照倍率(尘暴/断电压低)
      scrubber_off 本日 CDRA 是否失效
      mood_delta   本日额外士气增减
    同时负责:推进持续事件、按概率触发新事件、写入 event_log。
    """
    ctx_flags = {"light_mult": 1.0, "scrubber_off": False, "mood_delta": 0.0}

    def add_status(key, days):
        st.session_state.active_events.append({"key": key, "days_left": days})

    def scale_light(m):
        ctx_flags["light_mult"] = min(ctx_flags["light_mult"], m)

    def disable_scrubber():
        ctx_flags["scrubber_off"] = True

    def mood_shock(d):
        ctx_flags["mood_delta"] += d

    ctx = {
        "add_status": add_status,
        "scale_light": scale_light,
        "disable_scrubber": disable_scrubber,
        "mood_shock": mood_shock,
        "day": day_index,
    }

    # 🆕 v2:执行事件函数,并把 hull 损伤按 hull_durability mult 缩放
    hull_dur = s.get("research_multipliers", {}).get("hull_durability", 1.0)

    def _run_with_hull_wrap(fn):
        pre = s["hull_integrity"]
        fn(s, ctx)
        post = s["hull_integrity"]
        dmg = pre - post
        if dmg > 0 and hull_dur > 1.0:
            s["hull_integrity"] = pre - dmg / hull_dur

    # 1. 推进所有持续中的事件
    still_active = []
    for ev in st.session_state.active_events:
        if ev["key"] == "power_down":
            # 内部状态:断电当日,光照归零 + 关闭储罐调节
            scale_light(0.0)
            disable_scrubber()
        else:
            spec = EVENT_LIBRARY.get(ev["key"])
            if spec and "tick" in spec:
                _run_with_hull_wrap(spec["tick"])
        ev["days_left"] -= 1
        if ev["days_left"] > 0:
            still_active.append(ev)
    st.session_state.active_events = still_active

    # 2. 按概率触发一个新的随机事件
    if event_chance > 0 and np.random.random() < event_chance:
        keys = list(EVENT_LIBRARY.keys())
        weights = np.array([EVENT_LIBRARY[k]["weight"] for k in keys], dtype=float)
        weights /= weights.sum()
        chosen = np.random.choice(keys, p=weights)
        spec = EVENT_LIBRARY[chosen]

        if spec["category"] == "instant":
            _run_with_hull_wrap(spec["impact"])
        else:
            add_status(chosen, spec["duration"])
            if "tick" in spec:
                _run_with_hull_wrap(spec["tick"])

        st.session_state.event_log.append(
            {"day": day_index + 1, "name": spec["name"], "desc": spec["desc"]}
        )

    return ctx_flags


# ==========================================
# 核心演算引擎
# ==========================================
def sync_lab_count(target_count):
    """🆕 v2:实验室扩建/拆除时同步 lab_projects 列表长度。
    🆕 v4.1:拆除时把被释放实验室的研究员解锁回默认工作。"""
    cur = len(st.session_state.lab_projects)
    if target_count > cur:
        for _ in range(target_count - cur):
            st.session_state.lab_projects.append({"project": None, "progress": 0.0, "crew": 0, "assigned_crew": []})
    elif target_count < cur:
        for _removed in st.session_state.lab_projects[target_count:]:
            for _ci in _removed.get("assigned_crew", []):
                if 0 <= _ci < len(st.session_state.crew_list):
                    st.session_state.crew_list[_ci]["job"] = JOB_DEFAULT
        st.session_state.lab_projects = st.session_state.lab_projects[:target_count]


def step_system(hab, plant, compost, lab, greenhouse, alg_ww, alg_fert, reg_fert, reg_ww,
                light_h, incinerator_rate, solar_panel_m2, days_step, event_chance):
    if not st.session_state.is_alive:
        return
    s = st.session_state.state
    sync_lab_count(lab)                                 # 🆕 v2
    m = s["research_multipliers"]                       # 🆕 v2 课题加成

    # 物理扩建判定 (含实验室舱、🆕 v3 温室舱)
    new_vol = (hab * VOL_HABITAT + plant * VOL_PLANT + compost * VOL_COMPOST
               + lab * VOL_LAB + greenhouse * VOL_GREENHOUSE)
    old_vol = (st.session_state.last_hab * VOL_HABITAT + st.session_state.last_plant * VOL_PLANT
               + st.session_state.last_compost * VOL_COMPOST + st.session_state.last_lab * VOL_LAB
               + st.session_state.last_greenhouse * VOL_GREENHOUSE)
    delta_hab = hab - st.session_state.last_hab
    delta_plant = plant - st.session_state.last_plant
    delta_compost = compost - st.session_state.last_compost
    delta_lab = lab - st.session_state.last_lab
    delta_gh = greenhouse - st.session_state.last_greenhouse

    if new_vol > old_vol:
        build_water = (delta_hab * WATER_PER_HABITAT + delta_plant * WATER_PER_PLANT
                       + delta_compost * WATER_PER_COMPOST + delta_lab * WATER_PER_LAB
                       + delta_gh * WATER_PER_GREENHOUSE)
        if build_water > 0:
            if s["Clean_Water_kg"] < build_water:
                st.sidebar.error(f"❌ 净水不足！扩建需要注水 {build_water} kg。")
                return
            s["Clean_Water_kg"] -= build_water
            s["Structural_Water_kg"] += build_water
    elif new_vol < old_vol:
        ratio = (old_vol - new_vol) / old_vol
        s["O2_kg"] *= (1 - ratio)
        s["CO2_kg"] *= (1 - ratio)
        recovered_water = (abs(delta_hab) * WATER_PER_HABITAT + abs(delta_plant) * WATER_PER_PLANT
                           + abs(delta_compost) * WATER_PER_COMPOST + abs(delta_lab) * WATER_PER_LAB
                           + abs(delta_gh) * WATER_PER_GREENHOUSE)
        s["Clean_Water_kg"] += recovered_water
        s["Structural_Water_kg"] -= recovered_water

    (st.session_state.last_hab, st.session_state.last_plant,
     st.session_state.last_compost, st.session_state.last_lab,
     st.session_state.last_greenhouse) = hab, plant, compost, lab, greenhouse
    total_modules = hab + plant + compost + lab + greenhouse

    # 每日循环推演
    for _ in range(days_step):
        # ===== 0. 突发事件处理 =====
        ev_ctx = _process_events(s, st.session_state.day, hab, plant, compost, light_h, event_chance)
        day_light = light_h * ev_ctx["light_mult"]    # 本日实际光照(可被尘暴/断电压低)

        vol = (hab * VOL_HABITAT + plant * VOL_PLANT + compost * VOL_COMPOST
               + lab * VOL_LAB + greenhouse * VOL_GREENHOUSE)         # 🆕 v3
        max_ww = plant * 150.0 + compost * 50.0 + 50.0
        max_sw = compost * 30.0 + 10.0

        # 🆕 v3 本日净水流量累加器:产量 (生物/化学回收) 与 消耗 (代谢/维护)
        daily_water_reclaimed = 0.0
        daily_water_consumed = 0.0

        O2_pct_current = (s["O2_kg"] / DENSITY_O2) / vol * 100
        CO2_pct_current = (s["CO2_kg"] / DENSITY_CO2) / vol * 100

        total_crew = len(st.session_state.crew_list)
        # 🆕 v3 温室舱也提供住宿,纳入"每房间人数"以缓解拥挤
        living_rooms = hab + greenhouse
        people_per_room = total_crew / living_rooms if living_rooms > 0 else total_crew

        # ===== 🆕 v2 1. 电力结算 (太阳能发电 - 各舱耗电) =====
        # 太阳能发电:坑外面板 × 日照小时 × 0.066 kWh/m²/h × 效率 mult
        gen_solar = solar_panel_m2 * SOLAR_KWH_PER_M2_HOUR * day_light * m.get("solar_efficiency", 1.0)
        # 各舱耗电:基础+实验室待机 + 🆕 v3 温室 LED 补光
        active_labs = sum(1 for proj in st.session_state.lab_projects if proj.get("project"))
        cons_total = (hab * POWER_PER_HABITAT + plant * POWER_PER_PLANT
                      + compost * POWER_PER_COMPOST + lab * POWER_PER_LAB_IDLE
                      + active_labs * (POWER_PER_LAB_ACTIVE - POWER_PER_LAB_IDLE)
                      + greenhouse * POWER_PER_GREENHOUSE)
        net_power = gen_solar - cons_total
        s["Power_Battery_kWh"] = min(s["Power_Battery_kWh"] + net_power, s["Power_Battery_Cap_kWh"])
        power_shortage = s["Power_Battery_kWh"] < 0
        if power_shortage:
            s["Power_Battery_kWh"] = 0.0
            # 后果:作物补光减半 + 实验室停摆 + 居住舱失温扣 hull
            s["hull_integrity"] = max(0.0, s["hull_integrity"] - 0.5)

        # ===== 🆕 v4 1.5 角色工作分配:统计今日各工作人员(研究员直接由 lab.assigned_crew 决定) =====
        repairer_list = [c for c in st.session_state.crew_list if c.get("job") == "repair"]
        explorer_list = [c for c in st.session_state.crew_list if c.get("job") == "explore"]
        repairers = len(repairer_list)
        explorers = len(explorer_list)

        # ===== 🆕 v4.1 2. 科研课题推进:研究员 = 显式 assigned_crew(立项时选定的乘员) =====
        # 每个 lab 直接持有 assigned_crew(乘员索引列表),无需"意向→分配"两步映射
        total_research_crew = 0
        for lab_proj in st.session_state.lab_projects:
            proj_key = lab_proj.get("project")
            if proj_key and proj_key in RESEARCH_LIBRARY:
                spec = RESEARCH_LIBRARY[proj_key]
                valid_crew = [ci for ci in lab_proj.get("assigned_crew", [])
                              if 0 <= ci < len(st.session_state.crew_list)]
                actual = len(valid_crew)
                if not power_shortage and actual > 0:
                    eff = EFFECTIVE_CREW_TABLE[min(actual, len(EFFECTIVE_CREW_TABLE) - 1)]
                    # 🆕 v5 职业加成:科学家做科研 ×3
                    n_sci = sum(1 for ci in valid_crew
                                if st.session_state.crew_list[ci].get("profession") == "scientist")
                    prof_bonus = _team_prof_bonus(n_sci, actual)
                    lab_proj["progress"] += RESEARCH_BASE_RATE * eff * prof_bonus
                    total_research_crew += actual
                    if lab_proj["progress"] >= spec["cycle"]:
                        spec["on_complete"](m)
                        s["completed_research"].append(proj_key)
                        # 课题完成 → 释放研究员回默认工作(休息)
                        for ci in valid_crew:
                            st.session_state.crew_list[ci]["job"] = JOB_DEFAULT
                        st.session_state.event_log.append({
                            "day": st.session_state.day + 1,
                            "name": f"🏆 课题完成: {spec['name']}",
                            "desc": spec["desc"],
                        })
                        lab_proj["project"] = None
                        lab_proj["progress"] = 0.0
                        lab_proj["crew"] = 0
                        lab_proj["assigned_crew"] = []

        # ===== 🆕 v4 2.5 修复与采集工作结算(🆕 v5 含职业加成) =====
        # 修复:消耗月壤护甲(建筑材料) → 恢复 hull
        # v5:工程师 ×3 仅放大 hull 产出(同样材料修出更多结构),材料消耗保持不变
        if repairers > 0 and s["Regolith_Shield_m2"] > 0:
            eff = EFFECTIVE_CREW_TABLE[min(repairers, len(EFFECTIVE_CREW_TABLE) - 1)]
            n_eng = sum(1 for c in repairer_list if c.get("profession") == "engineer")
            prof_bonus = _team_prof_bonus(n_eng, repairers)
            shield_cost = min(s["Regolith_Shield_m2"], REPAIR_SHIELD_COST_PER_EFF * eff)
            hull_gain = (shield_cost / REPAIR_SHIELD_COST_PER_EFF) * REPAIR_HULL_GAIN_PER_EFF * prof_bonus
            s["Regolith_Shield_m2"] -= shield_cost
            s["hull_integrity"] = min(100.0, s["hull_integrity"] + hull_gain)

        # 采集:出舱采净水(月壤冰)+月壤;耗电;辐射暴露(健康损失在第 5 段统一处理)
        # v5:探险家 ×3 放大水+月壤产出,但电力消耗保持不变
        if explorers > 0:
            eff = EFFECTIVE_CREW_TABLE[min(explorers, len(EFFECTIVE_CREW_TABLE) - 1)]
            n_exp = sum(1 for c in explorer_list if c.get("profession") == "explorer")
            prof_bonus = _team_prof_bonus(n_exp, explorers)
            pow_need = explorers * EXPLORE_POWER_PER_CREW
            pow_have = min(pow_need, s["Power_Battery_kWh"])
            s["Power_Battery_kWh"] -= pow_have
            pow_factor = (pow_have / pow_need) if pow_need > 0 else 1.0   # 电力打折则产出按比例下降
            explore_water = EXPLORE_WATER_PER_EFF * eff * pow_factor * prof_bonus
            explore_regolith = EXPLORE_REGOLITH_PER_EFF * eff * pow_factor * prof_bonus
            s["Clean_Water_kg"] += explore_water
            s["Regolith_Shield_m2"] += explore_regolith
            daily_water_reclaimed += explore_water

        # ===== 3. 基础设施维护损耗 (apply maintenance mult) =====
        maint_water = total_modules * MAINTENANCE_COST_PER_MODULE * m.get("maintenance", 1.0)
        s["Clean_Water_kg"] -= maint_water
        daily_water_consumed += maint_water                                  # 🆕 v3

        # ===== 4. 压力测试评估 (用于心情) =====
        resource_stress = 0
        if s["Food_kg"] <= 10.0:
            resource_stress += 10.0
        if O2_pct_current < 19.5:
            resource_stress += 8.0
        if CO2_pct_current > 0.5:
            resource_stress += 6.0
        if CO2_pct_current < 0.04:
            resource_stress += 5.0
        if s["Waste_Water_kg"] > max_ww:
            resource_stress += 5.0
        if s["Solid_Waste_kg"] > max_sw:
            resource_stress += 7.0

        # ===== 5. 心情/健康精细化模型 v4 (心情=心理 / 健康=身体,双轨独立) =====
        # 🆕 v4 辐射护甲减免系数 (用于采集出舱者): 护甲越厚,辐射健康损失越小
        shield = s["Regolith_Shield_m2"]
        explore_rad_per_person = max(EXPLORE_RAD_MIN, EXPLORE_RAD_BASE - shield * 0.02)
        anoxia = O2_pct_current < 19.5                          # 缺氧也扣健康
        co2_toxic = CO2_pct_current > 0.5
        for member in st.session_state.crew_list:
            job = member.get("job", JOB_DEFAULT)
            prof = member.get("profession", PROFESSION_DEFAULT)
            # 🆕 v5 大学生休息时,恢复效率 ×3(只放大 rest 的正向 mood/health,不放大其他负向项)
            rest_bonus = PROFESSION_BONUS if (job == "rest" and prof == "student") else 1.0

            # --- 心情 ---
            base_decay = -np.random.uniform(0.1, 0.5)
            greenhouse_bonus = plant * 0.6
            green_room_bonus = greenhouse * GH_MOOD_BONUS_PER_UNIT
            crew_support_bonus = total_crew * 0.20
            crowding_penalty = -people_per_room * 0.7
            shield_safety_bonus = min(5.0, shield * 0.02)
            resource_penalty = -resource_stress
            event_shock = ev_ctx["mood_delta"]
            job_mood = JOB_MOOD_DELTA.get(job, 0.0) * rest_bonus   # 🆕 v5 学生休息 ×3 心情恢复

            delta_m = (base_decay + greenhouse_bonus + green_room_bonus + crew_support_bonus
                       + crowding_penalty + shield_safety_bonus
                       + resource_penalty + event_shock + job_mood)
            member["mood"] = max(0.0, min(100.0, member["mood"] + delta_m))

            # --- 🆕 v4 健康 ---
            health_d = JOB_HEALTH_DELTA.get(job, 0.0) * rest_bonus    # 🆕 v5 学生休息 ×3 健康恢复
            if job == "explore":
                health_d -= explore_rad_per_person               # 辐射,被护甲减免
            if anoxia:
                health_d -= 1.0                                  # 缺氧扣健康
            if co2_toxic:
                health_d -= 1.0                                  # CO2 中毒扣健康
            member["health"] = max(0.0, min(100.0, member["health"] + health_d))
        avg_mood = np.mean([mm["mood"] for mm in st.session_state.crew_list]) if total_crew > 0 else 0
        avg_health = np.mean([mm["health"] for mm in st.session_state.crew_list]) if total_crew > 0 else 0

        # ===== 6. 代谢与常规堆肥 (apply compost mult) =====
        s["O2_kg"] -= META["O2_CONS"] * total_crew
        s["CO2_kg"] += META["CO2_PROD"] * total_crew
        metab_water = META["WATER_USE"] * total_crew
        s["Clean_Water_kg"] -= metab_water
        s["Waste_Water_kg"] += metab_water
        daily_water_consumed += metab_water                                   # 🆕 v3
        s["Solid_Waste_kg"] += META["SOLID_WASTE"] * total_crew
        s["Food_kg"] -= META["FOOD_CONS"] * total_crew

        comp_mult = m.get("compost", 1.0)
        proc_sw = min(s["Solid_Waste_kg"], BIO_PARAMS["COMPOST_MAX_SW_PER_UNIT"] * compost * comp_mult)
        proc_ww = min(s["Waste_Water_kg"], BIO_PARAMS["COMPOST_MAX_WW_PER_UNIT"] * compost * comp_mult)
        s["Solid_Waste_kg"] -= proc_sw
        s["Waste_Water_kg"] -= proc_ww
        s["Fertilizer_kg"] += (proc_sw * 0.8 + proc_ww * 0.9) * comp_mult
        s["CO2_kg"] += (proc_sw * 0.2 + proc_ww * 0.1)

        # ===== 7. 固废高温催化反应器 (燃烧补碳 + 🆕 v2 发电) =====
        act_inc = min(s["Solid_Waste_kg"], incinerator_rate)
        act_inc = min(act_inc, s["O2_kg"] / 1.5)
        if act_inc > 0:
            s["Solid_Waste_kg"] -= act_inc
            s["O2_kg"] -= act_inc * 1.1
            s["CO2_kg"] += act_inc * 1.5
            s["Waste_Water_kg"] += act_inc * 0.6
            # 🆕 v2:焚化发电充入蓄电池
            s["Power_Battery_kWh"] = min(s["Power_Battery_kWh"] + act_inc * INCINERATOR_KWH_PER_KG,
                                          s["Power_Battery_Cap_kWh"])

        # ===== 8. 外部防御排洪 (MICP) =====
        act_reg_fert = min(s["Fertilizer_kg"], reg_fert)
        act_reg_ww = min(s["Waste_Water_kg"], reg_ww)
        s["Fertilizer_kg"] -= act_reg_fert
        s["Waste_Water_kg"] -= act_reg_ww
        s["Regolith_Shield_m2"] += (act_reg_fert * BIO_PARAMS["MICP_SHIELD_PER_FERT"]
                                     + act_reg_ww * BIO_PARAMS["MICP_SHIELD_PER_WW"])

        # ===== 9. 微藻 (apply algae_o2/algae_co2/water_recycle mult) =====
        K_cap = max(1.0, total_modules) * 20.0
        act_alg_fert = min(s["Fertilizer_kg"], alg_fert)
        s["Fertilizer_kg"] -= act_alg_fert
        nut_factor = (alg_ww + act_alg_fert * 10) / (s["Waste_Water_kg"] + 1) if (s["Waste_Water_kg"] + act_alg_fert) > 0 else 0
        l_fac = day_light / 24.0
        g_rate = 0.3 * l_fac * min(1.0, nut_factor * 5) if l_fac > 0 else -0.1
        s["Algae_Biomass_kg"] = max(0.1, s["Algae_Biomass_kg"] + g_rate * s["Algae_Biomass_kg"] * (1 - s["Algae_Biomass_kg"] / K_cap))
        alg_pur = min(min(s["Waste_Water_kg"], alg_ww), BIO_PARAMS["ALGAE_WATER_PUR_KG"] * s["Algae_Biomass_kg"])
        s["Waste_Water_kg"] -= alg_pur
        alg_pur_clean = alg_pur * m.get("water_recycle", 1.0)
        s["Clean_Water_kg"] += alg_pur_clean
        daily_water_reclaimed += alg_pur_clean                               # 🆕 v3
        alg_co2_abs = min(s["CO2_kg"], BIO_PARAMS["ALGAE_CO2_ABS_KG"] * m.get("algae_co2", 1.0) * s["Algae_Biomass_kg"] * l_fac)
        s["CO2_kg"] -= alg_co2_abs
        s["O2_kg"] += alg_co2_abs * 0.8 * m.get("algae_o2", 1.0)

        # ===== 10. 农作物 (apply crop_yield/water_recycle/缺电补光减半) =====
        base_evap = min(s["Waste_Water_kg"], plant * BIO_PARAMS["PLANT_BASE_EVAPORATION"])
        s["Waste_Water_kg"] -= base_evap
        base_evap_clean = base_evap * m.get("water_recycle", 1.0)
        s["Clean_Water_kg"] += base_evap_clean
        daily_water_reclaimed += base_evap_clean                              # 🆕 v3

        tot_req_ww = tot_req_co2 = tot_req_fert = 0.0
        for batch in st.session_state.crop_batches:
            cinfo = CROP_DATA[batch['type']]
            tot_req_ww += cinfo['daily_ww'] * batch['amount']
            tot_req_co2 += cinfo['daily_co2'] * batch['amount']
            tot_req_fert += cinfo['daily_fert'] * batch['amount']

        # 灌溉水池 = 废水 + 净水(净水作为废水不足时的备用源)
        total_water_pool = s["Waste_Water_kg"] + s["Clean_Water_kg"]
        r_ww = min(1.0, total_water_pool / tot_req_ww) if tot_req_ww > 0 else 1.0
        r_co2 = min(1.0, s["CO2_kg"] / tot_req_co2) if tot_req_co2 > 0 else 1.0
        r_fert = min(1.0, s["Fertilizer_kg"] / tot_req_fert) if tot_req_fert > 0 else 1.0

        # 光照系数:既受事件影响,也受缺电影响(LED 补光减半)
        light_crop_factor = (day_light / light_h) if light_h > 0 else 0.0
        if power_shortage:
            light_crop_factor *= 0.5

        surviving_batches = []
        for batch in st.session_state.crop_batches:
            cinfo = CROP_DATA[batch['type']]
            amt = batch['amount']

            # 灌溉:先从废水扣,不够再从净水补
            need_irrig = r_ww * cinfo['daily_ww'] * amt
            take_ww = min(need_irrig, s["Waste_Water_kg"])
            take_cw_irrig = min(need_irrig - take_ww, s["Clean_Water_kg"])
            s["Waste_Water_kg"] -= take_ww
            s["Clean_Water_kg"] -= take_cw_irrig
            daily_water_consumed += take_cw_irrig                              # 净水灌溉计入消耗

            # 蒸腾回收净水(与实际灌溉量挂钩)
            act_cw = r_ww * cinfo['daily_cw'] * amt * m.get("water_recycle", 1.0)
            s["Clean_Water_kg"] += act_cw
            daily_water_reclaimed += act_cw                                   # 🆕 v3

            act_co2_ratio = min(r_ww, r_co2) * light_crop_factor
            act_co2 = act_co2_ratio * cinfo['daily_co2'] * amt
            act_o2 = act_co2_ratio * cinfo['daily_o2'] * amt
            s["CO2_kg"] -= act_co2
            s["O2_kg"] += act_o2

            act_fert = r_fert * cinfo['daily_fert'] * amt
            s["Fertilizer_kg"] -= act_fert

            supply_min = min(r_ww, r_co2, r_fert)
            if supply_min < 0.5:
                batch['health'] -= 5.0 * (1.0 - supply_min)
            elif supply_min >= 0.8:
                batch['health'] = min(100.0, batch['health'] + 5.0)

            if batch['health'] <= 0:
                s["Solid_Waste_kg"] += amt * cinfo['yield_sw'] * 0.5
            else:
                batch['age'] += 1
                if batch['age'] >= cinfo['cycle']:
                    health_penalty = batch['health'] / 100.0
                    s["Food_kg"] += amt * cinfo['yield_food'] * health_penalty * m.get("crop_yield", 1.0)
                    s["Solid_Waste_kg"] += amt * cinfo['yield_sw']
                else:
                    surviving_batches.append(batch)

        st.session_state.crop_batches = surviving_batches

        # ===== 🆕 v3 10.5 温室舱结算 =====
        # 居住+种植复合舱:耗肥/废水/CO2 → 产 O2/净水 + 心情已在第 5 段加成
        # 缺电时 LED 减半,产出按光照系数缩放;受供应短板限制(min ratio)
        if greenhouse > 0:
            gh_light = light_crop_factor if light_h > 0 else 0.0       # 复用作物光照系数(含缺电减半)
            req_ww = greenhouse * GH_WW_PER_DAY
            req_co2 = greenhouse * GH_CO2_PER_DAY
            req_fert = greenhouse * GH_FERT_PER_DAY
            # 灌溉水池 = 废水 + 净水(净水作为废水不足时的备用源)
            gh_water_pool = s["Waste_Water_kg"] + s["Clean_Water_kg"]
            r_gh_ww = min(1.0, gh_water_pool / req_ww) if req_ww > 0 else 1.0
            r_gh_co2 = min(1.0, s["CO2_kg"] / req_co2) if req_co2 > 0 else 1.0
            r_gh_fert = min(1.0, s["Fertilizer_kg"] / req_fert) if req_fert > 0 else 1.0
            gh_factor = min(r_gh_ww, r_gh_co2, r_gh_fert) * gh_light * m.get("crop_yield", 1.0)

            # 灌溉:先从废水扣,不够再从净水补
            need_gh_irrig = req_ww * r_gh_ww
            take_gh_ww = min(need_gh_irrig, s["Waste_Water_kg"])
            take_gh_cw = min(need_gh_irrig - take_gh_ww, s["Clean_Water_kg"])
            s["Waste_Water_kg"] -= take_gh_ww
            s["Clean_Water_kg"] -= take_gh_cw
            daily_water_consumed += take_gh_cw

            s["CO2_kg"] -= req_co2 * r_gh_co2
            s["Fertilizer_kg"] -= req_fert * r_gh_fert
            s["O2_kg"] += greenhouse * GH_O2_PER_DAY * gh_factor

            # 蒸腾→冷凝回收净水(EDEN ISS 主力水源,本日净水流量主力之一)
            gh_water = greenhouse * GH_WATER_RECLAIM_PER_DAY * gh_factor * m.get("water_recycle", 1.0)
            s["Clean_Water_kg"] += gh_water
            daily_water_reclaimed += gh_water

        # ===== 🆕 v2 11. Sabatier 反应器:CO₂ → 水 (课题完成后启用) =====
        if m.get("co2_to_water", False):
            co2_threshold = 0.3 / 100 * vol * DENSITY_CO2     # 高于 0.3% 才转化
            if s["CO2_kg"] > co2_threshold:
                conv_co2 = min(s["CO2_kg"] - co2_threshold, 2.0)  # 上限 2 kg CO2/天
                s["CO2_kg"] -= conv_co2
                sabatier_water = conv_co2 * 0.5               # 近似化学计量比
                s["Clean_Water_kg"] += sabatier_water
                daily_water_reclaimed += sabatier_water        # 🆕 v3

        # ===== 12. 智能气压保护与 CO2 洗涤/释放池 (CDRA) =====
        temp_o2_pct = (s["O2_kg"] / DENSITY_O2) / vol * 100
        if temp_o2_pct > 24.0 and s["O2_Tank_kg"] < (st.session_state.init_tanks * O2_TANK_CAPACITY_PER_UNIT):
            mass_to_pull = min(s["O2_kg"] - (24.0 / 100 * vol * DENSITY_O2), (st.session_state.init_tanks * O2_TANK_CAPACITY_PER_UNIT) - s["O2_Tank_kg"])
            s["O2_kg"] -= max(0, mass_to_pull)
            s["O2_Tank_kg"] += max(0, mass_to_pull)
        elif temp_o2_pct < 19.5 and s["O2_Tank_kg"] > 0:
            mass_to_push = min((19.5 / 100 * vol * DENSITY_O2) - s["O2_kg"], s["O2_Tank_kg"])
            s["O2_kg"] += max(0, mass_to_push)
            s["O2_Tank_kg"] -= max(0, mass_to_push)

        temp_co2_pct = (s["CO2_kg"] / DENSITY_CO2) / vol * 100
        if (temp_co2_pct > 0.3 and s["CO2_Tank_kg"] < MAX_CO2_TANK_CAPACITY
                and not ev_ctx["scrubber_off"]):
            mass_to_pull = min(s["CO2_kg"] - (0.3 / 100 * vol * DENSITY_CO2), MAX_CO2_TANK_CAPACITY - s["CO2_Tank_kg"])
            s["CO2_kg"] -= max(0, mass_to_pull)
            s["CO2_Tank_kg"] += max(0, mass_to_pull)
        elif temp_co2_pct < 0.05 and s["CO2_Tank_kg"] > 0:
            mass_to_push = min((0.05 / 100 * vol * DENSITY_CO2) - s["CO2_kg"], s["CO2_Tank_kg"])
            s["CO2_kg"] += max(0, mass_to_push)
            s["CO2_Tank_kg"] -= max(0, mass_to_push)

        final_O2_pct = (s["O2_kg"] / DENSITY_O2) / vol * 100
        final_CO2_pct = (s["CO2_kg"] / DENSITY_CO2) / vol * 100

        st.session_state.day += 1
        history_entry = {
            "Day": st.session_state.day, "O2_percent": final_O2_pct, "CO2_percent": final_CO2_pct,
            "Clean_Water": s["Clean_Water_kg"], "Waste_Water": s["Waste_Water_kg"], "Max_WW": max_ww,
            "Solid_Waste": s["Solid_Waste_kg"], "Max_SW": max_sw,
            "Algae_Biomass": s["Algae_Biomass_kg"], "Food": s["Food_kg"], "Fertilizer": s["Fertilizer_kg"],
            "Mood": avg_mood, "O2_Tank": s["O2_Tank_kg"], "CO2_Tank": s["CO2_Tank_kg"],
            "Regolith_Shield": s["Regolith_Shield_m2"], "Hull": s["hull_integrity"],
            # 🆕 v2
            "Battery": s["Power_Battery_kWh"], "Battery_Cap": s["Power_Battery_Cap_kWh"],
            "Power_Net": net_power,
            # 🆕 v3 净水流量
            "Water_Reclaimed": daily_water_reclaimed,
            "Water_Consumed": daily_water_consumed,
            "Water_Net": daily_water_reclaimed - daily_water_consumed,
            # 🆕 v4 健康均值
            "Health": avg_health,
        }
        st.session_state.history = pd.concat([st.session_state.history, pd.DataFrame([history_entry])], ignore_index=True)

        if final_CO2_pct > 3.0:
            st.session_state.is_alive = False
            st.session_state.death_reason = "CO2 毒性崩溃"
            break
        if final_O2_pct < 18.0:
            st.session_state.is_alive = False
            st.session_state.death_reason = "缺氧崩溃 (尝试检查气瓶与制氧)"
            break
        if s["Clean_Water_kg"] < 0:
            st.session_state.is_alive = False
            st.session_state.death_reason = "饮用水枯竭"
            break
        if s["Food_kg"] < 0:
            st.session_state.is_alive = False
            st.session_state.death_reason = "口粮断绝"
            break
        if avg_mood <= 0:
            st.session_state.is_alive = False
            st.session_state.death_reason = "乘组精神崩溃，发生兵变！"
            break
        # 🆕 v4 健康双轨死亡判定
        if avg_health <= 0:
            st.session_state.is_alive = False
            st.session_state.death_reason = "乘组身体衰竭 (辐射/缺氧/过劳累积致死)"
            break
        if s["hull_integrity"] <= 0:
            st.session_state.is_alive = False
            st.session_state.death_reason = "壳体结构失效，舱体解体失压"
            break


# ==========================================
# 前端呈现 (Dashboard)
# ==========================================
st.header(f"📅 基地运转日志：第 {st.session_state.day} 天")

# 🆕 v4 角色面板:逐人显示心情/健康/今日工作 + 工作分配下拉
def _mood_health_tier(v):
    if v > 70:  return "✅"
    if v >= 40: return "⚠️"
    return "🚨"

st.subheader("👥 乘组工作分配")
st.caption("每位乘员每天选 1 项工作;产出按边际递减,休息是唯一的心情/健康恢复手段。耕作完全自动。"
           "「🔬科研」只能通过侧边栏「科研课题立项」派遣,被派遣的乘员在此处不可改派。")
_crew_n = len(st.session_state.crew_list)
# 🆕 v4.1 计算谁被锁定在科研(以及锁在哪个实验室)
_locked_to_lab = {}
for _li, _proj in enumerate(st.session_state.lab_projects):
    if _proj.get("project"):
        for _ci in _proj.get("assigned_crew", []):
            _locked_to_lab[_ci] = _li
# 自由选项不含 "research"(只能通过 lab 立项分派)
_free_job_keys = [k for k in JOBS if k != "research"]
_per_row = 4
for _row_start in range(0, _crew_n, _per_row):
    _row_members = st.session_state.crew_list[_row_start:_row_start + _per_row]
    _cols = st.columns(_per_row)
    for _i, _member in enumerate(_row_members):
        _abs_idx = _row_start + _i
        with _cols[_i]:
            _mt = _mood_health_tier(_member["mood"])
            _ht = _mood_health_tier(_member["health"])
            _prof_key = _member.get("profession", PROFESSION_DEFAULT)
            _prof = PROFESSIONS.get(_prof_key, PROFESSIONS[PROFESSION_DEFAULT])
            st.markdown(
                f"**{_member['name']}** · {_prof['name']}  \n"
                f"心情 {_mt} **{_member['mood']:.0f}** · 健康 {_ht} **{_member['health']:.0f}**"
            )
            if _abs_idx in _locked_to_lab:
                _lab_n = _locked_to_lab[_abs_idx] + 1
                _proj_key = st.session_state.lab_projects[_locked_to_lab[_abs_idx]].get("project")
                _proj_name = RESEARCH_LIBRARY[_proj_key]["name"] if _proj_key in RESEARCH_LIBRARY else "?"
                _spec_badge = " ✨ **×3 专长**" if _prof["specialty"] == "research" else ""
                st.markdown(f"🔒 **科研中** · 实验室 #{_lab_n}{_spec_badge}")
                st.caption(f"课题:{_proj_name} · 解锁请去侧边栏卸下课题或取消派遣")
            else:
                _cur_job = _member.get("job", JOB_DEFAULT)
                if _cur_job not in _free_job_keys:                      # 旧 job 已失效 → 回默认
                    _cur_job = JOB_DEFAULT
                _new_job = st.selectbox(
                    "今日工作", _free_job_keys,
                    index=_free_job_keys.index(_cur_job),
                    format_func=lambda k: JOBS[k]["name"] + (" ✨×3" if PROFESSIONS[_prof_key]["specialty"] == k else ""),
                    key=f"job_select_{_abs_idx}",
                )
                _member["job"] = _new_job
                if _prof["specialty"] == _new_job:
                    st.caption(f"✨ **×3 专长匹配** — {JOBS[_new_job]['desc']}")
                else:
                    st.caption(JOBS[_new_job]["desc"])
st.markdown("---")

with st.sidebar:
    # 🆕 v4 阶段 3:锁定参数(只读展示)
    st.header("🔒 任务约束 (开局已锁定)")
    _lk = st.session_state.locked_initial
    st.markdown(
        f"- 着陆携带 **{_lk['tanks']}** 瓶储氧罐\n"
        f"- 初始乘组 **{_lk['crew']}** 人\n"
        f"- 初始舱室 居住 **{_lk['hab']}** / 种植 **{_lk['plant']}** / 堆肥 **{_lk['compost']}**"
    )
    st.caption("以上为开局战略约束,无法在游戏中修改;乘组规模未来仅可通过正面突发事件增长。")

    st.markdown("---")
    st.header("🏠 舱室扩建 / 拆除")
    st.caption("游戏中可继续建造或拆除任意舱室(消耗净水构造,拆除回收一半结构水)。")
    hab = st.number_input("居住舱数量 (个)", min_value=1, value=st.session_state.last_hab, step=1)
    plant = st.number_input("种植舱数量 (个)", min_value=0, value=st.session_state.last_plant, step=1)
    compost = st.number_input("堆肥舱数量 (个)", min_value=0, value=st.session_state.last_compost, step=1)
    lab = st.number_input("🆕 实验室舱数量 (个)", min_value=0, value=st.session_state.last_lab, step=1,
                          help=f"每舱 {VOL_LAB} m³、构造水 {WATER_PER_LAB} kg；待机 {POWER_PER_LAB_IDLE} kWh/天，运行课题时 {POWER_PER_LAB_ACTIVE} kWh/天。")
    greenhouse = st.number_input("🆕 v3 温室舱数量 (个)", min_value=0, value=st.session_state.last_greenhouse, step=1,
                                 help=(f"居住+种植复合舱，每舱 {VOL_GREENHOUSE} m³、构造水 {WATER_PER_GREENHOUSE} kg。"
                                       f"每天耗肥 {GH_FERT_PER_DAY} / 废水 {GH_WW_PER_DAY} / CO₂ {GH_CO2_PER_DAY} kg、电 {POWER_PER_GREENHOUSE} kWh，"
                                       f"产 O₂ {GH_O2_PER_DAY} / 净水 {GH_WATER_RECLAIM_PER_DAY} kg/舱，并显著提升乘组心情。"))

    st.markdown("---")
    st.header("⚡ 电力系统")
    solar_panel_m2 = st.number_input("☀️ 坑外光伏面积 (m²)", min_value=0.0,
                                     value=float(st.session_state.solar_panel_m2), step=20.0,
                                     help=f"独立坑外阵列,与舱数解耦。基准 {SOLAR_KWH_PER_M2_HOUR:.3f} kWh/m²/h × 日照时长 × 效率倍率。")
    st.session_state.solar_panel_m2 = solar_panel_m2

    st.markdown("---")
    st.header("🌱 批次农业播种中心")
    current_load = sum(b['amount'] for b in st.session_state.crop_batches)
    max_load = plant * PLANT_CAPACITY_PER_UNIT
    st.caption(f"当前温室承载量: {current_load:.1f} / {max_load:.1f} kg")

    col_a, col_b = st.columns([3, 2])
    sel_crop = col_a.selectbox("播种作物", ["Lettuce", "Potato", "Wheat"], format_func=lambda x: CROP_DATA[x]['name'])
    sel_amt = col_b.number_input("预期产出 (kg)", min_value=1.0, value=15.0, step=5.0)

    if st.button("🚜 下达播种指令", use_container_width=True):
        if plant == 0:
            st.error("没有种植舱，无法播种！")
        elif current_load + sel_amt > max_load:
            st.error("温室容量不足！请等待作物成熟或增建种植舱。")
        else:
            st.session_state.crop_batches.append({"type": sel_crop, "amount": sel_amt, "age": 0, "health": 100.0})
            st.success(f"成功播种！预期 {CROP_DATA[sel_crop]['cycle']} 天后收获 {sel_amt}kg {CROP_DATA[sel_crop]['name']}。")
            st.rerun()

    st.markdown("---")
    st.header("🛡️ 污染治理与应急脱困")
    st.caption("极端缺碳或积水时使用的强力干预手段")
    incinerator_rate = st.number_input("🔥 固废高温催化炉 (kg/天)", min_value=0.0, value=0.0, step=2.0, help="燃烧垃圾和氧气，极速释放 CO2 挽救植物碳饥饿")
    reg_ww = st.number_input("排向月壤的废水 (kg/天)", min_value=0.0, value=0.0, step=10.0)
    reg_fert = st.number_input("排向月壤的化肥 (kg/天)", min_value=0.0, value=0.0, step=2.0)

    st.markdown("---")
    st.header("🦠 微藻光水调控")
    alg_ww = st.number_input("微藻废水通量 (kg/天)", min_value=0.0, value=20.0, step=10.0)
    alg_fert = st.number_input("微藻施肥量 (kg/天)", min_value=0.0, value=0.5, step=0.5)
    light_h = st.slider("光照时长 (h/day)", 0, 24, 16)

    st.markdown("---")
    st.header("🔬 科研课题立项")
    # 同步 lab_projects 列表长度,使 UI 总能渲染当前 lab 数量
    sync_lab_count(lab)
    if lab == 0:
        st.caption("尚未建造实验室舱。建造后可在此处为每个实验室立项与派人。")
    else:
        completed = set(st.session_state.state.get("completed_research", []))
        # 选项 = 未完成 & 未被其他 lab 占用 的课题
        in_progress = {p["project"] for p in st.session_state.lab_projects if p.get("project")}
        for idx, proj in enumerate(st.session_state.lab_projects):
            st.markdown(f"**实验室 #{idx + 1}**")
            cur_key = proj.get("project")
            available = [k for k in RESEARCH_LIBRARY
                         if k not in completed and (k == cur_key or k not in in_progress)]
            options = ["(空闲)"] + available
            cur_label = cur_key if cur_key in available else "(空闲)"
            choice = st.selectbox(
                f"课题 #{idx + 1}", options, index=options.index(cur_label),
                format_func=lambda k: "(空闲)" if k == "(空闲)" else f"{RESEARCH_LIBRARY[k]['name']} · {RESEARCH_LIBRARY[k]['cycle']}天",
                key=f"lab_proj_{idx}",
            )
            new_key = None if choice == "(空闲)" else choice
            if new_key != cur_key:
                # 切换/卸下课题:释放原研究员回默认工作,重置进度
                for _ci in proj.get("assigned_crew", []):
                    if 0 <= _ci < len(st.session_state.crew_list):
                        st.session_state.crew_list[_ci]["job"] = JOB_DEFAULT
                proj["assigned_crew"] = []
                proj["project"] = new_key
                proj["progress"] = 0.0

            # 🆕 v4.1 立项后,直接 multiselect 选派乘员;被选中者状态锁定为「🔬科研」
            if new_key:
                _crew_n = len(st.session_state.crew_list)
                # 可选范围 = 全员减去其他 lab 已占用者(本 lab 当前在岗者保留)
                _in_other_labs = set()
                for _j, _other in enumerate(st.session_state.lab_projects):
                    if _j != idx:
                        _in_other_labs.update(_other.get("assigned_crew", []))
                _crew_options = [i for i in range(_crew_n) if i not in _in_other_labs]
                _cur_assigned = [i for i in proj.get("assigned_crew", []) if i in _crew_options]
                _max = len(EFFECTIVE_CREW_TABLE) - 1                       # 4 人封顶
                def _fmt_crew(i):
                    _c = st.session_state.crew_list[i]
                    _pk = _c.get("profession", PROFESSION_DEFAULT)
                    _sci = " ✨×3" if PROFESSIONS.get(_pk, {}).get("specialty") == "research" else ""
                    return (f"{_c['name']} · {PROFESSIONS.get(_pk, {}).get('name', '?')}{_sci} "
                            f"(心情{_c['mood']:.0f}/健康{_c['health']:.0f})")
                _selected = st.multiselect(
                    f"派遣乘员 (上限 {_max} 人,边际递减)",
                    options=_crew_options,
                    default=_cur_assigned,
                    format_func=_fmt_crew,
                    max_selections=_max,
                    key=f"lab_assigned_{idx}",
                    help="选中即把该乘员的工作锁定为「🔬科研」,主面板上他们无法改派。"
                         "1人=1.0× / 2人=1.7× / 3人=2.2× / 4人=2.5×(封顶);科学家 ×3 专长再叠加。",
                )
                _old_set, _new_set = set(proj.get("assigned_crew", [])), set(_selected)
                for _ci in _old_set - _new_set:                            # 取消选派的人回默认
                    if 0 <= _ci < _crew_n:
                        st.session_state.crew_list[_ci]["job"] = JOB_DEFAULT
                for _ci in _new_set - _old_set:                            # 新选派的人锁为科研
                    if 0 <= _ci < _crew_n:
                        st.session_state.crew_list[_ci]["job"] = "research"
                proj["assigned_crew"] = list(_selected)
                proj["crew"] = len(_selected)                              # 维持旧字段一致(便于面板显示)

                spec = RESEARCH_LIBRARY[new_key]
                pct = min(1.0, proj["progress"] / spec["cycle"])
                st.progress(pct, text=f"进度 {proj['progress']:.1f} / {spec['cycle']} 天")
                st.caption(spec["desc"])
            else:
                proj["crew"] = 0
            st.markdown("")

    st.markdown("---")
    st.header("⚠️ 突发事件强度")
    event_level = st.select_slider("事件发生频率", options=["关闭", "低", "中", "高"], value="低",
                                   help="每天发生突发事件的概率。撞击/辐射/泄漏等会精确打击对应参数,并可能级联。")
    event_chance = {"关闭": 0.0, "低": 0.04, "中": 0.10, "高": 0.20}[event_level]

    step = st.slider("推演时间跨度 (可跳跃加速)", 1, 30, 5)
    if st.button("⏳ 闭环演进 (时间流逝)", type="primary", use_container_width=True):
        step_system(hab, plant, compost, lab, greenhouse, alg_ww, alg_fert, reg_fert, reg_ww,
                    light_h, incinerator_rate, solar_panel_m2, step, event_chance)

if not st.session_state.is_alive:
    st.error(f"💀 生物圈崩溃！原委：{st.session_state.death_reason}")
    if st.button("🔄 初始化新基地"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

if not st.session_state.history.empty:
    cur = st.session_state.history.iloc[-1]
    cur_max_ww = st.session_state.last_plant * 150.0 + st.session_state.last_compost * 50.0 + 50.0
    cur_max_sw = st.session_state.last_compost * 30.0 + 10.0

    # 🆕 进行中的事件提示
    if st.session_state.active_events:
        active_names = [EVENT_LIBRARY[e["key"]]["name"] + f"(剩{e['days_left']}天)"
                        for e in st.session_state.active_events if e["key"] in EVENT_LIBRARY]
        if active_names:
            st.warning("🔴 进行中的事件：" + " ｜ ".join(active_names))

    # 🆕 壳体结构完整性进度条
    hull = st.session_state.state.get("hull_integrity", 100.0)
    st.progress(max(0.0, min(1.0, hull / 100.0)), text=f"🛡️ 壳体结构完整性 σ：{hull:.1f} / 100")

    # 农作物实时监控大屏
    with st.expander("🌾 农作物实时生长监控大屏 (点击展开)", expanded=True):
        if len(st.session_state.crop_batches) == 0:
            st.info("目前温室处于闲置状态，请在左侧下达播种指令。")
        else:
            display_data = []
            for i, b in enumerate(st.session_state.crop_batches):
                cname = CROP_DATA[b['type']]['name']
                cycle = CROP_DATA[b['type']]['cycle']
                status = "✅ 生长中" if b['health'] > 50 else "⚠️ 濒临枯死 (缺水/肥/CO2)"
                display_data.append({
                    "批次ID": f"#{i+1}",
                    "作物种类": cname,
                    "预期产量 (kg)": f"{b['amount']:.1f}",
                    "生长进度": f"第 {b['age']} 天 / 共 {cycle} 天",
                    "当前健康度": f"{b['health']:.1f} %",
                    "系统状态": status
                })
            df_crops = pd.DataFrame(display_data)
            st.table(df_crops)

    st.subheader("📊 实时生态与防御雷达")

    avg_m = cur['Mood']
    mood_status = "✅ 士气高昂" if avg_m > 70 else ("⚠️ 幽闭焦虑" if avg_m > 40 else "🚨 叛乱边缘")

    # CO2 告警逻辑
    co2_val = cur['CO2_percent']
    if co2_val > 0.5:
        co2_status = "⚠️ 毒性堆积"
    elif co2_val < 0.04:
        co2_status = "⚠️ 碳饥饿"
    else:
        co2_status = "✅ 正常"

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("氧气 O₂", f"{cur['O2_percent']:.2f} %", "✅ 正常" if cur['O2_percent'] > 19.5 else "⚠️ 濒临缺氧")
    c2.metric("二氧化碳 CO₂", f"{co2_val:.2f} %", co2_status, delta_color="normal" if co2_status == "✅ 正常" else "inverse")
    c3.metric("备用高压氧罐", f"{cur['O2_Tank']:.1f} kg")
    c4.metric("备用高压碳源", f"{cur['CO2_Tank']:.1f} kg")
    c5.metric("团队心理韧性 (均值)", f"{cur['Mood']:.1f} / 100", mood_status)

    # 🆕 v4 乘组个体心情/健康明细 — 三级警报 + 红线成员高亮
    def _tier_label(v):
        if v > 70:   return "✅ 良好"
        if v >= 40:  return "⚠️ 警戒"
        return "🚨 崩溃边缘"

    mood_danger = [c["name"] for c in st.session_state.crew_list if c["mood"] < 40]
    health_danger = [c["name"] for c in st.session_state.crew_list if c["health"] < 40]
    if mood_danger:
        st.error(f"🚨 心情崩溃边缘（mood<40）：{', '.join(mood_danger)}")
    if health_danger:
        st.error(f"🚨 健康崩溃边缘（health<40）：{', '.join(health_danger)} —— 让他们休息！")

    with st.expander("🧠 乘组个体心情 / 健康 / 职业 / 今日工作 明细", expanded=False):
        rows = []
        for c in st.session_state.crew_list:
            _pk = c.get("profession", PROFESSION_DEFAULT)
            _jk = c.get("job", JOB_DEFAULT)
            _match = PROFESSIONS.get(_pk, {}).get("specialty") == _jk
            rows.append({
                "姓名": c["name"],
                "职业": PROFESSIONS.get(_pk, {}).get("name", "?"),
                "心情": f"{c['mood']:.1f}", "心情状态": _tier_label(c["mood"]),
                "健康": f"{c['health']:.1f}", "健康状态": _tier_label(c["health"]),
                "今日工作": JOBS.get(_jk, {"name": "?"})["name"] + (" ✨×3" if _match else ""),
            })
        st.table(pd.DataFrame(rows))

    st.markdown("<br>", unsafe_allow_html=True)

    c6, c7, c8, c9 = st.columns(4)
    c6.metric("当前食物储备", f"{cur['Food']:.1f} kg")
    c7.metric("全基地可用肥料", f"{cur['Fertilizer']:.1f} kg")
    c8.metric("废水池蓄积", f"{cur['Waste_Water']:.1f} kg", f"容量上限 {cur_max_ww:.0f} kg", delta_color="off")
    c9.metric("物理固废堆积", f"{cur['Solid_Waste']:.1f} kg", f"容量上限 {cur_max_sw:.0f} kg", delta_color="off")

    # 🆕 v2 电力 / 科研 状态条
    st.markdown("---")
    st.subheader("⚡ 电力与 🔬 科研")
    bat = cur.get("Battery", 0.0)
    bat_cap = cur.get("Battery_Cap", st.session_state.state.get("Power_Battery_Cap_kWh", BATTERY_CAP_DEFAULT))
    net = cur.get("Power_Net", 0.0)
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("蓄电池余量", f"{bat:.1f} / {bat_cap:.0f} kWh",
              "⚠️ 见底" if bat < 1.0 else ("⚠️ 紧张" if bat < bat_cap * 0.2 else "✅ 充裕"),
              delta_color="inverse" if bat < bat_cap * 0.2 else "normal")
    p2.metric("昨日净电量", f"{net:+.1f} kWh", "盈余" if net >= 0 else "赤字",
              delta_color="normal" if net >= 0 else "inverse")
    p3.metric("光伏面积", f"{st.session_state.solar_panel_m2:.0f} m²")
    p4.metric("实验室 / 温室", f"{st.session_state.last_lab} / {st.session_state.last_greenhouse} 个")
    st.progress(max(0.0, min(1.0, bat / bat_cap)) if bat_cap > 0 else 0.0,
                text=f"🔋 电池 {bat:.1f} / {bat_cap:.0f} kWh")

    # 🆕 v3 净水流量(产量 vs 消耗,与现有 Clean_Water 存量并列)
    w_rec = cur.get("Water_Reclaimed", 0.0)
    w_con = cur.get("Water_Consumed", 0.0)
    w_net = cur.get("Water_Net", w_rec - w_con)
    w1, w2, w3, w4 = st.columns(4)
    w1.metric("💧 今日净水产量", f"{w_rec:.2f} kg",
              "来自微藻+作物+温室+Sabatier", delta_color="off")
    w2.metric("今日净水消耗", f"{w_con:.2f} kg",
              "生活用水+模块维护", delta_color="off")
    w3.metric("净水净流量", f"{w_net:+.2f} kg",
              "盈余" if w_net >= 0 else "亏空",
              delta_color="normal" if w_net >= 0 else "inverse")
    w4.metric("净水存量", f"{cur['Clean_Water']:.1f} kg")

    # 科研进度 + 已完成课题
    completed = st.session_state.state.get("completed_research", [])
    with st.expander(f"🔬 科研课题状态 (进行中 {sum(1 for p in st.session_state.lab_projects if p.get('project'))} · 已完成 {len(completed)})", expanded=False):
        if st.session_state.lab_projects:
            for idx, proj in enumerate(st.session_state.lab_projects):
                key = proj.get("project")
                if key and key in RESEARCH_LIBRARY:
                    spec = RESEARCH_LIBRARY[key]
                    pct = min(1.0, proj["progress"] / spec["cycle"])
                    _names = [st.session_state.crew_list[ci]["name"]
                              for ci in proj.get("assigned_crew", [])
                              if 0 <= ci < len(st.session_state.crew_list)]
                    _team = "、".join(_names) if _names else "无人在岗"
                    st.progress(pct, text=f"实验室 #{idx + 1} · {spec['name']} · {proj['progress']:.1f}/{spec['cycle']} 天 · {_team}")
                else:
                    st.caption(f"实验室 #{idx + 1} · 空闲")
        if completed:
            st.markdown("**🏆 已完成课题：**")
            st.markdown("  \n".join(f"- {RESEARCH_LIBRARY[k]['name']}" for k in completed if k in RESEARCH_LIBRARY))

    # 🆕 突发事件日志
    if st.session_state.event_log:
        with st.expander("📜 突发事件日志 (最近 10 条)", expanded=True):
            for e in reversed(st.session_state.event_log[-10:]):
                st.markdown(f"**第 {e['day']} 天 — {e['name']}**  \n　{e['desc']}")

    st.markdown("---")

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(20, 5))
    days_axis = st.session_state.history["Day"]

    ax1.plot(days_axis, st.session_state.history["O2_percent"], label="O2 (%)", color='#2ca02c', lw=2.5)
    ax1.plot(days_axis, st.session_state.history["CO2_percent"], label="CO2 (%)", color='#d62728', lw=2)
    ax1.axhline(18, color='darkgreen', linestyle=':', label='缺氧线(18%)')
    ax1.axhline(3, color='darkred', linestyle=':', label='CO2毒性线(3%)')
    ax1.set_title("生命保障系统：大气动力学")
    ax1.legend()

    ax2.plot(days_axis, st.session_state.history["Waste_Water"], label="当前废水(kg)", color='brown')
    ax2.plot(days_axis, st.session_state.history["Max_WW"], label="动态废水上限", color='brown', linestyle=':', alpha=0.5)
    ax2.plot(days_axis, st.session_state.history["Solid_Waste"], label="当前固废(kg)", color='orange')
    ax2.plot(days_axis, st.session_state.history["Max_SW"], label="动态固废上限", color='orange', linestyle=':', alpha=0.5)
    ax2.plot(days_axis, st.session_state.history["Mood"], label="平均心情", color='purple', lw=2)
    if "Health" in st.session_state.history.columns:                            # 🆕 v4
        ax2.plot(days_axis, st.session_state.history["Health"].fillna(100.0),
                 label="平均健康", color='deeppink', lw=2, linestyle='--')
    # 🆕 v3 净水流量(右轴,kg/天) — 与左轴的存量/容量区分
    if "Water_Reclaimed" in st.session_state.history.columns:
        ax2_r = ax2.twinx()
        ax2_r.plot(days_axis, st.session_state.history["Water_Reclaimed"].fillna(0),
                   label="净水产量(kg/天)", color='dodgerblue', lw=1.8)
        ax2_r.plot(days_axis, st.session_state.history["Water_Consumed"].fillna(0),
                   label="净水消耗(kg/天)", color='dodgerblue', lw=1.5, linestyle='--', alpha=0.7)
        ax2_r.set_ylabel("净水流量 kg/天", color='dodgerblue')
        ax2_r.tick_params(axis='y', labelcolor='dodgerblue')
        ax2_r.legend(loc='upper right')
    ax2.set_title("污染控制 · 心理学 · 净水流量")
    ax2.legend(loc='upper left')

    ax3.plot(days_axis, st.session_state.history["Food"], label="粮食储备(kg)", color='gold', linestyle='-')
    ax3.plot(days_axis, st.session_state.history["Regolith_Shield"], label="生物护甲(m²)", color='silver', lw=2.5)
    ax3.plot(days_axis, st.session_state.history["Hull"], label="壳体完整性σ", color='black', lw=2)   # 🆕
    ax3.plot(days_axis, st.session_state.history["O2_Tank"], label="备用氧气罐(kg)", color='teal', linestyle=':')
    ax3.plot(days_axis, st.session_state.history["CO2_Tank"], label="高压碳源罐(kg)", color='grey', linestyle='-.')
    ax3.set_title("战略物资与外壳防御演进")
    ax3.legend()

    st.pyplot(fig)