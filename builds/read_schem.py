import nbtlib
import pandas as pd

# Load classic schematic
schem_path = "barn.schem"
nbt = nbtlib.load(schem_path)
schem = nbt["Schematic"]

# Dimensions
width = schem["Width"]
height = schem["Height"]
length = schem["Length"]

# Raw block ID and metadata arrays
blocks = schem["Blocks"].values  # ByteArray
data = schem["Data"].value      # ByteArray

# Decode block layout
block_entries = []
for y in range(height):
    for z in range(length):
        for x in range(width):
            index = y * length * width + z * width + x
            block_id = blocks[index]
            block_meta = data[index]
            if block_id != 0:  # 0 = air in classic format
                block_entries.append(((x, y, z), block_id, block_meta))

# Turn into a DataFrame
df = pd.DataFrame(block_entries, columns=["Position", "BlockID", "Metadata"])
df.to_csv("schematic_blocks_classic.csv", index=False)
print("✅ Saved classic-format block data to schematic_blocks_classic.csv")
