from core import image_processor
import sys
import os

print("TEST IMAGE PROCESSOR")
def test_image_processor():
    try: 
        IMG_PATH = 'assets/imagen_test.webp'
        TEST_OUTPUT_PATH = 'tests/outputs/image_processor_test/'

        img = image_processor._read_image(IMG_PATH)
        img_gray = image_processor._to_grayscale(img)
        img_eq = image_processor._equalize(img_gray)
        img_base64 = image_processor._to_base64(img_eq)
        full_pipeline = image_processor.preprocess(IMG_PATH)

        import cv2
        cv2.imwrite(TEST_OUTPUT_PATH+'test_img.png', img)
        cv2.imwrite(TEST_OUTPUT_PATH+'test_img_gray.png', img_gray)
        cv2.imwrite(TEST_OUTPUT_PATH+'test_img_eq.png', img_eq)
        output = image_processor.preprocess(IMG_PATH)
        assert "base64" in output and "shape" in output
        return (True, "Correcto")
    except Exception as e:
        print(str(e))
        return (False, str(e))
