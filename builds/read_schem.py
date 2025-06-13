import nbtlib
import pandas as pd

for i in range(1):
    schem_name = f"collection"
    schem_path = f"raw/{schem_name}.schem"
    nbt = nbtlib.load(schem_path)
    schem = nbt["Schematic"]

    width = schem["Width"]
    height = schem["Height"]
    length = schem["Length"]

    blocks_compound = schem["Blocks"]
    palette = blocks_compound["Palette"]
    block_data = blocks_compound["Data"]

    index_to_block = [None] * len(palette)
    for block_name, tag in palette.items():
        index_to_block[tag] = block_name

    block_entries = []
    max_x = max_y = max_z = 0

    for y in range(height):
        for z in range(length):
            for x in range(width):
                index = y * length * width + z * width + x
                block_index = block_data[index]
                block_name = index_to_block[block_index]
                if block_name not in ["minecraft:air", "minecraft:grass_block[snowy=false]", "minecraft:dirt"]:
                    block_entries.append(((x, y, z), block_name))
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)
                    max_z = max(max_z, z)

    df = pd.DataFrame(block_entries, columns=["Position", "Block"])
    df.to_csv(f"processed/{schem_name}.csv", index=False)

    print(f"🏠 {schem_name}: Max X (width) = {max_x}, Max Y (height) = {max_y}, Max Z (depth) = {max_z}")
