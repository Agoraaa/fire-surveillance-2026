from model import *
import solver
import sys

source_path = sys.argv[1] if len(sys.argv) > 1 else 'problem_data.xlsx'
problem = ProblemModel.from_excel(source_path)

solver.solve_set_covering(problem=problem)