import streamlit as st
from supabase import create_client
import json
import random
import time

# --- 1. SUPABASE BAĞLANTISI ---
# Kendi Pito Python Akademi proje bilgilerini buraya gir
URL = "https://whtawpamszuyemebwuvu.supabase.co"
KEY = "sb_publishable_pxXYAqzI8mf70h2YHNF1Xg_J7x2vZJU"
supabase = create_client(URL, KEY)

# --- 2. VERİ YÜKLEME ---
def load_data():
    try:
        with open('sehirler.json', 'r', encoding='utf-8') as f:
            return json.load(f)['oyun_verisi']
    except FileNotFoundError:
        st.error("Hata: 'sehirler.json' dosyası bulunamadı!")
        return []

sehirler = load_data()

# --- 3. SAYFA AYARLARI & STİL ---
st.set_page_config(page_title="Pito CityGuesser", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stButton>button { width: 100%; border-radius: 20px; background-color: #00FFCC; color: black; font-weight: bold; }
    .stVideo { border: 3px solid #00FFCC; border-radius: 15px; }
    .puan-karti { padding: 10px; border-radius: 10px; border: 1px solid #333; margin-bottom: 5px; background: #161b22; }
    </style>
""", unsafe_allow_html=True)

# --- 4. OTURUM YÖNETİMİ ---
if 'sorulanlar' not in st.session_state:
    st.session_state.sorulanlar = []

# --- 5. ANA BAŞLIK ---
st.title("🌍 Pito CityGuesser: Şehir Dedektifleri")

# Rol Seçimi
rol = st.sidebar.radio("Sistem Rolü", ["Öğrenci", "Öğretmen (GM)"])

# --- 6. ÖĞRETMEN (YÖNETİM) MODU ---
if rol == "Öğretmen (GM)":
    st.subheader("👨‍🏫 Oyun Kurucu Paneli")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        kalanlar = [s for s in sehirler if s['id'] not in st.session_state.sorulanlar]
        st.write(f"Kalan Şehir Sayısı: **{len(kalanlar)}**")
        
        if st.button("🎲 RASTGELE ŞEHİR SEÇ VE GÖNDER"):
            if kalanlar:
                yeni = random.choice(kalanlar)
                st.session_state.sorulanlar.append(yeni['id'])
                
                # Supabase'i güncelle
                supabase.table("oyun_odasi").update({
                    "aktif_sehir_id": yeni['id'],
                    "durum": "aktif",
                    "bitis_zamani": time.time() + 60 # 60 saniye süre
                }).eq("id", 1).execute()
                
                st.success(f"Yeni hedef gönderildi: {yeni['sehir']}")
            else:
                st.warning("Tüm şehirler bitti! Listeyi sıfırlamak için sayfayı yenile.")

    with col2:
        st.subheader("🏆 Anlık Skorbord")
        skor_data = supabase.table("sehir_tahmin_skor").select("*").order("puan", desc=True).limit(5).execute()
        for s in skor_data.data:
            st.markdown(f"<div class='puan-karti'>🏅 {s['ogrenci_adi']}: {s['puan']} XP</div>", unsafe_allow_html=True)

# --- 7. ÖĞRENCİ (OYUN) MODU ---
else:
    if 'ogrenci_ismi' not in st.session_state:
        st.session_state.ogrenci_ismi = st.text_input("Adın Soyadın:", placeholder="Örn: Gamzenur Muslu")
        st.stop()

    # Supabase'den o anki aktif oyunu çek
    oda = supabase.table("oyun_odasi").select("*").eq("id", 1).execute().data[0]
    
    if oda['aktif_sehir_id'] and oda['durum'] == "aktif":
        hedef = next(s for s in sehirler if s['id'] == oda['aktif_sehir_id'])
        
        st.subheader(f"📍 Dedektif {st.session_state.ogrenci_ismi}, Neredesin?")
        
        # VİDEO OYNATICI
        video_url = f"https://www.youtube.com/watch?v={hedef['video_id']}&t={hedef['baslangic_sn']}s"
        st.video(video_url)
        
        # TAHMİN ALANI
        st.write("---")
        tahmin_listesi = sorted([s['sehir'] for s in sehirler])
        tahmin = st.selectbox("Şehri Tahmin Et:", ["Seçiniz..."] + tahmin_listesi)
        
        if st.button("Tahminimi Onayla"):
            if tahmin == hedef['sehir']:
                st.balloons()
                st.success("Pito: 'Mükemmel! Doğru cevap.'")
                # Puanı RPC ile artır
                supabase.rpc('artir_sehir_puani', {
                    'ad': st.session_state.ogrenci_ismi, 
                    'ek_puan': 20
                }).execute()
            else:
                st.error("Pito: 'Hata! Bu mimari başka bir yere ait, tabelaları incele.'")
    else:
        st.info("Pito: 'Yeni bir şehrin gelmesini bekliyorum. Hazır ol!'")
        if st.button("Ekranı Yenile"):
            st.rerun()

# Otomatik Yenileme İpucu
st.sidebar.write("---")
st.sidebar.caption("Not: Yeni şehir gelmezse sayfayı manuel yenileyin.")
