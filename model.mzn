include "globals.mzn";

% Parameters
int: M;  % Number of machines
int: N;  % Number of tests
int: R;  % Number of resources

int: max_makespan;  % Maximum makespan (upper bound)
int: min_makespan;  % Minimum makespan (lower bound)

set of int: TESTS = 1..N;
set of int: MACHINES = 1..M;
set of int: RESOURCES = 1..R;

array[TESTS] of int: durations;
array[TESTS] of set of MACHINES: machines;
array[TESTS] of set of RESOURCES: resources;

% Decision Variables
array[TESTS] of var 0..max_makespan: start_times;
array[TESTS] of var MACHINES: assigned_machines;
var min_makespan..max_makespan: makespan;

% Auxiliary Variables
array[TESTS] of var 0..max_makespan: end_times;

array[TESTS, MACHINES] of int: task_resources;

% Auxiliary variable: for each task and machine, is the task assigned to that machine?
array[TESTS, MACHINES] of var 0..1: task_machine_assignment;

% Constraints

constraint forall(t in TESTS, m in MACHINES)(
    task_machine_assignment[t, m] = bool2int(assigned_machines[t] = m)
);

constraint forall(t in TESTS, m in MACHINES)(
    task_machine_assignment[t, m] <= task_resources[t, m]
);


% End times calculation
constraint forall(t in TESTS) (
    end_times[t] = start_times[t] + durations[t]
);

% Makespan definition
constraint makespan = max(end_times);

constraint forall(j in 1..N) (
    assigned_machines[j] in machines[j]
);


% Ensure assigned machines are compatible
constraint forall(t in TESTS) (
    task_resources[t, assigned_machines[t]] = 1
);

% Machine capacity constraint using cumulative
constraint forall(m in MACHINES)(
    cumulative(start_times,
               durations,
               [task_machine_assignment[t, m] | t in TESTS],
               1)
);

% experimentar symmetry breaking para reduzir o loop


% Resource constraints (using cumulative)
constraint forall(r in RESOURCES where exists(t in TESTS)(r in resources[t])) (
    cumulative(start_times,
               durations,
               [bool2int(r in resources[t]) | t in TESTS],
               1)
);


% Makespan constraint
constraint makespan = max(end_times);

% Redundant constraint: total duration must be less than or equal to makespan * number of machines
constraint sum(durations) <= makespan * M;

% Lower bound constraint
constraint makespan >= sum(durations) div M;

% Symmetry breaking constraints

constraint symmetry_breaking_constraint(
    lex_lesseq([start_times[i] | i in TESTS where card(machines[i]) = M],
               [start_times[j] | j in TESTS where card(machines[j]) = M])
);

constraint forall(i, j in TESTS where i < j /\ resources[i] = resources[j] /\ durations[i] = durations[j]) (
  start_times[i] <= start_times[j]
);

% Additional redundant constraints

% 4. Ensure all tasks start before the makespan minus their duration
constraint forall(t in TESTS) (
    start_times[t] <= makespan - durations[t]
);

% Ensure the maximum end time of any task is equal to the makespan
constraint max(end_times) = makespan;


% Search annotation
solve 
%:: seq_search([
%    int_search(assigned_machines, first_fail, indomain_random),
%    int_search(start_times, smallest, indomain_min),
%    int_search([makespan], input_order, indomain_min)
%])
%:: relax_and_reconstruct( start_times ++ assigned_machines, 60)
satisfy;

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