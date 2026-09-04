# %% [markdown]
# DOWNSCALE DAN VALIDASI

# %%
import xarray as xr
import numpy as np
import rioxarray
import os

path_folder_nc = r'C:\Users\sarah\OneDrive\Documents\TA\Timor'
path_file_gwa = r'C:\Users\sarah\OneDrive\Documents\TA\Data\gwantt.tif'
output_folder = r'C:\Users\sarah\OneDrive\Documents\TA\Output'

z0 = 0.02

# GWA
print("Membaca GWA...")

gwa = rioxarray.open_rasterio(
    path_file_gwa).squeeze()

# ERA5
print("Membaca ERA5...")

ds = xr.open_mfdataset(
    os.path.join(path_folder_nc,"*.nc"),
    combine="by_coords")

# WS10
print("Menghitung WS10...")

ws10 = np.sqrt(
    ds.u10**2 +
    ds.v10**2)

# KLIMATOLOGI
print("Menghitung klimatologi...")

era5_mean = ws10.mean(
    dim="valid_time")

# INTERPOLASI GWA
print("Interpolasi GWA")

gwa_on_era5 = gwa.interp(
    x=era5_mean.longitude,
    y=era5_mean.latitude,
    method="linear")

gwa_on_era5 = gwa_on_era5.fillna(
    gwa_on_era5.mean())

# CF
print("Menghitung CF...")

CF = gwa_on_era5 / era5_mean

CF = CF.clip(
    min=0.5,
    max=3)

print(CF.shape)
print(CF.dims)

# DOWNSCALING
print("Downscaling WS10...")

ws10_ds = ws10 * CF

# SIMPAN WS10
output_ws10 = os.path.join(
    output_folder,
    "WS10_Downscaled.nc")

ws10_ds.to_netcdf(
    output_ws10)

# 24 m
factor24 = (
    np.log(24/z0)
    /
    np.log(10/z0))

ws24_ds = ws10_ds * factor24

# SIMPAN WS24
output_ws24 = os.path.join(
    output_folder,
    "WS24_Downscaled.nc")

ws24_ds.to_netcdf(
    output_ws24)

print("SELESAI")

# %%
import rioxarray
import xarray as xr

# FUNGSI SIMPAN TIFF
def save_tif(da, output_file):

    print(f"\nMenyimpan: {output_file}")

    da = da.drop_vars(
        ["x", "y"],
        errors="ignore"
    )

    # ubah dimensi ke format raster

    if da.dims == ("latitude", "longitude"):

        da = da.rename(
            {
                "latitude": "y",
                "longitude": "x"
            }
        )

    elif da.dims == ("y", "x"):

        pass

    else:

        print("Dimensi tidak dikenali:")
        print(da.dims)

        raise ValueError(
            "Periksa dimensi data"
        )

    # CRS
    da = da.rio.write_crs(
        "EPSG:4326"
    )

    da.astype(
        "float32"
    ).rio.to_raster(
        output_file
    )

    print("Berhasil")

# OUTPUT FOLDER
folder_out = r"C:\Users\sarah\OneDrive\Documents\TA\Output"

# WS24 MEAN
save_tif(
    ws250,
    rf"{folder_out}\WS24_Mean_250m.tif"
)

# WEIBULL K
save_tif(
    k250,
    rf"{folder_out}\Weibull_k_250m.tif"
)

# WEIBULL C
save_tif(
    c250,
    rf"{folder_out}\Weibull_c_250m.tif"
)

# WPD
save_tif(
    wpd250,
    rf"{folder_out}\WPD_250m.tif"
)

print("\nOutput:")

print(
    rf"{folder_out}\WS_FINAL.tif"
)

print(
    rf"{folder_out}\Weibull_k_250m.tif"
)

print(
    rf"{folder_out}\Weibull_c_250m.tif"
)

print(
    rf"{folder_out}\WPD_250m.tif"
)

# %%
import pandas as pd
import numpy as np
import xarray as xr
import glob
import os

from scipy.stats import pearsonr
from sklearn.metrics import mean_squared_error
from sklearn.metrics import mean_absolute_error

import matplotlib.pyplot as plt

# PATH

folder_bmkg = r'C:\Users\sarah\OneDrive\Documents\TA\Timor\RoteNdao'
path_nc = r'C:\Users\sarah\OneDrive\Documents\TA\Output\WS10_Downscaled.nc'

# KOORDINAT STASIUN
lat_stn = -10.76662
lon_stn = 123.07395

# BACA DATA BMKG

print("Membaca data BMKG...")

all_files = [
    f for f in glob.glob(
        os.path.join(folder_bmkg, "*.xlsx")
    )
    if not os.path.basename(f).startswith("~$")
]

list_df = []

for f in all_files:

    try:

        raw_df = pd.read_excel(
            f,
            header=None,
            engine="openpyxl"
        )

        header_row = 0

        for i, row in raw_df.iterrows():

            if row.astype(str).str.contains(
                "TANGGAL",
                case=False
            ).any():

                header_row = i
                break

        temp_df = pd.read_excel(
            f,
            skiprows=header_row,
            engine="openpyxl"
        )

        temp_df.columns = [
            str(c).strip().upper()
            for c in temp_df.columns
        ]

        temp_df = temp_df[
            ["TANGGAL", "FF_AVG"]
        ]

        temp_df.columns = [
            "tanggal",
            "ws_bmkg"
        ]

        list_df.append(temp_df)

        print(
            f"Berhasil: {os.path.basename(f)}"
        )

    except Exception as e:

        print(
            f"Gagal: {os.path.basename(f)}"
        )

        print(e)

# GABUNG DATA BMKG
df_obs = pd.concat(
    list_df,
    ignore_index=True
)

df_obs["tanggal"] = pd.to_datetime(
    df_obs["tanggal"],
    dayfirst=True,
    errors="coerce"
)

df_obs["ws_bmkg"] = pd.to_numeric(
    df_obs["ws_bmkg"],
    errors="coerce"
)

df_obs = df_obs.dropna()

# hapus duplikat tanggal
df_obs = (
    df_obs
    .groupby("tanggal")
    ["ws_bmkg"]
    .mean()
    .reset_index()
)

df_obs = (
    df_obs
    .sort_values("tanggal")
    .reset_index(drop=True)
)

print()
print("Jumlah data BMKG :", len(df_obs))

# BACA WS10 DOWNSCALED
ds = xr.open_dataset(path_nc)

print(ds)

# AMBIL VARIABEL
varname = list(ds.data_vars)[0]

ws = ds[varname]

# GRID TERDEKAT STASIUN
ws_stn = ws.sel(
    latitude=lat_stn,
    longitude=lon_stn,
    method="nearest"
)

print("\nGrid yang dipakai:")

print(
    "Lat =",
    float(ws_stn.latitude.values)
)

print(
    "Lon =",
    float(ws_stn.longitude.values)
)

# DATAFRAME MODEL
df_sim = (
    ws_stn
    .to_dataframe(
        name="ws_sim"
    )
    .reset_index()
)

# hanya ambil kolom yang dibutuhkan
df_sim = df_sim[
    [
        "valid_time",
        "ws_sim"
    ]
]

# HARIAN
df_sim = (
    df_sim
    .set_index("valid_time")
    .resample("D")
    .mean()
    .reset_index()
)

df_sim.columns = [
    "tanggal",
    "ws_sim"
]

print(
    "\nJumlah data model :",
    len(df_sim)
)

# MERGE
df = pd.merge(
    df_obs,
    df_sim,
    on="tanggal",
    how="inner"
)

df = df.dropna()

print(
    "\nJumlah data cocok :",
    len(df)
)

# METRIK
obs = df["ws_bmkg"].values

sim = df["ws_sim"].values

bias = np.mean(
    sim - obs
)

rmse = np.sqrt(
    mean_squared_error(
        obs,
        sim
    )
)

mae = mean_absolute_error(
    obs,
    sim
)

r, p = pearsonr(
    obs,
    sim
)

mask = obs > 0

mape = np.mean(
    np.abs(
        (sim[mask] - obs[mask])
        /
        obs[mask]
    )
) * 100

# HASIL
print(
    f"Bias      : {bias:.3f} m/s"
)

print(
    f"RMSE      : {rmse:.3f} m/s"
)

print(
    f"MAE       : {mae:.3f} m/s"
)

print(
    f"Korelasi  : {r:.3f}"
)

print(
    f"P-value   : {p:.5f}"
)

print(
    f"MAPE      : {mape:.2f} %"
)

# SCATTER
plt.figure(figsize=(6,6))

plt.scatter(
    obs,
    sim,
    alpha=0.7
)

plt.plot(
    [obs.min(), obs.max()],
    [obs.min(), obs.max()],
    'r--'
)

plt.xlabel("BMKG (m/s)")
plt.ylabel("WS10 Downscaled (m/s)")
plt.title(f"R = {r:.3f}")

plt.grid(True)

plt.show()

# TIMESERIES
plt.figure(figsize=(14,5))

plt.plot(
    df["tanggal"],
    df["ws_bmkg"],
    label="BMKG"
)

plt.plot(
    df["tanggal"],
    df["ws_sim"],
    label="WS10 Downscaled"
)

plt.legend()

plt.grid(True)

plt.ylabel("Wind Speed (m/s)")

plt.title(
    "BMKG vs WS10 Downscaled"
)

plt.show()

# %%
import pandas as pd
import numpy as np
import xarray as xr
import glob
import os

from scipy.stats import pearsonr
from sklearn.metrics import mean_squared_error
from sklearn.metrics import mean_absolute_error

import matplotlib.pyplot as plt


folder_bmkg = r'C:\Users\sarah\OneDrive\Documents\TA\Timor\RoteNdao'
path_folder = r'C:\Users\sarah\OneDrive\Documents\TA\Timor'

lat_stn = -10.76662
lon_stn = 123.07395

# BACA DATA BMKG
all_files = [
    f for f in glob.glob(
        os.path.join(folder_bmkg, "*.xlsx")
    )
    if not os.path.basename(f).startswith("~$")
]

list_df = []

for f in all_files:

    try:

        raw_df = pd.read_excel(
            f,
            header=None,
            engine="openpyxl"
        )

        header_row = 0

        for i, row in raw_df.iterrows():

            if row.astype(str).str.contains(
                "TANGGAL",
                case=False
            ).any():

                header_row = i
                break

        temp_df = pd.read_excel(
            f,
            skiprows=header_row,
            engine="openpyxl"
        )

        temp_df.columns = [
            str(c).strip().upper()
            for c in temp_df.columns
        ]

        temp_df = temp_df[
            ["TANGGAL","FF_AVG"]
        ]

        temp_df.columns = [
            "tanggal",
            "ws_bmkg"
        ]

        list_df.append(temp_df)

        print(
            f"Berhasil : {os.path.basename(f)}"
        )

    except Exception as e:

        print(
            f"Gagal : {os.path.basename(f)}"
        )

        print(e)

# GABUNG DATA BMKG
df_obs = pd.concat(
    list_df,
    ignore_index=True
)

df_obs["tanggal"] = pd.to_datetime(
    df_obs["tanggal"],
    dayfirst=True,
    errors="coerce"
)

df_obs["ws_bmkg"] = pd.to_numeric(
    df_obs["ws_bmkg"],
    errors="coerce"
)

df_obs = df_obs.dropna()

df_obs = (
    df_obs
    .groupby("tanggal")
    ["ws_bmkg"]
    .mean()
    .reset_index()
)

df_obs = (
    df_obs
    .sort_values("tanggal")
    .reset_index(drop=True)
)

print()
print(
    "Jumlah data BMKG :",
    len(df_obs)
)

# BACA ERA5
files_nc = glob.glob(
    os.path.join(
        path_folder,
        "timor*.nc"
    )
)

ds = xr.open_mfdataset(
    files_nc,
    combine="by_coords"
)

print(ds)

# HITUNG WS DARI U10 DAN V10
ws = np.sqrt(
    ds.u10**2 +
    ds.v10**2
)

# AMBIL GRID TERDEKAT
ws_stn = ws.sel(
    latitude=lat_stn,
    longitude=lon_stn,
    method="nearest"
)

df_sim = (
    ws_stn
    .to_dataframe(
        name="ws_sim"
    )
    .reset_index()
)

df_sim = df_sim[
    [
        "valid_time",
        "ws_sim"
    ]
]

# RESAMPLE HARIAN
df_sim = (
    df_sim
    .set_index("valid_time")
    .resample("D")
    .mean()
    .reset_index()
)

df_sim.columns = [
    "tanggal",
    "ws_sim"
]
# MERGE
df = pd.merge(
    df_obs,
    df_sim,
    on="tanggal",
    how="inner"
)

df = df.dropna()

# METRIK VALIDASI
bias = np.mean(
    sim - obs
)

rmse = np.sqrt(
    mean_squared_error(
        obs,
        sim
    )
)

mae = mean_absolute_error(
    obs,
    sim
)

r, p = pearsonr(
    obs,
    sim
)

mask = obs > 0


# HASIL VALIDASI
print("\n===== ERA5 vs BMKG =====")

print(
    f"Bias      : {bias:.3f} m/s"
)

print(
    f"RMSE      : {rmse:.3f} m/s"
)

print(
    f"MAE       : {mae:.3f} m/s"
)

print(
    f"R         : {r:.3f}"
)

# SCATTER PLOtT
plt.figure(figsize=(6,6))

plt.scatter(
    obs,
    sim,
    alpha=0.7
)

plt.plot(
    [obs.min(), obs.max()],
    [obs.min(), obs.max()],
    'r--',
    linewidth=2
)

plt.xlabel("BMKG (m/s)")
plt.ylabel("ERA5 (m/s)")

plt.title(
    f"ERA5 vs BMKG (R = {r:.3f})"
)

plt.grid(True)

plt.tight_layout()

plt.show()

# TIME SERIES
plt.figure(figsize=(14,5))

plt.plot(
    df["tanggal"],
    df["ws_bmkg"],
    label="BMKG",
    linewidth=1.5
)

plt.plot(
    df["tanggal"],
    df["ws_sim"],
    label="ERA5",
    linewidth=1.5
)

plt.legend()

plt.grid(True)

plt.ylabel("Wind Speed (m/s)")
plt.xlabel("Date")

plt.title(
    "Daily Wind Speed: ERA5 vs BMKG"
)

plt.tight_layout()

plt.show()


