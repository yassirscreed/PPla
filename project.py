import minizinc
import numpy as np

# Read the input file
with open('input.txt', 'r') as file:
    lines = file.readlines()

# Parse the number of tests, machines, resources, and maximum makespan
data = {}
data['num_tests'] = int(lines[0].split(':')[1].strip())
data['num_machines'] = int(lines[1].split(':')[1].strip())
data['num_resources'] = int(lines[2].split(':')[1].strip())
data['max_makespan'] = int(lines[3].split(':')[1].strip())

# Print the parsed values for verification
print(f"Number of tests: {data['num_tests']}")
print(f"Number of machines: {data['num_machines']}")
print(f"Number of resources: {data['num_resources']}")
print(f"Maximum makespan: {data['max_makespan']}")

# Initialize dictionary with lists to store test data
data['names'] = []
data['durations'] = []
data['machines'] = []
data['resources'] = []

# Parse test data
for line in lines[4:]:
    parts = line.strip().split(',')
    
    # Extract test name, duration, machines, and resources
    test_name = parts[0].strip()
    duration = int(parts[1].strip())
    machine_list = [m.strip() for m in parts[2].strip('[]').split()]  # Parse machines
    resource_list = [r.strip() for r in parts[3].strip('[]').split()]  # Parse resources
    
    # Append values to respective lists in the dictionary
    data['names'].append(test_name)
    data['durations'].append(duration)
    data['machines'].append(machine_list)
    data['resources'].append(resource_list)

# Print the parsed test data for verification
print('Parsed Test Data:')
print(f"Names: {data['names']}")
print(f"Durations: {data['durations']}")
print(f"Machines: {data['machines']}")
print(f"Resources: {data['resources']}")

# Create a MiniZinc model
model = minizinc.Model()
