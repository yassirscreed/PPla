% Optimized Test Scheduling Problem (TSP) MiniZinc Model

include "globals.mzn";

% PARAMETERS
int: M;  % Number of machines
int: N;  % Number of tests
int: R;  % Number of resources

array[1..N] of int: durations;
array[1..N] of set of 1..M: machines;
array[1..N] of set of 1..R: resources;

% PRIORITY CALCULATION
array[1..N] of int: priority_scores = [
    durations[t] * 1000 + 
    card(resources[t]) * 100 + 
    (M - card(machines[t])) * 10 
    | t in 1..N
];

% VARIABLES
array[1..N] of var 0..sum(durations): start_times;
array[1..N] of var 1..M: assigned_machine;
var 0..sum(durations): makespan;

% DERIVED VARIABLES
array[1..N] of var 0..sum(durations): end_times;
constraint forall(t in 1..N) (end_times[t] = start_times[t] + durations[t]);

% CONSTRAINTS

% Assign machines considering machine options
constraint
    forall(t in 1..N) (
        if card(machines[t]) > 0 then
            assigned_machine[t] in machines[t]
        else
            assigned_machine[t] in 1..M
        endif
    );

% Define makespan
constraint makespan = max(end_times);

% Redundant constraint: total duration must fit within makespan * machines
constraint
    makespan * M >= sum(durations);

% No overlapping on the same machine using cumulative
constraint
    forall(m in 1..M) (
        cumulative(start_times, 
                   [if m in machines[t] then durations[t] else 0 endif | t in 1..N],
                   [if m in machines[t] then 1 else 0 endif | t in 1..N],
                   1)
    );

% Resource constraints using cumulative
constraint
    forall(r in 1..R) (
        cumulative(start_times,
                   [if r in resources[t] then durations[t] else 0 endif | t in 1..N],
                   [if r in resources[t] then 1 else 0 endif | t in 1..N],
                   1)
    );

% SEARCH STRATEGY
solve :: int_search(start_times ++ [assigned_machine[t] | t in 1..N], 
                    first_fail, 
                    indomain_min, 
                    complete)
      minimize makespan;