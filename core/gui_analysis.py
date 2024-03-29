import sys
import os
import threading
import tkinter as tk
import webbrowser
import chess
import platform
from tkinter import messagebox
from PIL import Image, ImageTk
from stockfish import Stockfish, StockfishException

# Try importing your local modules
try:
    from core.inference import BoardClassifier
    from core.utils import rotate_board_and_change_side
except ImportError:
    pass 

PIECE_MAP = {
    "bb": "b", "bk": "k", "bn": "n", "bp": "p", "bq": "q", "br": "r",
    "wb": "B", "wk": "K", "wn": "N", "wp": "P", "wq": "Q", "wr": "R",
}

COLORS = {
    'bg': '#1e1e1e',
    'fg': '#ffffff',
    'button_bg': '#4a9eff',
    'button_hover': '#3a8eef',
    'button_fg': '#ffffff',
    'secondary_bg': '#2b2b2b',
    'success': '#51cf66',
    'error': '#ff6b6b',
    'info': '#4a9eff',
    'light_square': '#F0D9B5',
    'dark_square': '#B58863'
}

def get_stockfish_instance():
    # 1. Check local 'engines' folder
    binary_name = "stockfish.exe" if platform.system() == 'Windows' else "stockfish"
    local_path = os.path.join(os.getcwd(), "engines", binary_name)
    
    if os.path.exists(local_path):
        try:
            return Stockfish(path=local_path)
        except Exception as e:
            print(f"Warning: Found binary at {local_path} but failed to load: {e}")

    # 2. Check Global PATH
    try:
        return Stockfish() 
    except (FileNotFoundError, StockfishException):
        return None

class ChessBoardGUI(tk.Toplevel):
    def __init__(self, fen, stockfish_engine=None):
        super().__init__()
        self.title("Chess Analysis Board")
        self.geometry("500x680")
        self.configure(bg=COLORS['bg'])
        self.resizable(False, False)
        
        self.fen = fen if fen else chess.STARTING_FEN
        self.stockfish = stockfish_engine
        self.board = chess.Board(self.fen)
        self.images = [] 

        self.setup_header()
        
        self.canvas = tk.Canvas(self, width=400, height=400, bg=COLORS['bg'], highlightthickness=0)
        self.canvas.pack(pady=(10, 15))
        
        self.setup_ui()
        self.draw_board()
        self.draw_pieces()

    def setup_header(self):
        header_frame = tk.Frame(self, bg=COLORS['bg'])
        header_frame.pack(fill=tk.X, pady=(15, 5))
        
        tk.Label(header_frame, text="Analysis Board", font=('Segoe UI', 16, 'bold'),
                 bg=COLORS['bg'], fg=COLORS['fg']).pack()
        
        self.lbl_fen = tk.Label(header_frame, text=self.fen[:50] + "...", 
                                font=('Consolas', 8), bg=COLORS['bg'], fg='#888888')
        self.lbl_fen.pack(pady=(5, 0))

    def setup_ui(self):
        control_frame = tk.Frame(self, bg=COLORS['secondary_bg'])
        control_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        btn_style = {'font': ('Segoe UI', 10), 'relief': tk.FLAT, 'cursor': 'hand2', 'width': 12, 'padx': 10, 'pady': 8}
        
        # Row 1: External Tools
        row1 = tk.Frame(control_frame, bg=COLORS['secondary_bg'])
        row1.pack(pady=(15, 10))
        
        tk.Button(row1, text="📝 Editor", bg='#2c5282', fg='white', 
                  command=lambda: self.open_lichess('editor'), **btn_style).pack(side=tk.LEFT, padx=5)
        
        tk.Button(row1, text="🔍 Analysis", bg='#2c5282', fg='white', 
                  command=lambda: self.open_lichess('analysis'), **btn_style).pack(side=tk.LEFT, padx=5)
        
        # Row 2: Stockfish
        if self.stockfish:
            row2 = tk.Frame(control_frame, bg=COLORS['secondary_bg'])
            row2.pack(pady=(0, 15))
            
            tk.Button(row2, text="♔ Best Move", bg=COLORS['button_bg'], fg='white',
                      command=self.start_best_move_thread, **btn_style).pack(side=tk.LEFT, padx=5)
            
            tk.Button(row2, text="📊 Eval", bg=COLORS['button_bg'], fg='white',
                      command=self.start_eval_thread, **btn_style).pack(side=tk.LEFT, padx=5)
            
            self.lbl_info = tk.Label(control_frame, text="✓ Engine Ready", font=('Segoe UI', 13, 'bold'),
                                     bg=COLORS['secondary_bg'], fg=COLORS['success'], wraplength=420, pady=10)
            self.lbl_info.pack(fill=tk.X, padx=10, pady=(0, 10))
        else:
            tk.Label(control_frame, text="⚠ Stockfish not found", bg=COLORS['secondary_bg'], 
                     fg=COLORS['error'], pady=15).pack()

    def draw_board(self):
        colors = [COLORS['light_square'], COLORS['dark_square']]
        for i in range(8):
            for j in range(8):
                color = colors[(i + j) % 2]
                self.canvas.create_rectangle(i*50, j*50, (i+1)*50, (j+1)*50, fill=color, outline="")
        
        files, ranks = "abcdefgh", "87654321"
        for i in range(8):
            self.canvas.create_text(i*50+42, 392, text=files[i], font=('Segoe UI', 8, 'bold'), fill=colors[i%2])
            self.canvas.create_text(8, i*50+10, text=ranks[i], font=('Segoe UI', 8, 'bold'), fill=colors[(i+1)%2])

    def draw_pieces(self):
        self.canvas.delete("piece")
        self.images = [] 
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                color = "w" if piece.color == chess.WHITE else "b"
                # FIXED: Pointing back to your existing folder
                path = f"assets/pieces/{color}{piece.symbol().upper()}.png"
                if os.path.exists(path):
                    img = Image.open(path).resize((50, 50), Image.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    self.images.append(photo)
                    file_idx, rank_idx = chess.square_file(square), 7 - chess.square_rank(square)
                    self.canvas.create_image(file_idx*50+25, rank_idx*50+25, image=photo, tags="piece")

    def start_best_move_thread(self):
        self.lbl_info.config(text="Calculating...", fg=COLORS['info'])
        threading.Thread(target=self.calculate_best_move, daemon=True).start()

    def calculate_best_move(self):
        try:
            self.stockfish.set_fen_position(self.fen)
            move = self.stockfish.get_best_move()
            if move:
                text = f"♔ Best: {move}"
                self.after(0, lambda: self.lbl_info.config(text=text, fg=COLORS['info']))
            else:
                self.after(0, lambda: self.lbl_info.config(text="No move found", fg=COLORS['error']))
        except Exception as e:
            self.after(0, lambda: self.lbl_info.config(text="Error", fg=COLORS['error']))
            print(e)

    def start_eval_thread(self):
        self.lbl_info.config(text="Evaluating...", fg=COLORS['info'])
        threading.Thread(target=self.calculate_eval, daemon=True).start()

    def calculate_eval(self):
        try:
            self.stockfish.set_fen_position(self.fen)
            eval_data = self.stockfish.get_evaluation()
            val = eval_data.get('value')
            if eval_data.get('type') == 'mate':
                text = f"Mate in {val}"
                color = COLORS['success'] if val > 0 else COLORS['error']
            else:
                cp = val / 100.0
                text = f"Eval: {cp:+.2f}"
                color = COLORS['success'] if cp > 0 else COLORS['error'] if cp < 0 else COLORS['fg']
            self.after(0, lambda: self.lbl_info.config(text=text, fg=color))
        except Exception as e:
            self.after(0, lambda: self.lbl_info.config(text="Error", fg=COLORS['error']))
            print(e)

    def open_lichess(self, mode):
        url = f"https://lichess.org/{mode}/{self.fen.replace(' ', '_')}"
        webbrowser.open(url)

def open_analysis_window(fen=None):
    if not fen:
        print("Analyzing screen...")
        try:
            classifier = BoardClassifier()
            # Kept your path 'processed/64_squares'
            predictions = classifier.predict_board("processed/64_squares") 
            board = chess.Board.empty()
            for sq, piece in predictions.items():
                if piece != "zEmpty":
                    symbol = PIECE_MAP.get(piece)
                    if symbol:
                        board.set_piece_at(chess.parse_square(sq.lower()), chess.Piece.from_symbol(symbol))
            fen = board.fen()
            print(f"Generated FEN: {fen}")
        except Exception as e:
            print(f"Error generating FEN: {e}")
            fen = chess.STARTING_FEN

    engine = get_stockfish_instance()
    if tk._default_root is None:
        root = tk.Tk()
        root.withdraw()
    
    app = ChessBoardGUI(fen, engine)
    app.mainloop()

if __name__ == "__main__":
    open_analysis_window()