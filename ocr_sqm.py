from PIL import Image
import pytesseract
import re


class Property():
    def __init__(self,img_path):
        self.img_path = img_path
        self.patterns = {'ft':'(\d\d\d\d?).+?sq.+?(feet|ft)', 'm':'([.\d]+)\s*(?:sq).{0,5}(m|meters|metres)'}
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
        if len(found)==0: return None
        list1 = [float(x[0]) for x in found]
        list1 = sorted(list1)
        result = list1[-1]
        if result < limit:
            result = None
        return result
    def iterate_parameters(self):
        #psm_list = list(range(6,13)) + list(range(1,6))
        for psm in [6,3,11,12]:
            self.get_text(oem=3,psm=psm)
            self.find_pattern_in_img()
            if (self.sqm is not None) or (self.sqft is not None): 
                break




if __name__ == "__main__":
    # house1 = Property('./example_images/test.jpg')
    # house1.iterate_parameters()
    # print(house1)

    # house1 = Property('extracted_images/1e27f846-910b-11ec-9f8c-c4b301d0ad5b.jpg')
    # house1.iterate_parameters()
    # print(house1)

    for i in [1,2,3,4]:
        h = Property(f"./example_images/test{i}.jpg")
        h.iterate_parameters()
        # print(h.text)
        print(h)


    a = re.findall(h.patterns['m'], h.text, re.IGNORECASEa)
    b = [float(x[0]) for x in a]
