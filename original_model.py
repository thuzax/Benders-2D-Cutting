import os
from gurobipy import *


def print_model(model):
    model.write("temp.lp")
    with open("temp.lp", "r") as f_model:
        text = f_model.read()
        print(text)
        os.remove("temp.lp")


def create_x_vars(model, items, board_height, board_width, number_of_boards):
    x_vars_names = []
    x_vars = []
    for i in range(len(items)):
        for j in range(number_of_boards):
            for l in range(board_width - items[i]["width"]):
                for w in range(board_height - items[i]["height"]):
                    var_name = (
                        "x_" 
                        + str(items[i]["id"]) + "_" 
                        + str(j) + "_" 
                        + str(l) + "_" 
                        + str(w)
                    )
                    
                    x_vars_names.append(var_name)
                    x_vars.append(model.addVar(
                        name=var_name,
                        vtype=GRB.BINARY
                    ))
                
    return (x_vars_names, x_vars)


def create_y_vars(model, number_of_boards):
    y_vars_names = []
    y_vars = []
    for j in range(number_of_boards):
        var_name = "y_" + str(j)
        y_vars_names.append(var_name)
        y_vars.append(
            model.addVar(name=var_name, vtype=GRB.BINARY)
        )
    return (y_vars_names, y_vars)

def create_overlapping_constr(
    model, 
    board_width,
    board_height,
    x_vars,
    x_vars_names,
    y_vars,
    y_vars_names,
    A
):
    overlapping_constrs = []
    for j in range(len(y_vars)):
        for r in range(board_width):
            for s in range(board_height):
                A_keys = []
                x_keys = []
                
                for k, x in enumerate(x_vars_names):
                    
                    x_key = k
                    i, c, l, w = tuple(int(p) for p in x.split("_")[1:])
                    A_key = (i, l, w, r, s)
                    
                    if (A_key in A):
                        A_keys.append(A_key)
                        x_keys.append(x_key)

                if (len(A_keys) > 0):
                    overlapping_constrs.append(model.addConstr(
                        quicksum(
                            A[A_keys[k]] * x_vars[x_keys[k]]
                            for k in range(len(A_keys))
                        )
                        <=
                        y_vars[j],
                        name=(
                            "overlapping_" 
                            + str(j) + "_" 
                            + str(r) + "_" 
                            + str(s)
                        )
                    ))

    return overlapping_constrs


def create_all_items_must_be_allocated_constr(
    model,
    items,
    x_vars,
    x_vars_names,
    number_of_boards
):
    must_be_allocated_constrs = []
    items_coords_dict = {items[i]["id"]: [] for i in range(len(items))}
    for k in range(len(x_vars_names)):
        i, j, l, w = tuple(int(p) for p in x_vars_names[k].split("_")[1:])
        items_coords_dict[i].append(k)
    
    for i in items_coords_dict.keys():
        must_be_allocated_constrs.append(model.addConstr(
            quicksum(x_vars[k] for k in items_coords_dict[i])
            ==
            1,
            name=(
                "must_be_allocated_" 
                + str(i) 
            )
        ))

    return must_be_allocated_constrs


def create_model(
        items, 
        board_height, 
        board_width, 
        A, 
        number_of_boards,
        model_name
    ):
    model = Model(name=model_name)

    x_vars_names, x_vars = create_x_vars(
        model, items, board_height, board_width, number_of_boards
    )
    y_vars_names, y_vars = create_y_vars(
        model, number_of_boards
    )

    model.setObjective(
        quicksum((j+1) * y_vars[j] for j in range(len(y_vars))),
        sense=GRB.MINIMIZE
    )

    
    overlapping_constrs = create_overlapping_constr(
        model, 
        board_width,
        board_height,
        x_vars,
        x_vars_names,
        y_vars,
        y_vars_names,
        A
    )

    must_be_allocated_constrs = create_all_items_must_be_allocated_constr(
        model,
        items,
        x_vars,
        x_vars_names,
        number_of_boards
    )


    print_model(model)
    print(A)
    return model