import base64
from datetime import datetime
import json
import os
import requests
import streamlit as st
import streamlit.components.v1 as components

# ==============================================================================
# 1. KONFIGURACJA STRONY I STYLE
# ==============================================================================
st.set_page_config(
    page_title="Twoja Stacja Pogodowa",
    page_icon="🌤",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    /* Kolor tła głównej części aplikacji i iframe */
    .stApp,
    [data-testid="stAppViewContainer"],
    .main .block-container {
        background-color: #cfe2f3 !important;
        background: #cfe2f3 !important;
    }

    iframe {
        background-color: #cfe2f3 !important;
    }

    /* Pasek boczny zachowuje swój domyślny kolor tła */
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] > div:first-child,
    section[data-testid="stSidebarContent"] {
        background-color: initial !important;
        background: initial !important;
    }

    /* Całkowite ukrycie podpowiedzi "Press Enter to apply" */
    [data-testid="InputInstructions"],
    [data-testid="stInputInstruction"],
    .stTextInput [data-testid="InputInstructions"],
    .stTextInput small,
    div[data-testid="stTextInputRootElement"] span {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* Ukrycie przycisku Fullscreen dla obrazów (w tym logo) */
    button[title="View fullscreen"],
    button[title="Pełny ekran"],
    [data-testid="StyledFullScreenButton"],
    div[data-testid="stImage"] button {
        display: none !important;
        visibility: hidden !important;
    }

    /* Dopasowanie i brak zaokrągleń dla klikalnego kontenera logo */
    .sidebar-logo-container {
        display: block;
        width: 85%;
        margin-top: 10px;
        margin-bottom: 10px;
        text-align: center;
        margin: auto;
    }
    .sidebar-logo-container img {
        width: 100%;
        height: auto;
        border-radius: 0 !important;
        clip-path: none !important;
        display: block;
        cursor: pointer;
    }
    
    header[data-testid="stHeader"] {
        background: transparent !important;
        z-index: 999999 !important;
    }
    footer {
        display: none !important;
    }
    .main .block-container {
        padding: 0 !important;
        max-width: 100% !important;
        margin: 0 !important;
    }
    .main iframe {
        width: 100% !important;
        height: 96vh !important;
        border: none !important;
        display: block !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ==============================================================================
# 2. UWIERZYTELNIENIE I ZASOBY GRAFICZNE
# ==============================================================================
API_KEY = st.secrets.get("OPENWEATHER_API_KEY", "")


def find_image_file(base_name):
    """Wyszukuje plik graficzny niezależnie od rozszerzenia (.webp, .png, .jpg) i zer wiodących."""
    candidates = [
        f"{base_name}.webp",
        f"{base_name}.png",
        f"{base_name}.jpg",
        f"{base_name}.jpeg",
        f"{base_name}.WEBP",
        f"{base_name}.PNG",
    ]
    if base_name in ["5d", "5n"]:
        zero_name = f"0{base_name}"
        candidates.extend(
            [f"{zero_name}.webp", f"{zero_name}.png", f"{zero_name}.jpg"]
        )

    for path in candidates:
        if os.path.exists(path):
            return path
    return None


@st.cache_data(show_spinner=False)
def load_all_wallpapers():
    """Wczytuje i koduje tapety do Base64 tylko raz, zapisując je w pamięci podręcznej."""
    ikony = [
        "01d",
        "01n",
        "02d",
        "02n",
        "03d",
        "03n",
        "04d",
        "04n",
        "09d",
        "09n",
        "10d",
        "10n",
        "11d",
        "11n",
        "13d",
        "13n",
        "50d",
        "50n",
        "5d",
        "5n",
    ]
    wallpapers = {}
    for kod in ikony:
        file_path = find_image_file(kod)
        if file_path:
            try:
                with open(file_path, "rb") as img:
                    ext = os.path.splitext(file_path)[1].lower().replace(".", "")
                    mime = "jpeg" if ext in ["jpg", "jpeg"] else ext
                    wallpapers[kod] = (
                        f"data:image/{mime};base64,{base64.b64encode(img.read()).decode()}"
                    )
            except Exception:
                wallpapers[kod] = ""
        else:
            wallpapers[kod] = ""
    return wallpapers


wallpapers_dict = load_all_wallpapers()
wallpapers_json = json.dumps(wallpapers_dict)

# ==============================================================================
# 3. ZARZĄDZANIE LOKALIZACJĄ
# ==============================================================================
MIASTA = {
    "Płock": {"lat": 52.5463, "lon": 19.7065, "kraj": "Polska"},
    "Warszawa": {"lat": 52.2297, "lon": 21.0122, "kraj": "Polska"},
    "Gdańsk": {"lat": 54.3520, "lon": 18.6466, "kraj": "Polska"},
    "Kraków": {"lat": 50.0647, "lon": 19.9450, "kraj": "Polska"},
    "Wrocław": {"lat": 51.1079, "lon": 17.0385, "kraj": "Polska"},
    "Poznań": {"lat": 52.4064, "lon": 16.9252, "kraj": "Polska"},
    "Katowice": {"lat": 50.2649, "lon": 19.0238, "kraj": "Polska"},
}

if "miasto_nazwa" not in st.session_state:
    st.session_state.miasto_nazwa = "Płock"
    st.session_state.lat = MIASTA["Płock"]["lat"]
    st.session_state.lon = MIASTA["Płock"]["lon"]
    st.session_state.kraj = MIASTA["Płock"]["kraj"]

# Obsługa geolokalizacji z URL
query_params = st.query_params
if "detect_lat" in query_params and "detect_lon" in query_params:
    try:
        det_lat = float(query_params["detect_lat"])
        det_lon = float(query_params["detect_lon"])
        geo_rev = requests.get(
            f"https://api.openweathermap.org/geo/1.0/reverse?lat={det_lat}&lon={det_lon}&limit=1&appid={API_KEY}",
            timeout=5,
        ).json()
        if geo_rev:
            st.session_state.miasto_nazwa = geo_rev[0].get(
                "local_names", {}
            ).get("pl", geo_rev[0].get("name", "Twoja Lokalizacja"))
            st.session_state.kraj = geo_rev[0].get("country", "PL")
        else:
            st.session_state.miasto_nazwa = "Twoja Lokalizacja"
            st.session_state.kraj = "PL"
        st.session_state.lat = det_lat
        st.session_state.lon = det_lon
        st.query_params.clear()
        st.rerun()
    except Exception:
        pass

# ==============================================================================
# 4. PANEL BOCZNY (SIDEBAR)
# ==============================================================================
with st.sidebar:
    if os.path.exists("logo3.svg"):
        try:
            with open("logo3.svg", "rb") as svg_file:
                svg_base64 = base64.b64encode(svg_file.read()).decode()
            st.markdown(
                f"""
                <a href="https://fabryka.tech/" target="_blank" class="sidebar-logo-container">
                    <img src="data:image/svg+xml;base64,{svg_base64}" alt="Logo Fabryka.tech" />
                </a>
                """,
                unsafe_allow_html=True,
            )
        except Exception:
            st.image("logo3.svg", use_container_width=True)

    st.header("Ustawienia Lokalizacji")

    # Formularz: naciśnięcie Enter w polu tekstowym automatycznie wysyła formularz
    with st.form("form_wyszukiwania", border=False):
        wpisane_miasto = st.text_input(
            "Wpisz lub wybierz miasto:",
            value=st.session_state.miasto_nazwa,
            help="Wpisz dowolne miasto (np. Płock, Berlin, Paryż, Rzym)",
        ).strip()

        col1, col2 = st.columns(2)
        with col1:
            szukaj_klikniete = st.form_submit_button(
                "Szukaj", type="primary", use_container_width=True
            )
        with col2:
            odswiez_klikniete = st.form_submit_button(
                "Odśwież", use_container_width=True
            )

        if szukaj_klikniete:
            if wpisane_miasto in MIASTA:
                st.session_state.miasto_nazwa = wpisane_miasto
                st.session_state.lat = MIASTA[wpisane_miasto]["lat"]
                st.session_state.lon = MIASTA[wpisane_miasto]["lon"]
                st.session_state.kraj = MIASTA[wpisane_miasto]["kraj"]
                st.rerun()
            else:
                try:
                    geo_res = requests.get(
                        f"https://api.openweathermap.org/geo/1.0/direct?q={wpisane_miasto}&limit=1&appid={API_KEY}",
                        timeout=5,
                    ).json()
                    if geo_res:
                        st.session_state.miasto_nazwa = geo_res[0].get(
                            "local_names", {}
                        ).get("pl", geo_res[0]["name"])
                        st.session_state.lat = geo_res[0]["lat"]
                        st.session_state.lon = geo_res[0]["lon"]
                        st.session_state.kraj = geo_res[0].get("country", "")
                        st.rerun()
                    else:
                        st.error("Nie znaleziono miasta.")
                except Exception as e:
                    st.error(f"Błąd wyszukiwania: {e}")
        elif odswiez_klikniete:
            st.rerun()

    st.markdown("---")
    st.markdown("##### Automatyczna detekcja:")
    gps_button_html = """
    <button onclick="getLocation()" style="
        width: 100%;
        background-color: #0284c7;
        color: white;
        border: none;
        padding: 9px 14px;
        border-radius: 8px;
        font-weight: 700;
        cursor: pointer;
        font-size: 14px;
    ">📍 Wykryj moją lokalizację</button>
    <div id="gps-status" style="font-size: 11px; color: #64748b; margin-top: 6px; text-align: center;"></div>

    <script>
    function getLocation() {
        const status = document.getElementById('gps-status');
        if (!navigator.geolocation) {
            status.innerText = "Twoja przeglądarka nie wspiera geolokalizacji.";
            return;
        }
        status.innerText = "Pobieranie pozycji GPS...";
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                status.innerText = "Pobrano pozycję! Przeładowywanie...";
                const url = new URL(window.parent.location.href);
                url.searchParams.set('detect_lat', pos.coords.latitude);
                url.searchParams.set('detect_lon', pos.coords.longitude);
                window.parent.location.href = url.href;
            },
            () => {
                status.innerText = "Brak dostępu do GPS w przeglądarce.";
            },
            { timeout: 10000, enableHighAccuracy: true }
        );
    }
    </script>
    """
    components.html(gps_button_html, height=75)

    st.markdown("---")
    st.markdown("##### Opinie, uwagi?")
    st.link_button("Formularz kontaktowy", "https://fabryka.tech/kontakt", use_container_width=True)

lat = st.session_state.lat
lon = st.session_state.lon
wybrane_miasto = st.session_state.miasto_nazwa
kraj = st.session_state.kraj


# ==============================================================================
# 5. POBIERANIE I NORMALIZACJA DANYCH POGODOWYCH
# ==============================================================================
def pobierz_dane_pogodowe(p_lat, p_lon, key):
    url_3 = f"https://api.openweathermap.org/data/3.0/onecall?lat={p_lat}&lon={p_lon}&appid={key}&units=metric&lang=pl"
    res = requests.get(url_3, timeout=8)

    if res.status_code == 200:
        d = res.json()
        curr = d.get("current", {})
        w_obj = curr.get("weather", [{}])[0]
        hourly = d.get("hourly", [])
        return {
            "temp": round(curr.get("temp", 0)),
            "feels": round(curr.get("feels_like", 0)),
            "desc": w_obj.get("description", "").capitalize(),
            "icon": w_obj.get("icon", "01d"),
            "id": w_obj.get("id", 800),
            "wind": round(curr.get("wind_speed", 0) * 3.6),
            "humidity": curr.get("humidity", 0),
            "pop": int(hourly[0].get("pop", 0) * 100) if hourly else 0,
            "hours": hourly[:10],
            "daily": d.get("daily", [])[1:8],
        }

    # Fallback na API 2.5
    w_url = f"https://api.openweathermap.org/data/2.5/weather?lat={p_lat}&lon={p_lon}&appid={key}&units=metric&lang=pl"
    f_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={p_lat}&lon={p_lon}&appid={key}&units=metric&lang=pl"
    w_res = requests.get(w_url, timeout=8).json()
    f_res = requests.get(f_url, timeout=8).json()

    main = w_res.get("main", {})
    w_obj = w_res.get("weather", [{}])[0]
    forecast_list = f_res.get("list", [])

    hours_mapped = []
    for it in forecast_list[:10]:
        hours_mapped.append(
            {
                "dt": it["dt"],
                "temp": it["main"]["temp"],
                "feels_like": it["main"].get("feels_like", it["main"]["temp"]),
                "wind_speed": it.get("wind", {}).get("speed", 0),
                "humidity": it["main"]["humidity"],
                "pop": it.get("pop", 0),
                "weather": it["weather"],
            }
        )

    daily_grouped = {}
    for it in forecast_list:
        day_k = datetime.fromtimestamp(it["dt"]).strftime("%Y-%m-%d")
        if day_k not in daily_grouped:
            daily_grouped[day_k] = {
                "dt": it["dt"],
                "temp": {
                    "day": it["main"]["temp"],
                    "night": it["main"]["temp_min"],
                },
                "feels_like": {
                    "day": it["main"].get("feels_like", it["main"]["temp"])
                },
                "wind_speed": it.get("wind", {}).get("speed", 0),
                "humidity": it["main"]["humidity"],
                "pop": it.get("pop", 0),
                "weather": it["weather"],
            }

    return {
        "temp": round(main.get("temp", 0)),
        "feels": round(main.get("feels_like", 0)),
        "desc": w_obj.get("description", "").capitalize(),
        "icon": w_obj.get("icon", "01d"),
        "id": w_obj.get("id", 800),
        "wind": round(w_res.get("wind", {}).get("speed", 0) * 3.6),
        "humidity": main.get("humidity", 0),
        "pop": int(forecast_list[0].get("pop", 0) * 100)
        if forecast_list
        else 0,
        "hours": hours_mapped,
        "daily": list(daily_grouped.values())[1:8],
    }


try:
    pogoda = pobierz_dane_pogodowe(lat, lon, API_KEY)
except Exception as err:
    st.error(f"Nie udało się pobrać danych pogodowych: {err}")
    st.stop()

# ==============================================================================
# 6. FORMATOWANIE DAT I GENEROWANIE KAFELKÓW HTML
# ==============================================================================
teraz = datetime.now()
DNI = [
    "Poniedziałek",
    "Wtorek",
    "Środa",
    "Czwartek",
    "Piątek",
    "Sobota",
    "Niedziela",
]
SKROTY = ["Pn", "Wt", "Śr", "Cz", "Pt", "So", "Nied"]
MIESIACE = [
    "",
    "Stycznia",
    "Lutego",
    "Marca",
    "Kwietnia",
    "Maja",
    "Czerwca",
    "Lipca",
    "Sierpnia",
    "Września",
    "Października",
    "Listopada",
    "Grudnia",
]

data_napis = f"{DNI[teraz.weekday()]}, {teraz.day} {MIESIACE[teraz.month]}"
godzina_napis = teraz.strftime("%H:%M")

daily_items_html = ""
for d in pogoda["daily"][:7]:
    dt = datetime.fromtimestamp(d["dt"])
    skrot = f"{SKROTY[dt.weekday()]} {dt.day}"
    pelna_data = f"{DNI[dt.weekday()]}, {dt.day} {MIESIACE[dt.month]}"

    w_info = d.get("weather", [{}])[0]
    ico = w_info.get("icon", "01d")
    w_id = w_info.get("id", 800)
    desc = w_info.get("description", "").capitalize()

    t_obj = d.get("temp", {})
    t_day = round(
        t_obj.get("day", t_obj if isinstance(t_obj, (int, float)) else 0)
    )
    t_night = round(t_obj.get("night", t_day - 3))

    f_obj = d.get("feels_like", {})
    f_day = round(f_obj.get("day", t_day) if isinstance(f_obj, dict) else f_obj)

    wind = round(d.get("wind_speed", pogoda["wind"] / 3.6) * 3.6)
    hum = d.get("humidity", pogoda["humidity"])
    pop = int(d.get("pop", 0) * 100)

    daily_items_html += f"""
    <div class="day-col clickable-card" 
         data-date="{pelna_data}" 
         data-clock="Prognoza dzienna" 
         data-temp="{t_day}" 
         data-feels="{f_day}" 
         data-desc="{desc}" 
         data-icon="{ico}" 
         data-id="{w_id}"
         data-wind="{wind}" 
         data-hum="{hum}" 
         data-pop="{pop}">
        <div class="day-name">{skrot}</div>
        <img class="day-icon" src="https://openweathermap.org/img/wn/{ico}@2x.png" alt="ikona">
        <div class="day-temp-main">{t_day}°C</div>
        <div class="day-temp-sub">{t_night}°C</div>
    </div>
    """

hourly_items_html = ""
for h in pogoda["hours"][:6]:
    ht = datetime.fromtimestamp(h["dt"])
    h_time = ht.strftime("%H:%M")
    h_date = f"{DNI[ht.weekday()]}, {ht.day} {MIESIACE[ht.month]}"

    w_info = h.get("weather", [{}])[0]
    ico = w_info.get("icon", "01d")
    w_id = w_info.get("id", 800)
    desc = w_info.get("description", "").capitalize()

    temp = round(h.get("temp", 0))
    feels = round(h.get("feels_like", temp))
    wind = round(h.get("wind_speed", pogoda["wind"] / 3.6) * 3.6)
    hum = h.get("humidity", 0)
    pop = int(h.get("pop", 0) * 100)

    hourly_items_html += f"""
    <div class="hour-col clickable-card" 
         data-date="{h_date}" 
         data-clock="{h_time}" 
         data-temp="{temp}" 
         data-feels="{feels}" 
         data-desc="{desc}" 
         data-icon="{ico}" 
         data-id="{w_id}"
         data-wind="{wind}" 
         data-hum="{hum}" 
         data-pop="{pop}">
        <div class="hour-time">{h_time}</div>
        <img class="hour-icon" src="https://openweathermap.org/img/wn/{ico}@2x.png" alt="ikona">
        <div class="hour-temp">{temp}°C</div>
        <div class="hour-hum">💧 {hum}%</div>
    </div>
    """

# ==============================================================================
# 7. SZABLON WIDOKU (HTML + CSS + JAVASCRIPT)
# ==============================================================================
template_html = """<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
    * {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    html, body {
        width: 100%;
        height: 100%;
        overflow: hidden;
        background: #cfe2f3;
    }
    .app-container {
        width: 100%;
        height: 100%;
        background: #cfe2f3;
        padding: 12px 16px;
        display: flex;
        flex-direction: column;
    }
    .app-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 14px;
        font-weight: 800;
        letter-spacing: 2px;
        color: #334155;
        text-transform: uppercase;
        margin-bottom: 8px;
        padding: 0 4px;
        flex-shrink: 0;
    }
    .dashboard-grid {
        display: grid;
        grid-template-columns: 1.4fr 1fr;
        gap: 16px;
        flex: 1;
        min-height: 0;
    }
    .hero-card {
        position: relative;
        border-radius: 24px;
        padding: 2.5vh 2vw;
        color: white;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 12px 28px rgba(15, 23, 42, 0.25);
        height: 100%;
        background-color: #1e293b;
        background-size: cover !important;
        background-position: center !important;
        background-repeat: no-repeat !important;
        transition: background-image 0.35s ease-in-out;
        overflow: hidden;
    }
    .hero-top-row {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        z-index: 2;
    }
    .hero-city {
        font-size: clamp(22px, 2vw, 32px);
        font-weight: 900;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        text-shadow: 0 2px 8px rgba(0,0,0,0.5);
    }
    .hero-date {
        font-size: clamp(13px, 0.95vw, 16px);
        opacity: 0.95;
        margin-top: 2px;
        text-shadow: 0 2px 6px rgba(0,0,0,0.4);
    }
    .hero-clock {
        font-size: clamp(20px, 1.6vw, 26px);
        font-weight: 700;
        margin-top: 3px;
        text-shadow: 0 2px 6px rgba(0,0,0,0.4);
    }
    .btn-reset {
        background: rgba(15, 23, 42, 0.4);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.4);
        border-radius: 12px;
        padding: 6px 14px;
        font-size: 13px;
        font-weight: 700;
        cursor: pointer;
        backdrop-filter: blur(8px);
        transition: all 0.2s ease;
        display: none;
    }
    .btn-reset:hover {
        background: rgba(15, 23, 42, 0.65);
    }
    .hero-body {
        display: flex;
        align-items: center;
        justify-content: flex-end;
        margin: auto 0;
        padding: 0.5vh 0;
        z-index: 2;
    }
    .hero-temp-block {
        text-align: right;
        padding-right: 1.5vw;
    }
    .hero-temp-main {
        font-size: clamp(58px, 6.2vw, 92px);
        font-weight: 800;
        line-height: 1;
        text-shadow: 0 4px 14px rgba(0,0,0,0.5);
    }
    .hero-feels {
        font-size: clamp(14px, 1.05vw, 18px);
        opacity: 0.95;
        margin-bottom: 8px;
        text-shadow: 0 2px 6px rgba(0,0,0,0.4);
    }
    .hero-conditions {
        font-size: clamp(18px, 1.4vw, 24px);
        font-weight: 800;
        margin-bottom: 8px;
        text-shadow: 0 2px 8px rgba(0,0,0,0.5);
    }
    .hero-subdetails {
        font-size: clamp(13px, 1vw, 16px);
        opacity: 0.95;
        line-height: 1.45;
        text-shadow: 0 2px 6px rgba(0,0,0,0.4);
    }
    .clickable-card {
        cursor: pointer;
        border-radius: 14px;
        padding: 6px;
        transition: all 0.2s ease;
        user-select: none;
    }
    .clickable-card:hover {
        transform: translateY(-2px);
    }
    .day-col.clickable-card:hover {
        background: rgba(30, 41, 59, 0.08);
    }
    .hour-col.clickable-card:hover {
        background: #e2e8f0;
    }
    .clickable-card.active-selected {
        transform: scale(1.04);
        background: #0284c7 !important;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.35);
    }
    .clickable-card.active-selected div {
        color: white !important;
    }
    .daily-bar {
        background: rgba(255, 255, 255, 0.92);
        backdrop-filter: blur(14px);
        border-radius: 18px;
        padding: 1vh 0.8vw;
        display: flex;
        justify-content: space-around;
        align-items: center;
        color: #1e293b;
        box-shadow: 0 6px 18px rgba(0,0,0,0.14);
        z-index: 2;
    }
    .day-col {
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        gap: 2px;
    }
    .day-name {
        font-size: clamp(13px, 1.05vw, 16px);
        font-weight: 800;
        color: #1e293b;
    }
    .day-icon {
        width: clamp(34px, 3vw, 48px);
        height: clamp(34px, 3vw, 48px);
    }
    .day-temp-main {
        font-size: clamp(15px, 1.2vw, 19px);
        font-weight: 800;
        color: #0f172a;
    }
    .day-temp-sub {
        font-size: clamp(12px, 0.95vw, 14px);
        font-weight: 600;
        color: #64748b;
    }
    .right-column {
        display: flex;
        flex-direction: column;
        gap: 12px;
        height: 100%;
        min-height: 0;
    }
    .hourly-card {
        background: #f8fafc;
        border-radius: 24px;
        padding: 1.6vh 1.4vw;
        box-shadow: 0 8px 20px rgba(0,0,0,0.06);
        flex-shrink: 0;
    }
    .hourly-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .hour-col {
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        gap: 2px;
    }
    .hour-time {
        font-size: clamp(12px, 0.95vw, 15px);
        color: #475569;
        font-weight: 700;
    }
    .hour-icon {
        width: clamp(34px, 2.8vw, 46px);
        height: clamp(34px, 2.8vw, 46px);
    }
    .hour-temp {
        font-size: clamp(15px, 1.2vw, 19px);
        font-weight: 800;
        color: #0f172a;
    }
    .hour-hum {
        font-size: clamp(12px, 0.9vw, 14px);
        color: #0284c7;
        font-weight: 700;
    }
    .map-card {
        background: #f8fafc;
        border-radius: 24px;
        padding: 1.6vh 1.4vw;
        box-shadow: 0 8px 20px rgba(0,0,0,0.06);
        flex: 1;
        display: flex;
        flex-direction: column;
        min-height: 0;
    }
    .card-title {
        font-size: clamp(17px, 1.3vw, 21px);
        font-weight: 800;
        color: #0f172a;
    }
    #map {
        width: 100%;
        flex: 1;
        min-height: 120px;
        border-radius: 16px;
        margin-top: 8px;
        border: 1px solid #cbd5e1;
        z-index: 1;
    }
    .map-scale {
        height: 7px;
        background: linear-gradient(to right, #38bdf8, #22c55e, #eab308, #ef4444);
        border-radius: 4px;
        margin-top: 8px;
        flex-shrink: 0;
    }
</style>
</head>
<body>

<div class="app-container">
    <div class="app-header">
        <span></span>
        <span>TWOJA STACJA POGODOWA</span>
        <span></span>
    </div>

    <div class="dashboard-grid">
        <div class="hero-card" id="hero-card">
            <div class="hero-top-row">
                <div>
                    <div class="hero-city">__MIASTO__, __KRAJ__</div>
                    <div class="hero-date" id="hero-date">__DATA__</div>
                    <div class="hero-clock" id="hero-clock">__GODZINA__</div>
                </div>
                <button class="btn-reset" id="btn-reset" onclick="resetToCurrent()">↺ Teraz</button>
            </div>

            <div class="hero-body">
                <div class="hero-temp-block">
                    <div class="hero-temp-main" id="hero-temp">__TEMP__°C</div>
                    <div class="hero-feels" id="hero-feels">(odczuwalna __FEELS__°C)</div>
                    <div class="hero-conditions" id="hero-desc">__OPIS__</div>
                    <div class="hero-subdetails" id="hero-subdetails">
                        Wiatr: __WIATR__ km/h<br>
                        Wilgotność: __WILGOC__%<br>
                        Opady: __OPADY__%
                    </div>
                </div>
            </div>

            <div class="daily-bar">
                __DAILY_ITEMS__
            </div>
        </div>

        <div class="right-column">
            <div class="hourly-card">
                <div class="hourly-row">
                    __HOURLY_ITEMS__
                </div>
            </div>

            <div class="map-card">
                <div class="card-title">Mapa Pogody</div>
                <div id="map"></div>
                <div class="map-scale"></div>
            </div>
        </div>
    </div>
</div>

<script>
    const wallpapers = __WALLPAPERS_JSON__;

    function setHeroBackground(icon, id, desc) {
        let bgKey = icon;
        const weatherId = parseInt(id, 10);
        const lowerDesc = (desc || '').toLowerCase();
        const isNight = icon && icon.endsWith('n');

        // Wykrywanie słabych opadów (kody 500, 520 oraz kody mżawki 300-321)
        const isLightRain = lowerDesc.includes('słabe opady') || 
                            lowerDesc.includes('słaby deszcz') || 
                            lowerDesc.includes('lekki deszcz') || 
                            lowerDesc.includes('mżawka') ||
                            weatherId === 500 || 
                            weatherId === 520 || 
                            (weatherId >= 300 && weatherId <= 321);

        if (isLightRain) {
            bgKey = isNight ? '5n' : '5d';
        }

        // Awaryjne dopasowanie tła (np. 5d -> 10d -> 02d)
        let url = wallpapers[bgKey];
        if (!url && isLightRain) {
            url = isNight ? (wallpapers['10n'] || wallpapers['09n']) : (wallpapers['10d'] || wallpapers['09d']);
        }
        if (!url) {
            url = wallpapers[icon] || wallpapers['02d'] || '';
        }

        const hero = document.getElementById('hero-card');
        if (url) {
            hero.style.background = "linear-gradient(rgba(15, 23, 42, 0.40), rgba(15, 23, 42, 0.65)), url('" + url + "') center/cover no-repeat";
        } else {
            hero.style.background = "linear-gradient(135deg, #1e293b 0%, #0f172a 100%)";
        }
    }

    const initialWeather = {
        date: "__DATA__",
        clock: "__GODZINA__",
        temp: "__TEMP__",
        feels: "__FEELS__",
        desc: "__OPIS__",
        icon: "__IKONA__",
        id: "__WEATHER_ID__",
        wind: "__WIATR__",
        hum: "__WILGOC__",
        pop: "__OPADY__"
    };

    setHeroBackground(initialWeather.icon, initialWeather.id, initialWeather.desc);

    const allCards = document.querySelectorAll('.clickable-card');
    const btnReset = document.getElementById('btn-reset');

    function updateHeroView(data) {
        document.getElementById('hero-date').innerText = data.date;
        document.getElementById('hero-clock').innerText = data.clock;
        document.getElementById('hero-temp').innerText = data.temp + '°C';
        document.getElementById('hero-feels').innerText = '(odczuwalna ' + data.feels + '°C)';
        document.getElementById('hero-desc').innerText = data.desc;
        document.getElementById('hero-subdetails').innerHTML = 
            'Wiatr: ' + data.wind + ' km/h<br>' +
            'Wilgotność: ' + data.hum + '%<br>' +
            'Opady: ' + data.pop + '%';
        setHeroBackground(data.icon, data.id, data.desc);
    }

    allCards.forEach(card => {
        card.addEventListener('click', function() {
            allCards.forEach(c => c.classList.remove('active-selected'));
            this.classList.add('active-selected');

            const itemData = {
                date: this.getAttribute('data-date'),
                clock: this.getAttribute('data-clock'),
                temp: this.getAttribute('data-temp'),
                feels: this.getAttribute('data-feels'),
                desc: this.getAttribute('data-desc'),
                icon: this.getAttribute('data-icon'),
                id: this.getAttribute('data-id'),
                wind: this.getAttribute('data-wind'),
                hum: this.getAttribute('data-hum'),
                pop: this.getAttribute('data-pop')
            };

            updateHeroView(itemData);
            btnReset.style.display = 'block';
        });
    });

    function resetToCurrent() {
        allCards.forEach(c => c.classList.remove('active-selected'));
        updateHeroView(initialWeather);
        btnReset.style.display = 'none';
    }

    var map = L.map('map', { zoomControl: false, attributionControl: false }).setView([__LAT__, __LON__], 7);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19
    }).addTo(map);

    L.tileLayer('https://tile.openweathermap.org/map/clouds_new/{z}/{x}/{y}.png?appid=__API_KEY__', {
        maxZoom: 19,
        opacity: 0.55
    }).addTo(map);

    var marker = L.circleMarker([__LAT__, __LON__], {
        radius: 7,
        fillColor: "#ef4444",
        color: "#ffffff",
        weight: 2,
        opacity: 1,
        fillOpacity: 0.95
    }).addTo(map);
    
    marker.bindTooltip("<b>__MIASTO_RAW__</b>", { permanent: true, direction: 'top', offset: [0, -6] }).openTooltip();

    setTimeout(function() { map.invalidateSize(); }, 250);
    window.addEventListener('resize', function() { map.invalidateSize(); });
</script>

</body>
</html>
"""

# ==============================================================================
# 8. RENDEROWANIE WIDOKU
# ==============================================================================
podmiany = {
    "__MIASTO__": str(wybrane_miasto.upper()),
    "__MIASTO_RAW__": str(wybrane_miasto),
    "__KRAJ__": str(kraj.upper()),
    "__DATA__": str(data_napis),
    "__GODZINA__": str(godzina_napis),
    "__TEMP__": str(pogoda["temp"]),
    "__FEELS__": str(pogoda["feels"]),
    "__OPIS__": str(pogoda["desc"]),
    "__IKONA__": str(pogoda["icon"]),
    "__WEATHER_ID__": str(pogoda["id"]),
    "__WIATR__": str(pogoda["wind"]),
    "__WILGOC__": str(pogoda["humidity"]),
    "__OPADY__": str(pogoda["pop"]),
    "__DAILY_ITEMS__": daily_items_html,
    "__HOURLY_ITEMS__": hourly_items_html,
    "__WALLPAPERS_JSON__": wallpapers_json,
    "__LAT__": str(lat),
    "__LON__": str(lon),
    "__API_KEY__": API_KEY,
}

dashboard_html = template_html
for klucz, wartosc in podmiany.items():
    dashboard_html = dashboard_html.replace(klucz, wartosc)

components.html(dashboard_html, height=820, scrolling=False)
