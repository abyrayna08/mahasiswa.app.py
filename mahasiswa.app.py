import json
import os
import re
import hashlib
import time

# =====================================================================
# 0. AUTENTIKASI (LOGIN)
# =====================================================================
class AutentikasiGagalError(Exception):
    """Dilempar jika username/password tidak cocok."""
    pass


class AkunTerkunciError(Exception):
    """Dilempar jika batas maksimal percobaan login terlampaui."""
    pass


class AutentikasiManager:

    # Kredensial "tersimpan" -> dalam aplikasi nyata sebaiknya disimpan
    # di database/file terenkripsi, bukan hardcode di source code.
    USERNAME_TERDAFTAR = "abyrayna"
    PASSWORD_HASH_TERDAFTAR = hashlib.sha256("abi1234567".encode("utf-8")).hexdigest()

    def __init__(self, batas_percobaan: int = 3):
        self.batas_percobaan = batas_percobaan

    @staticmethod
    def _hash_password(password: str) -> str:
        """Mengubah password menjadi hash SHA-256 (one-way, tidak bisa dibalik)."""
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def _ambil_password(self, prompt: str) -> str:
        """
        Mengambil input password tanpa menampilkannya di layar.
        Time Complexity: O(1).
        """
        try:
            return getpass.getpass(prompt)
        except Exception:
            # Fallback jika lingkungan tidak mendukung getpass (mis. beberapa IDE)
            print("[INFO] Mode input tersembunyi tidak didukung di lingkungan ini, "
                  "password akan terlihat saat diketik.")
            return input(prompt)

    def login(self) -> bool:
        """
        Menjalankan proses login interaktif.
        Mengembalikan True jika berhasil, False jika gagal/dikunci.
        Time Complexity: O(1) per percobaan (hanya perbandingan hash).
        """
        print("\n" + "=" * 60)
        print(" LOGIN APLIKASI MANAJEMEN DATA MAHASISWA ".center(60, "="))
        print("=" * 60)

        for percobaan in range(1, self.batas_percobaan + 1):
            try:
                username = input("Username : ").strip()
                password = self._ambil_password("Password : ")

                if not username or not password:
                    raise AutentikasiGagalError("Username/password tidak boleh kosong.")

                if (username == self.USERNAME_TERDAFTAR and
                        self._hash_password(password) == self.PASSWORD_HASH_TERDAFTAR):
                    print(f"\n[SUKSES] Login berhasil. Selamat datang, {username}!")
                    return True
                else:
                    raise AutentikasiGagalError("Username atau password salah.")

            except AutentikasiGagalError as e:
                sisa = self.batas_percobaan - percobaan
                if sisa > 0:
                    print(f"[ERROR] {e} Sisa percobaan: {sisa}.\n")
                else:
                    print(f"[ERROR] {e}")

        print("\n[GAGAL] Batas percobaan login terlampaui. Aplikasi akan ditutup.")
        return False

# =====================================================================
# 1. CUSTOM EXCEPTION
# =====================================================================
class ValidasiError(Exception):
    """Exception dasar untuk semua error validasi input."""
    pass


class NIMTidakValidError(ValidasiError):
    """Dilempar jika format NIM tidak sesuai pola regex yang ditentukan."""
    pass


class EmailTidakValidError(ValidasiError):
    """Dilempar jika format email bukan email Gmail yang valid."""
    pass


class NoHPTidakValidError(ValidasiError):
    """Dilempar jika format nomor HP tidak valid."""
    pass


class IPKTidakValidError(ValidasiError):
    """Dilempar jika nilai IPK di luar rentang 0.0 - 4.0."""
    pass


class DataTidakDitemukanError(Exception):
    """Dilempar jika data mahasiswa dengan NIM tertentu tidak ditemukan."""
    pass


class NIMDuplikatError(Exception):
    """Dilempar jika NIM yang akan ditambahkan sudah terdaftar sebelumnya."""
    pass


# =====================================================================
# 2. VALIDATOR (Regular Expression)
# =====================================================================
class Validator:

    # NIM: 8-12 digit angka, contoh: 220103001
    POLA_NIM = r'^\d{8,12}$'

    # Email khusus Gmail, contoh: budi.santoso01@gmail.com
    POLA_EMAIL_GMAIL = r'^[a-zA-Z0-9](?:[a-zA-Z0-9._]*[a-zA-Z0-9])?@gmail\.com$'

    # No HP Indonesia, contoh: 081234567890
    POLA_NO_HP = r'^08[0-9]{8,11}$'

    # Nama: hanya huruf, spasi, dan titik (untuk gelar)
    POLA_NAMA = r"^[A-Za-z\s.'-]{3,50}$"

    @staticmethod
    def validasi_nim(nim: str) -> bool:
        if not re.match(Validator.POLA_NIM, nim):
            raise NIMTidakValidError(
                f"NIM '{nim}' tidak valid. NIM harus berupa 8-12 digit angka."
            )
        return True

    @staticmethod
    def validasi_email_gmail(email: str) -> bool:
        if not re.match(Validator.POLA_EMAIL_GMAIL, email):
            raise EmailTidakValidError(
                f"Email '{email}' tidak valid. Gunakan format gmail yang benar, "
                f"contoh: nama.anda@gmail.com"
            )
        return True

    @staticmethod
    def validasi_no_hp(no_hp: str) -> bool:
        if not re.match(Validator.POLA_NO_HP, no_hp):
            raise NoHPTidakValidError(
                f"Nomor HP '{no_hp}' tidak valid. Format: diawali 08, total 10-13 digit."
            )
        return True

    @staticmethod
    def validasi_nama(nama: str) -> bool:
        if not re.match(Validator.POLA_NAMA, nama):
            raise ValidasiError(
                f"Nama '{nama}' tidak valid. Hanya boleh huruf, spasi, titik, "
                f"panjang 3-50 karakter."
            )
        return True

    @staticmethod
    def validasi_ipk(ipk: float) -> bool:
        if not (0.0 <= ipk <= 4.0):
            raise IPKTidakValidError(
                f"IPK '{ipk}' tidak valid. IPK harus berada di rentang 0.0 - 4.0."
            )
        return True


# =====================================================================
# 3. OOP: BASE CLASS (Person) -> Pewarisan & Enkapsulasi
# =====================================================================
class Person:

    def __init__(self, nama: str, email: str):
        self.nama = nama      # akan otomatis tervalidasi lewat setter di bawah
        self.email = email    # akan otomatis tervalidasi lewat setter di bawah

    # ---------- Property "nama" (encapsulation) ----------
    @property
    def nama(self) -> str:
        return self.__nama

    @nama.setter
    def nama(self, value: str):
        Validator.validasi_nama(value)
        self.__nama = value.strip()

    # ---------- Property "email" (encapsulation) ----------
    @property
    def email(self) -> str:
        return self.__email

    @email.setter
    def email(self, value: str):
        Validator.validasi_email_gmail(value)
        self.__email = value.strip().lower()

    def tampilkan_info(self) -> str:
        """Method ini akan di-override oleh subclass (POLIMORFISME)."""
        return f"Nama: {self.nama} | Email: {self.email}"


# =====================================================================
# 4. CLASS MAHASISWA (Pewarisan dari Person)
# =====================================================================
class Mahasiswa(Person):

    def __init__(self, nim: str, nama: str, email: str, jurusan: str,
                 ipk: float, no_hp: str, status: str = "Aktif"):
        super().__init__(nama, email)   # memanggil constructor parent class
        self.nim = nim
        self.jurusan = jurusan
        self.ipk = ipk
        self.no_hp = no_hp
        self.status = status

    # ---------- Property "nim" ----------
    @property
    def nim(self) -> str:
        return self.__nim

    @nim.setter
    def nim(self, value: str):
        Validator.validasi_nim(value)
        self.__nim = value

    # ---------- Property "ipk" ----------
    @property
    def ipk(self) -> float:
        return self.__ipk

    @ipk.setter
    def ipk(self, value):
        value = float(value)
        Validator.validasi_ipk(value)
        self.__ipk = value

    # ---------- Property "no_hp" ----------
    @property
    def no_hp(self) -> str:
        return self.__no_hp

    @no_hp.setter
    def no_hp(self, value: str):
        Validator.validasi_no_hp(value)
        self.__no_hp = value

    def tampilkan_info(self) -> str:
        return (f"NIM: {self.nim} | Nama: {self.nama} | Jurusan: {self.jurusan} | "
                f"IPK: {self.ipk:.2f} | Email: {self.email} | HP: {self.no_hp} | "
                f"Status: {self.status}")

    def to_dict(self) -> dict:
        return {
            "tipe": self.__class__.__name__,
            "nim": self.nim,
            "nama": self.nama,
            "email": self.email,
            "jurusan": self.jurusan,
            "ipk": self.ipk,
            "no_hp": self.no_hp,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict):
        tipe = data.get("tipe", "Mahasiswa")
        mapping = {
            "MahasiswaAktif": MahasiswaAktif,
            "MahasiswaCuti": MahasiswaCuti,
            "Mahasiswa": Mahasiswa,
        }
        target_class = mapping.get(tipe, Mahasiswa)
        return target_class(
            nim=data["nim"], nama=data["nama"], email=data["email"],
            jurusan=data["jurusan"], ipk=data["ipk"], no_hp=data["no_hp"],
            status=data.get("status", "Aktif"),
        )

    def __str__(self):
        return self.tampilkan_info()


# =====================================================================
# 5. SUBCLASS TAMBAHAN -> contoh POLIMORFISME lebih lanjut
# =====================================================================
class MahasiswaAktif(Mahasiswa):
    def __init__(self, nim, nama, email, jurusan, ipk, no_hp, status="Aktif"):
        super().__init__(nim, nama, email, jurusan, ipk, no_hp, status="Aktif")

    def tampilkan_info(self) -> str:
        return "[AKTIF] " + super().tampilkan_info()


class MahasiswaCuti(Mahasiswa):
    def __init__(self, nim, nama, email, jurusan, ipk, no_hp, status="Cuti"):
        super().__init__(nim, nama, email, jurusan, ipk, no_hp, status="Cuti")

    def tampilkan_info(self) -> str:
        return "[CUTI]  " + super().tampilkan_info()


# =====================================================================
# 6. DATA MANAGER -> CRUD, File I/O, Searching, Sorting, Ping
# =====================================================================
class DataManager:

    def __init__(self, filename: str = "data_mahasiswa.json"):
        self.data = []          # array/list objek Mahasiswa
        self.filename = filename

    # -----------------------------------------------------------------
    # CREATE
    # -----------------------------------------------------------------
    def tambah_mahasiswa(self, mhs: Mahasiswa):
        for m in self.data:
            if m.nim == mhs.nim:
                raise NIMDuplikatError(f"NIM {mhs.nim} sudah terdaftar!")
        self.data.append(mhs)

    # -----------------------------------------------------------------
    # READ
    # -----------------------------------------------------------------
    def tampilkan_semua(self):
        if not self.data:
            print("Belum ada data mahasiswa.")
            return
        print("-" * 100)
        for i, m in enumerate(self.data, start=1):
            print(f"{i}. {m.tampilkan_info()}")
        print("-" * 100)

    # -----------------------------------------------------------------
    # UPDATE
    # -----------------------------------------------------------------
    def edit_mahasiswa(self, nim: str, **field_baru):
        mhs = self._cari_objek_by_nim(nim)
        if mhs is None:
            raise DataTidakDitemukanError(f"Data dengan NIM {nim} tidak ditemukan.")

        for key, value in field_baru.items():
            if value in (None, ""):
                continue
            if key == "nama":
                mhs.nama = value
            elif key == "email":
                mhs.email = value
            elif key == "jurusan":
                mhs.jurusan = value
            elif key == "ipk":
                mhs.ipk = value
            elif key == "no_hp":
                mhs.no_hp = value
            elif key == "status":
                mhs.status = value
        return mhs

    # -----------------------------------------------------------------
    # DELETE
    # -----------------------------------------------------------------
    def hapus_mahasiswa(self, nim: str):
        mhs = self._cari_objek_by_nim(nim)
        if mhs is None:
            raise DataTidakDitemukanError(f"Data dengan NIM {nim} tidak ditemukan.")
        self.data.remove(mhs)
        return mhs

    def _cari_objek_by_nim(self, nim: str):
        """Helper internal: linear search sederhana untuk keperluan edit/hapus."""
        for m in self.data:
            if m.nim == nim:
                return m
        return None

    # -----------------------------------------------------------------
    # FILE I/O
    # -----------------------------------------------------------------
    def simpan_ke_file(self):
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump([m.to_dict() for m in self.data], f, indent=2, ensure_ascii=False)
            print(f"Data berhasil disimpan ke '{self.filename}'.")
        except (IOError, OSError) as e:
            print(f"[ERROR] Gagal menyimpan file: {e}")
        except TypeError as e:
            print(f"[ERROR] Gagal mengonversi data ke JSON: {e}")

    def muat_dari_file(self):
        if not os.path.exists(self.filename):
            print(f"[INFO] File '{self.filename}' belum ada. Mulai dengan data kosong.")
            return
        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                mentah = json.load(f)
            self.data = [Mahasiswa.from_dict(d) for d in mentah]
            print(f"Berhasil memuat {len(self.data)} data dari '{self.filename}'.")
        except json.JSONDecodeError as e:
            print(f"[ERROR] File JSON rusak/tidak valid: {e}")
        except (IOError, OSError) as e:
            print(f"[ERROR] Gagal membaca file: {e}")
        except (KeyError, ValidasiError) as e:
            print(f"[ERROR] Data pada file tidak valid: {e}")

    # -----------------------------------------------------------------
    # SEARCHING
    # -----------------------------------------------------------------
    def linear_search(self, nim: str):
        for m in self.data:
            if m.nim == nim:
                return m
        return None

    def sequential_search_nama(self, kata_kunci: str):
        kata_kunci = kata_kunci.lower()
        hasil = [m for m in self.data if kata_kunci in m.nama.lower()]
        return hasil

    def binary_search(self, nim: str):
        data_terurut = sorted(self.data, key=lambda m: m.nim)
        kiri, kanan = 0, len(data_terurut) - 1

        while kiri <= kanan:
            tengah = (kiri + kanan) // 2
            if data_terurut[tengah].nim == nim:
                return data_terurut[tengah]
            elif data_terurut[tengah].nim < nim:
                kiri = tengah + 1
            else:
                kanan = tengah - 1
        return None

    # -----------------------------------------------------------------
    # SORTING
    # -----------------------------------------------------------------
    def bubble_sort(self, key: str = "nim"):
        arr = self.data[:]   # salin agar data asli tidak berubah sebelum dikonfirmasi
        n = len(arr)
        for i in range(n - 1):
            swapped = False
            for j in range(n - 1 - i):
                if getattr(arr[j], key) > getattr(arr[j + 1], key):
                    arr[j], arr[j + 1] = arr[j + 1], arr[j]
                    swapped = True
            if not swapped:
                break
        return arr

    def selection_sort(self, key: str = "nim"):
        arr = self.data[:]
        n = len(arr)
        for i in range(n - 1):
            idx_min = i
            for j in range(i + 1, n):
                if getattr(arr[j], key) < getattr(arr[idx_min], key):
                    idx_min = j
            arr[i], arr[idx_min] = arr[idx_min], arr[i]
        return arr

    def insertion_sort(self, key: str = "ipk"):
        arr = self.data[:]
        for i in range(1, len(arr)):
            current = arr[i]
            j = i - 1
            while j >= 0 and getattr(arr[j], key) > getattr(current, key):
                arr[j + 1] = arr[j]
                j -= 1
            arr[j + 1] = current
        return arr

    def merge_sort(self, key: str = "ipk"):
        arr = self.data[:]
        return self._merge_sort_rekursif(arr, key)

    def _merge_sort_rekursif(self, arr, key):
        if len(arr) <= 1:
            return arr
        tengah = len(arr) // 2
        kiri = self._merge_sort_rekursif(arr[:tengah], key)
        kanan = self._merge_sort_rekursif(arr[tengah:], key)
        return self._merge(kiri, kanan, key)

    @staticmethod
    def _merge(kiri, kanan, key):
        hasil = []
        i = j = 0
        while i < len(kiri) and j < len(kanan):
            if getattr(kiri[i], key) <= getattr(kanan[j], key):
                hasil.append(kiri[i]); i += 1
            else:
                hasil.append(kanan[j]); j += 1
        hasil.extend(kiri[i:])
        hasil.extend(kanan[j:])
        return hasil

    def shell_sort(self, key: str = "nama"):
        arr = self.data[:]
        n = len(arr)
        gap = n // 2
        while gap > 0:
            for i in range(gap, n):
                temp = arr[i]
                j = i
                while j >= gap and getattr(arr[j - gap], key) > getattr(temp, key):
                    arr[j] = arr[j - gap]
                    j -= gap
                arr[j] = temp
            gap //= 2
        return arr

    # -----------------------------------------------------------------
    # FITUR PING EMAIL
    # -----------------------------------------------------------------
    def ping_email(self, mhs: Mahasiswa, timeout: float = 3.0):
        domain_smtp = "smtp.gmail.com"
        port = 587

        try:
            mulai = time.time()
            sock = socket.create_connection((domain_smtp, port), timeout=timeout)
            sock.close()
            durasi_ms = (time.time() - mulai) * 1000
            print(f"[PING OK] {mhs.email} -> server {domain_smtp} terjangkau "
                  f"dalam {durasi_ms:.2f} ms.")
            return True
        except socket.timeout:
            print(f"[PING GAGAL] {mhs.email} -> koneksi timeout setelah {timeout}s.")
        except socket.gaierror:
            print(f"[PING GAGAL] {mhs.email} -> domain '{domain_smtp}' tidak dapat "
                  f"di-resolve (periksa koneksi internet/DNS).")
        except OSError as e:
            print(f"[PING GAGAL] {mhs.email} -> {e}")
        return False


# =====================================================================
# 7. FUNGSI BANTUAN INPUT (dengan validasi & try-except)
# =====================================================================
def input_dengan_validasi(prompt: str, fungsi_validasi=None, tipe=str):
    while True:
        nilai_mentah = input(prompt).strip()
        try:
            nilai = tipe(nilai_mentah)
            if fungsi_validasi:
                fungsi_validasi(nilai)
            return nilai
        except ValueError:
            print("[ERROR] Format input salah, tipe data tidak sesuai. Coba lagi.")
        except ValidasiError as e:
            print(f"[ERROR] {e}")


# =====================================================================
# 8. MENU / TAMPILAN UTAMA (CLI)
# =====================================================================
def tampilkan_menu():
    print("\n" + "=" * 60)
    print(" APLIKASI MANAJEMEN DATA MAHASISWA ".center(60, "="))
    print("=" * 60)
    print("1. Tambah Data Mahasiswa")
    print("2. Edit Data Mahasiswa")
    print("3. Hapus Data Mahasiswa")
    print("4. Tampilkan Semua Data")
    print("5. Cari Data Mahasiswa")
    print("6. Urutkan Data Mahasiswa")
    print("7. Simpan Data ke File")
    print("8. Muat Data dari File")
    print("9. Ping Email Mahasiswa (cek konektivitas Gmail)")
    print("0. Keluar")
    print("=" * 60)


def menu_tambah(manager: DataManager):
    print("\n-- Tambah Data Mahasiswa --")
    try:
        nim = input_dengan_validasi("NIM (8-12 digit angka): ", Validator.validasi_nim)
        nama = input_dengan_validasi("Nama: ", Validator.validasi_nama)
        email = input_dengan_validasi("Email Gmail: ", Validator.validasi_email_gmail)
        jurusan = input("Jurusan: ").strip()
        ipk = input_dengan_validasi("IPK (0.0 - 4.0): ", Validator.validasi_ipk, tipe=float)
        no_hp = input_dengan_validasi("No HP (awali 08): ", Validator.validasi_no_hp)

        status = input("Status (Aktif/Cuti) [default Aktif]: ").strip().lower()
        if status == "cuti":
            mhs = MahasiswaCuti(nim, nama, email, jurusan, ipk, no_hp)
        else:
            mhs = MahasiswaAktif(nim, nama, email, jurusan, ipk, no_hp)

        manager.tambah_mahasiswa(mhs)
        print(f"[SUKSES] Data mahasiswa '{nama}' berhasil ditambahkan.")
    except NIMDuplikatError as e:
        print(f"[ERROR] {e}")
    except ValidasiError as e:
        print(f"[ERROR] {e}")
    except Exception as e:  # pengaman terakhir, sesuai prinsip robust error handling
        print(f"[ERROR TAK TERDUGA] {e}")


def menu_edit(manager: DataManager):
    print("\n-- Edit Data Mahasiswa --")
    try:
        nim = input("Masukkan NIM yang ingin diedit: ").strip()
        mhs_lama = manager._cari_objek_by_nim(nim)
        if mhs_lama is None:
            raise DataTidakDitemukanError(f"Data dengan NIM {nim} tidak ditemukan.")

        print(f"Data saat ini: {mhs_lama.tampilkan_info()}")
        print("(Kosongkan input jika tidak ingin mengubah field tsb)")

        nama_baru = input("Nama baru: ").strip()
        email_baru = input("Email baru: ").strip()
        jurusan_baru = input("Jurusan baru: ").strip()
        ipk_input = input("IPK baru: ").strip()
        no_hp_baru = input("No HP baru: ").strip()
        status_baru = input("Status baru (Aktif/Cuti): ").strip()

        ipk_baru = float(ipk_input) if ipk_input else None

        manager.edit_mahasiswa(
            nim,
            nama=nama_baru or None,
            email=email_baru or None,
            jurusan=jurusan_baru or None,
            ipk=ipk_baru,
            no_hp=no_hp_baru or None,
            status=status_baru or None,
        )
        print("[SUKSES] Data berhasil diperbarui.")
    except DataTidakDitemukanError as e:
        print(f"[ERROR] {e}")
    except ValidasiError as e:
        print(f"[ERROR] {e}")
    except ValueError:
        print("[ERROR] IPK harus berupa angka.")
    except Exception as e:
        print(f"[ERROR TAK TERDUGA] {e}")


def menu_hapus(manager: DataManager):
    print("\n-- Hapus Data Mahasiswa --")
    try:
        nim = input("Masukkan NIM yang ingin dihapus: ").strip()
        mhs = manager.hapus_mahasiswa(nim)
        print(f"[SUKSES] Data '{mhs.nama}' berhasil dihapus.")
    except DataTidakDitemukanError as e:
        print(f"[ERROR] {e}")


def menu_cari(manager: DataManager):
    print("\n-- Cari Data Mahasiswa --")
    print("1. Linear Search (berdasarkan NIM)")
    print("2. Binary Search (berdasarkan NIM, butuh data terurut)")
    print("3. Sequential Search (berdasarkan potongan Nama)")
    pilihan = input("Pilih metode pencarian: ").strip()

    try:
        if pilihan == "1":
            nim = input("Masukkan NIM: ").strip()
            hasil = manager.linear_search(nim)
            print(hasil.tampilkan_info() if hasil else "Data tidak ditemukan.")
        elif pilihan == "2":
            nim = input("Masukkan NIM: ").strip()
            hasil = manager.binary_search(nim)
            print(hasil.tampilkan_info() if hasil else "Data tidak ditemukan.")
        elif pilihan == "3":
            kata_kunci = input("Masukkan potongan nama: ").strip()
            hasil_list = manager.sequential_search_nama(kata_kunci)
            if hasil_list:
                for m in hasil_list:
                    print(m.tampilkan_info())
            else:
                print("Tidak ada data yang cocok.")
        else:
            print("Pilihan tidak valid.")
    except Exception as e:
        print(f"[ERROR] {e}")


def menu_urutkan(manager: DataManager):
    print("\n-- Urutkan Data Mahasiswa --")
    print("1. Bubble Sort   (key: nim)")
    print("2. Selection Sort (key: nim)")
    print("3. Insertion Sort (key: ipk)")
    print("4. Merge Sort     (key: ipk)")
    print("5. Shell Sort     (key: nama)")
    pilihan = input("Pilih metode pengurutan: ").strip()

    try:
        if pilihan == "1":
            hasil = manager.bubble_sort("nim")
        elif pilihan == "2":
            hasil = manager.selection_sort("nim")
        elif pilihan == "3":
            hasil = manager.insertion_sort("ipk")
        elif pilihan == "4":
            hasil = manager.merge_sort("ipk")
        elif pilihan == "5":
            hasil = manager.shell_sort("nama")
        else:
            print("Pilihan tidak valid.")
            return

        for i, m in enumerate(hasil, start=1):
            print(f"{i}. {m.tampilkan_info()}")
    except Exception as e:
        print(f"[ERROR] {e}")


def menu_ping(manager: DataManager):
    print("\n-- Ping Email Mahasiswa --")
    nim = input("Masukkan NIM mahasiswa: ").strip()
    mhs = manager.linear_search(nim)
    if mhs is None:
        print("[ERROR] Data tidak ditemukan.")
        return
    manager.ping_email(mhs)


def main():
    """Fungsi utama: menjalankan loop menu aplikasi."""
    manager = DataManager(filename="mahasiswa.app.json")
    manager.muat_dari_file()   # coba muat data lama saat aplikasi dijalankan

    while True:
        tampilkan_menu()
        try:
            pilihan = input("Pilih menu: ").strip()

            if pilihan == "1":
                menu_tambah(manager)
            elif pilihan == "2":
                menu_edit(manager)
            elif pilihan == "3":
                menu_hapus(manager)
            elif pilihan == "4":
                manager.tampilkan_semua()
            elif pilihan == "5":
                menu_cari(manager)
            elif pilihan == "6":
                menu_urutkan(manager)
            elif pilihan == "7":
                manager.simpan_ke_file()
            elif pilihan == "8":
                manager.muat_dari_file()
            elif pilihan == "9":
                menu_ping(manager)
            elif pilihan == "0":
                simpan = input("Simpan data sebelum keluar? (y/n): ").strip().lower()
                if simpan == "y":
                    manager.simpan_ke_file()
                print("Terima kasih telah menggunakan aplikasi ini. Sampai jumpa!")
                break
            else:
                print("[ERROR] Pilihan menu tidak valid, silakan coba lagi.")
        except KeyboardInterrupt:
            print("\n[INFO] Program dihentikan oleh pengguna.")
            break
        except Exception as e:
            # Pengaman terakhir agar aplikasi tidak crash karena error tak terduga
            print(f"[ERROR TAK TERDUGA] {e}")


if __name__ == "__main__":
    main()