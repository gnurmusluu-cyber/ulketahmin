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

# --- 3. KORUMALI VİDEO OYNATICI (CSS MASKELİ) ---
def pito_guvenli_video(video_id, start_time):
    # modestbranding ve rel parametreleri YouTube logosunu ve önerileri azaltır
    embed_url = f"https://www.youtube.com/embed/{video_id}?start={start_time}&autoplay=1&controls=0&rel=0&modestbranding=1&disablekb=1"
    
    html_kodu = f"""
    <div style="position: relative; width: 100%; height: 450px; overflow: hidden; border-radius: 15px; border: 3px solid #00FFCC; pointer-events: none;">
        <div style="position: absolute; top: 0; left: 0; width: 100%; height: 60px; background-color: black; z-index: 20;"></div>
        
        <div style="position: absolute; bottom: 0; right: 0; width: 150px; height: 50px; background-color: black; z-index: 20;"></div>
        
        <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 15; background: rgba(0,0,0,0);"></div>

        <iframe width="100%" height="550" src="{embed_url}" frameborder="0" allow="autoplay; encrypted-media" style="position: absolute; top: -50px; left: 0;"></iframe>
    </div>
    <p style="color: #666; font-size: 0.8rem; margin-top: 5px;">⚠️ Pito Güvenlik: Video kontrolleri ve dış bağlantılar devre dışı bırakıldı.</p>
    """
    components.html(html_kodu, height=480)

# --- 4. ŞIKLARI HAZIRLA ---
def siklari_hazirla(dogru_cevap_obj):
    dogru_metin = f"{dogru_cevap_obj['sehir']}, {dogru_cevap_obj['ulke']}"
    digerleri = [f"{s['sehir']}, {s['ulke']}" for s in sehirler if s['sehir'] != dogru_cevap_obj['sehir']]
    yanlislar = random.sample(digerleri, 3)
    hepsi = yanlislar + [dogru_metin]
    random.shuffle(hepsi)
    return hepsi

# --- 5. ANA EKRAN VE STİL ---
st.set_page_config(page_title="Pito CityGuesser", layout="wide")
st.markdown("<style>.stButton>button {height: 60px; font-size: 18px;}</style>", unsafe_allow_html=True)

# Liderlik Tablosu (Sağ Panel)
with st.sidebar:
    st.header("🏆 Liderlik Tablosu")
    try:
        skorlar = supabase.table("sehir_tahmin_skor").select("*").order("puan", desc=True).limit(8).execute()
        for i, s in enumerate(skorlar.data):
            st.markdown(f"**{i+1}. {s['ogrenci_adi']}** — `{s['puan']} XP`")
    except:
        st.write("Veriler yükleniyor...")
    
    st.write("---")
    rol = st.radio("Sistem", ["Öğrenci Girişi", "Öğretmen Paneli"])

# --- ÖĞRETMEN PANELİ ---
if rol == "Öğretmen Paneli":
    st.subheader("👨‍🏫 Maraton Kontrolü")
    if st.button("🚀 SIRADAKİ RASTGELE ŞEHRİ GÖNDER"):
        yeni = random.choice(sehirler)
        supabase.table("oyun_odasi").update({
            "aktif_sehir_id": yeni['id'],
            "durum": "aktif",
            "bitis_zamani": time.time()
        }).eq("id", 1).execute()
        st.success("Yeni hedef sınıfa gönderildi!")

# --- ÖĞRENCİ PANELİ ---
else:
    if 'ogrenci_ismi' not in st.session_state:
        st.session_state.ogrenci_ismi = st.text_input("Yarışmacı Adı:")
        st.stop()

    oda = supabase.table("oyun_odasi").select("*").eq("id", 1).execute().data[0]
    
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
                # Zaman Bonusu Hesaplama (İlk 30 saniye içinde ne kadar hızlıysa o kadar çok puan)
                gecen_sure = time.time() - st.session_state.baslangic_anlik
                zaman_bonusu = max(0, int(20 - gecen_sure)) # 20 saniyeden hızlıysa bonus
                toplam_puan = 20 + zaman_bonusu
                
                st.balloons()
                st.success(f"✅ MUHTEŞEM! {toplam_puan} XP kazandın! (Hız Bonusu: {zaman_bonusu})")
                supabase.rpc('artir_sehir_puani', {'ad': st.session_state.ogrenci_ismi, 'ek_puan': toplam_puan}).execute()
            else:
                st.error(f"❌ HATA! Doğru cevap: {dogru_cevap}")
            
            st.session_state.cevap_verildi = True
            st.rerun()

    elif st.session_state.cevap_verildi:
        st.info("🎯 Puanın kaydedildi. Yeni turun başlamasını bekle...")
        if st.button("🔄 Sıradaki Gelsin!"): st.rerun()
