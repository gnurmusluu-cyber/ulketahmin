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
        <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 15; background: rgba(0,0,0,0);"></div>
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

# --- 5. ANA EKRAN AYARLARI ---
st.set_page_config(page_title="Pito CityGuesser", layout="wide")

# Liderlik Tablosu (Sidebar)
with st.sidebar:
    st.header("🏆 Canlı Skorlar")
    try:
        skorlar = supabase.table("sehir_tahmin_skor").select("*").order("puan", desc=True).limit(8).execute()
        for i, s in enumerate(skorlar.data):
            st.markdown(f"**{i+1}. {s['ogrenci_adi']}** — `{s['puan']} XP`")
    except: st.write("Yükleniyor...")
    
    st.write("---")
    # GİZLİ YÖNETİM PANELİ GİRİŞİ
    with st.expander("🔐 Öğretmen Paneli"):
        sifre = st.text_input("Şifre Girin:", type="password")
        if sifre == "pito123":
            st.session_state.admin_onay = True
            st.success("Erişim Sağlandı!")
        else:
            st.session_state.admin_onay = False

# --- ÖĞRETMEN PANELİ ---
if st.session_state.get('admin_onay'):
    st.subheader("👨‍🏫 Maraton Kontrol Merkezi")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 SIRADAKİ ŞEHİR / OYUNU BAŞLAT"):
            yeni = random.choice(sehirler)
            supabase.table("oyun_odasi").update({
                "aktif_sehir_id": yeni['id'],
                "durum": "aktif"
            }).eq("id", 1).execute()
            st.success("Yeni görev gönderildi!")

    with col2:
        if st.button("🛑 OYUNU DURDUR (BEKLEME MODU)"):
            supabase.table("oyun_odasi").update({
                "durum": "bekleme",
                "aktif_sehir_id": None
            }).eq("id", 1).execute()
            st.warning("Oyun tüm öğrenciler için durduruldu.")

# --- ÖĞRENCİ PANELİ ---
else:
    if 'ogrenci_ismi' not in st.session_state:
        st.session_state.ogrenci_ismi = st.text_input("Yarışmacı Adın:", placeholder="İsmini yaz ve Enter'la...")
        st.stop()

    # Supabase'den durum kontrolü
    oda = supabase.table("oyun_odasi").select("*").eq("id", 1).execute().data[0]
    
    # EĞER DURUM BEKLEMEDE İSE VİDEOYU GÖSTERME, BURADA DUR!
    if oda['durum'] != "aktif":
        st.title(f"👋 Hoş Geldin {st.session_state.ogrenci_ismi}!")
        st.info("🎮 Pito: 'Şu an bekleme salonundayız. Öğretmenin maratonu başlattığında burada video belirecek. Sayfayı kapatma!'")
        if st.button("Yenile 🔄"):
            st.rerun()
        st.stop() # KRİTİK: Kodun geri kalanını çalıştırmaz!

    # --- BURADAN SONRASI SADECE DURUM 'AKTİF' İSE ÇALIŞIR ---
    if 'su_anki_id' not in st.session_state or st.session_state.su_anki_id != oda['aktif_sehir_id']:
        st.session_state.su_anki_id = oda['aktif_sehir_id']
        st.session_state.cevap_verildi = False
        hedef = next(s for s in sehirler if s['id'] == oda['aktif_sehir_id'])
        st.session_state.siklar = siklari_hazirla(hedef)
        st.session_state.zaman_basla = time.time()

    if not st.session_state.cevap_verildi:
        hedef = next(s for s in sehirler if s['id'] == oda['aktif_sehir_id'])
        st.subheader(f"📍 Dedektif {st.session_state.ogrenci_ismi}, Burası Neresi?")
        
        pito_guvenli_video(hedef['video_id'], hedef['baslangic_sn'])
        
        st.write("---")
        col_x, col_y = st.columns(2)
        secilen = None
        with col_x:
            if st.button(st.session_state.siklar[0], use_container_width=True, key="s1"): secilen = st.session_state.siklar[0]
            if st.button(st.session_state.siklar[1], use_container_width=True, key="s2"): secilen = st.session_state.siklar[1]
        with col_y:
            if st.button(st.session_state.siklar[2], use_container_width=True, key="s3"): secilen = st.session_state.siklar[2]
            if st.button(st.session_state.siklar[3], use_container_width=True, key="s4"): secilen = st.session_state.siklar[3]

        if secilen:
            dogru_cevap = f"{hedef['sehir']}, {hedef['ulke']}"
            if secilen == dogru_cevap:
                sure = time.time() - st.session_state.zaman_basla
                hiz_bonusu = max(0, int(20 - sure))
                toplam = 20 + hiz_bonusu
                st.balloons()
                st.success(f"✅ HARİKA! {toplam} XP! (Hız Bonusu: +{hiz_bonusu})")
                supabase.rpc('artir_sehir_puani', {'ad': st.session_state.ogrenci_ismi, 'ek_puan': toplam}).execute()
            else:
                st.error(f"❌ Üzgünüm! Doğru cevap: {dogru_cevap}")
            
            st.session_state.cevap_verildi = True
            st.rerun()
    else:
        st.info("🎯 Cevabını verdin. Pito: 'Şimdi arkana yaslan ve diğerlerini izle ya da yeni turu bekle!'")
        if st.button("Yeni Görev Geldi mi? 🔄"): st.rerun()
