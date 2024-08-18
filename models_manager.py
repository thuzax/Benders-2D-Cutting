import os
import time
from gurobipy import *

################################################################################
# Auxiliaries functions starts below
################################################################################

def set_parameters(model, time_limit, log_path="", problem_type="standard"):
    '''Set Gurobi Parameters'''
    model.Params.TimeLimit = time_limit
    if (problem_type == "subproblem"):
        # model.Params.OutputFlag = 0
        model.Params.LogToConsole = 0
        return
    if (problem_type == "master_problem"):
        model.Params.LazyConstraints = 1
    
    # model.Params.TimeLimit = time_limit
    if (log_path != ""):
        model.Params.LogToConsole = 0
        model.Params.LogFile = log_path


def print_model(model):
    '''Print the model in lp format'''
    model.write("temp.lp")
    with open("temp.lp", "r") as f_model:
        text = f_model.read()
        print(text)
        os.remove("temp.lp")


def print_iis(model):
    '''Print the infeasible constraints in lp format'''
    model.write("iismodel.ilp")
    with open("iismodel.ilp", "r") as f_model:
        text = f_model.read()
        print(text)
        os.remove("iismodel.ilp")


def model_is_infeasible(model):
    '''True, if model is infeasible'''
    return model.status == GRB.INFEASIBLE

def feasible_not_found(model):
    '''True, if no solutions was found for the model optimization'''
    return (model.SolCount == 0)


def get_solution_dict(model):
    '''Create a dictionary with data related to a optimized model'''
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
    '''Create a dictionary with data related to a optimized MIP model'''
    data = get_solution_dict(model)
    data["gap"] = None
    if (data["is_optimal"] or "feasible_found"):
        data["gap"] = model.MIPGap
    data["cb_total_time"] = model._cb_total_time
    return data

################################################################################
# Variable creation functions starts below
################################################################################

def create_x_j_vars(model, items, bin_height, bin_width, j):
    '''Create the x variables for a bin. Standard and subproblem models only.'''

    # Variable name on gurobi
    x_vars_names = {}
    # Variable key (i, j, l, w)
    x_vars_keys = {}
    # List of keys of the variables of bin j
    x_of_bin_vars_key = []
    # Dictionary of variables. Format -> {(i,j,l,w) : variable}
    x_vars = {}
    
    # Create each variable for each item and each possible (l,w) point
    for i in items.keys():
        for l in range(bin_width - items[i]["width"] + 1):
            for w in range(bin_height - items[i]["height"] + 1):
                var_name = (
                    "x_" 
                    + str(items[i]["id"]) + "_" 
                    + str(j) + "_" 
                    + str(l) + "_" 
                    + str(w)
                )
                x_of_bin_vars_key.append((i, j, l, w))
                x_vars_keys[i,j,l,w] = (i,j,l,w)
                x_vars_names[i,j,l,w] = var_name
                x_vars[i,j,l,w] = model.addVar(
                    name=var_name,
                    vtype=GRB.BINARY
                )

    return (x_vars_names, x_vars_keys, x_of_bin_vars_key, x_vars)


def create_x_vars(model, items, bin_height, bin_width, number_of_bins):
    '''Create the x variables for each bin. Standar model only.'''
    # Variable name on gurobi
    x_vars_names = {}
    # Variable key (i, j, l, w)
    x_vars_keys = {}
    # Dictionary containing the lists of keys of the variables of each bin j
    x_of_bin_vars_keys = {}
    # Dictionary of variables. Format -> {(i,j,l,w) : variable}
    x_vars = {}

    # Create the x variables for each bin j
    for j in range(1, number_of_bins+1):
        vars_data = create_x_j_vars(model, items, bin_height, bin_width, j)
        
        # Join the returned dictionaries
        x_vars_names |= vars_data[0]
        x_vars_keys |= vars_data[1]
        x_of_bin_vars_keys[j] = vars_data[2]
        x_vars |= vars_data[3]


    return (x_vars_names, x_vars_keys, x_of_bin_vars_keys, x_vars)


def create_z_vars(model, number_of_bins):
    '''Create the z variables for each bin. Standard and Master models only.'''
    # Variable name on gurobi
    z_vars_names = {}
    # Dictionary of variables. Format -> {j : variable}
    z_vars = {}

    for j in range(1, number_of_bins+1):
        var_name = "z_" + str(j)
        z_vars_names[j] = var_name
        z_vars[j] = model.addVar(name=var_name, vtype=GRB.BINARY)
    return (z_vars_names, z_vars)


def create_b_vars(model, items, number_of_bins):
    '''Create master b variables. Master model only.'''

    # Variable name on gurobi
    b_vars_names = {}
    # Dictionary of variables. Format -> {(i,j) : variable}
    b_vars = {}
    
    for i in items.keys():
        for j in range(1, number_of_bins+1):
            var_name = "b_" + str(i) + "_" + str(j)
            b_vars_names[i, j] = var_name
            b_vars[i, j] = model.addVar(name=var_name, vtype=GRB.BINARY)
    return (b_vars_names, b_vars)

################################################################################
# Constraints creation functions starts below
################################################################################


def create_standard_bin_not_used_constr(
    model, 
    items,
    number_of_bins,
    bin_width,
    bin_height,
    x_vars,
    z_vars
):
    '''Cutting constraints to avoid that a bin is used without any item being allocated to it. Standard model only.'''
    
    constr = {}
    
    # For each bin, create a costraint 
    # \sum_{i = 1}^{m}{\sum_{l \in X}{\sum_{w \in Y}{x_{i,j,l,w}} \geq z_{j}
    for j in range(1, number_of_bins+1):
        constr[j] = model.addConstr(
            quicksum(
                quicksum(
                    quicksum(
                        x_vars[i,j,l,w]
                        for w in range(bin_height - items[i]["height"] + 1)
                    )
                    for l in range(bin_width - items[i]["width"] + 1)
                )
                for i in items.keys()
            )
            >=
            z_vars[j],
            name="standard_bin_not_used_constr_" + str(j)
        )
    
    return constr


def create_bin_overlapping_constr(
    model, 
    bin_width,
    bin_height,
    j,
    keys,
    x_vars,
    z,
    point_is_cutted
):
    '''Create the overlapping constraint for a bin j. Standard and subproblem models only.'''

    constr = {}
    # For bin j, for each r \in bin_width, for each s \in bin_height
    # \sum_{i = 1}^{m}{\sum_{l \in X}{\sum_{w \in Y}{a_{i,l,w,r,s} * x_{i,j,l,w}} \leq z_{j}
    for r in range(bin_width):
        for s in range(bin_height):
            # Create a list with all variables of the constraint
            vars_constr = []
            for k in keys:
                i, c, l, w = k
                if ((i, l, w, r, s) in point_is_cutted):
                    vars_constr.append(x_vars[i, j, l, w])
            # If there is at least one variable, create constraint
            if (len(vars_constr) > 0):
                constr[j,r,s] = model.addConstr(
                    quicksum(vars_constr) <= z,
                    name=(
                        "bin_overlapping_constr_" 
                        + str(j) + "_" 
                        + str(r) + "_" 
                        + str(s)
                    )
                )
    return constr


def create_overlapping_constr(
    model, 
    bin_width,
    bin_height,
    x_vars,
    x_of_bin_vars_keys,
    z_vars,
    point_is_cutted
):
    '''Create the overlapping constraint for each bin. Standard model only.'''
    overlapping_constrs = {}
    
    # For each bin j, create an overlapping constraint
    for j, keys in x_of_bin_vars_keys.items():
        overlapping_constrs |= create_bin_overlapping_constr(
            model, 
            bin_width, 
            bin_height,
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
    '''For each item create a constraint to force its allocation. Standard and subproblem models only.'''
    must_be_allocated_constrs = {}

    for i in items.keys():
        # Create a list with all variables of the constraint
        items_for_constr = []
        for key in x_vars.keys():
            if (key[0] == i):
                items_for_constr.append(x_vars[key])
        
        # Create constraint
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
    bin_area,
    x_vars,
    x_of_bin_vars_keys
):
    '''Create a constraint to limit the area of the allocated items. Standard model only.'''
    constr = {}

    for j, x_j_vars_keys in x_of_bin_vars_keys.items():
        # Create a list with all variables of the constraint
        constr_vars = []
        for key in x_j_vars_keys:
            i, j, l, w = key
            constr_vars.append(items_areas[i] * x_vars[key])
        # Create constraint
        constr[j] = model.addConstr(
            quicksum(constr_vars) 
            <= 
            bin_area,
            "item_area_constr_" + 
            str(j)
        )
    
    return constr

def create_symmetry_cuts_constr(
    model,
    z_vars,
    number_of_bins
):
    '''Create symmetry cuts for the bins: z_{j-1} <= z_{j}. Standard and Master models only.'''
    constr = {}
    for j in range(2, number_of_bins+1):
        constr[j-1, j] = model.addConstr(
            z_vars[j-1] >= z_vars[j],
            name="symmetry_cut_" + str(j-1) + "_" + str(j)
        )
    return constr


def create_item_bin_allocation_constr(
    model,
    items,
    items_areas,
    bin_area,
    number_of_bins,
    z_vars,
    b_vars
):
    '''Create a constraint to force z_{j} = 1 if b_{ij} = 1. Master model only.'''
    constr = {}
    for j in range(1, number_of_bins+1):
        constr[j] = model.addConstr(
            quicksum(items_areas[i] * b_vars[i,j] for i in items.keys()) 
            <= 
            bin_area * z_vars[j],
            name="item_bin_allocation_" + str(j)
        )
    return constr


def create_bin_not_used_constr(
    model,
    items,
    number_of_bins,
    b_vars,
    z_vars
):
    '''Create a constraint to force z_{j} = 0 if all b_{ij} are 0. Master model only.'''

    bin_not_used = {}

    for j in range(1, number_of_bins+1):
        bin_not_used[j] = model.addConstr(
            quicksum(
                b_vars[i, j]
                for i in items.keys()
            )
            >=
            z_vars[j],
            name=(
                "bin_not_used_constr_" 
                + str(j)
            )
        )
    
    return bin_not_used

def create_all_items_must_be_on_a_bin_constr(
    model,
    items,
    number_of_bins,
    b_vars
):
    '''For each item create a constraint to force its allocation. Master model only.'''
    constr = {}
    for i in items.keys():
        constr[i] = model.addConstr(
            quicksum(b_vars[i,j] for j in range(1, number_of_bins+1)) == 1,
            name="all_items_must_be_on_a_bin_" + str(i)
        )
    return constr

################################################################################
# Callback related functions starts below
################################################################################

def create_feasibility_cut_expr_for_j(
    model, 
    j,
    subproblem_inf_sol
):
    '''Create the expression of a feasibility cut for a bin j'''
    
    # Create a dictionary for the variables b[i,j] with b*[i,j] = 1, where 
    # b*[i,j] is the previous solution value
    allocated_bins = {}
    for key, b_var in subproblem_inf_sol.items():
        if (b_var > 0.5):
            i, k = key
            allocated_bins[i, j] = model._b_vars[i, j]

    # Create constraint expression
    constr_expr = {}
    constr_expr[j] = (
        quicksum(
            1 - allocated_bins[key] 
            for key in allocated_bins.keys()
        ) 
        >= 
        1
    )
    
    return constr_expr

def create_feasibility_cut_expr_for_subproblem(
    model, 
    number_of_bins,
    subproblem_inf_sol
):
    '''Create the expressions of the feasibility cuts with the infeasible solution of a subproblem. The cut is created for each bin, since they are homogeneous. '''
    constr_expr = {}
    for j in range(1, number_of_bins+1):
        constr_expr |= create_feasibility_cut_expr_for_j(
            model, 
            j, 
            subproblem_inf_sol
        )
    return constr_expr


def solve_subproblem_j(
    j, 
    items, 
    bin_height, 
    bin_width, 
    point_is_cutted,
    b_values,
    model,
    cb_start_time
):
    '''Solve the subproblem of bin j'''

    # If there is no item allocated on bin j, then there is no problem
    if (len(items) <= 0):
        # print("Not allocated in bin " + str(j))
        return {"feasible" : {}, "infeasible" : {}}
    
    # Create model
    subproblem_model = create_subproblem(
        j, 
        items, 
        bin_height, 
        bin_width, 
        point_is_cutted, 
        "subproblem_" + str(j),
        1
    )
    
    print(model.Params.TimeLimit - model.cbGet(GRB.Callback.RUNTIME))

    if (model.Params.TimeLimit - model.cbGet(GRB.Callback.RUNTIME) <= 0):
        model.terminate()
        model._subproblems_incomplete = True
        return {"feasible" : {}, "infeasible" : {}}


    subproblem_model.optimize()
    
    # If it is infeasible, get the variables b[i, j], that is, the value of the 
    # variables that indicate wheter an item i was allocated on bin j. 
    # This is used to create the feasibility cut
    if (subproblem_model.status == GRB.INFEASIBLE):
        subproblem_inf = {}
        for i in items.keys():
            subproblem_inf[i, j] = b_values[i, j]
        return {"feasible" : {}, "infeasible" : subproblem_inf}
    
    if (feasible_not_found(subproblem_model)):
        model.terminate()
        model._subproblems_incomplete = True
        return {"feasible" : {}, "infeasible" : {}}
    # If there is a solution, then create a dictionary with the solutions
    subproblem_solution = {
        var.VarName : var.x 
        for var in subproblem_model.getVars()
    }

    return {"feasible" : subproblem_solution, "infeasible" : {}}


def solve_subproblems(
    all_items,
    number_of_bins,
    bin_height,
    bin_width,
    point_is_cutted,
    b_values,
    model,
    cb_start_time
):
    '''Solve the subproblem of each bin'''
    
    subproblems_sol = {"infeasible" : {}, "feasible" : {}}
    # For each subproblem
    for j in range(1, number_of_bins+1):
        # Create a dictionary with the items allocated on the bin (an item is 
        # allocated if b[i,j] is 1)
        items = {
            i : item
            for i, item in all_items.items()
            if (b_values[i, j] > 0.5)
        }
        
        # Solve subproblem
        solutions = solve_subproblem_j(
            j, 
            items,
            bin_height,
            bin_width,
            point_is_cutted,
            b_values,
            model,
            cb_start_time
        )

        # If solution is feasible, store as a feasible solution
        if (len(solutions["feasible"]) > 0):
            subproblems_sol["feasible"][j] = solutions["feasible"]
        # If solution is infeasible, store as an infeasible solution
        if (len(solutions["infeasible"]) > 0):
            subproblems_sol["infeasible"][j] = solutions["infeasible"]

    # Return the feasible and infeasible solutions
    return subproblems_sol


def add_benders_cuts(
    model,
    subproblems_inf
):
    '''Create a benders cut for each infeasible subproblem'''
    
    # For each infeasible subproblem
    for j in subproblems_inf.keys():
        if (len(subproblems_inf[j]) == 0):
            continue
        # Create the feasibility cut for the subproblem for each bin
        feasibility_cuts_expr = create_feasibility_cut_expr_for_subproblem(
            model, 
            model._number_of_bins,
            subproblems_inf[j]
        )
        # add lazy constraints
        for expr in feasibility_cuts_expr.values():
            model.cbLazy(expr)
            model._lazy_set.add(expr)


def master_call_back(model, where):
    '''Callback for master problem. Create a subproblem for each bin and add feasibility cuts for each infeasible subproblem solution.'''
    if where == GRB.Callback.MIPSOL:
        try:
            cb_start_time = time.time()

            # Get variables values of current solution
            b_values = model.cbGetSolution(model._b_vars)
            z_values = model.cbGetSolution(model._z_vars)
            
            # Solve the subproblems
            subproblems_sol = solve_subproblems(
                model._items,
                model._number_of_bins,
                model._bin_height,
                model._bin_width,
                model._point_is_cutted,
                b_values,
                model,
                cb_start_time
            )

            if (model._subproblems_incomplete):
                return

            # If there is at least one infeasible solution, then add benders monotone no good cuts
            if (len(subproblems_sol["infeasible"]) > 0):
                add_benders_cuts(
                    model,
                    subproblems_sol["infeasible"],
                )
            # Otherwise, get store the values of the feasible solution of the subproblem
            else:
                model._x_vars = {}
                for j, solutions_vars in subproblems_sol["feasible"].items():
                    model._x_vars |= solutions_vars
            model._cb_total_time += time.time() - cb_start_time
        except Exception as ex:
            # Terminate model if an error occurs
            model.terminate()
            raise ex



################################################################################
# Model creation related functions starts below
################################################################################


def create_standard_model(
    items, 
    bin_height, 
    bin_width, 
    items_areas,
    bin_area,
    point_is_cutted, 
    number_of_bins,
    model_name,
    log_path,
    time_limit
):
    '''Create standard model, that is, the complete model.'''
    
    model = Model(name=model_name)
    
    # Create variables
    x_vars_names, x_vars_keys, x_of_bin_vars_keys, x_vars = create_x_vars(
        model, items, bin_height, bin_width, number_of_bins
    )
    z_vars_names, z_vars = create_z_vars(
        model, number_of_bins
    )

    # Create objective function as sum_{j \in P}{j * z_{j}}
    model.setObjective(
        quicksum(j * z_vars[j] for j in range(1, len(z_vars)+1)),
        sense=GRB.MINIMIZE
    )

    # Create constraints

    overlapping_constrs = create_overlapping_constr(
        model, 
        bin_width,
        bin_height,
        x_vars,
        x_of_bin_vars_keys,
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
        bin_area, 
        x_vars, 
        x_of_bin_vars_keys
    )

    symmetry_custs = create_symmetry_cuts_constr(model, z_vars, number_of_bins)

    bins_not_used = create_standard_bin_not_used_constr(
        model,
        items,
        number_of_bins,
        bin_width,
        bin_height,
        x_vars,
        z_vars
    )

    model._cb_total_time = 0
    set_parameters(model, time_limit=time_limit, log_path=log_path)

    return model


def create_subproblem(
    j,
    items, 
    bin_height, 
    bin_width, 
    point_is_cutted, 
    model_name,
    time_limit
):
    '''Create a subproblem model.'''
    model = Model(name=model_name)

    # Create variables
    x_vars_names, x_vars_keys, x_of_bin_vars_keys, x_vars = create_x_j_vars(
        model, items, bin_height, bin_width, j
    )
    # Create objective function as 0, since it is an feasiblity problem
    model.setObjective(
        0,
        sense=GRB.MINIMIZE
    )

    # Create constraints
    overlapping_constrs = create_bin_overlapping_constr(
        model, 
        bin_width, 
        bin_height, 
        j, 
        x_of_bin_vars_keys, 
        x_vars, 
        1, 
        point_is_cutted 
    )

    must_be_allocated_constrs = create_all_items_must_be_allocated_constr(
        model,
        items,
        x_vars
    )

    set_parameters(model, time_limit=time_limit, problem_type="subproblem")
    return model

def create_master_problem(
    items, 
    bin_height, 
    bin_width, 
    items_areas,
    bin_area,
    point_is_cutted, 
    number_of_bins,
    model_name,
    log_path, 
    time_limit
):
    '''Create a Benders master model'''
    model = Model(name=model_name)
    

    # Create variables
    z_vars_names, z_vars = create_z_vars(
        model, number_of_bins
    )
    b_vars_names, b_vars = create_b_vars(model, items, number_of_bins)

    # Create objective function as sum_{j \in P}{j * z_{j}}
    model.setObjective(
        quicksum(j * z_vars[j] for j in range(1, len(z_vars)+1)),
        sense=GRB.MINIMIZE
    )

    # Create constraints
    item_bin_allocation = create_item_bin_allocation_constr(
        model, 
        items, 
        items_areas, 
        bin_area, 
        number_of_bins, 
        z_vars, 
        b_vars
    )

    all_items_must_be_on_a_bin = create_all_items_must_be_on_a_bin_constr(
        model, 
        items, 
        number_of_bins, 
        b_vars
    )

    symmetry_custs = create_symmetry_cuts_constr(
        model, 
        z_vars, 
        number_of_bins
    )

    bin_not_used = create_bin_not_used_constr(
        model,
        items,
        number_of_bins,
        b_vars,
        z_vars
    )

    # Create params and variables used on callback

    # problem params
    model._number_of_bins = number_of_bins
    # subproblem params
    model._items = items
    model._bin_height = bin_height
    model._bin_width = bin_width
    model._point_is_cutted = point_is_cutted

    # master variables
    model._b_vars = b_vars
    model._z_vars = z_vars

    # Lazy constraints set
    model._lazy_set = set()
    # total time spent on callback
    model._cb_total_time = 0

    model._subproblems_incomplete = False
    model._x_vars = {}

    set_parameters(
        model, 
        time_limit=time_limit, 
        log_path=log_path,
        problem_type="master_problem"
    )

    return model
