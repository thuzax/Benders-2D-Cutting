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


def create_b_vars(model, items, number_of_boards):
    b_vars_names = {}
    b_vars = {}
    for i in items.keys():
        for j in range(1, number_of_boards+1):
            var_name = "b_" + str(i) + "_" + str(j)
            b_vars_names[i, j] = var_name
            b_vars[i, j] = model.addVar(name=var_name, vtype=GRB.BINARY)
    return (b_vars_names, b_vars)


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


def create_items_areas_constr(
    model,
    items_areas,
    board_area,
    x_vars,
    x_of_board_vars_keys
):
    constr = {}
    for j, x_j_vars_keys in x_of_board_vars_keys.items():
        constr_vars = []
        for key in x_j_vars_keys:
            i, j, l, w = key
            constr_vars.append(items_areas[i] * x_vars[key])
        constr[j] = model.addConstr(
            quicksum(constr_vars) 
            <= 
            board_area,
            "item_area_constr_" + 
            str(j)
        )
    
    return constr

def create_symmetry_cuts_constr(
    model,
    y_vars,
    number_of_boards
):
    constr = {}
    for j in range(2, number_of_boards+1):
        constr[j-1, j] = model.addConstr(
            y_vars[j-1] >= y_vars[j],
            name="symmetry_cut_" + str(j-1) + "_" + str(j)
        )
    return constr


def create_item_board_allocation_constr(
    model,
    items,
    items_areas,
    board_area,
    number_of_boards,
    y_vars,
    b_vars
):
    constr = {}
    for j in range(1, number_of_boards+1):
        constr[j] = model.addConstr(
            quicksum(items_areas[i] * b_vars[i,j] for i in items.keys()) 
            <= 
            board_area * y_vars[j],
            name="item_board_allocation_" + str(j)
        )
    return constr

def create_all_items_must_be_on_a_board_constr(
    model,
    items,
    number_of_boards,
    b_vars
):
    constr = {}
    for i in items.keys():
        constr[i] = model.addConstr(
            quicksum(b_vars[i,j] for j in range(1, number_of_boards+1)) == 1,
            name="all_items_must_be_on_a_board_" + str(i)
        )
    return constr


def create_feasibility_cut_expr_for_j(
    model, 
    j,
    subproblem_inf_sol
):
    allocated_boards = {}
    for key, b_var in subproblem_inf_sol.items():
        print(key)
        if (b_var > 0.5):
            i, k = key
            allocated_boards[i, j] = model._b_vars[i, j]

    constr_expr = {}

    constr_expr[j] = (
        quicksum(
            1 - allocated_boards[key] 
            for key in allocated_boards.keys()
        ) 
        >= 
        1
    )
    
    return constr_expr

def create_feasibility_cut_expr_for_subproblem(
    model, 
    number_of_boards,
    subproblem_inf_sol
):
    constr_expr = {}
    for j in range(1, number_of_boards+1):
        constr_expr |= create_feasibility_cut_expr_for_j(
            model, 
            j, 
            subproblem_inf_sol
        )
    return constr_expr

def create_feasibility_cut_expr(
    model,
    number_of_boards
):
    pass
    # solve_subproblem
    # create_feasibility_cut_expr(solution)






















def create_original_model(
    items, 
    board_height, 
    board_width, 
    items_areas,
    board_area,
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
        quicksum(y_vars[j] for j in range(1, len(y_vars)+1)),
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

    items_areas_constr = create_items_areas_constr(
        model, 
        items_areas, 
        board_area, 
        x_vars, 
        x_of_board_vars_keys
    )

    symmetry_custs = create_symmetry_cuts_constr(model, y_vars, number_of_boards)

    # print_model(model)
    # print(A)
    return model


def create_subproblem(
    j,
    items, 
    board_height, 
    board_width, 
    A, 
    model_name
):
    
    model = Model(name=model_name)

    x_vars_names, x_vars_keys, x_of_board_vars_keys, x_vars = create_x_j_vars(
        model, items, board_height, board_width, j
    )

    model.setObjective(
        0,
        sense=GRB.MINIMIZE
    )

    
    overlapping_constrs = create_board_overlapping_constr(
        model, 
        board_width, 
        board_height, 
        j, 
        x_of_board_vars_keys, 
        x_vars, 
        1, 
        A 
    )

    must_be_allocated_constrs = create_all_items_must_be_allocated_constr(
        model,
        items,
        x_vars
    )

    print_model(model)
    # print(A)
    return model

def create_master_problem(
    items, 
    board_height, 
    board_width, 
    items_areas,
    board_area,
    A, 
    number_of_boards,
    model_name
):
    
    model = Model(name=model_name)

    y_vars_names, y_vars = create_y_vars(
        model, number_of_boards
    )

    b_vars_names, b_vars = create_b_vars(model, items, number_of_boards)

    model.setObjective(
        quicksum(y_vars[j] for j in range(1, len(y_vars)+1)),
        sense=GRB.MINIMIZE
    )

    item_board_allocation = create_item_board_allocation_constr(
        model, 
        items, 
        items_areas, 
        board_area, 
        number_of_boards, 
        y_vars, 
        b_vars
    )

    all_items_must_be_on_a_board = create_all_items_must_be_on_a_board_constr(
        model, 
        items, 
        number_of_boards, 
        b_vars
    )

    symmetry_custs = create_symmetry_cuts_constr(
        model, 
        y_vars, 
        number_of_boards
    )


    inf_sol = {
        (1, 1): 1, (1, 2): 0, (1, 3): 0, (1, 4): 0,
        (2, 1): 1, (2, 2): 0, (2, 3): 0, (2, 4): 0,
        (3, 1): 1, (3, 2): 0, (3, 3): 0, (3, 4): 0,
        (4, 1): 1, (4, 2): 0, (4, 3): 0, (4, 4): 0
    }

    model._b_vars = b_vars

    constr_expr = create_feasibility_cut_expr_for_subproblem(model, 4, inf_sol)
    for expr in constr_expr.values():
        model.addConstr(expr)

    print_model(model)
