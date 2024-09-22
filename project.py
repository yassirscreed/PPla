import sys
from minizinc import Instance, Model, Solver, Status
import re
from datetime import timedelta


def read_input(filename):
    problem_data = {
        'tests': [],
        'machines': set(),
        'resources': set()
    }
    
    pattern = re.compile(r"test\(\s*'([^']+)',\s*(\d+),\s*(\[.*?\]),\s*(\[.*?\])\s*\)")
    
    def parse_list(s):
        return [item.strip()[1:-1] for item in s[1:-1].split(',')] if s != '[]' else []

    with open(filename, 'r') as f:
        for line in f:
            if line.startswith('% Number of machines'):
                num_machines = int(line.split(':')[1].strip())
                problem_data['machines'] = set(f'm{i}' for i in range(1, num_machines + 1))
            elif line.startswith('test('):
                match = pattern.match(line.strip())
                if match:
                    name, duration, machines, resources = match.groups()
                    
                    machines = parse_list(machines)
                    resources = parse_list(resources)
                    
                    problem_data['tests'].append({
                        'name': name,
                        'duration': int(duration),
                        'machines': machines,
                        'resources': resources
                    })
                    
                    problem_data['resources'].update(resources)

    problem_data['machines'] = sorted(problem_data['machines'])
    problem_data['resources'] = sorted(problem_data['resources'])
    return problem_data

def create_minizinc_model(problem_data):
    model = Model()
    model.add_string(open("model.mzn").read())
    
    # Set up the parameters for the model
    model["M"] = len(problem_data['machines'])
    model["N"] = len(problem_data['tests'])
    model["R"] = len(problem_data['resources'])
    model["durations"] = [test['duration'] for test in problem_data['tests']]
    
    # Set up the machines each task can run on
    machine_sets = []
    for test in problem_data['tests']:
        if not test['machines']:
            machine_sets.append(set())
        else:
            machine_sets.append({problem_data['machines'].index(m) + 1 for m in test['machines']})
    model["machines"] = machine_sets
    
    # Set up the resources each task uses
    resource_sets = []
    for test in problem_data['tests']:
        resource_sets.append({problem_data['resources'].index(r) + 1 for r in test['resources']})
    model["resources"] = resource_sets

    return model

def solve_model(model): # Not used for now 
    instance = Instance(Solver.lookup("chuffed"), model)
    result = instance.solve()
    return result

def write_output(result, problem_data, output_file):
    with open(output_file, 'w') as f:
        f.write(f"% Makespan : {result['makespan']}\n")
        for m in range(1, len(problem_data['machines']) + 1):
            tasks = []
            for i, (start, machine) in enumerate(zip(result['start_times'], result['assigned_machines'])):
                if machine == m:
                    test = problem_data['tests'][i]
                    resources = ','.join(test['resources']) if test['resources'] else ''
                    resources_str = f",['{resources}']" if resources else ''
                    tasks.append(f"('{test['name']}',{start}{resources_str})")
            if tasks:
                f.write(f"machine( 'm{m}', {len(tasks)}, [{','.join(tasks)}])\n")

def print_debug_info(problem_data):
    print("\nTests:")
    for test in problem_data['tests']:
        print(f"  {test['name']}: duration={test['duration']}, machines={test['machines']}, resources={test['resources']}")
    print(f"\nMachines: {problem_data['machines']}")
    print(f"Resources: {problem_data['resources']}")
    print(f"\nNumber of tests: {len(problem_data['tests'])}")
    print(f"Number of machines: {len(problem_data['machines'])}")
    print(f"Number of resources: {len(problem_data['resources'])}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python proj.py <input-file> <output-file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    problem_data = read_input(input_file)
    model = create_minizinc_model(problem_data)
    
    print_debug_info(problem_data)
    
    # Try different solvers if one takes too long or doesnt work
    solvers = ["chuffed", "gecode", "or-tools"]
    for solver_name in solvers:
        print(f"\nTrying solver: {solver_name}")
        instance = Instance(Solver.lookup(solver_name), model)
        result = instance.solve(timeout=timedelta(milliseconds=500))
        
        if result.status == Status.OPTIMAL_SOLUTION or result.status == Status.SATISFIED:
            write_output(result, problem_data, output_file)
            print(f"Solution written to {output_file}")
            break
        elif result.status == Status.UNSATISFIABLE:
            print("The problem is unsatisfiable")
            break
        else:
            print(f"Solving process ended with status: {result.status}")
    
    if result.status not in [Status.OPTIMAL_SOLUTION, Status.SATISFIED, Status.UNSATISFIABLE]:
        print("Failed to find a solution with any solver.")