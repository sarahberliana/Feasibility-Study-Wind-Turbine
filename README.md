# Feasibility-Study-Wind-Turbine

Repositori ini berisi kode dan data pendukung Tugas Akhir (TA) dengan judul **"Optimasi Pembangkit Listrik Tenaga Bayu Stand-Alone terhadap Variabilitas Angin Menggunakan Multi-Objective Genetic Algorithm"**.

## This repository was created for academic purposes. Please contact the author if you wish to use the code or data for other purposes.

## Deskripsi

Penelitian ini membahas studi kelayakan (*feasibility study*) sistem Pembangkit Listrik Tenaga Bayu (PLTB) yang berdiri sendiri (*stand-alone*), dengan mempertimbangkan variabilitas kecepatan angin pada lokasi kajian. Optimasi konfigurasi sistem dilakukan menggunakan pendekatan **Multi-Objective Genetic Algorithm (MOGA)** untuk menghasilkan solusi terbaik (*trade-off*) antar beberapa tujuan optimasi, seperti keandalan sistem dan biaya pembangkitan energi.

## Tujuan Penelitian

- Menganalisis pengaruh variabilitas angin terhadap kinerja PLTB stand-alone.
- Melakukan optimasi multi-objektif terhadap konfigurasi sistem pembangkit menggunakan algoritma genetika.
- Mengevaluasi kelayakan teknis dan ekonomis dari hasil optimasi yang diperoleh.

## Struktur Repositori

```
Feasibility-Study-Wind-Turbine/
├── Data/       # Data masukan 
├── Script/     # Kode program untuk simulasi dan optimasi
└── README.md   
```
> Catatan: Sesuaikan deskripsi folder di atas apabila terdapat penambahan/perubahan struktur berkas.

## Metodologi Singkat

1. **Pengumpulan & pra-pemrosesan data angin** pada lokasi studi.
2. **Pemodelan sistem PLTB stand-alone** (turbin, baterai/penyimpanan, beban).
3. **Formulasi fungsi objektif** (minimasi biaya dan minimasi *loss of power supply*).
4. **Optimasi menggunakan Multi-Objective Genetic Algorithm (MOGA)** untuk memperoleh solusi optimal.
5. **Analisis kelayakan** teknis dan ekonomis dari hasil optimasi.
6. **Micro Sitting Wind Farm**

## Cara Menjalankan

1. Clone repositori ini:
   ```bash
   git clone https://github.com/sarahberliana/Feasibility-Study-Wind-Turbine.git
   cd Feasibility-Study-Wind-Turbine
   ```
2. Siapkan data pada folder `Data/` sesuai format yang digunakan pada script.
3. Jalankan script optimasi pada folder `Script/` sesuai instruksi di dalam masing-masing file.


## Informasi

Tugas Akhir ini disusun sebagai syarat kelulusan program studi. Untuk informasi lebih lanjut mengenai metodologi lengkap, silakan merujuk pada naskah TA terkait.

**Penulis:** Sarah Berliana Salsabila - Meteorologi Institut Teknologi Bandung - 2026
