from itertools import combinations
from pysat.solvers import Glucose3
from pysat.formula import CNF


def read_input_file(input_file):
    with open(input_file, "r") as f:
        lines = f.readlines()
    T, S, K = [int(x) for x in lines[0].split()]
    S_t = {t: [int(x) for x in lines[t+1].split()] for t in range(T)}
    return T, S, K, S_t


def definition_constraints(T, S, K, S_t):
    y_st = {}
    for s in range(S):
        for t in range(T):
            y_st[(s, t)] = 1 if s in S_t[t] else 0
    return y_st


def definition_to_cnf(y_st, y_st_idx):
    constraints = []
    for key, value in y_st.items():
        if value == 1:
            constraints.append([y_st_idx[key]])
        else:
            constraints.append([-y_st_idx[key]])
    return constraints


def convert_and_to_or(constraints: list[list[int, int]]):
    if len(constraints) == 1:
        return constraints
    elif len(constraints) == 2:
        new_constraints = []
        for c1 in constraints[0]:
            for c2 in constraints[1]:
                new_constraints.append([c1, c2])
        return new_constraints
    else:
        previous_constraints = convert_and_to_or(constraints[:-1])
        new_constraints = []
        for constraint in previous_constraints:
            for c in constraints[-1]:
                new_constraints.append(constraint + [c])
        return new_constraints


def class_taught_constraints(T, S, x_t_idx, y_st_idx):
    all_constraints = []
    for subject in range(S):
        current_constraint = []
        for t in range(T):
            current_constraint.append([y_st_idx[(subject, t)], x_t_idx[t]])
        all_constraints.extend(convert_and_to_or(current_constraint))
    return all_constraints


def less_than_k_classes_constraints(T, S, K, x_t_idx):
    all_constraints = []
    T = list(range(T))
    for subset in combinations(T, K+1):
        current_constraint = []
        for t in subset:
            current_constraint.append(-x_t_idx[t])
        all_constraints.append(current_constraint)
    return all_constraints


def more_than_k_classes_constraints(T, S, K, x_t_idx):
    all_constraints = []
    T = list(range(T))
    for subset in combinations(T, len(T)-K+1):
        current_constraint = []
        for t in subset:
            current_constraint.append(x_t_idx[t])
        all_constraints.append(current_constraint)
    return all_constraints


def to_cnf(T, S, K, S_t):
    y_st = definition_constraints(T, S, K, S_t)
    y_st_index = {v: i+1 for i, v in enumerate(y_st)}
    x_t_index = {i: t+1 for i, t in enumerate(range(len(y_st), len(y_st) + T))}
    complete_constraints = [
        *definition_to_cnf(y_st, y_st_index), *class_taught_constraints(T, S, x_t_index, y_st_index),
        *less_than_k_classes_constraints(T, S, K, x_t_index), *more_than_k_classes_constraints(T, S, K, x_t_index)
    ]
    return T, S, complete_constraints


def to_dimacs(cnf, problem_name="problem"):
    T, S, complete_constraints = cnf
    with open(f"{problem_name}.cnf", "w") as f:
        f.write(f"p cnf {T+S} {len(complete_constraints)}\n")
        for constraint in complete_constraints:
            f.write(" ".join([str(x) for x in constraint]) + " 0\n")


def solve_sat_from_file(file_name):
    formula = CNF(from_file=file_name)
    g = Glucose3()
    g.append_formula(formula.clauses)
    return g.solve(), g.get_model()


def model_to_output(model, T, S, output_file="output.txt"):
    with open(output_file, "w") as f:
        if model is None:
            f.write('There is no solution.')
        else:
            x_t_opposite = {t+1: i for i, t in enumerate(range(T * S, T * S + T))}
            teachers_in = [x_t_opposite[i] for i in model if i in x_t_opposite]
            f.write('The teachers that have been selected are (starting from 1): ' + ', '.join([f'Teacher {i+1}' for
                                                                                                i in teachers_in]))


if __name__ == '__main__':
    for file in range(1, 4):
        inpt = read_input_file(f"input{file}.txt")
        to_dimacs(to_cnf(*inpt), problem_name=f"problem{file}")
        solution = solve_sat_from_file(f"problem{file}.cnf")
        model_to_output(solution[1], inpt[0], inpt[1], f"output{file}.txt")
