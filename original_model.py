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

def create_x_j_vars(model, items, board_height, board_width, j):
    x_vars_names = {}
    x_vars_keys = {}
    x_of_board_vars_key = []
    x_vars = {}
    for i in items.keys():
        for l in range(board_width - items[i]["width"] + 1):
            for w in range(board_height - items[i]["height"] + 1):
                var_name = (
                    "x_" 
                    + str(items[i]["id"]) + "_" 
                    + str(j) + "_" 
                    + str(l) + "_" 
                    + str(w)
                )
                x_of_board_vars_key.append((i, j, l, w))
                x_vars_keys[i,j,l,w] = (i,j,l,w)
                x_vars_names[i,j,l,w] = var_name
                x_vars[i,j,l,w] = model.addVar(
                    name=var_name,
                    vtype=GRB.BINARY
                )

    return (x_vars_names, x_vars_keys, x_of_board_vars_key, x_vars)

def create_x_vars(model, items, board_height, board_width, number_of_boards):
    x_vars_names = {}
    x_vars_keys = {}
    x_of_board_vars_keys = {}
    x_vars = {}
    for j in range(1, number_of_boards+1):
        vars_data = create_x_j_vars(model, items, board_height, board_width, j)
        x_vars_names |= vars_data[0]
        x_vars_keys |= vars_data[1]
        x_of_board_vars_keys[j] = vars_data[2]
        x_vars |= vars_data[3]
        # x_of_board_vars_keys[j] = []
        # for i in items.keys():
        #     for l in range(board_width - items[i]["width"] + 1):
        #         for w in range(board_height - items[i]["height"] + 1):
        #             var_name = (
        #                 "x_" 
        #                 + str(items[i]["id"]) + "_" 
        #                 + str(j) + "_" 
        #                 + str(l) + "_" 
        #                 + str(w)
        #             )
        #             x_of_board_vars_keys[j].append((i, j, l, w))
        #             x_vars_keys[i,j,l,w] = (i,j,l,w)
        #             x_vars_names[i,j,l,w] = var_name
        #             x_vars[i,j,l,w] = model.addVar(
        #                 name=var_name,
        #                 vtype=GRB.BINARY
        #             )

    return (x_vars_names, x_vars_keys, x_of_board_vars_keys, x_vars)


def create_y_vars(model, number_of_boards):
    y_vars_names = {}
    y_vars = {}
    for j in range(1, number_of_boards+1):
        var_name = "y_" + str(j)
        y_vars_names[j] = var_name
        y_vars[j] = model.addVar(name=var_name, vtype=GRB.BINARY)
    return (y_vars_names, y_vars)


def create_board_overlapping_constr(
    model, 
    board_width,
    board_height,
    j,
    keys,
    x_vars,
    y,
    A
):
    constr = {}
    for r in range(board_width):
        for s in range(board_height):
            vars_constr = []
            for k in keys:
                i, c, l, w = k
                if ((i, l, w, r, s) in A):
                    vars_constr.append(x_vars[i, j, l, w])
            if (len(vars_constr) > 0):
                constr[j,r,s] = model.addConstr(
                    quicksum(vars_constr) <= y,
                    name=(
                        "overlapping_constr_" 
                        + str(j) + "_" 
                        + str(r) + "_" 
                        + str(s)
                    )
                )
    return constr


def create_overlapping_constr(
    model, 
    board_width,
    board_height,
    x_vars,
    x_of_board_vars_keys,
    y_vars,
    A
):
    overlapping_constrs = {}
    
    # keys = x_vars_keys

    # for j in range(1, len(y_vars)+1):
    for j, keys in x_of_board_vars_keys.items():
        overlapping_constrs |= create_board_overlapping_constr(
            model, 
            board_width, 
            board_height,
            j,
            keys,
            x_vars,
            y_vars[j],
            A
        )
        # for r in range(board_width):
        #     for s in range(board_height):
        #         vars_constr = []
        #         for k in keys.keys():
        #             i, c, l, w = k
        #             if (j == c and (i, l, w, r, s) in A):
        #                 vars_constr.append(x_vars[i, j, l, w])
        #         if (len(vars_constr) > 0):
        #             model.addConstr(
        #                 quicksum(vars_constr) <= y_vars[j],
        #                 name=(
        #                     "overlapping_constr_" 
        #                     + str(j) + "_" 
        #                     + str(r) + "_" 
        #                     + str(s)
        #                 )
        #             )

    return overlapping_constrs


def create_all_items_must_be_allocated_constr(
    model,
    items,
    x_vars,
):
    must_be_allocated_constrs = {}

    for i in items.keys():
        items_for_constr = []
        for key in x_vars.keys():
            if (key[0] == i):
                items_for_constr.append(x_vars[key])
        must_be_allocated_constrs[i] = model.addConstr(
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
        )
    
    return must_be_allocated_constrs


def create_original_model(
        items, 
        board_height, 
        board_width, 
        A, 
        number_of_boards,
        model_name
    ):
    model = Model(name=model_name)

    x_vars_names, x_vars_keys, x_of_board_vars_keys, x_vars = create_x_vars(
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
        board_width,
        board_height,
        x_vars,
        x_of_board_vars_keys,
        y_vars,
        A
    )

    must_be_allocated_constrs = create_all_items_must_be_allocated_constr(
        model,
        items,
        x_vars,
    )


    # print_model(model)
    # print(A)
    return model