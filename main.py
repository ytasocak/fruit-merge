import os
import sys
import tkinter as tk
from PIL import Image, ImageTk
from fruit_merge.constants import (
    BG_COLOR,
    WINDOW_HEIGHT,
    WINDOW_TITLE,
    WINDOW_WIDTH,
)
from fruit_merge.game import FruitMergeGame


def center_window(root: tk.Tk, width: int, height: int) -> None:
    """Centers the Tkinter window on the primary screen."""
    root.update_idletasks()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = max(0, (screen_width - width) // 2)
    y = max(0, (screen_height - height) // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")


def main() -> None:
    root = tk.Tk()
    root.title(WINDOW_TITLE)
    root.configure(bg=BG_COLOR)
    root.resizable(True, True)
    root.minsize(720, 580)

    # Set custom window & taskbar icon
    icon_path = os.path.join(os.path.dirname(__file__), "assets", "fruits", "tier_1_cherry.png")
    if os.path.exists(icon_path):
        try:
            icon_img = ImageTk.PhotoImage(Image.open(icon_path).resize((32, 32)))
            root.iconphoto(True, icon_img)
            root._icon_img_ref = icon_img
        except Exception:
            pass

    # F11 shortcut to toggle fullscreen
    def toggle_fullscreen(event=None):
        is_fullscreen = bool(root.attributes("-fullscreen"))
        root.attributes("-fullscreen", not is_fullscreen)

    root.bind("<F11>", toggle_fullscreen)

    center_window(root, WINDOW_WIDTH, WINDOW_HEIGHT)

    app = FruitMergeGame(root)

    def on_closing():
        try:
            app.destroy()
        except Exception:
            pass
        root.destroy()
        sys.exit(0)

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
