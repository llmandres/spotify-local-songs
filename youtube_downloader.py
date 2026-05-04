import yt_dlp
import os
import threading
import subprocess
import urllib.request
import time
import tempfile
import shutil
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, APIC, error
from PIL import Image
import io


def _get_thumbnail_data(info_dict):
    thumbnails = info_dict.get('thumbnails', [])
    thumbnails = sorted(thumbnails, key=lambda t: t.get('preference', 0), reverse=True)

    for thumb in thumbnails:
        url = thumb.get('url')
        if not url:
            continue
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                raw = resp.read()
            img = Image.open(io.BytesIO(raw))
            img = img.convert("RGB")
            img.thumbnail((500, 500), Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=85)
            return buf.getvalue()
        except Exception:
            continue
    return None


def _reencode_for_spotify(filepath):
    temp_path = None
    try:
        fd, temp_path = tempfile.mkstemp(suffix='.mp3')
        os.close(fd)

        result = subprocess.run(
            [
                'ffmpeg', '-y', '-i', filepath,
                '-vn',
                '-ar', '44100',
                '-ac', '2',
                '-b:a', '192k',
                '-map_metadata', '-1',
                '-id3v2_version', '0',
                temp_path
            ],
            capture_output=True,
            timeout=120
        )

        if result.returncode == 0 and os.path.isfile(temp_path):
            time.sleep(0.3)
            try:
                os.replace(temp_path, filepath)
            except PermissionError:
                time.sleep(0.5)
                os.remove(filepath)
                os.rename(temp_path, filepath)
            temp_path = None
    except Exception as e:
        print(f"Warning: could not re-encode for Spotify: {e}")
    finally:
        if temp_path and os.path.isfile(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


def _write_spotify_tags(filepath, title, artist, cover_jpeg_bytes=None):
    try:
        audio = MP3(filepath, ID3=ID3)

        try:
            audio.add_tags()
        except error:
            pass

        tags = audio.tags
        tags.clear()

        tags.add(TIT2(encoding=1, text=title))
        tags.add(TPE1(encoding=1, text=artist))
        tags.add(TALB(encoding=1, text=title))

        if cover_jpeg_bytes:
            tags.add(APIC(
                encoding=0,
                mime="image/jpeg",
                type=3,
                desc="Cover",
                data=cover_jpeg_bytes,
            ))

        audio.save(v2_version=3)
    except Exception as e:
        print(f"Warning: could not write Spotify tags: {e}")


def _cookie_options(cookiefile=None, cookies_browser=None):
    if cookiefile and os.path.isfile(cookiefile):
        return {"cookiefile": cookiefile}
    if cookies_browser:
        return {"cookiesfrombrowser": (cookies_browser,)}
    return {}


def download_audio(url, output_folder, on_success=None, on_error=None, cookiefile=None, cookies_browser=None):
    def run_download():
        temp_dir = None
        try:
            temp_dir = tempfile.mkdtemp(prefix='spotify_dl_')

            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'writethumbnail': False,
                'noplaylist': True,
            }
            ydl_opts.update(_cookie_options(cookiefile, cookies_browser))

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                title = info_dict.get('title', 'Unknown Title')
                artist = info_dict.get('uploader', info_dict.get('channel', ''))
                temp_mp3_path = os.path.splitext(ydl.prepare_filename(info_dict))[0] + '.mp3'

            if not os.path.isfile(temp_mp3_path):
                raise FileNotFoundError(f"Downloaded file not found: {temp_mp3_path}")

            _reencode_for_spotify(temp_mp3_path)

            cover_data = _get_thumbnail_data(info_dict)

            _write_spotify_tags(temp_mp3_path, title, artist, cover_data)

            safe_title = "".join(c for c in title if c.isalnum() or c in " .-_()")
            final_mp3_path = os.path.join(output_folder, f"{safe_title}.mp3")

            if os.path.exists(final_mp3_path):
                try:
                    os.remove(final_mp3_path)
                except Exception:
                    pass

            shutil.move(temp_mp3_path, final_mp3_path)

            if on_success:
                on_success(title)
        except Exception as e:
            if on_error:
                on_error(str(e))
        finally:
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass

    thread = threading.Thread(target=run_download, daemon=True)
    thread.start()
