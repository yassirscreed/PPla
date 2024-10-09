#Alternative solution to the problem 
import sys
import matplotlib.pyplot as plt
from matplotlib import patheffects
import numpy as np

def parse_input(filename):
    tasks = {}
    machines_list = []
    resource_list = []

    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('%'):
                if 'Number of machines' in line:
                    num_machines = int(line.split(':')[1].strip())
                    machines_list = [f'm{i+1}' for i in range(num_machines)]
                elif 'Number of resources' in line:
                    num_resources = int(line.split(':')[1].strip())
                    resource_list = [f'r{i+1}' for i in range(num_resources)]
            elif line.startswith('test('):
                parts = line[5:-1].split(', ')
                test_name = parts[0].strip("'")
                test_duration = int(parts[1])
                test_machines = eval(parts[2])
                test_resources = eval(parts[3])

                tasks[test_name] = {
                    'duration': test_duration,
                    'machines': test_machines,
                    'resources': test_resources
                }

    return tasks, machines_list, resource_list

def uses_global_resource(tasks, task):
    return bool(tasks[task]['resources'])

def all_global_resources_available(global_res_next_available, tasks, task, time):
    for res in tasks[task]['resources']:
        if global_res_next_available[res] > time:
            return False
    return True

def reserve_global_resources(global_res_next_available, current_time, tasks, task):
    for res in tasks[task]['resources']:
        global_res_next_available[res] = current_time + tasks[task]['duration']

def sort_tasks(tasks, tasks_sort_method):
    tasks_durations = {key: tasks[key]['duration'] for key in tasks}

    if tasks_sort_method == 'SHORTEST_FIRST':
        return sorted(tasks_durations, key=tasks_durations.__getitem__)
    elif tasks_sort_method == 'LONGEST_FIRST':
        return sorted(tasks_durations, key=tasks_durations.__getitem__, reverse=True)
    elif tasks_sort_method == 'REQUIREMENTS_FIRST':
        task_names = list(tasks.keys())
        tasks_sorted = [tsk for tsk in task_names if tasks[tsk]["resources"]]
        tasks_sorted.extend([tsk for tsk in task_names if tsk not in tasks_sorted])
        return tasks_sorted

def run_schedule(tasks, machines_list, resource_list, tasks_sort_method):
    machine_next_available = {machine: 0 for machine in machines_list}
    global_res_next_available = {resource: 0 for resource in resource_list}
    current_time = 0
    results = []
    max_time = 0

    tasks_sorted = sort_tasks(tasks, tasks_sort_method)

    while tasks_sorted:
        assigned_tasks = []

        for current_task in tasks_sorted:
            if not tasks[current_task]['machines']:
                tasks[current_task]['machines'] = machines_list.copy()

            if (not uses_global_resource(tasks, current_task) or
                    all_global_resources_available(global_res_next_available, tasks, current_task, current_time)):

                for possible_machine in tasks[current_task]['machines']:
                    if machine_next_available[possible_machine] <= current_time:
                        assigned_tasks.append(current_task)
                        task_end_time = current_time + tasks[current_task]['duration']
                        max_time = max(max_time, task_end_time)

                        results.append((current_task, current_time, possible_machine))
                        machine_next_available[possible_machine] = task_end_time

                        if uses_global_resource(tasks, current_task):
                            reserve_global_resources(global_res_next_available, current_time, tasks, current_task)

                        break

        current_time += 1
        for task in assigned_tasks:
            tasks_sorted.remove(task)

    print('Makespan (', tasks_sort_method, ')', max_time)
    return max_time, results

def draw_schedule(tasks, machines_list, resource_list, schedule):
    activities = [[] for _ in range(len(machines_list))]
    for task, start_time, machine in schedule:
        machine_index = machines_list.index(machine)
        activities[machine_index].append({
            'name': task,
            'start_time': start_time,
            'duration': tasks[task]['duration'],
            'resources': tasks[task]['resources']
        })

    end = max(start_time + tasks[task]['duration'] for task, start_time, _ in schedule)
    n_machines = len(machines_list)
    width = min(20, max(12, end // 50))  # Limit max width
    height = min(12, max(6, n_machines // 2))  # Limit max height

    fig, ax = plt.subplots(figsize=(width, height))
    ax.set_xlim(0, end + 1)
    ax.set_ylim(0, n_machines + 1)

    colors = plt.cm.Set3(np.linspace(0, 1, len(resource_list) + 1))
    color_map = {r: colors[i] for i, r in enumerate(resource_list)}
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
    ax.set_yticklabels(machines_list)
    ax.set_xlabel('Time')
    ax.set_title(f"Makespan: {end}")
    plt.grid(True, which='both', axis='x', linestyle='--', linewidth=0.5)

    # Create legend for resources
    legend_elements = [plt.Rectangle((0,0),1,1, facecolor=color_map[r], edgecolor='black', label=r)
                       for r in resource_list]
    legend_elements.append(plt.Rectangle((0,0),1,1, facecolor=color_map[''], edgecolor='black', label='No resource'))
    ax.legend(handles=legend_elements, title='Resources', loc='center left', bbox_to_anchor=(1, 0.5))

    plt.tight_layout()
    plt.show()

def main():
    if len(sys.argv) != 3:
        print("Usage: python script.py <input-file-name> <output-file-name>")
        sys.exit(1)

    input_filename = sys.argv[1]
    output_filename = sys.argv[2]

    tasks, machines_list, resource_list = parse_input(input_filename)

    results = sorted([
        run_schedule(tasks, machines_list, resource_list, 'SHORTEST_FIRST'),
        run_schedule(tasks, machines_list, resource_list, 'LONGEST_FIRST'),
        run_schedule(tasks, machines_list, resource_list, 'REQUIREMENTS_FIRST')
    ])

    best_makespan, best_schedule = results[0]

    # Add this line to draw the schedule
    #draw_schedule(tasks, machines_list, resource_list, best_schedule)

    with open(output_filename, 'w') as output_file:
        output_file.write(f"% Makespan: {best_makespan}\n")
        machine_schedules = {m: [] for m in machines_list}
        for task, start_time, machine in best_schedule:
            machine_schedules[machine].append((task, start_time, tasks[task]['resources']))

        for machine in machines_list:
            schedule = sorted(machine_schedules[machine], key=lambda x: x[1])
            output_file.write(f"machine( '{machine}', {len(schedule)}, [")
            output_file.write(", ".join(f"('{task}',{start}" + (f",{resources}" if resources else "") + ")"
                                        for task, start, resources in schedule))
            output_file.write("])\n")

    print("Best makespan:", best_makespan)

if __name__ == '__main__':
    main()