# %% [markdown]
# WIND ROSE

# %%
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from windrose import WindroseAxes
import os

path_folder_nc = r'C:\Users\sarah\OneDrive\Documents\TA\Timor'

lokasi_koordinat = {
    'Rote 1': {'lon': 123.229059, 'lat': -10.750426},
    'Rote 2': {'lon': 123.019667, 'lat': -10.859525},
    'Sabu 1': {'lon': 121.837516, 'lat': -10.614687},
    'Sabu 2': {'lon': 121.842286, 'lat': -10.557331}
}

def buat_wind_rose_gabungan():
    # Buka semua file .nc
    ds = xr.open_mfdataset(os.path.join(path_folder_nc, '*.nc'), combine='by_coords')
    
    # Samakan penamaan koordinat
    if 'latitude' in ds.dims:
        ds = ds.rename({'latitude': 'y', 'longitude': 'x'})

    fig = plt.figure(figsize=(14, 14))
    fig.suptitle("Wind Rose", fontsize=18, fontweight='bold', y=0.95)

    # LOOPING EKSTRAKSI & PLOTTING KE DALAM GRID
    for i, (nama_lokasi, koordinat) in enumerate(lokasi_koordinat.items()):
    
        titik_lokal = ds.sel(x=koordinat['lon'], y=koordinat['lat'], method='nearest')
        
        u_comp = titik_lokal.u10.values
        v_comp = titik_lokal.v10.values
        
        ws = np.sqrt(u_comp**2 + v_comp**2)
        wd = (270 - np.rad2deg(np.arctan2(v_comp, u_comp))) % 360

        # PLOTTING KE SUBPLOT
        ax = fig.add_subplot(2, 2, i+1, projection="windrose")
        
        # Bins 0-12 m/s 
        ax.bar(wd, ws, normed=True, opening=0.8, edgecolor='white', bins=np.arange(0, 14, 2))
        
        ax.set_title(f"{nama_lokasi}", fontsize=14, fontweight='bold', y=1.05)
        ax.set_legend(title="Kecepatan (m/s)", loc="lower center", bbox_to_anchor=(0.5, -0.2), ncol=3, fontsize=9)

    # SIMPAN GAMBAR
    plt.subplots_adjust(wspace=0.3, hspace=0.4) 
    nama_gambar = os.path.join(path_folder_nc, "Combined_Wind_Rose_4_Lokasi.png")
    
    plt.savefig(nama_gambar, bbox_inches='tight', dpi=300)
    plt.show() 
    plt.close()
    
    print(f"Selesai!disimpan di:\n{nama_gambar}")

if __name__ == "__main__":
    buat_wind_rose_gabungan()

# %% [markdown]
# MICRO SITTING

# %%
import pandas as pd
import math
import os

#LOKASI SABU 1
nama_lokasi = 'Sabu_1_Hutan_Rakyat'
jumlah_turbin = 10

lon_awal = 121.837516
lat_awal = -10.614687

arah_angin_datang = 112.5
D = 8

# Turbin butuh jarak 56 meter ke belakang (searah buangan angin)
jarak_downwind = 7 * D  
# Turbin butuh jarak 40 meter ke samping (tegak lurus arah angin)
jarak_crosswind = 5 * D 

# Menghitung sudut
arah_downwind = (arah_angin_datang + 180) % 360  
arah_crosswind = (arah_downwind + 90) % 360     

# SPASIAL
def hitung_koordinat_baru(lon, lat, jarak_m, bearing_deg):
    R_BUMI = 6378137.0 # Radius bumi
    
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    bearing_rad = math.radians(bearing_deg)
    
    lat_baru = math.asin(math.sin(lat_rad) * math.cos(jarak_m / R_BUMI) +
                         math.cos(lat_rad) * math.sin(jarak_m / R_BUMI) * math.cos(bearing_rad))
    
    lon_baru = lon_rad + math.atan2(math.sin(bearing_rad) * math.sin(jarak_m / R_BUMI) * math.cos(lat_rad),
                                    math.cos(jarak_m / R_BUMI) - math.sin(lat_rad) * math.sin(lat_baru))
    
    return math.degrees(lon_baru), math.degrees(lat_baru)

# PEMBUATAN GRID TURBIN
data_turbin = []
grid_size = math.ceil(math.sqrt(jumlah_turbin)) 

id_turbin = 1
for baris in range(grid_size):       
    for kolom in range(grid_size):   
        if id_turbin > jumlah_turbin:
            break
            
        # 1. Tentukan titik geser ke samping dulu
        jarak_x = kolom * jarak_crosswind
        lon_temp, lat_temp = hitung_koordinat_baru(lon_awal, lat_awal, jarak_x, arah_crosswind)
        
        # 2. Dari titik samping, tarik garis ke belakang
        jarak_y = baris * jarak_downwind
        lon_final, lat_final = hitung_koordinat_baru(lon_temp, lat_temp, jarak_y, arah_downwind)
        
        data_turbin.append({
            'ID_Turbin': f"WT_{id_turbin:02d}",
            'Longitude': lon_final,
            'Latitude': lat_final
        })
        id_turbin += 1
        
# SIMPAN KE CSV
path_folder = r'C:\Users\sarah\OneDrive\Documents\TA\Timor'
path_csv = os.path.join(path_folder, f'Layout_Turbin_{nama_lokasi}.csv')

df_layout = pd.DataFrame(data_turbin)
df_layout.to_csv(path_csv, index=False)

# %%
import pandas as pd
import math
import os

# LOKASI (SABU 2)
nama_lokasi = 'Sabu_2_Tanaman_Pangan'
jumlah_turbin = 10

lon_awal = 121.842286
lat_awal = -10.557331

arah_angin_datang = 112.5
D = 8 

# Turbin butuh jarak 56 meter ke belakang (searah buangan angin)
jarak_downwind = 7 * D  
# Turbin butuh jarak 40 meter ke samping (tegak lurus arah angin)
jarak_crosswind = 5 * D 

# Menghitung sudut
arah_downwind = (arah_angin_datang + 180) % 360  
arah_crosswind = (arah_downwind + 90) % 360      

# SPASIAL 
def hitung_koordinat_baru(lon, lat, jarak_m, bearing_deg):
    R_BUMI = 6378137.0 # Radius bumi
    
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    bearing_rad = math.radians(bearing_deg)
    
    lat_baru = math.asin(math.sin(lat_rad) * math.cos(jarak_m / R_BUMI) +
                         math.cos(lat_rad) * math.sin(jarak_m / R_BUMI) * math.cos(bearing_rad))
    
    lon_baru = lon_rad + math.atan2(math.sin(bearing_rad) * math.sin(jarak_m / R_BUMI) * math.cos(lat_rad),
                                    math.cos(jarak_m / R_BUMI) - math.sin(lat_rad) * math.sin(lat_baru))
    
    return math.degrees(lon_baru), math.degrees(lat_baru)

# PEMBUATAN GRID TURBIN
data_turbin = []
grid_size = math.ceil(math.sqrt(jumlah_turbin)) 

id_turbin = 1
for baris in range(grid_size):       
    for kolom in range(grid_size):   
        if id_turbin > jumlah_turbin:
            break
            
        # 1. Tentukan titik geser ke samping dulu
        jarak_x = kolom * jarak_crosswind
        lon_temp, lat_temp = hitung_koordinat_baru(lon_awal, lat_awal, jarak_x, arah_crosswind)
        
        # 2. Dari titik samping, tarik garis ke belakang
        jarak_y = baris * jarak_downwind
        lon_final, lat_final = hitung_koordinat_baru(lon_temp, lat_temp, jarak_y, arah_downwind)
        
        data_turbin.append({
            'ID_Turbin': f"WT_{id_turbin:02d}",
            'Longitude': lon_final,
            'Latitude': lat_final
        })
        id_turbin += 1
        
# SIMPAN KE CSV
path_folder = r'C:\Users\sarah\OneDrive\Documents\TA\Timor'
path_csv = os.path.join(path_folder, f'Layout_Turbin_{nama_lokasi}.csv')

df_layout = pd.DataFrame(data_turbin)
df_layout.to_csv(path_csv, index=False)

# %%
import pandas as pd
import math
import os

nama_lokasi = 'Rote 1'
jumlah_turbin = 10 

#Titik Koordinat Pusat
lon_awal = 123.229059
lat_awal = -10.750426

arah_angin_datang = 112.5
D = 8 

# Turbin butuh jarak 56 meter ke belakang (searah buangan angin)
jarak_downwind = 7 * D  

# Turbin butuh jarak 40 meter ke samping (tegak lurus arah angin)
jarak_crosswind = 5 * D 

arah_downwind = (arah_angin_datang + 180) % 360  
arah_crosswind = (arah_downwind + 90) % 360    

# SPASIAL
def hitung_koordinat_baru(lon, lat, jarak_m, bearing_deg):
    R_BUMI = 6378137.0 
    
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    bearing_rad = math.radians(bearing_deg)
    
    lat_baru = math.asin(math.sin(lat_rad) * math.cos(jarak_m / R_BUMI) +
                         math.cos(lat_rad) * math.sin(jarak_m / R_BUMI) * math.cos(bearing_rad))
    
    lon_baru = lon_rad + math.atan2(math.sin(bearing_rad) * math.sin(jarak_m / R_BUMI) * math.cos(lat_rad),
                                    math.cos(jarak_m / R_BUMI) - math.sin(lat_rad) * math.sin(lat_baru))
    
    return math.degrees(lon_baru), math.degrees(lat_baru)

# PEMBUATAN GRID TURBIN
data_turbin = []
grid_size = math.ceil(math.sqrt(jumlah_turbin)) 

id_turbin = 1
for baris in range(grid_size):       
    for kolom in range(grid_size):   
        if id_turbin > jumlah_turbin:
            break
            
        # 1. Tentukan titik geser ke samping dulu
        jarak_x = kolom * jarak_crosswind
        lon_temp, lat_temp = hitung_koordinat_baru(lon_awal, lat_awal, jarak_x, arah_crosswind)
        
        # 2. Dari titik samping, tarik garis ke belakang
        jarak_y = baris * jarak_downwind
        lon_final, lat_final = hitung_koordinat_baru(lon_temp, lat_temp, jarak_y, arah_downwind)
        
        data_turbin.append({
            'ID_Turbin': f"WT_{id_turbin:02d}",
            'Longitude': lon_final,
            'Latitude': lat_final
        })
        id_turbin += 1
        
# 5. SIMPAN KE CSV
path_folder = r'C:\Users\sarah\OneDrive\Documents\TA\Timor'
path_csv = os.path.join(path_folder, f'Layout_Turbin_{nama_lokasi}.csv')

df_layout = pd.DataFrame(data_turbin)
df_layout.to_csv(path_csv, index=False)

# %%
import pandas as pd
import math
import os

# LOKASI (ROTE 2)
nama_lokasi = 'Rote_2_fix'
jumlah_turbin_moga = 10 
baris_downwind = 4   
kolom_crosswind = 3   

lon_awal = 123.019667
lat_awal = -10.859525

arah_angin_datang = 112.5
D = 8 
jarak_downwind = 7 * D  
jarak_crosswind = 5 * D 

# Menghitung sudut 
arah_downwind = (arah_angin_datang + 180) % 360  
arah_crosswind = (arah_downwind + 90) % 360      

# SPASIAL
def hitung_koordinat_baru(lon, lat, jarak_m, bearing_deg):
    R_BUMI = 6378137.0 # Radius bumi
    
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    bearing_rad = math.radians(bearing_deg)
    
    lat_baru = math.asin(math.sin(lat_rad) * math.cos(jarak_m / R_BUMI) +
                         math.cos(lat_rad) * math.sin(jarak_m / R_BUMI) * math.cos(bearing_rad))
    
    lon_baru = lon_rad + math.atan2(math.sin(bearing_rad) * math.sin(jarak_m / R_BUMI) * math.cos(lat_rad),
                                    math.cos(jarak_m / R_BUMI) - math.sin(lat_rad) * math.sin(lat_baru))
    
    return math.degrees(lon_baru), math.degrees(lat_baru)

# PEMBUATAN GRID TURBIN 
data_turbin = []
id_turbin = 1

for baris in range(baris_downwind):      
    for kolom in range(kolom_crosswind):  
        
        if id_turbin <= jumlah_turbin_moga:
            
            # 1. Tentukan titik geser ke samping dulu (Crosswind)
            jarak_x = kolom * jarak_crosswind
            lon_temp, lat_temp = hitung_koordinat_baru(lon_awal, lat_awal, jarak_x, arah_crosswind)
            
            # 2. Tarik garis ke belakang (Downwind)
            jarak_y = baris * jarak_downwind
            lon_final, lat_final = hitung_koordinat_baru(lon_temp, lat_temp, jarak_y, arah_downwind)
            
            data_turbin.append({
                'ID_Turbin': f"WT_{id_turbin:02d}",
                'Longitude': lon_final,
                'Latitude': lat_final
            })
            id_turbin += 1

# SIMPAN KE CSV
path_folder = r'C:\Users\sarah\OneDrive\Documents\TA\Timor'
path_csv = os.path.join(path_folder, f'Layout_Turbin_{nama_lokasi}.csv')

df_layout = pd.DataFrame(data_turbin)
df_layout.to_csv(path_csv, index=False)


