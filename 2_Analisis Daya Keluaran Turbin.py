# %%
import xarray as xr
import numpy as np
import rioxarray
import pandas as pd
import os
import glob
from scipy.special import gamma

path_folder = r'C:\Users\sarah\OneDrive\Documents\TA\Timor'
path_tif = os.path.join(
    path_folder,
    "WS_FINAL.tif"
)

# LOKASI TERBAIK
daftar_lokasi = [

    {
        "nama":"Sabu_1",
        "lon":121.837516,
        "lat":-10.614687
    },

    {
        "nama":"Sabu_2",
        "lon":121.842286,
        "lat":-10.557330
    },

    {
        "nama":"Rote_1",
        "lon":123.229059,
        "lat":-10.750426
    },

    {
        "nama":"Rote_2",
        "lon":123.019667,
        "lat":-10.859525
    }

]

# POWER CURVE AEOLOS
ws_curve = np.array([
    0,2,3,4,5,6,7,8,9,10,
    11,12,13,14,15,16,17,18,19,20
])

power_curve = np.array([
    0,0,0.1,0.3,0.8,1.7,3.2,5.0,7.2,10.0,
    11,11,11,11,11,11,11,11,0,0
])

RATED_POWER = 10.0

# BACA WS_FINAL
raster = rioxarray.open_rasterio(
    path_tif
).squeeze()

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

summary_list = []

# LOOP LOKASI
for loc in daftar_lokasi:

    print(loc["nama"])

    # WS TARGET DARI TIFF
    ws_target = raster.sel(
        x=loc["lon"],
        y=loc["lat"],
        method="nearest"
    ).values

    ws_target = float(ws_target)

    print(
        "WS_FINAL :",
        round(ws_target,2),
        "m/s"
    )

    # ERA5 TIME SERIES
    ds_point = ds.sel(
        latitude=loc["lat"],
        longitude=loc["lon"],
        method="nearest"
    ).load()

    ws_era5 = np.sqrt(
        ds_point.u10.values**2 +
        ds_point.v10.values**2
    )

    mean_era5 = np.mean(
        ws_era5
    )

    print(
        "ERA5 Mean :",
        round(mean_era5,2)
    )

    # SCALING KE WS_FINAL
    scaling_factor = (
        ws_target /
        mean_era5
    )

    print(
        "Scaling Factor :",
        round(scaling_factor,3)
    )

    ws_final = (
        ws_era5 *
        scaling_factor
    )

    # POWER CURVE
    p_out = np.interp(
        ws_final,
        ws_curve,
        power_curve
    )

    p_out[
        ws_final < 2.5
    ] = 0

    p_out[
        ws_final >= 25
    ] = 0

    # SIMPAN INPUT GA
    waktu = pd.to_datetime(
        ds_point.valid_time.values
    )

    df_lokasi = pd.DataFrame({

        "Waktu": waktu,

        "WS_24m_ms":
        np.round(
            ws_final,
            2
        ),

        "P_Aeolos_kW":
        np.round(
            p_out,
            3
        )

    })

    nama_csv = os.path.join(
        path_folder,
        f"Input_GA_{loc['nama']}.csv"
    )

    df_lokasi.to_csv(
        nama_csv,
        index=False
    )

    print(
        "CSV disimpan:",
        nama_csv
    )

    # STATISTIK
    ws_mean = np.mean(
        ws_final
    )

    power_mean = np.mean(
        p_out
    )

    power_max = np.max(
        p_out
    )

    aep_kwh = (
        power_mean *
        8760
    )

    aep_mwh = (
        aep_kwh /
        1000
    )

    cf = (
        power_mean /
        RATED_POWER
    ) * 100
    # PARAMETER WEIBULL
    ws_std = np.std(
        ws_final
    )

    k = (
        ws_std /
        ws_mean
    ) ** (-1.086)

    c = (
        ws_mean /
        gamma(
            1 + (1 / k)
        )
    )

    print(
        "Weibull k :",
        round(k,2)
    )

    print(
        "Weibull c :",
        round(c,2),
        "m/s"
    )

    summary_list.append({

        "Lokasi":
        loc["nama"],

        "WS Mean (m/s)":
        round(
            ws_mean,
            2
        ),

        "k":
        round(
            k,
            2
        ),

        "c (m/s)":
        round(
            c,
            2
        ),

        "Power Mean (kW)":
        round(
            power_mean,
            2
        ),

        "Power Max (kW)":
        round(
            power_max,
            2
        ),

        "AEP (MWh/tahun)":
        round(
            aep_mwh,
            2
        ),

        "CF (%)":
        round(
            cf,
            2
        )

    })

    # TABEL HASIL
    df_res = pd.DataFrame(
        summary_list
    )

    print(
        df_res.to_string(
            index=False
        )
    )

    # SIMPAN EXCEL
    output_excel = os.path.join(
        path_folder,
        "Ringkasan_AEP_CF.xlsx"
    )

    df_res.to_excel(
        output_excel,
        index=False
    )

print("\nExcel disimpan:")
print(output_excel)

# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os


path_folder = r'C:\Users\sarah\OneDrive\Documents\TA\Timor'
csv_files = [

    os.path.join(path_folder,'Input_GA_Sabu_1.csv'),
    os.path.join(path_folder,'Input_GA_Sabu_2.csv'),
    os.path.join(path_folder,'Input_GA_Rote_1.csv'),
    os.path.join(path_folder,'Input_GA_Rote_2.csv')

]
lokasi = [

    'Sabu 1',
    'Sabu 2',
    'Rote 1',
    'Rote 2'
]

# LOAD DATA
data_all = []

for file in csv_files:

    df = pd.read_csv(file)

    df["Waktu"] = pd.to_datetime(df["Waktu"])

    data_all.append(df)

# DISTRIBUSI DAYA
fig, axes = plt.subplots(
    2,2,
    figsize=(14,10)
)

axes = axes.flatten()

for i, df in enumerate(data_all):

    ax = axes[i]

    daya = df["P_Aeolos_kW"]

    bins = np.arange(
        0,
        daya.max()+0.5,
        0.5
    )

    ax.hist(
        daya,
        bins=bins,
        color='skyblue',
        edgecolor='black',
        alpha=0.8
    )

    ax.axvline(
        daya.mean(),
        color='red',
        linestyle='--',
        linewidth=2,
        label=f'Mean = {daya.mean():.2f} kW'
    )

    ax.set_title(
        lokasi[i],
        fontweight='bold'
    )

    ax.set_xlabel('Daya (kW)')
    ax.set_ylabel('Frekuensi (Jam)')
    ax.legend()
    ax.grid(alpha=0.3)

fig.suptitle(
    'Distribusi Daya Turbin',
    fontsize=18,
    fontweight='bold'
)

plt.tight_layout()

plt.savefig(
    os.path.join(
        path_folder,
        'Distribusi_Daya_4Lokasi.png'
    ),
    dpi=300
)

# BOXPLOT MONSUN
fig, axes = plt.subplots(
    2,2,
    figsize=(14,10)
)

axes = axes.flatten()

for i, df in enumerate(data_all):

    ax = axes[i]

    df2025 = df[
        df["Waktu"].dt.year == 2025
    ]

    monsun_barat = df2025[
        df2025["Waktu"].dt.month.isin(
            [1,2]
        )
    ]

    monsun_timur = df2025[
        df2025["Waktu"].dt.month.isin(
            [6,7,8]
        )
    ]

    ax.boxplot(
        [
            monsun_barat["P_Aeolos_kW"],
            monsun_timur["P_Aeolos_kW"]
        ],
        tick_labels=[
            'Monsun Barat',
            'Monsun Timur'
        ]
    )

    ax.set_title(
        lokasi[i],
        fontweight='bold'
    )

    ax.set_ylabel(
        'Daya (kW)'
    )

    ax.grid(
        alpha=0.3
    )

fig.suptitle(
    'Perbandingan Daya Keluaran Saat Monsun Barat dan Monsun Timur (2025)',
    fontsize=18,
    fontweight='bold'
)

plt.tight_layout()

plt.savefig(
    os.path.join(
        path_folder,
        'Boxplot_Monsun_4Lokasi.png'
    ),
    dpi=300
)

# DIURNAL
fig, axes = plt.subplots(
    2,2,
    figsize=(14,10)
)

axes = axes.flatten()

for i, df in enumerate(data_all):

    ax = axes[i]

    df2025 = df[
        df["Waktu"].dt.year == 2025
    ].copy()

    df2025["Jam"] = (
        df2025["Waktu"]
        .dt.hour
    )

    diurnal = (

        df2025

        .groupby("Jam")

        ["P_Aeolos_kW"]

        .mean()

    )

    jam_max = diurnal.idxmax()
    nilai_max = diurnal.max()

    jam_min = diurnal.idxmin()
    nilai_min = diurnal.min()

    ax.plot(
        diurnal.index,
        diurnal.values,
        marker='o',
        linewidth=2
    )

    ax.scatter(
        jam_max,
        nilai_max,
        color='red',
        s=80
    )

    ax.scatter(
        jam_min,
        nilai_min,
        color='green',
        s=80
    )

    ax.set_title(
        f"{lokasi[i]}\n"
        f"Max = {jam_max:02d}:00 | Min = {jam_min:02d}:00",
        fontweight='bold'
    )

    ax.set_xlabel(
        'Jam Lokal'
    )

    ax.set_ylabel(
        'Daya (kW)'
    )

    ax.set_xticks(
        range(24)
    )

    ax.grid(
        alpha=0.3
    )

fig.suptitle(
    'Pola Diurnal Daya Keluaran Turbin Tahun 2025',
    fontsize=18,
    fontweight='bold'
)

plt.tight_layout()

plt.savefig(
    os.path.join(
        path_folder,
        'Diurnal_4Lokasi.png'
    ),
    dpi=300
)


