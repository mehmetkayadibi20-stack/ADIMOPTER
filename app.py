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

@app.route('/api/ucus-izni-formu', methods=['POST'])
def ucus_izni_formu_kaydet():
    data = request.json

    form_data = {
        # Başvuru Sahibi
        "basvuru_sahibi": data.get("basvuru_sahibi", ""),
        "adres": data.get("adres", ""),
        "telefon": data.get("telefon", ""),
        "eposta": data.get("eposta", ""),
        "ucus_amaci": data.get("ucus_amaci", ""),

        # İHA ve Pilot
        "sigorta_police_no": data.get("sigorta_police_no", ""),
        "iha_kayit_no": data.get("iha_kayit_no", ""),
        "iha_tipi": data.get("iha_tipi", ""),
        "pilot_lisans_no": data.get("pilot_lisans_no", ""),

        # Uçuş Zamanı
        "ucus_tarihi_baslangic": data.get("ucus_tarihi_baslangic", ""),
        "ucus_tarihi_bitis": data.get("ucus_tarihi_bitis", ""),
        "ucus_saati_baslangic": data.get("ucus_saati_baslangic", ""),
        "ucus_saati_bitis": data.get("ucus_saati_bitis", ""),
        "ucus_irtifasi": data.get("ucus_irtifasi", ""),

        # Bölge
        "il": data.get("il", ""),
        "ilce": data.get("ilce", ""),
        "bolge": data.get("bolge", ""),

        # Koordinatlar
        "enlem_derece": data.get("enlem_derece", ""),
        "enlem_dakika": data.get("enlem_dakika", ""),
        "enlem_saniye": data.get("enlem_saniye", ""),
        "boylam_derece": data.get("boylam_derece", ""),
        "boylam_dakika": data.get("boylam_dakika", ""),
        "boylam_saniye": data.get("boylam_saniye", ""),

        # Alan Tanımı
        "alan_turu": data.get("alan_turu", ""),
        "alan_yaricap": data.get("alan_yaricap", ""),
        "kalkis_adresi": data.get("kalkis_adresi", ""),
        "inis_adresi": data.get("inis_adresi", ""),

        # Onay
        "onay_ad_soyad": data.get("onay_ad_soyad", ""),
        "onay_unvan": data.get("onay_unvan", ""),
        "onay_tarih": data.get("onay_tarih", ""),
    }

    return jsonify({"status": "success", "message": "Form başarıyla kaydedildi.", "data": form_data})

@app.route('/api/analyze', methods=['POST'])
def analyze_location():
    data = request.json
    lat = float(data['lat'])
    lon = float(data['lon'])

    lat_dms = convert_to_dms(lat, 'lat')
    lon_dms = convert_to_dms(lon, 'lon')
    address = get_address(lat, lon)

    # Hava Durumu (Open-Meteo API'sine geçirildi - API Key gerektirmez)
    try:
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        w_res = requests.get(weather_url, timeout=5)
        if w_res.status_code == 200:
            w_data = w_res.json().get('current_weather', {})
            sicaklik = f"{w_data.get('temperature', 'Hata')} °C"
            wind_kmh = w_data.get('windspeed', 0)
            ruzgar = f"{round(wind_kmh / 3.6, 2)} m/s"
        else:
            sicaklik = "Hata"
            ruzgar = "Hata"
    except Exception:
        sicaklik = "Bağlantı Hatası"
        ruzgar = "Bağlantı Hatası"

    # Yükseklik (Elevation) - Open-Meteo Elevation API
    try:
        elev_url = f"https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={lon}"
        e_res = requests.get(elev_url, timeout=5)
        if e_res.status_code == 200:
            elev_data = e_res.json().get('elevation', [])
            yukseklik = f"{elev_data[0]} m" if len(elev_data) > 0 else "Hata"
        else:
            yukseklik = "Hata"
    except Exception:
        yukseklik = "Bağlantı Hatası"

    response_data = {
        "dms": f"{lat_dms}, {lon_dms}",
        "address": address,
        "sicaklik": sicaklik,
        "ruzgar": ruzgar,
        "yukseklik": yukseklik,
        "nfz_status": "Manuel SHGM Kontrolü Gereklidir."
    }

    return jsonify(response_data)

if __name__ == '__main__':
    app.run(debug=True, port=5000)

# [AI Traceability]