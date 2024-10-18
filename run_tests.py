# run_tests.py - Checks the output of the tests after running run.py vs the expected output from reference solution

import os
import subprocess
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import OrderedDict

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

def run_single_test(test, expected_makespans):
    input_file = f"tests_script/{test}"
    output_file = f"Solutions/output.txt"
    
    process = subprocess.Popen(['python', 'Solutions/python_solution2.py', input_file, output_file], 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    stdout, stderr = process.communicate()
    
    script_makespan = extract_makespan(stdout)
    expected_makespan = expected_makespans.get(test)
    
    result = {
        'test': test,
        'passed': False,
        'error': None,
        'makespan': script_makespan,
        'expected': expected_makespan,
        'stderr': stderr
    }

    if script_makespan is None:
        result['error'] = "Could not extract makespan from script output"
    elif expected_makespan is None:
        result['error'] = "Could not find expected makespan in test_output.txt"
    elif script_makespan <= expected_makespan:
        result['passed'] = True
    
    return result

def run_tests():
    tests_dir = 'tests_script'
    tests = [f for f in os.listdir(tests_dir) if f.endswith('.pl') and os.path.isfile(os.path.join(tests_dir, f))]

    expected_makespans = extract_makespan_from_file('test_output.txt')

    results = OrderedDict()
    passed_tests = 0
    failed_tests = []

    with ThreadPoolExecutor() as executor:
        future_to_test = {executor.submit(run_single_test, test, expected_makespans): test for test in tests}
        
        for future in as_completed(future_to_test):
            test = future_to_test[future]
            result = future.result()
            results[test] = result

    for test, result in results.items():
        print(f"\nRunning test: {test}")
        
        if result['error']:
            print(f"{test}: ERROR - {result['error']}")
            if result['error'] == "Could not extract makespan from script output":
                print(f"Script output: {result['stdout']}")
            failed_tests.append(test)
        elif result['passed']:
            print(f"{test}: PASS (Makespan: {result['makespan']})")
            passed_tests += 1
        else:
            print(f"{test}: FAIL (Expected: {result['expected']}, Our: {result['makespan']})")
            failed_tests.append(test)

        if result['stderr']:
            print(f"Error output: {result['stderr']}")

    total_tests = len(tests)

    # Print statistics
    print("\nTest Results:")
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {len(failed_tests)}")

    if failed_tests:
        print("\nFailed tests:")
        for test in failed_tests:
            print(f"- {test}")

if __name__ == "__main__":
    run_tests()
