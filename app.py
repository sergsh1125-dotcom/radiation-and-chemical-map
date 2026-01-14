import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from branca.element import DivIcon
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
col1, col2, col3 = st.columns(3)

with col1:
    rad_file = st.file_uploader(
        "☢ Завантажити radiation.data.csv",
        type="csv",
        key="rad"
    )

with col2:
    chem_file = st.file_uploader(
        "🧪 Завантажити chemical.data.csv",
        type="csv",
        key="chem"
    )

with col3:
    if st.button("🧹 Очистити всі дані"):
        st.session_state.radiation = pd.DataFrame()
        st.session_state.chemical = pd.DataFrame()
        st.experimental_rerun()

# =========================
# Завантаження CSV
# =========================
if rad_file:
    df = pd.read_csv(rad_file)
    required = {"lat", "lon", "value", "time"}
    if required.issubset(df.columns):
        st.session_state.radiation = df
    else:
        st.error("❌ radiation.data.csv має неправильні колонки")

if chem_file:
    df = pd.read_csv(chem_file)
    required = {"lat", "lon", "value", "time", "substance"}
    if required.issubset(df.columns):
        st.session_state.chemical = df
    else:
        st.error("❌ chemical.data.csv має неправильні колонки")

# =========================
# Ручне введення точок
# =========================
st.sidebar.header("➕ Додати точку вручну")
mode = st.sidebar.radio("Тип обстановки", ["Радіаційна", "Хімічна"])

lat = st.sidebar.number_input("Широта", format="%.6f")
lon = st.sidebar.number_input("Довгота", format="%.6f")

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

time = st.sidebar.text_input(
    "Час вимірювання",
    datetime.now().strftime("%Y-%m-%d %H:%M")
)

if st.sidebar.button("➕ Додати точку"):
    new_row = pd.DataFrame([{
        "lat": lat,
        "lon": lon,
        "value": round(value,2),
        "time": time,
        "substance": substance,
        "unit": unit,
        "color": color
    }])
    if mode == "Радіаційна":
        st.session_state.radiation = pd.concat([st.session_state.radiation, new_row], ignore_index=True)
    else:
        st.session_state.chemical = pd.concat([st.session_state.chemical, new_row], ignore_index=True)

# =========================
# Побудова карти
# =========================
m = folium.Map(location=[50.45, 30.52], zoom_start=12, tiles="OpenStreetMap")

# 🎯 FeatureGroup для шарів
fg_rad = folium.FeatureGroup(name="Радіаційна обстановка")
fg_chem = folium.FeatureGroup(name="Хімічна обстановка")

# Радіація (бордовий)
for _, r in st.session_state.radiation.iterrows():
    text = f"<b>Радіація</b><br>{r.value:.2f} мЗв/год<br><i>{r.time}</i>"
    folium.CircleMarker(
        location=[r.lat, r.lon],
        radius=7,
        color="darkred",
        fill=True,
        fill_color="darkred",
        fill_opacity=0.9
    ).add_to(fg_rad)
    folium.Marker(
        [r.lat, r.lon],
        icon=DivIcon(
            icon_size=(200,50),
            icon_anchor=(0,0),
            html=f'<div style="color:darkred;font-weight:bold;background:transparent">{text}</div>'
        )
    ).add_to(fg_rad)

# Хімія (синій)
for _, r in st.session_state.chemical.iterrows():
    text = f"<b>{r.substance}</b><br>{r.value:.2f} мг/куб.м<br><i>{r.time}</i>"
    folium.CircleMarker(
        location=[r.lat, r.lon],
        radius=7,
        color="blue",
        fill=True,
        fill_color="blue",
        fill_opacity=0.9
    ).add_to(fg_chem)
    folium.Marker(
        [r.lat, r.lon],
        icon=DivIcon(
            icon_size=(220,50),
            icon_anchor=(0,0),
            html=f'<div style="color:blue;font-weight:bold;background:transparent">{text}</div>'
        )
    ).add_to(fg_chem)

# Додаємо шари на карту
fg_rad.add_to(m)
fg_chem.add_to(m)

# Layer Control для включення/вимкнення
folium.LayerControl(collapsed=False).add_to(m)

# =========================
# Відображення карти
# =========================
st_folium(m, width=1400, height=650)

# =========================
# Збереження HTML
# =========================
if st.button("💾 Зберегти карту у HTML"):
    m.save("situation_map.html")
    st.success("✅ Файл situation_map.html створено")

