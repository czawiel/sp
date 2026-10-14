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
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* Kolor tła dla głównego widoku - delikatny atmosferyczny gradient */
    .stApp {
        background: transparent !important;
    }
    
    .stMain,
    section[data-testid="stMain"],
    [data-testid="stAppViewContainer"] > .main {
        background: linear-gradient(135deg, #dbeafe 0%, #e0f2fe 50%, #f1f5f9 100%) !important;
    }

    /* Spójne, eleganckie tło i obramowanie dla paska bocznego (Sidebar) */
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] > div:first-child {
        background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%) !important;
        border-right: 1px solid #cbd5e1 !important;
        opacity: 1 !important;
    }

    /* Nagłówki i etykiety w pasku bocznym */
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h5 {
        color: #0f172a !important;
        font-weight: 700 !important;
        letter-spacing: -0.3px;
    }

    [data-testid="stSidebar"] label {
        color: #334155 !important;
        font-weight: 600 !important;
    }

    /* Pole tekstowe w pasku bocznym */
    [data-testid="stSidebar"] div[data-baseweb="input"] {
        border-radius: 10px !important;
        border: 1px solid #cbd5e1 !important;
        background-color: #ffffff !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03) !important;
        transition: all 0.2s ease;
    }
    [data-testid="stSidebar"] div[data-baseweb="input"]:focus-within {
        border-color: #0284c7 !important;
        box-shadow: 0 0 0 3px rgba(2, 132, 199, 0.15) !important;
    }

    /* Przyciski w formularzu i link button */
    [data-testid="stSidebar"] button[kind="primaryFormSubmit"] {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.25) !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stSidebar"] button[kind="primaryFormSubmit"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 16px rgba(2, 132, 199, 0.35) !important;
    }

    [data-testid="stSidebar"] button[kind="secondaryFormSubmit"],
    [data-testid="stSidebar"] a[data-testid="stBaseLinkButton-secondary"] {
        border-radius: 10px !important;
        border: 1px solid #cbd5e1 !important;
        background-color: #ffffff !important;
        color: #334155 !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stSidebar"] button[kind="secondaryFormSubmit"]:hover,
    [data-testid="stSidebar"] a[data-testid="stBaseLinkButton-secondary"]:hover {
        background-color: #f8fafc !important;
        border-color: #94a3b8 !important;
        color: #0f172a !important;
    }

    /* Na telefonach / wąskich oknach pasek dostaje cień i wysoki z-index */
    @media (max-width: 700px) {
        [data-testid="stSidebar"] {
            background: #f8fafc !important;
            box-shadow: 8px 0 32px rgba(15, 23, 42, 0.25) !important;
            z-index: 9999999 !important;
        }
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

    /* Ukrycie przycisku Fullscreen dla obrazów */
    button[title="View fullscreen"],
    button[title="Pełny ekran"],
    [data-testid="StyledFullScreenButton"],
    div[data-testid="stImage"] button {
        display: none !important;
        visibility: hidden !important;
    }

    /* Dopasowanie klikalnego kontenera logo */
    .sidebar-logo-container {
        display: block;
        width: 82%;
        margin: 8px auto 16px auto;
        text-align: center;
    }
    .sidebar-logo-container img {
        width: 100%;
        height: auto;
        border-radius: 0 !important;
        clip-path: none !important;
        display: block;
        cursor: pointer;
        transition: opacity 0.2s ease;
    }
    .sidebar-logo-container img:hover {
        opacity: 0.9;
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
        height: 100vh !important;
        min-height: 860px !important;
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
        "01d", "01n", "02d", "02n", "03d", "03n", "04d", "04n",
        "09d", "09n", "10d", "10n", "11d", "11n", "13d", "13n",
        "50d", "50n", "5d", "5n",
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
        geo_rev_res = requests.get(
            f"https://api.openweathermap.org/geo/1.0/reverse?lat={det_lat}&lon={det_lon}&limit=1&appid={API_KEY}",
            timeout=5,
        )
        geo_rev = geo_rev_res.json() if geo_rev_res.status_code == 200 else []
        if isinstance(geo_rev, list) and len(geo_rev) > 0:
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
            pass

    st.header("Ustawienia Lokalizacji")

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

        if szukaj_klikniete and wpisane_miasto:
            # Dopasowanie nazwy miasta ze słownika niezależnie od wielkości liter
            dopasowane_miasto = next(
                (m for m in MIASTA if m.lower() == wpisane_miasto.lower()), None
            )
            if dopasowane_miasto:
                st.session_state.miasto_nazwa = dopasowane_miasto
                st.session_state.lat = MIASTA[dopasowane_miasto]["lat"]
                st.session_state.lon = MIASTA[dopasowane_miasto]["lon"]
                st.session_state.kraj = MIASTA[dopasowane_miasto]["kraj"]
                st.rerun()
            else:
                try:
                    geo_req = requests.get(
                        f"https://api.openweathermap.org/geo/1.0/direct?q={wpisane_miasto}&limit=1&appid={API_KEY}",
                        timeout=5,
                    )
                    geo_res = geo_req.json() if geo_req.status_code == 200 else []
                    if isinstance(geo_res, list) and len(geo_res) > 0:
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
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@600;700&display=swap');
        body { margin: 0; padding: 2px; font-family: 'Plus Jakarta Sans', sans-serif; background: transparent; }
        .gps-btn {
            width: 100%;
            background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
            color: white;
            border: none;
            padding: 10px 14px;
            border-radius: 10px;
            font-weight: 700;
            cursor: pointer;
            font-size: 13.5px;
            box-shadow: 0 4px 12px rgba(2, 132, 199, 0.22);
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
        }
        .gps-btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 16px rgba(2, 132, 199, 0.32);
        }
        #gps-status {
            font-size: 11.5px;
            color: #475569;
            margin-top: 6px;
            text-align: center;
            font-weight: 600;
        }
    </style>
    <button class="gps-btn" onclick="getLocation()">📍 Wykryj moją lokalizację</button>
    <div id="gps-status"></div>

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
    components.html(gps_button_html, height=76)

    st.markdown("---")
    st.markdown("##### Masz opinie, uwagi, komentarze?")
    st.link_button(
        "Formularz kontaktowy",
        "https://fabryka.tech/kontakt",
        use_container_width=True,
    )

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
    
    w_req = requests.get(w_url, timeout=8)
    f_req = requests.get(f_url, timeout=8)
    w_req.raise_for_status()
    f_req.raise_for_status()

    w_res = w_req.json()
    f_res = f_req.json()

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
SKROTY = ["Pn", "Wt", "Śr", "Cz", "Pt", "So", "Nd"]
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
        <img class="day-icon" src="https://openweathermap.org/img/wn/{ico}@2x.png" alt="{desc}">
        <div class="day-temp-main">{t_day}°</div>
        <div class="day-temp-sub">{t_night}°</div>
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
        <img class="hour-icon" src="https://openweathermap.org/img/wn/{ico}@2x.png" alt="{desc}">
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
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
    * {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    html, body {
        width: 100%;
        min-height: 100%;
        background: transparent;
        overflow-x: hidden;
    }
    .app-container {
        width: 100%;
        min-height: 100vh;
        background: linear-gradient(135deg, #dbeafe 0%, #e0f2fe 50%, #f1f5f9 100%);
        padding: 14px 20px 20px 20px;
        display: flex;
        flex-direction: column;
    }
    .app-header {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 14px;
        flex-shrink: 0;
    }
    .header-badge {
        background: rgba(255, 255, 255, 0.75);
        backdrop-filter: blur(10px);
        padding: 6px 18px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 2px;
        color: #0369a1;
        text-transform: uppercase;
        border: 1px solid rgba(255, 255, 255, 0.9);
        box-shadow: 0 2px 10px rgba(15, 23, 42, 0.04);
    }
    .dashboard-grid {
        display: grid;
        grid-template-columns: 1.38fr 1fr;
        gap: 20px;
        flex: 1;
        min-height: 0;
    }

    /* KARTA GŁÓWNA (HERO) */
    .hero-card {
        position: relative;
        border-radius: 28px;
        padding: 28px;
        color: white;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 20px 40px -12px rgba(15, 23, 42, 0.32), inset 0 1px 0 rgba(255, 255, 255, 0.25);
        min-height: 500px;
        background-color: #0f172a;
        background-size: cover !important;
        background-position: center !important;
        background-repeat: no-repeat !important;
        transition: background 0.4s ease-in-out;
        overflow: hidden;
    }
    .hero-top-row {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        z-index: 2;
        gap: 12px;
    }
    .location-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(15, 23, 42, 0.35);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 6px 14px;
        border-radius: 999px;
        margin-bottom: 10px;
    }
    .hero-city {
        font-size: clamp(18px, 1.8vw, 26px);
        font-weight: 800;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        text-shadow: 0 2px 8px rgba(0,0,0,0.4);
    }
    .hero-date {
        font-size: clamp(13px, 1vw, 15px);
        font-weight: 500;
        opacity: 0.92;
        padding-left: 4px;
        text-shadow: 0 2px 6px rgba(0,0,0,0.45);
    }
    .hero-clock {
        font-size: clamp(20px, 1.6vw, 26px);
        font-weight: 800;
        margin-top: 2px;
        padding-left: 4px;
        letter-spacing: -0.5px;
        text-shadow: 0 2px 8px rgba(0,0,0,0.45);
    }
    .btn-reset {
        background: rgba(15, 23, 42, 0.45);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.35);
        border-radius: 999px;
        padding: 8px 16px;
        font-size: 13px;
        font-weight: 700;
        cursor: pointer;
        backdrop-filter: blur(12px);
        transition: all 0.2s ease;
        display: none;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    .btn-reset:hover {
        background: rgba(2, 132, 199, 0.85);
        border-color: rgba(255, 255, 255, 0.6);
        transform: translateY(-1px);
    }

    .hero-body {
        display: flex;
        align-items: center;
        justify-content: flex-end;
        margin: 24px 0;
        z-index: 2;
    }
    .hero-temp-block {
        text-align: right;
        display: flex;
        flex-direction: column;
        align-items: flex-end;
    }
    .hero-temp-main {
        font-size: clamp(58px, 6vw, 96px);
        font-weight: 800;
        line-height: 0.95;
        letter-spacing: -3px;
        text-shadow: 0 6px 20px rgba(0,0,0,0.45);
    }
    .hero-feels {
        font-size: clamp(13px, 1vw, 16px);
        font-weight: 500;
        opacity: 0.9;
        margin-top: 6px;
        margin-bottom: 10px;
        text-shadow: 0 2px 6px rgba(0,0,0,0.45);
    }
    .hero-conditions {
        font-size: clamp(18px, 1.5vw, 24px);
        font-weight: 800;
        margin-bottom: 14px;
        text-shadow: 0 2px 10px rgba(0,0,0,0.5);
    }
    .hero-subdetails {
        display: flex;
        flex-wrap: wrap;
        justify-content: flex-end;
        gap: 8px;
    }
    .stat-pill {
        background: rgba(15, 23, 42, 0.42);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.22);
        padding: 6px 12px;
        border-radius: 12px;
        font-size: 13px;
        font-weight: 600;
        color: #f8fafc;
        display: inline-flex;
        align-items: center;
        gap: 5px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.15);
    }

    /* INTERAKTYWNE KAFELKI DNI I GODZIN */
    .clickable-card {
        cursor: pointer;
        border-radius: 16px;
        padding: 8px 6px;
        transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1);
        user-select: none;
        border: 1px solid transparent;
    }
    .clickable-card:hover {
        transform: translateY(-3px);
    }
    .day-col.clickable-card:hover {
        background: rgba(2, 132, 199, 0.08);
        border-color: rgba(2, 132, 199, 0.18);
    }
    .hour-col.clickable-card {
        background: rgba(241, 245, 249, 0.7);
        border: 1px solid rgba(226, 232, 240, 0.8);
    }
    .hour-col.clickable-card:hover {
        background: rgba(224, 242, 254, 0.75);
        border-color: rgba(125, 211, 252, 0.6);
    }
    .clickable-card.active-selected {
        transform: translateY(-3px) scale(1.02);
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
        border-color: rgba(255, 255, 255, 0.3) !important;
        box-shadow: 0 8px 20px -4px rgba(2, 132, 199, 0.45);
    }
    .clickable-card.active-selected div {
        color: white !important;
    }

    /* PASEK TYGODNIOWY NA DOLE HERO */
    .daily-bar {
        background: rgba(255, 255, 255, 0.88);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.95);
        border-radius: 22px;
        padding: 12px 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: #1e293b;
        box-shadow: 0 10px 25px rgba(15, 23, 42, 0.18);
        z-index: 2;
        overflow-x: auto;
        gap: 4px;
    }
    .day-col {
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        gap: 2px;
        min-width: 56px;
        flex: 1;
    }
    .day-name {
        font-size: 12.5px;
        font-weight: 800;
        color: #334155;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }
    .day-icon, .hour-icon {
        width: 40px;
        height: 40px;
        filter: drop-shadow(0 3px 5px rgba(15, 23, 42, 0.18));
    }
    .day-temp-main {
        font-size: 15px;
        font-weight: 800;
        color: #0f172a;
    }
    .day-temp-sub {
        font-size: 12px;
        font-weight: 600;
        color: #64748b;
    }

    /* PRAWA KOLUMNA */
    .right-column {
        display: flex;
        flex-direction: column;
        gap: 20px;
        height: 100%;
        min-height: 0;
    }
    .hourly-card {
        background: rgba(255, 255, 255, 0.82);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.9);
        border-radius: 28px;
        padding: 18px 20px;
        box-shadow: 0 10px 30px -5px rgba(15, 23, 42, 0.06);
        flex-shrink: 0;
        overflow-x: auto;
    }
    .section-subtitle {
        font-size: 12px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #64748b;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .hourly-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 8px;
        min-width: 320px;
    }
    .hour-col {
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        gap: 3px;
        min-width: 54px;
        flex: 1;
    }
    .hour-time {
        font-size: 12.5px;
        color: #475569;
        font-weight: 700;
    }
    .hour-temp {
        font-size: 15px;
        font-weight: 800;
        color: #0f172a;
    }
    .hour-hum {
        font-size: 11.5px;
        color: #0284c7;
        font-weight: 700;
    }

    /* KARTA MAPY */
    .map-card {
        background: rgba(255, 255, 255, 0.82);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.9);
        border-radius: 28px;
        padding: 18px 20px;
        box-shadow: 0 10px 30px -5px rgba(15, 23, 42, 0.06);
        flex: 1;
        display: flex;
        flex-direction: column;
        min-height: 290px;
    }
    .card-header-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }
    .card-title {
        font-size: 16px;
        font-weight: 800;
        color: #0f172a;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .card-badge {
        font-size: 11px;
        font-weight: 700;
        color: #0284c7;
        background: #e0f2fe;
        padding: 4px 10px;
        border-radius: 999px;
    }
    #map {
        width: 100%;
        flex: 1;
        min-height: 220px;
        border-radius: 18px;
        border: 1px solid #cbd5e1;
        box-shadow: inset 0 2px 6px rgba(0,0,0,0.05);
        z-index: 1;
    }
    .map-scale-wrapper {
        margin-top: 10px;
        flex-shrink: 0;
    }
    .map-scale {
        height: 6px;
        background: linear-gradient(to right, #38bdf8, #22c55e, #eab308, #ef4444);
        border-radius: 999px;
    }
    .map-scale-labels {
        display: flex;
        justify-content: space-between;
        font-size: 10.5px;
        font-weight: 700;
        color: #64748b;
        margin-top: 4px;
    }

    /* RESPONSYWNOŚĆ DLA MNIEJSZYCH EKRANÓW */
    @media (max-width: 768px) {
        html, body {
            overflow-y: auto !important;
            height: auto !important;
        }
        .app-container {
            height: auto !important;
            min-height: auto;
            padding: 12px;
        }
        .dashboard-grid {
            grid-template-columns: 1fr !important;
            display: flex !important;
            flex-direction: column !important;
            gap: 16px;
        }
        .hero-card {
            min-height: 440px;
            padding: 20px;
            height: auto !important;
        }
        .right-column {
            height: auto !important;
        }
        .map-card {
            min-height: 320px;
        }
        #map {
            min-height: 240px;
        }
    }
</style>
</head>
<body>

<div class="app-container">
    <div class="app-header">
        <div class="header-badge">⛅ TWOJA STACJA POGODOWA</div>
    </div>

    <div class="dashboard-grid">
        <div class="hero-card" id="hero-card">
            <div class="hero-top-row">
                <div>
                    <div class="location-pill">
                        <span>📍</span>
                        <span class="hero-city">__MIASTO__, __KRAJ__</span>
                    </div>
                    <div class="hero-date" id="hero-date">__DATA__</div>
                    <div class="hero-clock" id="hero-clock">__GODZINA__</div>
                </div>
                <button class="btn-reset" id="btn-reset" onclick="resetToCurrent()">↺ Teraz</button>
            </div>

            <div class="hero-body">
                <div class="hero-temp-block">
                    <div class="hero-temp-main" id="hero-temp">__TEMP__°C</div>
                    <div class="hero-feels" id="hero-feels">Odczuwalna __FEELS__°C</div>
                    <div class="hero-conditions" id="hero-desc">__OPIS__</div>
                    <div class="hero-subdetails" id="hero-subdetails">
                        <span class="stat-pill">💨 Wiatr: __WIATR__ km/h</span>
                        <span class="stat-pill">💧 Wilgotność: __WILGOC__%</span>
                        <span class="stat-pill">☔ Opady: __OPADY__%</span>
                    </div>
                </div>
            </div>

            <div class="daily-bar">
                __DAILY_ITEMS__
            </div>
        </div>

        <div class="right-column">
            <div class="hourly-card">
                <div class="section-subtitle">🕒 Prognoza godzinowa</div>
                <div class="hourly-row">
                    __HOURLY_ITEMS__
                </div>
            </div>

            <div class="map-card">
                <div class="card-header-row">
                    <div class="card-title">🗺️ Mapa Pogody</div>
                    <div class="card-badge">Warstwa chmur</div>
                </div>
                <div id="map"></div>
                <div class="map-scale-wrapper">
                    <div class="map-scale"></div>
                    <div class="map-scale-labels">
                        <span>Bezchmurnie</span>
                        <span>Umiarkowane</span>
                        <span>Pełne zachmurzenie</span>
                    </div>
                </div>
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

        let url = wallpapers[bgKey];
        if (!url && isLightRain) {
            url = isNight ? (wallpapers['10n'] || wallpapers['09n']) : (wallpapers['10d'] || wallpapers['09d']);
        }
        if (!url) {
            url = wallpapers[icon] || wallpapers['02d'] || '';
        }

        const hero = document.getElementById('hero-card');
        if (url) {
            hero.style.background = "linear-gradient(180deg, rgba(15, 23, 42, 0.30) 0%, rgba(15, 23, 42, 0.72) 100%), url('" + url + "') center/cover no-repeat";
        } else {
            hero.style.background = isNight 
                ? "linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #312e81 100%)"
                : "linear-gradient(135deg, #0284c7 0%, #0369a1 50%, #1e3a8a 100%)";
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
        document.getElementById('hero-feels').innerText = 'Odczuwalna ' + data.feels + '°C';
        document.getElementById('hero-desc').innerText = data.desc;
        document.getElementById('hero-subdetails').innerHTML = 
            '<span class="stat-pill">💨 Wiatr: ' + data.wind + ' km/h</span>' +
            '<span class="stat-pill">💧 Wilgotność: ' + data.hum + '%</span>' +
            '<span class="stat-pill">☔ Opady: ' + data.pop + '%</span>';
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
        opacity: 0.6
    }).addTo(map);

    var marker = L.circleMarker([__LAT__, __LON__], {
        radius: 8,
        fillColor: "#0284c7",
        color: "#ffffff",
        weight: 2.5,
        opacity: 1,
        fillOpacity: 0.95
    }).addTo(map);
    
    marker.bindTooltip("<b>__MIASTO_RAW__</b>", { permanent: true, direction: 'top', offset: [0, -8] }).openTooltip();

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

components.html(dashboard_html, height=880, scrolling=True)
