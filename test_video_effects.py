import sys
import os
from unittest.mock import MagicMock
import unittest
from PIL import Image, ImageChops, ImageDraw
import numpy as np

# Mock database module
db_mock = MagicMock()
sys.modules['database'] = db_mock

# Mock flask
flask_mock = MagicMock()
sys.modules['flask'] = flask_mock

# We assume app.py is in the current directory or PYTHONPATH
sys.path.append(os.getcwd())

try:
    from app import VideoProcessor
except ImportError as e:
    print(f"Failed to import VideoProcessor: {e}")
    sys.exit(1)

def images_are_equal(img1, img2):
    return ImageChops.difference(img1, img2).getbbox() is None

class TestVideoProcessorEffects(unittest.TestCase):
    def setUp(self):
        self.vp = VideoProcessor('uploads')
        # Create a test image with enough detail for all effects to be noticeable
        self.img = Image.new('RGB', (1000, 1000), color='white')
        draw = ImageDraw.Draw(self.img)
        draw.rectangle([200, 200, 800, 800], fill='red')
        draw.line([0, 0, 1000, 1000], fill='blue', width=20)
        self.img = self.img.resize((100, 100), Image.Resampling.LANCZOS)

    def test_sharpen_effect(self):
        processed = self.vp.apply_effect(self.img, 'sharpen')
        self.assertFalse(images_are_equal(self.img, processed), "Effect 'sharpen' should change the image")

    def test_solarize_effect(self):
        processed = self.vp.apply_effect(self.img, 'solarize')
        self.assertFalse(images_are_equal(self.img, processed), "Effect 'solarize' should change the image")

    def test_invert_effect(self):
        processed = self.vp.apply_effect(self.img, 'invert')
        self.assertFalse(images_are_equal(self.img, processed), "Effect 'invert' should change the image")

    def test_grayscale_effect(self):
        processed = self.vp.apply_effect(self.img, 'grayscale')
        self.assertFalse(images_are_equal(self.img, processed), "Effect 'grayscale' should change the image")
        # Grayscale image might still be in RGB mode (3 channels) but visually grayscale
        # If it was converted to 'L', convert back to RGB for consistency check if needed
        # but apply_effect implementation for grayscale usually returns RGB.
        
        # Check if pixels are gray (R=G=B)
        # Note: Our implementation returns RGB.
        pixels = list(processed.getdata())
        for r, g, b in pixels[:10]: # Check first 10 pixels
             self.assertTrue(abs(r - g) < 2 and abs(g - b) < 2, f"Pixel {(r,g,b)} is not grayscale")

if __name__ == '__main__':
    unittest.main()
