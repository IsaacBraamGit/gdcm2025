#  /setbuildarea ~0 ~0 ~0 ~100 ~100 ~100
import logging
import random
from random import randint

from glm import ivec2, ivec3

from gdpc import Block, Editor, Box, Transform
from gdpc import geometry as geo
from gdpc import minecraft_tools as mt
from gdpc import editor_tools as et
import numpy as np
from copy import copy, deepcopy
from gdpc.geometry import placeBox

from get_build_map import MapHolder
ED = Editor(buffering=True)

BUILD_AREA = ED.getBuildArea()  # BUILDAREA

STARTX, STARTY, STARTZ = BUILD_AREA.begin
LASTX, LASTY, LASTZ = BUILD_AREA.last
SIZEX, SIZEY, SIZEZ = BUILD_AREA.size
CENTERX = STARTX + (LASTX - STARTX) // 2
CENTERZ = STARTZ + (LASTZ - STARTZ) // 2

building_places = np.zeros((SIZEX, SIZEZ))

WORLDSLICE = ED.loadWorldSlice(BUILD_AREA.toRect(), cache=True)  # this takes a while
heights = WORLDSLICE.heightmaps["MOTION_BLOCKING_NO_LEAVES"]



def claim_zone(xstart, zstart, sizex, sizez, door):
    edges = 9
    for x in range(xstart - STARTX - edges, xstart + sizex - STARTX + edges):
        for z in range(zstart - STARTZ - edges, zstart + sizez - STARTZ + edges):
            try:
                if building_places[x,z] == 0:
                    building_places[x, z] = 10_000
            except:
                pass

    for x in range(xstart - STARTX-1, xstart + sizex - STARTX+2):
        for z in range(zstart - STARTZ-1, zstart + sizez - STARTZ+2):
            try:
                building_places[x, z] = 20_000
            except:
                pass


def build_deco_railing(sizex, sizey, sizez, ylevel, height, wood_type):
    for _ in range(height):
        ylevel -= 1
        for x in range(0, sizex + 1):
            if x == 0 or x == 2 or x == 5 or x == 7:
                ED.placeBlock((x, ylevel + sizey, -1), Block(f"{wood_type}_stairs", {"facing": "south", "half": "top"}))
            else:
                ED.placeBlock((x, ylevel + sizey, -1),
                              Block(f"{wood_type}_stairs", {"facing": "south", "half": "bottom"}))
            if x == 0 or x == 7:
                ED.placeBlock((x, ylevel + sizey + 1, -1), Block(f"{wood_type}_slab"))
        ED.placeBlock((-1, ylevel + sizey + 1, -1), Block(f"{wood_type}_planks"))
        ED.placeBlock((-1, ylevel + sizey + 2, -1), Block("lantern"))

        for x in range(0, sizex + 1):
            if x == 0 or x == 2 or x == 5 or x == 7:
                ED.placeBlock((x, ylevel + sizey, sizez + 1),
                              Block(f"{wood_type}_stairs", {"facing": "north", "half": "top"}))
            else:
                ED.placeBlock((x, ylevel + sizey, sizez + 1),
                              Block(f"{wood_type}_stairs", {"facing": "north", "half": "bottom"}))
            if x == 0 or x == 7:
                ED.placeBlock((x, ylevel + sizey + 1, sizez + 1), Block(f"{wood_type}_slab"))
        ED.placeBlock((x + 1, ylevel + sizey + 1, sizez + 1), Block(f"{wood_type}_planks"))
        ED.placeBlock((x + 1, ylevel + sizey + 2, sizez + 1), Block("lantern"))

        for z in range(0, sizez + 1):
            if z == 0 or z == 2 or z == 5 or z == 7:
                ED.placeBlock((-1, ylevel + sizey, z), Block(f"{wood_type}_stairs", {"facing": "east", "half": "top"}))
            else:
                ED.placeBlock((-1, ylevel + sizey, z),
                              Block(f"{wood_type}_stairs", {"facing": "east", "half": "bottom"}))
            if z == 0 or z == 7:
                ED.placeBlock((-1, ylevel + sizey + 1, z), Block(f"{wood_type}_slab"))

        ED.placeBlock((-1, ylevel + sizey + 1, z + 1), Block(f"{wood_type}_planks"))
        ED.placeBlock((-1, ylevel + sizey + 2, z + 1), Block("lantern"))

        for z in range(0, sizez + 1):
            if z == 0 or z == 2 or z == 5 or z == 7:
                ED.placeBlock((sizex + 1, ylevel + sizey, z),
                              Block(f"{wood_type}_stairs", {"facing": "west", "half": "top"}))
            else:
                ED.placeBlock((sizex + 1, ylevel + sizey, z),
                              Block(f"{wood_type}_stairs", {"facing": "west", "half": "bottom"}))
            if z == 0 or z == 7:
                ED.placeBlock((sizex + 1, ylevel + sizey + 1, z), Block(f"{wood_type}_slab"))

        ED.placeBlock((sizex + 1, ylevel + sizey + 1, -1), Block(f"{wood_type}_planks"))
        ED.placeBlock((sizex + 1, ylevel + sizey + 2, -1), Block("lantern"))
        ylevel += 1
        ylevel += sizey


def build_exterior_one_house_part(sizex, sizey, sizez, ylevel, height, wood_type):
    for _ in range(height):
        if _ == 0:
            # remove dirt
            for x in range(1, sizex):
                for z in range(1, sizez):
                    for y in range(ylevel, ylevel + sizey):
                        ED.placeBlock((x, y, z), Block("air"))

            # foundation
            for x in range(0, sizex + 1):
                for z in range(0, sizez + 1):
                    ED.placeBlock((x, ylevel - 2, z), Block(f"{wood_type}_wood"))
                    ED.placeBlock((x, ylevel - 3, z), Block(f"{wood_type}_wood"))
                    ED.placeBlock((x, ylevel - 4, z), Block(f"{wood_type}_wood"))

        # floor
        for x in range(0, sizex + 1):
            for z in range(0, sizez + 1):
                ED.placeBlock((x, ylevel - 1, z), Block(f"{wood_type}_wood"))

        for x in range(1, sizex):
            for z in range(1, sizez):
                ED.placeBlock((x, ylevel - 1, z), Block("beehive"))

        # walls
        for x in range(0, sizex):
            for y in range(0, sizey):
                if randint(0, 1) == 1:
                    ED.placeBlock((x, ylevel + y, 0), Block("cobblestone_wall"))
                else:
                    ED.placeBlock((x, ylevel + y, 0), Block("andesite_wall"))
        for x in range(0, sizex):
            for y in range(0, sizey):
                if randint(0, 1) == 1:
                    ED.placeBlock((x, ylevel + y, sizez), Block("cobblestone_wall"))
                else:
                    ED.placeBlock((x, ylevel + y, sizez), Block("andesite_wall"))

        for z in range(0, sizez):
            for y in range(0, sizey):
                if randint(0, 1) == 1:
                    ED.placeBlock((0, ylevel + y, z), Block("cobblestone_wall"))
                else:
                    ED.placeBlock((0, ylevel + y, z), Block("andesite_wall"))

        for z in range(0, sizez):
            for y in range(0, sizey):
                if randint(0, 1) == 1:
                    ED.placeBlock((sizex, ylevel + y, z), Block("cobblestone_wall"))
                else:
                    ED.placeBlock((sizex, ylevel + y, z), Block("andesite_wall"))

        # pillars
        for y in range(0, sizey):
            ED.placeBlock((0, ylevel + y, 0), Block(f"{wood_type}_log"))
            ED.placeBlock((sizex, ylevel + y, 0), Block(f"{wood_type}_log"))
            ED.placeBlock((0, ylevel + y, sizez), Block(f"{wood_type}_log"))
            ED.placeBlock((sizex, ylevel + y, sizez), Block(f"{wood_type}_log"))

        build_deco(sizex, sizez, ylevel)
        ylevel += sizey

    # roof
    for x in range(0, sizex + 1):
        for z in range(0, sizez + 1):
            ED.placeBlock((x, ylevel - 1, z), Block(f"{wood_type}_wood"))

    for x in range(1, sizex):
        for z in range(1, sizez):
            ED.placeBlock((x, ylevel - 1, z), Block("beehive"))
    build_deco_roof(sizex, sizez, ylevel)
    ylevel_save = ylevel
    for it in range(2):
        ylevel = ylevel_save
        if it == 1:
            roofing_it_mat = f"{wood_type}_slab"
            ylevel += 1
        else:
            roofing_it_mat = f"{wood_type}_wood"

        # l1
        ED.placeBlock((0, ylevel, 0), Block(roofing_it_mat))
        ED.placeBlock((0, ylevel, sizez), Block(roofing_it_mat))
        ED.placeBlock((sizex, ylevel, 0), Block(roofing_it_mat))
        ED.placeBlock((sizex, ylevel, sizez), Block(roofing_it_mat))

        # l2
        ylevel += 1
        ED.placeBlock((1, ylevel, 1), Block(roofing_it_mat))
        ED.placeBlock((0, ylevel, 1), Block(roofing_it_mat))
        ED.placeBlock((1, ylevel, 0), Block(roofing_it_mat))

        ED.placeBlock((sizex - 1, ylevel, 1), Block(roofing_it_mat))
        ED.placeBlock((sizex, ylevel, 1), Block(roofing_it_mat))
        ED.placeBlock((sizex - 1, ylevel, 0), Block(roofing_it_mat))

        ED.placeBlock((1, ylevel, sizez - 1), Block(roofing_it_mat))
        ED.placeBlock((0, ylevel, sizez - 1), Block(roofing_it_mat))
        ED.placeBlock((1, ylevel, sizez), Block(roofing_it_mat))

        ED.placeBlock((sizex - 1, ylevel, sizez - 1), Block(roofing_it_mat))
        ED.placeBlock((sizex, ylevel, sizez - 1), Block(roofing_it_mat))
        ED.placeBlock((sizex - 1, ylevel, sizez), Block(roofing_it_mat))

        # l3
        ylevel += 1
        ED.placeBlock((2, ylevel, 2), Block(roofing_it_mat))
        ED.placeBlock((1, ylevel, 2), Block(roofing_it_mat))
        ED.placeBlock((2, ylevel, 1), Block(roofing_it_mat))
        ED.placeBlock((0, ylevel, 2), Block(roofing_it_mat))
        ED.placeBlock((2, ylevel, 0), Block(roofing_it_mat))

        ED.placeBlock((sizex - 2, ylevel, 2), Block(roofing_it_mat))
        ED.placeBlock((sizex - 1, ylevel, 2), Block(roofing_it_mat))
        ED.placeBlock((sizex - 2, ylevel, 1), Block(roofing_it_mat))
        ED.placeBlock((sizex, ylevel, 2), Block(roofing_it_mat))
        ED.placeBlock((sizex - 2, ylevel, 0), Block(roofing_it_mat))

        ED.placeBlock((2, ylevel, sizez - 2), Block(roofing_it_mat))
        ED.placeBlock((1, ylevel, sizez - 2), Block(roofing_it_mat))
        ED.placeBlock((2, ylevel, sizez - 1), Block(roofing_it_mat))
        ED.placeBlock((0, ylevel, sizez - 2), Block(roofing_it_mat))
        ED.placeBlock((2, ylevel, sizez), Block(roofing_it_mat))

        ED.placeBlock((sizex - 2, ylevel, sizez - 2), Block(roofing_it_mat))
        ED.placeBlock((sizex - 1, ylevel, sizez - 2), Block(roofing_it_mat))
        ED.placeBlock((sizex - 2, ylevel, sizez - 1), Block(roofing_it_mat))
        ED.placeBlock((sizex, ylevel, sizez - 2), Block(roofing_it_mat))
        ED.placeBlock((sizex - 2, ylevel, sizez), Block(roofing_it_mat))

        ylevel += 1
        # L4
        for x in range(0, sizex + 1):
            ED.placeBlock((x, ylevel, 3), Block(roofing_it_mat))
            ED.placeBlock((x, ylevel, 4), Block(roofing_it_mat))

        for z in range(0, sizez + 1):
            ED.placeBlock((3, ylevel, z), Block(roofing_it_mat))
            ED.placeBlock((4, ylevel, z), Block(roofing_it_mat))

        ED.placeBlock((3, ylevel, 3), Block(f"{wood_type}_planks"))
        ED.placeBlock((4, ylevel, 4), Block(f"{wood_type}_planks"))
        ED.placeBlock((4, ylevel, 3), Block(f"{wood_type}_planks"))
        ED.placeBlock((3, ylevel, 4), Block(f"{wood_type}_planks"))

    ylevel = ylevel_save
    Glass = "glass_pane"
    for x in range(1, sizex):
        ED.placeBlock((x, ylevel, 0), Block(Glass))
        ED.placeBlock((x, ylevel, sizez), Block(Glass))
        if x > 1 and x < sizex - 1:
            ED.placeBlock((x, ylevel + 1, 0), Block(Glass))
            ED.placeBlock((x, ylevel + 1, sizez), Block(Glass))
            if x > 2 and x < sizex - 2:
                ED.placeBlock((x, ylevel + 2, 0), Block(Glass))
                ED.placeBlock((x, ylevel + 2, sizez), Block(Glass))

    for z in range(1, sizez):
        ED.placeBlock((0, ylevel, z), Block(Glass))
        ED.placeBlock((sizex, ylevel, z), Block(Glass))
        if z > 1 and z < sizez - 1:
            ED.placeBlock((0, ylevel + 1, z), Block(Glass))
            ED.placeBlock((sizex, ylevel + 1, z), Block(Glass))
            if z > 2 and z < sizez - 2:
                ED.placeBlock((0, ylevel + 2, z), Block(Glass))
                ED.placeBlock((sizex, ylevel + 2, z), Block(Glass))
    ylevel = 0
    for _ in range(height):
        # stairs
        ED.placeBlock((3, ylevel, 1), Block("stone_brick_stairs", {"facing": "west", "half": "bottom"}))
        ED.placeBlock((2, ylevel + 1, 1), Block("stone_brick_stairs", {"facing": "west", "half": "bottom"}))
        ED.placeBlock((1, ylevel + 1, 1), Block("stone_bricks"))
        ED.placeBlock((1, ylevel + 2, 2), Block("stone_brick_stairs", {"facing": "south", "half": "bottom"}))
        ED.placeBlock((1, ylevel + 3, 3), Block("stone_brick_stairs", {"facing": "south", "half": "bottom"}))
        ED.placeBlock((1, ylevel + 4, 4), Block("stone_brick_stairs", {"facing": "south", "half": "bottom"}))
        ED.placeBlock((1, ylevel + 4, 3), Block("air"))
        ED.placeBlock((1, ylevel + 4, 2), Block("air"))
        ED.placeBlock((1, ylevel + 4, 1), Block("air"))

        ylevel += sizey


def build_deco(sizex, sizez, ylevel):
    num_deco = 5
    deco_choice = randint(0, num_deco)
    if deco_choice == 0:
        for x in range(2, sizex - 1):
            for z in range(2, sizez - 1):
                ED.placeBlock((x, ylevel-1, z), Block("deepslate_bricks"))
        ED.placeBlock((2, ylevel, 2), Block("cauldron"))
        ED.placeBlock((2, ylevel, 3), Block("furnace",{"facing":"east"}))
        ED.placeBlock((2, ylevel, 4), Block("furnace",{"facing":"east"}))
        ED.placeBlock((2, ylevel+1, 4), Block("lantern"))
        ED.placeBlock((2, ylevel+1, 5), Block("grindstone",{"face":"floor"}))
        ED.placeBlock((2, ylevel, 5), Block("furnace", {"facing": "north"}))
        ED.placeBlock((3, ylevel, 5), Block("furnace",{"facing":"north"}))
        ED.placeBlock((4, ylevel, 5), Block("furnace",{"facing":"north"}))
        ED.placeBlock((5, ylevel, 5), Block("anvil"))
        ED.placeBlock((4, ylevel-1, 3), Block("soul_sand"))
        ED.placeBlock((4, ylevel, 3), Block("fire"))
        for x in range(3, sizex - 1):
            for z in range(2, sizez - 2):
                ED.placeBlock((x, ylevel+3, z), Block("deepslate_bricks"))
                ED.placeBlock((x, ylevel + 2, z), Block("iron_bars"))
        ED.placeBlock((4, ylevel + 3, 3), Block("tinted_glass"))
        ED.placeBlock((4, ylevel + 2, 3), Block("air"))
    if deco_choice == 1:
        for x in range(2, sizex - 1):
            for z in range(2, sizez - 1):
                direction = random.choice(["east", "north", "south", "up", "west"])
                chest1 = Block("barrel", {"facing": direction},
                               data='{Items: [{Slot: 0b, id: "bread", Count: 10b}]}')

                block = random.choice([chest1, chest1, Block("hay_block"), Block("hay_block"), Block("hay_block"), Block("air"),
                                       Block("cobweb")])
                ED.placeBlock((x, ylevel, z), block)
        ED.placeBlock((2, ylevel, sizex - 2), Block("hay_block"))
        ED.placeBlock((2, ylevel+1, sizex - 2), Block("lantern"))
        for x in range(3, sizex - 2):
            for z in range(3, sizez - 2):
                direction = random.choice(["down", "east", "north", "south", "up", "west"])
                chest1 = Block("barrel", {"facing": direction},
                               data='{Items: [{Slot: 0b, id: "wheat", Count: 30b}]}')

                block = random.choice([chest1,chest1, Block("hay_block"), Block("hay_block"), Block("hay_block"), Block("air"),
                                       Block("cobweb")])
                ED.placeBlock((x, ylevel+1, z), block)

        ED.placeBlock((4, ylevel + 2, 4), Block("hay_block"))

    if deco_choice == 2:
        if ylevel != 0:
            with ED.pushTransform(Transform((1, 0, 0))):
                # dispenser = Block("dispenser", data='{Items: [{Slot: 1b, id: "warden_spawn_egg", Count: 1b}]}')
                # ED.placeBlock((4, ylevel, 3), dispenser)
                ED.placeBlock((4, ylevel, 4), Block("sculk_sensor"))
                ED.placeBlock((3, ylevel, 4), Block("sticky_piston", {"facing": "west"}))
                ED.placeBlock((2, ylevel, 4), Block("slime_block"))
                ED.placeBlock((2, ylevel, 3), Block("slime_block"))
                ED.placeBlock((2, ylevel, 2), Block("slime_block"))
                ED.placeBlock((1, ylevel, 4), Block("netherite_block"))
                ED.placeBlock((1, ylevel, 3), Block("netherite_block"))
                ED.placeBlock((1, ylevel, 2), Block("netherite_block"))
        else:
            with ED.pushTransform(Transform((1, 0, 0))):
                ED.placeBlock((2, ylevel, 2), Block("dirt"))
                ED.placeBlock((2, ylevel, 3), Block("spruce_trapdoor", {"facing": "south", "open": "true"}))
                ED.placeBlock((3, ylevel, 2), Block("spruce_trapdoor", {"facing": "east", "open": "true"}))
                ED.placeBlock((1, ylevel, 2), Block("spruce_trapdoor", {"facing": "west", "open": "true"}))

                ED.placeBlock((2, ylevel + 1, 2), Block("oak_wood"))
                ED.placeBlock((2, ylevel + 2, 2), Block("mangrove_leaves"))

                ED.placeBlock((3, ylevel, 3), Block("bookshelf"))
                ED.placeBlock((3, ylevel + 1, 3), Block("lantern"))
                bookData = mt.bookData(
                    "Welcome stranger, to my humble home, please be a bit quite, I am trying to read.")
                et.placeLectern(ED, (3, ylevel, 4), bookData=bookData, facing="east")
                ED.placeBlock((4, ylevel, 4), Block("quartz_stairs", {"facing": "east"}))

                ED.placeBlock((2, ylevel, 5), Block("lightning_rod"))
                ED.placeBlock((2, ylevel + 1, 5), Block("redstone_lamp"))
                ED.placeBlock((2, ylevel + 2, 5), Block("sculk_sensor"))

    if deco_choice == 3:
        with ED.pushTransform(Transform((1, 0, 0))):
            ED.placeBlock((1, ylevel, 2), Block("bookshelf"))
            ED.placeBlock((2, ylevel, 2), Block("bookshelf"))
            ED.placeBlock((3, ylevel, 2), Block("bookshelf"))
            ED.placeBlock((4, ylevel, 2), Block("bookshelf"))
            ED.placeBlock((4, ylevel, 3), Block("bookshelf"))
            ED.placeBlock((4, ylevel, 4), Block("bookshelf"))
            ED.placeBlock((3, ylevel + 1, 2), Block("bookshelf"))
            ED.placeBlock((4, ylevel + 1, 2), Block("bookshelf"))
            ED.placeBlock((4, ylevel + 1, 3), Block("bookshelf"))
            ED.placeBlock((4, ylevel + 1, 4), Block("bookshelf"))
            ED.placeBlock((4, ylevel, 5), Block("bookshelf"))
            ED.placeBlock((3, ylevel, 5), Block("bookshelf"))
            ED.placeBlock((3, ylevel, 3), Block("bookshelf"))
            ED.placeBlock((3, ylevel + 1, 3), Block("lantern"))
            bookData = mt.bookData(
                "I have been experimenting for days and still can't find the spell for love. All these spells just make my weapons stronger, but I'm not a fighter...")
            et.placeLectern(ED, (3, ylevel, 4), bookData=bookData, facing="west")
            ED.placeBlock((2, ylevel, 3), Block("enchanting_table"))

    if deco_choice == 4:
        with ED.pushTransform(Transform((0, 0, 1))):
            ED.placeBlock((3, ylevel, 2), Block("quartz_stairs", {"facing": "north", "half": "bottom"}))
            ED.placeBlock((4, ylevel, 2), Block("quartz_stairs", {"facing": "north", "half": "bottom"}))

            ED.placeBlock((3, ylevel, 4), Block("quartz_stairs", {"facing": "south", "half": "bottom"}))
            ED.placeBlock((4, ylevel, 4), Block("quartz_stairs", {"facing": "south", "half": "bottom"}))

            ED.placeBlock((2, ylevel, 3), Block("quartz_stairs", {"facing": "west", "half": "bottom"}))
            ED.placeBlock((5, ylevel, 3), Block("quartz_stairs", {"facing": "east", "half": "bottom"}))

            ED.placeBlock((3, ylevel, 3), Block("dark_oak_fence"))
            ED.placeBlock((4, ylevel, 3), Block("dark_oak_fence"))

            ED.placeBlock((3, ylevel + 1, 3), Block("dark_oak_pressure_plate"))
            ED.placeBlock((4, ylevel + 1, 3), Block("dark_oak_pressure_plate"))

            ED.placeBlock((3, ylevel + 3, 3), Block("glowstone"))
            ED.placeBlock((4, ylevel + 3, 3), Block("glowstone"))

            ED.placeBlock((3, ylevel + 3, 2), Block("iron_bars"))
            ED.placeBlock((4, ylevel + 3, 2), Block("iron_bars"))

            ED.placeBlock((3, ylevel + 3, 4), Block("iron_bars"))
            ED.placeBlock((4, ylevel + 3, 4), Block("iron_bars"))

            ED.placeBlock((2, ylevel + 3, 3), Block("iron_bars"))
            ED.placeBlock((5, ylevel + 3, 3), Block("iron_bars"))

            ED.placeBlock((2, ylevel, 2), Block("red_carpet"))
            ED.placeBlock((5, ylevel, 2), Block("red_carpet"))

            ED.placeBlock((2, ylevel, 4), Block("red_carpet"))
            ED.placeBlock((5, ylevel, 4), Block("red_carpet"))

    if deco_choice == 5:
        if ylevel != 0:
            for x in range(1, sizex):
                for z in range(1, sizez):
                    for y in range(ylevel,ylevel+5):
                        ED.placeBlock((x, y, z), Block("dark_prismarine"))
            for x in range(1, sizex-1):
                for z in range(1, sizez-1):
                    for y in range(ylevel,ylevel+5):
                        ED.placeBlock((x, y, z), Block("air"))

            for x in range(2, sizex):
                ED.placeBlock((x, ylevel+2, sizez-1), Block("redstone_block"))

            for z in range(2, sizez):
                ED.placeBlock((sizex-1, ylevel+2, z), Block("redstone_block"))

            for x in range(2, sizex-1):
                ED.placeBlock((x, ylevel+2, sizez-2), Block("redstone_lamp"))

            for z in range(2, sizez-1):
                ED.placeBlock((sizex-2, ylevel+2, z), Block("redstone_lamp"))

            for x in range(2, sizex-1):
                rand_int = randint(0,4)
                if rand_int == 0 :
                    ED.placeBlock((x, ylevel, sizez-2), Block("crafting_table"))
                if rand_int == 1 :
                    ED.placeBlock((x, ylevel, sizez-2), Block("furnace"))
                    if randint(0,1) == 1:
                        ED.placeBlock((x, ylevel+1, sizez - 2), Block("furnace"))
                if rand_int == 2:
                    ED.placeBlock((x, ylevel, sizez-2), Block("cauldron"))
                    ED.placeBlock((x, ylevel+1, sizez-2), Block("lightning_rod",{"facing":"south"}))
                if rand_int == 3:
                    ED.placeBlock((x, ylevel, sizez-2), Block("scaffolding"))
                    ED.placeBlock((x, ylevel+1, sizez - 2), Block("heavy_weighted_pressure_plate"))
                if rand_int ==4:
                    ED.placeBlock((x, ylevel, sizez-2), Block("smoker"))
            for z in range(3, sizez-1):
                rand_int = randint(0,4)
                if rand_int == 0 :
                    ED.placeBlock((sizex-2, ylevel, z), Block("crafting_table"))
                    ED.placeBlock((sizex - 2, ylevel+1, z), Block("cake"))
                if rand_int == 1 :
                    ED.placeBlock((sizex-2, ylevel, z), Block("furnace",{"facing":"west"}))
                    if randint(0,1) == 1:
                        ED.placeBlock((sizex-2, ylevel+1, z), Block("furnace",{"facing":"west"}))
                if rand_int == 2:
                    ED.placeBlock((sizex-2, ylevel, z), Block("cauldron"))
                    ED.placeBlock((sizex-2, ylevel+1, z), Block("lightning_rod",{"facing":"east"}))
                if rand_int == 3:
                    ED.placeBlock((sizex-2, ylevel, z), Block("scaffolding"))
                    ED.placeBlock((sizex-2, ylevel+1, z), Block("heavy_weighted_pressure_plate"))
                if rand_int ==4:
                    ED.placeBlock((sizex-2, ylevel, z), Block("smoker"))

        else:
            with ED.pushTransform(Transform((1, 0, 0))):
                ED.placeBlock((2, ylevel, 2), Block("dirt"))
                ED.placeBlock((2, ylevel, 3), Block("spruce_trapdoor", {"facing": "south", "open": "true"}))
                ED.placeBlock((3, ylevel, 2), Block("spruce_trapdoor", {"facing": "east", "open": "true"}))
                ED.placeBlock((1, ylevel, 2), Block("spruce_trapdoor", {"facing": "west", "open": "true"}))

                ED.placeBlock((2, ylevel + 1, 2), Block("oak_wood"))
                ED.placeBlock((2, ylevel + 2, 2), Block("mangrove_leaves"))

                ED.placeBlock((3, ylevel, 3), Block("bookshelf"))
                ED.placeBlock((3, ylevel + 1, 3), Block("lantern"))
                bookData = mt.bookData(
                    "Welcome stranger, to my humble home, please be a bit quite, I am trying to read.")
                et.placeLectern(ED, (3, ylevel, 4), bookData=bookData, facing="east")
                ED.placeBlock((4, ylevel, 4), Block("quartz_stairs", {"facing": "east"}))

                ED.placeBlock((2, ylevel, 5), Block("lightning_rod"))
                ED.placeBlock((2, ylevel+1, 5), Block("redstone_lamp"))
                ED.placeBlock((2, ylevel+2, 5), Block("sculk_sensor"))

def build_deco_roof(sizex, sizez, ylevel):
    chest1 = Block("chest", {"facing": "south", "type": "left"},
                   data='{Items: [{Slot: 0b, id: "milk_bucket", Count: 1b}]}')
    chest2 = Block("chest", {"facing": "south", "type": "right"},
                   data='{Items: [{Slot: 0b, id: "diamond", Count: 1b}]}')
    left_deco = random.choice(["crafting_table", "jukebox", "note_block", "scaffolding", "barrel", "loom"])
    right_deco = random.choice(["crafting_table", "jukebox", "note_block", "scaffolding", "barrel", "loom"])
    bed_color = random.choice(["red", "blue", "yellow", "black", "brown", "purple", "cyan"])
    carpet1 = random.choice(["red", "blue", "yellow", "black", "brown", "purple", "cyan"])
    carpet2 = random.choice(["red", "blue", "yellow", "black", "brown", "purple", "cyan"])
    ED.placeBlock((6, ylevel, 5), Block(left_deco))
    ED.placeBlock((6, ylevel, 2), Block(right_deco))

    ED.placeBlock((6, ylevel + 1, 5), Block("lantern"))
    ED.placeBlock((6, ylevel + 1, 2), Block("flower_pot"))

    ED.placeBlock((4, ylevel, 1), chest1)
    ED.placeBlock((3, ylevel, 1), chest2)

    ED.placeBlock((5, ylevel, 3), Block(f"{bed_color}_bed", {"facing": "east"}))
    ED.placeBlock((5, ylevel, 4), Block(f"{bed_color}_bed", {"facing": "east"}))

    ED.placeBlock((4, ylevel, 6), Block("quartz_stairs", {"facing": "south"}))
    ED.placeBlock((3, ylevel, 6), Block("quartz_stairs", {"facing": "south"}))

    ED.placeBlock((5, ylevel, 6), Block("oak_wall_sign", {"facing": "east"}))
    ED.placeBlock((2, ylevel, 6), Block("oak_wall_sign", {"facing": "west"}))

    ED.placeBlock((5, ylevel, 2), Block(f"{carpet2}_carpet"))
    ED.placeBlock((5, ylevel, 5), Block(f"{carpet1}_carpet"))

    number = 0
    for x in range(2, 5):
        for z in range(2, 6):
            if number % 2 == 0:
                ED.placeBlock((x, ylevel, z), Block(f"{carpet1}_carpet"))
            else:
                ED.placeBlock((x, ylevel, z), Block(f"{carpet2}_carpet"))
            number += 1
        number += 1


def make_door_claim(sizex, sizez, direction_door, xstart, ystart, zstart):
    if direction_door == "north":
        ED.placeBlock((sizex, 0, 3), Block("air"))
        ED.placeBlock((sizex, 1, 3), Block("air"))
        ED.placeBlock((sizex + 1, 0, 3), Block("air"))
        ED.placeBlock((sizex + 1, 1, 3), Block("air"))
        building_places[xstart - STARTX+sizex+1, zstart - STARTZ+3] = 5_000

    if direction_door == "south":
        ED.placeBlock((0, 0, 3), Block("air"))
        ED.placeBlock((0, 1, 3), Block("air"))
        ED.placeBlock((-1, 0, 3), Block("air"))
        ED.placeBlock((-1, 1, 3), Block("air"))
        building_places[xstart - STARTX-1, zstart - STARTZ+3] = 5_000

    if direction_door == "east":
        ED.placeBlock((4, 0, sizez), Block("air"))
        ED.placeBlock((4, 1, sizez), Block("air"))
        ED.placeBlock((4, 0, sizez + 1), Block("air"))
        ED.placeBlock((4, 1, sizez + 1), Block("air"))
        building_places[xstart - STARTX+4, zstart - STARTZ+sizez+1] = 5_000

    if direction_door == "west":
        ED.placeBlock((4, 0, 0), Block("air"))
        ED.placeBlock((4, 1, 0), Block("air"))
        ED.placeBlock((4, 0, -1), Block("air"))
        ED.placeBlock((4, 1, -1), Block("air"))
        building_places[xstart - STARTX+4, zstart - STARTZ-1] = 5_000

def make_door(sizex, sizez, direction_door):
    if direction_door == "north":
        ED.placeBlock((sizex, 0, 3), Block("air"))
        ED.placeBlock((sizex, 1, 3), Block("air"))
        ED.placeBlock((sizex + 1, 0, 3), Block("air"))
        ED.placeBlock((sizex + 1, 1, 3), Block("air"))

    if direction_door == "south":
        ED.placeBlock((0, 0, 3), Block("air"))
        ED.placeBlock((0, 1, 3), Block("air"))
        ED.placeBlock((-1, 0, 3), Block("air"))
        ED.placeBlock((-1, 1, 3), Block("air"))

    if direction_door == "east":
        ED.placeBlock((4, 0, sizez), Block("air"))
        ED.placeBlock((4, 1, sizez), Block("air"))
        ED.placeBlock((4, 0, sizez + 1), Block("air"))
        ED.placeBlock((4, 1, sizez + 1), Block("air"))

    if direction_door == "west":
        ED.placeBlock((4, 0, 0), Block("air"))
        ED.placeBlock((4, 1, 0), Block("air"))
        ED.placeBlock((4, 0, -1), Block("air"))
        ED.placeBlock((4, 1, -1), Block("air"))


def build_structure(xstart, ystart, zstart, sizex, sizey, sizez, direction_door, direction_extra_houses):
    xstart = xstart - int(sizex / 2)
    zstart = zstart - int(sizez / 2)
    sizey = 5
    ylevel = 0
    height = randint(1, 3)
    heightnorth = randint(1, 3)
    heightsouth = randint(1, 3)
    heighteast = randint(1, 3)
    heightwest = randint(1, 3)
    wood_type = random.choice(build_map.trees_found)
    # wood_type = random.choice(["oak","spruce","birch","jungle","acacia","dark_oak","mangrove"])

    # claim and remove trees first
    claim_zone(xstart, zstart, sizex, sizez, "todo")
    remove_trees(xstart, ystart, zstart, sizex, sizey, sizez)

    for extra_building_dir in direction_extra_houses:
        if extra_building_dir == "north":
            claim_zone(xstart + sizex + 1, zstart, sizex, sizez, "todo")
            remove_trees(xstart + sizex + 1, ystart, zstart, sizex, sizey, sizez)

        if extra_building_dir == "south":
            claim_zone(xstart - sizex - 1, zstart, sizex, sizez, "todo")
            remove_trees(xstart - sizex - 1, ystart, zstart, sizex, sizey, sizez)

        if extra_building_dir == "east":
            claim_zone(xstart, zstart + sizez + 1, sizex, sizez, "todo")
            remove_trees(xstart, ystart, zstart + sizez + 1, sizex, sizey, sizez)

        if extra_building_dir == "west":
            claim_zone(xstart, zstart - sizez - 1, sizex, sizez, "todo")
            remove_trees(xstart, ystart, zstart - sizez - 1, sizex, sizey, sizez)

    # make deco railing
    with ED.pushTransform(Transform((xstart, ystart, zstart))):
        # main building with door
        build_deco_railing(sizex, sizey, sizez, ylevel, height, wood_type)
        make_door_claim(sizex, sizez, direction_door,xstart, ystart, zstart)

    # side buildings
    for extra_building_dir in direction_extra_houses:
        if extra_building_dir == "north":
            with ED.pushTransform(Transform((xstart + sizex + 1, ystart, zstart))):
                build_deco_railing(sizex, sizey, sizez, ylevel, heightnorth, wood_type)

        if extra_building_dir == "south":
            with ED.pushTransform(Transform((xstart - sizex - 1, ystart, zstart))):
                build_deco_railing(sizex, sizey, sizez, ylevel, heightsouth, wood_type)

        if extra_building_dir == "east":
            with ED.pushTransform(Transform((xstart, ystart, zstart + sizez + 1))):
                build_deco_railing(sizex, sizey, sizez, ylevel, heighteast, wood_type)

        if extra_building_dir == "west":
            with ED.pushTransform(Transform((xstart, ystart, zstart - sizez - 1))):
                build_deco_railing(sizex, sizey, sizez, ylevel, heightwest, wood_type)

    # make buildings
    # make buildings
    with ED.pushTransform(Transform((xstart, ystart, zstart))):
        # main building with door
        build_exterior_one_house_part(sizex, sizey, sizez, ylevel, height, wood_type)
        make_door(sizex, sizez, direction_door)

    # side buildings
    for extra_building_dir in direction_extra_houses:
        print("direction extra houses" + extra_building_dir)

        if extra_building_dir == "north":
            with ED.pushTransform(Transform((xstart + sizex + 1, ystart, zstart))):
                build_exterior_one_house_part(sizex, sizey, sizez, ylevel, heightnorth, wood_type)

        if extra_building_dir == "south":
            with ED.pushTransform(Transform((xstart - sizex - 1, ystart, zstart))):
                build_exterior_one_house_part(sizex, sizey, sizez, ylevel, heightsouth, wood_type)

        if extra_building_dir == "east":
            with ED.pushTransform(Transform((xstart, ystart, zstart + sizez + 1))):
                build_exterior_one_house_part(sizex, sizey, sizez, ylevel, heighteast, wood_type)

        if extra_building_dir == "west":
            with ED.pushTransform(Transform((xstart, ystart, zstart - sizez - 1))):
                build_exterior_one_house_part(sizex, sizey, sizez, ylevel, heightwest, wood_type)

        with ED.pushTransform(Transform((xstart, ystart, zstart))):
            make_door(sizex, sizez, extra_building_dir)


def remove_trees(xstart, ystart, zstart, sizex, sizey, sizez):
    removed_tree_blocks = []
    borderxz = 2
    bordery = 10
    for x in range(xstart - borderxz, xstart + sizex + borderxz + 1):
        for y in range(ystart, ystart + sizey + bordery):
            for z in range(zstart - borderxz, zstart + sizez + borderxz + 1):
                type = ED.getBlock((x, y, z))
                if ("leaves" in type.id or "log" in type.id or "wood" in type.id):
                    ED.placeBlock((x, y, z), Block("air"))
                    removed_tree_blocks.append((x, y, z))

    # todo: these neighbours do leave some artifacts of trees, but all corners
    #  often results in requesting blocks that are off the map. Remove the artifacts,
    #  or make map bigger, but this seems harder.

    neighbour_pos = [ivec3(1, 0, 0), ivec3(-1, 0, 0), ivec3(0, 1, 0), ivec3(0, -1, 0), ivec3(0, 0, 1), ivec3(0, 0, -1)]

    while len(removed_tree_blocks) > 0:
        block = removed_tree_blocks[0]
        removed_tree_blocks.pop(0)

        for np in neighbour_pos:
            neighbor_block = block + np
            type = ED.getBlock(neighbor_block)
            if ("leaves" in type.id or "log" in type.id or "wood" in type.id):
                ED.placeBlock(neighbor_block, Block("air"))
                removed_tree_blocks.append(neighbor_block)


def where_door(best_loc_x, best_loc_z):
    distance_door_look = 5
    current_highest_side = 10_000
    try:
        current_highest_side = build_map.block_slope_score[best_loc_x + distance_door_look, best_loc_z]
        direction = "north"
    except:
        pass

    try:
        south = build_map.block_slope_score[best_loc_x - distance_door_look, best_loc_z]
        if (south < current_highest_side):
            current_highest_side = south
            direction = "south"
    except:
        pass
    try:
        east = build_map.block_slope_score[best_loc_x, best_loc_z + distance_door_look]
        if (east < current_highest_side):
            current_highest_side = east
            direction = "east"
    except:
        pass

    try:
        west = build_map.block_slope_score[best_loc_x, best_loc_z - distance_door_look]
        if (west < current_highest_side):
            direction = "west"
    except:
        pass

    return direction


def free_area_for_extra(best_loc_x, best_loc_y, best_loc_z, direction_door, block_slope_score):
    distance_area_look = 9
    acceptable_score = 2
    directions = []

    try:
        if direction_door != "north":
            if (heights[best_loc_x + distance_area_look, best_loc_z] == best_loc_y):
                if (block_slope_score[(best_loc_x + distance_area_look, best_loc_z)] < acceptable_score):
                    directions.append("north")
    except:
        pass

    try:
        if direction_door != "south":
            if (heights[best_loc_x - distance_area_look, best_loc_z] == best_loc_y):
                if (block_slope_score[(best_loc_x - distance_area_look, best_loc_z)] < acceptable_score):
                    directions.append("south")
    except:
        pass

    try:
        if direction_door != "east":
            if (heights[best_loc_x, best_loc_z + distance_area_look] == best_loc_y):
                if (block_slope_score[(best_loc_x, best_loc_z + distance_area_look)] < acceptable_score):
                    directions.append("east")
    except:
        pass
    try:
        if direction_door != "west":
            if (heights[best_loc_x, best_loc_z - distance_area_look] == best_loc_y):
                if (block_slope_score[(best_loc_x, best_loc_z - distance_area_look)] < acceptable_score):
                    directions.append("west")
    except:
        pass

    return directions


def build_boxes(block_slope_score, it):
    structx = 7
    structy = 7
    structz = 7

    block_slope_score += building_places
    best_loc_x, best_loc_z = build_map.find_min_idx(block_slope_score)
    min_score = min([min(r) for r in block_slope_score])
    if (min_score) > 2 and it > 1:
        return
    best_loc_y = heights[(best_loc_x, best_loc_z)]


    while build_map.is_tree(STARTX + best_loc_x, best_loc_y, STARTZ + best_loc_z) or build_map.is_air(STARTX + best_loc_x, best_loc_y,                                                              STARTZ + best_loc_z):
        best_loc_y -= 1

    direction_door = where_door(best_loc_x, best_loc_z)
    print(f"building house at: {(best_loc_x, best_loc_y, best_loc_z)}")

    direction_extra_house = free_area_for_extra(best_loc_x, best_loc_y, best_loc_z, direction_door, block_slope_score)
    build_structure(STARTX + best_loc_x, best_loc_y, STARTZ + best_loc_z, structx, structy, structz, direction_door,
                    direction_extra_house)
class Node():
    """A node class for A* Pathfinding"""

    def __init__(self, parent=None, position=None):
        self.parent = parent
        self.position = position

        self.g = 0
        self.h = 0
        self.f = 0

    def __eq__(self, other):
        return self.position == other.position

#code not writen by me, but adjusted by me.
def astar(maze, start, end):
    """Returns a list of tuples as a path from the given start to the given end in the given maze"""

    # Create start and end node
    start_node = Node(None, start)
    start_node.g = start_node.h = start_node.f = 0
    end_node = Node(None, end)
    end_node.g = end_node.h = end_node.f = 0

    # Initialize both open and closed list
    open_list = []
    closed_list = []

    # Add the start node
    open_list.append(start_node)
    iteration = 0
    # Loop until you find the end
    while len(open_list) > 0:
        iteration += 1
        if iteration > 4000:
            return None
        # Get the current node
        current_node = open_list[0]
        current_index = 0
        for index, item in enumerate(open_list):
            if item.f < current_node.f:
                current_node = item
                current_index = index

        # Pop current off open list, add to closed list
        open_list.pop(current_index)
        closed_list.append(current_node)

        # Found the goal
        if current_node == end_node:
            path = []
            current = current_node
            while current is not None:
                path.append(current.position)
                current = current.parent
            return path[::-1] # Return reversed path

        # Generate children
        children = []
        for new_position in [(0, -1), (0, 1), (-1, 0), (1, 0)]: # Adjacent squares

            # Get node position
            node_position = (current_node.position[0] + new_position[0], current_node.position[1] + new_position[1])

            # Make sure within range
            if node_position[0] > (len(maze) - 1) or node_position[0] < 0 or node_position[1] > (len(maze[len(maze)-1]) -1) or node_position[1] < 0:
                continue

            # Make sure walkable terrain
            if maze[node_position[0]][node_position[1]] != 0:
                continue

            # Create new node
            new_node = Node(current_node, node_position)

            # Append
            children.append(new_node)

        # Loop through children
        for child in children:

            # Child is on the closed list
            for closed_child in closed_list:
                if child == closed_child:
                    continue

            # Create the f, g, and h values
            child.g = current_node.g + 1
            child.h = ((child.position[0] - end_node.position[0]) ** 2) + ((child.position[1] - end_node.position[1]) ** 2)
            child.f = child.g + child.h

            # Child is already in the open list
            for open_node in open_list:
                if child == open_node and child.g > open_node.g:
                    continue

            # Add the child to the open list
            open_list.append(child)



def build_paths():
    doors = list(zip(*np.where(building_places == 5_000)))
    doors = sorted(doors, key=lambda tup: tup[0])
    for i in range(len(building_places)):
        for j in range(len(building_places[i])):
            if building_places[i][j] == 0 or building_places[i][j] == 10_000:
                building_places[i][j] = 0
            if building_places[i][j] == 5_000:
                building_places[i][j] = 0
            if building_places[i][j] == 20_000:
                building_places[i][j] = 1

    all_pairs = [(i, j) for i, j in zip(doors, doors[1:])]
    for pair in all_pairs:
        start = pair[0]
        end = pair[1]

        path = astar(building_places, start, end)
        if path is not None:
            for p in path:
                x, z = p
                if build_map.is_water(x+STARTX, heights[(x,z)],z+STARTZ):
                    ED.placeBlock((x + STARTX, heights[(x, z)], z + STARTZ), Block("oak_slab"))
                else:
                    ED.placeBlock((x+STARTX, heights[(x,z)]-1,z+STARTZ), Block("dirt_path"))




print("calculating heights...")

build_map = MapHolder(ED, heights, 1.3)
build_map.find_flat_areas_and_trees(print_colors=True)

for it in range(20):
    build_boxes(build_map.block_slope_score, it)
    ED.flushBuffer()
    # WORLDSLICE = ED.loadWorldSlice(BUILD_AREA.toRect(), cache=True)  # this takes a while
    # heights = WORLDSLICE.heightmaps["MOTION_BLOCKING_NO_LEAVES"]
WORLDSLICE = ED.loadWorldSlice(BUILD_AREA.toRect(), cache=True)  # this takes a while
heights = WORLDSLICE.heightmaps["MOTION_BLOCKING_NO_LEAVES"]
print("building paths...")
build_paths()

