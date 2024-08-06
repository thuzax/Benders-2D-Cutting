from gurobipy import *

def create_model(model_name="MODEL"):
    return Model(name=model_name)
