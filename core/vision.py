import cv2
import numpy as np
from PIL import Image
from dotenv import load_dotenv
import os

load_dotenv()

Chess_Board_ML = os.getenv("Chess_Board_ML_DIR")

def line_intersection(line1, line2):
    x1, y1, x2, y2 = line1
    x3, y3, x4, y4 = line2
    det = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if det != 0:
        px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / det
        py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / det
        return px, py
    else:
        return None

def find_chessboard(image, canny_low=50, canny_high=150):
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray_image, (5, 5), 0)
    edges = cv2.Canny(blurred, canny_low, canny_high)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    largest_area = 0
    chessboard_contour = None

    for contour in contours:
        area = cv2.contourArea(contour)
        if area > largest_area:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = float(w) / h

            if 0.8 <= aspect_ratio <= 1.2:
                largest_area = area
                chessboard_contour = contour

    if chessboard_contour is not None:
        x, y, w, h = cv2.boundingRect(chessboard_contour)
        return x, y, x + w, y + h

    return None



def crop_chessboard(image, padding=3):
    cv2_img = np.array(image)
    chessboard_coordinates = find_chessboard(cv2_img)

    if chessboard_coordinates is not None:
        x1, y1, x2, y2 = chessboard_coordinates

        x1 = max(x1 - padding, 0)
        y1 = max(y1 - padding, 0)
        x2 = min(x2 + padding, cv2_img.shape[1])
        y2 = min(y2 + padding, cv2_img.shape[0])

        cropped_img = image.crop((x1, y1, x2, y2))
        cropped_img.save('cropped_chessboard.png')

        return cropped_img
    else:
        print("Chessboard not found in the image.")
        return None


