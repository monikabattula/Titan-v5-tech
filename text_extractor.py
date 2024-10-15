import pytesseract
from pytesseract import Output
from PIL import Image
import cv2

def text_extractor(image_path):
  img_path1 = image_path
  text = pytesseract.image_to_string(img_path1,lang='eng')
  print(text)
  return text

# import easyocr
# import cv2
# import ssl
# ssl._create_default_https_context = ssl._create_unverified_context


# def text_extractor(image_path):
#   reader = easyocr.Reader(['en'], gpu=True)
#   result = reader.readtext(image_path)
#   extracted_text = [entry[1] for entry in result]
#   result_string = '\n'.join(extracted_text)
#   print(result_string)
#   return result_string