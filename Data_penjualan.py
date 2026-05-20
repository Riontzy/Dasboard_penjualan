import streamlit as st
import pandas as pd
import plotly.express as px

# ==========================================
# 1. KONFIGURASI HALAMAN UTAMA DASHBOARD
# ==========================================
st.set_page_config(page_title="Dashboard Penjualan Honda", layout="wide")
st.title("📊 Dashboard Analisis Penjualan Motor")
st.markdown("Aplikasi perbandingan penjualan bulanan, tahunan, koordinator, tipe motor, dan wilayah.")

# ==========================================
# 2. LOAD DATA DARI GOOGLE SHEETS
# ==========================================
SHEET_ID = "1KUtjz33w7w6q5Shq1iGYe4uufJwpHD5buEcUjEePKWU"
GID = "1840604455"
csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

@st.cache_data(ttl=1200) # Cache data selama 20 menit untuk mengurangi beban load ulang saat interaksi
def load_data():
    try:
        df = pd.read_csv(csv_url, sep=',', on_bad_lines='skip')
        if df.shape[1] <= 1:
            df = pd.read_csv(csv_url, sep=';', on_bad_lines='skip')
    except:
        df = pd.read_csv(csv_url, sep=';', on_bad_lines='skip')
    
    df.columns = df.columns.str.strip()
    nama_kolom_tgl = 'Tgl laku'
    
    if nama_kolom_tgl in df.columns:
        df[nama_kolom_tgl] = pd.to_datetime(df[nama_kolom_tgl], dayfirst=True, errors='coerce')
        df = df.dropna(subset=[nama_kolom_tgl])
        
        # Konversi Tahun ke String agar Plotly memperlakukannya sebagai kategori warna/legenda terpisah
        df['Tahun'] = df[nama_kolom_tgl].dt.year.astype(str)
        df['Bulan_Angka'] = df[nama_kolom_tgl].dt.month
        df['Bulan'] = df[nama_kolom_tgl].dt.strftime('%B') 
    else:
        st.error(f"❌ Kolom '{nama_kolom_tgl}' tidak ditemukan!")
        df['Tahun'] = str(pd.Timestamp.now().year)
        df['Bulan_Angka'] = pd.Timestamp.now().month
        df['Bulan'] = pd.Timestamp.now().strftime('%B')
        
    return df

try:
    df = load_data()
    st.success("✅ Data sukses sinkron dan terurai dengan benar!")
except Exception as e:
    st.error(f"❌ Gagal memproses data. Error: {e}")
    st.stop()

# --- URUTAN BULAN STANDAR KALENDER ---
URUTAN_BULAN = [
    "January", "February", "March", "April", "May", "June", 
    "July", "August", "September", "October", "November", "December"
]
bulan_tersedia = [b for b in URUTAN_BULAN if b in df['Bulan'].unique()]

st.markdown("---")

# ==========================================
# 3. FITUR 1: TREN TOTAL (PERBANDINGAN MULTI-TAHUN)
# ==========================================
st.header("📈 1. Tren Perbandingan Penjualan Antar-Tahun")
st.write("Grafik di bawah membandingkan performa penjualan bulan ke bulan untuk semua tahun yang tersedia di data Anda.")

# Mengelompokkan data berdasarkan Tahun, Angka Bulan (untuk sortir), dan Nama Bulan
df_tren = df.groupby(['Tahun', 'Bulan_Angka', 'Bulan']).size().reset_index(name='Total Unit')
df_tren = df_tren.sort_values('Bulan_Angka') # Urut Januari -> Desember

col_g1, col_g2 = st.columns(2)

with col_g1:
    st.subheader("📊 Model Batang Berdampingan (Grouped Bar Chart)")
    # barmode='group' membuat batang tiap tahun berdiri berdampingan di bulan yang sama
    fig_bar_multi = px.bar(
        df_tren, 
        x='Bulan', 
        y='Total Unit', 
        color='Tahun', 
        barmode='group',
        text_auto=True,
        title="Perbandingan Bulan vs Tahun (Model Batang)",
        labels={'Bulan': 'Bulan Laku', 'Total Unit': 'Unit Terjual', 'Tahun': 'Tahun Laku'}
    )
    st.plotly_chart(fig_bar_multi, use_container_width=True)

with col_g2:
    st.subheader("📉 Model Garis Multi-Tahun (Multi-Line Chart)")
    # Grafik garis dengan warna pembeda untuk mempermudah melihat naik-turun tren antar-tahun
    fig_line_multi = px.line(
        df_tren, 
        x='Bulan', 
        y='Total Unit', 
        color='Tahun', 
        markers=True,
        title="Perbandingan Pergerakan Tren (Model Garis)",
        labels={'Bulan': 'Bulan Laku', 'Total Unit': 'Unit Terjual', 'Tahun': 'Tahun Laku'}
    )
    st.plotly_chart(fig_line_multi, use_container_width=True)

st.markdown("---")

# ==========================================
# 4. FITUR 2: KOORDINATOR & SALES
# ==========================================
st.header("👥 2. Analisis Performa Koordinator & Tim Sales")

if 'Koordinator' in df.columns and 'Sales' in df.columns:
    col_k1, col_k2 = st.columns(2)
    with col_k1:
        # Pilihan tahun disortir
        tahun_koor = st.selectbox("Pilih Tahun (Filter Tim):", options=sorted(df['Tahun'].unique(), reverse=True))
    with col_k2:
        bulan_koor = st.selectbox("Pilih Bulan (Filter Tim):", options=bulan_tersedia, key="k_bln")

    df_filtered_koor = df[(df['Tahun'] == tahun_koor) & (df['Bulan'] == bulan_koor)]

    df_koor_g = df_filtered_koor.groupby('Koordinator').size().reset_index(name='Penjualan').sort_values(by='Penjualan', ascending=False)
    fig_koor = px.bar(df_koor_g, x='Koordinator', y='Penjualan', text_auto=True, color='Koordinator')
    st.plotly_chart(fig_koor, use_container_width=True)

    koor_terpilih = st.selectbox("Pilih Nama Koordinator untuk breakdown Sales:", options=df_koor_g['Koordinator'].unique())
    df_sales_g = df_filtered_koor[df_filtered_koor['Koordinator'] == koor_terpilih].groupby('Sales').size().reset_index(name='Penjualan').sort_values(by='Penjualan', ascending=False)
    fig_sales = px.bar(df_sales_g, x='Sales', y='Penjualan', text_auto=True, color_discrete_sequence=['#00CC96'])
    st.plotly_chart(fig_sales, use_container_width=True)
else:
    st.info("ℹ️ Kolom 'Koordinator' atau 'Sales' tidak ditemukan di sheet Laporan laku ini.")

st.markdown("---")

# ==========================================
# 5. FITUR 3: PERBANDINGAN TIPE MOTOR
# ==========================================
st.header("🏍️ 3. Tipe Motor Terlaris Tiap Bulan")
col_m1, col_m2 = st.columns(2)
with col_m1:
    tahun_motor = st.selectbox("Pilih Tahun (Motor):", options=sorted(df['Tahun'].unique(), reverse=True), key="m_thn")
with col_m2:
    bulan_motor = st.selectbox("Pilih Bulan (Motor):", options=bulan_tersedia, key="m_bln")

df_filtered_motor = df[(df['Tahun'] == tahun_motor) & (df['Bulan'] == bulan_motor)]

if 'Nama unit' in df.columns:
    # 1. Kelompokkan dan urutkan data dari terbesar ke terkecil
    df_motor_g = df_filtered_motor.groupby('Nama unit').size().reset_index(name='Jumlah Terjual').sort_values(by='Jumlah Terjual', ascending=False)
    
    # 2. Buat fig bar chart seperti biasa
    fig_motor = px.bar(
        df_motor_g, 
        x='Jumlah Terjual', 
        y='Nama unit', 
        orientation='h', 
        text_auto=True, 
        color='Nama unit'
    )
    
    # 💡 PERBAIKAN UTAMA: Paksa sumbu Y mengikuti urutan data asli (kategori data)
    # 'category descending' digunakan agar item paling laris berada di posisi paling atas pada chart horizontal
    fig_motor.update_layout(
        yaxis={'categoryorder': 'total ascending'},
        height=700, # Menambah tinggi chart agar nama unit yang banyak tidak saling bertumpuk
        showlegend=False # Opsional: Menyembunyikan legenda di kanan agar grafik lebih luas & rapi
    )
    
    # fig_motor.update_layout(showlegend=False)
    st.plotly_chart(fig_motor, use_container_width=True)

# ==========================================
# 6. FITUR 4: ANALISIS WILAYAH (DRILLDOWN)
# ==========================================
st.header("📍 4. Analisis Penjualan per Wilayah (Kecamatan & Kelurahan)")
col_w1, col_w2 = st.columns(2)
with col_w1:
    tahun_wil = st.selectbox("Pilih Tahun (Wilayah):", options=sorted(df['Tahun'].unique(), reverse=True), key="w_thn")
with col_w2:
    bulan_wil = st.selectbox("Pilih Bulan (Wilayah):", options=bulan_tersedia, key="w_bln")

df_filtered_wil = df[(df['Tahun'] == tahun_wil) & (df['Bulan'] == bulan_wil)]

if 'Kecamatan' in df.columns and 'Kelurahan' in df.columns:
    df_kec_g = df_filtered_wil.groupby('Kecamatan').size().reset_index(name='Penjualan').sort_values(by='Penjualan', ascending=False)
    fig_kec = px.bar(df_kec_g, x='Kecamatan', y='Penjualan', text_auto=True, color_discrete_sequence=['#AB63FA'])
    st.plotly_chart(fig_kec, use_container_width=True)

    fig_kec.update_layout(
        yaxis={'categoryorder': 'total ascending'},
        height=700, # Menambah tinggi chart agar nama unit yang banyak tidak saling bertumpuk
        showlegend=False # Opsional: Menyembunyikan legenda di kanan agar grafik lebih luas & rapi
    )
    
    st.markdown("### 🏘️ Detail Kelurahan Berdasarkan Pilihan Kecamatan")
    kec_terpilih = st.selectbox("Pilih Nama Kecamatan untuk memunculkan detail Kelurahan:", options=df_kec_g['Kecamatan'].unique())
    
    if kec_terpilih:
        df_kel_g = df_filtered_wil[df_filtered_wil['Kecamatan'] == kec_terpilih].groupby('Kelurahan').size().reset_index(name='Penjualan').sort_values(by='Penjualan', ascending=False)
        fig_kel = px.bar(df_kel_g, x='Kelurahan', y='Penjualan', text_auto=True, color='Kelurahan')
        st.plotly_chart(fig_kel, use_container_width=True)
