import sys
from minizinc import Instance, Model, Solver, Status
import re
from datetime import timedelta
import matplotlib.pyplot as plt
from matplotlib import patheffects
import numpy as np


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

def draw_schedule(problem_data, result):
    activities = [[] for _ in range(len(problem_data['machines']))]
    for i, (start, machine) in enumerate(zip(result['start_times'], result['assigned_machine'])):
        test = problem_data['tests'][i]
        activities[machine-1].append({
            'name': test['name'],
            'start_time': start,
            'duration': test['duration']
        })

    end = result['makespan']
    n_machines = len(problem_data['machines'])
    width = min(20, max(12, end // 50))  # Limit max width
    height = min(12, max(6, n_machines // 2))  # Limit max height

    fig, ax = plt.subplots(figsize=(width, height))
    ax.set_xlim(0, end + 1)
    ax.set_ylim(0, n_machines + 1)

    colors = plt.cm.Set3(np.linspace(0, 1, len(problem_data['resources']) + 1))
    color_map = {r: colors[i] for i, r in enumerate(problem_data['resources'])}
    color_map[''] = colors[-1]

    for i, activity_line in enumerate(activities, start=1):
        for activity in activity_line:
            start_time = activity['start_time']
            duration = activity['duration']
            end_time = start_time + duration
            test = next(t for t in problem_data['tests'] if t['name'] == activity['name'])
            color = color_map[test['resources'][0] if test['resources'] else '']

            # Draw the task bar
            ax.plot([start_time, end_time], [i, i], linewidth=16, solid_capstyle='butt', color=color)
            
            # Draw black task separators (vertical lines)
            ax.plot([start_time, start_time], [i - 0.2, i + 0.2], color='black', linewidth=0.5)
            ax.plot([end_time, end_time], [i - 0.2, i + 0.2], color='black', linewidth=0.5)

            # Add text
            text_x = (start_time + end_time) / 2
            text_y = i
            fontsize = max(6, min(10, 120 // len(activity_line)))  # Adjust font size based on number of tasks
            mytxt = ax.text(text_x, text_y, activity['name'], ha='center', va='center', color='white', fontsize=fontsize)
            mytxt.set_path_effects([patheffects.withStroke(linewidth=2, foreground='black')])

    ax.set_yticks(range(1, n_machines + 1))
    ax.set_yticklabels([f'M{i}' for i in range(1, n_machines + 1)])
    ax.set_xlabel('Time')
    ax.set_title(f"Makespan: {end} ")
    plt.grid(True, which='both', axis='x', linestyle='--', linewidth=0.5)

    # Create legend for resources
    legend_elements = [plt.Rectangle((0,0),1,1, facecolor=color_map[r], edgecolor='black', label=r)
                       for r in problem_data['resources']]
    legend_elements.append(plt.Rectangle((0,0),1,1, facecolor=color_map[''], edgecolor='black', label='No resource'))
    ax.legend(handles=legend_elements, title='Resources', loc='center left', bbox_to_anchor=(1, 0.5))

    plt.tight_layout()
    plt.show()


def create_minizinc_model(problem_data):
    model = Model()
    model.add_string(open("model.mzn").read())
    
    # Set up the parameters for the model
    model["M"] = len(problem_data['machines'])
    model["N"] = len(problem_data['tests'])
    model["R"] = len(problem_data['resources'])
    model["durations"] = [test['duration'] for test in problem_data['tests']]
    #model['max_makespan'] = sum(model["durations"]) + 1
    
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
            for i, (start, machine) in enumerate(zip(result['start_times'], result['assigned_machine'])):
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
    
    solvers = ['com.google.ortools.sat', "chuffed", "gecode"]
    for solver_name in solvers:
        print(f"\nTrying solver: {solver_name}")
        instance = Instance(Solver.lookup(solver_name), model)
        result = instance.solve(timeout=timedelta(seconds=10))
        
        if result.status == Status.OPTIMAL_SOLUTION or result.status == Status.SATISFIED:
            write_output(result, problem_data, output_file)
            print(f"Solution written to {output_file}")
            
            # Draw the schedule
            draw_schedule(problem_data, result)
            
            break
        elif result.status == Status.UNSATISFIABLE:
            print("The problem is unsatisfiable")
            break
        else:
            print(f"Solving process ended with status: {result.status}")
    
    if result.status not in [Status.OPTIMAL_SOLUTION, Status.SATISFIED, Status.UNSATISFIABLE]:
        print("Failed to find a solution with any solver.")