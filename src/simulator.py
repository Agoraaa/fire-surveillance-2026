from model import *
import math
import heapq
from heapq import heappush, heappop
import multiprocessing as mp
import random
import numpy as np

_worker_node_data = None
_worker_neighbors = None

def _node_data_from_problem(problem: ProblemModel):
    return {
        'forest_rate': np.array([n.forest_rate for n in problem.nodes]),
        'ymn':         np.array([n.ymn for n in problem.nodes]),
        'slope_coeff': np.array([n.slope_coeff for n in problem.nodes]),
        'ymn_coeff':   np.array([n.ymn_coeff for n in problem.nodes]),
        'x_coord':     np.array([n.x_coord for n in problem.nodes]),
        'y_coord':     np.array([n.y_coord for n in problem.nodes]),
    }

def _init_worker(node_data, neighbors):
    global _worker_node_data, _worker_neighbors
    _worker_node_data = node_data
    _worker_neighbors = neighbors

def _worker_burn_value(args):
    node_id, wind_direction, response_time, wind_speed_kmh = args
    return _calculate_burn_value_raw(node_id, wind_direction, _worker_node_data,
                                     _worker_neighbors, response_time, wind_speed_kmh)

def _calculate_burn_value_raw(start_node_id, wind_direction_rads, node_data, neighbors, response_time, wind_speed_kmh):
    wind_x = wind_speed_kmh * math.cos(wind_direction_rads)
    wind_y = wind_speed_kmh * math.sin(wind_direction_rads)
    x = node_data['x_coord']
    y = node_data['y_coord']
    forest_rate = node_data['forest_rate']
    ymn = node_data['ymn']
    slope_coeff = node_data['slope_coeff']
    ymn_coeff = node_data['ymn_coeff']
    pq = []
    heappush(pq, (0, start_node_id))
    forests_burned = []
    is_visited = [False] * len(forest_rate)
    while pq:
        fire_start_time, node_id = heappop(pq)
        if is_visited[node_id]:
            continue
        is_visited[node_id] = True
        forests_burned.append(forest_rate[node_id])
        if ymn[node_id] > 30:
            continue
        for spread_node_id in neighbors[node_id]:
            dx = x[spread_node_id] - x[node_id]
            dy = y[spread_node_id] - y[node_id]
            dist = math.sqrt(dx*dx + dy*dy)
            dir_x, dir_y = dx/dist, dy/dist
            wind_component_speed = wind_x*dir_x + wind_y*dir_y
            wind_coeff = 1 + (100/60)*max(10, wind_component_speed)
            speed_kmh = wind_coeff * slope_coeff[node_id] * ymn_coeff[node_id] * 0.06
            reach_time = fire_start_time + dist/speed_kmh
            if reach_time < response_time:
                heappush(pq, (reach_time, spread_node_id))
    return sum(forests_burned)/len(forests_burned)

def calculate_burn_value(start_node_id, wind_direction_rads, problem: ProblemModel, neighbor_cut_threshold, response_time=10, neighbors=None, wind_speed_kmh=30):
    if neighbors is None:
        neighbors = _create_nb_list(neighbor_cut_threshold, problem)
    node_data = _node_data_from_problem(problem)
    return _calculate_burn_value_raw(start_node_id, wind_direction_rads, node_data, neighbors, response_time, wind_speed_kmh)

def calculate_burn_values(problem: ProblemModel, neighbor_cut_threshold, response_time=2, n_workers=None, parallel=True):
    neighbors = _create_nb_list(neighbor_cut_threshold, problem)
    node_data = _node_data_from_problem(problem)
    wind_count = 5
    wind_step = math.tau / wind_count
    wind_directions = [wind_step * i for i in range(wind_count)]
    n_nodes = len(problem.nodes)

    tasks = [
        (node_id, wind_dir, response_time, problem.wind_speed)
        for wind_dir in wind_directions
        for node_id in range(n_nodes)
    ]

    if parallel:
        with mp.Pool(n_workers, initializer=_init_worker, initargs=(node_data, neighbors)) as pool:
            results = pool.map(_worker_burn_value, tasks)
    else:
        _init_worker(node_data, neighbors)
        results = [_worker_burn_value(task) for task in tasks]

    node_results = [[] for _ in range(n_nodes)]
    for i, val in enumerate(results):
        node_results[i % n_nodes].append(val)

    return [sum(node_results[nid]) / len(node_results[nid]) for nid in range(n_nodes)]

def _create_nb_list(neighbor_cut_threshold, problem: ProblemModel):
    import scipy.spatial as scipy
    xys = np.array([(n.x_coord, n.y_coord) for n in problem.nodes])
    tree = scipy.KDTree(xys)
    _, indices = tree.query(xys, k=21)  # k=21: includes self
    neighbors = {}
    for i, node in enumerate(problem.nodes):
        neighbor_ids = [problem.nodes[j].id for j in indices[i] if j != i]
        neighbors[node.id] = neighbor_ids[:20]
    return neighbors

def simulate_fire_with_snapshots(fire_start_id, wind_speed, wind_direction_rads, problem: ProblemModel, neighbor_cut_threshold, snapshot_times):
    neighbors = _create_nb_list(neighbor_cut_threshold, problem)
    snapshots = []
    next_snapshot_ind = 0
    snapshot_times = sorted(snapshot_times)
    pq = []
    heappush(pq, (0, start_node_id))
    is_visited = [False for _ in range(len(problem.nodes))]
    while len(pq):
        fire_start_time, node_id = heappop(pq)
        if fire_start_time >= snapshot_times[next_snapshot_ind]:
            next_snapshot_ind += 1
            snapshots.append(is_visited.copy())
            if next_snapshot_ind >= len(snapshot_times):
                break
        node = problem.nodes[node_id]
        if is_visited[node_id]:
            continue
        is_visited[node_id] = True
        for spread_node_id in neighbors[node_id]:
            spread_node = problem.nodes[spread_node_id]
            dx, dy = (spread_node.x_coord-node.x_coord), (spread_node.y_coord-node.y_coord)
            dist = spread_node.dist_to(node)
            speed = node.fire_spread_rate
            cos_similarity = (wind_x*dx + wind_y*dy)/(dist*wind_speed)
            speed += wind_speed* 0.1*cos_similarity
            speed = max(1, speed)
            reach_time = fire_start_time + dist/speed
            heappush(pq, (reach_time, spread_node_id))
    return snapshots


if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))

    PROBLEM_PATH = sys.argv[1]
    print(f'SOLVING {PROBLEM_PATH}')
    NEIGHBOR_THRESHOLD = 3.0
    RESPONSE_TIME = 5
    WIND_DIRECTION = 0.0  # radians

    print(f"Loading problem: {PROBLEM_PATH}")
    problem = ProblemModel.from_excel(PROBLEM_PATH)
    print(f"  {len(problem.nodes)} nodes, wind_speed={problem.wind_speed} km/h")

    print(f"\nBuilding neighbor list (threshold={NEIGHBOR_THRESHOLD})...")
    neighbors = _create_nb_list(NEIGHBOR_THRESHOLD, problem)
    avg_nb = sum(len(v) for v in neighbors.values()) / len(neighbors)
    print(f"  avg neighbors per node: {avg_nb:.1f}")

    
    # pick highest-risk node as fire start
    start_node = random.choice(problem.nodes) #max(problem.nodes, key=lambda n: n.forest_rate)
    print(f"\nFire start: node {start_node.id}  forest_rate={start_node.forest_rate:.3f}  "
          f"pos=({start_node.x_coord:.1f}, {start_node.y_coord:.1f})")

    print(f"\nRunning simulate_burn_value (response_time={RESPONSE_TIME}, wind_dir={WIND_DIRECTION:.2f} rad)...")
    wind_x = problem.wind_speed * math.cos(WIND_DIRECTION)
    wind_y = problem.wind_speed * math.sin(WIND_DIRECTION)

    # step through the BFS manually so we can print progress
    pq = []
    heappush(pq, (0.0, start_node.id))
    is_visited = [False] * len(problem.nodes)
    burned_nodes = []

    while pq:
        fire_time, node_id = heappop(pq)
        if is_visited[node_id]:
            continue
        is_visited[node_id] = True
        node = problem.nodes[node_id]
        burned_nodes.append((fire_time, node_id, node.forest_rate))
        print(f"  t={fire_time:6.3f}h  node={node_id:4d}  "
              f"forest_rate={node.forest_rate:.3f}  ymn={node.ymn:.1f}  "
              f"slope_coeff={node.slope_coeff:.3f}")

        if node.ymn > 30:
            continue
        for spread_id in neighbors[node_id]:
            spread = problem.nodes[spread_id]
            dx = spread.x_coord - node.x_coord
            dy = spread.y_coord - node.y_coord
            mag = (dx**2 + dy**2) ** 0.5
            dist = spread.dist_to(node)
            wind_component = (wind_x * dx/mag + wind_y * dy/mag)
            wind_coeff = 1 + (100/60) * max(10, wind_component)
            speed_kmh = wind_coeff * node.slope_coeff * node.ymn_coeff * 0.06
            reach_time = fire_time + dist / speed_kmh
            if reach_time < RESPONSE_TIME:
                heappush(pq, (reach_time, spread_id))

    forest_rates = [fr for _, _, fr in burned_nodes]
    avg_burn = sum(forest_rates) / len(forest_rates) if forest_rates else 0.0
    print(f"\nSummary:")
    print(f"  nodes burned: {len(burned_nodes)}")
    print(f"  avg forest_rate burned: {avg_burn:.4f}")

    print(f"\nRunning calculate_burn_values (5 wind dirs)...")
    burn_values = calculate_burn_values(problem, NEIGHBOR_THRESHOLD, response_time=RESPONSE_TIME)
    top5 = sorted(enumerate(burn_values), key=lambda x: -x[1])[:5]
    print("Top 5 highest-risk nodes:")
    for node_id, val in top5:
        n = problem.nodes[node_id]
        print(f"  node={node_id}  burn_value={val:.4f}  pos=({n.x_coord:.1f},{n.y_coord:.1f})")