import cv2
from PIL import Image
import os
import io
from google.cloud import vision
from difflib import SequenceMatcher

FILENAME = "frame.jpg"

class ImageRecognition:
    def __init__(self):
        self.client = vision.ImageAnnotatorClient()

    def similar(self, a, b):
        return SequenceMatcher(None, a, b).ratio()
    
    def analyze(self, mods):
        filepath = os.path.realpath(FILENAME)

        with io.open(filepath, 'rb') as image_file:
            content = image_file.read()
        
        pil_image = Image.open(FILENAME)
        width, height = pil_image.size

        image = vision.types.Image(content=content)
        response = self.client.text_detection(image=image)
        texts = response.text_annotations

        item = 0
        modifiers = []
        left = ""
        right = ""
        prevWord = ""
        for text in texts:
            if item < 1:
                sentences = text.description.splitlines()
                for sentence in sentences:
                    for mod in mods:
                        if self.similar(sentence.lower(), mod.lower()) > 0.7:
                            modifiers.append(mod)
                            break
                item += 1
                continue

            if prevWord:
                stringToCheck = prevWord + " " + text.description
                for m in modifiers:
                    if stringToCheck.lower() in m.lower():
                        for vertex in text.bounding_poly.vertices:
                            xVertex = vertex.x
                            break

                        if (xVertex < width / 2) and not left:
                            left = m
                        elif (xVertex >= width / 2) and not right:
                            right = m

            prevWord = text.description
            item += 1

        return left, right
