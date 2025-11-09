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

def chromosome_to_sol(chromosome, quad_tree, problem: ProblemModel):
    units = problem.units
    nodes = problem.nodes
    res = []
    for coords in chromosome:
        x, y = coords
        _, closest_id = quad_tree.query(coords)
        res.append(closest_id)
    return res

def sol_to_z(chromosome, quad_tree, risk_values, problem:ProblemModel):
    solution = chromosome_to_sol(chromosome, quad_tree, problem)
    z = 0
    units = []
    for unit_type in problem.units:
        for _ in range(unit_type.inventory):
            units.append(unit_type)
    nodes = problem.nodes
    for i in range(len(nodes)):
        node = nodes[i]
        visibility = 0
        for k in range(len(units)):
            visibility += problem.covering_rate(i, int(solution[k]), units[k])
        visibility = min(visibility, 1)
        visibility = min(visibility, node.risk_status)
        z += visibility * risk_values[i]
    global best_sol
    if z > best_sol:
        best_sol = z
        print(f'New best solution: {z}')
    return z

def crossover(good_sol, bad_sol):
    bias = 0.65
    res = []
    for i in range(len(good_sol)):
        if random.random() < bias:
            res.append(good_sol[i])
        else:
            res.append(bad_sol[i])
    return res


def genetic_time(problem: ProblemModel):
    global best_sol
    best_sol = 0
    nodes = problem.nodes
    quad_tree = scipy.KDTree([[node.x_coord, node.y_coord] for node in nodes])
    node_count = len(problem.nodes)
    unit_count = sum([unit.inventory for unit in problem.units])
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
    min_x = min([node.x_coord for node in nodes])
    max_x = max([node.x_coord for node in nodes])
    min_y = min([node.y_coord for node in nodes])
    max_y = max([node.y_coord for node in nodes])
    elite_count = 5
    mutant_count = 10
    pop_size = 50
    
    population = []
    for _ in range(pop_size):
        sol = []
        for _ in range(unit_count):
            sol.append([random.random()*max_x, random.random()*max_y])
        population.append((sol, sol_to_z(sol, quad_tree, risk_values, problem)))

    generation = 0
    # 100x100 için 2600 optimum
    while 1:
        if generation % 1 == 0:
            print(f'Gen {generation}')
        population.sort(key=(lambda x: x[1]), reverse=True)
        new_pop = []
        new_pop.extend(population[:elite_count])
        for _ in range(mutant_count):
            sol = []
            for _ in range(unit_count):
                sol.append([random.random()*max_x, random.random()*max_y])
            new_pop.append((sol, sol_to_z(sol, quad_tree, risk_values, problem)))
        while len(new_pop) < pop_size:
            sol1, z1 = random.choice(population)
            sol2, z2 = random.choice(population)
            if z1 > z2:
                child = crossover(sol1, sol2)
            else:
                child = crossover(sol2, sol1)
            new_pop.append((child, sol_to_z(child, quad_tree, risk_values, problem)))
        population = new_pop
        generation += 1

