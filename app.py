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
# Ініціалізація session_state
# =========================
for key in ["radiation","chemical","map_object"]:
    if key not in st.session_state:
        if key=="map_object":
            st.session_state[key]=None
        else:
            st.session_state[key]=pd.DataFrame()

# =========================
# Інструкція користування
# =========================
with st.expander("📘 Інструкція користування"):
    st.markdown("""
**Призначення:**  
Візуалізація радіаційної та хімічної обстановки на карті.

**Вхідні дані:**  
- CSV-файли:
    - `radiation.data.csv` (lat, lon, value, time)
    - `chemical.data.csv` (lat, lon, value, time, substance)
- Або введення точок вручну через бічну панель.

**Вихідні дані:**  
- Точки на карті з підписами
- Бордові точки — радіація, сині — хімія
- Можливість збереження карти у HTML
""")

# =========================
# Сайдбар для завантаження CSV та ручного введення
# =========================
st.sidebar.header("📁 Завантаження CSV")
rad_file = st.sidebar.file_uploader("☢ radiation.data.csv", type="csv", key="rad")
chem_file = st.sidebar.file_uploader("🧪 chemical.data.csv", type="csv", key="chem")

st.sidebar.header("➕ Додати точку вручну")
mode = st.sidebar.radio("Тип обстановки", ["Радіаційна","Хімічна"])
lat = st.sidebar.number_input("Широта", format="%.6f")
lon = st.sidebar.number_input("Довгота", format="%.6f")
time = st.sidebar.text_input("Час вимірювання", datetime.now().strftime("%Y-%m-%d %H:%M"))
if mode=="Радіаційна":
    value = st.sidebar.number_input("Потужність дози (мЗв/год)", format="%.4f")
    color = "darkred"
    unit = "мЗв/год"
    substance = "Радіація"
else:
    substance = st.sidebar.text_input("Назва речовини", "Хлор")
    value = st.sidebar.number_input("Концентрація (мг/куб.м)", format="%.4f")
    color = "blue"
    unit = "мг/куб.м"

if st.sidebar.button("➕ Додати точку"):
    new_row = pd.DataFrame([{
        "lat": lat, "lon": lon, "value": round(value,2),
        "time": time, "substance": substance, "unit": unit, "color": color
    }])
    if mode=="Радіаційна":
        st.session_state.radiation = pd.concat([st.session_state.radiation, new_row], ignore_index=True)
    else:
        st.session_state.chemical = pd.concat([st.session_state.chemical, new_row], ignore_index=True)

if st.sidebar.button("🧹 Очистити всі дані"):
    st.session_state.radiation = pd.DataFrame()
    st.session_state.chemical = pd.DataFrame()
    st.session_state.map_object = None

# =========================
# Функція додавання точок на карту
# =========================
def add_points(df, m, is_rad=True):
    for _, r in df.iterrows():
        text = f"<b>{'Радіація' if is_rad else r.substance}</b><br>{r.value:.2f} {r.unit}<br><i>{r.time}</i>"
        color = "darkred" if is_rad else r.color
        folium.CircleMarker(
            location=[r.lat, r.lon], radius=7, color=color,
            fill=True, fill_color=color, fill_opacity=0.9
        ).add_to(m)
        folium.Marker(
            [r.lat,r.lon],
            icon=DivIcon(icon_size=(220,50), icon_anchor=(0,0),
                         html=f'<div style="color:{color};font-weight:bold;background:transparent">{text}</div>')
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
        if {"lat","lon","value","time"}.issubset(df.columns):
            st.session_state.radiation = df
        else:
            st.error("radiation.data.csv має невірні колонки")
    if chem_file:
        df = pd.read_csv(chem_file)
        if {"lat","lon","value","time","substance"}.issubset(df.columns):
            st.session_state.chemical = df
        else:
            st.error("chemical.data.csv має невірні колонки")

    # Генеруємо карту лише один раз
    all_points = pd.concat([st.session_state.radiation, st.session_state.chemical], ignore_index=True)
    if not all_points.empty:
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
# Кнопка збереження HTML
# =========================
if st.button("💾 Зберегти карту у HTML"):
    if st.session_state.map_object:
        st.session_state.map_object.save("situation_map.html")
        st.success("✅ Файл situation_map.html створено")
    else:
        st.warning("⚠ Спершу натисніть 'Оновити карту'")

