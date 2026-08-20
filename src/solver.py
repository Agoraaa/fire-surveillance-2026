import gurobipy as gp
import sys
from gurobipy import GRB
from model import *
import simulator
import pandas as pd
import os
import scipy.spatial as scipy
import numpy as np
import math
import time

def solve_set_covering(problem: ProblemModel, output_file, epsilon = -1):
    node_count = len(problem.nodes)
    unit_count = len(problem.units)
    model = gp.Model('Fire_Surveillance_Model')
    cache_path = os.path.splitext(output_file)[0] + '_cachedvals'
    risk_values = []
    simulation_time_sec = 0
    if os.path.exists(cache_path):
        print('Reading simulation results from cache')
        risk_values = np.fromfile(cache_path)
    else:
        print("Calculating values thru simulation...")
        sim_start = time.time()
        risk_values = simulator.calculate_burn_values(problem, 1.5, response_time=5)
        simulation_time_sec = time.time() - sim_start
        max_risk = max(risk_values)
        risk_values = np.array([r/max_risk for r in risk_values])
        risk_values.tofile(cache_path)

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
    
    if 0:
        print('C5')
        minimum_stayaway_dist = 15
        nb_nodes = quadtree.query_pairs(minimum_stayaway_dist/2)
        nbs = [[] for i in range(node_count)]
        for surv_type in range(unit_count):
            for i in range(node_count):
                nbs[i].append(is_assigned[i, surv_type])
            for i, j in nb_nodes:
                nbs[i].append(is_assigned[j, surv_type])
                nbs[j].append(is_assigned[i, surv_type])
            for clique in nbs:
                model.addConstr(
                    gp.quicksum(clique) <= 1
                )

    print('Adding minimum covering rate')
    eps = model.addVar()
    for i in range(node_count):
        if problem.nodes[i].risk_status > 0:
            model.addConstr(
                eps <= gp.quicksum(covering_rates[i])
            )

    if epsilon != -1:
        model.addConstr(eps >= epsilon)
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

    summary_df = pd.DataFrame([{
        'solve_time_sec': model.Runtime,
        'simulation_time_sec': simulation_time_sec,
        'objective_value': model.ObjVal,
        'mip_gap': model.MIPGap,
        'simulation_value_mean': float(np.mean(risk_values)),
        'simulation_value_var': float(np.var(risk_values)),
    }])

    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        unit_df.to_excel(writer, sheet_name="Built_Units", index=False)
        node_df.to_excel(writer, sheet_name="Nodes", index=False)
        summary_df.to_excel(writer, sheet_name="Summary", index=False)

def solve_probabilistic(problem: ProblemModel, output_file, time_limit_sec=600):
    node_count = len(problem.nodes)
    unit_count = len(problem.units)
    model = gp.Model('Fire_Surveillance_Model')
    cache_path = os.path.splitext(output_file)[0] + '_cachedvals'
    importances = []
    raw_importances = None
    simulation_time_sec = 0
    if os.path.exists(cache_path):
        print('Reading simulation results from cache')
        importances = np.fromfile(cache_path)
    else:
        print("Calculating values through simulation...")
        sim_start = time.time()
        raw_importances = np.array(simulator.calculate_burn_values(problem, 5, response_time=5))
        simulation_time_sec = time.time() - sim_start
        max_importance = raw_importances.max()
        importances = (raw_importances / max_importance)
        importances.tofile(cache_path)
        print(f'Simulation calculated in {time.time() - sim_start} seconds')

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
            covering_rates[i].append((problem.covering_rate(j, i, k), is_assigned[j,k]))
            covering_rates[j].append((problem.covering_rate(i, j, k), is_assigned[i,k]))
        for i in range(node_count):
            covering_rates[i].append((1, is_assigned[i,k]))


    for i in range(node_count):
        detection_chances = [t[0] for t in covering_rates[i]]
        detection_dv = [t[1] for t in covering_rates[i]]
        log_chances = [0] * len(detection_chances)
        for j in range(len(log_chances)):
            if detection_chances[j] > 0.99:
                log_chances[j] = -20
            else:
                log_chances[j] = math.log(1-detection_chances[j])
        exp = model.addVar(lb= float('-inf'),ub=0)
        probability_not_catching = model.addVar(ub=1)
        breakpoints = [-10, -2, -0.8, -0.5, -0.3, 0]
        y_points = [math.exp(p) for p in breakpoints]
        y_points[0] = 0
        model.addConstr(sum([ci*dv for ci, dv in zip(log_chances, detection_dv)]) <= exp)
        model.addGenConstrPWL(exp, probability_not_catching, breakpoints, y_points)
        model.addConstr(
            risk_reduced[i] == (1-probability_not_catching) * problem.nodes[i].risk_status
                )
    
    
    print('C2')
    for i in range(node_count):
        model.addConstr(risk_reduced[i] <= problem.nodes[i].risk_status)

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

    print('Warm start')
    prev_assignments = {}
    fname = os.path.basename(output_file)
    out_dir = os.path.dirname(output_file)
    unit_level_tag = next((f'-{l}U-' for l in ['low', 'mid', 'high'] if f'-{l}U-' in fname), None)
    if unit_level_tag:
        for candidate in sorted(os.listdir(out_dir)):
            if candidate == fname or not candidate.endswith('_output.xlsx'):
                continue
            if unit_level_tag not in candidate:
                continue
            candidate_path = os.path.join(out_dir, candidate)
            print(f'  Using {candidate} as warm start')
            prev_df = pd.read_excel(candidate_path, sheet_name='Built_Units')
            unit_name_to_k = {problem.units[k].name: k for k in range(unit_count)}
            for _, row in prev_df.iterrows():
                node_idx = int(row['located_node_id'].split('_')[1]) - 1
                k = unit_name_to_k.get(row['unit_type'])
                if k is not None:
                    prev_assignments[(node_idx, k)] = 1
            break

    buildable = [i for i in range(node_count) if problem.nodes[i].is_buildable == 'buildable']
    scores = [importances[i] * problem.nodes[i].risk_status for i in range(node_count)]
    for k in range(unit_count):
        already_assigned = {i for (i, kk) in prev_assignments if kk == k}
        remaining_inventory = problem.units[k].inventory - len(already_assigned)
        candidates = [i for i in buildable if i not in already_assigned]
        greedy_nodes = set(sorted(candidates, key=lambda i: scores[i], reverse=True)[:max(0, remaining_inventory)])
        for i in range(node_count):
            is_assigned[i, k].Start = 1 if i in already_assigned | greedy_nodes else 0

    print('Setting objective')
    model.setObjective(
        gp.quicksum([importances[i] * risk_reduced[i] for i in range(node_count)]),
        GRB.MAXIMIZE
    )
    model.setParam('TimeLimit', time_limit_sec)
    #model.setParam('MIPGap', 0.02)

    print('Starting to solve... Good luck!')
    model.optimize()

    if model.Status == GRB.INFEASIBLE:
        print("Model came out as infeasible, exiting...")
        sys.exit(1)

    node_results = []
    for i in range(node_count):
        node_results.append([i+1, risk_reduced[i].X, problem.nodes[i].risk_status, importances[i], problem.nodes[i].x_coord, problem.nodes[i].y_coord])
    node_df = pd.DataFrame(node_results, columns=['id', 'reduced_risk', 'total_risk', 'value_coeff', 'x_coord', 'y_coord'])

    unit_results = []
    for i in range(node_count):
        for k in range(unit_count):
            if is_assigned[i, k].X > 0.5:
                unit_results.append([problem.units[k].name, f'node_{i+1}', problem.nodes[i].x_coord, problem.nodes[i].y_coord])
    unit_df = pd.DataFrame(unit_results, columns=['unit_type', 'located_node_id', 'x_coord', 'y_coord'])

    risk_statuses = np.array([problem.nodes[i].risk_status for i in range(node_count)])
    reduced_risks = np.array([risk_reduced[i].X for i in range(node_count)])

    if raw_importances is not None:
        max_importance = raw_importances.max()
        unscaled = raw_importances
        best_score_unscaled = float((unscaled * risk_statuses).sum())
        objective_unscaled = float((unscaled * reduced_risks).sum())
    else:
        best_score_unscaled = None
        objective_unscaled = None

    summary_df = pd.DataFrame([{
        'solve_time_sec': model.Runtime,
        'simulation_time_sec': simulation_time_sec,
        'objective_value': model.ObjVal,
        'mip_gap': model.MIPGap,
        'simulation_value_mean': float(np.mean(importances)),
        'simulation_value_var': float(np.var(importances)),
        'simulation_value_mean_unscaled': float(np.mean(raw_importances)) if raw_importances is not None else None,
        'simulation_value_var_unscaled': float(np.var(raw_importances)) if raw_importances is not None else None,
        'best_score': float((importances * risk_statuses).sum()),
        'best_score_unscaled': best_score_unscaled,
        'objective_unscaled': objective_unscaled,
        'objective_ratio': model.ObjVal / float((importances * risk_statuses).sum()),
        'objective_ratio_unscaled': (objective_unscaled / best_score_unscaled) if best_score_unscaled else None,
    }])

    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        unit_df.to_excel(writer, sheet_name="Built_Units", index=False)
        node_df.to_excel(writer, sheet_name="Nodes", index=False)
        summary_df.to_excel(writer, sheet_name="Summary", index=False)