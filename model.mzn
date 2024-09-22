include "globals.mzn";

% Parameters
int: M;  % Number of machines
int: N;  % Number of tests
int: R;  % Number of resources

set of int: TESTS = 1..N;
set of int: MACHINES = 1..M;
set of int: RESOURCES = 1..R;

array[TESTS] of int: durations;
array[TESTS] of set of MACHINES: machines;
array[TESTS] of set of RESOURCES: resources;

% Decision Variables
array[TESTS] of var 0..sum(durations): start_times;
array[TESTS] of var MACHINES: assigned_machines;
var 0..sum(durations): makespan;

% Auxiliary Variables
array[TESTS] of var 0..sum(durations): end_times;

% Constraints

% End times calculation
constraint forall(t in TESTS) (
    end_times[t] = start_times[t] + durations[t]
);

% Makespan definition
constraint makespan = max(end_times);

% Machine assignment
constraint forall(t in TESTS) (
    if card(machines[t]) > 0 then
        assigned_machines[t] in machines[t]
    else
        assigned_machines[t] in MACHINES
    endif
);

% Machine capacity (using cumulative)
constraint forall(m in MACHINES) (
    cumulative(start_times, 
               [durations[t] | t in TESTS], 
               [bool2int(assigned_machines[t] = m) | t in TESTS],
               1)
);

% Resource constraints (using cumulative)
constraint forall(r in RESOURCES) (
    cumulative(start_times,
               durations,
               [bool2int(r in resources[t]) | t in TESTS],
               1)
);

% Redundant constraint: total duration must be less than or equal to makespan * number of machines
constraint sum(durations) <= makespan * M;

% Balance load across machines
constraint forall(m in MACHINES)(
    count(assigned_machines, m) <= N div M + 1  % Limit the number of tasks per machine
);

% Search annotation
solve :: seq_search([
    int_search(assigned_machines, first_fail, indomain_min),
    int_search(start_times, smallest, indomain_min)
]) minimize makespan;

% Output
output [
    "% Makespan : \(makespan)\n"
] ++ [
    "machine( 'm\(m)', \(count(assigned_machines, m)), [" 
    ++ join(", ", [ 
        "('t\(t)',\(start_times[t])" 
        ++ if card(resources[t]) > 0 then 
            ",['" ++ join("','", [show(r) | r in resources[t]]) ++ "']" 
        else 
            "" 
        endif
        | t in TESTS where fix(assigned_machines[t]) = m
    ]) 
    ++ "])\n"
    | m in MACHINES
];
