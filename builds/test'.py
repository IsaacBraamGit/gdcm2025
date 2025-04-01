import nbtlib
import pandas as pd

# Load schematic
schem_path = "barn.schem"
nbt = nbtlib.load(schem_path)
schem = nbt["Schematic"]

width = schem["Width"]
height = schem["Height"]
length = schem["Length"]

blocks_compound = schem["Blocks"]
palette = blocks_compound["Palette"]
block_data = blocks_compound["Data"] # ByteArray

# Build index-to-block map
index_to_block = [None] * len(palette)
for block_name, tag in palette.items():
    index_to_block[tag] = block_name  # tag is Int

# Decode block layout
block_entries = []
for y in range(height):
    for z in range(length):
        for x in range(width):
            index = y * length * width + z * width + x
            block_index = block_data[index]
            block_name = index_to_block[block_index]
            if block_name != "minecraft:air":
                block_entries.append(((x, y, z), block_name))

# Save as CSV
df = pd.DataFrame(block_entries, columns=["Position", "Block"])
df.to_csv("schematic_blocks_final.csv", index=False)
print("✅ Block data extracted to schematic_blocks_final.csv")
