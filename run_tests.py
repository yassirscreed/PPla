import os
import subprocess
import multiprocessing
import re
import time
import shutil

def extract_makespan(output_file):
    try:
        with open(output_file, 'r') as f:
            first_line = f.readline().strip()
            match = re.search(r'Makespan\s*:\s*(\d+)', first_line)
            if match:
                return int(match.group(1))
    except FileNotFoundError:
        return None
    return None

def run_test(args):
    input_file, your_solution, reference_solution, temp_dir = args
    test_name = os.path.basename(input_file)
    print(f"Running test: {test_name}")

    # Run your solution with a timeout
    your_output = os.path.join(temp_dir, f"your_output_{test_name}.txt")
    start_time = time.time()
    try:
        subprocess.run(["python", your_solution, input_file, your_output, "--test"], capture_output=True, timeout=120)
    except subprocess.TimeoutExpired:
        print(f"Test {test_name} FAILED: Timeout (120 seconds)")
        return (test_name, None, None, "Timeout")

    # Run reference solution
    ref_output = os.path.join(temp_dir, f"ref_output_{test_name}.txt")
    subprocess.run(["python", reference_solution, input_file, ref_output], capture_output=True)

    # Extract makespans
    your_makespan = extract_makespan(your_output)
    ref_makespan = extract_makespan(ref_output)

    # Compare makespans
    if your_makespan is None or ref_makespan is None:
        result = "Failed (Could not extract makespan)"
    elif your_makespan <= ref_makespan:
        result = "Passed"
    else:
        result = "Failed"

    return (test_name, your_makespan, ref_makespan, result)

def main():
    test_dir = "tests_script"
    temp_dir = os.path.join(test_dir, "temp")
    your_solution = "project.py"
    reference_solution = os.path.join("Solutions", "python_solution2.py")

    # Create temp directory if it doesn't exist
    os.makedirs(temp_dir, exist_ok=True)

    test_files = [f for f in os.listdir(test_dir) if f.endswith('.pl')]
    args_list = [(os.path.join(test_dir, test_file), your_solution, reference_solution, temp_dir) for test_file in test_files]

    with multiprocessing.Pool() as pool:
        results = pool.map(run_test, args_list)

    failed_tests = []
    passed = 0
    total = len(results)

    print("\nTest Results:")
    print("-------------")
    print(f"{'Test Name':<20} {'Your Makespan':<15} {'Ref Makespan':<15} {'Result':<10}")
    print("-" * 60)

    for test_name, your_makespan, ref_makespan, result in results:
        your_makespan_str = str(your_makespan) if your_makespan is not None else "N/A"
        ref_makespan_str = str(ref_makespan) if ref_makespan is not None else "N/A"
        print(f"{test_name:<20} {your_makespan_str:<15} {ref_makespan_str:<15} {result:<10}")
        
        if result == "Passed":
            passed += 1
        else:
            failed_tests.append(test_name)

    print("\nSummary:")
    print(f"Total tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")

    if failed_tests:
        print("\nFailed tests (in order):")
        for test in failed_tests:
            print(f"- {test}")

    # Clean up temporary output files
    shutil.rmtree(temp_dir)

if __name__ == "__main__":
    main()
