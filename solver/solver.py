import gurobipy as gp
import sys
from gurobipy import GRB
from model import *
import random
import simulator
import pandas as pd
import os
import scipy.spatial as scipy
import numpy as np

def solve_set_covering(problem: ProblemModel):
    node_count = len(problem.nodes)
    unit_count = len(problem.units)
    model = gp.Model('Fire_Surveillance_Model')
    risk_values = []
    if os.path.exists('./cachedvals'):
        print('Reading simulationo results from cache')
        risk_values = np.fromfile('./cachedvals')
    else:
        print("Calculating values thru simulation...")
        risk_values = simulator.calculate_burn_values(problem, 2.01, response_time=5)
        max_risk = max(risk_values) 
        risk_values = [r/max_risk for r in risk_values]
        risk_values = np.array(risk_values)
        risk_values = risk_values**2
        risk_values.tofile('./cachedvals')

    print('Initializing vars')
    is_assigned = model.addVars(node_count, unit_count, vtype=GRB.BINARY)
    risk_reduced = model.addVars(node_count)

    print('C1')
    xys = [(problem.nodes[i].x_coord, problem.nodes[i].y_coord) for i in range(node_count)]
    covering_rates = [[] for _ in range(node_count)]
    quadtree = scipy.KDTree(xys)
    for k in range(unit_count):
        if problem.units[k].inventory == 0:
            continue
        print(f'| Surveillance type {k}')
        min_range = problem.units[k].min_vision
        max_range = problem.units[k].max_vision
        nb_nodes = quadtree.query_pairs(max_range)
        for i, j in nb_nodes:
            covering_rates[i].append(problem.covering_rate(j, i, k)*is_assigned[j,k])
            covering_rates[j].append(problem.covering_rate(i, j, k)*is_assigned[i,k])

    for i in range(node_count):
        model.addConstr(
            risk_reduced[i] <= gp.quicksum(covering_rates[i])
                )
    print('C2')
    
    for i in range(node_count):
        node: Node = problem.nodes[i]
        model.addConstr(
            risk_reduced[i] <= node.risk_status
        )

    # no budget consts
    print('C3')
    for i in range(node_count):
        model.addConstr(
            gp.quicksum([is_assigned[i, k] for k in range(unit_count)]) <= int(problem.nodes[i].is_buildable == 'buildable')
        )
    print('C4')
    for k in range(unit_count):
        model.addConstr(
            gp.quicksum([is_assigned[i, k] for i in range(node_count)]) <= problem.units[k].inventory
        )
    print('Setting objective')
    model.setObjective(
        gp.quicksum([risk_values[i] * risk_reduced[i] for i in range(node_count)]),
        GRB.MAXIMIZE
    )

    model.setParam('MIPGap', 0.02)
    print('Starting to solve... Good luck!')
    model.optimize()

    if model.Status == GRB.INFEASIBLE:
        print("Model came out as infeasible, exiting...")
        sys.exit(1)

    node_results = []
    for i in range(node_count):
        node_results.append([i+1, risk_reduced[i].X, problem.nodes[i].risk_status, risk_values[i], problem.nodes[i].x_coord, problem.nodes[i].y_coord])
    node_df = pd.DataFrame(node_results, columns=['id', 'reduced_risk', 'total_risk', 'value_coeff', 'x_coord', 'y_coord'])

    unit_results = []
    for i in range(node_count):
        for k in range(unit_count):
            if is_assigned[i, k].X > 0.5:
                unit_results.append([problem.units[k].name, f'node_{i+1}', problem.nodes[i].x_coord, problem.nodes[i].y_coord])
    unit_df = pd.DataFrame(unit_results, columns=['unit_type', 'located_node_id', 'x_coord', 'y_coord'])

    with pd.ExcelWriter('results.xlsx', engine='xlsxwriter') as writer:
        unit_df.to_excel(writer, sheet_name="Built_Units", index=False)
        node_df.to_excel(writer, sheet_name="Nodes", index=False)