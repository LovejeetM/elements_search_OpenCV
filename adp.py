import cv2
import numpy as np
from PIL import Image

MIN_CONTOUR_AREA = 15
MAX_CONTOUR_AREA = 10000  


ADAPTIVE_BLOCK_SIZE = 15
ADAPTIVE_C = 5

MORPH_KERNEL_SIZE = (9, 3)
MORPH_ITERATIONS = 1

try:
    screenshot = Image.open('test.png') 
except FileNotFoundError:
    print("Error: test.png not found.")
    exit()


img_orig = np.array(screenshot)

# img = cv2.cvtColor(img_orig, cv2.COLOR_RGB2BGR)
if img_orig.shape[2] == 4:
    img = cv2.cvtColor(img_orig, cv2.COLOR_BGRA2BGR)
elif img_orig.shape[2] == 3:
    img = cv2.cvtColor(img_orig, cv2.COLOR_RGB2BGR)
else:
     print(f"Error: Unexpected number of channels in image: {img_orig.shape[2]}")
     exit()


img_display = img.copy()


gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


thresh_img = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, ADAPTIVE_BLOCK_SIZE, ADAPTIVE_C)


kernel = cv2.getStructuringElement(cv2.MORPH_RECT, MORPH_KERNEL_SIZE)
closed_thresh = cv2.morphologyEx(thresh_img, cv2.MORPH_CLOSE, kernel, iterations=MORPH_ITERATIONS)

contours, hierarchy = cv2.findContours(closed_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
contours, hierarchy = cv2.findContours(closed_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

print(f"Found {len(contours)} contours after thresholding and morphology.")

cv2.imshow('Grayscale', gray)
cv2.imshow('Adaptive Threshold', thresh_img)
cv2.imshow('Closed Threshold', closed_thresh)

elements_found = 0
for contour in contours:
    area = cv2.contourArea(contour)

    if MIN_CONTOUR_AREA < area < MAX_CONTOUR_AREA:
        x, y, w, h = cv2.boundingRect(contour)

        aspect_ratio = float(w) / h if h > 0 else 0


        elements_found += 1

        M = cv2.moments(contour)
        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
        else:
            cX, cY = x + w // 2, y + h // 2

        cv2.rectangle(img_display, (x, y), (x + w, y + h), (0, 0, 255), 2)
        # cv2.circle(img_display, (cX, cY), radius=3, color=(0, 0, 255), thickness=-1)

print(f"Filtered down to {elements_found} potential elements.")

cv2.imwrite("example.png", img_display)
cv2.imshow('Detected Elements (Adaptive Thresholding)', img_display)
cv2.waitKey(0)
cv2.destroyAllWindows()

