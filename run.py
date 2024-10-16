import subprocess
import os
from pathlib import Path
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import sys

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

# Function to run a single test
def run_test(test_file):
    test_name = test_file.name
    print(f'Running test: {test_name}')
    
    # Create a unique output file for this test
    unique_output_file = f'output_{test_name}.txt'
    
    try:
        # Run the Python script with the test file
        process = subprocess.Popen(
            ['python', 'project.py', str(test_file), unique_output_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        try:
            stdout, stderr = process.communicate(timeout=time_limit)
            output = f'Test: {test_name}\n'
            output += stdout.decode('utf-8') + '\n'
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            output = f'Test: {test_name}\n'
            output += f'TIMEOUT: Test exceeded {time_limit} seconds\n'
        
        # Run the checker if the output file exists
        if os.path.exists(unique_output_file):
            checker_result = subprocess.run(
                ['python', 'checker.py', str(test_file), unique_output_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10
            )
            
            output += "Checker output:\n"
            output += checker_result.stdout.decode('utf-8') + '\n'
            output += checker_result.stderr.decode('utf-8') + '\n'
        else:
            output += "No output file generated. Skipping checker.\n"
        
        output += '-' * 50 + '\n'  # Separator line
    
    finally:
        # Clean up the unique output file
        if os.path.exists(unique_output_file):
            os.remove(unique_output_file)

    return test_name, output

# Main execution
if __name__ == "__main__":
    # Get all the .pl files and sort them based on the numerical part
    test_files = sorted(Path(folder).glob('*.pl'), key=lambda f: extract_number(f.name))
    
    results = {}
    
    # Use ThreadPoolExecutor to run tests concurrently
    with ThreadPoolExecutor() as executor:
        future_to_test = {executor.submit(run_test, test_file): test_file for test_file in test_files}
        
        try:
            for future in as_completed(future_to_test):
                test_name, output = future.result()
                results[test_name] = output
        except KeyboardInterrupt:
            print("Interrupted by user. Exiting gracefully.")
            sys.exit(1)
    
    # Write results to the output file in the order of test_files
    with open(output_file, 'w') as out_file:
        for test_file in test_files:
            if test_file.name in results:
                out_file.write(results[test_file.name])

    print("All tests completed. Results written to", output_file)
