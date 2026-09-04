# %%
import pandas as pd
import numpy as np
import random
import time
import matplotlib.pyplot as plt
import os

random.seed(123)
np.random.seed(123)

# PARAMETER TEKNIS & EKONOMI
C_WT = 560_000_000      
C_BATT = 161_000_000    
CAP_BATT_KWH = 42.62    
SOC_MIN, SOC_MAX = 0.10, 1.0           
EFF_BATT = 0.96         
SIGMA = 0.0002          
N_PROYEK = 20           
N_BATT_LIFE = 15        
BUNGA = 0.08            
O_M_RATE = 0.015        

JUMLAH_RUMAH = 100
BEBAN_PER_HARI = 1.6 * JUMLAH_RUMAH 

# Parameter MOGA
POP_SIZE = 40        
GENERATIONS = 30     
MUTATION_RATE = 0.15 
WT_BOUNDS = (10, 30) 
BATT_BOUNDS = (10, 50) 

# SIMULASI
def generate_load_profile():
    hourly_weight = [
        0.02, 0.02, 0.02, 0.02, 0.02, 0.03, 
        0.04, 0.04, 0.04,                   
        0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.04, 
        0.06, 0.08, 0.10, 0.09, 0.08,       
        0.05, 0.04                          
    ]
    return np.tile(hourly_weight, 365) * BEBAN_PER_HARI

def simulasi_sistem(N_wt, N_batt, df_angin):
    load_profile = generate_load_profile()
    E_batt_max = N_batt * CAP_BATT_KWH
    E_batt_min = E_batt_max * SOC_MIN
    E_batt_current = E_batt_max 
    
    total_lps = 0
    total_load = np.sum(load_profile)
    P_wt_array = df_angin['P_Aeolos_kW'].values * N_wt
    
    for t in range(8760):
        P_load = load_profile[t]
        P_wt = P_wt_array[t]
        E_net = P_wt - P_load
        
        if E_net > 0:
            E_batt_next = E_batt_current * (1 - SIGMA) + (E_net * EFF_BATT)
            E_batt_current = min(E_batt_next, E_batt_max) 
        else:
            E_batt_next = E_batt_current * (1 - SIGMA) - (abs(E_net) / EFF_BATT)
            if E_batt_next >= E_batt_min:
                E_batt_current = E_batt_next
            else:
                P_batt_avail = (E_batt_current - E_batt_min) * EFF_BATT
                total_lps += P_load - (P_wt + P_batt_avail)
                E_batt_current = E_batt_min
                
    LPSP = total_lps / total_load
    
    C_capital = (N_wt * C_WT) + (N_batt * C_BATT) + (0.20 * ((N_wt * C_WT) + (N_batt * C_BATT)))
    PVAF = ((1 + BUNGA)**N_PROYEK - 1) / (BUNGA * (1 + BUNGA)**N_PROYEK)
    NPC = C_capital + (O_M_RATE * C_capital * PVAF) + ((N_batt * C_BATT) / ((1 + BUNGA)**N_BATT_LIFE)) - (((N_batt * C_BATT) * (10 / 15)) / ((1 + BUNGA)**N_PROYEK))
    
    return LPSP, NPC

def hitung_daya_aeolos(v):
    if v < 2.5:
        return 0.0
    elif 2.5 <= v < 10.0:
        return 10.0 * ((v**3 - 2.5**3) / (10.0**3 - 2.5**3))
    elif 10.0 <= v <= 25.0:
        return 10.0
    else:
        return 0.0

# MOGA CORE (PENCARIAN PARETO FRONT)
def init_population(pop_size):
    return [{'wt': random.randint(*WT_BOUNDS), 'batt': random.randint(*BATT_BOUNDS)} for _ in range(pop_size)]

def get_non_dominated(pop_evaluated):
    non_dominated = []
    for i, (lpsp1, npc1, ind1) in enumerate(pop_evaluated):
        is_dominated = False
        for j, (lpsp2, npc2, ind2) in enumerate(pop_evaluated):
            if i != j:
                if (npc2 <= npc1 and lpsp2 <= lpsp1) and (npc2 < npc1 or lpsp2 < lpsp1):
                    is_dominated = True
                    break
        if not is_dominated:
            non_dominated.append((lpsp1, npc1, ind1))
    return non_dominated

def crossover_mutate(p1, p2):
    child = {'wt': random.choice([p1['wt'], p2['wt']]), 'batt': random.choice([p1['batt'], p2['batt']])}
    if random.random() < MUTATION_RATE:
        child['wt'] += random.choice([-2, -1, 1, 2])
        child['wt'] = max(WT_BOUNDS[0], min(WT_BOUNDS[1], child['wt']))
    if random.random() < MUTATION_RATE:
        child['batt'] += random.choice([-3, -2, 1, 2, 3])
        child['batt'] = max(BATT_BOUNDS[0], min(BATT_BOUNDS[1], child['batt']))
    return child

def run_moga(df_angin, nama_lokasi):
    start_time = time.time()
    population = init_population(POP_SIZE)
    
    for gen in range(GENERATIONS):
        pop_evaluated = []
        for ind in population:
            lpsp, npc = simulasi_sistem(ind['wt'], ind['batt'], df_angin)
            pop_evaluated.append((lpsp, npc, ind.copy()))
            
        pareto_front = get_non_dominated(pop_evaluated)
        
        if (gen+1) % 10 == 0 or gen == 0:
            print(f"Gen {gen+1:02d} | Menemukan {len(pareto_front)} Solusi Pareto")
        
        next_gen = [item[2] for item in pareto_front]
        while len(next_gen) < POP_SIZE:
            p1, p2 = random.sample(pareto_front, 2) if len(pareto_front) >= 2 else (pareto_front[0], pareto_front[0])
            next_gen.append(crossover_mutate(p1[2], p2[2]))
            
        population = next_gen[:POP_SIZE]

    end_time = time.time()
    
    # Evaluasi Final
    final_eval = [(simulasi_sistem(ind['wt'], ind['batt'], df_angin)) for ind in population]
    final_pop = [(eval[0], eval[1], ind) for eval, ind in zip(final_eval, population)]
    final_pareto = get_non_dominated(final_pop)
    
    unik_pareto = []
    seen = set()
    for lpsp, npc, ind in final_pareto:
        state = (ind['wt'], ind['batt'])
        if state not in seen:
            unik_pareto.append((lpsp, npc, ind))
            seen.add(state)
            
    unik_pareto.sort(key=lambda x: x[0]) 
    
    # PENCARIAN TITIK SIKU (SMART TRADE-OFF / KNEE POINT)
    opsi_aman = [item for item in unik_pareto if item[0] <= 0.01]
    
    if opsi_aman:
        # Jika cuma 1 opsi aman, langsung pilih itu
        if len(opsi_aman) == 1:
            solusi_terpilih = opsi_aman[0]
        else:
            lpsp_min = min(opsi_aman, key=lambda x: x[0])[0]
            lpsp_max = max(opsi_aman, key=lambda x: x[0])[0]
            npc_min = min(opsi_aman, key=lambda x: x[1])[1]
            npc_max = max(opsi_aman, key=lambda x: x[1])[1]
            
            best_score = float('inf')
            solusi_terpilih = None
            
            for item in opsi_aman:
                lpsp_norm = (item[0] - lpsp_min) / (lpsp_max - lpsp_min) if lpsp_max != lpsp_min else 0
                npc_norm = (item[1] - npc_min) / (npc_max - npc_min) if npc_max != npc_min else 0
                score = (lpsp_norm**2 + npc_norm**2)**0.5
                
                if score < best_score:
                    best_score = score
                    solusi_terpilih = item
    else:
        solusi_terpilih = None
        
    for i, (lpsp, npc, ind) in enumerate(unik_pareto):
        status = ""
        if solusi_terpilih and lpsp == solusi_terpilih[0] and npc == solusi_terpilih[1]:
            status = " <--- REKOMENDASI TERBAIK"
        print(f"Opsi {i+1:02d} | WT: {ind['wt']}, Batt: {ind['batt']} | LPSP: {lpsp*100:.2f}% | NPC: Rp {npc:,.0f} {status}")
        
    # PLOT
    npc_vals = [p[1] / 1e9 for p in unik_pareto] 
    
    # Siapkan data tabel
    table_data = []
    for i, (lpsp, npc, ind) in enumerate(unik_pareto):
        N_wt = ind['wt']
        N_batt = ind['batt']
        C_initial = (N_wt * C_WT) + (N_batt * C_BATT)
        C_capital = C_initial * 1.20 
        C_O_M_annual = O_M_RATE * C_capital 
        C_replace_pv = (N_batt * C_BATT) / ((1 + BUNGA)**N_BATT_LIFE)
        table_data.append({
            'Opsi': f"Opsi {i+1:02d}",
            'Turbin\n(Unit)': N_wt,
            'Baterai\n(Rak)': N_batt,
            'LPSP\n(%)': f"{lpsp*100:.2f}",
            'Biaya Modal\n(Juta Rp)': f"{C_capital/1e6:,.0f}",
            'O&M / Tahun\n(Juta Rp)': f"{C_O_M_annual/1e6:,.0f}",
            'Total NPC\n(Juta Rp)': f"{npc/1e6:,.0f}"
        })
    df_table = pd.DataFrame(table_data)

    table_height = len(df_table) * 0.4 + 1
    fig, (ax_graph, ax_table) = plt.subplots(2, 1, figsize=(10, 6 + table_height), gridspec_kw={'height_ratios': [6, table_height]})
    
    # PLOT PARETO
    ax_graph.plot(lpsp_vals, npc_vals, marker='o', linestyle='-', color='b', label='Pareto Front')
    if solusi_terpilih:
        ax_graph.scatter(solusi_terpilih[0]*100, solusi_terpilih[1]/1e9, color='red', s=150, zorder=5, label='Solusi Optimal (Sweet Spot)')
    ax_graph.axvline(x=1.0, color='r', linestyle='--', alpha=0.5, label='Batas LPSP 1%')
    ax_graph.set_title(f'Grafik Hasil Optimasi - {nama_lokasi}', fontsize=14, pad=10)
    ax_graph.set_xlabel('LPSP (%)', fontsize=12)
    ax_graph.set_ylabel('NPC (Miliar Rupiah)', fontsize=12)
    ax_graph.grid(True, alpha=0.3)
    ax_graph.legend()

    # TABEL
    ax_table.axis('off')
    tabel_moga = ax_table.table(cellText=df_table.values, colLabels=df_table.columns, cellLoc='center', loc='center', bbox=[0, 0, 1, 1])
    tabel_moga.auto_set_font_size(False)
    tabel_moga.set_fontsize(10)
    
    for (row, col), cell in tabel_moga.get_celld().items():
        cell.set_linewidth(0) 
        if row == 0 or row == len(df_table):
            cell.visible_edges = 'B'
            cell.set_linewidth(1.5)
            if row == 0: cell.set_text_props(weight='bold')
        
        if solusi_terpilih and row > 0:
            if df_table.iloc[row-1]['LPSP\n(%)'] == f"{solusi_terpilih[0]*100:.2f}" and df_table.iloc[row-1]['Total NPC\n(Juta Rp)'] == f"{solusi_terpilih[1]/1e6:,.0f}":
                cell.set_text_props(weight='bold', color='darkred')

    ax_table.set_title(f'Rincian Teknis dan Ekonomi Hasil Optimasi', loc='center', fontsize=12, pad=5, fontweight='bold')
    
    # Save & Show 
    plt.tight_layout()
    nama_file_gabungan = f'Hasil_Optimasi_MOGA_{nama_lokasi.replace(" ", "_")}.png'
    plt.savefig(nama_file_gabungan, bbox_inches='tight', dpi=300)
    plt.show() 
    plt.close()
    
    return solusi_terpilih

#   LOOPING
if __name__ == "__main__":
    
    # --- GANTI PATH INI SESUAI FOLDER LAPTOP KAMU ---
    base_path = r'C:\Users\sarah\OneDrive\Documents\TA\Timor'
    
    daftar_lokasi = {
        'Rote 1': 'Input_GA_Rote_3.csv',
        'Rote 2': 'Input_GA_Rote_4.csv',
        'Sabu 1': 'Input_GA_Sabu_1.csv',
        'Sabu 2': 'Input_GA_Sabu_2.csv'
    }

    for nama_lokasi, nama_file in daftar_lokasi.items():
        path_csv = os.path.join(base_path, nama_file)

        if not os.path.exists(path_csv):
            print(f"File {nama_file} tidak ditemukan di folder! Skip...\n")
            continue

        # MOGA ANGIN NORMAL
        print(f"PENCARIAN OPTIMAL MOGA ({nama_lokasi})")
        df_normal = pd.read_csv(path_csv)
        solusi_terpilih = run_moga(df_normal, nama_lokasi)
        
        #VALIDASI SENSITIVITAS (-5% ANGIN)
        if solusi_terpilih:
            print(f"\nVALIDASI SENSITIVITAS (-5% ANGIN) ({nama_lokasi})")
            
            wt_terpilih = solusi_terpilih[2]['wt']
            batt_terpilih = solusi_terpilih[2]['batt']
            lpsp_lama = solusi_terpilih[0]
            
            # Skenario angin turun 5%
            df_low_wind = df_normal.copy()
            ws_low = df_low_wind['WS_24m_ms'] * 0.95 
            df_low_wind['P_Aeolos_kW'] = [hitung_daya_aeolos(v) for v in ws_low]
            
            lpsp_baru, npc_baru = simulasi_sistem(wt_terpilih, batt_terpilih, df_low_wind)
            
            print(f"Menguji Konfigurasi Terkunci: {wt_terpilih} Turbin & {batt_terpilih} Baterai")
            print(f"LPSP Normal : {lpsp_lama*100:.2f}%")
            print(f"LPSP (-5%)  : {lpsp_baru*100:.2f}%")
            
            if lpsp_baru <= 0.01:
                print("KESIMPULAN: AMAN")
            else:
                print("KESIMPULAN: TIDAK AMAN")
        else:
            print("Tidak ada solusi yang memenuhi batas LPSP <= 1% pada kondisi normal.")