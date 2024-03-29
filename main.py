import subprocess
import tkinter as tk
import chess
from tkinter import ttk
from core.vision import crop_chessboard
from core.capture import grab_screen
from core.grid import square_maker
from core.gui_analysis import open_analysis_window

COLORS = {
    'bg': '#2b2b2b',
    'fg': '#ffffff',
    'button_bg': '#4a9eff',
    'button_hover': '#3a8eef',
    'button_fg': '#ffffff',
    'entry_bg': '#3c3c3c',
    'entry_fg': '#ffffff',
    'error': '#ff6b6b',
    'success': '#51cf66',
    'frame_bg': '#1e1e1e'
}

def screenshot_button_click(error_label, root_window):
    error_label.config(text="Processing...", fg=COLORS['button_bg'])
    root_window.update()
    
    img = grab_screen()
    if img is None:
        error_label.config(text="No browser found!", fg=COLORS['error'])
        return False
    try:
        cropped_img = crop_chessboard(img)
        square_maker(img, cropped_img)
        error_label.config(text="Success! Opening analysis...", fg=COLORS['success'])
        root_window.update()
        open_analysis_window()
        error_label.config(text="")
        return True
    except subprocess.CalledProcessError as e:
        output = e.output
        print(f"An error occurred: {output}")
        error_label.config(text="Error processing image", fg=COLORS['error'])
        return False
    except Exception as e:
        print(f"Error: {e}")
        error_label.config(text=f"Error: {str(e)[:30]}", fg=COLORS['error'])
        return False


def fen_button_click(fen, fen_error_label, fen_entry, root_window):
    if not fen.strip():
        fen_error_label.config(text="Please enter a FEN string", fg=COLORS['error'])
        return False
    
    board = chess.Board()
    try:
        board.set_fen(fen)
        print("Valid FEN code.")
        fen_error_label.config(text="Valid FEN! Opening...", fg=COLORS['success'])
        root_window.update()
        open_analysis_window(fen)
        fen_error_label.config(text="")
        return True
    except ValueError:
        print("Error: Invalid FEN code.")
        fen_error_label.config(text="Invalid FEN position", fg=COLORS['error'])
        fen_entry.delete(0, tk.END)
        return False


def run_mainloop():
    root = tk.Tk()
    root.title("Chess Vision")
    root.geometry("420x280")
    root.configure(bg=COLORS['bg'])
    root.resizable(False, False)
    
    # Center window
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")

    # Title
    title_frame = tk.Frame(root, bg=COLORS['bg'])
    title_frame.pack(pady=(20, 10))
    title_label = tk.Label(
        title_frame, 
        text="Chess Vision", 
        font=('Segoe UI', 24, 'bold'),
        bg=COLORS['bg'],
        fg=COLORS['fg']
    )
    title_label.pack()
    subtitle_label = tk.Label(
        title_frame,
        text="Board Recognition & Analysis",
        font=('Segoe UI', 10),
        bg=COLORS['bg'],
        fg='#888888'
    )
    subtitle_label.pack()

    # Main content frame
    content_frame = tk.Frame(root, bg=COLORS['bg'])
    content_frame.pack(pady=20, padx=30, fill=tk.BOTH, expand=True)

    # Screenshot section
    screenshot_frame = tk.Frame(content_frame, bg=COLORS['bg'])
    screenshot_frame.pack(fill=tk.X, pady=(0, 15))
    
    take_screenshot_button = tk.Button(
        screenshot_frame,
        text="📸 Take Screenshot",
        font=('Segoe UI', 11, 'bold'),
        bg=COLORS['button_bg'],
        fg=COLORS['button_fg'],
        activebackground=COLORS['button_hover'],
        activeforeground=COLORS['button_fg'],
        relief=tk.FLAT,
        padx=20,
        pady=10,
        cursor='hand2',
        command=lambda: screenshot_button_click(screenshot_error_label, root)
    )
    take_screenshot_button.pack(fill=tk.X)

    screenshot_error_label = tk.Label(
        screenshot_frame,
        text="",
        font=('Segoe UI', 9),
        bg=COLORS['bg'],
        fg=COLORS['error'],
        height=1
    )
    screenshot_error_label.pack(pady=(5, 0))

    # FEN section
    fen_frame = tk.Frame(content_frame, bg=COLORS['bg'])
    fen_frame.pack(fill=tk.X)
    
    fen_label = tk.Label(
        fen_frame,
        text="Or enter FEN:",
        font=('Segoe UI', 9),
        bg=COLORS['bg'],
        fg='#aaaaaa',
        anchor='w'
    )
    fen_label.pack(fill=tk.X, pady=(0, 5))

    fen_entry = tk.Entry(
        fen_frame,
        font=('Consolas', 10),
        bg=COLORS['entry_bg'],
        fg=COLORS['entry_fg'],
        insertbackground=COLORS['fg'],
        relief=tk.FLAT,
        borderwidth=0,
        highlightthickness=1,
        highlightbackground='#555555',
        highlightcolor=COLORS['button_bg']
    )
    fen_entry.pack(fill=tk.X, ipady=8, pady=(0, 5))
    fen_entry.bind('<Return>', lambda e: fen_button_click(fen_entry.get(), fen_error_label, fen_entry, root))

    fen_button = tk.Button(
        fen_frame,
        text="Load FEN",
        font=('Segoe UI', 10),
        bg=COLORS['frame_bg'],
        fg=COLORS['fg'],
        activebackground='#2a2a2a',
        activeforeground=COLORS['fg'],
        relief=tk.FLAT,
        padx=15,
        pady=6,
        cursor='hand2',
        command=lambda: fen_button_click(fen_entry.get(), fen_error_label, fen_entry, root)
    )
    fen_button.pack(fill=tk.X)

    fen_error_label = tk.Label(
        fen_frame,
        text="",
        font=('Segoe UI', 9),
        bg=COLORS['bg'],
        fg=COLORS['error'],
        height=1
    )
    fen_error_label.pack(pady=(5, 0))

    root.mainloop()


if __name__ == "__main__":
    run_mainloop()
