import os
import io
import shutil
import customtkinter as ctk
from PIL import Image
from config_manager import load_config, save_config
from audio_manager import AudioMetadata, get_mp3_files
from youtube_downloader import download_audio
from tkinter import filedialog, messagebox

SPOTIFY_BG = "#121212"
SPOTIFY_PANEL = "#181818"
SPOTIFY_HOVER = "#282828"
SPOTIFY_GREEN = "#1DB954"
SPOTIFY_GREEN_HOVER = "#1ED760"
SPOTIFY_TEXT = "#FFFFFF"
SPOTIFY_SUBTEXT = "#B3B3B3"

class SpotifyLocalFileManager(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Spotify Local Song")
        self.geometry("1000x650")
        self.minsize(800, 500)
        self.configure(fg_color=SPOTIFY_BG)

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.config = load_config()
        self.current_folder = self.config.get("last_folder", "")
        self.mp3_files = []
        self.current_audio = None
        self.new_image_path = None
        self.song_buttons = []

        self._build_ui()

        if self.current_folder and os.path.isdir(self.current_folder):
            self._load_folder(self.current_folder)

    def _build_ui(self):
        self.top_bar = ctk.CTkFrame(self, fg_color=SPOTIFY_PANEL, corner_radius=0, height=100)
        self.top_bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.top_bar.grid_propagate(False)

        self.top_row_1 = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        self.top_row_1.pack(fill="x", padx=10, pady=(10, 5))

        self.btn_select_folder = ctk.CTkButton(
            self.top_row_1, text="Select Folder",
            fg_color=SPOTIFY_GREEN, hover_color=SPOTIFY_GREEN_HOVER,
            text_color=SPOTIFY_BG, font=("Helvetica", 14, "bold"),
            command=self._select_folder, width=120
        )
        self.btn_select_folder.pack(side="left", padx=10)

        self.btn_add_local = ctk.CTkButton(
            self.top_row_1, text="Add Local MP3",
            fg_color="transparent", border_width=1, border_color=SPOTIFY_SUBTEXT,
            text_color=SPOTIFY_TEXT, hover_color=SPOTIFY_HOVER,
            command=self._add_local_mp3, width=120, state="disabled"
        )
        self.btn_add_local.pack(side="left", padx=10)

        self.btn_refresh = ctk.CTkButton(
            self.top_row_1, text="Refresh",
            fg_color="transparent", border_width=1, border_color=SPOTIFY_SUBTEXT,
            text_color=SPOTIFY_TEXT, hover_color=SPOTIFY_HOVER,
            command=self._refresh_manual, width=80, state="disabled"
        )
        self.btn_refresh.pack(side="left", padx=10)

        self.lbl_folder_path = ctk.CTkLabel(
            self.top_row_1, text=self.current_folder or "No folder selected",
            text_color=SPOTIFY_SUBTEXT, font=("Helvetica", 12)
        )
        self.lbl_folder_path.pack(side="left", padx=10)

        self.top_row_2 = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        self.top_row_2.pack(fill="x", padx=10, pady=(5, 10))

        ctk.CTkLabel(self.top_row_2, text="YouTube URL:", text_color=SPOTIFY_TEXT, font=("Helvetica", 12)).pack(side="left", padx=10)

        self.entry_yt_url = ctk.CTkEntry(
            self.top_row_2, fg_color=SPOTIFY_BG, border_width=0, text_color=SPOTIFY_TEXT,
            width=300, placeholder_text="https://www.youtube.com/watch?v=..."
        )
        self.entry_yt_url.pack(side="left", padx=10)

        self.btn_download_yt = ctk.CTkButton(
            self.top_row_2, text="Download",
            fg_color=SPOTIFY_GREEN, hover_color=SPOTIFY_GREEN_HOVER,
            text_color=SPOTIFY_BG, font=("Helvetica", 12, "bold"),
            command=self._download_from_youtube, width=100, state="disabled"
        )
        self.btn_download_yt.pack(side="left", padx=10)

        self.lbl_status = ctk.CTkLabel(
            self.top_row_2, text="", text_color=SPOTIFY_SUBTEXT, font=("Helvetica", 12)
        )
        self.lbl_status.pack(side="left", padx=10)

        self.sidebar = ctk.CTkScrollableFrame(self, fg_color=SPOTIFY_BG, width=250, corner_radius=0)
        self.sidebar.grid(row=1, column=0, sticky="nsew")

        self.editor_panel = ctk.CTkFrame(self, fg_color=SPOTIFY_BG, corner_radius=0)
        self.editor_panel.grid(row=1, column=1, sticky="nsew")
        self.editor_panel.grid_rowconfigure(0, weight=1)
        self.editor_panel.grid_columnconfigure(0, weight=1)

        self.editor_content = ctk.CTkFrame(self.editor_panel, fg_color="transparent")
        self.editor_content.grid(row=0, column=0, padx=40, pady=40, sticky="nsew")

        self.cover_frame = ctk.CTkFrame(self.editor_content, fg_color="transparent")
        self.cover_frame.pack(side="left", fill="y", padx=(0, 40))

        self.lbl_cover = ctk.CTkLabel(self.cover_frame, text="", width=250, height=250, fg_color=SPOTIFY_HOVER, corner_radius=10)
        self.lbl_cover.pack(pady=(0, 20))

        self.btn_change_cover = ctk.CTkButton(
            self.cover_frame, text="Change Cover",
            fg_color="transparent", border_width=1, border_color=SPOTIFY_SUBTEXT,
            text_color=SPOTIFY_TEXT, hover_color=SPOTIFY_HOVER,
            command=self._change_cover, state="disabled"
        )
        self.btn_change_cover.pack()

        self.metadata_frame = ctk.CTkFrame(self.editor_content, fg_color="transparent")
        self.metadata_frame.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(self.metadata_frame, text="Title", text_color=SPOTIFY_SUBTEXT, font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(0, 5))
        self.entry_title = ctk.CTkEntry(self.metadata_frame, fg_color=SPOTIFY_HOVER, border_width=0, text_color=SPOTIFY_TEXT, font=("Helvetica", 24, "bold"), height=50)
        self.entry_title.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(self.metadata_frame, text="Artist", text_color=SPOTIFY_SUBTEXT, font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(0, 5))
        self.entry_artist = ctk.CTkEntry(self.metadata_frame, fg_color=SPOTIFY_HOVER, border_width=0, text_color=SPOTIFY_TEXT, font=("Helvetica", 16), height=40)
        self.entry_artist.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(self.metadata_frame, text="Album", text_color=SPOTIFY_SUBTEXT, font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(0, 5))
        self.entry_album = ctk.CTkEntry(self.metadata_frame, fg_color=SPOTIFY_HOVER, border_width=0, text_color=SPOTIFY_TEXT, font=("Helvetica", 16), height=40)
        self.entry_album.pack(fill="x", pady=(0, 40))

        self.btn_save = ctk.CTkButton(
            self.metadata_frame, text="Save Changes",
            fg_color=SPOTIFY_GREEN, hover_color=SPOTIFY_GREEN_HOVER,
            text_color=SPOTIFY_BG, font=("Helvetica", 16, "bold"), height=50,
            command=self._save_changes, state="disabled"
        )
        self.btn_save.pack(anchor="w")

        self._set_default_image()

    def _set_default_image(self):
        img = Image.new('RGB', (250, 250), color=SPOTIFY_HOVER)
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(250, 250))
        self.lbl_cover.configure(image=ctk_img, text="")

    def _select_folder(self):
        folder = filedialog.askdirectory(title="Select Music Folder")
        if folder:
            self._load_folder(folder)

    def _load_folder(self, folder):
        self.current_folder = folder
        self.lbl_folder_path.configure(text=folder)
        self.config["last_folder"] = folder
        save_config(self.config)

        self.btn_add_local.configure(state="normal")
        self.btn_refresh.configure(state="normal")
        self.btn_download_yt.configure(state="normal")

        self.mp3_files = get_mp3_files(folder)
        self._refresh_song_list()
        self._clear_editor()

    def _refresh_song_list(self):
        for btn in self.song_buttons:
            btn.destroy()
        self.song_buttons.clear()

        if not self.mp3_files:
            lbl = ctk.CTkLabel(self.sidebar, text="No MP3 files found.", text_color=SPOTIFY_SUBTEXT)
            lbl.pack(pady=20)
            self.song_buttons.append(lbl)
            return

        for filepath in self.mp3_files:
            filename = os.path.basename(filepath)
            frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
            frame.pack(fill="x", pady=2)

            btn = ctk.CTkButton(
                frame, text=filename, anchor="w",
                fg_color="transparent", hover_color=SPOTIFY_HOVER,
                text_color=SPOTIFY_TEXT, font=("Helvetica", 14), height=40,
                command=lambda p=filepath: self._load_song(p)
            )
            btn.pack(fill="x", padx=10)
            self.song_buttons.append(frame)

    def _load_song(self, filepath):
        self.current_audio = AudioMetadata(filepath)
        self.new_image_path = None

        self.btn_change_cover.configure(state="normal")
        self.btn_save.configure(state="normal")

        self.entry_title.delete(0, "end")
        self.entry_title.insert(0, self.current_audio.title)

        self.entry_artist.delete(0, "end")
        self.entry_artist.insert(0, self.current_audio.artist)

        self.entry_album.delete(0, "end")
        self.entry_album.insert(0, self.current_audio.album)

        if self.current_audio.image_data:
            try:
                img = Image.open(io.BytesIO(self.current_audio.image_data))
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(250, 250))
                self.lbl_cover.configure(image=ctk_img)
            except Exception:
                self._set_default_image()
        else:
            self._set_default_image()

    def _clear_editor(self):
        self.current_audio = None
        self.new_image_path = None
        self.entry_title.delete(0, "end")
        self.entry_artist.delete(0, "end")
        self.entry_album.delete(0, "end")
        self._set_default_image()
        self.btn_change_cover.configure(state="disabled")
        self.btn_save.configure(state="disabled")

    def _change_cover(self):
        if not self.current_audio:
            return

        filetypes = [("Images", "*.jpg *.jpeg *.png")]
        filepath = filedialog.askopenfilename(title="Select Cover Image", filetypes=filetypes)

        if filepath:
            self.new_image_path = filepath
            try:
                img = Image.open(filepath)
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(250, 250))
                self.lbl_cover.configure(image=ctk_img)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {e}")
                self.new_image_path = None

    def _refresh_manual(self):
        if self.current_folder and os.path.isdir(self.current_folder):
            self.mp3_files = get_mp3_files(self.current_folder)
            self._refresh_song_list()
            self._clear_editor()
            self.lbl_status.configure(text="List refreshed.", text_color=SPOTIFY_GREEN)

    def _save_changes(self):
        if not self.current_audio:
            return

        title = self.entry_title.get().strip()
        artist = self.entry_artist.get().strip()
        album = self.entry_album.get().strip()

        safe_title = "".join(c for c in title if c not in r'\/:*?"<>|')
        new_filepath = None
        if safe_title:
            new_filename = f"{safe_title}.mp3"
            new_filepath = os.path.join(self.current_folder, new_filename)

        success, err_msg = self.current_audio.save(title, artist, album, self.new_image_path, new_filepath)

        if success:
            self._load_song(self.current_audio.filepath)

            self.mp3_files = get_mp3_files(self.current_folder)
            self._refresh_song_list()

            messagebox.showinfo("Success", "Changes saved successfully.")
        else:
            messagebox.showerror("Error", f"Failed to save changes. Make sure the file is not open in another program.\nDetails: {err_msg}")

    def _add_local_mp3(self):
        if not self.current_folder:
            return

        filetypes = [("MP3 Files", "*.mp3")]
        filepaths = filedialog.askopenfilenames(title="Select MP3 Files", filetypes=filetypes)

        if filepaths:
            added_count = 0
            for path in filepaths:
                filename = os.path.basename(path)
                dest = os.path.join(self.current_folder, filename)
                if not os.path.exists(dest):
                    try:
                        shutil.copy2(path, dest)
                        added_count += 1
                    except Exception as e:
                        print(f"Error copying {filename}: {e}")

            if added_count > 0:
                self.mp3_files = get_mp3_files(self.current_folder)
                self._refresh_song_list()
                self.lbl_status.configure(text=f"Added {added_count} files.", text_color=SPOTIFY_GREEN)
            else:
                self.lbl_status.configure(text="No new files added.", text_color=SPOTIFY_SUBTEXT)

    def _download_from_youtube(self):
        if not self.current_folder:
            return

        url = self.entry_yt_url.get().strip()
        if not url:
            return

        self.btn_download_yt.configure(state="disabled")
        self.entry_yt_url.configure(state="disabled")
        self.lbl_status.configure(text="Downloading...", text_color=SPOTIFY_TEXT)

        def on_success(title):
            self.after(0, self._on_download_complete, title)

        def on_error(err_msg):
            self.after(0, self._on_download_error, err_msg)

        download_audio(url, self.current_folder, on_success, on_error)

    def _on_download_complete(self, title):
        self.entry_yt_url.configure(state="normal")
        self.entry_yt_url.delete(0, "end")
        self.btn_download_yt.configure(state="normal")
        self.lbl_status.configure(text=f"Downloaded: {title}", text_color=SPOTIFY_GREEN)

        self.mp3_files = get_mp3_files(self.current_folder)
        self._refresh_song_list()

    def _on_download_error(self, err_msg):
        self.entry_yt_url.configure(state="normal")
        self.btn_download_yt.configure(state="normal")
        self.lbl_status.configure(text="Error downloading video", text_color="red")
        messagebox.showerror("Download Error", f"Failed to download from YouTube:\n{err_msg}")
