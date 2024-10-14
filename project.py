from minizinc import Instance, Model, Solver, Status
import re
from datetime import timedelta
import matplotlib.pyplot as plt
from matplotlib import patheffects
import numpy as np
import argparse
import os
import sys

USE_SORTING = True

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
    
    # Always keep track of the original order
    problem_data['original_order'] = {test['name']: i for i, test in enumerate(problem_data['tests'])}
    
    if USE_SORTING:
        problem_data['tests'] = sort_tests(problem_data['tests'])
    
    return problem_data

def sort_tests(tests):
    # Sort tests by resources needed and lower machine options
    #return sorted(tests, key=lambda x: (len(x['resources']), x['duration']), reverse=True)
    # Sort by descending duration
    return sorted(tests, key=lambda x: x['duration'], reverse=True)
    # Sort by resources needed
    #    return sorted(tests, key=lambda x: len(x['resources']), reverse=True)
    # Sort by number of lower number of machine options
   # return sorted(tests, key=lambda x: (len(x['machines']) == 0, len(x['machines']), -x['duration']))

def draw_schedule(problem_data, output_file):
    activities = [[] for _ in range(len(problem_data['machines']))]
    
    # Read the output file
    with open(output_file, 'r') as f:
        lines = f.readlines()
    
    # Extract makespan
    makespan = int(lines[0].split(':')[1].strip())
    
    # Parse the schedule
    for line in lines[1:]:
        if line.startswith('machine'):
            parts = line.split(', [')
            machine_num = int(parts[0].split("'")[1][1:])  # Extract machine number
            tasks = eval('[' + parts[1][:-2])  # Convert string representation of list to actual list
            
            for task in tasks:
                task_name, start_time = task[:2]
                resources = task[2] if len(task) > 2 else []
                
                # Find the corresponding test in problem_data
                test = next(t for t in problem_data['tests'] if t['name'] == task_name)
                
                activities[machine_num-1].append({
                    'name': task_name,
                    'start_time': start_time,
                    'duration': test['duration'],
                    'resources': resources
                })

    n_machines = len(problem_data['machines'])
    width = min(20, max(12, makespan // 50))  # Limit max width
    height = min(12, max(6, n_machines // 2))  # Limit max height

    fig, ax = plt.subplots(figsize=(width, height))
    ax.set_xlim(0, makespan + 1)
    ax.set_ylim(0, n_machines + 1)

    colors = plt.cm.Set3(np.linspace(0, 1, len(problem_data['resources']) + 1))
    color_map = {f'r{i+1}': colors[i] for i in range(len(problem_data['resources']))}
    color_map[''] = colors[-1]

    for i, activity_line in enumerate(activities, start=1):
        for activity in activity_line:
            start_time = activity['start_time']
            duration = activity['duration']
            end_time = start_time + duration
            resources = activity['resources']
            color = color_map[resources[0] if resources else '']

            # Draw the task bar
            ax.plot([start_time, end_time], [i, i], linewidth=16, solid_capstyle='butt', color=color)
            
            # Draw black task separators (vertical lines)
            ax.plot([start_time, start_time], [i - 0.2, i + 0.2], color='black', linewidth=0.5)
            ax.plot([end_time, end_time], [i - 0.2, i + 0.2], color='black', linewidth=0.5)

            # Add text
            text_x = (start_time + end_time) / 2
            text_y = i
            fontsize = max(6, min(10, 120 // len(activity_line)))  # Adjust font size based on number of tasks
            
            # Include resource count in the text if there are multiple resources
            display_text = activity['name']
            if len(resources) > 1:
                display_text += f" ({len(resources)}R)"
            
            mytxt = ax.text(text_x, text_y, display_text, ha='center', va='center', color='white', fontsize=fontsize)
            mytxt.set_path_effects([patheffects.withStroke(linewidth=2, foreground='black')])

    ax.set_yticks(range(1, n_machines + 1))
    ax.set_yticklabels([f'M{i}' for i in range(1, n_machines + 1)])
    ax.set_xlabel('Time')
    ax.set_title(f"Makespan: {makespan}")
    plt.grid(True, which='both', axis='x', linestyle='--', linewidth=0.5)

    # Create legend for resources
    legend_elements = [plt.Rectangle((0,0),1,1, facecolor=color_map[f'r{i+1}'], edgecolor='black', label=f'r{i+1}')
                       for i in range(len(problem_data['resources']))]
    legend_elements.append(plt.Rectangle((0,0),1,1, facecolor=color_map[''], edgecolor='black', label='No resource'))
    ax.legend(handles=legend_elements, title='Resources', loc='center left', bbox_to_anchor=(1, 0.5))

    plt.tight_layout()
    plt.show()

def calculate_upper_bound(problem_data):
    machine_loads = [0] * len(problem_data['machines'])
    resource_loads = [0] * len(problem_data['resources'])
    
    for test in problem_data['tests']:
        if test['machines']:
            min_machine_load = min(machine_loads[problem_data['machines'].index(m)] for m in test['machines'])
        else:
            min_machine_load = min(machine_loads)
        machine_loads[machine_loads.index(min_machine_load)] += test['duration']
        for r in test['resources']:
            resource_loads[problem_data['resources'].index(r)] += test['duration']
    
    return max(max(machine_loads), max(resource_loads))

def calculate_lower_bound(problem_data):
    resource_loads = [sum(test['duration'] for test in problem_data['tests'] if r in test['resources']) 
                      for r in problem_data['resources']]
    machine_loads = [sum(test['duration'] for test in problem_data['tests'] if m in test['machines']) 
                     for m in problem_data['machines']]
    return max(max(resource_loads), max(machine_loads))

def binary_search_optimization(model, problem_data, solver_name, timeout=300):
    solver = Solver.lookup(solver_name)
    instance = Instance(solver, model)
    
    lower_bound = calculate_lower_bound(problem_data)
    upper_bound = calculate_upper_bound(problem_data)
    
    # Add extra 10% to upper bound if lower bound equals upper bound initially
    if lower_bound == upper_bound:
        upper_bound = int(upper_bound * 1.1)
    
    best_solution = None
    best_makespan = upper_bound
    
    print(f"Initial lower bound: {lower_bound}")
    print(f"Initial upper bound: {upper_bound}")
    
    iteration = 0
    while lower_bound <= upper_bound:
        iteration += 1
        current_makespan = (lower_bound + upper_bound) // 2
        
        # Create a new branch of the model for this iteration
        with instance.branch() as child:
            # Assign the new max_makespan
            child["max_makespan"] = current_makespan
            
            print(f"\nIteration {iteration}:")
            print(f"  Current makespan: {current_makespan}")
            
            result = child.solve(timeout=timedelta(seconds=timeout))
            
            print(f"  Solver status: {result.status}")
            
            if result.status == Status.SATISFIED or result.status == Status.ALL_SOLUTIONS:
                best_solution = result
                best_makespan = result["makespan"]
                upper_bound = best_makespan - 1
                print(f"  Found solution with makespan: {best_makespan}")
                print(f"  New upper bound: {upper_bound}")
            elif result.status == Status.UNSATISFIABLE:
                lower_bound = current_makespan + 1
                print(f"  No solution found. New lower bound: {lower_bound}")
            else:
                print(f"  Search stopped due to {result.status}")
                break
    
    print(f"\nFinal best makespan: {best_makespan}")
    return best_solution

def create_minizinc_model(problem_data, dzn_file=None):
    model = Model()
    model.add_string(open("model.mzn").read())
    
    if dzn_file:
        model.add_file(dzn_file)
    else:
        # Set up the parameters for the model
        model["M"] = len(problem_data['machines'])
        model["N"] = len(problem_data['tests'])
        model["R"] = len(problem_data['resources'])
        model["durations"] = [test['duration'] for test in problem_data['tests']]

        lower_bound = calculate_lower_bound(problem_data)
        model["min_makespan"] = lower_bound
        
        # Set up the machines each task can run on
        machine_sets = []
        all_machines = set(range(1, len(problem_data['machines']) + 1))
        for test in problem_data['tests']:
            if not test['machines']:
                machine_sets.append(all_machines)
            else:
                machine_sets.append({int(m[1:]) for m in test['machines']})
        model["machines"] = machine_sets
        
        # Set up the resources each task uses
        resource_sets = []
        for test in problem_data['tests']:
            resource_sets.append({int(r[1:]) for r in test['resources']})
        model["resources"] = resource_sets

    return model

def write_output(result, problem_data, output_file):
    with open(output_file, 'w') as f:
        f.write(f"% Makespan : {result['makespan']}\n")
        
        if USE_SORTING:
            # Create a mapping from sorted index to original name
            sorted_to_original = {i: test['name'] for i, test in enumerate(problem_data['tests'])}
        
        for m in range(1, len(problem_data['machines']) + 1):
            tasks = []
            for i, (start, machine) in enumerate(zip(result['start_times'], result['assigned_machines'])):
                if machine == m:
                    if USE_SORTING:
                        original_name = sorted_to_original[i]
                        original_index = problem_data['original_order'][original_name]
                    else:
                        original_index = i
                    test = problem_data['tests'][i]
                    # Preserve the original order of resources
                    resources = [f"'{r}'" for r in test['resources']]
                    resources_str = f",[{','.join(resources)}]" if resources else ''
                    tasks.append((start, f"('t{original_index+1}',{start}{resources_str})"))
            if tasks:
                sorted_tasks = [task[1] for task in sorted(tasks, key=lambda x: x[0])]
                f.write(f"machine( 'm{m}', {len(sorted_tasks)}, [{', '.join(sorted_tasks)}])\n")

def print_debug_info(problem_data):
    print("\nTests:")
    for test in problem_data['tests']:
        print(f"  {test['name']}: duration={test['duration']}, machines={test['machines']}, resources={test['resources']}")
    print(f"\nMachines: {problem_data['machines']}")
    print(f"Resources: {problem_data['resources']}")
    print(f"\nNumber of tests: {len(problem_data['tests'])}")
    print(f"Number of machines: {len(problem_data['machines'])}")
    print(f"Number of resources: {len(problem_data['resources'])}")
    
    upper_bound = calculate_upper_bound(problem_data)
    lower_bound = calculate_lower_bound(problem_data)
    print(f"\nLower bound (minimum makespan): {lower_bound}")
    print(f"Upper bound (maximum makespan): {upper_bound}")

def generate_dzn_content(problem_data):
    content = []
    content.append(f"M = {len(problem_data['machines'])};")
    content.append(f"N = {len(problem_data['tests'])};")
    content.append(f"R = {len(problem_data['resources'])};")
    
    upper_bound = calculate_upper_bound(problem_data)
    lower_bound = calculate_lower_bound(problem_data)
    content.append(f"max_makespan = {upper_bound if upper_bound > lower_bound else round(upper_bound * 1.18)};")
    content.append(f"min_makespan = {lower_bound};")
    
    durations = [test['duration'] for test in problem_data['tests']]
    content.append(f"durations = {durations};")
    
    machine_sets = []
    all_machines = set(range(1, len(problem_data['machines']) + 1))
    for test in problem_data['tests']:
        if not test['machines']:
            machine_sets.append(str(all_machines))
        else:
            machine_set = "{" + ", ".join(str(int(m[1:])) for m in test['machines']) + "}"
            machine_sets.append(machine_set)
    content.append(f"machines = [{', '.join(machine_sets)}];")
    
    resource_sets = []
    for test in problem_data['tests']:
        resource_set = "{" + ", ".join(str(int(r[1:])) for r in test['resources']) + "}"
        resource_sets.append(resource_set)
    content.append(f"resources = [{', '.join(resource_sets)}];")
    
    return "\n".join(content)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Solve the scheduling problem or generate .dzn file.")
    parser.add_argument("input_file", help="Input file path")
    parser.add_argument("output_file", help="Output file path", nargs='?')
    parser.add_argument("--test", action="store_true", help="Run in test mode (no plotting or debug output)")
    parser.add_argument("--dzn", action="store_true", help="Create a .dzn file for the model and exit")
    parser.add_argument("--no-sort", action="store_true", help="Disable sorting of tests")
    args = parser.parse_args()

    USE_SORTING = not args.no_sort

    problem_data = read_input(args.input_file)
    
    if args.dzn:
        dzn_content = generate_dzn_content(problem_data)
        dzn_file = os.path.splitext(args.input_file)[0] + ".dzn"
        with open(dzn_file, "w") as f:
            f.write(dzn_content)
        print(f"Created .dzn file: {dzn_file}")
        sys.exit(0)  # Exit after creating the .dzn file
    
    if not args.output_file:
        print("Error: output_file is required when not using --dzn flag")
        sys.exit(1)

    model = create_minizinc_model(problem_data)

    if not args.test:
        print_debug_info(problem_data)
    
    solvers = ['com.google.ortools.sat', "chuffed", "gecode"]
    for solver_name in solvers:
        if not args.test:
            print(f"\nTrying solver: {solver_name}")
        
        result = binary_search_optimization(model, problem_data, solver_name, timeout=300)
        
        if result:
            if args.test:
                print(f"Makespan : {result['makespan']}")
            
            write_output(result, problem_data, args.output_file)
            if not args.test:
                print(f"Solution written to {args.output_file}")
                draw_schedule(problem_data, args.output_file)
            break
        else:
            if not args.test:
                print(f"Failed to find a solution with {solver_name}")
    
    if not result:
        if not args.test:
            print("Failed to find a solution with any solver.")