@echo off
cd /d "%~dp0"
python -m pip install -r requirements.txt -r requirements-build.txt -q
python -m PyInstaller SpotifyLocalSong.spec --clean --noconfirm
echo.
echo Output: dist\SpotifyLocalSong\SpotifyLocalSong.exe
echo Zip dist\SpotifyLocalSong for GitHub Releases.
