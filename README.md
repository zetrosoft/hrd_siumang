# HRD Siumang Custom App

## Tentang Aplikasi

`hrd_siumang` adalah aplikasi kustom Frappe yang dirancang untuk memperluas fungsionalitas HR untuk Siumang. Aplikasi ini menyediakan fitur dan alur kerja khusus untuk menyederhanakan proses Departemen Sumber Daya Manusia.

Aplikasi ini dibangun di atas Frappe Framework dan terintegrasi secara mulus dengan ekosistem Frappe.

## Fitur Utama

*   **Manajemen Permintaan Pekerjaan (Job Requisition)**: Alur kerja khusus untuk mengelola permintaan pekerjaan, termasuk skrip sisi klien (client script) kustom untuk pengalaman pengguna yang lebih baik.
*   **Field Kustom**: Aplikasi ini menyertakan berbagai field kustom yang disesuaikan untuk kebutuhan spesifik proses HR Siumang.
*   **Alur Kerja Pengembangan Modern**: Memanfaatkan `pre-commit` hooks dengan alat seperti `ruff`, `eslint`, dan `prettier` untuk memastikan kualitas dan konsistensi kode.

## Instalasi

Anda dapat menginstal aplikasi ini menggunakan [bench](https://github.com/frappe/bench) CLI:

1.  Arahkan ke direktori bench Anda:
    ```bash
    cd $PATH_TO_YOUR_BENCH
    ```

2.  Dapatkan aplikasi dari repositori:
    ```bash
    bench get-app https://github.com/zetrosoft/hrd_siumang --branch develop
    ```

3.  Instal aplikasi di situs Anda:
    ```bash
    bench --site nama_situs_anda install-app hrd_siumang
    ```

## Kontribusi

Aplikasi ini menggunakan `pre-commit` untuk pemformatan dan linting kode. Silakan [instal pre-commit](https://pre-commit.com/#installation) dan aktifkan untuk repositori ini jika ingin berkontribusi:

1.  Arahkan ke direktori aplikasi:
    ```bash
    cd apps/hrd_siumang
    ```

2.  Instal git hooks:
    ```bash
    pre-commit install
    ```

Pre-commit dikonfigurasi untuk menggunakan alat-alat berikut untuk memeriksa dan memformat kode Anda:

*   `ruff` (untuk linting dan pemformatan Python)
*   `eslint` (untuk linting JavaScript)
*   `prettier` (untuk pemformatan kode)

## Lisensi

Proyek ini dilisensikan di bawah Lisensi MIT.
