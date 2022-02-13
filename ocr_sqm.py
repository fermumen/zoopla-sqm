from PIL import Image
import pytesseract
import re

oem = 3
psm = 6

class Property():
    def __init__(self,img_path):
        self.img_path = img_path
        self.patterns = {'ft':'(\d\d\d).+?sq.+?(feet|ft)', 'm':'(\d\d).+?sq.+?(meter|m)'}
    def __str__(self):
        return f"Detected {self.sqft} sq.ft. and {self.sqm} sqm."
    def get_text(self, oem=3, psm=6):
        custom_config = f'--oem {oem} --psm {psm}'
        self.text = pytesseract.image_to_string(Image.open(self.img_path), config = custom_config)
        return self
    def find_pattern_in_img(self):
        self.sqm = re.findall(self.patterns['m'], self.text, re.IGNORECASE)
        self.sqft = re.findall(self.patterns['ft'], self.text, re.IGNORECASE)
        self.sqm = self.get_highest_sqm_value(self.sqm, 50)
        self.sqft = self.get_highest_sqm_value(self.sqft, 500)
    def get_highest_sqm_value(self, found, limit):
        list1 = [int(x[0]) for x in found]
        list1.sort
        result = list1[-1]
        if result < limit:
            result = None
        return result
    def iterate_parameters(self):
        psm_list = list(range(6,13)) + list(range(1,6))
        for psm in psm_list:
            self.get_text(oem=3,psm=psm)
            self.find_pattern_in_img()
            if (self.sqm is not None) or (self.sqft is not None): 
                break





house1 = Property('test2.jpg')
house1.iterate_parameters()
print(house1)