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
    try:
        with open('sehirler.json', 'r', encoding='utf-8') as f:
            return json.load(f)['oyun_verisi']
    except:
        return []

sehirler = load_data()

# --- 3. GÜVENLİ VİDEO OYNATICI (KOPYA ENGELLEYİCİ) ---
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

# --- 4. ANA YAPI ---
st.set_page_config(page_title="Pito Maraton", layout="wide")

# Liderlik Tablosu (Sidebar)
with st.sidebar:
    st.header("🏆 Yarışma Kürsüsü")
    try:
        skorlar = supabase.table("sehir_tahmin_skor").select("*").order("puan", desc=True).limit(5).execute()
        for i, s in enumerate(skorlar.data):
            st.write(f"{i+1}. {s['ogrenci_adi']} - {s['puan']} XP")
    except: pass
    
    st.write("---")
    with st.expander("🔐 Öğretmen Girişi"):
        sifre = st.text_input("Şifre:", type="password")
        admin_modu = (sifre == "pito123")

# --- 5. ÖĞRETMEN PANELİ ---
if admin_modu:
    st.subheader("👨‍🏫 Oyun Kurucu Paneli")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔴 OYUNU BAŞLAT / YENİ ŞEHİR", use_container_width=True):
            yeni = random.choice(sehirler)
            # Veritabanını 'aktif' yap ve yeni şehri ata
            supabase.table("oyun_odasi").update({
                "aktif_sehir_id": yeni['id'],
                "durum": "aktif"
            }).eq("id", 1).execute()
            st.success("Oyun başlatıldı! Öğrenciler şu an videoyu görüyor.")

    with col2:
        if st.button("⚪ LOBİYE DÖN (DURDUR)", use_container_width=True):
            # Durumu bekleme yap
            supabase.table("oyun_odasi").update({
                "durum": "bekleme",
                "aktif_sehir_id": None
            }).eq("id", 1).execute()
            st.warning("Oyun durduruldu, öğrenciler lobiye alındı.")

# --- 6. ÖĞRENCİ PANELİ ---
else:
    if 'ogrenci_ismi' not in st.session_state:
        st.session_state.ogrenci_ismi = st.text_input("Yarışmacı Adın:", placeholder="İsmini yaz ve bekle...")
        st.stop()

    # SÜREKLİ KONTROL: Veritabanı durumunu oku
    res = supabase.table("oyun_odasi").select("*").eq("id", 1).execute()
    oda = res.data[0]

    # KONTROL: Eğer öğretmen henüz 'aktif' yapmadıysa
    if oda['durum'] != "aktif":
        st.title(f"👋 Selam {st.session_state.ogrenci_ismi}!")
        st.markdown("## ⏳ Bekleme Odasındasın")
        st.info("Pito: 'Diğer arkadaşların da gelmesini bekliyoruz. Öğretmen oyunu başlattığında maraton otomatik açılacak!'")
        
        # Kahoot gibi isimleri ekranda döndürebiliriz ama şimdilik manuel yenileme:
        if st.button("Sıradaki Tur Başladı mı? Kontrol Et 🔄"):
            st.rerun()
        st.stop() # BURADAN AŞAĞIYA GEÇİŞ YOK!

    # --- BURASI SADECE ÖĞRETMEN BAŞLATINCA ÇALIŞIR ---
    if 'su_anki_tur' not in st.session_state or st.session_state.su_anki_tur != oda['aktif_sehir_id']:
        st.session_state.su_anki_tur = oda['aktif_sehir_id']
        st.session_state.cevap_verildi = False
        hedef = next(s for s in sehirler if s['id'] == oda['aktif_sehir_id'])
        
        # Şıklar her öğrenci için farklı sırada oluşsun
        dogru_metin = f"{hedef['sehir']}, {hedef['ulke']}"
        yanlislar = random.sample([f"{s['sehir']}, {s['ulke']}" for s in sehirler if s['sehir'] != hedef['sehir']], 3)
        st.session_state.siklar = yanlislar + [dogru_metin]
        random.shuffle(st.session_state.siklar)
        st.session_state.zaman_basla = time.time()

    if not st.session_state.cevap_verildi:
        hedef = next(s for s in sehirler if s['id'] == oda['aktif_sehir_id'])
        st.subheader(f"📍 Dedektif {st.session_state.ogrenci_ismi}, Burası Neresi?")
        pito_guvenli_video(hedef['video_id'], hedef['baslangic_sn'])
        
        st.write("---")
        c1, c2 = st.columns(2)
        secim = None
        with c1:
            if st.button(st.session_state.siklar[0], use_container_width=True, key="x1"): secim = st.session_state.siklar[0]
            if st.button(st.session_state.siklar[1], use_container_width=True, key="x2"): secim = st.session_state.siklar[1]
        with c2:
            if st.button(st.session_state.siklar[2], use_container_width=True, key="x3"): secim = st.session_state.siklar[2]
            if st.button(st.session_state.siklar[3], use_container_width=True, key="x4"): secim = st.session_state.siklar[3]

        if secim:
            dogru_cevap = f"{hedef['sehir']}, {hedef['ulke']}"
            if secim == dogru_cevap:
                gecen = time.time() - st.session_state.zaman_basla
                bonus = max(0, int(20 - gecen))
                toplam = 20 + bonus
                st.balloons()
                st.success(f"✅ BİLDİN! {toplam} XP (Hız Bonusu: {bonus})")
                supabase.rpc('artir_sehir_puani', {'ad': st.session_state.ogrenci_ismi, 'ek_puan': toplam}).execute()
            else:
                st.error(f"❌ YANLIŞ! Doğru cevap: {dogru_cevap}")
            st.session_state.cevap_verildi = True
            st.rerun()
    else:
        st.info("🎯 Cevabını verdin. Öğretmenin yeni şehri seçmesini bekliyoruz...")
        if st.button("Yeni Şehir Geldi mi? 🔄"): st.rerun()
