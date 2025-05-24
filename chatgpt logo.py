
from PIL import Image
import numpy as np
from gdpc import Editor, Block
from gdpc import geometry

def build_image_in_minecraft(image_path, resize_to=(100, 100), build_height=50, scale=3):
    # Load and process the image
    image = Image.open(image_path).convert("L")
    image = image.resize(resize_to)
    image_array = np.array(image)

    # Threshold to binary: True = place block (black), False = air (white)
    binary_array = image_array < 128

    editor = Editor(buffering=True)
    block_type = Block("white_concrete")

    for x in range(resize_to[0]):
        for z in range(resize_to[1]):
            if binary_array[x][z]:
                geometry.placeCuboid(
                    editor,
                    (x * scale, build_height, z * scale),
                    (x * scale + scale - 1, build_height, z * scale + scale - 1),
                    block_type
                )

    editor.flush()

# Example usage
# Make sure to update the path to your image
build_image_in_minecraft("tpg.png")
