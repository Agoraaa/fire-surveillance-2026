import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import os
import sys


def draw_result(filepath, output_dir):
    df = pd.read_excel(filepath, sheet_name="Nodes")
    units = pd.read_excel(filepath, sheet_name="Built_Units")

    width = int(df['x_coord'].max()) + 1
    height = int(df['y_coord'].max()) + 1

    reduced_risks = np.zeros((width, height))
    initial_risks = np.zeros((width, height))
    is_unit_base = np.zeros((width, height), dtype=bool)

    for _, row in df.iterrows():
        x = int(row['x_coord'])
        y = int(row['y_coord'])
        reduced_risks[x, y] = row['reduced_risk']
        initial_risks[x, y] = row['total_risk']

    for _, row in units.iterrows():
        x = int(row['x_coord'])
        y = int(row['y_coord'])
        is_unit_base[x, y] = True

    basename = os.path.basename(filepath)
    instance_name = basename.replace('_output.xlsx', '')

    plots = [
        ('initial_risk', initial_risks, None),
        ('reduced_risk', reduced_risks, is_unit_base),
        ('risk_diff', initial_risks - reduced_risks, is_unit_base),
    ]

    for label, data, mask in plots:
        fig, ax = plt.subplots()
        sns.heatmap(data, vmin=0, vmax=1, cmap="inferno", mask=mask,
                    xticklabels=False, yticklabels=False, linewidths=0, ax=ax)
        ax.set_title(f"{instance_name} — {label}")
        out_path = os.path.join(output_dir, f"{instance_name}_{label}.png")
        fig.savefig(out_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f"  Saved {out_path}")


def process_path(input_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    if os.path.isdir(input_path):
        files = sorted(
            f for f in os.listdir(input_path)
            if f.endswith('_output.xlsx')
        )
        if not files:
            print(f"No *_output.xlsx files found in {input_path}")
            return
        for f in files:
            print(f"Visualizing {f}...")
            draw_result(os.path.join(input_path, f), output_dir)
    else:
        if not input_path.endswith('_output.xlsx'):
            print(f"Warning: {input_path} is not an _output.xlsx file. Processing anyway.")
        print(f"Visualizing {os.path.basename(input_path)}...")
        draw_result(input_path, output_dir)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python visualize.py <file_or_folder> [output_dir]")
        print("  file_or_folder : path to *_output.xlsx or directory containing them")
        print("  output_dir     : where to save images (default: ./visualizations)")
        sys.exit(1)

    input_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else 'visualizations'
    process_path(input_path, output_dir)
