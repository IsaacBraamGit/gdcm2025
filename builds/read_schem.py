import nbtlib
import pandas as pd
schem_name = "barn"
# Load schematic
schem_path = f"raw/{schem_name}.schem"
nbt = nbtlib.load(schem_path)
schem = nbt["Schematic"]

# Dimensions
width = schem["Width"]
height = schem["Height"]
length = schem["Length"]

# Go into "Blocks" compound
blocks_compound = schem["Blocks"]
palette = blocks_compound["Palette"]
block_data = blocks_compound["Data"]  # Already a list-like object

# Build index-to-block map
index_to_block = [None] * len(palette)
for block_name, tag in palette.items():
    index_to_block[tag] = block_name  # tag is an Int

# Decode block layout
block_entries = []
for y in range(height):
    for z in range(length):
        for x in range(width):
            index = y * length * width + z * width + x
            block_index = block_data[index]
            block_name = index_to_block[block_index]
            if block_name != "minecraft:air" and block_name != "minecraft:grass_block" and block_name != "minecraft:dirt":
                block_entries.append(((x, y, z), block_name))

# Save or view
df = pd.DataFrame(block_entries, columns=["Position", "Block"])
df.to_csv(f"processed/{schem_name}.csv", index=False)
print("✅ All non-air block data saved to schematic_blocks_final.csv")
