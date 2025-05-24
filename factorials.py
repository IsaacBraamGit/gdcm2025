import math
from gdpc import Editor, Block

editor = Editor(buffering=True)

PHI = (1 + 5 ** 0.5) / 2
Y_HEIGHT = 90
INNER_RADIUS = 20
OUTER_RADIUS = 100
PLATFORM_THICKNESS = 100
ARM_WIDTH = 4
NUM_ARMS = 3
CENTER = (0, 0)

def place_hollow_circle(center, radius, height, block):
    """Place a thin circle outline."""
    cx, cz = center
    steps = int(2 * math.pi * radius * 2)  # enough steps for a smooth circle
    for i in range(steps):
        angle = (i / steps) * 2 * math.pi
        x = int(cx + radius * math.cos(angle))
        z = int(cz + radius * math.sin(angle))
        editor.placeBlock((x, height, z), block)
        # Make it thick enough
        for dx in range(-ARM_WIDTH, ARM_WIDTH + 1):
            for dz in range(-ARM_WIDTH, ARM_WIDTH + 1):
                if dx**2 + dz**2 <= ARM_WIDTH**2:
                    editor.placeBlock((x + dx, height, z + dz), block)

def place_spiral_arms(center, inner_r, outer_r, num_arms, arm_width, height, block):
    """Create phi-spiral arms connecting inner and outer rings."""
    cx, cz = center
    for arm in range(num_arms):
        offset_angle = arm * (2 * math.pi / num_arms)
        for t in range(100):  # more = smoother curve
            ratio = t / 100
            r = inner_r + (outer_r - inner_r) * ratio
            angle = offset_angle + ratio * PHI * 6 * math.pi  # phi spiral twist

            x = int(cx + r * math.cos(angle))
            z = int(cz + r * math.sin(angle))

            for dx in range(-arm_width, arm_width + 1):
                for dz in range(-arm_width, arm_width + 1):
                    if dx**2 + dz**2 <= arm_width**2:
                        editor.placeBlock((x + dx, height, z + dz), block)

def build_spoked_phi_ring():
    block = Block("glowstone")
    place_hollow_circle(CENTER, INNER_RADIUS, Y_HEIGHT, block)
    place_hollow_circle(CENTER, OUTER_RADIUS, Y_HEIGHT, block)
    place_spiral_arms(CENTER, INNER_RADIUS, OUTER_RADIUS, NUM_ARMS, ARM_WIDTH, Y_HEIGHT, block)

build_spoked_phi_ring()
