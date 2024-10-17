import os
import subprocess
import re

def extract_makespan(output):
    # Find all makespan values
    makespans = re.findall(r"Makespan \(.*?\) (\d+)", output)
    
    # If we found any makespans, convert them to integers
    if makespans:
        makespans = [int(m) for m in makespans]
        
    # Look for the "Best makespan" line
    best_match = re.search(r"Best makespan: (\d+)", output)
    
    if best_match:
        # If we found a "Best makespan" line, use that value
        return int(best_match.group(1))
    elif makespans:
        # If we didn't find a "Best makespan" line but found other makespans, return the minimum
        return min(makespans)
    else:
        # If we didn't find any makespans, return None
        return None

def extract_makespan_from_file(filename):
    with open(filename, 'r') as f:
        content = f.read()
        tests = content.split('--------------------------------------------------')
        results = {}
        for test in tests:
            match = re.search(r"Test: (.*?)\n.*?Makespan : (\d+)", test, re.DOTALL)
            if match:
                test_name = match.group(1).strip()
                makespan = int(match.group(2))
                results[test_name] = makespan
    return results

def run_tests():
    tests_dir = 'tests_script'
    tests = [f for f in os.listdir(tests_dir) if f.endswith('.pl') and os.path.isfile(os.path.join(tests_dir, f))]

    # Extract all makespans from test_output.txt
    expected_makespans = extract_makespan_from_file('test_output.txt')

    for test in tests:
        input_file = f"tests_script/{test}"
        output_file = f"Solutions/output.txt"
        
        print(f"\nRunning test: {test}")
        
        # Run the python_solution2.py script
        print(f"Running python script: python Solutions/python_solution2.py {input_file} {output_file}")
        process = subprocess.Popen(['python', 'Solutions/python_solution2.py', input_file, output_file], 
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait for the process to complete and capture output
        stdout, stderr = process.communicate()
        
        # Extract the makespan from the script output
        script_makespan = extract_makespan(stdout)
        
        # Get the expected makespan from the pre-extracted results
        expected_makespan = expected_makespans.get(test)
        
        # Compare the results
        if script_makespan is None:
            print(f"{test}: ERROR - Could not extract makespan from script output")
            print(f"Script output: {stdout}")
        elif expected_makespan is None:
            print(f"{test}: ERROR - Could not find expected makespan in test_output.txt")
        elif script_makespan == expected_makespan:
            print(f"{test}: PASS (Makespan: {script_makespan})")
        else:
            print(f"{test}: FAIL (Script: {script_makespan}, Expected: {expected_makespan})")

        if stderr:
            print(f"Error output: {stderr}")

if __name__ == "__main__":
    run_tests()