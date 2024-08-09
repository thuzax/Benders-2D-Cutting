import os
import sys
import numpy
from model_manager import *
from input_manager import read
from output_manager import draw_solution


def calculate_items_areas(items):
    return {
        i: item["width"] * item["height"]
        for i, item in items.items()
    }
    

def create_points_cutted_matrix(items, board_height, board_width):
    A = set()
    
    for i in range(1, len(items)+1):
        item = items[i]
        l = 0
        width = item["width"]
        height = item["height"]
        while (l + width - 1 <= board_width - 1):
            r = l
            while (r <= l + width - 1):
                w = 0
                while (w + height - 1 <= board_height - 1):
                    s = w
                    while (s <= w + height - 1):
                        A.add((item["id"],l,w,r,s))
                        s += 1
                    w += 1
                r += 1
            l += 1
    return A


def run(argv):
    if (len(argv) < 3):
        print("1. Needs instance name")
        print("2. Needs output directory")
        exit(0)
    
    input_file = argv[1]
    output_directory = argv[2]

    if (not os.path.exists(output_directory)):
        os.mkdir(output_directory)

    instance_data, items_ids_mapping = read(input_file)
    items_areas = calculate_items_areas(instance_data["items"])
    board_area = instance_data["height"] * instance_data["width"]

    A = create_points_cutted_matrix(
        instance_data["items"], 
        instance_data["height"], 
        instance_data["width"]
    )

    number_of_boards = instance_data["number_of_items"]

    model = create_original_model(
        instance_data["items"],
        instance_data["height"],
        instance_data["width"], 
        items_areas,
        board_area,
        A,
        number_of_boards,
        "2D-BPP"
    )
    
    print("======================")
    print_model(model)
    model.optimize()
    # model.computeIIS()
    # print_iis(model)
    print("======================")

    board = {}
    board_ids = []

    for var in model.getVars():
        if ("y" in var.VarName):
            if (var.x > 0.5):
                board_ids.append(int(var.VarName.split("_")[1]))

    last_board_id = max(board_ids)
    
    for k in range(1, last_board_id+1):
        x = {}
        y = {}
        items_to_draw = {}
        for var in model.getVars():
            if ("x" in var.VarName):
                i, j, l, w = var.VarName.split("_")[1:]
                if (int(j) == k and var.x > 0.5):
                    x[int(i)] = int(l)
                    y[int(i)] = int(w)
                    items_to_draw[int(i)] = instance_data["items"][int(i)]
        
        draw_solution(
            items_to_draw,
            items_ids_mapping,
            x,
            y,
            instance_data["width"], 
            instance_data["height"],
            output_directory,
            k
        )

    # create_subproblem(1, 
    #     instance_data["items"], 
    #     instance_data["height"], 
    #     instance_data["width"], 
    #     A, 
    #     "SP1"
    # )

    model = create_master_problem(
        instance_data["items"],
        instance_data["height"],
        instance_data["width"], 
        items_areas,
        board_area,
        A,
        number_of_boards,
        "master-2D-BPP"
    )

    # for var in model.getVars():
    #     if (var.x > 0.5):
    #         print(var)

    
if __name__ == "__main__":
    run(sys.argv)







