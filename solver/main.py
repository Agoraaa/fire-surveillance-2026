from model import *
import solver
import genetic
import sys
import os

def solve_file(source_path):
    problem = ProblemModel.from_excel(source_path)
    #genetic.genetic_time(problem)
    solver.solve_probabilistic(problem, source_path.replace('.xlsx', '_output.xlsx'))

input_path = sys.argv[1] if len(sys.argv) > 1 else 'problem_data.xlsx'

if os.path.isdir(input_path):
    files = sorted(f for f in os.listdir(input_path) if f.endswith('.xlsx') and not f.endswith('_output.xlsx'))
    for f in files:
        output_path = os.path.join(input_path, f.replace('.xlsx', '_output.xlsx'))
        if os.path.exists(output_path):
            print(f"Skipping {f} (already solved).")
            continue
        print(f"Solving {f}...")
        solve_file(os.path.join(input_path, f))
else:
    solve_file(input_path)