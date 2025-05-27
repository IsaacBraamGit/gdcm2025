#  /setbuildarea ~0 ~0 ~0 ~200 ~100 ~200
from gdpc import Editor, Block, Transform, geometry

import find_buildings

ED = Editor(buffering=True)
# === Block Translator and Placement Generator ===

import csv

def rotate_props(name, props, orientation):
    orientation = orientation % 4  # Normalize rotation to 0–3

    # === 1. Rotate 'facing' property ===
    if "facing" in props:
        facing = props["facing"]
        facing_order = ["north", "east", "south", "west"]
        if facing in facing_order:
            idx = facing_order.index(facing)
            # Rotate clockwise, then flip 180° if 90° or 270°
            rotated_idx = (idx + orientation) % 4
            if orientation in [1, 3]:
                rotated_idx = (rotated_idx + 2) % 4  # Apply 180° flip
            props["facing"] = facing_order[rotated_idx]

    # === 2. Rotate 'axis' property (e.g. logs) ===
    if "axis" in props:
        axis = props["axis"]
        if orientation % 2 == 1:  # At 90° or 270°, x ↔ z
            if axis == "x":
                props["axis"] = "z"
            elif axis == "z":
                props["axis"] = "x"

    # === 3. Rotate 'rotation' property (0–15 for signs/skulls) ===
    if "rotation" in props:
        try:
            val = int(props["rotation"])
            props["rotation"] = str((val + orientation * 4) % 16)
        except ValueError:
            pass  # Leave as-is if not an integer

    return props









def rotate_coords(x, z, orientation, width, height):
    if orientation == 0:
        return x, z
    elif orientation == 1:  # 90 degrees
        return z, width - 1 - x
    elif orientation == 2:  # 180 degrees
        return width - 1 - x, height - 1 - z
    elif orientation == 3:  # 270 degrees
        return height - 1 - z, x
    else:
        raise ValueError(f"Invalid orientation: {orientation}")


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

def placeFromFile(filename, x_offset, y_offset, z_offset, orientation, width, height):
    print(f"Placing blocks from {filename} with orientation {orientation}...")
    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # skip header
        for pos_str, block_str in reader:
            x, y, z = [int(v.strip()) for v in pos_str.strip("()").split(",")]
            x_rot, z_rot = rotate_coords(x, z, orientation, width, height)
            name, props = parse_props(block_str.strip())
            props = rotate_props(name, props, orientation)  # <<<<< rotate metadata
            ED.placeBlock((x_rot + x_offset, y + y_offset, z_rot + z_offset), Block(name, props))
    print("Done.")





from collections import Counter

def place_build(building):
    print(f"Placing {building['name']} in the world...")

    orig_height, orig_width = building["size"]
    orientation = building["orientation"]

    if orientation % 2 == 0:
        height, width = orig_height, orig_width
    else:
        height, width = orig_width, orig_height
    # for correct in-place rotation
    x_offset = building["top_left"][0]
    z_offset = building["top_left"][1]
    y_offset = heights[(x_offset+int(height/2), z_offset+int(width/2))] - 1
    orientation = building["orientation"]

    # === Step 1: Analyze the current ground blocks under the building ===
    block_counter = Counter()
    for dx in range(height):
        for dz in range(width):
            world_x = x_offset + dx
            world_z = z_offset + dz
            ground_y = heights[(world_x, world_z)] - 1
            block = WORLDSLICE.getBlock((world_x, ground_y, world_z))
            if block is not None:
                block_counter[block.id] += 1

    if not block_counter:
        most_common_block = "grass_block"
    else:
        most_common_block = block_counter.most_common(1)[0][0]

    # === Step 2: Clear the space ===
    for dx in range(height):
        for dz in range(width):
            for dy in range(30):  # remove up to 30 blocks tall
                ED.placeBlock((x_offset + dx, y_offset + dy, z_offset + dz), Block("air"))

    # === Step 3: Place platform ===
    for dx in range(height):
        for dz in range(width):
            ED.placeBlock((x_offset + dx, y_offset, z_offset + dz), Block(most_common_block))

    # === Step 4: Place the building on top ===
    placeFromFile(
        f"builds/processed/{building['name']}.csv",
        x_offset, y_offset + 1, z_offset,  # note the +1
        orientation,
        width, height
    )



from find_buildings import *
from get_build_map import MapHolder
# 🏠 fhouse1: Max X (width) = 30, Max Y (height) = 16, Max Z (depth) = 17
# 🏠 fhouse2: Max X (width) = 13, Max Y (height) = 17, Max Z (depth) = 17
# 🏠 fhouse3: Max X (width) = 13, Max Y (height) = 12, Max Z (depth) = 14
# 🏠 fhouse4: Max X (width) = 10, Max Y (height) = 23, Max Z (depth) = 18
# 🏠 fhouse5: Max X (width) = 18, Max Y (height) = 26, Max Z (depth) = 11
# 🏠 fhouse6: Max X (width) = 22, Max Y (height) = 10, Max Z (depth) = 16
# 🏠 fhouse7: Max X (width) = 10, Max Y (height) = 15, Max Z (depth) = 10
# 🏠 fhouse8: Max X (width) = 10, Max Y (height) = 8, Max Z (depth) = 8
# todo: door_pos
BUILDING_TYPES = [
    #{"name": "barn", "size": (12, 14), "max": 3, "border": 6, "door_pos": (6, 1, 0)},
    #{"name": "tent", "size": (4, 5), "max": 2, "border": 3, "door_pos": (1, 0, 0)},
    {'name': 'fhouse1', 'size': (30, 17), 'max': 3, 'border': 3, 'door_pos': (15, 0, 0)},
    {'name': 'fhouse2', 'size': (13, 17), 'max': 3, 'border': 2, 'door_pos': (6, 0, 0)},
    {'name': 'fhouse3', 'size': (13, 14), 'max': 3, 'border': 2, 'door_pos': (6, 0, 0)},
    {'name': 'fhouse4', 'size': (10, 18), 'max': 3, 'border': 2, 'door_pos': (5, 0, 0)},
    {'name': 'fhouse5', 'size': (18, 11), 'max': 3, 'border': 2, 'door_pos': (9, 0, 0)},
    {'name': 'fhouse6', 'size': (22, 16), 'max': 3, 'border': 3, 'door_pos': (11, 0, 0)},
    {'name': 'fhouse7', 'size': (10, 10), 'max': 3, 'border': 2, 'door_pos': (5, 0, 0)},
    {'name': 'fhouse8', 'size': (10, 8), 'max': 3, 'border': 1, 'door_pos': (5, 0, 0)},
]

buildArea = ED.getBuildArea()
WORLDSLICE = ED.loadWorldSlice(buildArea.toRect(), cache=True)  # this takes a while
heights = WORLDSLICE.heightmaps["MOTION_BLOCKING_NO_LEAVES"]
build_map = MapHolder(ED, heights, 1.3)
build_map.find_flat_areas_and_trees(print_colors=False)
with ED.pushTransform((buildArea.offset.x, 0, buildArea.offset.z)):
    build_spots = find_buildings.get_placements(build_map.block_slope_score, BUILDING_TYPES)
    for building in build_spots:
        print(building["orientation"])
        place_build(building)



