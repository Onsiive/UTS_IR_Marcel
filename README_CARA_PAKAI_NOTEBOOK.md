# Program IR PN Tanjung Redeb 

Paket ini berisi notebook SUBCPMK 3 dan 4 (kode baru, bukan salinan program PN Bangil) dan satu salinan ZIP PDF yang kamu berikan.

## Cara membuka di Google Colab
1. Ekstrak paket ZIP ini di laptop.
2. Buka masing-masing notebook `.ipynb` dengan Colab.
3. Upload `INPUT_DATASET_50_PDF_UNTUK_COLAB.zip` ke panel **Files** Colab. Notebook mendeteksi nama tersebut otomatis; tidak perlu rename. Jika memakai nama/lokasi lain, isi `ZIP_MANUAL`.
4. Jalankan seluruh sel SUBCPMK 3 terlebih dahulu, kemudian SUBCPMK 4. Keduanya memakai folder kerja bersama `PN_Tanjung_Redeb`: SUBCPMK 3 menghasilkan PDF, TXT, CSV dan ZIP hasil; SUBCPMK 4 langsung membaca PDF/TXT tersebut dan menghasilkan inverted index, statistik, BM25, dan TF-IDF.
5. Pada Jupyter lokal, notebook otomatis menemukan root folder `UTS`, ZIP input di root/SUBCPMK 2, dan keluaran SUBCPMK 3. Notebook dapat dibuka dari folder mana pun selama kernel masih berada di dalam struktur folder UTS.
5. Untuk memperbarui sumber, ganti ZIP input dengan **PDF putusan resmi yang lengkap**, kemudian run ulang.

**Penting:** 50 berkas pada input saat ini adalah 50 PDF **ringkasan satu halaman** dari pengunggah. Keaslian sebagai putusan lengkap dan status bukan BHT belum dapat dibuktikan. Notebook tetap memproses teks yang tersedia, tetapi hasilnya bukan bukti bahwa SUBCPMK 2–4 memenuhi semua syarat dosen.

**Setting yang diperbarui:** ZIP dideteksi otomatis dan crawler utama memakai browser Playwright dari `https://putusan3.mahkamahagung.go.id/direktori.html`. Browser terlihat agar verifikasi situs dapat diselesaikan manual; program tidak melewati CAPTCHA. Crawler memfilter PN Tanjung Redeb serta narkotika/psikotropika, menyimpan unduhan di `pdf_crawler`, dan menulis `log_crawling.csv`. Set `JALANKAN_CRAWLER_PLAYWRIGHT=False` jika hanya ingin memproses ZIP lokal.

Untuk penggunaan pertama di Jupyter lokal, jalankan sel instalasi lalu restart kernel bila diminta. Chrome sistem akan dipakai jika tersedia. Jika tidak, instal browser Playwright dengan `python -m playwright install chromium` pada environment/kernel yang sama.
