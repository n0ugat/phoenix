# importing cv2
import cv2

# Get image
photo_number = str(224).zfill(3)
path = "C:/Users/oscar/Google Drive/CreativeProjects/AstroPi/Images/phoenix_" + photo_number + ".jpg"
img = cv2.imread(path)
img_arr_r = img[:,:,2]

# Center coordinates
center_coordinates = (int(len(img_arr_r[1])/2), int(len(img_arr_r)/2)+50)
 
# Radius of circle
radius = 1095
  
# White color in BGR
color = (255,255,255)

# Line thickness of -1 px
thickness = -1

# Using cv2.circle() method
image = cv2.circle(img, center_coordinates, radius, color, thickness)

cv2.imwrite("C:/Users/oscar/Google Drive/CreativeProjects/AstroPi/Images/phoenix_mask_" + photo_number + ".jpg", image)