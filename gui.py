"""Modern, sade bir YouTube indirici arayuzu (customtkinter)."""
import os
import threading
import queue
import itertools
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from tkinter import filedialog, messagebox

import customtkinter as ctk

import downloader
from surum import GITHUB_REPO, __version__

SURUMLER_URL = f"https://github.com/{GITHUB_REPO}/releases/latest"

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

QUALITY_MAP_VIDEO = {
    "En Yüksek Kalite": "best",
    "1080p": "1080",
    "720p": "720",
    "480p": "480",
    "360p": "360",
}
QUALITY_MAP_AUDIO = {
    "320 kbps (En İyi)": "320",
    "256 kbps": "256",
    "192 kbps": "192",
    "128 kbps": "128",
}

_uid_counter = itertools.count(1)


def format_duration(seconds):
    try:
        seconds = int(seconds)
    except (TypeError, ValueError):
        return ""
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


class VideoRow(ctk.CTkFrame):
    def __init__(self, master, item, on_remove):
        super().__init__(master, fg_color=("gray90", "gray17"), corner_radius=8)
        self.item = item
        self.uid = next(_uid_counter)
        self.cancel_event = threading.Event()
        self.state = "waiting"  # waiting -> downloading -> done / error / cancelled
        self.on_remove = on_remove
        self._dur_text = format_duration(item.get("duration"))

        self.grid_columnconfigure(1, weight=1)

        self.select_var = ctk.BooleanVar(value=True)
        self.checkbox = ctk.CTkCheckBox(self, text="", variable=self.select_var, width=20)
        self.checkbox.grid(row=0, column=0, rowspan=2, padx=(12, 8), pady=10)

        title = item["title"]
        if len(title) > 80:
            title = title[:77] + "..."
        self.title_label = ctk.CTkLabel(self, text=title, anchor="w",
                                         font=ctk.CTkFont(size=13, weight="bold"))
        self.title_label.grid(row=0, column=1, sticky="ew", padx=4, pady=(10, 0))

        duration = item.get("duration") or 0
        initial_status = "Bekliyor - uzun video, indirme biraz sürebilir" if duration > 1800 else "Bekliyor"
        self.status_label = ctk.CTkLabel(self, text=self._compose_status(initial_status), anchor="w",
                                          text_color=("gray35", "gray70"), font=ctk.CTkFont(size=11))
        self.status_label.grid(row=1, column=1, sticky="ew", padx=4, pady=(0, 10))

        self.progress = ctk.CTkProgressBar(self, width=150, height=10)
        self.progress.set(0)
        self.progress.grid(row=0, column=2, rowspan=2, padx=12, pady=10)

        self.remove_btn = ctk.CTkButton(self, text="✕", width=28, height=28, fg_color="transparent",
                                         hover_color=("gray80", "gray25"), text_color=("gray20", "gray80"),
                                         command=self._remove_clicked)
        self.remove_btn.grid(row=0, column=3, rowspan=2, padx=(0, 12), pady=10)

    def _compose_status(self, text):
        return f"{self._dur_text}  ·  {text}" if self._dur_text else text

    def _remove_clicked(self):
        self.cancel_event.set()
        self.on_remove(self)

    def set_status(self, text, fraction=None):
        self.status_label.configure(text=self._compose_status(text))
        if fraction is not None:
            self.progress.set(fraction)

    def set_selected(self, value: bool):
        self.select_var.set(value)


class App(ctk.CTk):
    def __init__(self, ytdlp_surum=None, python_yetersiz=False):
        super().__init__()
        self.title("YouTube İndirici")
        self.geometry("1000x700")
        self.minsize(860, 560)

        self.ytdlp_surum = ytdlp_surum
        self.rows_by_uid = {}
        self.update_queue = queue.Queue()
        self.executor = None
        self.active_futures = []
        self.total_count = 0
        self.done_count = 0
        self.default_output = os.path.join(os.path.expanduser("~"), "Downloads", "YouTube Indirilenler")

        self._build_ui()
        if python_yetersiz:
            self._banner_ac("YouTube'daki değişikliklere uymak için uygulamanın yeni sürümü gerekiyor.",
                            "İndir", lambda: webbrowser.open(SURUMLER_URL))
        self.after(100, self._drain_queue)

    # ---------------------------------------------------------- UI build --
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)

        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 0))
        top_bar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(top_bar, text="YouTube MP3 / MP4 İndirici",
                     font=ctk.CTkFont(size=22, weight="bold")).grid(row=0, column=0, sticky="w")

        self.theme_switch = ctk.CTkSegmentedButton(top_bar, values=["Sistem", "Açık", "Koyu"],
                                                    command=self._on_theme_change, width=180)
        self.theme_switch.set("Sistem")
        self.theme_switch.grid(row=0, column=1, sticky="e")

        # Gizli bilgi seridi: yeni surum / uygulama guncellemesi gerekiyor
        self.banner = ctk.CTkFrame(top_bar, fg_color=("#fff4ce", "#4a3f12"), corner_radius=8)
        self.banner.grid_columnconfigure(0, weight=1)
        self.banner_label = ctk.CTkLabel(self.banner, text="", anchor="w", justify="left")
        self.banner_label.grid(row=0, column=0, sticky="ew", padx=12, pady=8)
        self.banner_btn = ctk.CTkButton(self.banner, text="", width=90)
        self.banner_btn.grid(row=0, column=1, padx=(0, 12), pady=8)

        ctk.CTkLabel(self, text="Video veya oynatma listesi linkini yapıştırın; birden fazla linki alt alta ekleyebilirsiniz.",
                     text_color=("gray30", "gray70")).grid(row=1, column=0, sticky="w", padx=24, pady=(4, 12))

        # URL input row
        url_frame = ctk.CTkFrame(self, fg_color="transparent")
        url_frame.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 12))
        url_frame.grid_columnconfigure(0, weight=1)

        self.url_entry = ctk.CTkEntry(url_frame, placeholder_text="https://www.youtube.com/watch?v=... veya playlist linki",
                                       height=40)
        self.url_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.url_entry.bind("<Return>", lambda e: self.fetch_url())

        self.fetch_btn = ctk.CTkButton(url_frame, text="Ekle", width=110, height=40, command=self.fetch_url)
        self.fetch_btn.grid(row=0, column=1)

        # Options card
        options = ctk.CTkFrame(self, corner_radius=10)
        options.grid(row=3, column=0, sticky="ew", padx=24, pady=(0, 16))
        options.grid_columnconfigure((0, 1), weight=1)
        options.grid_columnconfigure(2, weight=2)

        fmt_col = ctk.CTkFrame(options, fg_color="transparent")
        fmt_col.grid(row=0, column=0, sticky="w", padx=16, pady=14)
        ctk.CTkLabel(fmt_col, text="Format", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
        self.format_btn = ctk.CTkSegmentedButton(fmt_col, values=["MP3 (Ses)", "MP4 (Video)"],
                                                  command=self.on_format_change)
        self.format_btn.set("MP3 (Ses)")
        self.format_btn.pack(anchor="w", pady=(6, 0))

        qual_col = ctk.CTkFrame(options, fg_color="transparent")
        qual_col.grid(row=0, column=1, sticky="w", padx=16, pady=14)
        ctk.CTkLabel(qual_col, text="Kalite", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
        self.quality_menu = ctk.CTkOptionMenu(qual_col, values=list(QUALITY_MAP_AUDIO.keys()), width=170)
        self.quality_menu.pack(anchor="w", pady=(6, 0))

        out_col = ctk.CTkFrame(options, fg_color="transparent")
        out_col.grid(row=0, column=2, sticky="ew", padx=16, pady=14)
        out_col.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(out_col, text="Kayıt Klasörü", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, columnspan=2, sticky="w")
        self.output_var = ctk.StringVar(value=self.default_output)
        self.output_entry = ctk.CTkEntry(out_col, textvariable=self.output_var)
        self.output_entry.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        ctk.CTkButton(out_col, text="Seç...", width=70, command=self.browse_output).grid(row=1, column=1, padx=(8, 0), pady=(6, 0))

        # List header
        list_header = ctk.CTkFrame(self, fg_color="transparent")
        list_header.grid(row=4, column=0, sticky="ew", padx=24, pady=(0, 6))
        list_header.grid_columnconfigure(1, weight=1)

        self.select_all_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(list_header, text="", variable=self.select_all_var, width=20,
                         command=self._select_all_toggle).grid(row=0, column=0, padx=(0, 8))
        self.list_title = ctk.CTkLabel(list_header, text="Video Listesi (0)", font=ctk.CTkFont(size=14, weight="bold"))
        self.list_title.grid(row=0, column=1, sticky="w")
        ctk.CTkButton(list_header, text="Listeyi Temizle", width=120, fg_color="transparent",
                      border_width=1, text_color=("gray20", "gray85"),
                      command=self.clear_list).grid(row=0, column=2)

        # Scrollable list
        self.list_container = ctk.CTkScrollableFrame(self, fg_color=("gray95", "gray14"), corner_radius=10)
        self.list_container.grid(row=5, column=0, sticky="nsew", padx=24, pady=(0, 12))

        self.empty_label = ctk.CTkLabel(self.list_container, text="Henüz video eklenmedi. Yukarıya bir link yapıştırıp \"Ekle\"ye basın.",
                                         text_color=("gray45", "gray55"))
        self.empty_label.pack(pady=30)

        # Bottom bar
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(row=6, column=0, sticky="ew", padx=24, pady=(0, 20))
        bottom.grid_columnconfigure(0, weight=1)

        self.overall_progress = ctk.CTkProgressBar(bottom)
        self.overall_progress.set(0)
        self.overall_progress.grid(row=0, column=0, sticky="ew", padx=(0, 16))

        self.overall_label = ctk.CTkLabel(bottom, text="0/0 tamamlandı", width=110)
        self.overall_label.grid(row=0, column=1, padx=(0, 16))

        self.cancel_btn = ctk.CTkButton(bottom, text="İptal Et", width=110, fg_color="#b3413e",
                                         hover_color="#8f312e", state="disabled", command=self.cancel_downloads)
        self.cancel_btn.grid(row=0, column=2, padx=(0, 10))

        self.download_btn = ctk.CTkButton(bottom, text="İndir", width=140, height=38,
                                           font=ctk.CTkFont(size=14, weight="bold"),
                                           state="disabled", command=self.start_download)
        self.download_btn.grid(row=0, column=3)

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=7, column=0, sticky="ew", padx=26, pady=(0, 10))
        footer.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(footer, text="Yalnızca indirme izniniz olan veya telif hakkı size ait içerikleri indirin.",
                     text_color=("gray45", "gray55"), font=ctk.CTkFont(size=10)).grid(row=0, column=0, sticky="w")
        self.surum_label = ctk.CTkLabel(footer, text=f"v{__version__} · yt-dlp {self.ytdlp_surum or '?'}",
                                         text_color=("gray45", "gray55"), font=ctk.CTkFont(size=10))
        self.surum_label.grid(row=0, column=1, sticky="e")

    # ----------------------------------------------------------- banner --
    def _banner_ac(self, metin, buton, komut):
        self.banner_label.configure(text=metin)
        self.banner_btn.configure(text=buton, command=komut)
        self.banner.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))

    def yeni_surum_goster(self, surum, url):
        self._banner_ac(f"Yeni sürüm var ({surum}). İndirip kurmanız yeterli.", "İndir",
                        lambda: webbrowser.open(url))

    # ------------------------------------------------------------ theme --
    def _on_theme_change(self, value):
        mapping = {"Sistem": "System", "Açık": "Light", "Koyu": "Dark"}
        ctk.set_appearance_mode(mapping.get(value, "System"))

    # ------------------------------------------------------------ fetch --
    def fetch_url(self):
        raw = self.url_entry.get().strip()
        if not raw:
            return
        urls = [u.strip() for u in raw.replace(",", "\n").split() if u.strip()]
        self.url_entry.delete(0, "end")
        self.fetch_btn.configure(state="disabled", text="Getiriliyor...")
        threading.Thread(target=self._fetch_worker, args=(urls,), daemon=True).start()

    def _fetch_worker(self, urls):
        results = []
        errors = []
        for u in urls:
            try:
                items, playlist_title = downloader.fetch_entries(u)
                results.append((items, playlist_title))
            except Exception as e:
                errors.append(f"{u}\n  -> {e}")
        self.after(0, lambda: self._fetch_done(results, errors))

    def _fetch_done(self, results, errors):
        for items, playlist_title in results:
            for item in items:
                item["_playlist_title"] = playlist_title
                self._add_row(item)
        self.fetch_btn.configure(state="normal", text="Ekle")
        self._update_counts()
        if errors:
            messagebox.showerror("Bazı linkler eklenemedi", "\n\n".join(errors))

    def _add_row(self, item):
        if not self.rows_by_uid:
            self.empty_label.pack_forget()
        row = VideoRow(self.list_container, item, on_remove=self._remove_row)
        row.pack(fill="x", padx=4, pady=4)
        self.rows_by_uid[row.uid] = row

    def _remove_row(self, row):
        row.destroy()
        self.rows_by_uid.pop(row.uid, None)
        if not self.rows_by_uid:
            self.empty_label.pack(pady=30)
        self._update_counts()

    def _select_all_toggle(self):
        value = bool(self.select_all_var.get())
        for row in self.rows_by_uid.values():
            row.set_selected(value)

    def clear_list(self):
        if self.executor is not None:
            messagebox.showwarning("Uyarı", "İndirme devam ederken liste temizlenemez.")
            return
        for row in list(self.rows_by_uid.values()):
            row.destroy()
        self.rows_by_uid.clear()
        self.empty_label.pack(pady=30)
        self._update_counts()

    def _update_counts(self):
        n = len(self.rows_by_uid)
        self.list_title.configure(text=f"Video Listesi ({n})")
        self.download_btn.configure(state="normal" if n else "disabled")

    # ---------------------------------------------------------- options --
    def on_format_change(self, value):
        is_audio = value.startswith("MP3")
        opts = QUALITY_MAP_AUDIO if is_audio else QUALITY_MAP_VIDEO
        self.quality_menu.configure(values=list(opts.keys()))
        self.quality_menu.set(list(opts.keys())[0])

    def browse_output(self):
        path = filedialog.askdirectory(initialdir=self.output_var.get() or os.path.expanduser("~"))
        if path:
            self.output_var.set(path)

    # -------------------------------------------------------- downloads --
    def start_download(self):
        selected_rows = [r for r in self.rows_by_uid.values() if r.select_var.get() and r.state == "waiting"]
        if not selected_rows:
            messagebox.showinfo("Bilgi", "İndirilecek seçili video yok.")
            return

        fmt = "mp3" if self.format_btn.get().startswith("MP3") else "mp4"
        quality_map = QUALITY_MAP_AUDIO if fmt == "mp3" else QUALITY_MAP_VIDEO
        quality = quality_map[self.quality_menu.get()]
        output_dir = self.output_var.get().strip() or self.default_output

        try:
            os.makedirs(output_dir, exist_ok=True)
        except OSError as e:
            messagebox.showerror("Hata", f"Kayıt klasörü oluşturulamadı:\n{e}")
            return

        self.download_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self.total_count = len(selected_rows)
        self.done_count = 0
        self.overall_progress.set(0)
        self.overall_label.configure(text=f"0/{self.total_count} tamamlandı")

        self.executor = ThreadPoolExecutor(max_workers=3)
        self.active_futures = []
        for row in selected_rows:
            row.state = "downloading"
            row.set_status("Sırada...", 0)
            subfolder = row.item.get("_playlist_title")
            future = self.executor.submit(self._download_worker, row, fmt, quality, output_dir, subfolder)
            self.active_futures.append(future)

        threading.Thread(target=self._watch_futures, daemon=True).start()

    def _download_worker(self, row, fmt, quality, output_dir, subfolder):
        uid = row.uid

        def hook(d):
            if row.cancel_event.is_set():
                raise Exception("İptal edildi")
            status = d.get("status")
            if status == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate")
                downloaded = d.get("downloaded_bytes", 0)
                frac = (downloaded / total) if total else 0
                speed = d.get("speed")
                speed_txt = f" · {speed / 1024 / 1024:.1f} MB/s" if speed else ""
                self.update_queue.put((uid, f"İndiriliyor %{int(frac * 100)}{speed_txt}", frac))
            elif status == "finished":
                self.update_queue.put((uid, "İşleniyor...", 1.0))

        try:
            downloader.download_item(row.item["url"], fmt, quality, output_dir, hook, subfolder)
            row.state = "done"
            self.update_queue.put((uid, "Tamamlandı", 1.0))
        except Exception as e:
            if row.cancel_event.is_set():
                row.state = "cancelled"
                self.update_queue.put((uid, "İptal edildi", None))
            else:
                row.state = "error"
                self.update_queue.put((uid, f"Hata: {e}", None))
        finally:
            self.update_queue.put(("__done__", uid, None))

    def _watch_futures(self):
        for f in self.active_futures:
            try:
                f.result()
            except Exception:
                pass
        self.after(0, self._all_downloads_finished)

    def _all_downloads_finished(self):
        self.executor = None
        self.download_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")

    def cancel_downloads(self):
        for row in self.rows_by_uid.values():
            if row.state == "downloading":
                row.cancel_event.set()
        if self.executor:
            self.executor.shutdown(wait=False, cancel_futures=True)
        self.cancel_btn.configure(state="disabled")

    def _drain_queue(self):
        try:
            while True:
                entry = self.update_queue.get_nowait()
                if entry[0] == "__done__":
                    _, _uid, _ = entry
                    self.done_count += 1
                    total = self.total_count or 1
                    self.overall_progress.set(min(self.done_count / total, 1.0))
                    self.overall_label.configure(text=f"{self.done_count}/{self.total_count} tamamlandı")
                    continue
                uid, text, frac = entry
                row = self.rows_by_uid.get(uid)
                if row:
                    row.set_status(text, frac)
        except queue.Empty:
            pass
        self.after(100, self._drain_queue)
