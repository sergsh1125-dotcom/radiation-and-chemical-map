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

# =========================
# Інструкція
# =========================
with st.expander("📘 Інструкція користування"):
    st.markdown("""
**Призначення програми:**  
Візуалізація радіаційної та хімічної обстановки на карті.

### Вхідні дані
- CSV-файли:
  - `radiation.data.csv` (колонки: lat, lon, value, time)
  - `chemical.data.csv` (колонки: lat, lon, value, time, substance)

### Вихідні дані
- Точки вимірювань на карті
- Підписи біля точок
- Збереження карти у HTML

### Способи введення даних
1. Вручну через бокову панель
2. Через CSV-файли
""")

# =========================
# Завантаження CSV
# =========================
st.sidebar.header("📁 Завантаження CSV")
rad_file = st.sidebar.file_uploader("☢ radiation.data.csv", type="csv", key="rad")
chem_file = st.sidebar.file_uploader("🧪 chemical.data.csv", type="csv", key="chem")

if st.sidebar.button("🧹 Очистити всі дані"):
    st.session_state.radiation = pd.DataFrame()
    st.session_state.chemical = pd.DataFrame()
    st.session_state.map_object = None

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
            color = r.color if "color" in df.columns else "blue"
            unit = r.unit if "unit" in df.columns else "мг/куб.м"
            name = r.substance if "substance" in df.columns else "Хімія"

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
# Чекбокси для шарів
# =========================
st.sidebar.header("🗂 Шари на карті")
show_rad = st.sidebar.checkbox("Радіаційна обстановка", value=True)
show_chem = st.sidebar.checkbox("Хімічна обстановка", value=True)

# =========================
# Кнопка оновлення карти
# =========================
if st.button("🔄 Оновити карту"):
    # Завантажуємо CSV у session_state
    if rad_file:
        df = pd.read_csv(rad_file)
        required = {"lat","lon","value","time"}
        if required.issubset(df.columns):
            st.session_state.radiation = df
        else:
            st.error("radiation.data.csv має невірні колонки")
    if chem_file:
        df = pd.read_csv(chem_file)
        required = {"lat","lon","value","time","substance"}
        if required.issubset(df.columns):
            st.session_state.chemical = df
        else:
            st.error("chemical.data.csv має невірні колонки")

    if st.session_state.radiation.empty and st.session_state.chemical.empty:
        st.warning("⚠ Спершу завантажте дані або додайте точки вручну")
    else:
        all_points = pd.concat([st.session_state.radiation, st.session_state.chemical], ignore_index=True)
        center_lat = all_points.lat.mean()
        center_lon = all_points.lon.mean()
        m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

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

