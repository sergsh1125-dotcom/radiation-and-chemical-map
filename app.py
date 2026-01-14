import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from branca.element import DivIcon

# ===============================
# Налаштування сторінки
# ===============================
st.set_page_config(page_title="Radiation and Chemical Map", layout="wide")

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
if "radiation" not in st.session_state:
    st.session_state.radiation = pd.DataFrame(columns=["lat","lon","dose","time"])
if "chemical" not in st.session_state:
    st.session_state.chemical = pd.DataFrame(columns=["lat","lon","concentration","time","substance"])
if "show_help" not in st.session_state:
    st.session_state.show_help = False

# ===============================
# Заголовок та інструкція
# ===============================
st.title("☢️🧪 Карта радіаційної та хімічної обстановки")
if st.button("ℹ️ Інструкція користування", use_container_width=True):
    st.session_state.show_help = not st.session_state.show_help

if st.session_state.show_help:
    st.info("""
**Призначення:**  
Програма відображає радіаційну та хімічну обстановку на карті.  

**Можливості:**  
- Додавати точки вручну або завантажувати CSV-файли  
- Відображати концентрацію або потужність дози та час вимірювання  
- Підписи біля точок кольорові та завжди видимі  
- Завантажувати карти у форматі HTML  

**Алгоритм:**  
1. Введіть дані вручну або завантажте CSV:  
   - `radiation.data.csv`: lat, lon, dose, time  
   - `chemical.data.csv`: lat, lon, concentration, time, substance  
2. Дані з’являються на карті з кольоровими підписами.  

**Кольори:**  
- 🔴 Радіація — бордові точки  
- 🔵 Хімія — сині точки
""")

# ===============================
# Розділення екрану
# ===============================
col_map, col_gui = st.columns([2.5, 1])

# ===============================
# GUI — права панель
# ===============================
with col_gui:
    st.subheader("⚙️ Ввід даних")

    # --- Радіація ---
    st.markdown("### ☢️ Радіаційна обстановка")
    r_lat = st.number_input("Lat (радіація)", format="%.6f", key="r_lat")
    r_lon = st.number_input("Lon (радіація)", format="%.6f", key="r_lon")
    r_dose = st.number_input("Потужність дози (мЗв/год)", min_value=0.0, step=0.01)
    r_time = st.text_input("Час вимірювання", key="r_time")
    if st.button("➕ Додати радіацію", use_container_width=True):
        st.session_state.radiation = pd.concat(
            [st.session_state.radiation,
             pd.DataFrame([{"lat": r_lat, "lon": r_lon, "dose": round(r_dose,2), "time": r_time}])],
            ignore_index=True
        )

    st.divider()

    # --- Хімія ---
    st.markdown("### 🧪 Хімічна речовина")
    c_sub = st.text_input("Назва речовини", value="Хлор")
    c_lat = st.number_input("Lat (хімія)", format="%.6f", key="c_lat")
    c_lon = st.number_input("Lon (хімія)", format="%.6f", key="c_lon")
    c_val = st.number_input("Концентрація (мг/м³)", min_value=0.0, step=0.01)
    c_time = st.text_input("Час вимірювання", key="c_time")
    if st.button("➕ Додати хімію", use_container_width=True):
        st.session_state.chemical = pd.concat(
            [st.session_state.chemical,
             pd.DataFrame([{"lat": c_lat,"lon": c_lon,"concentration": round(c_val,2),
                            "time": c_time,"substance": c_sub}])],
            ignore_index=True
        )

    st.divider()

    # --- CSV завантаження ---
    rad_file = st.file_uploader("📂 radiation.data.csv", type=["csv"])
    if rad_file:
        df_rad = pd.read_csv(rad_file)
        df_rad["lat"] = pd.to_numeric(df_rad["lat"], errors="coerce")
        df_rad["lon"] = pd.to_numeric(df_rad["lon"], errors="coerce")
        df_rad["dose"] = pd.to_numeric(df_rad["dose"], errors="coerce")
        df_rad = df_rad.dropna(subset=["lat","lon","dose"])
        st.session_state.radiation = df_rad
        st.success(f"Завантажено {len(df_rad)} точок радіації")

    chem_file = st.file_uploader("📂 chemical.data.csv", type=["csv"])
    if chem_file:
        df_chem = pd.read_csv(chem_file)
        df_chem["lat"] = pd.to_numeric(df_chem["lat"], errors="coerce")
        df_chem["lon"] = pd.to_numeric(df_chem["lon"], errors="coerce")
        df_chem["concentration"] = pd.to_numeric(df_chem["concentration"], errors="coerce")
        df_chem = df_chem.dropna(subset=["lat","lon","concentration"])
        st.session_state.chemical = df_chem
        st.success(f"Завантажено {len(df_chem)} точок хімії")

    if st.button("🧹 Очистити всі дані", use_container_width=True):
        st.session_state.radiation = st.session_state.radiation.iloc[0:0]
        st.session_state.chemical = st.session_state.chemical.iloc[0:0]

# ===============================
# Карта — ліва панель
# ===============================
with col_map:
    if st.session_state.radiation.empty and st.session_state.chemical.empty:
        st.info("Немає даних для відображення")
    else:
        # Центр карти
        all_lat = pd.concat([
            pd.to_numeric(st.session_state.radiation.get("lat", pd.Series(dtype=float))),
            pd.to_numeric(st.session_state.chemical.get("lat", pd.Series(dtype=float)))
        ])
        all_lon = pd.concat([
            pd.to_numeric(st.session_state.radiation.get("lon", pd.Series(dtype=float))),
            pd.to_numeric(st.session_state.chemical.get("lon", pd.Series(dtype=float)))
        ])
        m = folium.Map(location=[all_lat.mean(), all_lon.mean()], zoom_start=13, control_scale=True)

        # Радіація
        for _, r in st.session_state.radiation.iterrows():
            label_html = f"""
            <div style="color: darkred; font-weight:bold; white-space:nowrap;">
                ☢️ {r['dose']:.2f} мЗв/год<br><i>{r['time']}</i>
            </div>
            """
            folium.CircleMarker([r["lat"], r["lon"]], radius=7, color="darkred",
                                fill=True, fill_color="darkred", fill_opacity=0.9).add_to(m)
            folium.Marker([r["lat"], r["lon"]],
                          icon=DivIcon(icon_size=(150,36), icon_anchor=(0,0), html=label_html)
                          ).add_to(m)

        # Хімія
        for _, r in st.session_state.chemical.iterrows():
            label_html = f"""
            <div style="color: blue; font-weight:bold; white-space:nowrap;">
                🧪 {r['substance']} – {r['concentration']:.2f} мг/м³<br><i>{r['time']}</i>
            </div>
            """
            folium.CircleMarker([r["lat"], r["lon"]], radius=7, color="blue",
                                fill=True, fill_color="blue", fill_opacity=0.9).add_to(m)
            folium.Marker([r["lat"], r["lon"]],
                          icon=DivIcon(icon_size=(180,36), icon_anchor=(0,0), html=label_html)
                          ).add_to(m)

        st_folium(m, height=550, width=None, key="map")

        # HTML експорт
        m.save("situation_map.html")
        with open("situation_map.html", "rb") as f:
            st.download_button("💾 Завантажити радіаційну та хімічну обстановку",
                               f, file_name="situation_map.html", mime="text/html",
                               use_container_width=True)

