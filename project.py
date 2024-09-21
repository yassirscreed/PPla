import sys
import re
from collections import defaultdict

from minizinc import Instance, Model, Solver


# Read input file and return tests, machines, and resources
# Example input file:
#% Number of tests: 5
#% Number of machines: 3
#% Number of resources: 2
#
#test( 't1', 10, ['m1'], ['r1'])
#test( 't2', 15, ['m2', 'm3'], [])
#test( 't3', 20, [], ['r1', 'r2'])
#test( 't4', 12, ['m1', 'm3'], ['r2'])
#test( 't5', 8, [], [])
def read_input(filename):
    data = {
        'tests': [],
        'machines': set(),
        'resources': set()
    }
    
    # Compile the regex pattern once
    pattern = re.compile(r"test\(\s*'([^']+)',\s*(\d+),\s*(\[.*?\]),\s*(\[.*?\])\s*\)")
    
    def parse_list(s):
        return [item.strip()[1:-1] for item in s[1:-1].split(',')] if s != '[]' else []

    with open(filename, 'r') as f:
        for line in f:
            if line.startswith('test('):
                match = pattern.match(line.strip())
                if match:
                    name, duration, machines, resources = match.groups()
                    
                    machines = parse_list(machines)
                    resources = parse_list(resources)
                    
                    data['tests'].append({
                        'name': name,
                        'duration': int(duration),
                        'machines': machines,
                        'resources': resources
                    })
                    
                    data['machines'].update(machines)
                    data['resources'].update(resources)

    data['machines'] = sorted(data['machines'])
    data['resources'] = sorted(data['resources'])
    return data

def create_minizinc_model(data):
    model = Model()
    
    # Parametros (passamos como parametros para o modelo)
    model["n_tests"] = len(data['tests'])
    model["n_machines"] = len(data['machines'])
    model["n_resources"] = len(data['resources'])
    model["durations"] = [test['duration'] for test in data['tests']]
    

    return model

def print_debug_info(data):
    print("\nTests:")
    for test in data['tests']:
        print(f"  {test['name']}: duration={test['duration']}, machines={test['machines']}, resources={test['resources']}")
    print(f"\nMachines: {data['machines']}")
    print(f"Resources: {data['resources']}")
    print(f"\nNumber of tests: {len(data['tests'])}")
    print(f"Number of machines: {len(data['machines'])}")
    print(f"Number of resources: {len(data['resources'])}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python proj.py <input-file> <output-file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    data = read_input(input_file)
    model = create_minizinc_model(data)
    
    # Create a MiniZinc instance and solve (to be implemented in future checkpoints)
    #instance = Instance(Solver.lookup("chuffed"), model)
    
    print_debug_info(data)
    
    # TODO: Implement solving and output writing in future checkpoints

    # Save the MiniZinc model to a file
    with open("model.mzn", "w") as f:
        f.write(str(model))
    print("MiniZinc model written to 'model.mzn'")