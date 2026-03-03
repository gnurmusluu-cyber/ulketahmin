import streamlit as st
from supabase import create_client
import random
import time
import streamlit.components.v1 as components

# --- 1. BAĞLANTI ---
URL = "https://whtawpamszuyemebwuvu.supabase.co"
KEY = "sb_publishable_pxXYAqzI8mf70h2YHNF1Xg_J7x2vZJU"
supabase = create_client(URL, KEY)

# --- 2. ŞEHİR HAVUZU (Sonsuz Video İçin Kaynak) ---
# Buraya ne kadar çok şehir eklersen o kadar devasa bir oyun olur
SEHIR_HAVUZU = [
    {"sehir": "Paris", "ulke": "Fransa", "ids": ["5p5FoQR8wTM", "EsFheWkimsU"]}, # Örnek ID'ler
    {"sehir": "Londra", "ulke": "İngiltere", "ids": ["lh8dNmneVyY", "AQqPG14QjJM"]},
    # ... Bu liste sadece isim olarak bile kalsa yeterli olacak şekilde geliştirilebilir
]

# --- 3. PİTO GÜVENLİ OYNATICI ---
def pito_video_oynatici(video_id, start_time):
    embed_url = f"https://www.youtube.com/embed/{video_id}?start={start_time}&autoplay=1&controls=0&rel=0&modestbranding=1"
    html_kodu = f"""
    <div style="position: relative; width: 100%; height: 450px; overflow: hidden; border-radius: 15px; border: 3px solid #00FFCC; pointer-events: none;">
        <div style="position: absolute; top: 0; left: 0; width: 100%; height: 60px; background-color: black; z-index: 20;"></div>
        <div style="position: absolute; bottom: 0; right: 0; width: 150px; height: 50px; background-color: black; z-index: 20;"></div>
        <iframe width="100%" height="550" src="{embed_url}" frameborder="0" allow="autoplay; encrypted-media" style="position: absolute; top: -50px; left: 0;"></iframe>
    </div>
    """
    components.html(html_kodu, height=460)

# --- 4. AKILLI ŞIK OLUŞTURUCU ---
def dinamik_sik_hazirla(dogru_cevap):
    yanlislar = random.sample([s for s in SEHIR_HAVUZU if f"{s['sehir']}, {s['ulke']}" != dogru_cevap], 3)
    hepsi = [f"{s['sehir']}, {s['ulke']}" for s in yanlislar] + [dogru_cevap]
    random.shuffle(hepsi)
    return hepsi

# --- 5. ANA YAPI ---
st.set_page_config(page_title="Pito Ultimate Guesser", layout="wide")

with st.sidebar:
    st.header("🏆 Pito Ligi")
    # Skorbord kodu buraya gelecek...
    with st.expander("🔐 Yönetim"):
        is_admin = (st.text_input("Şifre:", type="password") == "pito123")

# --- ÖĞRETMEN PANELİ (Gelişmiş) ---
if is_admin:
    st.subheader("🎮 Oyun Kurucu Merkezi")
    if st.button("🎲 RASTGELE YENİ BÖLÜM OLUŞTUR"):
        secilen = random.choice(SEHIR_HAVUZU)
        v_id = random.choice(secilen['ids'])
        v_start = random.randint(180, 600) # Her seferinde farklı bir saniyeden başlar!
        
        supabase.table("oyun_odasi").update({
            "aktif_sehir_id": v_id, # Artık ID yerine direkt video ID saklıyoruz
            "durum": "aktif",
            "ek_bilgi": f"{secilen['sehir']}, {secilen['ulke']}", # Cevabı buraya sakladık
            "bitis_zamani": v_start
        }).eq("id", 1).execute()
        st.success(f"Yeni Tur: {secilen['sehir']} Yayında!")

# --- ÖĞRENCİ PANELİ ---
else:
    if 'ogrenci_ismi' not in st.session_state:
        st.session_state.ogrenci_ismi = st.text_input("Yarışmacı Adı:")
        st.stop()

    oda = supabase.table("oyun_odasi").select("*").eq("id", 1).execute().data[0]
    
    if oda['durum'] != "aktif":
        st.info("👋 Hoş geldin! Öğretmeninin maratonu başlatmasını bekliyoruz...")
        st.stop()

    # Tur Değişimi Kontrolü
    if 'tur_id' not in st.session_state or st.session_state.tur_id != oda['aktif_sehir_id']:
        st.session_state.tur_id = oda['aktif_sehir_id']
        st.session_state.cevap_verildi = False
        st.session_state.siklar = dinamik_sik_hazirla(oda['ek_bilgi'])
        st.session_state.baslama_t = time.time()

    if not st.session_state.cevap_verildi:
        pito_video_oynatici(oda['aktif_sehir_id'], oda['bitis_zamani'])
        
        st.write("---")
        secilen_cevap = None
        c1, c2 = st.columns(2)
        with c1:
            if st.button(st.session_state.siklar[0], use_container_width=True): secilen_cevap = st.session_state.siklar[0]
            if st.button(st.session_state.siklar[1], use_container_width=True): secilen_cevap = st.session_state.siklar[1]
        with c2:
            if st.button(st.session_state.siklar[2], use_container_width=True): secilen_cevap = st.session_state.siklar[2]
            if st.button(st.session_state.siklar[3], use_container_width=True): secilen_cevap = st.session_state.siklar[3]

        if secilen_cevap:
            if secilen_cevap == oda['ek_bilgi']:
                gecen = time.time() - st.session_state.baslama_t
                bonus = max(0, int(25 - gecen))
                st.balloons()
                st.success(f"✅ BİLDİN! +{20 + bonus} XP")
                supabase.rpc('artir_sehir_puani', {'ad': st.session_state.ogrenci_ismi, 'ek_puan': 20 + bonus}).execute()
            else:
                st.error(f"❌ YANLIŞ! Doğru cevap: {oda['ek_bilgi']}")
            st.session_state.cevap_verildi = True
            st.rerun()