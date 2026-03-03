import streamlit as st
from supabase import create_client
import json
import random
import time
import streamlit.components.v1 as components

# --- 1. SUPABASE BAĞLANTISI ---
# Senin verdiğin güncel bilgilerle güncellendi
URL = "https://whtawpamszuyemebwuvu.supabase.co"
KEY = "sb_publishable_pxXYAqzI8mf70h2YHNF1Xg_J7x2vZJU"
supabase = create_client(URL, KEY)

# --- 2. VERİ YÜKLEME ---
def load_data():
    try:
        with open('sehirler.json', 'r', encoding='utf-8') as f:
            return json.load(f)['oyun_verisi']
    except Exception as e:
        st.error(f"JSON Yükleme Hatası: {e}")
        return []

sehirler = load_data()

# --- 3. ÖZEL VİDEO OYNATICI (BAŞLIK MASKELİ) ---
def pito_video_oynatici(video_id, start_time):
    embed_url = f"https://www.youtube.com/embed/{video_id}?start={start_time}&autoplay=1&controls=1&rel=0&modestbranding=1"
    html_kodu = f"""
    <div style="position: relative; width: 100%; height: 450px; overflow: hidden; border-radius: 15px; border: 3px solid #00FFCC;">
        <div style="position: absolute; top: 0; left: 0; width: 100%; height: 60px; background-color: black; z-index: 10;"></div>
        <iframe width="100%" height="450" src="{embed_url}" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen style="position: absolute; top: -50px; left: 0;"></iframe>
    </div>
    """
    components.html(html_kodu, height=450)

# --- 4. ŞIKLARI HAZIRLA ---
def siklari_hazirla(dogru_cevap_obj):
    dogru_metin = f"{dogru_cevap_obj['sehir']}, {dogru_cevap_obj['ulke']}"
    # Diğer tüm şehirlerden rastgele 3 tane seç
    digerleri = [f"{s['sehir']}, {s['ulke']}" for s in sehirler if s['sehir'] != dogru_cevap_obj['sehir']]
    yanlislar = random.sample(digerleri, min(len(digerleri), 3))
    hepsi = yanlislar + [dogru_metin]
    random.shuffle(hepsi)
    return hepsi

# --- 5. ANA PANEL ---
st.set_page_config(page_title="Pito CityGuesser", layout="wide")
st.title("🏁 Pito Maraton: Coğrafya Dedektifleri")

# Rol seçimi (Sadece öğretmen gizli panelden yönetir)
mod = st.sidebar.selectbox("Erişim Türü", ["Öğrenci Girişi", "Öğretmen Paneli"])

# --- ÖĞRETMEN PANELİ ---
if mod == "Öğretmen Paneli":
    st.subheader("👨‍🏫 Yarışma Yönetimi")
    st.write("Öğrenciler hazır olduğunda butona basarak rastgele bir şehir gönder.")
    
    if st.button("🎲 SIRADAKİ RASTGELE ŞEHRİ GÖNDER"):
        yeni_sehir = random.choice(sehirler)
        supabase.table("oyun_odasi").update({
            "aktif_sehir_id": yeni_sehir['id'],
            "durum": "aktif"
        }).eq("id", 1).execute()
        st.success(f"Yeni şehir gönderildi! (Doğru Cevap: {yeni_sehir['sehir']})")

    st.sidebar.write("---")
    st.sidebar.subheader("🏆 Liderlik Tablosu")
    try:
        skorlar = supabase.table("sehir_tahmin_skor").select("*").order("puan", desc=True).limit(10).execute()
        for s in skorlar.data:
            st.sidebar.write(f"⭐ {s['ogrenci_adi']}: {s['puan']} XP")
    except:
        st.sidebar.info("Henüz skor kaydı yok.")

# --- ÖĞRENCİ PANELİ ---
else:
    if 'ogrenci_ismi' not in st.session_state:
        st.session_state.ogrenci_ismi = st.text_input("Yarışmacı Adı:", placeholder="Adını yaz ve bekle...")
        st.stop()

    # Supabase'den oda verisini anlık çek
    try:
        oda = supabase.table("oyun_odasi").select("*").eq("id", 1).execute().data[0]
    except:
        st.warning("Oda verisi yüklenemedi. Veritabanında 'oyun_odasi' tablosunda ID=1 olan bir satır olduğundan emin ol.")
        st.stop()
    
    # Yeni bir şehre geçildiğini anlama mekanizması
    if 'mevcut_id' not in st.session_state or st.session_state.mevcut_id != oda['aktif_sehir_id']:
        st.session_state.mevcut_id = oda['aktif_sehir_id']
        st.session_state.cevap_verildi = False
        if oda['aktif_sehir_id']:
            hedef = next(s for s in sehirler if s['id'] == oda['aktif_sehir_id'])
            st.session_state.siklar = siklari_hazirla(hedef)

    if oda['aktif_sehir_id'] and not st.session_state.cevap_verildi:
        hedef = next(s for s in sehirler if s['id'] == oda['aktif_sehir_id'])
        st.subheader(f"📍 Neresi Burası {st.session_state.ogrenci_ismi}?")
        
        pito_video_oynatici(hedef['video_id'], hedef['baslangic_sn'])
        
        st.write("---")
        # 2x2 Şık Düzeni
        col1, col2 = st.columns(2)
        secim = None
        
        with col1:
            if st.button(st.session_state.siklar[0], use_container_width=True, key="c1"): secim = st.session_state.siklar[0]
            if st.button(st.session_state.siklar[1], use_container_width=True, key="c2"): secim = st.session_state.siklar[1]
        with col2:
            if st.button(st.session_state.siklar[2], use_container_width=True, key="c3"): secim = st.session_state.siklar[2]
            if st.button(st.session_state.siklar[3], use_container_width=True, key="c4"): secim = st.session_state.siklar[3]

        if secim:
            dogru_cevap = f"{hedef['sehir']}, {hedef['ulke']}"
            if secim == dogru_cevap:
                st.balloons()
                st.success(f"✅ Harika! Doğru cevap: {dogru_cevap}")
                supabase.rpc('artir_sehir_puani', {'ad': st.session_state.ogrenci_ismi, 'ek_puan': 20}).execute()
            else:
                st.error(f"❌ Yanlış! Aslında orası {dogru_cevap} idi.")
            
            st.session_state.cevap_verildi = True
            st.rerun()

    elif st.session_state.cevap_verildi:
        st.info("🎯 Cevabın kaydedildi. Pito: 'Öğretmenin sıradaki şehri göndermesini bekle...'")
        if st.button("Sıradaki Şehir Geldi mi?"):
            st.rerun()
    else:
        st.warning("⏳ Oyun kurucunun maratonu başlatması bekleniyor...")
