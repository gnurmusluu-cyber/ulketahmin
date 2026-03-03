import streamlit as st
from supabase import create_client
import json
import random
import time
import streamlit.components.v1 as components
# --- 1. SUPABASE BAĞLANTISI ---
# Kendi Pito Python Akademi proje bilgilerini buraya gir
URL = "https://whtawpamszuyemebwuvu.supabase.co"
KEY = "sb_publishable_pxXYAqzI8mf70h2YHNF1Xg_J7x2vZJU"
supabase = create_client(URL, KEY)

# --- 2. VERİ YÜKLEME ---
def load_data():
    with open('sehirler.json', 'r', encoding='utf-8') as f:
        return json.load(f)['oyun_verisi']

sehirler = load_data()

# --- 3. ÖZEL VİDEO OYNATICI (BAŞLIK GİZLEME) ---
def pito_video_oynatici(video_id, start_time):
    embed_url = f"https://www.youtube.com/embed/{video_id}?start={start_time}&autoplay=1&controls=1&rel=0&modestbranding=1"
    html_kodu = f"""
    <div style="position: relative; width: 100%; height: 500px; overflow: hidden; border-radius: 15px; border: 3px solid #00FFCC;">
        <div style="position: absolute; top: 0; left: 0; width: 100%; height: 60px; background-color: black; z-index: 10;"></div>
        <iframe width="100%" height="500" src="{embed_url}" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen style="position: absolute; top: -50px; left: 0;"></iframe>
    </div>
    """
    components.html(html_kodu, height=500)

# --- 4. ŞIK OLUŞTURMA MANTIĞI ---
def siklari_hazirla(dogru_cevap_obj):
    dogru_metin = f"{dogru_cevap_obj['sehir']}, {dogru_cevap_obj['ulke']}"
    digerleri = [f"{s['sehir']}, {s['ulke']}" for s in sehirler if s['sehir'] != dogru_cevap_obj['sehir']]
    yanlislar = random.sample(digerleri, 3)
    hepsi = yanlislar + [dogru_metin]
    random.shuffle(hepsi)
    return hepsi

# --- 5. ANA EKRAN ---
st.title("🎮 Pito Kahoot: Şehir & Ülke Avcısı")

rol = st.sidebar.radio("Sistem Rolü", ["Öğrenci", "Öğretmen (GM)"])

if rol == "Öğretmen (GM)":
    st.subheader("👨‍🏫 Oyun Kurucu Paneli")
    if st.button("🎲 YENİ RASTGELE TUR BAŞLAT"):
        yeni = random.choice(sehirler)
        supabase.table("oyun_odasi").update({
            "aktif_sehir_id": yeni['id'],
            "durum": "aktif"
        }).eq("id", 1).execute()
        st.success(f"Yeni Tur: {yeni['sehir']} gönderildi!")

else:
    if 'ogrenci_ismi' not in st.session_state:
        st.session_state.ogrenci_ismi = st.text_input("Adın Soyadın:")
        st.stop()

    oda = supabase.table("oyun_odasi").select("*").eq("id", 1).execute().data[0]
    
    if oda['aktif_sehir_id']:
        hedef = next(s for s in sehirler if s['id'] == oda['aktif_sehir_id'])
        
        # Videoyu gizli başlıkla oynat
        pito_video_oynatici(hedef['video_id'], hedef['baslangic_sn'])
        
        # Şıkları oluştur (Sadece tur başında oluşturulması için session_state kullanalım)
        if 'mevcut_siklar' not in st.session_state or st.session_state.get('son_id') != hedef['id']:
            st.session_state.mevcut_siklar = siklari_hazirla(hedef)
            st.session_state.son_id = hedef['id']
            st.session_state.cevaplandi = False

        st.write("---")
        st.subheader("🧐 Sence burası neresi?")
        
        # Kahoot tarzı 4 şık
        col1, col2 = st.columns(2)
        secim = None
        
        with col1:
            if st.button(st.session_state.mevcut_siklar[0], key="btn0"): secim = st.session_state.mevcut_siklar[0]
            if st.button(st.session_state.mevcut_siklar[1], key="btn1"): secim = st.session_state.mevcut_siklar[1]
        with col2:
            if st.button(st.session_state.mevcut_siklar[2], key="btn2"): secim = st.session_state.mevcut_siklar[2]
            if st.button(st.session_state.mevcut_siklar[3], key="btn3"): secim = st.session_state.mevcut_siklar[3]

        if secim and not st.session_state.cevaplandi:
            dogru_cevap = f"{hedef['sehir']}, {hedef['ulke']}"
            if secim == dogru_cevap:
                st.balloons()
                st.success(f"BASARI! Doğru cevap: {dogru_cevap}")
                supabase.rpc('artir_sehir_puani', {'ad': st.session_state.ogrenci_ismi, 'ek_puan': 20}).execute()
            else:
                st.error(f"HATA! Maalesef yanlış. Doğru cevap: {dogru_cevap}")
            st.session_state.cevaplandi = True
    else:
        st.info("Pito: 'Yeni turu bekliyoruz...'")
