import os
import tempfile
import shutil
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB, error

class AudioMetadata:
    def __init__(self, filepath):
        self.filepath = filepath
        self.title = os.path.splitext(os.path.basename(filepath))[0]
        self.artist = ""
        self.album = ""
        self.image_data = None
        self.load()

    def load(self):
        try:
            audio = MP3(self.filepath, ID3=ID3)
            tags = audio.tags
            if tags is None:
                return

            if 'TIT2' in tags:
                parts = []
                for fr in tags.getall('TIT2'):
                    if fr.text:
                        parts.extend([t for t in fr.text if t])
                combined = '/'.join(parts) if parts else ''
                if combined.strip():
                    self.title = combined

            if 'TPE1' in tags:
                parts = []
                for fr in tags.getall('TPE1'):
                    if fr.text:
                        parts.extend([t for t in fr.text if t])
                if parts:
                    self.artist = '/'.join(parts)

            if 'TALB' in tags:
                parts = []
                for fr in tags.getall('TALB'):
                    if fr.text:
                        parts.extend([t for t in fr.text if t])
                if parts:
                    self.album = '/'.join(parts)

            for tag in tags.values():
                if isinstance(tag, APIC):
                    if tag.type == 3:
                        self.image_data = tag.data
                        break
            if not self.image_data:
                for tag in tags.values():
                    if isinstance(tag, APIC):
                        self.image_data = tag.data
                        break

        except Exception as e:
            print(f"Error loading {self.filepath}: {e}")

    def save(self, title, artist, album, new_image_path=None, new_filepath=None):
        dest_path = new_filepath if new_filepath else self.filepath

        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, "temp_edit.mp3")

        try:
            shutil.copy2(self.filepath, temp_path)

            audio = MP3(temp_path, ID3=ID3)

            try:
                audio.add_tags()
            except error:
                pass

            tags = audio.tags

            for key in ('TIT2', 'TPE1', 'TALB'):
                tags.delall(key)

            tags.add(TIT2(encoding=1, text=title))
            tags.add(TPE1(encoding=1, text=artist))
            tags.add(TALB(encoding=1, text=album))

            if new_image_path and os.path.exists(new_image_path):
                with open(new_image_path, "rb") as img_file:
                    img_data = img_file.read()

                mime = 'image/jpeg' if new_image_path.lower().endswith(('.jpg', '.jpeg')) else 'image/png'

                apic_keys = [k for k in tags.keys() if k.startswith('APIC')]
                for k in apic_keys:
                    tags.delall(k)

                tags.add(
                    APIC(
                        encoding=1,
                        mime=mime,
                        type=3,
                        desc='Cover',
                        data=img_data
                    )
                )

            audio.save(v2_version=3)

            if os.path.abspath(dest_path).lower() != os.path.abspath(self.filepath).lower():
                if os.path.exists(dest_path):
                    raise Exception("A file with this title already exists. Overwriting is not supported automatically.")

                shutil.move(temp_path, dest_path)

                try:
                    os.remove(self.filepath)
                except OSError:
                    print(f"Warning: Could not remove old file {self.filepath} because it is in use.")
            else:
                os.replace(temp_path, dest_path)

            self.filepath = dest_path
            self.title = title
            self.artist = artist
            self.album = album
            if new_image_path:
                with open(new_image_path, "rb") as f:
                    self.image_data = f.read()

            return True, ""
        except Exception as e:
            print(f"Error saving {self.filepath}: {e}")
            return False, str(e)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

def get_mp3_files(folder_path):
    if not os.path.isdir(folder_path):
        return []
    return [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith('.mp3')]
