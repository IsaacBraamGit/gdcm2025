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
        return height - 1 - x, width - 1 - z
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

    import numpy as np
    from scipy.ndimage import gaussian_filter
    from collections import Counter

    orig_height, orig_width = building["size"]
    orientation = building["orientation"]

    # Compute rotated bounding box in world coordinates
    rotated_coords = [rotate_coords(x, z, orientation, orig_width, orig_height)
                      for x in range(orig_height)
                      for z in range(orig_width)]
    rotated_x = [x for x, _ in rotated_coords]
    rotated_z = [z for _, z in rotated_coords]
    min_dx, max_dx = min(rotated_x), max(rotated_x)
    min_dz, max_dz = min(rotated_z), max(rotated_z)

    x_offset = building["top_left"][0]
    z_offset = building["top_left"][1]

    # Average terrain height under the footprint
    avg_height = sum(
        heights[(x_offset + dx, z_offset + dz)]
        for dx in range(min_dx, max_dx + 1)
        for dz in range(min_dz, max_dz + 1)
    ) // ((max_dx - min_dx + 1) * (max_dz - min_dz + 1))

    y_offset = avg_height - 2
    platform_y = y_offset + 1  # Height at which platform will be placed

    # Determine most common ground block
    block_counter = Counter()
    for dx in range(min_dx, max_dx + 1):
        for dz in range(min_dz, max_dz + 1):
            world_x = x_offset + dx
            world_z = z_offset + dz
            ground_y = heights[(world_x, world_z)] - 1
            block = WORLDSLICE.getBlock((world_x, ground_y, world_z))
            if block:
                block_counter[block.id] += 1

    most_common_block = block_counter.most_common(1)[0][0] if block_counter else "grass_block"
    most_common_block_under = most_common_block
    if most_common_block == "dirt":
        most_common_block = "grass_block"
        most_common_block_under = "dirt"

    # Clear and place foundation
    for dx in range(orig_height):
        for dz in range(orig_width):
            world_x = x_offset + dx
            world_z = z_offset + dz
            # Clear above
            for dy in range(15):
                ED.placeBlock((world_x, y_offset + 1 + dy, world_z), Block("air"))
            # Place foundation
            for down in range(0, -4, -1):
                ED.placeBlock((world_x, y_offset + 1 + down, world_z), Block(most_common_block))

    # --- SMOOTHING LOGIC ---
    smoothing_radius = 6
    sigma = 1.0
    platform_weight = 10.0

    # Area bounds for smoothing
    min_x = max(x_offset - smoothing_radius, 0)
    max_x = min(x_offset + orig_height + smoothing_radius, heights.shape[0] - 1)
    min_z = max(z_offset - smoothing_radius, 0)
    max_z = min(z_offset + orig_width + smoothing_radius, heights.shape[1] - 1)

    height_slice = heights[min_x:max_x + 1, min_z:max_z + 1].copy().astype(float)
    weight_slice = np.ones_like(height_slice)

    # Inject platform and halo into smoothing map
    for dx in range(-2, orig_height + 2):
        for dz in range(-2, orig_width + 2):
            world_x = x_offset + dx
            world_z = z_offset + dz
            local_x = world_x - min_x
            local_z = world_z - min_z

            if not (0 <= local_x < height_slice.shape[0] and 0 <= local_z < height_slice.shape[1]):
                continue

            distance_from_platform = max(
                max(0, -dx),
                max(0, dx - (orig_height - 1)),
                max(0, -dz),
                max(0, dz - (orig_width - 1)),
            )

            if distance_from_platform == 0:
                weight = platform_weight
                height = platform_y
            elif distance_from_platform <= 2:
                falloff = 1.0 - (distance_from_platform / 3.0)
                weight = platform_weight * falloff
                height = platform_y  # Keep same height, lower influence
            else:
                continue

            height_slice[local_x, local_z] = height
            weight_slice[local_x, local_z] = weight

    # Apply Gaussian smoothing
    blurred_values = gaussian_filter(height_slice * weight_slice, sigma=sigma)
    blurred_weights = gaussian_filter(weight_slice, sigma=sigma)
    epsilon = 1e-6
    target_heights = np.floor(blurred_values / (blurred_weights + epsilon)).astype(int)

    # Reassert platform height after smoothing
    for dx in range(orig_height):
        for dz in range(orig_width):
            world_x = x_offset + dx
            world_z = z_offset + dz
            local_x = world_x - min_x
            local_z = world_z - min_z
            if 0 <= local_x < target_heights.shape[0] and 0 <= local_z < target_heights.shape[1]:
                target_heights[local_x, local_z] = platform_y

    # Apply smoothed terrain outside platform
    for local_x in range(target_heights.shape[0]):
        for local_z in range(target_heights.shape[1]):
            world_x = min_x + local_x
            world_z = min_z + local_z

            # Skip platform itself
            if x_offset <= world_x < x_offset + orig_height and z_offset <= world_z < z_offset + orig_width:
                continue

            try:
                current_y = heights[world_x, world_z]
                target_y = target_heights[local_x, local_z]
            except IndexError:
                continue

            # Raise terrain
            if current_y <= target_y:
                ED.placeBlock((world_x, target_y, world_z), Block(most_common_block))
                for y in range(current_y + 1, target_y + 1):
                    ED.placeBlock((world_x, y, world_z), Block(most_common_block))
                    ED.placeBlock((world_x, y-1, world_z), Block("blue_concrete"))
                    ED.placeBlock((world_x, y-2, world_z), Block("blue_concrete"))
            # Lower terrain
            elif current_y > target_y:
                ED.placeBlock((world_x, target_y, world_z), Block(most_common_block))
                for y in range(target_y + 1, current_y + 1):

                    ED.placeBlock((world_x, y, world_z), Block("air"))


            # Update heightmap to new terrain
            heights[world_x, world_z] = target_y

    # 5x5 neighborhood smoothing with 55% threshold
    for local_x in range(2, target_heights.shape[0] - 2):
        for local_z in range(2, target_heights.shape[1] - 2):
            world_x = min_x + local_x
            world_z = min_z + local_z
            current_y = heights[world_x, world_z]

            # Get 5x5 neighborhood excluding center
            neighborhood = [
                heights[world_x + dx, world_z + dz]
                for dx in [-2, -1, 0, 1, 2]
                for dz in [-2, -1, 0, 1, 2]
                if not (dx == 0 and dz == 0)
            ]

            height_counts = Counter(neighborhood)
            mode_height, count = height_counts.most_common(1)[0]

            if count >= 14 and abs(current_y - mode_height) >= 2:
                # Apply correction
                if current_y < mode_height:
                    for y in range(current_y + 1, mode_height + 1):
                        ED.placeBlock((world_x, y, world_z), Block(most_common_block))
                else:
                    for y in range(mode_height + 1, current_y + 1):
                        ED.placeBlock((world_x, y, world_z), Block("air"))
                    ED.placeBlock((world_x, mode_height, world_z), Block(most_common_block))

                heights[world_x, world_z] = mode_height
    # Place the actual building on top
    placeFromFile(
        f"builds/processed/{building['name']}.csv",
        x_offset, y_offset + 1, z_offset,
        orientation,
        orig_width, orig_height
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
     {'name': 'fhouse1', 'size': (30, 17), 'max': 3, 'border': 5, 'door_pos': (15, 0, 0)},
     {'name': 'fhouse2', 'size': (13, 17), 'max': 3, 'border': 5, 'door_pos': (6, 0, 0)},
     {'name': 'fhouse3', 'size': (13, 14), 'max': 3, 'border': 5, 'door_pos': (6, 0, 0)},
     {'name': 'fhouse4', 'size': (10, 18), 'max': 3, 'border': 4, 'door_pos': (5, 0, 0)},
     {'name': 'fhouse5', 'size': (18, 11), 'max': 3, 'border': 4, 'door_pos': (9, 0, 0)},
     {'name': 'fhouse6', 'size': (22, 16), 'max': 3, 'border': 5, 'door_pos': (11, 0, 0)},
     {'name': 'fhouse7', 'size': (10, 10), 'max': 3, 'border': 4, 'door_pos': (5, 0, 0)},
     {'name': 'fhouse8', 'size': (10, 8), 'max': 3, 'border': 3, 'door_pos': (5, 0, 0)},
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



