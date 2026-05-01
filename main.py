import customtkinter as ctk
from ui import SpotifyLocalFileManager

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("green")
    
    app = SpotifyLocalFileManager()
    app.mainloop()
