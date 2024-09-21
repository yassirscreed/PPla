from minizinc import Instance, Model, Solver
import numpy as np
import re

# Read the input file
with open('input.txt', 'r') as file:
    lines = file.readlines()

# Parse the number of tests, machines, resources, and maximum makespan
data = {}
data['num_tests'] = int(lines[0].split(':')[1].strip())
data['num_machines'] = int(lines[1].split(':')[1].strip())
data['num_resources'] = int(lines[2].split(':')[1].strip())  # This is not currently used in the model
data['max_makespan'] = int(lines[3].split(':')[1].strip())

# Initialize dictionary with lists to store test data
data['names'] = []
data['durations'] = []
data['machines'] = []
data['resources'] = []  # Not currently used in the model

# Function to clean up names (removes 'test(' and extracts only the test identifier)
def clean_name(raw_name):
    return re.search(r"’(\w+)’", raw_name).group(1)  # Extracts 't1', 't2', etc.

# Function to clean up machines/resources (removes unwanted characters and empty strings)
def clean_list(raw_str):
    # Replace non-standard quotes with standard single quotes
    raw_str = raw_str.replace('’', "'")
    
    # Remove brackets, parentheses, and extra characters
    items = [item.strip("'").strip('()').strip('[]').strip() for item in raw_str.strip('[]').split(',') if item.strip()]
    
    # Filter out empty strings and clean quotes
    items = [item.strip("'") for item in items if item]
    
    return items if items else []

# Parse test data
for line in lines[4:]:
    parts = line.strip().split(',')
    
    # Extract and clean test name, duration, machines, and resources
    test_name = clean_name(parts[0].strip())
    duration = int(parts[1].strip())
    
    machine_list = clean_list(parts[2].strip())  # Clean up machine list
    resource_list = clean_list(parts[3].strip())  # Clean up resource list (no brackets)

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

model = minizinc.Model()
model.add_file("model.mzn")  # Your MiniZinc model file

# Initialize the MiniZinc solver and instance
solver = None
instance = None
try:
    solver = minizinc.Solver.lookup("gecode")  # Ensure Gecode is installed
    instance = minizinc.Instance(solver, model)
except Exception as e:
    print(f"Error initializing MiniZinc solver or instance: {e}")

# Ensure that instance is created before setting parameters
if instance:
    # Pass input data to the MiniZinc instance
    instance["N"] = data['num_tests']
    instance["M"] = data['num_machines']
    instance["max_makespan"] = data['max_makespan']
    instance["durations"] = data['durations']
    instance["machines"] = data['machines']
    
    # Solve the MiniZinc model
    try:
        result = instance.solve()
        print(f"Solution: {result}")
        print(f"Makespan: {result['makespan']}")
        print(f"Assigned machines: {result['assigned_machines']}")
        print(f"Start times: {result['start_times']}")
    except Exception as e:
        print(f"Error solving MiniZinc model: {e}")
else:
    print("MiniZinc instance was not created. Ensure that the MiniZinc model file and solver are correctly configured.")