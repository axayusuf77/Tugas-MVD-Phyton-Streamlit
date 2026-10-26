import pandas as pd
import plotly.express as px
import streamlit as st

# ---------- Pengaturan halaman ----------
st.set_page_config(page_title="Dashboard Penjualan Superstore", page_icon="📊", layout="wide")

# Tema warna: satu warna utama (biru) biar tampilannya konsisten
BIRU = "#2563EB"
BIRU_TRANSPARAN = "rgba(37, 99, 235, 0.12)"
WARNA_SEGMEN = ["#1D4ED8", "#60A5FA", "#BFDBFE"]
NAMA_BULAN = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]

# Sedikit CSS untuk merapikan jarak halaman
st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}
    h1 {font-size: 2rem !important; margin-bottom: 0;}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------- Fungsi bantu ----------
def titik(angka, desimal=0):
    """Format angka gaya Indonesia: titik untuk ribuan, koma untuk desimal."""
    teks = f"{angka:,.{desimal}f}"
    return teks.replace(",", "_").replace(".", ",").replace("_", ".")


def ringkas(rupiah):
    """Ubah rupiah jadi bentuk singkat, misalnya 36180000000 jadi Rp 36,18 M."""
    if rupiah >= 1_000_000_000_000:
        return f"Rp {titik(rupiah / 1_000_000_000_000, 2)} T"
    if rupiah >= 1_000_000_000:
        return f"Rp {titik(rupiah / 1_000_000_000, 2)} M"
    if rupiah >= 1_000_000:
        return f"Rp {titik(rupiah / 1_000_000, 1)} jt"
    return f"Rp {titik(rupiah)}"


def tampilkan(fig, tinggi=360):
    """Rapikan tampilan grafik lalu tampilkan di dalam kotak berborder."""
    fig.update_layout(
        height=tinggi,
        margin=dict(l=10, r=10, t=50, b=10),
        title=dict(font=dict(size=16)),
        legend_title_text="",
        separators=",.",  # koma untuk desimal, titik untuk ribuan
    )
    with st.container(border=True):
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


@st.cache_data
def load_data():
    df = pd.read_csv("train.csv")
    df["Order Date"] = pd.to_datetime(df["Order Date"], dayfirst=True)
    df["Tahun"] = df["Order Date"].dt.year
    df["Bulan"] = df["Order Date"].dt.to_period("M").dt.to_timestamp()
    return df


df = load_data()

# ---------- Filter (sidebar) ----------
st.sidebar.header("Filter Data")

tahun = st.sidebar.slider(
    "Rentang Tahun",
    int(df["Tahun"].min()),
    int(df["Tahun"].max()),
    (int(df["Tahun"].min()), int(df["Tahun"].max())),
)
region = st.sidebar.multiselect(
    "Wilayah (Region)", sorted(df["Region"].unique()), default=sorted(df["Region"].unique())
)
category = st.sidebar.multiselect(
    "Kategori Produk", sorted(df["Category"].unique()), default=sorted(df["Category"].unique())
)
segment = st.sidebar.multiselect(
    "Segmen Pelanggan", sorted(df["Segment"].unique()), default=sorted(df["Segment"].unique())
)

st.sidebar.divider()
kurs = st.sidebar.number_input(
    "Kurs 1 USD (Rp)", min_value=1000, max_value=50000, value=18000, step=100,
    help="Data aslinya dalam dolar AS (USD). Nilai penjualan dikonversi ke rupiah dengan kurs ini.",
)
st.sidebar.caption("Semua angka dan grafik mengikuti filter di atas. Data asli dalam USD, dikonversi ke rupiah dengan kurs di atas.")

data = df[
    df["Region"].isin(region)
    & df["Category"].isin(category)
    & df["Segment"].isin(segment)
    & df["Tahun"].between(tahun[0], tahun[1])
].copy()

# Mulai dari sini, kolom Sales sudah dalam rupiah
data["Sales"] = data["Sales"] * kurs

# ---------- Judul dan deskripsi ----------
st.title("📊 Dashboard Penjualan Superstore")
st.caption(
    "Ringkasan penjualan toko ritel di Amerika Serikat, periode "
    f"{tahun[0]} sampai {tahun[1]}. Nilai dalam rupiah (kurs 1 USD = Rp {titik(kurs)}). "
    "Sumber data: Kaggle (Sales Forecasting / Superstore Sales)."
)

if data.empty:
    st.warning("Tidak ada data untuk filter yang dipilih. Coba ubah filternya.")
    st.stop()

# ---------- KPI ----------
total_sales = data["Sales"].sum()
total_order = data["Order ID"].nunique()
total_customer = data["Customer ID"].nunique()
rata_order = total_sales / total_order

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Penjualan", ringkas(total_sales), border=True,
          help=f"Jumlah seluruh nilai penjualan: Rp {titik(total_sales)}")
k2.metric("Jumlah Pesanan", titik(total_order), border=True,
          help="Banyaknya pesanan unik (berdasarkan Order ID).")
k3.metric("Jumlah Pelanggan", titik(total_customer), border=True,
          help="Banyaknya pelanggan unik (berdasarkan Customer ID).")
k4.metric("Rata-rata Nilai Pesanan", ringkas(rata_order), border=True,
          help=f"Total penjualan dibagi jumlah pesanan: Rp {titik(rata_order)}")

# ---------- Baris 1: tren dan segmen ----------
st.subheader("Tren dan Komposisi Penjualan")
kiri, kanan = st.columns([2, 1])

with kiri:
    tren = data.groupby("Bulan", as_index=False)["Sales"].sum()
    tren["Juta"] = tren["Sales"] / 1_000_000
    fig = px.line(tren, x="Bulan", y="Juta", markers=True,
                  title="Tren Penjualan per Bulan", color_discrete_sequence=[BIRU])
    fig.update_traces(
        fill="tozeroy", fillcolor=BIRU_TRANSPARAN,
        hovertemplate="%{x|%b %Y}<br>Rp %{y:,.0f} juta<extra></extra>",
    )
    fig.update_xaxes(title="")
    fig.update_yaxes(title="Penjualan (juta Rp)", tickformat=",.0f")
    tampilkan(fig)

with kanan:
    seg = data.groupby("Segment", as_index=False)["Sales"].sum().sort_values("Sales", ascending=False)
    fig = px.pie(seg, names="Segment", values="Sales", hole=0.55,
                 title="Proporsi Penjualan per Segmen",
                 color_discrete_sequence=WARNA_SEGMEN)
    fig.update_traces(textinfo="percent", sort=False,
                      hovertemplate="%{label}<br>Rp %{value:,.0f} (%{percent})<extra></extra>")
    fig.update_layout(legend=dict(orientation="h", y=-0.05, x=0.5, xanchor="center"))
    tampilkan(fig)

# ---------- Baris 2: produk dan wilayah ----------
st.subheader("Produk dan Wilayah")
kiri, kanan = st.columns(2)

with kiri:
    sub = (data.groupby("Sub-Category", as_index=False)["Sales"].sum()
           .sort_values("Sales", ascending=False).head(10).sort_values("Sales"))
    sub["Juta"] = sub["Sales"] / 1_000_000
    fig = px.bar(sub, x="Juta", y="Sub-Category", orientation="h",
                 title="10 Sub-Kategori dengan Penjualan Tertinggi (juta Rp)",
                 color_discrete_sequence=[BIRU])
    fig.update_traces(texttemplate="Rp %{x:,.0f} jt", textposition="outside", cliponaxis=False,
                      hovertemplate="%{y}<br>Rp %{x:,.0f} juta<extra></extra>")
    fig.update_xaxes(title="", showticklabels=False, showgrid=False,
                     range=[0, sub["Juta"].max() * 1.35])
    fig.update_yaxes(title="")
    tampilkan(fig, 400)

with kanan:
    pivot = data.pivot_table(index="Region", columns="Category", values="Sales",
                             aggfunc="sum", fill_value=0) / 1_000_000
    fig = px.imshow(pivot, text_auto=",.0f", aspect="auto",
                    color_continuous_scale="Blues",
                    title="Penjualan per Wilayah dan Kategori (juta Rp)")
    fig.update_coloraxes(showscale=False)
    fig.update_xaxes(title="", side="bottom")
    fig.update_yaxes(title="")
    tampilkan(fig, 400)

# ---------- Baris 3: sebaran dan pelanggan ----------
st.subheader("Transaksi dan Pelanggan")
kiri, kanan = st.columns(2)

with kiri:
    batas = data["Sales"].quantile(0.95)
    median = data["Sales"].median()
    ribu = data[data["Sales"] <= batas].assign(Ribu=lambda x: x["Sales"] / 1000)
    fig = px.histogram(ribu, x="Ribu", nbins=40,
                       title="Sebaran Nilai Transaksi (95% data terbawah)",
                       color_discrete_sequence=[BIRU])
    fig.add_vline(x=median / 1000, line_dash="dash", line_color="#F59E0B",
                  annotation_text=f"Median Rp {titik(median / 1000)} rb",
                  annotation_position="top right")
    fig.update_xaxes(title="Nilai Transaksi (ribu Rp)", tickformat=",.0f")
    fig.update_yaxes(title="Jumlah Transaksi")
    fig.update_traces(marker_line_width=0.5, marker_line_color="white")
    tampilkan(fig, 400)

with kanan:
    top = (data.groupby("Customer Name", as_index=False)["Sales"].sum()
           .sort_values("Sales", ascending=False).head(10))
    top["Sales"] = top["Sales"] / 1_000_000
    top = top.rename(columns={"Customer Name": "Pelanggan", "Sales": "Total Belanja (juta Rp)"})
    with st.container(border=True):
        st.markdown("**10 Pelanggan dengan Belanja Terbesar**")
        st.dataframe(
            top, hide_index=True, width="stretch", height=390,
            column_config={
                "Total Belanja (juta Rp)": st.column_config.ProgressColumn(
                    "Total Belanja (juta Rp)", format="%.0f",
                    min_value=0, max_value=float(top["Total Belanja (juta Rp)"].max()),
                )
            },
        )

# ---------- Insight otomatis ----------
st.subheader("Insight Singkat")

per_kategori = data.groupby("Category")["Sales"].sum()
per_wilayah = data.groupby("Region")["Sales"].sum()
per_segmen = data.groupby("Segment")["Sales"].sum()
bulan_terbaik = tren.loc[tren["Sales"].idxmax()]
nama_bulan = f"{NAMA_BULAN[bulan_terbaik['Bulan'].month - 1]} {bulan_terbaik['Bulan'].year}"
sub_terbaik = sub.iloc[-1]

with st.container(border=True):
    st.markdown(
        f"""
- Kategori dengan penjualan tertinggi adalah **{per_kategori.idxmax()}** ({ringkas(per_kategori.max())}), dan sub-kategori terbesarnya adalah **{sub_terbaik['Sub-Category']}** ({ringkas(sub_terbaik['Sales'])}).
- Wilayah **{per_wilayah.idxmax()}** paling besar kontribusinya ({ringkas(per_wilayah.max())}), sedangkan **{per_wilayah.idxmin()}** paling kecil ({ringkas(per_wilayah.min())}).
- Penjualan bulanan tertinggi terjadi pada **{nama_bulan}** ({ringkas(bulan_terbaik['Sales'])}).
- Segmen **{per_segmen.idxmax()}** menyumbang {titik(per_segmen.max() / per_segmen.sum() * 100, 1)}% dari total penjualan.
        """
    )

# ---------- Data mentah ----------
with st.expander("Lihat dan unduh data"):
    tabel = data.drop(columns=["Bulan", "Tahun"]).rename(columns={"Sales": "Sales (Rp)"})
    st.dataframe(tabel, width="stretch", height=300)
    st.download_button("Unduh data terfilter (CSV)", tabel.to_csv(index=False),
                       file_name="data_terfilter.csv", mime="text/csv")

st.caption("Dashboard dibuat dengan Python dan Streamlit.")
