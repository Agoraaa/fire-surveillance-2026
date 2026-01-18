import matplotlib.pyplot as plt
import seaborn as sns
from colorsys import rgb_to_hls, hls_to_rgb
import numpy as np
import math
import pandas as pd
from perlin_numpy import (
    generate_perlin_noise_2d, generate_fractal_noise_2d
)

def _generate_noise(x, mean, std):
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

def generate_risk_map(risk_density = 0.5, width_height = 100):
    risk_map = _generate_noise(width_height, 0, 1)
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

def generate_instance(output_file, node_xy_count, width_height_kilometers, importance_mean_std, ymn_mean_std, slope_std, wind_speed, risk_density):
    importances = _generate_noise(node_xy_count, importance_mean_std[0], importance_mean_std[1])
    ymns = _generate_noise(node_xy_count, ymn_mean_std[0], ymn_mean_std[1])
    slopes = abs(_generate_noise(node_xy_count, 0, slope_std))
    risk_statuses, _ = generate_risk_map(risk_density, node_xy_count)
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
    for node_count in [5, 10, 20, 50, 100, 200]:
        generate_instance(f'problem_{node_count}x{node_count}.xlsx', node_count, node_count, (1, 0.2), (15, 5), 8, 20, 0.55)