from gdpc import Editor, Block, Transform, geometry

editor = Editor(buffering=True)

# Get a block
block = editor.getBlock((0, 48, 0))

# Place a block
editor.placeBlock((0, 80, 0), Block("stone"))

# Build a cube
geometry.placeCuboid(editor, (0, 80, 2), (2, 82, 4), Block("oak_planks"))

# Get the build area
buildArea = editor.getBuildArea()
print(buildArea.offset, buildArea.size)

# Place a more complex block (there are also helpers available!)
data = '{Items: [{Slot: 13b, id: "apple", Count: 1b}]}'
block = Block("chest", {"facing": "east"}, data)
editor.placeBlock((0, 80, 0), block)

# Use local coordinates
with editor.pushTransform(buildArea.offset):
    editor.placeBlock((10, 10, 10), Block("stone"))

    t = Transform(translation=(1, 2, 3), rotation=1, flip=(True, False, False))
    with editor.pushTransform(t):
        editor.placeBlock((10, 10, 10), Block("stone"))
