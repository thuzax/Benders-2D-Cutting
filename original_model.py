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
            for l in range(board_width - items[i]["width"]):
                for w in range(board_height - items[i]["height"]):
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
    overlapping_constrs = []
    for j in range(1, len(y_vars)+1):
        for r in range(board_width):
            for s in range(board_height):
                A_keys = []
                x_keys = []
                items_to_constr = []
                for key in x_vars_names.keys():
                    i, c, l, w = key
                    A_key = (i, l, w, r, s)
                    x_key = (i, c, l, w)                    
                    if (A_key in A):
                        items_to_constr.append(x_vars[x_key])
                        print(A_key, x_key, x_vars_names[x_key])

                if (len(items_to_constr) > 0):
                    overlapping_constrs.append(model.addConstr(
                        quicksum(
                            item
                            for item in items_to_constr
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


    print_model(model)
    # print(A)
    return model