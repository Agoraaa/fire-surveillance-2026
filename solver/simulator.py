from model import *
import math
import heapq
from heapq import heappush, heappop
def calculate_burn_value(start_node_id, wind_direction_rads, problem: ProblemModel, neighbor_cut_threshold, response_time = 10, neighbors = None, wind_speed_kmh = 30):
    if neighbors is None:
        neighbors = _create_nb_list(neighbor_cut_threshold, problem)
    wind_speed_kmh = 30
    wind_x = wind_speed_kmh * math.cos(wind_direction_rads)
    wind_y = wind_speed_kmh * math.sin(wind_direction_rads)
    pq = []
    heappush(pq, (0, start_node_id))
    forests_burned = []
    is_visited = [False for _ in range(len(problem.nodes))]
    # bfs time
    while len(pq):
        fire_start_time, node_id = heappop(pq)
        node = problem.nodes[node_id]
        
        if is_visited[node_id]:
            continue
        is_visited[node_id] = True
        forests_burned.append(node.forest_rate)
        if node.ymn > 30:
            continue
        for spread_node_id in neighbors[node_id].keys():
            spread_node = problem.nodes[spread_node_id]
            dx, dy = (spread_node.x_coord-node.x_coord), (spread_node.y_coord-node.y_coord)
            mag = ((dx**2) + (dy**2))**(1/2)
            dir_x, dir_y = dx/mag, dy/mag
            dist = spread_node.dist_to(node)

            wind_component_speed = (wind_x*dir_x + wind_y*dir_y)
            wind_coeff = 1 + (100/60)*max(10, wind_component_speed)
            speed_ms = wind_coeff* node.slope_coeff * node.ymn_coeff
            speed_kmh = speed_ms * 0.06
            reach_time = fire_start_time + dist/speed_kmh
            if reach_time < response_time:
                heappush(pq, (reach_time, spread_node_id))
    return sum(forests_burned)/len(forests_burned)

def calculate_burn_values(problem: ProblemModel, neighbor_cut_threshold, response_time = 2):
    neighbors = _create_nb_list(neighbor_cut_threshold, problem)
    wind_count = 5
    wind_up = math.tau
    wind_step = (wind_up-0)/wind_count
    node_results = [[] for _ in range(len(problem.nodes))]
    for i in range(wind_count):
        print(f"### WIND {i} ###")
        wind_direction = 0 + wind_step*i
        for node_id in range(len(problem.nodes)):
            if node_id % 1000 == 0:
                print(f'Node {node_id}')
            node_results[node_id].append(calculate_burn_value(node_id, wind_direction, problem, 
            neighbor_cut_threshold, response_time=10, neighbors=neighbors, wind_speed_kmh=problem.wind_speed))
    res = []
    for node_id in range(len(problem.nodes)):
        res.append(
            sum(node_results[node_id])/len(node_results[node_id])
        )
    return res

def _create_nb_list(neighbor_cut_threshold, problem: ProblemModel):
    neighbors = {}
    for node in problem.nodes:
        neighbors[node.id] = {}
        for nb_node in problem.nodes:
            if node == nb_node:
                continue
            if node.dist_to(nb_node) <= neighbor_cut_threshold:
                neighbors[node.id][nb_node.id] = True
    return neighbors

def simulate_fire_with_snapshots(fire_start_id, wind_speed, wind_direction_rads, problem: ProblemModel, neighbor_cut_threshold, snapshot_times):
    neighbors = _create_nb_list(neighbor_cut_threshold, problem)
    snapshots = []
    next_snapshot_ind = 0
    snapshot_times = sorted(snapshot_times)
    pq = []
    heappush(pq, (0, start_node_id))
    is_visited = [False for _ in range(len(problem.nodes))]
    # bfs time
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
        for spread_node_id in neighbors[node_id].keys():
            spread_node = problem.nodes[spread_node_id]
            dx, dy = (spread_node.x_coord-node.x_coord), (spread_node.y_coord-node.y_coord)
            dist = spread_node.dist_to(node)
            speed = node.fire_spread_rate
            # there is no way this is right
            cos_similarity = (wind_x*dx + wind_y*dy)/(dist*wind_speed)
            speed += wind_speed* 0.1*cos_similarity
            speed = max(1, speed)
            reach_time = fire_start_time + dist/speed
            heappush(pq, (reach_time, spread_node_id))
    return snapshots