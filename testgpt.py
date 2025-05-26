from gdpc import Editor, Block, Transform, geometry
import math

editor = Editor(buffering=True)
buildArea = editor.getBuildArea()

with editor.pushTransform(buildArea.offset):
    center_x, center_y, center_z = 40, 40, 40  # Big central coordinates

    # === Build the AI Core ===
    def build_core(cx, cy, cz, size):
        geometry.placeCuboid(editor,
            (cx - size, cy - size, cz - size),
            (cx + size, cy + size, cz + size),
            Block("obsidian"))

        geometry.placeCuboid(editor,
            (cx - size + 1, cy - size + 1, cz - size + 1),
            (cx + size - 1, cy + size - 1, cz + size - 1),
            Block("glass"))

        editor.placeBlock((cx, cy, cz), Block("redstone_block"))

    build_core(center_x, center_y, center_z, size=5)

    # === Water Elevator ===
    def build_water_elevator(cx, cy, cz, height):
        for y in range(cy - height, cy):
            editor.placeBlock((cx, y, cz), Block("water"))
        editor.placeBlock((cx, cy - height, cz), Block("soul_sand"))

    build_water_elevator(center_x, center_y, center_z, height=30)

    # === Tentacle Function ===
    def build_tentacle(cx, cy, cz, length, angle_offset):
        for i in range(length):
            theta = i / 4 + angle_offset
            x = int(cx + math.cos(theta) * (i / 3))
            z = int(cz + math.sin(theta) * (i / 3))
            y = cy - i // 2
            editor.placeBlock((x, y, z), Block("blackstone_wall"))

    # === Deploy Multiple Tentacles ===
    for a in range(0, 360, 45):
        radians = math.radians(a)
        build_tentacle(center_x, center_y, center_z, length=30, angle_offset=radians)

    # === Glowing aura blocks ===
    aura_offsets = [
        (-6, 6, -6), (6, 6, -6), (-6, 6, 6), (6, 6, 6)
    ]
    for ox, oy, oz in aura_offsets:
        editor.placeBlock((center_x + ox, center_y + oy, center_z + oz), Block("soul_fire"))

editor.flushBuffer()
