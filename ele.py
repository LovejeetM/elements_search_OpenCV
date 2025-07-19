import cv2
import numpy as np
from PIL import Image

screenshot= Image.open('test.png')
img = np.array(screenshot)
img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Canny edge detection
edges = cv2.Canny(gray, 50, 150)

contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
cv2.drawContours(img, contours, -1, (0, 255, 0), 2)

cv2.imshow('Detected Elements', img)
cv2.waitKey(0)
cv2.destroyAllWindows()