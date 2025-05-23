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





def place_build(building):
    print(f"Placing {building['name']} in the world...")
    print(building)

    x_offset = building["top_left"][0]
    z_offset = building["top_left"][1]
    y_offset = heights[(x_offset, z_offset)]

    orientation = building["orientation"]
    height, width = building["size"]  # for correct in-place rotation

    placeFromFile(
        f"builds/processed/{building['name']}.csv",
        x_offset, y_offset, z_offset,
        orientation,
        width, height
    )


from find_buildings import *
from get_build_map import MapHolder

BUILDING_TYPES = [
    {"name": "barn", "size": (12, 14), "max": 3, "border": 6, "door_pos": (6, 1, 0)},
    {"name": "tent", "size": (4, 5), "max": 10, "border": 3, "door_pos": (1, 0, 0)},
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



