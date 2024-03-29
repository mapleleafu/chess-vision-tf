from PIL import Image
from core.vision import crop_chessboard
import os

def crop_chess_board_squares(image, output_folder, square_size=0):
    square_width, square_height = square_size, square_size
    letters = ["A", "B", "C", "D", "E", "F", "G", "H", ]
    for i in range(0, 8):
        count = 1
        for j in range(0, 8):
            left = j * square_width
            upper = i * square_height
            right = left + square_width
            lower = upper + square_height

            cropped_square = image.crop((left, upper, right, lower))

            output_file_name = os.path.join(output_folder, f"{letters[j]}{8 - i}.png")
            cropped_square.save(output_file_name)
            count += 1

def square_maker(img, cropped):
    output_folder = 'processed/64_squares'
    # Create the output directory if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    width, height = cropped.size
    square_size = width // 8
    crop_chess_board_squares(cropped, output_folder, square_size)
