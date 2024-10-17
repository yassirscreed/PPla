# Test Scheduling Problem as a CSP

## Group -  22
- Yassir Yassin 100611
- Rodrigo Laia 102674

## Overview
This project implements a solution for the Test Scheduling Problem (TSP) as a Constraint Satisfaction Problem (CSP). The problem, originally presented as the Industrial Modelling Challenge at CP2015, involves scheduling multiple tests across various machines and resources to minimize the overall makespan.

## Problem Specification
The Test Scheduling Problem arises in the context of a testing facility where:
- Multiple tests need to be performed in minimum time
- Each test has a specific duration and must run on one machine
- Some tests are restricted to certain machines, while others can use any available machine
- Some tests require additional global resources
- The objective is to minimize the makespan (time between the start of the earliest test and the end of the latest test)

For a detailed problem description, see [CSPlib problem 073](https://www.csplib.org/Problems/prob073/).

## Project Goals
The main objectives of this project are:
1. Implement a Python program that solves the TSP using the MiniZinc CSP solver (version 2.8.5)
2. Minimize the makespan for given input data
3. Generate solutions in the specified output format

## Usage
To run the program:

```
python proj.py <input-file-name> <output-file-name>
```

### Input Format
The input file should be in Prolog-style format, containing:
- Comment lines with problem information (number of tests, machines, resources, and maximum makespan)
- Test descriptions (name, duration, required machines, required resources)

### Output Format
The output file will contain:
- Comment line with the calculated makespan
- Machine assignments, including the number of tests and details for each assigned test

## Requirements
- Python 3.11
- MiniZinc 2.8.5

## Implementation Details
- The solution is implemented in `proj.py`
- [MiniZinc Python](https://python.minizinc.dev/) may be used for integration with the MiniZinc solver
