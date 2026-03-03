import streamlit as st
from supabase import create_client
import random
import time
import streamlit.components.v1 as components

# --- 1. BAĞLANTI AYARLARI ---
URL = "https://whtawpamszuyemebwuvu.supabase.co"
KEY = "sb_publishable_pxXYAqzI8mf70h2YHNF1Xg_J7x2vZJU"
supabase = create_client(URL, KEY)

# --- 2. DİNAMİC ŞEHİR & VİDEO HAVUZU ---
# Burayı dilediğin kadar büyütebilirsin. JSON'a ihtiyaç yok!
HAVUZ = [
    {"ad": "Roma, İtalya", "v": "EsFheWkimsU"},
    {"ad": "Tokyo, Japonya", "v": "Xp7S_CstMog"},
    {"ad": "New York, ABD", "v": "PEhKhACVfaA"},
    {"ad": "Paris, Fransa", "v": "5p5FoQR8wTM"},
    {"ad": "Londra, İngiltere", "v": "lh8dNmneVyY"},
    {"ad": "Amsterdam, Hollanda", "v": "M7X9_Hl60Kk"},
    {"ad": "Barselona, İspanya", "v": "Y8S98GqR0bE"},
    {"ad": "Seul, Güney Kore", "v": "nN_n2B97zK8"},
    {"ad": "İstanbul, Türkiye", "v": "S_fS7p19m00"}
]

# --- 3. VİDEO OYNATICI (GÜVENLİ MOD) ---
def pito_video_oynatici(video_id, start_time):
    embed_url = f"https://www.youtube.com/embed/{video_id}?start={start_time}&autoplay=1&rel=0&modestbranding=1&controls=0"
    html_kodu = f"""
    <div style="position: relative; width: 100%; height: 450px; overflow: hidden; border-radius: 15px; border: 3px solid #00FFCC;">
        <div style="position: absolute; top: 0; left: 0; width: 100%; height: 60px; background-color: black; z-index: 20;"></div>
        <div style="position: absolute; bottom: 0; right: 0; width: 150px; height: 50px; background-color: black; z-index: 20;"></div>
        <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 15; background: rgba(0,0,0,0);"></div>
        <iframe width="100%" height="550" src="{embed_url}" frameborder="0" allow="autoplay; encrypted-media" style="position: absolute; top: -50px; left: 0;"></iframe>
    </div>
    """
    components.html(html_kodu, height=460)

# --- 4. AKILLI ŞIK OLUŞTURUCU ---
def siklari_hazirla(dogru_cevap):
    yanlislar = random.sample([s['ad'] for s in HAVUZ if s['ad'] != dogru_cevap], 3)
    hepsi = yanlislar + [dogru_cevap]
    random.shuffle(hepsi)
    return hepsi

# --- 5. ANA EKRAN ---
st.set_page_config(page_title="Pito Ultimate Guesser", layout="wide")

with st.sidebar:
    st.header("🏆 Canlı Skorlar")
    try:
        skorlar = supabase.table("sehir_tahmin_skor").select("*").order("puan", desc=True).limit(8).execute()
        for i, s in enumerate(skorlar.data):
            st.write(f"**{i+1}. {s['ogrenci_adi']}** — `{s['puan']} XP`")
    except: st.write("Yükleniyor...")
    
    st.write("---")
    with st.expander("🔐 Öğretmen Paneli"):
        admin_onay = (st.text_input("Şifre:", type="password") == "pito123")

# --- ÖĞRETMEN PANELİ ---
if admin_onay:
    st.subheader("👨‍🏫 Maraton Kontrolü")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🚀 YENİ RASTGELE TUR", use_container_width=True):
            secilen = random.choice(HAVUZ)
            v_start = random.randint(150, 600) # Her seferinde farklı saniye!
            
            # Veritabanını güncelle
            supabase.table("oyun_odasi").update({
                "aktif_sehir_id": secilen['v'], # Video ID
                "durum": "aktif",
                "ek_bilgi": secilen['ad'], # Doğru Cevap
                "bitis_zamani": v_start # Başlangıç saniyesi
            }).eq("id", 1).execute()
            st.success(f"Yayınlandı: {secilen['ad']}")

    with c2:
        if st.button("🛑 OYUNU DURDUR (LOBİ)", use_container_width=True):
            supabase.table("oyun_odasi").update({"durum": "bekleme", "aktif_sehir_id": None}).eq("id", 1).execute()
            st.warning("Herkes lobiye alındı.")

# --- ÖĞRENCİ PANELİ ---
else:
    if 'ogrenci_ismi' not in st.session_state:
        st.session_state.ogrenci_ismi = st.text_input("Adın Soyadın:", placeholder="Giriş yap...")
        st.stop()

    # Veritabanını anlık oku
    oda = supabase.table("oyun_odasi").select("*").eq("id", 1).execute().data[0]
    
    # LOBİ KİLİDİ
    if oda['durum'] != "aktif" or oda['aktif_sehir_id'] is None:
        st.title(f"👋 Selam {st.session_state.ogrenci_ismi}!")
        st.info("🎮 Pito: 'Şu an lobideyiz. Öğretmen maratonu başlattığında aksiyon burada başlayacak!'")
        if st.button("🔄 Kontrol Et"): st.rerun()
        st.stop()

    # YENİ TUR BAŞLATMA MANTIĞI
    if 'mevcut_v_id' not in st.session_state or st.session_state.mevcut_v_id != oda['aktif_sehir_id']:
        st.session_state.mevcut_v_id = oda['aktif_sehir_id']
        st.session_state.cevap_verildi = False
        st.session_state.siklar = siklari_hazirla(oda['ek_bilgi'])
        st.session_state.baslangic_t = time.time()

    if not st.session_state.cevap_verildi:
        st.subheader(f"📍 Dedektif {st.session_state.ogrenci_ismi}, Neredesin?")
        pito_video_oynatici(oda['aktif_sehir_id'], oda['bitis_zamani'])
        
        st.write("---")
        c1, c2 = st.columns(2)
        secim = None
        with c1:
            if st.button(st.session_state.siklar[0], use_container_width=True, key="s1"): secim = st.session_state.siklar[0]
            if st.button(st.session_state.siklar[1], use_container_width=True, key="s2"): secim = st.session_state.siklar[1]
        with c2:
            if st.button(st.session_state.siklar[2], use_container_width=True, key="s3"): secim = st.session_state.siklar[2]
            if st.button(st.session_state.siklar[3], use_container_width=True, key="s4"): secim = st.session_state.siklar[3]

        if secim:
            if secim == oda['ek_bilgi']:
                gecen = time.time() - st.session_state.baslangic_t
                bonus = max(0, int(20 - gecen))
                st.balloons()
                st.success(f"✅ BİLDİN! +{20 + bonus} XP")
                supabase.rpc('artir_sehir_puani', {'ad': st.session_state.ogrenci_ismi, 'ek_puan': 20 + bonus}).execute()
            else:
                st.error(f"❌ YANLIŞ! Doğru: {oda['ek_bilgi']}")
            st.session_state.cevap_verildi = True
            st.rerun()
    else:
        st.info("🎯 Cevap kaydedildi. Yeni turu bekliyoruz...")
        if st.button("🔄 Sıradaki Geldi mi?"): st.rerun()
