from gdpc import Editor, Block, Transform, geometry

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

def placeFromFile(filename):
    print(f"Placing blocks from {filename}...")
    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # skip header
        for pos_str, block_str in reader:
            x, y, z = [int(v.strip()) for v in pos_str.strip("()").split(",")]
            name, props = parse_props(block_str.strip())
            print(f"Placing {name} at ({x}, {y}, {z}) with {props}")
            ED.placeBlock((x, y, z), Block(name, props))
    print("Done.")

def placeTent():
    placeFromFile("builds/processed/barn.csv")
buildArea = ED.getBuildArea()
with ED.pushTransform(buildArea.offset):
    print("Placing tent in the world...")
    ED.placeBlock((1,1,1), Block(f"spruce_stairs", {"facing": "east", "half": "top"}))
    placeTent()
    print("Tent has been placed in the world using ED.placeBlock.")


