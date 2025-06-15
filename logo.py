from PIL import Image, ImageFilter
import numpy as np
from gdpc import Editor, Block
from gdpc import geometry
import math
from scipy.ndimage import binary_dilation, convolve
import csv
import random

editor = Editor(buffering=True)

head = ["redstone", "coal", "lapis_lazuli", "emerald", "amethyst_shard"]

ore = [
    "redstone_ore", "coal_ore", "lapis_ore", "emerald_ore", "amethyst_cluster"
]

deep_ore = [
    "deepslate_redstone_ore", "deepslate_coal_ore", "deepslate_lapis_ore", "deepslate_emerald_ore", "amethyst_cluster"
]

block = [
    "redstone_block", "coal_block",
    "lapis_block", "emerald_block", "amethyst_block"
]

glass = [
    "red_stained_glass", "black_stained_glass",
    "blue_stained_glass", "lime_stained_glass", "purple_stained_glass"
]

candle = [
    "red_candle", "black_candle","blue_candle","lime_candle","purple_candle",
]
default = 0
choice = 0

# === Block Translator and Placement Generator ===

def change_text_prop(line):

    if "wire" not in str(line) and "ore" not in str(line) and "block" not in str(line):
        line = [cell.replace(head[default], head[choice]) for cell in line]
    line = [cell.replace(ore[default], ore[choice]) for cell in line]
    line = [cell.replace(deep_ore[default], deep_ore[choice]) for cell in line]
    line = [cell.replace(glass[default], glass[choice]) for cell in line]
    line = [cell.replace(block[default], block[choice]) for cell in line]
    line = [cell.replace(candle[default], candle[choice]) for cell in line]

    return line

def parse_props(block_str):
    if "[" in block_str:
        name, raw_props = block_str.split("[", 1)
        name = name.replace("minecraft:", "").strip()
        props = {}
        for pair in raw_props.rstrip("]").split(","):
            key, val = pair.split("=")
            key, val = key.strip(), val.strip()
            props[key] = val

        return name, props
    return block_str.replace("minecraft:", "").strip(), {}

def placeFromFile(filename, x_offset, y_offset, z_offset, orientation= 0, width=100, height=100):
    print(f"Placing blocks from {filename} with orientation {orientation}...")
    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # skip header
        for pos_str, block_str in reader:
            block_str = change_text_prop([block_str])[0]
            x, y, z = [int(v.strip()) for v in pos_str.strip("()").split(",")]
            x_rot, z_rot =x,z
            name, props = parse_props(block_str.strip())
 # <<<<< rotate metadata
            editor.placeBlock((x_rot + x_offset, y + y_offset, z_rot + z_offset), Block(name, props))
    print("Done.")
import random

def add_tornado(wx, wz, base_y, height=15):
    for y in range(height):
        layer_y = base_y + y
        swirl_radius = max(1, int(1 + y * 0.4))  # ✅ expands with height
  # Shrinks toward top
        angle_offset = random.uniform(0, 2 * math.pi)

        for i in range(0, 360, 30):  # Sparser points = twisty shape
            angle = math.radians(i) + angle_offset
            dx = int(math.cos(angle) * swirl_radius)
            dz = int(math.sin(angle) * swirl_radius)

            block_pos = (wx + dx, layer_y, wz + dz)

            # Random block type for variety
            block_type = random.choices(
                [block[choice], glass[choice], glass[choice]],
                weights=[0.3, 0.4, 0.3],
                k=1
            )[0]

            editor.placeBlock(block_pos, Block(block_type))


def add_reactor_tower(wx, wz, base_y, H, R0):
    base_y -= 1  # Lower build by 1

    wall_radii = []

    # === 1. Build red glass outer shell ===
    for y in range(H + 1):
        z_rel = y / H
        curve_factor = 0.9  # Increase this for more dramatic hourglass shape
        z_rel = y / H
        r = int(R0 * (1 + ((z_rel - 0.5) * 2) ** 2 * curve_factor)) + 1
        wall_radii.append(r)

        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                dist_sq = dx**2 + dz**2
                if r*r - 2*r <= dist_sq <= r*r:
                    editor.placeBlock((wx + dx, base_y + y, wz + dz), Block("orange_stained_glass"))

    # === 3. Bottom copper cap (1 layer) ===
    bottom_radius = wall_radii[0]
    for dx in range(-bottom_radius, bottom_radius + 1):
        for dz in range(-bottom_radius, bottom_radius + 1):
            if dx**2 + dz**2 <= bottom_radius**2:
                editor.placeBlock((wx + dx, base_y - 1, wz + dz), Block("waxed_copper_bulb"))

    # === 4. Top copper cap (1 layer) ===
    top_y = base_y + H + 1
    top_radius = wall_radii[-1]
    for dx in range(-top_radius, top_radius + 1):
        for dz in range(-top_radius, top_radius + 1):
            if dx**2 + dz**2 <= top_radius**2:
                editor.placeBlock((wx + dx, top_y, wz + dz), Block("waxed_copper_bulb"))

    # === 2. Fill lava inside the shell ===
    for y in range(H + 1):
        r = wall_radii[y] - 1
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                if dx*dx + dz*dz <= r*r:
                    editor.placeBlock((wx + dx, base_y + y, wz + dz), Block("lava"))


    # --- First: small filled circle on top ---
    radius = 2  # Gives a 5x5 block disc
    for dx in range(-radius, radius + 1):
        for dz in range(-radius, radius + 1):
            if dx*dx + dz*dz <= radius*radius:
                editor.placeBlock((wx + dx, top_y, wz + dz), Block("orange_stained_glass"))

    # --- Second: tight 5-block ring just above ---
    ring_y = top_y + 1
    offsets = [(1, 0), (-1, 0), (0, 1), (0, -1), (0, 0)]  # Plus center
    for dx, dz in offsets:
        editor.placeBlock((wx + dx, ring_y, wz + dz), Block("orange_stained_glass"))
    add_tornado(wx, wz, top_y + 1)  # Starts just above top copper cap

# def add_gold_pillars(wx, wz, top_y, radius=8, pillar_height=10, count=5):
#     """
#     Places gold block pillars in a circle around a center point (wx, wz)
#     starting from `top_y` downward.
#     """
#     for i in range(count):
#         angle = 2 * math.pi * i / count
#         dx = int(round(math.cos(angle) * radius))
#         dz = int(round(math.sin(angle) * radius))
#         px, pz = wx + dx, wz + dz
#
#         for dy in range(pillar_height):
#             editor.placeBlock((px, top_y - dy, pz), Block("gold_block"))

def add_bubble_column(binary_array, build_height, radius):

    black_pixels = np.argwhere(binary_array)
    avg_x = int(np.mean(black_pixels[:, 0]))
    avg_z = int(np.mean(black_pixels[:, 1]))

    dx = avg_x - binary_array.shape[0] // 2 - 1
    dz = avg_z - binary_array.shape[1] // 2

    dy = int(math.sqrt(max(0, radius ** 2 - dx ** 2 - dz ** 2)))
    placeFromFile("builds/processed/red_skull.csv", dx - 34, dy + build_height , dz - 33)
    wx, wz = dx, dz
    base_y = 5
    top_y = build_height + dy
    add_reactor_tower(wx, wz, top_y + 3, H=9, R0=3)
    #add_gold_pillars(wx, wz, top_y + 3, radius=90, pillar_height=20, count=6)

    # Build glass tube and water column
    for y in range(base_y, top_y + 2):
        for dx_ in [-1, 0, 1]:
            for dz_ in [-1, 0, 1]:
                if abs(dx_) == 1 or abs(dz_) == 1:
                    if dx_ == 0 or dz_ == 0:
                        editor.placeBlock((wx + dx_, y, wz + dz_), Block("glass"))
                    else:
                        editor.placeBlock((wx + dx_, y, wz + dz_), Block("sea_lantern"))
        editor.placeBlock((wx, y, wz), Block("water"))

    float_y = top_y + 36
    sign_x, sign_y, sign_z = wx, float_y + 1, wz
    editor.placeBlock((sign_x, float_y-1, sign_z), Block("sea_lantern"))
    sign = Block(
        "oak_sign",
        {"rotation": "0"},
        '{front_text: {messages: [\'{"text": "We shouldn’t "}\', \'{"text": "know what an AGI"}\', \'{"text": "looks like from"}\', \'{"text": "the inside!"}\']}}'
    )

    editor.placeBlock((sign_x, float_y, sign_z), sign)
    sign = Block(
        "oak_sign",
        {"rotation": "0"},
        '{front_text: {messages: [\'{"text": "Aren’t you"}\', \'{"text": "learning anything"}\', \'{"text": "from this"}\', \'{"text": "narrative?"}\']}}'
    )

    editor.placeBlock((sign_x, sign_y, sign_z), sign)


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
                        block_type = Block("sea_lantern")
                    elif core_array[x, z] and thickness >= 4 and t == thickness - 4:
                        block_type = Block("sculk_sensor")
                    elif core_array[x, z] and thickness >= 3 and t == thickness - 3:
                        block_type = Block("amethyst_block")
                    elif core_array[x, z] and thickness >= 2 and t == thickness - 2:
                        block_type = Block("sculk_sensor")
                    elif core_array[x, z] and thickness >= 1 and t == thickness - 1:
                        block_type = Block("sea_lantern")
                    else:
                        block_type = core_block if core_array[x, z] else outer_block

                    geometry.placeCuboid(editor, (wx, wy, wz), (wx, wy, wz), block_type)
    add_bubble_column(binary_array, build_height, radius)

def place_logo(x,y,z, choice_loc):
    # Run with pushTransform
    buildArea = editor.getBuildArea()
    editor.bufferLimit = 2048
    global choice
    choice = choice_loc
    # Replace function call accordingly
    with editor.pushTransform((buildArea.offset.x+x, y, buildArea.offset.z+z)):
        build_image_on_dome(
            image_path="gpt3.png",
            resize_to=(250, 250),
            build_height=-50,
            radius=200,
            thickness=5,
            line_thickness=5,
            min_neighbors_for_core=90
        )


if __name__ == "__main__":
    buildArea = editor.getBuildArea()
    place_logo(buildArea.offset.x,buildArea.offset.y,buildArea.offset.z)