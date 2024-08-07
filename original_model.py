import os
from gurobipy import *


def print_model(model):
    model.write("temp.lp")
    with open("temp.lp", "r") as f_model:
        text = f_model.read()
        print(text)
        os.remove("temp.lp")


def print_iis(model):
    model.write("iismodel.ilp")
    with open("iismodel.ilp", "r") as f_model:
        text = f_model.read()
        print(text)
        os.remove("iismodel.ilp")


def create_x_vars(model, items, board_height, board_width, number_of_boards):
    x_vars_names = {}
    x_vars = {}
    for i in range(1, len(items)+1):
        for j in range(1, number_of_boards+1):
            for l in range(board_width - items[i]["width"] + 1):
                for w in range(board_height - items[i]["height"] + 1):
                    var_name = (
                        "x_" 
                        + str(items[i]["id"]) + "_" 
                        + str(j) + "_" 
                        + str(l) + "_" 
                        + str(w)
                    )
                    x_vars_names[i,j,l,w] = var_name
                    x_vars[i,j,l,w] = model.addVar(
                        name=var_name,
                        vtype=GRB.BINARY
                    )
                    
                
    return (x_vars_names, x_vars)


def create_y_vars(model, number_of_boards):
    y_vars_names = {}
    y_vars = {}
    for j in range(1, number_of_boards+1):
        var_name = "y_" + str(j)
        y_vars_names[j] = var_name
        y_vars[j] = model.addVar(name=var_name, vtype=GRB.BINARY)
    return (y_vars_names, y_vars)


def create_overlapping_constr(
    model, 
    items,
    board_width,
    board_height,
    x_vars,
    x_vars_names,
    y_vars,
    y_vars_names,
    A
):
    overlapping_constrs = {}
    
    keys = [
        x_var_name.split("_")[1:] 
        for x_var_name in x_vars_names.values()
    ]

    for k in range(len(keys)):
        keys[k][0] = int(keys[k][0])
        keys[k][1] = int(keys[k][1])
        keys[k][2] = int(keys[k][2])
        keys[k][3] = int(keys[k][3])
        keys[k] = tuple(keys[k])

    for j in range(1, len(y_vars)+1):
        for r in range(board_width):
            for s in range(board_height):
                vars_constr = []
                for k in range(len(keys)):
                    i, c, l, w = keys[k]
                    if (j == c and (i, l, w, r, s) in A):
                        # constr_hash[j, r, s].append(x_vars[i, j, l, w])
                        vars_constr.append(x_vars[i, j, l, w])
                
                if (len(vars_constr) > 0):
                    model.addConstr(
                        quicksum(vars_constr) <= y_vars[j],
                        name=(
                            "overlapping_constr_" 
                            + str(j) + "_" 
                            + str(r) + "_" 
                            + str(s)
                        )
                    )



    return overlapping_constrs


def create_all_items_must_be_allocated_constr(
    model,
    items,
    x_vars,
    x_vars_names,
    number_of_boards
):
    must_be_allocated_constrs = []

    for i in range(1, len(items)+1):
        items_for_constr = []
        for key in x_vars.keys():
            if (key[0] == i):
                items_for_constr.append(x_vars[key])
        must_be_allocated_constrs.append(model.addConstr(
            quicksum(
                item
                for item in items_for_constr
            )
            ==
            1,
            name=(
                "must_be_allocated_constrs_" 
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
        quicksum(j * y_vars[j] for j in range(1, len(y_vars)+1)),
        sense=GRB.MINIMIZE
    )

    
    overlapping_constrs = create_overlapping_constr(
        model, 
        items,
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


    # print_model(model)
    # print(A)
    return model