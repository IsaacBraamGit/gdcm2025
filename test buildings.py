#  /setbuildarea ~0 ~0 ~0 ~256 ~100 ~256
from gdpc import Editor, Block, Transform, geometry
from logo import place_logo
import find_buildings
import csv
import numpy as np
from scipy.ndimage import gaussian_filter
from collections import Counter
from Water_sim import make_paths
import random

ED = Editor(buffering=True)


head = ["redstone", "coal", "lapis_lazuli", "emerald", "amethyst_shard"]

ore = [
    "redstone_ore", "coal_ore", "lapis_ore", "emerald_ore", "amethyst_cluster"
]

deep_ore = [
    "deepslate_redstone_ore", "deepslate_coal_ore", "deepslate_lapis_ore", "deepslate_emerald_ore", "amethyst_cluster"
]

#block = [
#    "redstone_block", "coal_block",
#    "lapis_block", "emerald_block", "amethyst_block"
#]

glass = [
    "red_stained_glass", "black_stained_glass",
    "blue_stained_glass", "green_stained_glass", "purple_stained_glass"
]

candle = [
    "red_candle", "black_candle","blue_candle","green_candle","purple_candle",
]
default = 0
choice = 4#random.randint(0, 4)

# === Block Translator and Placement Generator ===

def change_text_prop(line):
    if "wire" not in str(line) and "ore" not in str(line) and "block" not in str(line):
        line = [cell.replace(head[default], head[choice]) for cell in line]
    line = [cell.replace(ore[default], ore[choice]) for cell in line]
    line = [cell.replace(deep_ore[default], deep_ore[choice]) for cell in line]

    line = [cell.replace(glass[default], glass[choice]) for cell in line]

    return line


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
        header = next(reader)  # skip header
        for row in reader:
            if len(row) < 2:
                continue  # skip invalid lines

            ##dif blocks:
            row = change_text_prop(row)
            # === Parse position and rotate ===
            pos_str = row[0]
            block_str = row[1]
            inventory = ",".join(row[2:]) if len(row) > 2 else ""

            x, y, z = [int(v.strip()) for v in pos_str.strip("()").split(",")]
            x_rot, z_rot = rotate_coords(x, z, orientation, width, height)
            target_pos = (x_rot + x_offset, y + y_offset, z_rot + z_offset)

            if block_str.strip().lower() == "*villager":
                # === Spawn a Villager ===
                tx, ty, tz = buildArea.offset
                x0, y0, z0 = target_pos
                world_x, world_y, world_z = x0 + tx, y0 , z0 + tz
                cmd = f'summon villager {world_x} {world_y} {world_z}'
                print(f"Running command: {cmd}")
                ED.runCommand(cmd)
            else:
                # === Parse and rotate block ===
                name, props = parse_props(block_str.strip())
                props = rotate_props(name, props, orientation)

                # === Create block entity data for up to 9 items ===
                data = ""
                if inventory:
                    items_nbt = []
                    for slot, item in enumerate(inventory.split(",")):
                        if slot >= 9:
                            break  # Limit to 9 slots
                        item = item.strip()
                        if not item:
                            continue

                        if "*" in item:
                            item_id, count_str = item.split("*", 1)
                            item_id = item_id.strip()
                            try:
                                count = int(count_str.strip())
                            except ValueError:
                                count = 64
                        else:
                            item_id = item.strip()
                            count = 64  # default stack size

                        items_nbt.append(
                            f'{{Slot:{slot}b,id:"minecraft:{item_id}",count:{count}}}'
                        )

                    if items_nbt:
                        data = f'{{Items:[{",".join(items_nbt)}]}}'
                        print(f"Placing at {target_pos} with data: {data}")

                # === Place block ===
                ED.placeBlock(target_pos, Block(name, props, data))
    print("Done.")


from collections import Counter


def place_build(building):
    print(f"Placing {building['name']} in the world...")

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

    y_offset = avg_height - 1
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
    if most_common_block == "minecraft:dirt" or most_common_block_under == "minecraft:grass_block":
        most_common_block = "grass_block"
        most_common_block_under = "dirt"
    print(most_common_block_under)
    print(most_common_block)
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
    sigma = 1.8
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

            height_slice[local_x, local_z] = height + 1
            weight_slice[local_x, local_z] = weight

    # Apply Gaussian smoothing
    blurred_values = gaussian_filter(height_slice * weight_slice, sigma=sigma)
    blurred_weights = gaussian_filter(weight_slice, sigma=sigma)
    epsilon = 1e-6
    target_heights = np.round(blurred_values / (blurred_weights + epsilon)).astype(int)

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
            if current_y < target_y:
                for y in range(current_y + 1, target_y + 1):
                    for delta in [1, 2, 3]:
                        block_below = str(WORLDSLICE.getBlock((world_x, y - delta, world_z)).id) + str(
                            WORLDSLICE.getBlock((world_x, y - delta - 1, world_z)).id)
                        if block_below and "water" in block_below:
                            continue  # skip placing over water
                        block_to_place = most_common_block if delta == 1 else most_common_block_under
                        ED.placeBlock((world_x, y - delta, world_z), Block(block_to_place))
            # Lower terrain
            elif current_y > target_y:
                block_at_target = str(WORLDSLICE.getBlock((world_x, target_y - 1, world_z)).id) + str(
                    WORLDSLICE.getBlock((world_x, target_y - 2, world_z)).id)
                if not (block_at_target and "water" in block_at_target):
                    ED.placeBlock((world_x, target_y - 1, world_z), Block(most_common_block))
                for y in range(target_y + 1, current_y + 1):
                    ED.placeBlock((world_x, y - 1, world_z), Block("air"))

            if current_y == target_y:
                block_at_target = str(WORLDSLICE.getBlock((world_x, target_y - 1, world_z)).id) + str(
                    WORLDSLICE.getBlock((world_x, target_y - 2, world_z)).id)
                if not (block_at_target and "water" in block_at_target):
                    ED.placeBlock((world_x, target_y - 1, world_z), Block(most_common_block))

            # Update heightmap to new terrain
            heights[world_x, world_z] = target_y

    # Place the actual building on top
    placeFromFile(
        f"builds/processed/{building['name']}.csv",
        x_offset, y_offset + 1 + building['y_offset'], z_offset,
        orientation,
        orig_width, orig_height
    )
    return heights

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
    {'name': 'collection', 'size': (25, 25), 'max': 1, 'border': 5, 'door_pos': (13, 0, 0),'y_offset': -3},
    {'name': 'quarry2', 'size': (10, 10), 'max': 8, 'border': 5, 'door_pos': (9, 0, 9), 'y_offset': 0},
    {'name': 'fhouse1', 'size': (30, 17), 'max': 3, 'border': 5, 'door_pos': (15, 0, 0), 'y_offset': 0},
    {'name': 'fhouse2', 'size': (13, 17), 'max': 5, 'border': 5, 'door_pos': (6, 0, 0), 'y_offset': 0},
    {'name': 'fhouse3', 'size': (13, 14), 'max': 5, 'border': 5, 'door_pos': (6, 0, 0), 'y_offset': 0},
    {'name': 'fhouse4', 'size': (10, 18), 'max': 5, 'border': 4, 'door_pos': (5, 0, 0), 'y_offset': 0},
    {'name': 'fhouse5', 'size': (18, 11), 'max': 5, 'border': 4, 'door_pos': (9, 0, 0), 'y_offset': 0},
    {'name': 'fhouse6', 'size': (22, 16), 'max': 5, 'border': 5, 'door_pos': (11, 0, 0), 'y_offset': 0},
    {'name': 'fhouse7', 'size': (10, 10), 'max': 5, 'border': 4, 'door_pos': (5, 0, 0), 'y_offset': 0},
    {'name': 'fhouse8', 'size': (10, 8), 'max': 5, 'border': 3, 'door_pos': (5, 0, 0), 'y_offset': 0},
]

buildArea = ED.getBuildArea()
WORLDSLICE = ED.loadWorldSlice(buildArea.toRect(), cache=True)  # this takes a while
heights = WORLDSLICE.heightmaps["MOTION_BLOCKING_NO_LEAVES"]
build_map = MapHolder(ED, heights, 1.3)
build_map.find_flat_areas_and_trees(print_colors=False)
with ED.pushTransform((buildArea.offset.x, 0, buildArea.offset.z)):
    build_spots, placement_map, crop_offset = find_buildings.get_placements(build_map.block_slope_score, BUILDING_TYPES, heights)
    for building in build_spots:
        print(building["orientation"])
        heights = place_build(building)

    from scipy.ndimage import gaussian_filter
    import numpy as np
    import random

    path_tiles = set()  # Global set of all (x, z) that become path

    # Define path materials and decorations
    path_blocks = ["dirt_path"]
    decorations = ["oak_leaves[persistent=true]", "oak_fence"]

    with open("immutable_block_base_types.csv", newline="") as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        IMMUTABLE_BLOCKS = set(row[0] for row in reader)

    # Expand placement_map back to original map size
    full_map = np.zeros_like(build_map.block_slope_score)
    i0, j0 = crop_offset
    h, w = placement_map.shape
    full_map[i0:i0 + h, j0:j0 + w] = placement_map

    # Run path generation using full-size map
    final_paths = make_paths(build_map.block_slope_score, full_map, build_map.water_mask)

    path_columns = set()  # All (x, z) columns used by path
    light_post_positions = []  # List of placed light posts
    MIN_LIGHT_SPACING = 8  # Minimum spacing between lamp posts


    # --- Helper: Check light post spacing ---
    def too_close_to_other_posts(x, z):
        for px, pz in light_post_positions:
            if abs(px - x) + abs(pz - z) < MIN_LIGHT_SPACING:
                return True
        return False


    # --- Helper: Build a full street lamp post ---
    def build_light_post(x, y, z):
        structure = [
            (x, y, z, "stone_bricks"),
            (x, y + 1, z, "stone_brick_wall"),
            (x, y + 2, z, "stone_brick_wall"),
            (x, y + 3, z, "stone_bricks"),
            (x - 1, y + 3, z, "stone_brick_stairs[facing=east,half=bottom]"),
            (x + 1, y + 3, z, "stone_brick_stairs[facing=west,half=bottom]"),
            (x, y + 3, z - 1, "stone_brick_stairs[facing=south,half=bottom]"),
            (x, y + 3, z + 1, "stone_brick_stairs[facing=north,half=bottom]"),
            (x - 1, y + 2, z, "lantern[hanging=true]"),
            (x + 1, y + 2, z, "lantern[hanging=true]"),
            (x, y + 2, z - 1, "lantern[hanging=true]"),
            (x, y + 2, z + 1, "lantern[hanging=true]"),
        ]
        if (x, z) not in path_columns:
            for bx, by, bz, block_type in structure:
                ED.placeBlock((bx, by, bz), Block(block_type))
        light_post_positions.append((x, z))


   # --- PRE-PROCESS: Smooth terrain for 3x3 path tiles using Gaussian filter ---

    # Create mask and height map for smoothed 3x3 path area
    path_mask = np.zeros_like(final_paths, dtype=float)
    path_heightmap = np.zeros_like(heights, dtype=float)

    for x in range(final_paths.shape[0]):
        for z in range(final_paths.shape[1]):
            if final_paths[x, z] == 1 or full_map[x,z] == 1:
                for dx in range(-1, 2):
                    for dz in range(-1, 2):
                        nx, nz = x + dx, z + dz
                        if 0 <= nx < final_paths.shape[0] and 0 <= nz < final_paths.shape[1]:
                            path_mask[nx, nz] = 1
                            path_heightmap[nx, nz] = heights[nx, nz]

    # Apply Gaussian blur
    sigma = 3  # Adjust for smoothing level
    blurred_heights = gaussian_filter(path_heightmap, sigma=sigma)
    blurred_mask = gaussian_filter(path_mask, sigma=sigma)

    # Normalize and update only the relevant (3x3-expanded) path tiles
    for x in range(final_paths.shape[0]):
        for z in range(final_paths.shape[1]):
            if path_mask[x, z] > 0:
                heights[x, z] = int(round(blurred_heights[x, z] / (blurred_mask[x, z] + 1e-6)))

    # Precompute constants
    dxz_range = (-1, 0, 1)
    air_block = Block("air")
    path_blocks_choices = path_blocks  # assumes path_blocks is a list
    rand_choice = random.choice
    shape_x, shape_z = final_paths.shape

    # Local references
    get_block = ED.getBlock
    place_block = ED.placeBlock
    immutable = IMMUTABLE_BLOCKS

    # --- Optimized Step 1: Build 3x3 paths and track path columns ---
    for x in range(shape_x):
        for z in range(shape_z):
            if final_paths[x, z] != 1:
                continue

            for dx in dxz_range:
                for dz in dxz_range:
                    nx, nz = x + dx, z + dz
                    if not (0 <= nx < shape_x and 0 <= nz < shape_z):
                        continue

                    ny = heights[nx, nz] - 1
                    skip = False

                    # Check for immutable blocks
                    for dy in range(6):
                        block_id = get_block((nx, ny + dy, nz)).id.split("[", 1)[0]
                        if block_id in immutable:
                            skip = True
                            break

                    if skip:
                        continue

                    # Clear space above
                    for dy in (1, 2, 3, 4, 5):
                        place_block((nx, ny + dy, nz), air_block)

                    # Place path block
                    place_block((nx, ny, nz), Block(rand_choice(path_blocks_choices)))
                    path_columns.add((nx, nz))

    # --- Step 1.5: Add slabs where path height difference is 1 ---
    for x, z in path_columns:
        current_y = heights[x, z]

        for dx, dz in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, nz = x + dx, z + dz
            if (nx, nz) in path_columns:
                neighbor_y = heights[nx, nz]
                height_diff = current_y - neighbor_y

                if height_diff == 1:
                    # Current is higher — place slab at neighbor (lower)
                    ED.placeBlock((nx, neighbor_y, nz), Block("oak_slab[type=bottom]"))
                elif height_diff == -1:
                    # Neighbor is higher — place slab at current (lower)
                    ED.placeBlock((x, current_y, z), Block("oak_slab[type=bottom]"))

    # --- Step 2: Decorate around the path ---
    for x in range(final_paths.shape[0]):
        for z in range(final_paths.shape[1]):
            if final_paths[x, z] == 1:
                for dx in range(-2, 3):
                    for dz in range(-2, 3):
                        nx, nz = x + dx, z + dz
                        if 0 <= nx < heights.shape[0] and 0 <= nz < heights.shape[1]:
                            ny = heights[nx, nz]
                        else:
                            # Handle out-of-bounds case
                            continue
                        ny = heights[nx, nz]
                        # Skip if outside bounds or inside path
                        if not (0 <= nx < final_paths.shape[0] and 0 <= nz < final_paths.shape[1]):
                            continue
                        if (nx, nz) in path_columns:
                            continue

                        should_skip = False
                        for dy in range(0, 6):  # Check from base (ny) to ny+5
                            existing_block = ED.getBlock((nx, ny + dy, nz)).id.split("[")[0]
                            if existing_block in IMMUTABLE_BLOCKS:
                                should_skip = True
                                break  # stop checking this column

                        if should_skip:
                            continue


                        ny = heights[nx, nz]

                        # Decoration on ground
                        if ED.getBlock((nx, ny, nz)) == Block("minecraft:air") and random.random() < 0.25:
                            deco = random.choice(decorations)
                            ED.placeBlock((nx, ny, nz), Block(deco))

                        # Overhead decoration
                        if ED.getBlock((nx, ny + 1, nz)) == Block("minecraft:air") and random.random() < 0.15:
                            over = random.choice(["oak_leaves[persistent=true]"])
                            ED.placeBlock((nx, ny + 1, nz), Block(over))

                        # Street lamp — sparse and spaced
                        if (
                            random.random() < 0.03
                            and not too_close_to_other_posts(nx, nz)
                            and full_map[nx, nz] == 0  # ⛔ not on a building tile
                        ):
                            build_light_post(nx, ny, nz)


x = build_spots[0]["top_left"][0] + int(build_spots[0]["size"][0] / 2) + 1
z = build_spots[0]["top_left"][1] + int(build_spots[0]["size"][1] / 2) + 1
y = heights[x, z]


place_logo(x,y,z, choice)
