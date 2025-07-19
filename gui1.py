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

try:
    screenshot = Image.open('scr.png')
except FileNotFoundError:
    print("Error: scr.png not found. Make sure the image is in the same directory.")
    exit()

img_orig = np.array(screenshot)

if img_orig.shape[2] == 4:
    img = cv2.cvtColor(img_orig, cv2.COLOR_BGRA2BGR)
elif img_orig.shape[2] == 3:
    img = cv2.cvtColor(img_orig, cv2.COLOR_RGB2BGR)
else:
     print(f"Error: Unexpected number of channels in image: {img_orig.shape[2]}")
     exit()

img_display = img.copy()
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
edges = cv2.Canny(gray, CANNY_LOW_THRESHOLD, CANNY_HIGH_THRESHOLD)
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, MORPH_KERNEL_SIZE)
closed_edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=MORPH_ITERATIONS)
contours, hierarchy = cv2.findContours(closed_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

print(f"Found {len(contours)} contours initially after morphology.")

saved_image_count = 0 
image_counter = 1   

for i, contour in enumerate(contours):
    area = cv2.contourArea(contour)

    if MIN_CONTOUR_AREA < area < MAX_CONTOUR_AREA:
        x, y, w, h = cv2.boundingRect(contour)

        if w > 0 and h > 0:
            print(f"Processing contour {i}: Area={area:.2f}, Box=(x={x}, y={y}, w={w}, h={h}) -> Saving as {image_counter}.png")
            cv2.rectangle(img_display, (x, y), (x + w, y + h), (255, 0, 0), 2)
            cv2.putText(img_display, str(image_counter), (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1) 

            img_to_save = img.copy() 
            cropped_region = img_to_save[y:y+h, x:x+w]

            if cropped_region.size > 0:
                save_path = f'{image_counter}.png'
                try:
                    cv2.imwrite(save_path, cropped_region)
                    print(f"   Successfully saved {save_path}")
                    saved_image_count += 1 
                    image_counter += 1  
                except Exception as e:
                    print(f"   ERROR saving {save_path}: {e}")
            else:
                print(f"   Skipped saving contour {i}: Cropped region is empty (w={w}, h={h})")
        else:
             print(f"Skipping contour {i}: Invalid bounding box (w={w}, h={h})")


print(f"\nFinished processing contours. Saved {saved_image_count} images.")
print("\nReview the 'Detected Regions' window.")
print("Press 'q' in the terminal (not the image window) to proceed to PyAutoGUI search, or close the window.")

keyboard.wait('q')
cv2.destroyAllWindows()

print("\nStarting PyAutoGUI search...")
if saved_image_count > 0:
    for i in range(1, saved_image_count + 1):
        element_image = f'{i}.png'
        print(f"Searching for: {element_image}")

        if not os.path.exists(element_image):
            print(f"   Error: Template image {element_image} not found. Skipping.")
            continue

        try:
            # confidence matching (0.8-0.95)
            element_location = pyautogui.locateOnScreen(element_image, confidence=0.85)

            if element_location:
                element_center = pyautogui.center(element_location)
                print(f"   Element {i} FOUND at: {element_center}")
            else:
                print(f"   Element {i} NOT found on the screen.")
        except pyautogui.PyAutoGUIException as e:
            print(f"   PyAutoGUI error searching for {element_image}: {e}")
        except Exception as e:
            print(f"   Unexpected error searching for {element_image}: {e}")
else:
    print("No images were saved by OpenCV, skipping PyAutoGUI search.")


pyautogui.moveTo(187, 137, duration=1) 
# pyautogui.moveRel(xOffset, yOffset, duration=num_seconds)

# pyautogui.click(x=187, y=137, clicks=1, interval=0.1, button='left')

pyautogui.doubleClick(x=187, y=137)

print("\nProgram finished.")



# pyautogui.moveTo(187, 137, duration=2) 
# pyautogui.click(x=187, y=137, clicks=1, interval=0.1, button='left')
