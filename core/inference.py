import os
import cv2
import numpy as np
from tensorflow.keras.models import load_model

class BoardClassifier:
    def __init__(self, model_path='models/model.h5'):
        self.model_path = model_path
        self.model = None
        self.img_size = 100
        self.categories = ["bb", "bk", "bn", "bp", "bq", "br", "wb", "wk", "wn", "wp", "wq", "wr", "zEmpty"]
        # Standard chess files (columns) a-h
        self.files = ["A", "B", "C", "D", "E", "F", "G", "H"]

    def load_model(self):
        """Lazy loads the model only when needed."""
        if self.model is None:
            print("Loading TensorFlow model... (this may take a moment)")
            try:
                self.model = load_model(self.model_path)
            except OSError:
                print(f"Error: Model not found at {self.model_path}")
                raise

    def preprocess_image(self, image_path):
        """Reads and formats an image for the CNN."""
        img = cv2.imread(image_path, cv2.IMREAD_ANYCOLOR)
        if img is None:
            return None
        
        img_resized = cv2.resize(img, (self.img_size, self.img_size))
        # Normalize pixel values to 0-1
        img_normalized = img_resized.astype('float32') / 255.0
        # Expand dims to match model input (1, 100, 100, 3)
        return np.expand_dims(img_normalized, axis=0)

    def predict_board(self, squares_dir):
        """
        Iterates through A1..H8 images in the directory and returns predictions.
        Returns: Dict { 'A1': 'wp', 'A2': 'wp', ... }
        """
        self.load_model()
        board_state = {}

        for file_char in self.files:
            for rank_num in range(1, 9): # 1 to 8
                square_name = f"{file_char}{rank_num}"
                img_path = os.path.join(squares_dir, f"{square_name}.png")

                processed_img = self.preprocess_image(img_path)
                
                if processed_img is not None:
                    prediction = self.model.predict(processed_img, verbose=0)
                    class_idx = np.argmax(prediction)
                    piece_code = self.categories[class_idx]
                    board_state[square_name] = piece_code
                else:
                    print(f"Warning: Could not read image for {square_name}")
                    board_state[square_name] = "zEmpty"

        return board_state