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

    if turn == 0:
        return {"size": (h, w), "door_pos": (door_x,0, door_y)}

    elif turn == 1:  # 90°
        new_size = (w, h)
        new_door_x = door_y
        new_door_y = h - 1 - door_x
        return {"size": new_size, "door_pos": (new_door_x,0, new_door_y)}

    elif turn == 2:  # 180°
        new_size = (h, w)
        new_door_x = h - 1 - door_x
        new_door_y = w - 1 - door_y
        return {"size": new_size, "door_pos": (new_door_x,0, new_door_y)}

    elif turn == 3:  # 270°
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


def get_placements(slope_map, building_types):
    rows, cols = slope_map.shape
    placement_map = np.zeros_like(slope_map)
    building_spots = []

    for building in sorted(building_types, key=lambda b: b["size"][0] * b["size"][1], reverse=True):
        max_count = building["max"]
        border = building["border"]
        placed = 0

        while placed < max_count:
            turn = random.randint(0, 3)
            rotated = rotate_building(building, turn)
            new_building = building.copy()
            new_building["size"] = rotated["size"]
            new_building["door_pos"]= rotated["door_pos"]
            h, w = new_building["size"]
            filterd_slope_building_map = get_avg_slope_map(slope_map, placement_map, h, w, border)

            i, j = find_min_idx(filterd_slope_building_map)

            if filterd_slope_building_map[i, j] > SLOPE_THRESHOLD:
                break
            place_building(i, j, h, w, border, placement_map, new_building)
            building_spots.append({
                "name": new_building["name"],
                "top_left": (i, j),
                "size": (h, w),
                "border": border,
                "building_type": new_building,
                "orientation": turn,
            })

            bi_start = max(i - border, 0)
            bi_end   = min(i + h + border, rows)
            bj_start = max(j - border, 0)
            bj_end   = min(j + w + border, cols)

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