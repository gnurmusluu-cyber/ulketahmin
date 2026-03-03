import streamlit as st
from supabase import create_client
import json
import random
import time
import streamlit.components.v1 as components

# --- 1. SUPABASE BAĞLANTISI ---
URL = "https://whtawpamszuyemebwuvu.supabase.co"
KEY = "sb_publishable_pxXYAqzI8mf70h2YHNF1Xg_J7x2vZJU"
supabase = create_client(URL, KEY)

# --- 2. VERİ YÜKLEME ---
def load_data():
    with open('sehirler.json', 'r', encoding='utf-8') as f:
        return json.load(f)['oyun_verisi']

sehirler = load_data()

# --- 3. GÜVENLİ VİDEO OYNATICI ---
def pito_guvenli_video(video_id, start_time):
    embed_url = f"https://www.youtube.com/embed/{video_id}?start={start_time}&autoplay=1&controls=0&rel=0&modestbranding=1&disablekb=1"
    html_kodu = f"""
    <div style="position: relative; width: 100%; height: 450px; overflow: hidden; border-radius: 15px; border: 3px solid #00FFCC; pointer-events: none;">
        <div style="position: absolute; top: 0; left: 0; width: 100%; height: 60px; background-color: black; z-index: 20;"></div>
        <div style="position: absolute; bottom: 0; right: 0; width: 150px; height: 50px; background-color: black; z-index: 20;"></div>
        <iframe width="100%" height="550" src="{embed_url}" frameborder="0" allow="autoplay; encrypted-media" style="position: absolute; top: -50px; left: 0;"></iframe>
    </div>
    """
    components.html(html_kodu, height=460)

# --- 4. ŞIKLARI HAZIRLA ---
def siklari_hazirla(dogru_cevap_obj):
    dogru_metin = f"{dogru_cevap_obj['sehir']}, {dogru_cevap_obj['ulke']}"
    digerleri = [f"{s['sehir']}, {s['ulke']}" for s in sehirler if s['sehir'] != dogru_cevap_obj['sehir']]
    yanlislar = random.sample(digerleri, 3)
    hepsi = yanlislar + [dogru_metin]
    random.shuffle(hepsi)
    return hepsi

# --- 5. ANA EKRAN VE YÖNETİM ---
st.set_page_config(page_title="Pito CityGuesser", layout="wide")

# Liderlik Tablosu
with st.sidebar:
    st.header("🏆 Skor Tabelası")
    try:
        skorlar = supabase.table("sehir_tahmin_skor").select("*").order("puan", desc=True).limit(10).execute()
        for i, s in enumerate(skorlar.data):
            st.write(f"**{i+1}. {s['ogrenci_adi']}** — `{s['puan']} XP`")
    except: st.write("Puanlar yükleniyor...")
    
    st.write("---")
    with st.expander("🔐 Öğretmen Girişi"):
        sifre = st.text_input("Şifre:", type="password")
        is_admin = (sifre == "pito123")

# --- ÖĞRETMEN PANELİ ---
if is_admin:
    st.subheader("👨‍🏫 Maraton Kontrol Merkezi")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 OYUNU BAŞLAT / SIRADAKİ", use_container_width=True):
            yeni = random.choice(sehirler)
            # HEM durumu aktif yapıyoruz HEM yeni şehir ID'sini gönderiyoruz
            supabase.table("oyun_odasi").update({
                "aktif_sehir_id": yeni['id'],
                "durum": "aktif"
            }).eq("id", 1).execute()
            st.success("Oyun BAŞLATILDI!")
            
    with col2:
        if st.button("🛑 OYUNU DURDUR", use_container_width=True):
            # Durumu bekleme yapıyoruz, ID'yi siliyoruz
            supabase.table("oyun_odasi").update({
                "durum": "bekleme",
                "aktif_sehir_id": None
            }).eq("id", 1).execute()
            st.warning("Oyun DURDURULDU!")

# --- ÖĞRENCİ PANELİ ---
else:
    if 'ogrenci_ismi' not in st.session_state:
        st.session_state.ogrenci_ismi = st.text_input("Adın Soyadın:", placeholder="Giriş yapmak için yaz...")
        st.stop()

    # Supabase'den oda verisini çek
    oda_data = supabase.table("oyun_odasi").select("*").eq("id", 1).execute().data[0]
    
    # KONTROL: Eğer durum 'aktif' değilse bekleme odasını göster
    if oda_data['durum'] != "aktif" or oda_data['aktif_sehir_id'] is None:
        st.title(f"👋 Selam {st.session_state.ogrenci_ismi}!")
        st.markdown("### ⏳ Bekleme Odası")
        st.info("Pito: 'Öğretmenin oyunu başlatmasını bekliyoruz. Ekranını kapatma, her an başlayabilir!'")
        
        if st.button("Kontrol Et 🔄"):
            st.rerun()
        st.stop() # Kodun geri kalanını çalıştırmayı burada keser!

    # --- BURASI SADECE OYUN AKTİFKEN ÇALIŞIR ---
    if 'su_anki_tur' not in st.session_state or st.session_state.su_anki_tur != oda_data['aktif_sehir_id']:
        st.session_state.su_anki_tur = oda_data['aktif_sehir_id']
        st.session_state.cevap_verildi = False
        hedef = next(s for s in sehirler if s['id'] == oda_data['aktif_sehir_id'])
        st.session_state.siklar = siklari_hazirla(hedef)
        st.session_state.zamanlayici = time.time()

    if not st.session_state.cevap_verildi:
        hedef = next(s for s in sehirler if s['id'] == oda_data['aktif_sehir_id'])
        st.subheader(f"📍 Dedektif {st.session_state.ogrenci_ismi}, Neredesin?")
        
        pito_guvenli_video(hedef['video_id'], hedef['baslangic_sn'])
        
        st.write("---")
        c1, c2 = st.columns(2)
        secilen = None
        with c1:
            if st.button(st.session_state.siklar[0], use_container_width=True, key="b1"): secilen = st.session_state.siklar[0]
            if st.button(st.session_state.siklar[1], use_container_width=True, key="b2"): secilen = st.session_state.siklar[1]
        with c2:
            if st.button(st.session_state.siklar[2], use_container_width=True, key="b3"): secilen = st.session_state.siklar[2]
            if st.button(st.session_state.siklar[3], use_container_width=True, key="b4"): secilen = st.session_state.siklar[3]

        if secilen:
            dogru_cevap = f"{hedef['sehir']}, {hedef['ulke']}"
            if secilen == dogru_cevap:
                gecen = time.time() - st.session_state.zamanlayici
                bonus = max(0, int(20 - gecen))
                toplam = 20 + bonus
                st.balloons()
                st.success(f"✅ HARİKA! {toplam} XP! (Hız: {int(gecen)}sn)")
                supabase.rpc('artir_sehir_puani', {'ad': st.session_state.ogrenci_ismi, 'ek_puan': toplam}).execute()
            else:
                st.error(f"❌ Yanlış! Doğru cevap: {dogru_cevap}")
            
            st.session_state.cevap_verildi = True
            st.rerun()
    else:
        st.info("🎯 Cevabın alındı! Diğer tur için öğretmeni bekle...")
        if st.button("Sıradaki Geldi mi? 🔄"): st.rerun()
