# Paket UTS Information Retrieval — PN Tanjung Redeb

## Isi paket
1. `01_SUBCPMK1_State_of_the_Art/`: PDF tabel lima penelitian; isi nama dan NIM serta verifikasi sumber penelitian sebelum dikumpulkan.
2. `02_SUBCPMK2_Dataset_GitHub/`: rancangan repo GitHub, berisi ZIP 50 PDF **ringkasan satu halaman yang BELUM diverifikasi sebagai putusan lengkap non-BHT**, `Overview.xlsx`, dan audit. **Belum memenuhi syarat final SUBCPMK 2.**
3. `03_SUBCPMK3_Crawler_dan_Ekstraksi/`: notebook ekstraksi dan crawler browser Playwright dengan titik masuk Direktori Putusan MA, filter PN Tanjung Redeb serta narkotika/psikotropika, download PDF ke `pdf_crawler`, dan pencatatan URL/status ke `log_crawling.csv`. Verifikasi situs harus diselesaikan manual jika muncul.
4. `04_SUBCPMK4_Preprocessing_Indexing/`: notebook preprocessing dan indexing yang dapat bekerja dengan dataset ringkasan. Keberhasilan teknis tidak memvalidasi sumber dokumen.
5. `INPUT_DATASET_50_PDF_UNTUK_COLAB.zip`: salinan input untuk kedua notebook.

## Penting
- Dokumen awal mensyaratkan **50 file PDF putusan pengadilan lengkap** dengan kategori pidana khusus / narkotika dan psikotropika, dan tidak berstatus BHT.
- Berkas yang saat ini ada hanyalah 50 PDF *ringkasan* satu halaman; tidak terdapat bukti otoritatif status non-BHT.
- Perlu ganti PDF dengan putusan asli dan bandingkan nomor perkara: hanya 2 nomor dari dataset ringkasan ZIP terakhir cocok dengan tabel 50 perkara awal.
- Keluaran SUBCPMK 3 menurut soal: Colab runnable, CSV, serta folder PDF dan TXT; SUBCPMK 4: Colab preprocessing/indexing atas dokumen lengkap, bukan ringkasan.
- Penamaan repository perlu mengganti `XXX` dan `YYY` dengan 3 digit akhir NIM anggota.

## Cara penggunaan
1. Periksa `02_SUBCPMK2_Dataset_GitHub/.../Overview/Overview.xlsx` dan sheet audit.
2. Untuk menjalankan notebook, gunakan petunjuk `README_CARA_PAKAI_NOTEBOOK.md`.
3. Jalankan notebook SUBCPMK 3 terlebih dahulu lalu SUBCPMK 4. Keduanya otomatis memakai folder kerja bersama `03_SUBCPMK3_Crawler_dan_Ekstraksi/PN_Tanjung_Redeb` dan mendeteksi ZIP dari root UTS atau SUBCPMK 2.
4. Setelah memperoleh PDF asli non-BHT, ganti `Narkotika.zip` atau `INPUT_DATASET_50_PDF_UNTUK_COLAB.zip`, perbarui Overview dari PDF asli, lalu jalankan ulang kedua notebook.
5. **Jangan kumpulkan sebagai tugas final selama pemeriksaan nomor, status BHT, dan keaslian putusan belum tuntas.**
