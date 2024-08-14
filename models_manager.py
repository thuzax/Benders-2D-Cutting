import os
import time
from gurobipy import *

def set_parameters(model, log_path="", problem_type="standard"):
    if (problem_type == "subproblem"):
        # model.Params.OutputFlag = 0
        # model.Params.LogToConsole = 0
        return
    if (problem_type == "master_problem"):
        model.Params.LazyConstraints = 1
    
    model.Params.TimeLimit = 900
    if (log_path != ""):
        model.Params.LogToConsole = 0
        model.Params.LogFile = log_path


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


def model_is_infeasible(model):
    return model.status == GRB.INFEASIBLE

def feasible_not_found(model):
    return (model.SolCount == 0)

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


    return (x_vars_names, x_vars_keys, x_of_board_vars_keys, x_vars)


def create_z_vars(model, number_of_boards):
    z_vars_names = {}
    z_vars = {}
    for j in range(1, number_of_boards+1):
        var_name = "z_" + str(j)
        z_vars_names[j] = var_name
        z_vars[j] = model.addVar(name=var_name, vtype=GRB.BINARY)
    return (z_vars_names, z_vars)


def create_standard_board_not_used_constr(
    model, 
    items,
    number_of_boards,
    board_width,
    board_height,
    x_vars,
    z_vars
):
    constr = {}
    
    for j in range(1, number_of_boards+1):
        constr[j] = model.addConstr(
            quicksum(
                quicksum(
                    quicksum(
                        x_vars[i,j,l,w]
                        for w in range(board_height - items[i]["height"] + 1)
                    )
                    for l in range(board_width - items[i]["width"] + 1)
                )
                for i in items.keys()
            )
            >=
            z_vars[j],
            name="standard_board_not_used_constr_" + str(j)
        )
    
    return constr


def create_board_overlapping_constr(
    model, 
    board_width,
    board_height,
    j,
    keys,
    x_vars,
    z,
    point_is_cutted
):
    constr = {}
    for r in range(board_width):
        for s in range(board_height):
            vars_constr = []
            for k in keys:
                i, c, l, w = k
                if ((i, l, w, r, s) in point_is_cutted):
                    vars_constr.append(x_vars[i, j, l, w])
            if (len(vars_constr) > 0):
                constr[j,r,s] = model.addConstr(
                    quicksum(vars_constr) <= z,
                    name=(
                        "board_overlapping_constr_" 
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
    z_vars,
    point_is_cutted
):
    overlapping_constrs = {}
    
    for j, keys in x_of_board_vars_keys.items():
        overlapping_constrs |= create_board_overlapping_constr(
            model, 
            board_width, 
            board_height,
            j,
            keys,
            x_vars,
            z_vars[j],
            point_is_cutted
        )

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
    z_vars,
    number_of_boards
):
    constr = {}
    for j in range(2, number_of_boards+1):
        constr[j-1, j] = model.addConstr(
            z_vars[j-1] >= z_vars[j],
            name="symmetry_cut_" + str(j-1) + "_" + str(j)
        )
    return constr


def create_item_board_allocation_constr(
    model,
    items,
    items_areas,
    board_area,
    number_of_boards,
    z_vars,
    b_vars
):
    constr = {}
    for j in range(1, number_of_boards+1):
        constr[j] = model.addConstr(
            quicksum(items_areas[i] * b_vars[i,j] for i in items.keys()) 
            <= 
            board_area * z_vars[j],
            name="item_board_allocation_" + str(j)
        )
    return constr


def create_board_not_used_constr(
    model,
    items,
    number_of_boards,
    b_vars,
    z_vars
):
    board_not_used = {}

    for j in range(1, number_of_boards+1):
        board_not_used[j] = model.addConstr(
            quicksum(
                b_vars[i, j]
                for i in items.keys()
            )
            >=
            z_vars[j],
            name=(
                "board_not_used_constr_" 
                + str(j)
            )
        )
    
    return board_not_used

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





















def create_standard_model(
    items, 
    board_height, 
    board_width, 
    items_areas,
    board_area,
    point_is_cutted, 
    number_of_boards,
    model_name,
    log_path
):
    model = Model(name=model_name)
    set_parameters(model, log_path)
    
    x_vars_names, x_vars_keys, x_of_board_vars_keys, x_vars = create_x_vars(
        model, items, board_height, board_width, number_of_boards
    )
    z_vars_names, z_vars = create_z_vars(
        model, number_of_boards
    )

    model.setObjective(
        quicksum(j * z_vars[j] for j in range(1, len(z_vars)+1)),
        sense=GRB.MINIMIZE
    )

    
    overlapping_constrs = create_overlapping_constr(
        model, 
        board_width,
        board_height,
        x_vars,
        x_of_board_vars_keys,
        z_vars,
        point_is_cutted
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

    symmetry_custs = create_symmetry_cuts_constr(model, z_vars, number_of_boards)

    boards_not_used = create_standard_board_not_used_constr(
        model,
        items,
        number_of_boards,
        board_width,
        board_height,
        x_vars,
        z_vars
    )

    model._cb_total_time = 0

    return model


def create_subproblem(
    j,
    items, 
    board_height, 
    board_width, 
    point_is_cutted, 
    model_name
):
    
    model = Model(name=model_name)
    set_parameters(model, problem_type="subproblem")

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
        point_is_cutted 
    )

    must_be_allocated_constrs = create_all_items_must_be_allocated_constr(
        model,
        items,
        x_vars
    )

    return model

def create_master_problem(
    items, 
    board_height, 
    board_width, 
    items_areas,
    board_area,
    point_is_cutted, 
    number_of_boards,
    model_name,
    log_path
):
    
    model = Model(name=model_name)
    set_parameters(model, log_path, "master_problem")

    z_vars_names, z_vars = create_z_vars(
        model, number_of_boards
    )

    b_vars_names, b_vars = create_b_vars(model, items, number_of_boards)

    model.setObjective(
        quicksum(j * z_vars[j] for j in range(1, len(z_vars)+1)),
        sense=GRB.MINIMIZE
    )

    item_board_allocation = create_item_board_allocation_constr(
        model, 
        items, 
        items_areas, 
        board_area, 
        number_of_boards, 
        z_vars, 
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
        z_vars, 
        number_of_boards
    )

    board_not_used = create_board_not_used_constr(
        model,
        items,
        number_of_boards,
        b_vars,
        z_vars
    )

    # problem params
    model._number_of_boards = number_of_boards
    # subproblem params
    model._items = items
    model._board_height = board_height
    model._board_width = board_width
    model._point_is_cutted = point_is_cutted

    # master variables
    model._b_vars = b_vars
    model._z_vars = z_vars

    # Lazy constraints set
    model._lazy_set = set()
    # total time spent on callback
    model._cb_total_time = 0

    return model


def solve_subproblem_j(
    j, 
    items, 
    board_height, 
    board_width, 
    point_is_cutted,
    b_values
):
    if (len(items) <= 0):
        # print("Not allocated in board " + str(j))
        return {"feasible" : {}, "infeasible" : {}}
    

    subproblem_model = create_subproblem(
        j, 
        items, 
        board_height, 
        board_width, 
        point_is_cutted, 
        "subproblem_" + str(j)
    )
    
    subproblem_model.optimize()
    
    if (subproblem_model.status == GRB.INFEASIBLE):
        subproblem_inf = {}
        for i in items.keys():
            subproblem_inf[i, j] = b_values[i, j]
        return {"feasible" : {}, "infeasible" : subproblem_inf}
    
    subproblem_solution = {
        var.VarName : var.x 
        for var in subproblem_model.getVars()
    }

    return {"feasible" : subproblem_solution, "infeasible" : {}}


def solve_subproblems(
    all_items,
    number_of_boards,
    board_height,
    board_width,
    point_is_cutted,
    b_values
):
    subproblems_sol = {"infeasible" : {}, "feasible" : {}}

    for j in range(1, number_of_boards+1):
        items = {
            i : item
            for i, item in all_items.items()
            if (b_values[i, j] > 0.5)
        }
        solutions = solve_subproblem_j(
            j, 
            items,
            board_height,
            board_width,
            point_is_cutted,
            b_values
        )
        if (len(solutions["feasible"]) > 0):
            subproblems_sol["feasible"][j] = solutions["feasible"]
        if (len(solutions["infeasible"]) > 0):
            subproblems_sol["infeasible"][j] = solutions["infeasible"]
    
    return subproblems_sol

def add_benders_cuts(
    model,
    subproblems_inf
):
    
    for j in subproblems_inf.keys():
        if (len(subproblems_inf[j]) == 0):
            continue
        feasibility_cuts_expr = create_feasibility_cut_expr_for_subproblem(
            model, 
            model._number_of_boards,
            subproblems_inf[j]
        )
        for expr in feasibility_cuts_expr.values():
            model.cbLazy(expr)
            model._lazy_set.add(expr)


def master_call_back(model, where):
    if where == GRB.Callback.MIPSOL:
        try:
            cb_start_time = time.time()
            b_values = model.cbGetSolution(model._b_vars)
            z_values = model.cbGetSolution(model._z_vars)
            
            subproblems_sol = solve_subproblems(
                model._items,
                model._number_of_boards,
                model._board_height,
                model._board_width,
                model._point_is_cutted,
                b_values
            )            
            
            if (len(subproblems_sol["infeasible"]) > 0):
                add_benders_cuts(
                    model,
                    subproblems_sol["infeasible"],
                )
            else:
                model._x_vars = {}
                for j, solutions_vars in subproblems_sol["feasible"].items():
                    model._x_vars |= solutions_vars
            model._cb_total_time += time.time() - cb_start_time
        except Exception as ex:
            model.terminate()
            raise ex



def get_solution_dict(model):
    data = {
        "variables": None,
        "objective": None,
        "is_optimal": False,
        "inf_or_unb": False,
        "feasible_found": False,
        "node_count": None,
        "total_time": None
    }
    data["total_time"] = model.Runtime

    if (model.status == GRB.INFEASIBLE):
        data["inf_or_unb"] = True
        return data
    
    if (model.status == GRB.UNBOUNDED):
        data["inf_or_unb"] = True
        return data

    data["node_count"] = model.NodeCount

    if (model.SolCount == 0):
        return data
    

    data["variables"] = {}
    for v in model.getVars():
        data["variables"][v.VarName] = v.X

    if (model.status == GRB.OPTIMAL):
        data["is_optimal"] = True

    data["feasible_found"] = True
    data["objective"] = model.getObjective().getValue()
    data["dual_bound"] = model.ObjBound

    return data


def get_solution_dict_MIP(model):
    data = get_solution_dict(model)
    data["gap"] = None
    if (data["is_optimal"] or "feasible_found"):
        data["gap"] = model.MIPGap
    data["cb_total_time"] = model._cb_total_time
    return data