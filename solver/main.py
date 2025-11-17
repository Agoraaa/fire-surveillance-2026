from model import *
import solver
import genetic
import sys

source_path = sys.argv[1] if len(sys.argv) > 1 else 'problem_data.xlsx'
problem = ProblemModel.from_excel(source_path)

#genetic.genetic_time(problem)
solver.solve_set_covering(problem, source_path.replace('.xlsx', '_output.xlsx'))