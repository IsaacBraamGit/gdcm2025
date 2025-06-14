import random
import time
import heapq

import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import gaussian_filter

HOUSE_AVOID_MULT = 4
SLOPE_AVOID_MULT = 0.2
NUM_paths = 2
Iterations = 30


def plot_iteration(map_base, paths, iteration):
    mapcopy = map_base.copy()
    rows, cols = mapcopy.shape

    for path in paths:
        for r, c in path:
            if 0 <= r < rows and 0 <= c < cols:
                mapcopy[r, c] = 3  # Mark path with 3

    plt.figure(figsize=(6, 6))
    plt.imshow(mapcopy, cmap="hot", interpolation="nearest")
    plt.title(f"Iteration {iteration}")
    plt.xlabel("Column")
    plt.ylabel("Row")
    plt.colorbar(label="Value")
    plt.tight_layout()
    plt.pause(0.1)
    plt.clf()


def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def a_star(start, goal, map_data, watermask=None):
    rows, cols = map_data.shape
    open_set = []
    heapq.heappush(open_set, (heuristic(start, goal), 0, start, [start]))

    visited = set()

    while open_set:
        est_total, curr_cost, current, path = heapq.heappop(open_set)

        if current == goal:
            return path, curr_cost

        if current in visited:
            continue
        visited.add(current)

        r, c = current
        neighbors = [
            (r + dr, c + dc)
            for dr in [-1, 0, 1]
            for dc in [-1, 0, 1]
            if not (dr == 0 and dc == 0)
        ]

        for nr, nc in neighbors:
            if 0 <= nr < rows and 0 <= nc < cols:
                if map_data[nr, nc] == 1:  # Avoid buildings
                    continue
                if watermask is not None and watermask[nr, nc]:
                    continue

                next_cost = curr_cost + 1
                heapq.heappush(open_set, (
                    next_cost + heuristic((nr, nc), goal),
                    next_cost,
                    (nr, nc),
                    path + [(nr, nc)]
                ))

    return [], float('inf')


def new_spot(path, indx, path_array):
    rows, cols = path_array.shape
    row, col = path[indx]

    if row < 0 or row >= rows or col < 0 or col >= cols:
        return None

    neighbors = [
        (row - 1, col - 1), (row - 1, col), (row - 1, col + 1),
        (row, col - 1), (row, col + 1),
        (row + 1, col - 1), (row + 1, col), (row + 1, col + 1)
    ]

    new_neighbors = []
    for n in neighbors:
        if 0 <= n[0] < rows and 0 <= n[1] < cols:
            if (
                abs(n[0] - path[indx + 1][0]) + abs(n[1] - path[indx + 1][1]) > 0 and
                abs(n[0] - path[indx - 1][0]) + abs(n[1] - path[indx - 1][1]) > 0
            ):
                new_neighbors.append(n)

    max_value = float("-inf")
    max_index = None

    for r, c in new_neighbors:
        value = path_array[r, c]
        if value > max_value:
            max_value = value
            max_index = (r, c)

    return max_index if max_index else path[indx]


def alter_path(path, path_array):
    if len(path) < 3:
        return path

    start = path[0]
    end = path[-1]

    for i in range(1, len(path) - 2):
        new_p = new_spot(path, i, path_array)
        if new_p:
            path[i] = new_p

    new_path = []
    for i in range(len(path) - 1):
        new_path.append(path[i])
        if (abs(path[i][0] - path[i + 1][0]) + abs(path[i][1] - path[i + 1][1])) > 2:
            new_path.append((
                (path[i][0] + path[i + 1][0]) // 2,
                (path[i][1] + path[i + 1][1]) // 2,
            ))

    # Ensure start and end are explicitly added
    new_path = [start] + new_path[1:-1] + [end]

    return list(dict.fromkeys(new_path))



def fix_path_final(path):
    new_path = []
    for i in range(len(path) - 1):
        new_path.append(path[i])
        if (abs(path[i][0] - path[i + 1][0]) + abs(path[i][1] - path[i + 1][1])) > 1:
            new_path.append((
                (path[i][0] + path[i + 1][0]) // 2,
                (path[i][1] + path[i + 1][1]) // 2,
            ))
    return new_path


def get_neighbour_paths(paths, map_avoid, slope):
    rows, cols = map_avoid.shape
    path_array = np.zeros((rows, cols))

    for path in paths:
        for r, c in path:
            if 0 <= r < rows and 0 <= c < cols:
                path_array[r, c] = 5

    path_array = gaussian_filter(path_array, sigma=2, mode="constant")
    path_array -= map_avoid * HOUSE_AVOID_MULT
    path_array -= slope[:rows, :cols] * SLOPE_AVOID_MULT

    return path_array

def make_paths(slope, map_data, watermask):
    rows, cols = map_data.shape
    map_avoid = gaussian_filter(map_data, sigma=3, mode="constant")

    doors = [(r, c) for r in range(rows) for c in range(cols) if map_data[r][c] == 2]
    if len(doors) < 2:
        raise ValueError("Need at least 2 door locations to generate paths.")

    paths = []

    for start in doors:
        # Find nearest door (excluding self)
        nearest = min(
            (d for d in doors if d != start),
            key=lambda d: heuristic(start, d)
        )

        # Nearest path
        path1, cost1 = a_star(start, nearest, map_data, watermask=watermask)
        if path1 and cost1 <= 1.5 * heuristic(start, nearest):
            paths.append(path1)

        # Random different door
        end = random.choice([d for d in doors if d != start and d != nearest])
        path2, cost2 = a_star(start, end, map_data, watermask=watermask)
        if path2 and cost2 <= 1.5 * heuristic(start, end):
            paths.append(path2)

    for iter_num in range(Iterations):
        for i in range(len(paths)):
            path_array = get_neighbour_paths(paths, map_avoid, slope)
            paths[i] = alter_path(paths[i], path_array)

        plot_iteration(map_data.copy(), paths, iter_num + 1)

    mapcopy = map_data.copy()
    final_paths = np.zeros_like(map_data, dtype=int)

    for p in paths:
        p = fix_path_final(p)
        for r, c in p:
            if 0 <= r < rows and 0 <= c < cols:
                mapcopy[r, c] = 3
                final_paths[r, c] = 1

    fig, ax = plt.subplots(layout='constrained')
    cax = ax.imshow(mapcopy, cmap='hot', interpolation='nearest')
    fig.colorbar(cax, ax=ax, label='Value')
    ax.set_title("Final Paths on Map")
    ax.set_xlabel("Column")
    ax.set_ylabel("Row")
    plt.show()

    return final_paths



if __name__ == "__main__":
    slope = np.loadtxt('../slope.txt', dtype=float)
    map_data = np.loadtxt('map.txt', dtype=float)

    if slope.shape != map_data.shape:
        raise ValueError("Slope and map must be the same shape.")

    final_paths = make_paths(slope, map_data)
    print(final_paths)
