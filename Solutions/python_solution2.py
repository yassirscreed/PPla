import sys

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

    best_makespan = results[0][0]
    best_schedule = results[0][1]

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