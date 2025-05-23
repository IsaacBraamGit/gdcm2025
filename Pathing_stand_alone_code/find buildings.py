from gdpc import Editor, Block, Transform, geometry

import find_buildings

ED = Editor(buffering=True)
# === Block Translator and Placement Generator ===

import csv


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

def placeFromFile(filename,x_offset,y_offset,z_offset):
    print(f"Placing blocks from {filename}...")
    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # skip header
        for pos_str, block_str in reader:
            x, y, z = [int(v.strip()) for v in pos_str.strip("()").split(",")]
            name, props = parse_props(block_str.strip())
            #print(f"Placing {name} at ({x}, {y}, {z}) with {props}")
            ED.placeBlock((x+x_offset, y+y_offset, z+z_offset), Block(name, props))
    print("Done.")

def placeTent(building):
    print(building)
    x_offset = building["top_left"][0]
    z_offset = building["top_left"][1]
    y_offset = heights[(x_offset, z_offset)]
    placeFromFile("builds/processed/barn.csv",x_offset,y_offset,z_offset)


from find_buildings import *
from get_build_map import MapHolder

BUILDING_TYPES = [
    {"name": "barn", "size": (8, 13), "max": 3, "border": 6, "door_pos":(7, 1, 12), "door_orientation": "N"},
    {"name": "tent", "size": (4, 5), "max": 40, "border": 3, "door_pos":(2, 0, 2),"door_orientation": "N"},
]

buildArea = ED.getBuildArea()
WORLDSLICE = ED.loadWorldSlice(buildArea.toRect(), cache=True)  # this takes a while
heights = WORLDSLICE.heightmaps["MOTION_BLOCKING_NO_LEAVES"]
build_map = MapHolder(ED, heights, 1.3)
build_map.find_flat_areas_and_trees(print_colors=False)
with ED.pushTransform((buildArea.offset.x,0,buildArea.offset.z)):
    print("Placing tent in the world...")
    build_spots = find_buildings.get_placements(build_map.block_slope_score, BUILDING_TYPES)
    for building in build_spots:
        placeTent(building)
    print("Tent has been placed in the world using ED.placeBlock.")


