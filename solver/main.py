from model import *
import solver

source_path = 'problem_data.xlsx'
problem = ProblemModel.from_excel(source_path)

solver.solve_set_covering(problem=problem)