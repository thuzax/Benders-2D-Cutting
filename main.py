import os
import sys
from model_manager import *
from input_manager import read
from output_manager import draw_solution


def run(argv):
    if (len(argv) < 3):
        print("1. Needs instance name")
        print("2. Needs output directory")
        exit(0)
    
    input_file = argv[1]
    output_directory = argv[2]

    if (not os.path.exists(output_directory)):
        os.mkdir(output_directory)

    instance_data, items_ids_mapping = read(argv[1])

    board_1 = [instance_data["items"][0], instance_data["items"][2]]
    board_2 = [instance_data["items"][1], instance_data["items"][3]]
    board_3 = [instance_data["items"][4]]

    draw_solution(
        board_1, 
        items_ids_mapping, 
        {1: 0, 3: 20}, 
        {1: 0, 3: 0}, 
        instance_data["width"], instance_data["height"],
        output_directory,
        1
    )

    draw_solution(
        board_2, 
        items_ids_mapping, 
        {2: 0, 4: 0}, 
        {2: 0, 4: 30}, 
        instance_data["width"], instance_data["height"],
        output_directory,
        2
    )

    draw_solution(
        board_3, 
        items_ids_mapping, 
        {5: 0}, 
        {5: 0}, 
        instance_data["width"], instance_data["height"],
        output_directory,
        3
    )

if __name__ == "__main__":
    run(sys.argv)







