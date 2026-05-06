import os
from dotenv import load_dotenv # Bu satır mutlaka olmalı
from flask import Flask, render_template, request, jsonify
import requests

load_dotenv() # Bu satır .env içindeki verileri sisteme yükler
app = Flask(__name__)

# Değişken isminin .env içindekiyle BİREBİR aynı olduğundan emin ol
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
print(f"DEBUG - API KEY: {WEATHER_API_KEY}")

def convert_to_dms(deg, axis):
    direction = ('N' if deg >= 0 else 'S') if axis == 'lat' else ('E' if deg >= 0 else 'W')
    deg = abs(deg)
    d = int(deg)
    m = int((deg - d) * 60)
    s = round((deg - d - m/60) * 3600, 2)
    return f"{d}° {m}' {s}'' {direction}"

def get_address(lat, lon):
    url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=18&addressdetails=1"
    headers = {'User-Agent': 'AdimopterApp/1.0'}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            data = res.json()
            address = data.get('address', {})
            il = address.get('province', address.get('city', address.get('state', 'Bilinmiyor')))
            ilce = address.get('town', address.get('county', 'Bilinmiyor'))
            mahalle = address.get('suburb', address.get('neighbourhood', 'Bilinmiyor'))
            return f"{il}, {ilce}, {mahalle}"
    except:
        pass
    return "Adres Bulunamadı"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze_location():
    data = request.json
    lat = float(data['lat'])
    lon = float(data['lon'])

    lat_dms = convert_to_dms(lat, 'lat')
    lon_dms = convert_to_dms(lon, 'lon')
    address = get_address(lat, lon)

    # Hava Durumu
    weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric"
    w_res = requests.get(weather_url)
    
    # Yükseklik (Elevation)
    elev_url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}"
    e_res = requests.get(elev_url)

    response_data = {
        "dms": f"{lat_dms}, {lon_dms}",
        "address": address,
        "sicaklik": f"{w_res.json()['main']['temp']} °C" if w_res.status_code == 200 else "Hata",
        "ruzgar": f"{w_res.json()['wind']['speed']} m/s" if w_res.status_code == 200 else "Hata",
        "yukseklik": f"{e_res.json()['results'][0]['elevation']} m" if e_res.status_code == 200 else "Hata",
        "nfz_status": "Manuel SHGM Kontrolü Gereklidir."
    }

    return jsonify(response_data)

if __name__ == '__main__':
    app.run(debug=True, port=5000)