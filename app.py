import pandas as pd
import plotly.express as px
import streamlit as st

# ---------- Pengaturan halaman ----------
st.set_page_config(page_title="Dashboard Penjualan Superstore", page_icon="📊", layout="wide")


# ---------- Load data ----------
@st.cache_data
def load_data():
    df = pd.read_csv("train.csv")
    df["Order Date"] = pd.to_datetime(df["Order Date"], dayfirst=True)
    df["Tahun"] = df["Order Date"].dt.year
    df["Bulan"] = df["Order Date"].dt.to_period("M").dt.to_timestamp()
    return df


df = load_data()

# ---------- Judul dan deskripsi ----------
st.title("📊 Dashboard Penjualan Superstore")
st.write(
    "Dashboard ini menampilkan ringkasan data penjualan sebuah toko ritel di Amerika Serikat "
    "(dataset Superstore Sales dari Kaggle). Kamu bisa melihat total penjualan, jumlah pesanan, "
    "dan pelanggan, serta pola penjualan berdasarkan kategori, wilayah, segmen, dan waktu. "
    "Gunakan filter di sebelah kiri untuk mengubah data yang ditampilkan."
)

# ---------- Filter (sidebar) ----------
st.sidebar.header("Filter Data")

region = st.sidebar.multiselect(
    "Wilayah (Region)", sorted(df["Region"].unique()), default=sorted(df["Region"].unique())
)
category = st.sidebar.multiselect(
    "Kategori", sorted(df["Category"].unique()), default=sorted(df["Category"].unique())
)
segment = st.sidebar.multiselect(
    "Segmen Pelanggan", sorted(df["Segment"].unique()), default=sorted(df["Segment"].unique())
)
tahun = st.sidebar.slider(
    "Rentang Tahun",
    int(df["Tahun"].min()),
    int(df["Tahun"].max()),
    (int(df["Tahun"].min()), int(df["Tahun"].max())),
)

data = df[
    df["Region"].isin(region)
    & df["Category"].isin(category)
    & df["Segment"].isin(segment)
    & df["Tahun"].between(tahun[0], tahun[1])
]

if data.empty:
    st.warning("Tidak ada data untuk filter yang dipilih. Coba ubah filternya.")
    st.stop()

# ---------- KPI ----------
total_sales = data["Sales"].sum()
total_order = data["Order ID"].nunique()
total_customer = data["Customer ID"].nunique()
rata_order = total_sales / total_order

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Penjualan", f"${total_sales:,.0f}")
k2.metric("Jumlah Pesanan", f"{total_order:,}")
k3.metric("Jumlah Pelanggan", f"{total_customer:,}")
k4.metric("Rata-rata Nilai Pesanan", f"${rata_order:,.2f}")

st.divider()

# ---------- Visualisasi ----------
# 1. Line chart: tren penjualan per bulan
tren = data.groupby("Bulan", as_index=False)["Sales"].sum()
fig_line = px.line(tren, x="Bulan", y="Sales", markers=True, title="Tren Penjualan per Bulan")
fig_line.update_layout(xaxis_title="Bulan", yaxis_title="Penjualan ($)")
st.plotly_chart(fig_line, width="stretch")

c1, c2 = st.columns(2)

# 2. Bar chart: penjualan per sub-kategori
sub = (
    data.groupby("Sub-Category", as_index=False)["Sales"].sum().sort_values("Sales")
)
fig_bar = px.bar(sub, x="Sales", y="Sub-Category", orientation="h", title="Penjualan per Sub-Kategori")
fig_bar.update_layout(xaxis_title="Penjualan ($)", yaxis_title="")
c1.plotly_chart(fig_bar, width="stretch")

# 3. Pie chart: proporsi penjualan per segmen
seg = data.groupby("Segment", as_index=False)["Sales"].sum()
fig_pie = px.pie(seg, names="Segment", values="Sales", title="Proporsi Penjualan per Segmen")
c2.plotly_chart(fig_pie, width="stretch")

c3, c4 = st.columns(2)

# 4. Histogram: sebaran nilai penjualan per transaksi
fig_hist = px.histogram(
    data[data["Sales"] <= data["Sales"].quantile(0.95)],
    x="Sales",
    nbins=40,
    title="Sebaran Nilai Penjualan per Transaksi (95% data terbawah)",
)
fig_hist.update_layout(xaxis_title="Nilai Penjualan ($)", yaxis_title="Jumlah Transaksi")
c3.plotly_chart(fig_hist, width="stretch")

# 5. Heatmap: penjualan berdasarkan wilayah dan kategori
pivot = data.pivot_table(index="Region", columns="Category", values="Sales", aggfunc="sum", fill_value=0)
fig_heat = px.imshow(
    pivot, text_auto=".0f", aspect="auto", color_continuous_scale="Blues",
    title="Penjualan per Wilayah dan Kategori ($)",
)
c4.plotly_chart(fig_heat, width="stretch")

# ---------- Tabel data ----------
with st.expander("Lihat data mentah"):
    st.dataframe(data, width="stretch")

st.caption("Sumber data: Kaggle - Superstore Sales Dataset")
