from ortools.linear_solver import pywraplp

def optimize_itinerary(candidates, total_budget, days):
    """
    MILP Solver: Maximize Match Score while staying under Budget.
    """
    solver = pywraplp.Solver.CreateSolver('SCIP')
    if not solver: return candidates[:days]

    # Variables: x[i] is 1 if we visit location i
    x = {}
    for i in range(len(candidates)):
        x[i] = solver.IntVar(0, 1, f'x_{i}')

    # Constraint 1: Stay under total budget
    solver.Add(sum(x[i] * candidates[i]['price_per_night'] for i in range(len(candidates))) <= total_budget)

    # Constraint 2: Fill exactly the number of days requested (or max available)
    solver.Add(sum(x[i] for i in range(len(candidates))) <= days)

    # Objective: Maximize the match_score (vibe)
    objective = solver.Objective()
    for i in range(len(candidates)):
        objective.SetCoefficient(x[i], candidates[i]['match_score'])
    objective.SetMaximization()

    status = solver.Solve()

    if status == pywraplp.Solver.OPTIMAL:
        return [candidates[i] for i in range(len(candidates)) if x[i].solution_value() > 0.5]
    return candidates[:days]