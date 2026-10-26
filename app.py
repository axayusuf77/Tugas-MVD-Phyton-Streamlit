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
def ringkas(angka):
    """Ubah angka jadi bentuk singkat, misalnya 2261537 jadi $2.26M."""
    if angka >= 1_000_000:
        return f"${angka / 1_000_000:.2f}M"
    if angka >= 1_000:
        return f"${angka / 1_000:.1f}K"
    return f"${angka:,.0f}"


def tampilkan(fig, tinggi=360):
    """Rapikan tampilan grafik lalu tampilkan di dalam kotak berborder."""
    fig.update_layout(
        height=tinggi,
        margin=dict(l=10, r=10, t=50, b=10),
        title=dict(font=dict(size=16)),
        legend_title_text="",
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
st.sidebar.caption("Semua angka dan grafik mengikuti filter di atas.")

data = df[
    df["Region"].isin(region)
    & df["Category"].isin(category)
    & df["Segment"].isin(segment)
    & df["Tahun"].between(tahun[0], tahun[1])
]

# ---------- Judul dan deskripsi ----------
st.title("📊 Dashboard Penjualan Superstore")
st.caption(
    "Ringkasan penjualan toko ritel di Amerika Serikat, periode "
    f"{tahun[0]} sampai {tahun[1]}. Sumber data: Kaggle (Sales Forecasting / Superstore Sales)."
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
          help="Jumlah seluruh nilai penjualan pada data yang dipilih.")
k2.metric("Jumlah Pesanan", f"{total_order:,}", border=True,
          help="Banyaknya pesanan unik (berdasarkan Order ID).")
k3.metric("Jumlah Pelanggan", f"{total_customer:,}", border=True,
          help="Banyaknya pelanggan unik (berdasarkan Customer ID).")
k4.metric("Rata-rata Nilai Pesanan", f"${rata_order:,.0f}", border=True,
          help="Total penjualan dibagi jumlah pesanan.")

# ---------- Baris 1: tren dan segmen ----------
st.subheader("Tren dan Komposisi Penjualan")
kiri, kanan = st.columns([2, 1])

with kiri:
    tren = data.groupby("Bulan", as_index=False)["Sales"].sum()
    fig = px.line(tren, x="Bulan", y="Sales", markers=True,
                  title="Tren Penjualan per Bulan", color_discrete_sequence=[BIRU])
    fig.update_traces(
        fill="tozeroy", fillcolor=BIRU_TRANSPARAN,
        hovertemplate="%{x|%b %Y}<br>$%{y:,.0f}<extra></extra>",
    )
    fig.update_xaxes(title="")
    fig.update_yaxes(title="Penjualan ($)", tickprefix="$", tickformat=",.0f")
    tampilkan(fig)

with kanan:
    seg = data.groupby("Segment", as_index=False)["Sales"].sum().sort_values("Sales", ascending=False)
    fig = px.pie(seg, names="Segment", values="Sales", hole=0.55,
                 title="Proporsi Penjualan per Segmen",
                 color_discrete_sequence=WARNA_SEGMEN)
    fig.update_traces(textinfo="percent", sort=False,
                      hovertemplate="%{label}<br>$%{value:,.0f} (%{percent})<extra></extra>")
    fig.update_layout(legend=dict(orientation="h", y=-0.05, x=0.5, xanchor="center"))
    tampilkan(fig)

# ---------- Baris 2: produk dan wilayah ----------
st.subheader("Produk dan Wilayah")
kiri, kanan = st.columns(2)

with kiri:
    sub = (data.groupby("Sub-Category", as_index=False)["Sales"].sum()
           .sort_values("Sales", ascending=False).head(10).sort_values("Sales"))
    fig = px.bar(sub, x="Sales", y="Sub-Category", orientation="h",
                 title="10 Sub-Kategori dengan Penjualan Tertinggi",
                 color_discrete_sequence=[BIRU])
    fig.update_traces(texttemplate="$%{x:,.0f}", textposition="outside", cliponaxis=False,
                      hovertemplate="%{y}<br>$%{x:,.0f}<extra></extra>")
    fig.update_xaxes(title="", showticklabels=False, showgrid=False,
                     range=[0, sub["Sales"].max() * 1.25])
    fig.update_yaxes(title="")
    tampilkan(fig, 400)

with kanan:
    pivot = data.pivot_table(index="Region", columns="Category", values="Sales",
                             aggfunc="sum", fill_value=0)
    fig = px.imshow(pivot, text_auto=",.0f", aspect="auto",
                    color_continuous_scale="Blues",
                    title="Penjualan per Wilayah dan Kategori ($)")
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
    fig = px.histogram(data[data["Sales"] <= batas], x="Sales", nbins=40,
                       title="Sebaran Nilai Transaksi (95% data terbawah)",
                       color_discrete_sequence=[BIRU])
    fig.add_vline(x=median, line_dash="dash", line_color="#F59E0B",
                  annotation_text=f"Median ${median:,.0f}", annotation_position="top right")
    fig.update_xaxes(title="Nilai Transaksi ($)", tickprefix="$")
    fig.update_yaxes(title="Jumlah Transaksi")
    fig.update_traces(marker_line_width=0.5, marker_line_color="white")
    tampilkan(fig, 400)

with kanan:
    top = (data.groupby("Customer Name", as_index=False)["Sales"].sum()
           .sort_values("Sales", ascending=False).head(10)
           .rename(columns={"Customer Name": "Pelanggan", "Sales": "Total Belanja"}))
    with st.container(border=True):
        st.markdown("**10 Pelanggan dengan Belanja Terbesar**")
        st.dataframe(
            top, hide_index=True, width="stretch", height=390,
            column_config={
                "Total Belanja": st.column_config.ProgressColumn(
                    "Total Belanja", format="$%.0f",
                    min_value=0, max_value=float(top["Total Belanja"].max()),
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


def rp(angka):
    """Sama seperti ringkas(), tapi tanda $ di-escape supaya tidak dibaca sebagai rumus."""
    return ringkas(angka).replace("$", "\\$")


with st.container(border=True):
    st.markdown(
        f"""
- Kategori dengan penjualan tertinggi adalah **{per_kategori.idxmax()}** ({rp(per_kategori.max())}), dan sub-kategori terbesarnya adalah **{sub_terbaik['Sub-Category']}** ({rp(sub_terbaik['Sales'])}).
- Wilayah **{per_wilayah.idxmax()}** paling besar kontribusinya ({rp(per_wilayah.max())}), sedangkan **{per_wilayah.idxmin()}** paling kecil ({rp(per_wilayah.min())}).
- Penjualan bulanan tertinggi terjadi pada **{nama_bulan}** ({rp(bulan_terbaik['Sales'])}).
- Segmen **{per_segmen.idxmax()}** menyumbang {per_segmen.max() / per_segmen.sum() * 100:.1f}% dari total penjualan.
        """
    )

# ---------- Data mentah ----------
with st.expander("Lihat dan unduh data"):
    tabel = data.drop(columns=["Bulan", "Tahun"])
    st.dataframe(tabel, width="stretch", height=300)
    st.download_button("Unduh data terfilter (CSV)", tabel.to_csv(index=False),
                       file_name="data_terfilter.csv", mime="text/csv")

st.caption("Dashboard dibuat dengan Python dan Streamlit.")
