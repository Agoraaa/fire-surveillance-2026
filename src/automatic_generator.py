import numpy as np
import math
import pandas as pd
import pathlib as pl
from perlin_numpy import (
    generate_perlin_noise_2d, generate_fractal_noise_2d
)

def _generate_noise(x, mean, std, seed=None):
    if seed is not None:
        np.random.seed(seed)
    noise = generate_fractal_noise_2d((1024, 1024), (8, 8),
                                  octaves=8,
                                 persistence=0.2,
                                 lacunarity=2,
                                 #tileable=(True,True)
                                 )
    noise *= (std/noise.std())
    noise += (mean-noise.mean())
    res = []
    y = x
    for i in range(x):
        res.append([])
        for j in range(x):
            closest_x = math.floor((i/x)*1024)
            closest_y = math.floor((j/y)*1024)
            res[i].append(noise[closest_x][closest_y])
    return np.array(res)

def generate_risk_map(risk_density = 0.5, width_height = 100, seed=None):
    risk_map = _generate_noise(width_height, 0, 1, seed=seed)
    risk_map -= risk_map.min()
    risk_map /= risk_map.max()
    is_hidden = risk_map < (1-risk_density)
    for i in range(width_height):
        for j in range(width_height):
            risk_map[i][j] = (risk_map[i][j] - (1-risk_density) ) / (1- (1-risk_density) )
            if is_hidden[i][j]:
                risk_map[i][j] = 0
    risk_map = risk_map**(1/3)
    return risk_map, is_hidden

def generate_instance(output_file, node_xy_count, width_height_kilometers, importance_mean_std, ymn_mean_std, slope_mean_std, wind_speed, risk_density, unit_level="high", seed=None):
    importances = _generate_noise(node_xy_count, importance_mean_std[0], importance_mean_std[1], seed=seed)
    ymns = _generate_noise(node_xy_count, ymn_mean_std[0], ymn_mean_std[1], seed=seed+1 if seed is not None else None)
    slopes = abs(_generate_noise(node_xy_count, slope_mean_std[0], slope_mean_std[1], seed=seed+2 if seed is not None else None))
    risk_statuses, _ = generate_risk_map(risk_density, node_xy_count, seed=seed+3 if seed is not None else None)
    lines = []
    for i in range(node_xy_count):
        for j in range(node_xy_count):
            id = 1 + (i*node_xy_count) + j
            x_coord = (i/node_xy_count) * width_height_kilometers
            y_coord = (j/node_xy_count) * width_height_kilometers
            importance = importances[i][j]
            ymn = ymns[i][j]
            slope = slopes[i][j]
            risk_status = risk_statuses[i][j]
            is_buildable = 'buildable'
            lines.append([id, x_coord, y_coord, risk_status, is_buildable, importance, slope, ymn])
    df1 = pd.DataFrame(lines, columns = ['id', 'x_coord', 'y_coord', 'risk_status', 'is_buildable', 'forest_rate', 'slope', 'ymn'])
    inv = UNIT_INVENTORIES[unit_level]
    lines = []
    lines.append(['Long-range UAV', 3, 100, 6, 15])
    lines.append(['Short-range UAV', 3, 100, 1, 5])
    lines.append(['Watchtower', 1, 100, 10, 20])
    lines.append(['Sensor Tower', 1, 100, 3, 4])
    df2 = pd.DataFrame(lines, columns = ['observer_type', 'inventory', 'cost', 'min_vision', 'max_vision'])
    df3 = pd.DataFrame([['wind_speed', wind_speed]], columns=['parameter', 'value'])
    with pd.ExcelWriter(output_file) as writer:
        df1.to_excel(writer, sheet_name="Nodes", index=False)
        df2.to_excel(writer, sheet_name="Units", index=False)
        df3.to_excel(writer, sheet_name="Parameters", index=False)


def _run(args):
    output_file, node_xy_count, km, importance, ymn, slope, wind, risk, unit_level, seed = args
    print(f'Generating {pl.Path(output_file).stem}')
    generate_instance(output_file, node_xy_count, km, importance, ymn, slope, wind, risk, unit_level=unit_level, seed=seed)

if __name__ == '__main__':
    generate_instance(
        'example_instance.xlsx',
        node_xy_count=30,
        width_height_kilometers=100,
        importance_mean_std= (55, 15),
        ymn_mean_std= (15, 5),
        slope_mean_std= (10, 5),
        wind_speed=30,
        risk_density=0.6
    )
    