# We found a minor flaw in the code used for the images in the report
# The improved images can be seen as "Improved_NDVI_225" and "Improved_NDVI_312"
# The small difference in output NDVI is negligible and has no impact on the conclusions drawn in the report
# In addition, the new NDVI images make the positive influence of Colima even clearer. An expected change.
# The other high NDVI density areas can be explained by the general volcanic activity in the area and the volcanic ashes spread by Colimas' eruptions

from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import ListedColormap, LinearSegmentedColormap

viridis = cm.get_cmap('viridis')
im_mask = Image.open(str('C:/Users/Admin/desktop/phoenix/phoenix_mask.jpg')).convert('RGB')
def within_mask(mask_r, mask_g, mask_b):
    return mask_r == 255 and mask_g == 255 and mask_b == 255

for PhotoNummber in range(78,79):
    im = Image.open(str('C:/Users/Admin/desktop/phoenix/phoenix_' + str(PhotoNummber).zfill(3) + '.jpg')).convert('RGB')
    for x in range(0,2592):
        if x%10==0:
            print(str(round(x/2592*100)))
        for y in range (0, 1944):
            mask_r, mask_g, mask_b = im_mask.getpixel((x, y))
            if within_mask(mask_r, mask_g, mask_b):
                r, g, b = im.getpixel((x, y))
                if r+b!=0:
                    NDVI=((r-b)/(r+b)+1)/2
                else:
                    NDVI=0
                NDVI_AMP=(NDVI**7)*48
                RGB_float=viridis(NDVI_AMP)
                RGB_int=(round(RGB_float[0]*255), round(RGB_float[1]*255), round(RGB_float[2]*255))
                im.putpixel((x,y), RGB_int)
            else:
                im.putpixel((x,y), (0,0,0,0))
    im.save('c:/Users/Admin/desktop/NDVI/result' + str(PhotoNummber).zfill(3) + '.png')
