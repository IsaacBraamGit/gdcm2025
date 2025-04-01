from scipy.ndimage import gaussian_filter
import numpy as np  # Needed for np.zeros and np.absolute
from gdpc import Block

class MapHolder:
    def __init__(self, ED, heights, ACCEPTABLE_BUILDING_SCORE=1.3):
        self.ED = ED
        self.heights = heights
        self.ACCEPTABLE_BUILDING_SCORE = ACCEPTABLE_BUILDING_SCORE

        BUILD_AREA = self.ED.getBuildArea()
        self.STARTX, self.STARTY, self.STARTZ = BUILD_AREA.begin
        self.LASTX, self.LASTY, self.LASTZ = BUILD_AREA.last
        self.SIZEX, self.SIZEY, self.SIZEZ = BUILD_AREA.size

        self.trees_found = []
        for wood in ["oak", "spruce", "birch", "jungle", "acacia", "dark_oak", "mangrove"]:
            self.trees_found.append(wood)
        self.block_slope_score = None

    def is_water(self, x, y, z):
        block_type = self.ED.getBlock((x, y - 1, z))
        return "water" in block_type.id or "lava" in block_type.id

    def is_tree_count(self, x, y, z):
        block_type = self.ED.getBlock((x, y - 1, z))
        if "wood" in block_type.id:
            wood_type = block_type.id.replace('wood', '').replace("_", "").replace("minecraft:", "")
            self.trees_found.append(wood_type)
            return True
        if "log" in block_type.id:
            wood_type = block_type.id.replace('log', '').replace("_", "").replace("minecraft:", "")
            self.trees_found.append(wood_type)
            return True
        return False

    def is_tree(self, x, y, z):
        block_type = self.ED.getBlock((x, y - 1, z))
        return "wood" in block_type.id or "log" in block_type.id

    def is_air(self, x, y, z):
        block_type = self.ED.getBlock((x, y - 1, z))
        return "air" in block_type.id

    def find_min_idx(self, x):
        k = x.argmin()
        ncol = x.shape[1]
        return int(k / ncol), int(k % ncol)

    def find_flat_areas_and_trees(self, print_colors=False):
        block_slope_score = np.zeros((self.SIZEX, self.SIZEZ))
        tree_spots = np.zeros((self.SIZEX, self.SIZEZ), dtype=bool)

        for x in range(self.STARTX, self.LASTX + 1):
            for z in range(self.STARTZ, self.LASTZ + 1):
                height_current_block = self.heights[(x - self.STARTX, z - self.STARTZ)]
                score_current_block = 0

                if self.is_water(x, height_current_block, z):
                    block_slope_score[x - self.STARTX, z - self.STARTZ] = 10
                elif self.is_tree_count(x, height_current_block, z):
                    tree_spots[x - self.STARTX, z - self.STARTZ] = True
                    block_slope_score[x - self.STARTX, z - self.STARTZ] = 1
                else:
                    try:
                        neighbor_height = self.heights[(x - self.STARTX + 1, z - self.STARTZ)]
                        if not self.is_tree(x + 1, neighbor_height, z):
                            score_current_block += np.abs(height_current_block - neighbor_height)
                        else:
                            score_current_block += 1
                    except:
                        score_current_block += 10

                    try:
                        neighbor_height = self.heights[(x - self.STARTX - 1, z - self.STARTZ)]
                        if not self.is_tree(x - 1, neighbor_height, z):
                            score_current_block += np.abs(height_current_block - neighbor_height)
                        else:
                            score_current_block += 1
                    except:
                        score_current_block += 10

                    try:
                        neighbor_height = self.heights[(x - self.STARTX, z - self.STARTZ + 1)]
                        if not self.is_tree(x, neighbor_height, z + 1):
                            score_current_block += np.abs(height_current_block - neighbor_height)
                        else:
                            score_current_block += 1
                    except:
                        score_current_block += 10

                    try:
                        neighbor_height = self.heights[(x - self.STARTX, z - self.STARTZ - 1)]
                        if not self.is_tree(x, neighbor_height, z - 1):
                            score_current_block += np.abs(height_current_block - neighbor_height)
                        else:
                            score_current_block += 1
                    except:
                        score_current_block += 10

                    block_slope_score[x - self.STARTX, z - self.STARTZ] = score_current_block

        block_slope_score = gaussian_filter(block_slope_score, sigma=3, mode="constant")

        if print_colors:
            for x in range(self.STARTX + 1, self.LASTX):
                for z in range(self.STARTZ + 1, self.LASTZ):
                    height_current_block = self.heights[(x - self.STARTX, z - self.STARTZ)] - 1
                    score = block_slope_score[x - self.STARTX, z - self.STARTZ]
                    if score > 7:
                        self.ED.placeBlock((x, height_current_block, z), Block("red_wool"))
                    elif score > 5:
                        self.ED.placeBlock((x, height_current_block, z), Block("pink_wool"))
                    elif score > 3:
                        self.ED.placeBlock((x, height_current_block, z), Block("yellow_wool"))
                    elif score > 1.5:
                        self.ED.placeBlock((x, height_current_block, z), Block("blue_wool"))
                    else:
                        self.ED.placeBlock((x, height_current_block, z), Block("green_wool"))

        self.block_slope_score = block_slope_score
        return block_slope_score, tree_spots
