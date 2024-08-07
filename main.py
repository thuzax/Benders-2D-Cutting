import os
import sys
import numpy
from original_model import *
from input_manager import read
from output_manager import draw_solution

def verify_cut_on_X(l, r, item, board_width):
    '''
    if 0 <= l <= r <= l + item width - 1 <= board width, then r is within the horizontal cut range
    '''
    if (
        (l <= r) 
        and (r <= l + item["width"] - 1)
        and (l + item["width"] - 1 <= board_width - 1)
    ):
        return 1
    return 0

def verify_cut_on_Y(w, s, item, board_height):
    '''
    if 0 <= w <= s <= w + item height - 1 <= board height, then s is within the vertical cut range
    '''
    if (
        (w <= s) 
        and (w <= w + item["height"] - 1)
        and (w + item["height"] - 1 <= board_height - 1)
    ):
        return 1
    return 0



def create_points_cutted_matrix(items, board_height, board_width):
    A = dict()
    
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
                        A[item["id"],l,w,r,s] = True
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


    A = create_points_cutted_matrix(
        instance_data["items"], 
        instance_data["height"], 
        instance_data["width"]
    )

    model = create_model(
        instance_data["items"],
        instance_data["height"],
        instance_data["width"], 
        A,
        instance_data["number_of_items"],
        "2D-BPP"
    )
    
    print("======================")
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

    # for var in model.getVars():
    #     if (var.x > 0.5):
    #         print(var)

    # example to use later
    # board_1 = [instance_data["items"][0], instance_data["items"][1]]
    # draw_solution(
    #     board_1, 
    #     items_ids_mapping, 
    #     {1: 0, 3: 20}, 
    #     {1: 0, 3: 0}, 
    #     instance_data["width"], instance_data["height"],
    #     output_directory,
    #     1
    # )

    
if __name__ == "__main__":
    run(sys.argv)







