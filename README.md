# Spotify Local Song

Small desktop app to manage **local MP3s** in a folder you use with **Spotify Local Files**: edit **title, artist, album**, and **cover art**, optionally match the filename to the title, and **download audio from a YouTube URL** with tags formatted for local playback.

Useful when you want your liked tracks as **normal local songs** instead of dealing with odd Spotify catalog behavior (e.g. episodes or bad matches for things you actually own as files).

---

## Requirements

- **Windows** (for the pre-built release).
- [**FFmpeg**](https://ffmpeg.org/download.html) installed and available on your system `PATH` (needed for YouTube download / re-encode).
- **Spotify** desktop or mobile, with **Local files** enabled (see below).

---

## Run from source

```bash
git clone https://github.com/llmandres/spotify-local-songs.git
cd spotify-local-songs
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Build a Windows executable (see `build.bat` and `SpotifyLocalSong.spec`):

```bash
build.bat
```

Release zip contains `dist\SpotifyLocalSong\` — run `SpotifyLocalSong.exe` and keep the `_internal` folder alongside it.

---

## How to use (desktop)

1. **Select folder** — Choose the directory where your MP3s live (this is the “library” Spotify will read from).
2. **Pick a track** in the sidebar to edit **Title / Artist / Album** and **cover**.
3. **Save** — Writes **ID3v2.3** tags (what Spotify expects for local files). If the title is valid as a filename, the file may be renamed to match.
4. **Add MP3s** — Use **Add Local MP3** or copy files into that folder yourself.
5. **YouTube URL** — Paste a link and **Download**. The app downloads, re-encodes for compatibility, and tags the file.

**Playlist warning:** If you paste a **playlist** URL, the downloader may fetch the **entire playlist**, not a single video. Prefer a single-video URL when you only want one track.

---

## Spotify: show local files (PC)

1. Open **Spotify** → **Settings**.
2. Turn on **Show Local Files** (wording may vary slightly by version).
3. Add your **music folder** as a source — use the **same folder** you select in this app.

After that, local tracks from that folder appear in **Your Library** under Local (as Spotify labels it).

---

## Phones & keeping the same music (OneDrive + sync)

Local files in Spotify are **only what’s on that device’s disk**. The PC and your phone do **not** share one magic cloud library; you need a way to get the **same files** onto the phone.

A practical setup:

1. Put your MP3 folder somewhere **OneDrive** syncs on the PC (e.g. a dedicated “Spotify music” folder inside OneDrive).
2. Use this app with that folder so every save lands in a cloud-synced directory.
3. On **Android**, use a sync app — for example **[OneSync: Autosync for OneDrive](https://play.google.com/store/apps/details?id=com.ttxapps.onesyncv2)** (MetaCtrl) — to sync that OneDrive folder into **Music** (or another folder Spotify is allowed to scan). Configure it to pull from your cloud folder into the phone’s **Music** directory and, if you want, run on a schedule.
4. In **Spotify on the phone**, turn on **Show local files** and point it at the folder where the synced MP3s end up (often under Music).

**`.nomedia` (Android):** Android’s media scanner may pick up **everything** under Music, including folders you don’t want (e.g. WhatsApp voice notes). Put an empty file named **`.nomedia`** in any directory you want the system (and often Spotify’s local scan) to **ignore**. That keeps junk out of your library.

Once OneDrive + phone sync + Spotify local sources are set, new tracks you add or fix on the PC can flow to the phone after sync — still as **local files**, not as Spotify streaming catalog entries. The tracks won’t appear in Spotify’s cloud catalog on other devices unless you set up this kind of sync or copy the files some other way.
