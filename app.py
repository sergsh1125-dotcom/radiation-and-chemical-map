import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.features import DivIcon
from datetime import datetime

# ===============================
# Налаштування сторінки
# ===============================
st.set_page_config(
    page_title="Карта радіаційної та хімічної обстановки",
    layout="wide"
)

# Приховуємо меню та футер
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ===============================
# Стан програми
# ===============================
for key in ["radiation","chemical","substance","map_object"]:
    if key not in st.session_state:
        if key=="map_object":
            st.session_state[key]=None
        elif key=="substance":
            st.session_state[key]="Хлор"
        else:
            st.session_state[key]=pd.DataFrame(columns=["lat","lon","value","time","substance"])

# ===============================
# Заголовок та інструкція
# ===============================
st.title("🗺️ Карта радіаційної та хімічної обстановки")

if st.button("ℹ️ Інструкція користування", use_container_width=True):
    st.info("""
**Призначення:**  
Візуалізація радіаційної та хімічної обстановки на карті.

**Вхідні дані:**  
- CSV-файли:
    - `radiation.data.csv` (lat, lon, value, time)
    - `chemical.data.csv` (lat, lon, value, time, substance)
- Або введення точок вручну.

**Вихідні дані:**  
- Бордові точки — радіація, сині — хімія  
- Підписи: назва речовини/потужність дози – дата/час вимірювання  
- HTML-файл карти для завантаження
""")

# ===============================
# Розділення екрану
# ===============================
col_map, col_gui = st.columns([2.2,1])

# ===============================
# GUI: права панель
# ===============================
with col_gui:
    st.subheader("⚙️ Ввід даних")

    st.session_state.substance = st.text_input(
        "Назва небезпечної речовини", st.session_state.substance
    )

    st.markdown("### ➕ Додати точку вручну")
    mode = st.radio("Тип обстановки", ["Радіаційна","Хімічна"])
    lat = st.number_input("Широта (lat)", format="%.6f")
    lon = st.number_input("Довгота (lon)", format="%.6f")
    value = st.number_input("Значення", min_value=0.0, step=0.01)
    time = st.text_input("Час вимірювання", datetime.now().strftime("%Y-%m-%d %H:%M"))

    if st.button("➕ Додати точку", use_container_width=True):
        new_row = pd.DataFrame([{
            "lat": lat, "lon": lon, "value": round(value,2),
            "time": time, "substance": "Радіація" if mode=="Радіаційна" else st.session_state.substance
        }])
        if mode=="Радіаційна":
            st.session_state.radiation = pd.concat([st.session_state.radiation, new_row], ignore_index=True)
        else:
            st.session_state.chemical = pd.concat([st.session_state.chemical, new_row], ignore_index=True)

    st.divider()
    rad_file = st.file_uploader("☢ Завантажити radiation.data.csv", type="csv")
    chem_file = st.file_uploader("🧪 Завантажити chemical.data.csv", type="csv")

    if rad_file:
        df = pd.read_csv(rad_file)
        st.session_state.radiation = df
        st.success(f"Завантажено {len(df)} точок радіації")
    if chem_file:
        df = pd.read_csv(chem_file)
        st.session_state.chemical = df
        st.success(f"Завантажено {len(df)} точок хімії")

    if st.button("🧹 Очистити всі дані", use_container_width=True):
        st.session_state.radiation = pd.DataFrame(columns=["lat","lon","value","time","substance"])
        st.session_state.chemical = pd.DataFrame(columns=["lat","lon","value","time","substance"])
        st.session_state.map_object = None

# ===============================
# Функція для нанесення точок
# ===============================
def add_points(df, m, color):
    for _, r in df.iterrows():
        text_html = f"""
        <div style="
            color:{color};
            font-size:14px;
            font-weight:bold;
            white-space: nowrap;
            background:transparent;
        ">
            {r.substance} – {r.value:.2f}<br>
            <hr style="margin:2px 0;border:1px solid {color};">
            {r.time}
        </div>
        """
        folium.CircleMarker(
            [r.lat,r.lon], radius=7, color=color,
            fill=True, fill_color=color, fill_opacity=0.9
        ).add_to(m)
        folium.Marker([r.lat,r.lon], icon=DivIcon(icon_anchor=(0,-12), html=text_html)).add_to(m)

# ===============================
# Кнопка оновлення карти
# ===============================
if st.button("🔄 Оновити карту"):
    all_points = pd.concat([st.session_state.radiation, st.session_state.chemical], ignore_index=True)
    if not all_points.empty:
        center_lat = all_points.lat.mean()
        center_lon = all_points.lon.mean()
        m = folium.Map(location=[center_lat, center_lon], zoom_start=13)
        if not st.session_state.radiation.empty:
            add_points(st.session_state.radiation, m, "darkred")
        if not st.session_state.chemical.empty:
            add_points(st.session_state.chemical, m, "blue")
        folium.LayerControl(collapsed=False).add_to(m)
        st.session_state.map_object = m

# ===============================
# Відображення карти
# ===============================
with col_map:
    if st.session_state.map_object:
        st.markdown("<style>iframe {width:100% !important;}</style>", unsafe_allow_html=True)
        st_folium(st.session_state.map_object, width=0, height=600)

        # HTML експорт
        st.session_state.map_object.save("situation_map.html")
        with open("situation_map.html","rb") as f:
            st.download_button("💾 Завантажити карту (HTML)", f,
                               file_name="situation_map.html",
                               mime="text/html", use_container_width=True)
    else:
        st.info("Немає даних для відображення карти")

