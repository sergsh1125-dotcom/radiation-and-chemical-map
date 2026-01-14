import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.features import DivIcon
from datetime import datetime

# =========================
# Налаштування сторінки
# =========================
st.set_page_config(
    page_title="Карта радіаційної та хімічної обстановки",
    layout="wide"
)
st.title("🗺️ Карта радіаційної та хімічної обстановки")

# =========================
# Session State
# =========================
if "radiation" not in st.session_state:
    st.session_state.radiation = pd.DataFrame()
if "chemical" not in st.session_state:
    st.session_state.chemical = pd.DataFrame()
if "map_object" not in st.session_state:
    st.session_state.map_object = None
if "map_data_version" not in st.session_state:
    st.session_state.map_data_version = 0

# =========================
# Інструкція
# =========================
with st.expander("📘 Інструкція користування"):
    st.markdown("""
**Призначення програми**  
Візуалізація радіаційної та хімічної обстановки на карті.

### Вхідні дані
- Завантаження CSV-файлів:
  - `radiation.data.csv` (колонки: lat, lon, value, time)
  - `chemical.data.csv` (колонки: lat, lon, value, time, substance)

### Вихідні дані
- Точки вимірювань на карті
- Підписи біля точок
- Можливість збереження карти у HTML

### Способи введення даних
1. Вручну через бокову панель
2. Через CSV-файли
""")

# =========================
# Кнопки керування
# =========================
col1, col2, col3 = st.columns([3,3,2])
with col1:
    rad_file = st.file_uploader("☢ Завантажити radiation.data.csv", type="csv", key="rad")
with col2:
    chem_file = st.file_uploader("🧪 Завантажити chemical.data.csv", type="csv", key="chem")
with col3:
    if st.button("🧹 Очистити всі дані"):
        st.session_state.radiation = pd.DataFrame()
        st.session_state.chemical = pd.DataFrame()
        st.session_state.map_object = None
        st.session_state.map_data_version += 1

# =========================
# Завантаження CSV
# =========================
def load_csv(file, required_cols):
    if file:
        df = pd.read_csv(file)
        if required_cols.issubset(df.columns):
            return df
        else:
            st.error(f"❌ {file.name} має неправильні колонки")
    return pd.DataFrame()

rad_df = load_csv(rad_file, {"lat", "lon", "value", "time"})
if not rad_df.empty:
    st.session_state.radiation = rad_df
    st.session_state.map_data_version += 1

chem_df = load_csv(chem_file, {"lat", "lon", "value", "time", "substance"})
if not chem_df.empty:
    st.session_state.chemical = chem_df
    st.session_state.map_data_version += 1

# =========================
# Ручне введення точок
# =========================
st.sidebar.header("➕ Додати точку вручну")
mode = st.sidebar.radio("Тип обстановки", ["Радіаційна", "Хімічна"])

lat = st.sidebar.number_input("Широта", format="%.6f")
lon = st.sidebar.number_input("Довгота", format="%.6f")
time = st.sidebar.text_input("Час вимірювання", datetime.now().strftime("%Y-%m-%d %H:%M"))

if mode == "Радіаційна":
    value = st.sidebar.number_input("Потужність дози (мЗв/год)", format="%.4f")
    substance = "Радіація"
    unit = "мЗв/год"
    color = "darkred"
else:
    substance = st.sidebar.text_input("Назва речовини", "Хлор")
    value = st.sidebar.number_input("Концентрація (мг/куб.м)", format="%.4f")
    unit = "мг/куб.м"
    color = "blue"

if st.sidebar.button("➕ Додати точку"):
    new_row = pd.DataFrame([{
        "lat": lat, "lon": lon, "value": round(value,2),
        "time": time, "substance": substance, "unit": unit, "color": color
    }])
    if mode == "Радіаційна":
        st.session_state.radiation = pd.concat([st.session_state.radiation, new_row], ignore_index=True)
    else:
        st.session_state.chemical = pd.concat([st.session_state.chemical, new_row], ignore_index=True)
    st.session_state.map_data_version += 1

# =========================
# Чекбокси для шарів
# =========================
st.sidebar.header("🗂 Шари на карті")
show_rad = st.sidebar.checkbox("Радіаційна обстановка", value=True)
show_chem = st.sidebar.checkbox("Хімічна обстановка", value=True)

# =========================
# Функція додавання точок на карту
# =========================
def add_points(df, m, is_rad=True):
    for _, r in df.iterrows():
        if is_rad:
            color = "darkred"
            unit = "мЗв/год"
            name = "Радіація"
        else:
            color = r.color
            unit = r.unit
            name = r.substance
        text = f"<b>{name}</b><br>{r.value:.2f} {unit}<br><i>{r.time}</i>"
        folium.CircleMarker(
            location=[r.lat, r.lon], radius=7, color=color,
            fill=True, fill_color=color, fill_opacity=0.9
        ).add_to(m)
        folium.Marker(
            [r.lat, r.lon],
            icon=DivIcon(
                icon_size=(220,50), icon_anchor=(0,0),
                html=f'<div style="color:{color};font-weight:bold;background:transparent">{text}</div>'
            )
        ).add_to(m)

# =========================
# Кнопка для оновлення карти
# =========================
if st.button("🔄 Оновити карту"):
    m = folium.Map(location=[50.45, 30.52], zoom_start=12, tiles="OpenStreetMap")
    if show_rad and not st.session_state.radiation.empty:
        add_points(st.session_state.radiation, m, is_rad=True)
    if show_chem and not st.session_state.chemical.empty:
        add_points(st.session_state.chemical, m, is_rad=False)
    folium.LayerControl(collapsed=False).add_to(m)
    st.session_state.map_object = m

# =========================
# Відображення карти
# =========================
if st.session_state.map_object:
    st.markdown("<style>iframe {width:100% !important;}</style>", unsafe_allow_html=True)
    st_folium(st.session_state.map_object, width=0, height=650)

# =========================
# Збереження HTML
# =========================
if st.button("💾 Зберегти карту у HTML"):
    if st.session_state.map_object:
        st.session_state.map_object.save("situation_map.html")
        st.success("✅ Файл situation_map.html створено")
    else:
        st.warning("⚠ Спершу натисніть 'Оновити карту'")

