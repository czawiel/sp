import streamlit as st
import streamlit.components.v1 as components
import requests
import base64
import json
import os
from datetime import datetime

# Ustawienia strony
st.set_page_config(
    page_title="Twoja Stacja Pogodowa",
    page_icon="🌤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Poprawione dopasowanie kontenera i iframe do przestrzeni roboczej
st.markdown("""
<style>
    /* Ukrycie instrukcji "Press Enter to apply" pod polami tekstowymi */
    [data-testid="InputInstructions"] {
        display: none !important;
    }

    /* Pasek nagłówka pozostaje widoczny, by móc rozwijać/zwijać sidebar */
    header[data-testid="stHeader"] {
        background: transparent !important;
        z-index: 999999 !important;
    }
    footer {
        display: none !important;
    }
    .stApp {
        background-color: #f1f5f9;
        margin: 0 !important;
        padding: 0 !important;
    }
    .main .block-container {
        padding: 0 !important;
        max-width: 100% !important;
        margin: 0 !important;
    }
    /* Ograniczenie 96vh tylko do głównego dashboardu, aby nie psuć iframe w sidebarze */
    .main iframe {
        width: 100% !important;
        height: 96vh !important;
        border: none !important;
        display: block !important;
    }
</style>
""", unsafe_allow_html=True)

# Pobieranie klucza wyłącznie ze Streamlit Secrets
API_KEY = st.secrets.get("OPENWEATHER_API_KEY", "")

if not API_KEY:
    st.error("Brak klucza API! Skonfiguruj klucz 'OPENWEATHER_API_KEY' w ustawieniach Streamlit Secrets (App settings -> Secrets) lub w pliku .streamlit/secrets.toml.")
    st.stop()

# Funkcja pomocnicza kodująca lokalne pliki webp do formatu Base64
def get_base64_image(image_path):
    if not os.path.exists(image_path):
        return ""
    try:
        with open(image_path, "rb") as img_file:
            return f"data:image/webp;base64,{base64.b64encode(img_file.read()).decode()}"
    except Exception:
        return ""

# Automatyczne załadowanie wszystkich kodów pogodowych do jednego słownika
IKONY_POGODY = [
    "01d", "01n", "02d", "02n", "03d", "03n", "04d", "04n",
    "09d", "09n", "10d", "10n", "11d", "11n", "13d", "13n", "50d", "50n"
]

wallpapers_dict = {kod: get_base64_image(f"{kod}.webp") for kod in IKONY_POGODY}
wallpapers_json = json.dumps(wallpapers_dict)

# Baza predefiniowanych miast
MIASTA = {
    "Płock": {"lat": 52.5463, "lon": 19.7065, "kraj": "Polska"},
    "Warszawa": {"lat": 52.2297, "lon": 21.0122, "kraj": "Polska"},
    "Gdańsk": {"lat": 54.3520, "lon": 18.6466, "kraj": "Polska"},
    "Kraków": {"lat": 50.0647, "lon": 19.9450, "kraj": "Polska"},
    "Wrocław": {"lat": 51.1079, "lon": 17.0385, "kraj": "Polska"},
    "Poznań": {"lat": 52.4064, "lon": 16.9252, "kraj": "Polska"},
    "Katowice": {"lat": 50.2649, "lon": 19.0238, "kraj": "Polska"},
}

# Inicjalizacja stanu lokalizacji w sesji
if "miasto_nazwa" not in st.session_state:
    st.session_state.miasto_nazwa = "Płock"
if "lat" not in st.session_state:
    st.session_state.lat = MIASTA["Płock"]["lat"]
if "lon" not in st.session_state:
    st.session_state.lon = MIASTA["Płock"]["lon"]
if "kraj" not in st.session_state:
    st.session_state.kraj = MIASTA["Płock"]["kraj"]

# Odczyt parametrów query przekazanych przez detektor GPS
query_params = st.query_params
if "detect_lat" in query_params and "detect_lon" in query_params:
    try:
        det_lat = float(query_params["detect_lat"])
        det_lon = float(query_params["detect_lon"])
        # Reverse Geocoding przez OpenWeather
        geo_rev = requests.get(
            f"https://api.openweathermap.org/geo/1.0/reverse?lat={det_lat}&lon={det_lon}&limit=1&appid={API_KEY}",
            timeout=5
        ).json()
        if geo_rev and len(geo_rev) > 0:
            st.session_state.miasto_nazwa = geo_rev[0].get("local_names", {}).get("pl", geo_rev[0].get("name", "Twoja Lokalizacja"))
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

# ----------------- PANEL BOCZNY -----------------
with st.sidebar:
    try:
        if os.path.exists("logo.png"):
            st.image("logo.png", use_container_width=True)
    except Exception:
        pass
    st.header("Ustawienia Lokalizacji")
    
    wpisane_miasto = st.text_input(
        "Wpisz lub wybierz miasto:",
        value=st.session_state.miasto_nazwa,
        help="Możesz wpisać dowolne miasto na świecie (np. Płock, Berlin, Paryż, Rzym)"
    ).strip()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Szukaj", type="primary", use_container_width=True):
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
                        timeout=5
                    ).json()
                    if geo_res and len(geo_res) > 0:
                        st.session_state.miasto_nazwa = geo_res[0].get("local_names", {}).get("pl", geo_res[0]["name"])
                        st.session_state.lat = geo_res[0]["lat"]
                        st.session_state.lon = geo_res[0]["lon"]
                        st.session_state.kraj = geo_res[0].get("country", "")
                        st.rerun()
                    else:
                        st.error("Nie znaleziono takiego miasta.")
                except Exception as e:
                    st.error(f"Błąd wyszukiwania: {e}")

    with col2:
        if st.button("Odśwież", use_container_width=True):
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
            (position) => {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;
                status.innerText = "Lokalizacja pobrana! Przeładowywanie...";
                const url = new URL(window.parent.location.href);
                url.searchParams.set('detect_lat', lat);
                url.searchParams.set('detect_lon', lon);
                window.parent.location.href = url.href;
            },
            (error) => {
                status.innerText = "Nie udało się pobrać pozycji (zezwól na dostęp w przeglądarce).";
            },
            { timeout: 10000, enableHighAccuracy: true }
        );
    }
    </script>
    """
    components.html(gps_button_html, height=75)

lat = st.session_state.lat
lon = st.session_state.lon
wybrane_miasto = st.session_state.miasto_nazwa
kraj = st.session_state.kraj

# ----------------- Pobieranie Danych Pogodowych -----------------
url_onecall = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=pl"

try:
    res_onecall = requests.get(url_onecall, timeout=8)
    
    if res_onecall.status_code == 200:
        data = res_onecall.json()
        curr = data.get("current", {})
        weather_obj = curr.get("weather", [{}])[0]
        
        temp_aktualna = round(curr.get("temp", 0))
        temp_odczuwalna = round(curr.get("feels_like", 0))
        opis = weather_obj.get("description", "").capitalize()
        ikona = weather_obj.get("icon", "01d")
        
        predkosc_wiatru = round(curr.get("wind_speed", 0) * 3.6)
        wilgotnosc = curr.get("humidity", 0)
        
        hourly_raw = data.get("hourly", [])
        opady_proc = int(hourly_raw[0].get("pop", 0) * 100) if hourly_raw else 0
        
        hours_list = hourly_raw[:10]
        daily_list = data.get("daily", [])[1:8]
    else:
        w_data = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=pl", timeout=8).json()
        f_data = requests.get(f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=pl", timeout=8).json()
        
        main = w_data.get("main", {})
        weather_obj = w_data.get("weather", [{}])[0]
        
        temp_aktualna = round(main.get("temp", 0))
        temp_odczuwalna = round(main.get("feels_like", 0))
        opis = weather_obj.get("description", "").capitalize()
        ikona = weather_obj.get("icon", "01d")
        predkosc_wiatru = round(w_data.get("wind", {}).get("speed", 0) * 3.6)
        wilgotnosc = main.get("humidity", 0)
        opady_proc = int(f_data.get("list", [{}])[0].get("pop", 0) * 100) if f_data.get("list") else 0
        
        hours_list = []
        for item in f_data.get("list", [])[:10]:
            hours_list.append({
                "dt": item["dt"],
                "temp": item["main"]["temp"],
                "feels_like": item["main"].get("feels_like", item["main"]["temp"]),
                "wind_speed": item.get("wind", {}).get("speed", 0),
                "humidity": item["main"]["humidity"],
                "pop": item.get("pop", 0),
                "weather": item["weather"]
            })
            
        daily_dict = {}
        for item in f_data.get("list", []):
            day_key = datetime.fromtimestamp(item["dt"]).strftime("%Y-%m-%d")
            if day_key not in daily_dict:
                daily_dict[day_key] = {
                    "dt": item["dt"],
                    "temp": {"day": item["main"]["temp"], "night": item["main"]["temp_min"]},
                    "feels_like": {"day": item["main"].get("feels_like", item["main"]["temp"])},
                    "wind_speed": item.get("wind", {}).get("speed", 0),
                    "humidity": item["main"]["humidity"],
                    "pop": item.get("pop", 0),
                    "weather": item["weather"]
                }
        daily_list = list(daily_dict.values())[1:8]

except Exception as e:
    st.error(f"Nie udało się połączyć z API: {e}")
    st.stop()

# ----------------- Formatowanie Daty i Dni -----------------
teraz = datetime.now()
dni_tygodnia = {
    0: "Poniedziałek", 1: "Wtorek", 2: "Środa",
    3: "Czwartek", 4: "Piątek", 5: "Sobota", 6: "Niedziela"
}
dni_skrot = {
    0: "Pn", 1: "Wt", 2: "Śr",
    3: "Cz", 4: "Pt", 5: "So", 6: "Nied"
}
miesiace = {
    1: "Stycznia", 2: "Lutego", 3: "Marca", 4: "Kwietnia", 5: "Maja", 6: "Czerwca",
    7: "Lipca", 8: "Sierpnia", 9: "Września", 10: "Października", 11: "Listopada", 12: "Grudnia"
}

data_napis = f"{dni_tygodnia[teraz.weekday()]}, {teraz.day} {miesiace[teraz.month]}"
godzina_napis = teraz.strftime("%H:%M")

# ----------------- Generowanie Kafelków Dziennych -----------------
daily_items_html = ""
for d in daily_list[:7]:
    d_date = datetime.fromtimestamp(d["dt"])
    skrot = f"{dni_skrot[d_date.weekday()]} {d_date.day}"
    pelna_data = f"{dni_tygodnia[d_date.weekday()]}, {d_date.day} {miesiace[d_date.month]}"
    
    weather_info = d.get("weather", [{}])[0]
    d_ico = weather_info.get("icon", "01d")
    d_desc = weather_info.get("description", "").capitalize()
    
    t_obj = d.get("temp", {})
    t_day = round(t_obj.get("day", t_obj if isinstance(t_obj, (int, float)) else 0))
    t_night = round(t_obj.get("night", t_day - 3))
    
    f_obj = d.get("feels_like", {})
    f_day = round(f_obj.get("day", t_day) if isinstance(f_obj, dict) else f_obj)
    
    d_wind = round(d.get("wind_speed", predkosc_wiatru / 3.6) * 3.6)
    d_hum = d.get("humidity", wilgotnosc)
    d_pop = int(d.get("pop", 0) * 100)
    
    daily_items_html += f"""
    <div class="day-col clickable-card" 
         data-date="{pelna_data}" 
         data-clock="Prognoza dzienna" 
         data-temp="{t_day}" 
         data-feels="{f_day}" 
         data-desc="{d_desc}" 
         data-icon="{d_ico}" 
         data-wind="{d_wind}" 
         data-hum="{d_hum}" 
         data-pop="{d_pop}">
        <div class="day-name">{skrot}</div>
        <img class="day-icon" src="https://openweathermap.org/img/wn/{d_ico}@2x.png" alt="ikona">
        <div class="day-temp-main">{t_day}°C</div>
        <div class="day-temp-sub">{t_night}°C</div>
    </div>
    """

# ----------------- Generowanie Kafelków Godzinowych -----------------
hourly_items_html = ""
for h in hours_list[:6]:
    h_date = datetime.fromtimestamp(h["dt"])
    h_time = h_date.strftime("%H:%M")
    h_pelna_data = f"{dni_tygodnia[h_date.weekday()]}, {h_date.day} {miesiace[h_date.month]}"
    
    w_info = h.get("weather", [{}])[0]
    h_ico = w_info.get("icon", "01d")
    h_desc = w_info.get("description", "").capitalize()
    
    h_temp = round(h.get("temp", 0))
    h_feels = round(h.get("feels_like", h_temp))
    h_wind = round(h.get("wind_speed", predkosc_wiatru / 3.6) * 3.6)
    h_hum = h.get("humidity", 0)
    h_pop = int(h.get("pop", 0) * 100)
    
    hourly_items_html += f"""
    <div class="hour-col clickable-card" 
         data-date="{h_pelna_data}" 
         data-clock="{h_time}" 
         data-temp="{h_temp}" 
         data-feels="{h_feels}" 
         data-desc="{h_desc}" 
         data-icon="{h_ico}" 
         data-wind="{h_wind}" 
         data-hum="{h_hum}" 
         data-pop="{h_pop}">
        <div class="hour-time">{h_time}</div>
        <img class="hour-icon" src="https://openweathermap.org/img/wn/{h_ico}@2x.png" alt="ikona">
        <div class="hour-temp">{h_temp}°C</div>
        <div class="hour-hum">💧 {h_hum}%</div>
    </div>
    """

# ----------------- Szablon Dashboardu (HTML + CSS + Leaflet OSM) -----------------
dashboard_html = f"""
<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
    * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }}
    html, body {{
        width: 100%;
        height: 100%;
        overflow: hidden;
        background: #cfe2f3;
    }}
    .app-container {{
        width: 100%;
        height: 100%;
        background: #cfe2f3;
        padding: 12px 16px;
        display: flex;
        flex-direction: column;
    }}
    .app-header {{
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
    }}
    .dashboard-grid {{
        display: grid;
        grid-template-columns: 1.4fr 1fr;
        gap: 16px;
        flex: 1;
        min-height: 0;
    }}
    
    /* LEWY KAFELEK - GŁÓWNA POGODA Z DYNAMICZNĄ TAPETĄ */
    .hero-card {{
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
        transition: background-image 0.4s ease-in-out;
        overflow: hidden;
    }}
    .hero-top-row {{
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        z-index: 2;
    }}
    .hero-city {{
        font-size: clamp(22px, 2vw, 32px);
        font-weight: 900;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        text-shadow: 0 2px 8px rgba(0,0,0,0.5);
    }}
    .hero-date {{
        font-size: clamp(13px, 0.95vw, 16px);
        opacity: 0.95;
        margin-top: 2px;
        text-shadow: 0 2px 6px rgba(0,0,0,0.4);
    }}
    .hero-clock {{
        font-size: clamp(20px, 1.6vw, 26px);
        font-weight: 700;
        margin-top: 3px;
        text-shadow: 0 2px 6px rgba(0,0,0,0.4);
    }}
    .btn-reset {{
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
    }}
    .btn-reset:hover {{
        background: rgba(15, 23, 42, 0.65);
    }}
    .hero-body {{
        display: flex;
        align-items: center;
        justify-content: flex-end;
        margin: auto 0;
        padding: 0.5vh 0;
        z-index: 2;
    }}
    .hero-temp-block {{
        text-align: right;
        padding-right: 1.5vw;
    }}
    .hero-temp-main {{
        font-size: clamp(58px, 6.2vw, 92px);
        font-weight: 800;
        line-height: 1;
        text-shadow: 0 4px 14px rgba(0,0,0,0.5);
    }}
    .hero-feels {{
        font-size: clamp(14px, 1.05vw, 18px);
        opacity: 0.95;
        margin-bottom: 8px;
        text-shadow: 0 2px 6px rgba(0,0,0,0.4);
    }}
    .hero-conditions {{
        font-size: clamp(18px, 1.4vw, 24px);
        font-weight: 800;
        margin-bottom: 8px;
        text-shadow: 0 2px 8px rgba(0,0,0,0.5);
    }}
    .hero-subdetails {{
        font-size: clamp(13px, 1vw, 16px);
        opacity: 0.95;
        line-height: 1.45;
        text-shadow: 0 2px 6px rgba(0,0,0,0.4);
    }}

    /* INTERAKTYWNE KAFELKI */
    .clickable-card {{
        cursor: pointer;
        border-radius: 14px;
        padding: 6px 6px;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        user-select: none;
    }}
    .clickable-card:hover {{
        transform: translateY(-2px);
    }}
    .day-col.clickable-card:hover {{
        background: rgba(30, 41, 59, 0.08);
    }}
    .hour-col.clickable-card:hover {{
        background: #e2e8f0;
    }}
    .clickable-card.active-selected {{
        transform: scale(1.04);
    }}
    .day-col.clickable-card.active-selected,
    .hour-col.clickable-card.active-selected {{
        background: #0284c7 !important;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.35);
    }}
    .day-col.clickable-card.active-selected div,
    .hour-col.clickable-card.active-selected div {{
        color: white !important;
    }}

    /* DOLNY PASEK DNI */
    .daily-bar {{
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
    }}
    .day-col {{
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        gap: 2px;
    }}
    .day-name {{
        font-size: clamp(13px, 1.05vw, 16px);
        font-weight: 800;
        color: #1e293b;
    }}
    .day-icon {{
        width: clamp(34px, 3vw, 48px);
        height: clamp(34px, 3vw, 48px);
    }}
    .day-temp-main {{
        font-size: clamp(15px, 1.2vw, 19px);
        font-weight: 800;
        color: #0f172a;
    }}
    .day-temp-sub {{
        font-size: clamp(12px, 0.95vw, 14px);
        font-weight: 600;
        color: #64748b;
    }}

    /* PRAWA STRONA */
    .right-column {{
        display: flex;
        flex-direction: column;
        gap: 12px;
        height: 100%;
        min-height: 0;
    }}

    /* KAFELEK GODZINOWY */
    .hourly-card {{
        background: #f8fafc;
        border-radius: 24px;
        padding: 1.6vh 1.4vw;
        box-shadow: 0 8px 20px rgba(0,0,0,0.06);
        flex-shrink: 0;
    }}
    .hourly-row {{
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}
    .hour-col {{
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        gap: 2px;
    }}
    .hour-time {{
        font-size: clamp(12px, 0.95vw, 15px);
        color: #475569;
        font-weight: 700;
    }}
    .hour-icon {{
        width: clamp(34px, 2.8vw, 46px);
        height: clamp(34px, 2.8vw, 46px);
    }}
    .hour-temp {{
        font-size: clamp(15px, 1.2vw, 19px);
        font-weight: 800;
        color: #0f172a;
    }}
    .hour-hum {{
        font-size: clamp(12px, 0.9vw, 14px);
        color: #0284c7;
        font-weight: 700;
    }}

    /* KAFELEK Z MAPĄ */
    .map-card {{
        background: #f8fafc;
        border-radius: 24px;
        padding: 1.6vh 1.4vw;
        box-shadow: 0 8px 20px rgba(0,0,0,0.06);
        flex: 1;
        display: flex;
        flex-direction: column;
        min-height: 0;
    }}
    .card-title {{
        font-size: clamp(17px, 1.3vw, 21px);
        font-weight: 800;
        color: #0f172a;
    }}
    #map {{
        width: 100%;
        flex: 1;
        min-height: 120px;
        border-radius: 16px;
        margin-top: 8px;
        border: 1px solid #cbd5e1;
        z-index: 1;
    }}
    .map-scale {{
        height: 7px;
        background: linear-gradient(to right, #38bdf8, #22c55e, #eab308, #ef4444);
        border-radius: 4px;
        margin-top: 8px;
        flex-shrink: 0;
    }}
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
        <!-- LEWA STRONA: POGODA GŁÓWNA Z DYNAMICZNĄ TAPETĄ -->
        <div class="hero-card" id="hero-card">
            <div class="hero-top-row">
                <div>
                    <div class="hero-city">{wybrane_miasto.upper()}, {kraj.upper()}</div>
                    <div class="hero-date" id="hero-date">{data_napis}</div>
                    <div class="hero-clock" id="hero-clock">{godzina_napis}</div>
                </div>
                <button class="btn-reset" id="btn-reset" onclick="resetToCurrent()">↺ Teraz</button>
            </div>

            <div class="hero-body">
                <div class="hero-temp-block">
                    <div class="hero-temp-main" id="hero-temp">{temp_aktualna}°C</div>
                    <div class="hero-feels" id="hero-feels">(odczuwalna {temp_odczuwalna}°C)</div>
                    <div class="hero-conditions" id="hero-desc">{opis}</div>
                    <div class="hero-subdetails" id="hero-subdetails">
                        Wiatr: {predkosc_wiatru} km/h<br>
                        Wilgotność: {wilgotnosc}%<br>
                        Opady: {opady_proc}%
                    </div>
                </div>
            </div>

            <div class="daily-bar">
                {daily_items_html}
            </div>
        </div>

        <!-- PRAWA STRONA: GODZINOWA + MAPA -->
        <div class="right-column">
            <div class="hourly-card">
                <div class="hourly-row">
                    {hourly_items_html}
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
    // Bezpiecznie przekazany słownik grafik w formacie JSON
    const wallpapers = {wallpapers_json};

    function setHeroBackground(icon) {{
        const url = wallpapers[icon] || wallpapers['02d'] || '';
        const hero = document.getElementById('hero-card');
        if (url) {{
            hero.style.background = `linear-gradient(rgba(15, 23, 42, 0.40), rgba(15, 23, 42, 0.65)), url('${{url}}') center/cover no-repeat`;
        }} else {{
            hero.style.background = `linear-gradient(135deg, #1e293b 0%, #0f172a 100%)`;
        }}
    }}

    const initialWeather = {{
        date: "{data_napis}",
        clock: "{godzina_napis}",
        temp: "{temp_aktualna}",
        feels: "{temp_odczuwalna}",
        desc: "{opis}",
        icon: "{ikona}",
        wind: "{predkosc_wiatru}",
        hum: "{wilgotnosc}",
        pop: "{opady_proc}"
    }};

    // Ustawienie początkowej tapety
    setHeroBackground(initialWeather.icon);

    const allCards = document.querySelectorAll('.clickable-card');
    const btnReset = document.getElementById('btn-reset');

    function updateHeroView(data) {{
        document.getElementById('hero-date').innerText = data.date;
        document.getElementById('hero-clock').innerText = data.clock;
        document.getElementById('hero-temp').innerText = data.temp + '°C';
        document.getElementById('hero-feels').innerText = '(odczuwalna ' + data.feels + '°C)';
        document.getElementById('hero-desc').innerText = data.desc;
        document.getElementById('hero-subdetails').innerHTML = 
            'Wiatr: ' + data.wind + ' km/h<br>' +
            'Wilgotność: ' + data.hum + '%<br>' +
            'Opady: ' + data.pop + '%';
        setHeroBackground(data.icon);
    }}

    allCards.forEach(card => {{
        card.addEventListener('click', function() {{
            allCards.forEach(c => c.classList.remove('active-selected'));
            this.classList.add('active-selected');

            const itemData = {{
                date: this.getAttribute('data-date'),
                clock: this.getAttribute('data-clock'),
                temp: this.getAttribute('data-temp'),
                feels: this.getAttribute('data-feels'),
                desc: this.getAttribute('data-desc'),
                icon: this.getAttribute('data-icon'),
                wind: this.getAttribute('data-wind'),
                hum: this.getAttribute('data-hum'),
                pop: this.getAttribute('data-pop')
            }};

            updateHeroView(itemData);
            btnReset.style.display = 'block';
        }});
    }});

    function resetToCurrent() {{
        allCards.forEach(c => c.classList.remove('active-selected'));
        updateHeroView(initialWeather);
        btnReset.style.display = 'none';
    }}

    var map = L.map('map', {{ zoomControl: false, attributionControl: false }}).setView([{lat}, {lon}], 7);
    
    L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
        maxZoom: 19
    }}).addTo(map);

    L.tileLayer('https://tile.openweathermap.org/map/clouds_new/{{z}}/{{x}}/{{y}}.png?appid={API_KEY}', {{
        maxZoom: 19,
        opacity: 0.55
    }}).addTo(map);

    var marker = L.circleMarker([{lat}, {lon}], {{
        radius: 7,
        fillColor: "#ef4444",
        color: "#ffffff",
        weight: 2,
        opacity: 1,
        fillOpacity: 0.95
    }}).addTo(map);
    
    marker.bindTooltip("<b>{wybrane_miasto}</b>", {{ permanent: true, direction: 'top', offset: [0, -6] }}).openTooltip();

    setTimeout(function() {{
        map.invalidateSize();
    }}, 250);

    window.addEventListener('resize', function() {{
        map.invalidateSize();
    }});
</script>

</body>
</html>
"""

# Główny dashboard pogodowy
components.html(dashboard_html, height=820, scrolling=False)
