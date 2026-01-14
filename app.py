import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.features import DivIcon
from datetime import datetime
from io import BytesIO

# ===============================
# НАЛАШТУВАННЯ
# ===============================
st.set_page_config(
    page_title="Карта хімічної та радіаційної обстановки",
    layout="wide"
)

# ===============================
# СТАН
# ===============================
if "data" not in st.session_state:
    st.session_state.data = []

# ===============================
# ЗАГОЛОВОК
# ===============================
st.title("🗺️ Карта хімічної та радіаційної обстановки")

# ===============================
# ІНСТРУКЦІЯ
# ===============================
with st.sidebar.expander("📘 Інструкція користування"):
    st.markdown("""
**Призначення програми**  
Програма призначена для нанесення на карту:
- хімічної обстановки (мг/куб.м)
- радіаційної обстановки (мЗв/год)

**Вхідні дані**
- координати точки вимірювання концентрації небезпечної хімічної речовини (бойової отруйної речовини) або потужності дози опромінення
- значення концентрації НХР (БОР) або потужності дози опромінення
- час вимірювання
- назва небезпечної хімічної речовини (бойової отруйної речовини) 

**Способи введення даних**
1. Вручну через графічний інтерфейс
2. Через CSV-файли:
   - `chemical.data.csv`
   - `radiation.data.csv`

**Вихідні дані**
- карта з точками вимірювання
- кольорове розділення:
  - ☣️ НХР (БОР) — **синій**
  - ☢️ потужність дози  — **бордовий**
- підпис біля кожної точки
- можливість збереження карти у HTML
""")

# ===============================
# БОКОВА ПАНЕЛЬ — ВРУЧНУ
# ===============================
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
    st.session_state.data.append({
        "lat": lat,
        "lon": lon,
        "value": round(value, 2),
        "time": time,
        "substance": substance,
        "unit": unit,
        "color": color
    })

# ===============================
# CSV ЗАВАНТАЖЕННЯ
# ===============================
st.sidebar.header("📂 Завантаження CSV")

rad_file = st.sidebar.file_uploader(
    "☢️ radiation.data.csv",
    type="csv"
)

chem_file = st.sidebar.file_uploader(
    "☣️ chemical.data.csv",
    type="csv"
)

if st.sidebar.button("📥 Завантажити CSV"):
    if rad_file:
        df = pd.read_csv(rad_file)
        for _, r in df.iterrows():
            st.session_state.data.append({
                "lat": r.lat,
                "lon": r.lon,
                "value": round(r.dose, 2),
                "time": r.time,
                "substance": "Радіація",
                "unit": "мЗв/год",
                "color": "darkred"
            })

    if chem_file:
        df = pd.read_csv(chem_file)
        for _, r in df.iterrows():
            st.session_state.data.append({
                "lat": r.lat,
                "lon": r.lon,
                "value": round(r.concentration, 2),
                "time": r.time,
                "substance": r.substance,
                "unit": "мг/куб.м",
                "color": "blue"
            })

# ===============================
# ОЧИСТКА
# ===============================
if st.sidebar.button("🧹 Очистити всі дані"):
    st.session_state.data.clear()

# ===============================
# КАРТА
# ===============================
if st.session_state.data:
    df = pd.DataFrame(st.session_state.data)

    m = folium.Map(
        location=[df.lat.mean(), df.lon.mean()],
        zoom_start=12,
        control_scale=True
    )

    for _, r in df.iterrows():
        folium.CircleMarker(
            location=[r.lat, r.lon],
            radius=7,
            color=r.color,
            fill=True,
            fill_color=r.color,
            fill_opacity=0.9
        ).add_to(m)

        folium.Marker(
            [r.lat, r.lon],
            icon=DivIcon(html=f"""
            <div style="
                color:{r.color};
                font-weight:bold;
                background:transparent;
                white-space:nowrap">
            {r.substance} – {r.value:.2f} {r.unit}<br>
            {r.time}
            </div>
            """)
        ).add_to(m)

    # ВІДОБРАЖЕННЯ НА ВСЮ ШИРИНУ
    st_folium(m, height=650, width=None)

    # ===============================
    # ЕКСПОРТ HTML
    # ===============================
    html_data = m.get_root().render()
    st.download_button(
        "💾 Зберегти карту у HTML",
        data=html_data,
        file_name="chemical_radiation_map.html",
        mime="text/html"
    )

else:
    st.info("Дані для відображення відсутні")

