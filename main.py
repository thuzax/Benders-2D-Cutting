import os
import sys
import math
import json
import csv
import time
import signal
from models_manager import *
from input_manager import read
from output_manager import draw_solution


def create_directory_if_not_exists(dir_path):
    '''Create a directory (folder) if it does not exists using its path'''
    if (not os.path.exists(dir_path)):
        os.makedirs(dir_path)

def draw(
    x_vars_dict, 
    z_vars_dict, 
    instance_data, 
    items_ids_mapping, 
    output_directory, 
    prefix=""
):
    '''Get draw parameters and call draw_solution to plot the optimization result'''
    bin_ids = []

    # Get the index of the last used bin
    for var_name, value in z_vars_dict.items():
        if (value > 0.5):
            bin_ids.append(int(var_name.split("_")[1]))
    last_bin_id = max(bin_ids)

    for k in range(1, last_bin_id+1):
        x = {}
        y = {}
        items_to_draw = {}
        # Get the position (x, y) of the bin for each item 
        for var_name, value in x_vars_dict.items():
            i, j, l, w = var_name.split("_")[1:]
            if (int(j) == k and value > 0.5):
                x[int(i)] = int(l)
                y[int(i)] = int(w)
                items_to_draw[int(i)] = instance_data["items"][int(i)]
        
        # Plot the items on bin k
        draw_solution(
            items_to_draw,
            items_ids_mapping,
            x,
            y,
            instance_data["width"], 
            instance_data["height"],
            output_directory,
            k,
            prefix
        )


def calculate_items_areas(items):
    '''Returns a dicionary with the areas of the items'''
    return {
        i: item["width"] * item["height"]
        for i, item in items.items()
    }
    

def create_points_cutted_matrix(items, bin_height, bin_width):
    '''Returns a set of tuples (i,l,w,r,s). If (i,l,w,r,s) is in the set, then the point (r,s) is cutted if the left bottom of item i is placed on point (l,w)'''

    point_is_cutted = set()
    
    for i in range(1, len(items)+1):
        item = items[i]
        l = 0
        width = item["width"]
        height = item["height"]
        while (l + width - 1 <= bin_width - 1):
            r = l
            while (r <= l + width - 1):
                w = 0
                while (w + height - 1 <= bin_height - 1):
                    s = w
                    while (s <= w + height - 1):
                        point_is_cutted.add((item["id"],l,w,r,s))
                        s += 1
                    w += 1
                r += 1
            l += 1
    
    return point_is_cutted


def calculate_number_of_bins(items_areas, bin_area):
    '''Return the estimated number of bins. The value is calculated by dividing the sum of the items areas by the bin area. The number is rounded to ceil and then is increased in 20% and then it is rounded to ceil again.'''
    return math.ceil((math.ceil(sum(items_areas.values())/bin_area)) * 1.2)


def run_standard_model(
    instance_data, 
    point_is_cutted, 
    time_limit,
    log_path="" 
):    
    '''Construct and run the complete model'''
    
    model = create_standard_model(
        instance_data["items"],
        instance_data["height"],
        instance_data["width"], 
        instance_data["items_areas"],
        instance_data["bin_area"],
        point_is_cutted,
        instance_data["number_of_bins"],
        "standard-2D-BPP",
        log_path,
        time_limit
    )

    print("STARTING OPT")
    s = time.time()
    model.optimize()
    opt_time = time.time() - s
    print("opt time:", time.time() - s)

    # If infeasible calculate the infeasible constraints
    if (model_is_infeasible(model)):
        model.computeIIS()
        print_iis(model)

    if (feasible_not_found(model)):
        sol_dict = get_solution_dict_MIP(model)
        model.close()
        return ({}, {}, {})
    
    # Get the variables values
    z_vars_dict = {}
    x_vars_dict = {}
    for var in model.getVars():
        if ("z" in var.VarName):
            if (var.x > 0.5):
                z_vars_dict[var.VarName] = var.x
        if ("x" in var.VarName):
            if (var.x > 0.5):
                x_vars_dict[var.VarName] = var.x

    # Create a dictionary with data related to the solution
    sol_dict = get_solution_dict_MIP(model)
    sol_dict["opt_time"] = opt_time

    model.close()

    return (x_vars_dict, z_vars_dict, sol_dict)


def run_benders_model(instance_data, point_is_cutted, time_limit, log_path=""):

    model = create_master_problem(
        instance_data["items"],
        instance_data["height"],
        instance_data["width"], 
        instance_data["items_areas"],
        instance_data["bin_area"],
        point_is_cutted,
        instance_data["number_of_bins"],
        "master-2D-BPP",
        log_path,
        time_limit
    )
    print("STARTING OPT")
    s = time.time()
    model.optimize(master_call_back)
    opt_time = time.time() - s
    print("opt time:", time.time() - s)
    
    # If infeasible calculate the infeasible constraints
    if (model_is_infeasible(model)):
        model.computeIIS(master_call_back)
        print_iis(model)

    if (feasible_not_found(model)):
        model.close()
        return ({}, {}, {})
    
    # Get the variables z values
    z_vars_dict = {}
    for var in model.getVars():
        if ("z" in var.VarName):
            if (var.x > 0.5):
                z_vars_dict[var.VarName] = var.x
    
    # # Uncomment to print the model with lazy constraints
    # for lazy in model._lazy_set:
    #     model.addConstr(lazy)
    # print_model(model)

    # Create a dictionary with data related to the solution
    sol_dict = get_solution_dict_MIP(model)
    sol_dict["opt_time"] = opt_time
    
    model.close()

    return (model._x_vars, z_vars_dict, sol_dict)

def run(argv):
    start_time = time.time()

    if (len(argv) < 2):
        print("1. Needs instance name")
        print("2. Needs output directory")
        text = "3. (Optional, Default = 0) "
        text += "Which method will be used: 1 - Benders; 2 - Standard Model" 
        print(text)
        exit(0)

    input_file = argv[0]
    output_directory = argv[1]

    create_directory_if_not_exists(output_directory)

    instance_data, items_ids_mapping = read(input_file)

    instance_data["items_areas"] = calculate_items_areas(instance_data["items"])
    instance_data["bin_area"] = (
        instance_data["height"] * instance_data["width"]
    )

    instance_data["number_of_bins"] = calculate_number_of_bins(
        instance_data["items_areas"], 
        instance_data["bin_area"]
    )

    # set containing a_{i,l,w,r,s}
    point_is_cutted = create_points_cutted_matrix(
        instance_data["items"],
        instance_data["height"],
        instance_data["width"]
    )

    # print("Set with a_{i,l,w,r,s} created")

    draw_prefix = ""
    log_path = os.path.join(output_directory, "solution.log")
    time_limit = 60
    # argv[2] indicates the solution method. If 1, then use benders. Otherwise, use the complete model
    if (len(argv) >= 3 and int(argv[2]) == 1):
        x_vars_dict, z_vars_dict, sol_dict = run_benders_model(
            instance_data, 
            point_is_cutted,
            time_limit,
            log_path 
        )
        draw_prefix = "benders_"
    
    else:
        x_vars_dict, z_vars_dict, sol_dict = run_standard_model(
            instance_data, 
            point_is_cutted,
            time_limit,
            log_path
        )
        draw_prefix = "standard_"
    
    end_time = time.time()

    # Calculate the total time spent by the program
    sol_dict["real_time"] = end_time - start_time
    
    # Save the dictionary with data related to the solution in a json
    json_file_path = os.path.join(output_directory, "solution_data.json")
    with open(json_file_path, "w") as output:
        json.dump(sol_dict, output, indent=2)
    
    # Save the dictionary with data related to the solution in a csv
    csv_file_path = os.path.join(output_directory, "solution_data.csv")
    with open(csv_file_path, "w", newline="") as output:
        keys = [
            key 
            for key in sol_dict.keys() 
            if key != "variables"
        ]
        out_csv = csv.writer(output, keys)
        out_csv.writerow(keys)
        out_csv.writerow([sol_dict[key] for key in keys])

    # If z_vars_dict is empty, then no solution was found
    if (len(z_vars_dict) == 0):
        return

    # Otherwise, draw the solution
    draw(
        x_vars_dict,
        z_vars_dict,
        instance_data,
        items_ids_mapping,
        output_directory,
        draw_prefix
    )
    

if __name__ == "__main__":
    run(sys.argv[1:])