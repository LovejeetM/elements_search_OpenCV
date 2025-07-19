import cv2
import numpy as np
from PIL import Image
import pyautogui
import keyboard
import os

MIN_CONTOUR_AREA = 100
MAX_CONTOUR_AREA = 15000
CANNY_LOW_THRESHOLD = 50
CANNY_HIGH_THRESHOLD = 150
MORPH_KERNEL_SIZE = (12, 12)
MORPH_ITERATIONS = 1
MARGIN = 5 

screenshot = Image.open('test.png')

def detect(screenshot):
    global img_display

    img = np.array(screenshot)
    img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    img_display = img.copy()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, CANNY_LOW_THRESHOLD, CANNY_HIGH_THRESHOLD)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, MORPH_KERNEL_SIZE)
    closed_edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=MORPH_ITERATIONS)
    contours, hierarchy = cv2.findContours(closed_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    print(f"Found {len(contours)} contours initially after morphology.")

    saved_image_count = 0
    image_counter = 1
    
    # image dimensions
    img_height, img_width = img.shape[:2] 

    for i, contour in enumerate(contours):
        area = cv2.contourArea(contour)

        if MIN_CONTOUR_AREA < area < MAX_CONTOUR_AREA:
            x, y, w, h = cv2.boundingRect(contour)

            
            x_m = max(0, x - MARGIN)
            y_m = max(0, y - MARGIN)
            x_end = min(img_width, x + w + MARGIN)
            y_end = min(img_height, y + h + MARGIN)

            
            w_m = x_end - x_m
            h_m = y_end - y_m

            if w_m > 0 and h_m > 0:
                print(f"Processing contour {i}: Area={area:.2f}, Box=(x={x}, y={y}, w={w}, h={h}) -> Saving margined region as {image_counter}.png")
                cv2.rectangle(img_display, (x, y), (x + w, y + h), (255, 0, 0), 2)
                cv2.putText(img_display, str(image_counter), (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

                img_to_save = img.copy()
                cropped_region = img_to_save[y_m:y_end, x_m:x_end]

                if cropped_region.size > 0:
                    save_path = f'{image_counter}.png'
                    cv2.imwrite(save_path, cropped_region)
                    print(f"   Successfully saved {save_path}")
                    saved_image_count += 1
                    image_counter += 1

cv2.imshow('Detected Regions', img_display)

# keyboard.wait('q')
cv2.waitKey(0)
cv2.destroyAllWindows()