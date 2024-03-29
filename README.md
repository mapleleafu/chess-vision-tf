# Chess Vision: Real-Time Board Recognition & Analysis

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.20-orange.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

A computer vision application that recognizes chess positions from screenshots and provides engine analysis. Combines deep learning, computer vision, and chess engine integration into a cross-platform pipeline.

![Analysis Board Preview](https://i.imgur.com/Fm8eTkE.png)

## Architecture

```
Screen Capture → Chessboard Detection → Grid Segmentation → CNN Inference → FEN Generation → Stockfish Analysis
```

**Input:** Cross-platform screen capture (`mss` on Linux/Mac, `win32gui` on Windows) with automatic browser window detection.

**Vision:** Chessboard detection via OpenCV (Canny edge detection, contour analysis), 8×8 grid segmentation with coordinate mapping (A1-H8), image preprocessing (100×100 normalization).

**Inference:** Custom CNN model (TensorFlow/Keras) for 13-class piece classification (6 black pieces, 6 white pieces, empty square).

**Engine:** FEN generation from predictions using `python-chess`, Stockfish integration for evaluation and best move calculation.

## Setup

### Prerequisites

- Python 3.10+
- Stockfish binary ([download](https://stockfishchess.org/download/))

### Installation

1. Clone and setup environment:
   ```bash
   git clone <repository-url>
   cd chess-vision-tf
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Install Stockfish binary:
   - Place executable in `engines/` directory:
     - Windows: `engines/stockfish.exe`
     - Linux/Mac: `engines/stockfish`
   - Or ensure Stockfish is in system PATH

3. Place trained model at `models/model.h5`

### Platform Notes

**Windows:** Automatically detects and captures browser windows.

**Linux/Mac:** Captures primary monitor by default. For window-specific capture, install `xdotool` or `wmctrl`.

## Usage

```bash
python main.py
```

Two input methods:
- **Screenshot Analysis**: Captures screen, detects chessboard, classifies pieces, opens analysis window
- **FEN Input**: Directly load a position using Forsyth-Edwards Notation

![Main Window](https://i.imgur.com/7aMfvAD.png)

## License

MIT License - see LICENSE file for details.
