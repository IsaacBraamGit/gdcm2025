from PIL import Image, ImageFilter
import numpy as np
from gdpc import Editor, Block
from gdpc import geometry
import math
from scipy.ndimage import binary_dilation, convolve

editor = Editor(buffering=True)


def add_bubble_column(binary_array, build_height, radius):
    black_pixels = np.argwhere(binary_array)
    avg_x = int(np.mean(black_pixels[:, 0]))
    avg_z = int(np.mean(black_pixels[:, 1]))

    dx = avg_x - binary_array.shape[0] // 2
    dz = avg_z - binary_array.shape[1] // 2

    dy = int(math.sqrt(max(0, radius ** 2 - dx ** 2 - dz ** 2)))

    # Actual world position
    wx, wz = dx, dz
    #todo: change to height map
    base_y = 0  # Start at ground level (Y = 0)
    top_y = build_height + dy  # End at top of dome at that X,Z position

    # Build glass tube and water
    for y in range(base_y, top_y + 1):
        # Glass walls
        for dx_ in [-1, 0, 1]:
            for dz_ in [-1, 0, 1]:
                if abs(dx_) == 1 or abs(dz_) == 1:
                    if dx_ == 0 or dz_ == 0:
                        editor.placeBlock((wx + dx_, y, wz + dz_), Block("glass"))
                    else:
                        editor.placeBlock((wx + dx_, y, wz + dz_), Block("sea_lantern"))
        # Water inside
        editor.placeBlock((wx, y, wz), Block("water"))

    # Bubble source at the bottom
    editor.placeBlock((wx, base_y, wz), Block("soul_sand"))




def build_image_on_dome(
    image_path,
    resize_to=(200, 200),
    build_height=20,
    radius=50,
    thickness=1,
    line_thickness=1,
    min_neighbors_for_core=5  # NEW: control glow core threshold
):
    """
    Projects a 2D image onto a hemisphere surface in Minecraft for a smooth 3D logo,
    with optional line thickening and glowing core detection.
    """

    # Load and blur the image
    image = Image.open(image_path).convert("L").resize(resize_to)
    blurred = image.filter(ImageFilter.GaussianBlur(radius=1))
    image_array = np.array(blurred)
    binary_array = image_array < 128  # Dark = True

    # Thicken the binary mask
    if line_thickness > 1:
        structure = np.ones((line_thickness, line_thickness), dtype=bool)
        binary_array = binary_dilation(binary_array, structure=structure)

    # Count neighbors to detect line "core" pixels
    neighbor_kernel = np.ones((10, 10), dtype=int)
    neighbor_count = convolve(binary_array.astype(int), neighbor_kernel, mode='constant', cval=0)
    core_array = (binary_array) & (neighbor_count >= min_neighbors_for_core)

    # Blocks
    outer_block = Block("white_concrete")
    core_block = Block("redstone_block")

    width, height = resize_to
    center_x = width // 2
    center_z = height // 2

    for x in range(width):
        for z in range(height):
            if binary_array[x, z]:
                dx = x - center_x
                dz = z - center_z
                distance = math.sqrt(dx**2 + dz**2)
                if distance > radius:
                    continue

                dy = math.sqrt(max(0, radius**2 - dx**2 - dz**2))
                block_type = core_block if core_array[x, z] else outer_block

                for t in range(thickness):
                    wx = dx
                    wy = build_height + int(dy) - t
                    wz = dz

                    # Choose block based on depth (t = 0 is outermost, t = thickness - 1 is deepest)
                    if core_array[x, z] and thickness >= 5 and t == thickness - 5:
                        block_type = Block("redstone_lamp")
                    elif core_array[x, z] and thickness >= 4 and t == thickness - 4:
                        block_type = Block("sculk_sensor")
                    elif core_array[x, z] and thickness >= 3 and t == thickness - 3:
                        block_type = Block("amethyst_block")
                    elif core_array[x, z] and thickness >= 2 and t == thickness - 2:
                        block_type = Block("sculk_sensor")
                    elif core_array[x, z] and thickness >= 1 and t == thickness - 1:
                        block_type = Block("redstone_lamp")
                    else:
                        block_type = core_block if core_array[x, z] else outer_block

                    geometry.placeCuboid(editor, (wx, wy, wz), (wx, wy, wz), block_type)
    add_bubble_column(binary_array, build_height, radius)


# Run with pushTransform
buildArea = editor.getBuildArea()
WORLDSLICE = editor.loadWorldSlice(buildArea.toRect(), cache=True)

# Replace function call accordingly
with editor.pushTransform((buildArea.offset.x, 0, buildArea.offset.z)):
    build_image_on_dome(
        image_path="gpt2.png",
        resize_to=(200, 200),
        build_height=50,
        radius=120,
        thickness=5,
        line_thickness=5,
        min_neighbors_for_core=90
    )
