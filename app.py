import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# =====================================================
# НАЛАШТУВАННЯ СТОРІНКИ
# =====================================================
st.set_page_config(
    page_title="Радіаційна та хімічна обстановка",
    layout="wide"
)

# Приховуємо службові елементи
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# =====================================================
# СТАН ПРОГРАМИ
# =====================================================
if "radiation" not in st.session_state:
    st.session_state.radiation = pd.DataFrame(
        columns=["lat", "lon", "dose", "time"]
    )

if "chemical" not in st.session_state:
    st.session_state.chemical = pd.DataFrame(
        columns=["lat", "lon", "concentration", "time", "substance"]
    )

# =====================================================
# ЗАГОЛОВОК
# =====================================================
st.title("☢️🧪 Радіаційна та хімічна обстановка")

# =====================================================
# РОЗДІЛЕННЯ ЕКРАНУ
# =====================================================
col_map, col_gui = st.columns([2.5, 1])

# =====================================================
# ПРАВА ПАНЕЛЬ — ВВІД ДАНИХ
# =====================================================
with col_gui:
    st.subheader("⚙️ Ввід даних")

    # -------------------------
    # Радіація
    # -------------------------
    st.markdown("### ☢️ Радіація (мЗв/год)")
    r_lat = st.number_input("Lat (радіація)", format="%.6f", key="r_lat")
    r_lon = st.number_input("Lon (радіація)", format="%.6f", key="r_lon")
    r_dose = st.number_input(
        "Потужність дози (мЗв/год)",
        min_value=0.0,
        step=0.01
    )
    r_time = st.text_input("Час вимірювання (радіація)", key="r_time")

    if st.button("➕ Додати радіацію", use_container_width=True):
        st.session_state.radiation = pd.concat(
            [
                st.session_state.radiation,
                pd.DataFrame([{
                    "lat": r_lat,
                    "lon": r_lon,
                    "dose": round(r_dose, 2),
                    "time": r_time
                }])
            ],
            ignore_index=True
        )

    st.divider()

    # -------------------------
    # Хімія
    # -------------------------
    st.markdown("### 🧪 Хімічна обстановка")
    c_sub = st.text_input("Назва речовини", value="Хлор")
    c_lat = st.number_input("Lat (хімія)", format="%.6f", key="c_lat")
    c_lon = st.number_input("Lon (хімія)", format="%.6f", key="c_lon")
    c_val = st.number_input(
        "Концентрація (мг/м³)",
        min_value=0.0,
        step=0.01
    )
    c_time = st.text_input("Час вимірювання (хімія)", key="c_time")

    if st.button("➕ Додати хімію", use_container_width=True):
        st.session_state.chemical = pd.concat(
            [
                st.session_state.chemical,
                pd.DataFrame([{
                    "lat": c_lat,
                    "lon": c_lon,
                    "concentration": round(c_val, 2),
                    "time": c_time,
                    "substance": c_sub
                }])
            ],
            ignore_index=True
        )

    st.divider()

    # -------------------------
    # CSV
    # -------------------------
    rad_file = st.file_uploader("📂 radiation.data.csv", type=["csv"])
    if rad_file:
        df = pd.read_csv(rad_file)
        if {"lat", "lon", "dose", "time"}.issubset(df.columns):
            st.session_state.radiation = df
        else:
            st.error("❌ Невірна структура radiation CSV")

    chem_file = st.file_uploader("📂 chemical.data.csv", type=["csv"])
    if chem_file:
        df = pd.read_csv(chem_file)
        if {"lat", "lon", "concentration", "time", "substance"}.issubset(df.columns):
            st.session_state.chemical = df
        else:
            st.error("❌ Невірна структура chemical CSV")

    if st.button("🧹 Очистити всі дані", use_container_width=True):
        st.session_state.radiation = st.session_state.radiation.iloc[0:0]
        st.session_state.chemical = st.session_state.chemical.iloc[0:0]

# =====================================================
# ЛІВА ПАНЕЛЬ — КАРТА
# =====================================================
with col_map:
    if st.session_state.radiation.empty and st.session_state.chemical.empty:
        st.info("Немає даних для відображення")
    else:
        all_lat = pd.concat([
            st.session_state.radiation.get("lat", pd.Series(dtype=float)),
            st.session_state.chemical.get("lat", pd.Series(dtype=float))
        ])

        all_lon = pd.concat([
            st.session_state.radiation.get("lon", pd.Series(dtype=float)),
            st.session_state.chemical.get("lon", pd.Series(dtype=float))
        ])

        m = folium.Map(
            location=[all_lat.mean(), all_lon.mean()],
            zoom_start=13,
            control_scale=True
        )

        # Радіація
        for _, r in st.session_state.radiation.iterrows():
            folium.CircleMarker(
                [r["lat"], r["lon"]],
                radius=7,
                color="darkred",
                fill=True,
                fill_color="darkred",
                fill_opacity=0.9,
                tooltip=f"Радіація: {r['dose']:.2f} мЗв/год | {r['time']}"
            ).add_to(m)

        # Хімія
        for _, r in st.session_state.chemical.iterrows():
            folium.CircleMarker(
                [r["lat"], r["lon"]],
                radius=7,
                color="blue",
                fill=True,
                fill_color="blue",
                fill_opacity=0.9,
                tooltip=f"{r['substance']}: {r['concentration']:.2f} мг/м³ | {r['time']}"
            ).add_to(m)

        st_folium(m, height=550, width=None, key="map")

        # Експорт HTML
        m.save("situation_map.html")
        with open("situation_map.html", "rb") as f:
            st.download_button(
                "💾 Завантажити карту (HTML)",
                f,
                file_name="situation_map.html",
                mime="text/html",
                use_container_width=True
            )

