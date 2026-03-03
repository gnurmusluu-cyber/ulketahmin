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
    st.header("🏆 Skorbord")
    try:
        skorlar = supabase.table("sehir_tahmin_skor").select("*").order("puan", desc=True).limit(5).execute()
        for i, s in enumerate(skorlar.data):
            st.write(f"**{i+1}. {s['ogrenci_adi']}** — `{s['puan']} XP`")
    except: st.write("Veri bekleniyor...")
    
    st.write("---")
    # GİZLİ ÖĞRETMEN GİRİŞİ
    with st.expander("🔐 Yönetim"):
        sifre = st.text_input("Öğretmen Şifresi:", type="password")
        if sifre == "pito123": # Buradan şifreyi değiştirebilirsin
            st.session_state.is_admin = True
            st.success("Yönetici Erişimi Aktif!")
        else:
            st.session_state.is_admin = False

# --- ÖĞRETMEN KONTROLÜ (ŞİFRELİ) ---
if st.session_state.get('is_admin'):
    st.subheader("👨‍🏫 Maraton Kontrol Merkezi")
    
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🚀 OYUNU BAŞLAT / SIRADAKİ ŞEHİR"):
            yeni = random.choice(sehirler)
            supabase.table("oyun_odasi").update({
                "aktif_sehir_id": yeni['id'],
                "durum": "aktif",
                "bitis_zamani": time.time()
            }).eq("id", 1).execute()
            st.balloons()
            st.success("Yeni şehir sınıfa gönderildi!")
            
    with col_b:
        if st.button("🛑 OYUNU DURDUR / BEKLEME MODU"):
            supabase.table("oyun_odasi").update({"durum": "beklemede", "aktif_sehir_id": None}).eq("id", 1).execute()
            st.warning("Oyun durduruldu, öğrenciler bekleme salonuna alındı.")

# --- ÖĞRENCİ PANELİ ---
else:
    if 'ogrenci_ismi' not in st.session_state:
        st.session_state.ogrenci_ismi = st.text_input("Yarışmacı Adı:")
        st.info("Pito: 'İsmini yaz ve öğretmeninin oyunu başlatmasını bekle!'")
        st.stop()

    # Oda verisini çek
    oda = supabase.table("oyun_odasi").select("*").eq("id", 1).execute().data[0]
    
    if oda['durum'] == "beklemede":
        st.title(f"👋 Selam {st.session_state.ogrenci_ismi}!")
        st.info("🎮 Oyun Henüz Başlamadı. Pito: 'Öğretmenin butona bastığında macera başlayacak!'")
        if st.button("Yenile"): st.rerun()
    
    else:
        # Yeni tur kontrolü
        if 'mevcut_id' not in st.session_state or st.session_state.mevcut_id != oda['aktif_sehir_id']:
            st.session_state.mevcut_id = oda['aktif_sehir_id']
            st.session_state.cevap_verildi = False
            if oda['aktif_sehir_id']:
                hedef = next(s for s in sehirler if s['id'] == oda['aktif_sehir_id'])
                st.session_state.siklar = siklari_hazirla(hedef)
                st.session_state.baslangic_anlik = time.time()

        if oda['aktif_sehir_id'] and not st.session_state.cevap_verildi:
            hedef = next(s for s in sehirler if s['id'] == oda['aktif_sehir_id'])
            st.subheader(f"📍 Dedektif {st.session_state.ogrenci_ismi}, Neredesin?")
            pito_guvenli_video(hedef['video_id'], hedef['baslangic_sn'])
            
            st.write("---")
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
                    gecen_sure = time.time() - st.session_state.baslangic_anlik
                    zaman_bonusu = max(0, int(20 - gecen_sure))
                    toplam_puan = 20 + zaman_bonusu
                    st.balloons()
                    st.success(f"✅ BİLDİN! {toplam_puan} XP Kazandın! (Hız: {int(gecen_sure)}sn)")
                    supabase.rpc('artir_sehir_puani', {'ad': st.session_state.ogrenci_ismi, 'ek_puan': toplam_puan}).execute()
                else:
                    st.error(f"❌ YANLIŞ! Doğru cevap: {dogru_cevap}")
                
                st.session_state.cevap_verildi = True
                st.rerun()

        elif st.session_state.cevap_verildi:
            st.info("🎯 Cevabın kaydedildi. Yeni turun gelmesini bekliyorsun...")
            if st.button("Yeni Tur Geldi mi?"): st.rerun()
