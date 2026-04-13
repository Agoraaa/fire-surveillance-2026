import matplotlib.pyplot as plt
import seaborn as sns
from colorsys import rgb_to_hls, hls_to_rgb
import numpy as np
import math
import pandas as pd
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

def generate_instance(output_file, node_xy_count, width_height_kilometers, importance_mean_std, ymn_mean_std, slope_mean_std, wind_speed, risk_density, seed=None):
    importances = _generate_noise(node_xy_count, importance_mean_std[0], importance_mean_std[1], seed=seed)
    ymns = _generate_noise(node_xy_count, ymn_mean_std[0], ymn_mean_std[1], seed=seed)
    slopes = abs(_generate_noise(node_xy_count, slope_mean_std[0], slope_mean_std[1], seed=seed))
    risk_statuses, _ = generate_risk_map(risk_density, node_xy_count, seed=seed)
    lines = []
    for i in range(width_height_kilometers):
        for j in range(width_height_kilometers):
            id = 1 + (i*width_height_kilometers) + j
            x_coord = (i/width_height_kilometers) * width_height_kilometers
            y_coord = (j/width_height_kilometers) * width_height_kilometers
            importance = importances[i][j]
            ymn = ymns[i][j]
            slope = slopes[i][j]
            risk_status = risk_statuses[i][j]
            is_buildable = 'buildable'
            lines.append([id, x_coord, y_coord, risk_status, is_buildable, importance, slope, ymn])
    df1 = pd.DataFrame(lines, columns = ['id', 'x_coord', 'y_coord', 'risk_status', 'is_buildable', 'forest_rate', 'slope', 'ymn'])
    lines = []
    lines.append(['UAV_type_A', 1, 100, 5, 6])
    lines.append(['UAV_type_B', 0, 100, 5, 6])
    lines.append(['Surv_Tower_Basic', 0, 100, 5, 6])
    lines.append(['Augmented_Tower', 0, 100, 5, 6])
    df2 = pd.DataFrame(lines, columns = ['observer_type', 'inventory', 'cost', 'min_vision', 'max_vision'])
    df3 = pd.DataFrame([['wind_speed', wind_speed]], columns=['parameter', 'value'])
    with pd.ExcelWriter(output_file) as writer:
        df1.to_excel(writer, sheet_name="Nodes", index=False)
        df2.to_excel(writer, sheet_name="Units", index=False)
        df3.to_excel(writer, sheet_name="Parameters", index=False)


if __name__ == '__main__':
    forest_densities = {
        "low": (25, 15),
        "mid": (55, 15),
        "high": (85, 15)
    }
    slopes = {
        "low": (3, 2),
        "mid": (10, 5),
        "high": (25, 10)
    }
    moistures = {
        "critical": (5, 5),
        "mid": (15, 5),
        "high": (30, 10)
    }
    winds = {
        "low": 10,
        "mid": 20,
        "high": 30
    }
    risks = {
        "high": 0.6,
        "medium": 0.55,
        "low": 0.5
    }
    
    seeds = [2640, 45]
    for seed in seeds:
        for forest_density in forest_densities:
            for slope in slopes:
                for moisture in moistures:
                    for wind in winds:
                        for risk in risks:
                            instance_name = f'{forest_density}F-{slope}S-{moisture}M-{wind}W-{risk}R-seed{seed}'
                            print(f'Generating {instance_name}')
                            generate_instance(
                                f'test/{instance_name}.xlsx',
                                45,
                                45,
                                forest_densities[forest_density],
                                moistures[moisture],
                                slopes[slope],
                                winds[wind],
                                risks[risk],
                                seed=seed
                            )