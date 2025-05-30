import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.ndimage import convolve
import random


SLOPE_THRESHOLD = 1  # Maximum average slope allowed
CLAIM_SCORE = 10     # Value used to fill in claimed building spots
BLOCKED_SCORE = 5    # Value used to mark border zones
DOOR_SCORE = 15


def find_min_idx( x):
    k = x.argmin()
    ncol = x.shape[1]
    return int(k / ncol), int(k % ncol)
import numpy as np

def get_downhill_sides(heights, i, j, h, w, distance=6):
    max_i, max_j = heights.shape

    if i - distance >= 0:
        north_edge = heights[i, j:j+w]
        north_comp = heights[i - distance, j:j+w]
        north = (north_edge - north_comp).mean() / distance
    else:
        north = 0

    if i + h - 1 + distance < max_i:
        south_edge = heights[i + h - 1, j:j+w]
        south_comp = heights[i + h - 1 + distance, j:j+w]
        south = (south_edge - south_comp).mean() / distance
    else:
        south = 0

    if j - distance >= 0:
        west_edge = heights[i:i+h, j]
        west_comp = heights[i:i+h, j - distance]
        west = (west_edge - west_comp).mean() / distance
    else:
        west = 0

    if j + w - 1 + distance < max_j:
        east_edge = heights[i:i+h, j + w - 1]
        east_comp = heights[i:i+h, j + w - 1 + distance]
        east = (east_edge - east_comp).mean() / distance
    else:
        east = 0

    return [north, east, south, west]

def get_direction_to_center(i, j, h, w, rows, cols, axis_swap=True):
    """
    Returns orientation (0=N, 1=E, 2=S, 3=W) to face the center,
    with optional axis swap for Minecraft/plot rotation.
    axis_swap: if True, swaps axes to match Minecraft's X/Z orientation.
    """
    # Building center
    ci = i + h / 2
    cj = j + w / 2
    # Map center
    mi = rows / 2
    mj = cols / 2

    if axis_swap:
        # Swap i (row) <-> Z and j (col) <-> X for Minecraft
        cX, cZ = cj, ci
        mX, mZ = mj, mi
    else:
        cX, cZ = ci, cj
        mX, mZ = mi, mj

    # Vector from building to map center
    dX = mX - cX
    dZ = mZ - cZ

    # Find cardinal direction (Minecraft: 0=N, 1=E, 2=S, 3=W)
    if abs(dX) > abs(dZ):
        # East or West
        if dX > 0:
            orientation = 0  # East
        else:
            orientation = 2  # West
    else:
        # North or South
        if dZ > 0:
            orientation = 1  # South
        else:
            orientation = 3  # North
    return orientation



def place_building(i, j, h, w, border, placement_map, building):
    rows, cols = placement_map.shape
    door_pos = building["door_pos"]
    # Mark building area
    placement_map[i:i+h, j:j+w] = CLAIM_SCORE
    placement_map[i+door_pos[0], j+door_pos[2]] = DOOR_SCORE
    # Mark border area as unavailable (BLOCKED_SCORE)
    bi_start = max(i - border, 0)
    bi_end   = min(i + h + border, rows)
    bj_start = max(j - border, 0)
    bj_end   = min(j + w + border, cols)

    for bi in range(bi_start, bi_end):
        for bj in range(bj_start, bj_end):
            if placement_map[bi, bj] == 0:
                placement_map[bi, bj] = BLOCKED_SCORE

def get_avg_slope_map(slope_map, placement_map, h, w, border):
    slope_map = np.array(slope_map, dtype=float)
    placement_map = np.array(placement_map, dtype=float)
    rows, cols = slope_map.shape

    # Step 1: Basic finite slope + free placement mask
    valid_mask = (np.isfinite(slope_map) & (placement_map == 0)).astype(float)
    slope_valid = np.nan_to_num(slope_map, nan=0.0, posinf=0.0, neginf=0.0)

    kernel = np.ones((h, w), dtype=float)
    sum_slope = convolve(slope_valid, kernel, mode='constant', cval=0.0)
    count_valid = convolve(valid_mask, kernel, mode='constant', cval=0.0)

    avg_slope = sum_slope / count_valid + 0.001
    avg_slope[count_valid < h * w] = np.inf

    # Step 2: Invalidate placements where the full (building + border) region is not clear
    border_mask = (placement_map > 0).astype(float)
    border_kernel = np.ones((h + 2 * border, w + 2 * border))
    border_hits = convolve(border_mask, border_kernel, mode='constant', cval=1.0)

    # Crop avg_slope to valid placement range
    cropped = avg_slope[h-1:rows, w-1:cols]
    border_hits_cropped = border_hits[border:rows - h - border + 1, border:cols - w - border + 1]

    # Ensure alignment
    if cropped.shape != border_hits_cropped.shape:
        min_rows = min(cropped.shape[0], border_hits_cropped.shape[0])
        min_cols = min(cropped.shape[1], border_hits_cropped.shape[1])
        cropped = cropped[:min_rows, :min_cols]
        border_hits_cropped = border_hits_cropped[:min_rows, :min_cols]

    cropped[border_hits_cropped > 0] = np.inf

    return cropped

def rotate_building(building, turn):
    h, w = building["size"]
    door_x, door_z, door_y = building["door_pos"]

    if turn == 2:
        return {"size": (h, w), "door_pos": (door_x,0, door_y)}

    elif turn == 3:  # 90°
        new_size = (w, h)
        new_door_x = door_y
        new_door_y = h - 1 - door_x
        return {"size": new_size, "door_pos": (new_door_x,0, new_door_y)}

    elif turn == 0:  # 180°
        new_size = (h, w)
        new_door_x = h - 1 - door_x
        new_door_y = w - 1 - door_y
        return {"size": new_size, "door_pos": (new_door_x,0, new_door_y)}

    elif turn == 1:  # 270°
        new_size = (w, h)
        new_door_x = w - 1 - door_y
        new_door_y = door_x
        return {"size": new_size, "door_pos": (new_door_x,0, new_door_y)}
    return None


def plot_placement(placement_map):
    """Plot the building placement map rotated 90° counter-clockwise with inverted Y-axis."""
    # Rotate the matrix 90 degrees counter-clockwise
    rotated_map = np.rot90(np.rot90(np.rot90(placement_map)))

    plt.figure(figsize=(12, 8))
    ax = sns.heatmap(rotated_map, cmap="coolwarm", cbar=False, square=True,
                     xticklabels=False, yticklabels=False)
    ax.invert_yaxis()  # Invert the Y-axis
    plt.title("Building Placement (Rotated 90° CCW & Y-Inverted)")
    plt.axis('off')
    plt.show()

def get_side_slopes(slope_map, i, j, h, w):
    """
    Returns the average slope of each side (N, E, S, W) for a building at (i, j) with size (h, w).
    - North: top edge
    - East: right edge
    - South: bottom edge
    - West: left edge
    """
    # Prevent out-of-bounds
    north = slope_map[i, j:j+w].mean() if i >= 0 and i < slope_map.shape[0] else np.inf
    south = slope_map[i+h-1, j:j+w].mean() if (i+h-1) < slope_map.shape[0] else np.inf
    west  = slope_map[i:i+h, j].mean() if j >= 0 and j < slope_map.shape[1] else np.inf
    east  = slope_map[i:i+h, j+w-1].mean() if (j+w-1) < slope_map.shape[1] else np.inf
    return [north, east, south, west]


def get_placements(slope_map, building_types, heights, downhill_distance=6, downhill_thresh=2.0):
    rows, cols = slope_map.shape
    placement_map = np.zeros_like(slope_map)
    building_spots = []

    for building in sorted(building_types, key=lambda b: b["size"][0] * b["size"][1], reverse=True):
        max_count = building["max"]
        border = building["border"]
        placed = 0

        while placed < max_count:
            h, w = building["size"]
            filterd_slope_building_map = get_avg_slope_map(slope_map, placement_map, h, w, border)
            i, j = find_min_idx(filterd_slope_building_map)
            if filterd_slope_building_map[i, j] > SLOPE_THRESHOLD:
                break

            downhill = get_downhill_sides(heights, i, j, h, w, distance=downhill_distance)
            # Use the most negative value (steepest downhill)
            steepest = np.min(downhill)
            # Also get the absolute value for all sides
            flat_enough = np.all(np.abs(downhill) <= downhill_thresh)
            flat_enough = True
            if flat_enough:
                # All directions are fairly flat, face center
                orientation = get_direction_to_center(i, j, h, w, rows, cols)
            else:
                # Face north toward steepest downhill
                orientation = int(np.argmin(downhill))

            rotated = rotate_building(building, orientation)
            new_building = building.copy()
            new_building["size"] = rotated["size"]
            new_building["door_pos"] = rotated["door_pos"]
            h_new, w_new = new_building["size"]

            place_building(i, j, h_new, w_new, border, placement_map, new_building)
            building_spots.append({
                "name": new_building["name"],
                "top_left": (i, j),
                "size": (h_new, w_new),
                "border": border,
                "building_type": new_building,
                "orientation": orientation,
            })

            bi_start = max(i - border, 0)
            bi_end   = min(i + h_new + border, rows)
            bj_start = max(j - border, 0)
            bj_end   = min(j + w_new + border, cols)
            slope_map[bi_start:bi_end, bj_start:bj_end] = np.inf

            placed += 1

    plot_placement(placement_map)
    return building_spots



if __name__ == "__main__":
    BUILDING_TYPES = [
    #{"name": "barn", "size": (12, 14), "max": 3, "border": 6, "door_pos": (6, 1, 0)},
    #{"name": "tent", "size": (4, 5), "max": 2, "border": 3, "door_pos": (1, 0, 0)},
    {'name': 'fhouse1', 'size': (30, 17), 'max': 3, 'border': 3, 'door_pos': (15, 0, 0)},
    {'name': 'fhouse2', 'size': (13, 17), 'max': 3, 'border': 2, 'door_pos': (6, 0, 0)},
    {'name': 'fhouse3', 'size': (13, 14), 'max': 3, 'border': 2, 'door_pos': (6, 0, 0)},
    {'name': 'fhouse4', 'size': (10, 18), 'max': 3, 'border': 2, 'door_pos': (5, 0, 0)},
    {'name': 'fhouse5', 'size': (18, 11), 'max': 3, 'border': 2, 'door_pos': (9, 0, 0)},
    {'name': 'fhouse6', 'size': (22, 16), 'max': 3, 'border': 3, 'door_pos': (11, 0, 0)},
    {'name': 'fhouse7', 'size': (10, 10), 'max': 3, 'border': 2, 'door_pos': (5, 0, 0)},
    {'name': 'fhouse8', 'size': (10, 8), 'max': 3, 'border': 1, 'door_pos': (5, 0, 0)},
]

    with open("slope.txt", "r") as f:
        data = [list(map(float, line.strip().split())) for line in f]
    slope_map = np.array(data)

    building_spots = get_placements(slope_map, BUILDING_TYPES)
    print(building_spots)