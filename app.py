import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.features import DivIcon
from datetime import datetime

# ===============================
# НАЛАШТУВАННЯ СТОРІНКИ
# ===============================
st.set_page_config(
    page_title="Карта хімічної та радіаційної обстановки",
    layout="wide"
)

# ===============================
# СТАН ДОДАТКУ
# ===============================
if "data" not in st.session_state:
    st.session_state.data = []

# ===============================
# ЗАГОЛОВОК
# ===============================
st.title("🗺️ Карта хімічної та радіаційної обстановки")

st.markdown("""
Веб-застосунок для нанесення на карту:

- ☢️ **радіаційної обстановки** (мЗв/год)
- ☣️ **хімічної обстановки** (мг/куб.м)

Дані вводяться **вручну** або **через CSV**, результат можна **зберегти у HTML**.
""")

# ===============================
# БОКОВА ПАНЕЛЬ — ДОДАВАННЯ ТОЧКИ
# ===============================
st.sidebar.header("➕ Додати точку вимірювання")

mode = st.sidebar.radio(
    "Тип обстановки",
    ["Радіаційна", "Хімічна"]
)

lat = st.sidebar.number_input("Широта (lat)", format="%.6f")
lon = st.sidebar.number_input("Довгота (lon)", format="%.6f")

if mode == "Радіаційна":
    substance = "Радіація"
    value = st.sidebar.number_input(
        "Потужність дози (мЗв/год)",
        min_value=0.0,
        format="%.4f"
    )
    unit = "мЗв/год"
    color = "darkred"   # ☢️ бордовий
else:
    substance = st.sidebar.text_input("Назва речовини", "Хлор")
    value = st.sidebar.number_input(
        "Концентрація (мг/куб.м)",
        min_value=0.0,
        format="%.4f"
    )
    unit = "мг/куб.м"
    color = "blue"      # ☣️ синій

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
        "type": mode,
        "substance": substance,
        "unit": unit,
        "color": color
    })
    st.sidebar.success("Точку додано")

# ===============================
# ЗАВАНТАЖЕННЯ CSV
# ===============================
st.sidebar.header("📂 Завантажити CSV")

uploaded = st.sidebar.file_uploader(
    "CSV файл",
    type=["csv"]
)

if uploaded:
    df = pd.read_csv(uploaded)

    required_cols = {"lat", "lon", "value", "time", "type"}
    if required_cols.issubset(df.columns):
        for _, r in df.iterrows():
            if r["type"] == "Радіаційна":
                st.session_state.data.append({
                    "lat": r.lat,
                    "lon": r.lon,
                    "value": round(float(r.value), 2),
                    "time": r.time,
                    "type": "Радіаційна",
                    "substance": "Радіація",
                    "unit": "мЗв/год",
                    "color": "darkred"
                })
            else:
                st.session_state.data.append({
                    "lat": r.lat,
                    "lon": r.lon,
                    "value": round(float(r.value), 2),
                    "time": r.time,
                    "type": "Хімічна",
                    "substance": r.get("substance", "Речовина"),
                    "unit": "мг/куб.м",
                    "color": "blue"
                })
        st.sidebar.success("CSV успішно завантажено")
    else:
        st.sidebar.error("CSV має містити: lat, lon, value, time, type")

# ===============================
# ПОБУДОВА КАРТИ
# ===============================
if st.session_state.data:
    df = pd.DataFrame(st.session_state.data)

    m = folium.Map(
        location=[df.lat.mean(), df.lon.mean()],
        zoom_start=13
    )

    for _, r in df.iterrows():
        # Точка
        folium.CircleMarker(
            location=[r.lat, r.lon],
            radius=7,
            color=r.color,
            fill=True,
            fill_color=r.color,
            fill_opacity=0.8
        ).add_to(m)

        # Підпис біля точки
        label_html = f"""
        <div style="
            color:{r.color};
            font-size:14px;
            font-weight:bold;
            background: transparent;
            white-space: nowrap;
        ">
            {r.substance} – {r.value:.2f} {r.unit}
            <hr style="margin:2px 0;border:1px solid {r.color};">
            {r.time}
        </div>
        """

        folium.Marker(
            [r.lat, r.lon],
            icon=DivIcon(
                icon_size=(220, 60),
                icon_anchor=(0, -10),
                html=label_html
            )
        ).add_to(m)

    st.subheader("🗺️ Карта обстановки")
    st_folium(m, height=600, width=None)

    # ===============================
    # ЕКСПОРТ HTML
    # ===============================
    st.subheader("💾 Експорт")
    html_map = m.get_root().render()

    st.download_button(
        "⬇️ Завантажити карту (HTML)",
        data=html_map,
        file_name="map.html",
        mime="text/html"
    )

else:
    st.info("Додайте точки вимірювання для відображення карти")

