import streamlit as st
import math
from datetime import datetime

st.set_page_config(page_title="ElectroAI", page_icon="⚡", layout="wide")

st.markdown("""
<style>
    .main {background: linear-gradient(135deg, #0f172a 0%, #1e2937 100%);}
    h1 {color: #60a5fa; text-align: center; font-size: 3.2rem;}
    .subtitle {text-align: center; color: #94a3b8; font-size: 1.4rem;}
    .stButton>button {background: linear-gradient(90deg, #3b82f6, #60a5fa); color: white; font-weight: bold; border-radius: 12px;}
</style>
""", unsafe_allow_html=True)

# ====================== ДАННЫЕ ======================
standards = {
    "ПУЭ (Россия/СНГ)": "pue",
    "IEC (Европа)": "iec",
    "NEC (США)": "nec"
}

TABLES = {
    "pue": {1.5: 19, 2.5: 27, 4: 38, 6: 46, 10: 70, 16: 85, 25: 115, 35: 135, 50: 175, 70: 215, 95: 260},
    "iec": {1.5: 23, 2.5: 31, 4: 42, 6: 54, 10: 73, 16: 95, 25: 125, 35: 151, 50: 182},
    "nec": {1.5: 20, 2.5: 27, 4: 36, 6: 48, 10: 66, 16: 88, 25: 115, 35: 145, 50: 175}
}

BREAKERS = [6, 10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250]

# ====================== ФУНКЦИИ ======================
def calculate_current(power_kw, voltage=220, phases=1):
    cos_phi = 0.95
    if phases == 1:
        return (power_kw * 1000) / (voltage * cos_phi)
    return (power_kw * 1000) / (math.sqrt(3) * voltage * cos_phi)

def select_breaker(current, standard):
    multiplier = 1.25 if standard == "nec" else 1.1
    for b in BREAKERS:
        if b >= current * multiplier:
            return b
    return "Слишком большая нагрузка"

def recommend_section(current, standard, material="Cu"):
    table = TABLES.get(standard, TABLES["pue"])
    for sec, max_i in sorted(table.items()):
        if max_i >= current:
            return sec
    return "Требуется специалист"

def calculate_voltage_drop(current, length, section, voltage=220, phases=1, material="Cu"):
    rho = 0.018 if material == "Cu" else 0.029
    if phases == 1:
        drop_v = (2 * current * rho * length) / section
    else:
        drop_v = (math.sqrt(3) * current * rho * length) / section
    percent = (drop_v / voltage) * 100
    return round(drop_v, 2), round(percent, 2)

# ====================== МОДУЛЬ ЗАЩИТЫ ======================
def recommend_protection(current, load_type, is_wet=False, is_critical=False):
    rec = {}
    if is_critical:
        rec["УЗО"] = "10 мА, тип A — обязательно"
    elif is_wet:
        rec["УЗО"] = "10 мА, тип A (рекомендуется)"
    elif current > 40:
        rec["УЗО"] = "30 мА (основное) + 100/300 мА (противопожарное)"
    else:
        rec["УЗО"] = "30 мА, тип A"
    
    rec["Дифавтомат"] = f"{rec['УЗО']}, номинал {int(current*1.25)} А"
    rec["Реле напряжения"] = "Обязательно на вводе (УЗМ, Zubr, РН-260 и т.д.)"
    
    if current > 10:
        rec["Реле контроля фаз"] = "Рекомендуется"
    
    return rec

# ====================== ИНТЕРФЕЙС ======================
tab1, tab2, tab3 = st.tabs(["⚡ Калькулятор", "🛡️ Защитные устройства и реле", "💬 ИИ Помощник"])

with tab1:
    st.title("⚡ ElectroAI")
    st.markdown("**Мультистандартный расчёт электрики**")
    
    with st.sidebar:
        st.header("Параметры")
        standard_name = st.selectbox("Стандарт", list(standards.keys()))
        standard = standards[standard_name]
        power = st.number_input("Мощность (кВт)", min_value=0.1, value=5.0, step=0.1)
        voltage = st.selectbox("Напряжение (В)", [220, 230, 380, 400, 120, 240])
        phases = st.selectbox("Фазы", [1, 3])
        material = st.selectbox("Материал", ["Медь (Cu)", "Алюминий (Al)"])
        length = st.number_input("Длина линии (м)", min_value=0.0, value=25.0, step=1.0)

    if st.button("🔍 Рассчитать", type="primary", use_container_width=True):
        mat_short = "Cu" if "Медь" in material else "Al"
        current = calculate_current(power, voltage, phases)
        breaker = select_breaker(current, standard)
        section = recommend_section(current, standard, mat_short)
        
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Ток", f"{current:.2f} А")
        with col2: st.metric("Автомат", f"{breaker} А")
        with col3: st.metric("Сечение", f"{section} мм²")

with tab2:
    st.title("🛡️ Защитные устройства и реле")
    st.markdown("**Продвинутый подбор УЗО, дифавтоматов и защиты**")
    
    col1, col2 = st.columns(2)
    with col1:
        current = st.number_input("Ток нагрузки (А)", min_value=1, value=16, step=1)
        load_type = st.selectbox("Тип нагрузки", ["Розеточная группа", "Кухонная техника", "Электроплита", "Освещение", "Насос / двигатель", "Сауна / бассейн"])
        is_wet = st.checkbox("Влажное помещение", value=False)
        is_critical = st.checkbox("Особо опасное помещение", value=False)
    
    with col2:
        standard_name = st.selectbox("Стандарт", list(standards.keys()), key="protect_std")
    
    if st.button("🔍 Подобрать защиту", type="primary", use_container_width=True):
        protection = recommend_protection(current, load_type, is_wet, is_critical)
        st.success("### Рекомендации по защите")
        for key, value in protection.items():
            st.info(f"**{key}**: {value}")

with tab3:
    st.title("💬 ИИ Помощник")
    st.info("ИИ-чат в разработке. Скоро будет значительно умнее.")

st.caption("ElectroAI v2.4 — Модуль УЗО восстановлен")