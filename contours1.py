import cv2
import numpy as np
from PIL import Image
import pyautogui
import keyboard

img1= 1

MIN_CONTOUR_AREA = 0   
MAX_CONTOUR_AREA = 15000 

# Canny thresholds / morphology
CANNY_LOW_THRESHOLD = 50  # Often lower thresholds for morphology
CANNY_HIGH_THRESHOLD = 150

# MORPH_KERNEL_SIZE = (5, 15) # Rectangular kernel: (width, height) 
MORPH_KERNEL_SIZE = (12, 12) 
MORPH_ITERATIONS = 1      
# ---


try:
    screenshot = Image.open('test.png')
except FileNotFoundError:
    print("Error: scr.png not found. Make sure the image is in the same directory.")
    exit()


img_orig = np.array(screenshot)

# Ensure image is 3-channel BGR
if img_orig.shape[2] == 4:
    img = cv2.cvtColor(img_orig, cv2.COLOR_BGRA2BGR)
elif img_orig.shape[2] == 3:
    img = cv2.cvtColor(img_orig, cv2.COLOR_RGB2BGR)
else:
     print(f"Error: Unexpected number of channels in image: {img_orig.shape[2]}")
     exit()

# drawing
img_display = img.copy()


gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Canny edge detection
edges = cv2.Canny(gray, CANNY_LOW_THRESHOLD, CANNY_HIGH_THRESHOLD)

kernel = cv2.getStructuringElement(cv2.MORPH_RECT, MORPH_KERNEL_SIZE)

closed_edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=MORPH_ITERATIONS)

contours, hierarchy = cv2.findContours(closed_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

print(f"Found {len(contours)} contours after morphology.")

# cv2.imshow('Original Edges', edges)
# cv2.imshow('Closed Edges', closed_edges)
# cv2.waitKey(0)
# ---

icons_found = 0
for contour in contours:
    # Calculate contour area
    area = cv2.contourArea(contour)
    if MIN_CONTOUR_AREA < area < MAX_CONTOUR_AREA:
        
        x, y, w, h = cv2.boundingRect(contour)
        # aspect_ratio = float(w)/h
        # icons_found += 1
        M = cv2.moments(contour)
        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
        else:
            cX, cY = x + w // 2, y + h // 2
        cv2.rectangle(img_display, (x, y), (x + w, y + h), (255, 0, 0), 2)
        img3 = img.copy()
        cropped_board = img3[y:y+h, x:x+w]
        cv2.imwrite(f'{img1}.png', cropped_board)
        img1 +=1

print(f"Filtered down to {icons_found} potential icon+text regions.")

print("Press 'q' to exit the program.")

keyboard.wait('q')

for imag in range(1, 26):

    element_image = f'{imag}.png'
    element_location = pyautogui.locateOnScreen(element_image)

    if element_location:
        element_center = pyautogui.center(element_location)
        print(f"Element found at: {element_center}")
    else:
        print("Element not found on the screen.")
cv2.waitKey(0)
cv2.destroyAllWindows()
