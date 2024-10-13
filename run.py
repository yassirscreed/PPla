import subprocess
import os
from pathlib import Path
import re

# Define the folder where the test files are located
folder = 'tests_script'

# Define the output file where results will be saved
output_file = 'test_output.txt'

# Time limit for each test (in seconds)
time_limit = 300  # 5 minutes

# Function to extract the numerical part from the filename
def extract_number(filename):
    match = re.search(r't(\d+)', filename)
    return int(match.group(1)) if match else float('inf')

# Open the output file for appending
with open(output_file, 'a') as out_file:
    # Get all the .pl files and sort them based on the numerical part
    test_files = sorted(Path(folder).glob('*.pl'), key=lambda f: extract_number(f.name))
    
    # Iterate through the sorted list of test files
    for test_file in test_files:
        test_name = test_file.name
        print(f'Running test: {test_name}')
        
        try:
            # Run the Python script with the test file, passing the output file
            result = subprocess.run(
                ['python', 'project.py', str(test_file), output_file, '--test'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=time_limit
            )
            
            # Write the test name and output to the output file
            out_file.write(f'Test: {test_name}\n')
            out_file.write(result.stdout.decode('utf-8') + '\n')

            # Run the checker
            checker_result = subprocess.run(
                ['python', 'checker.py', str(test_file), output_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=time_limit
            )
            
            # Write the checker output to the output file
            out_file.write("Checker output:\n")
            out_file.write(checker_result.stdout.decode('utf-8') + '\n')
            out_file.write(checker_result.stderr.decode('utf-8') + '\n')
            out_file.write('-' * 50 + '\n')  # Separator line

        except subprocess.TimeoutExpired:
            # If the process takes longer than the timeout, log the timeout
            out_file.write(f'Test: {test_name} (Timeout)\n')
            print(f'Test {test_name} exceeded the time limit and was skipped.')
            out_file.write('-' * 50 + '\n')  # Separator line
