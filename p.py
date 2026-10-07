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
    /* Ustawienie koloru #cfe2f3 na całą aplikację oraz pasek boczny (Sidebar) */
    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] > div:first-child,
    section[data-testid="stSidebarContent"] {
        background-color: #cfe2f3 !important;
        background: #cfe2f3 !important;
    }

    /* Dopasowanie tła iframe z komponentem */
    iframe {
        background-color: #cfe2f3 !important;
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
        "wind": round(w_res.get("
