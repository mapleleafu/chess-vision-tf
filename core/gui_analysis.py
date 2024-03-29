import sys
import os
import tkinter as tk
import webbrowser
import chess
from tkinter import messagebox
from PIL import Image, ImageTk
from stockfish import Stockfish, StockfishException

from core.inference import BoardClassifier
from core.utils import rotate_board_and_change_side

PIECE_MAP = {
    "bb": "b", "bk": "k", "bn": "n", "bp": "p", "bq": "q", "br": "r",
    "wb": "B", "wk": "K", "wn": "N", "wp": "P", "wq": "Q", "wr": "R",
}

def get_stockfish_instance():
    """
    Attempts to load Stockfish from:
    1. A local 'engines' folder (e.g. engines/stockfish.exe)
    2. System PATH
    Returns None if failing.
    """
    # 1. Check local 'engines' folder
    binary_name = "stockfish.exe" if os.name == 'nt' else "stockfish"
    local_path = os.path.join(os.getcwd(), "engines", binary_name)
    
    if os.path.exists(local_path):
        try:
            return Stockfish(path=local_path)
        except Exception as e:
            print(f"Warning: Found binary at {local_path} but failed to load: {e}")

    # 2. Check Global PATH
    try:
        return Stockfish() # Expects 'stockfish' in system PATH
    except (FileNotFoundError, StockfishException):
        print("Warning: Stockfish not found in 'engines/' folder or system PATH.")
        return None

class ChessBoardGUI(tk.Toplevel):
    """
    Using Toplevel allows this window to be opened from a main menu 
    without blocking the entire app loop if you expand later.
    """
    def __init__(self, fen, stockfish_engine=None):
        super().__init__()
        self.title("Analysis Board")
        self.geometry("400x520")
        
        self.fen = fen
        self.stockfish = stockfish_engine
        self.board = chess.Board(fen)
        self.images = [] # Keep references to prevent GC

        # UI Components
        self.canvas = tk.Canvas(self, width=400, height=400)
        self.canvas.pack()
        
        self.button_area = tk.Frame(self)
        self.button_area.pack(fill=tk.X, pady=10)

        self.setup_ui()
        self.draw_board()
        self.draw_pieces()

    def setup_ui(self):
        # Action Buttons
        btn_opts = {'padx': 5, 'pady': 5, 'side': tk.LEFT}
        
        tk.Button(self.button_area, text="Open Lichess", command=self.open_lichess).pack(**btn_opts)
        
        if self.stockfish:
            tk.Button(self.button_area, text="Best Move", command=self.show_best_move).pack(**btn_opts)
            tk.Button(self.button_area, text="Eval", command=self.show_eval).pack(**btn_opts)
            self.lbl_info = tk.Label(self.button_area, text="Engine Ready", fg="green")
            self.lbl_info.pack(side=tk.LEFT, padx=10)
        else:
            tk.Label(self.button_area, text="Stockfish not found", fg="red").pack(**btn_opts)

    def draw_board(self):
        colors = ["#F0D9B5", "#B58863"] # Classic wood colors
        square_size = 50
        for i in range(8):
            for j in range(8):
                color = colors[(i + j) % 2]
                self.canvas.create_rectangle(
                    i * square_size, j * square_size, 
                    (i + 1) * square_size, (j + 1) * square_size, 
                    fill=color, outline=""
                )

    def draw_pieces(self):
        self.canvas.delete("piece")
        square_size = 50
        
        # Determine orientation
        # If it's black to move, usually we flip the board? 
        # For now, let's keep white-bottom default unless specified.
        
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                piece_color = "w" if piece.color == chess.WHITE else "b"
                piece_name = piece.symbol().upper() # P, N, B, R, Q, K
                image_path = f"assets/pieces/{piece_color}{piece_name}.png"
                
                if os.path.exists(image_path):
                    img = Image.open(image_path).resize((square_size, square_size), Image.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    self.images.append(photo)

                    # Calculate coords
                    file_idx = chess.square_file(square)
                    rank_idx = 7 - chess.square_rank(square)
                    
                    self.canvas.create_image(
                        file_idx * square_size + 25, 
                        rank_idx * square_size + 25, 
                        image=photo, tags="piece"
                    )

    def show_best_move(self):
        if not self.stockfish: return
        self.stockfish.set_fen_position(self.fen)
        move = self.stockfish.get_best_move()
        self.lbl_info.config(text=f"Best: {move}", fg="blue")

    def show_eval(self):
        if not self.stockfish: return
        self.stockfish.set_fen_position(self.fen)
        eval_data = self.stockfish.get_evaluation()
        val = eval_data.get('value')
        type_ = eval_data.get('type')
        
        if type_ == 'mate':
            text = f"Mate in {val}"
        else:
            text = f"CP: {val/100:.2f}"
            
        self.lbl_info.config(text=text, fg="blue")

    def open_lichess(self):
        fen_clean = self.fen.replace(" ", "_")
        webbrowser.open(f"https://lichess.org/analysis/{fen_clean}")

def open_analysis_window(fen=None):
    """
    Main logic to prepare data and open the window.
    """
    # 1. If no FEN provided, generate it using the Classifier
    if not fen:
        print("Analyzing screen...")
        try:
            classifier = BoardClassifier()
            predictions = classifier.predict_board("64_squares")
            
            # Convert predictions dict to FEN
            board = chess.Board.empty()
            for square_name, piece_code in predictions.items():
                if piece_code != "zEmpty":
                    piece_symbol = PIECE_MAP.get(piece_code)
                    if piece_symbol:
                        board.set_piece_at(chess.parse_square(square_name.lower()), chess.Piece.from_symbol(piece_symbol))
            
            fen = board.fen()
            print(f"Generated FEN: {fen}")
            
        except Exception as e:
            print(f"Error generating FEN: {e}")
            return

    engine = get_stockfish_instance()

    if tk._default_root is None:
        root = tk.Tk()
        root.withdraw()
    
    app = ChessBoardGUI(fen, engine)
    app.mainloop()

if __name__ == "__main__":
    # Test mode
    test_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    open_analysis_window(test_fen)