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

% Constraints
% End times calculation
constraint forall(t in TESTS) (
    end_times[t] = start_times[t] + durations[t]
);

% Makespan definition
constraint makespan = max(end_times);

% Machine assignment, Olhar para esta !!!
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



% Symmetry breaking constraints

% 1. Symmetry breaking for tasks sharing all their machine choices
constraint forall(t1, t2 in TESTS where t1 < t2 /\ machines[t1] = machines[t2] /\ card(machines[t1]) > 0) (
    start_times[t1] <= start_times[t2]
);

% 2. Symmetry breaking for tasks with the same duration and overlapping machine choices
constraint forall(t1, t2 in TESTS where t1 < t2 /\ durations[t1] = durations[t2] /\ card(machines[t1] intersect machines[t2]) > 0) (
    lex_lesseq([start_times[t1], assigned_machines[t1]], [start_times[t2], assigned_machines[t2]])
);

% 3. Symmetry breaking: order tasks on the same machine (modified for our model)
constraint forall(m in MACHINES) (
    forall(t1, t2 in TESTS where t1 < t2 /\ card(machines[t1]) = 1 /\ card(machines[t2]) = 1 /\ machines[t1] = machines[t2]) (
        (assigned_machines[t1] = m /\ assigned_machines[t2] = m) -> start_times[t1] < start_times[t2]
    )
);

% Additional redundant constraints

% 4. Ensure all tasks start before the makespan minus their duration
constraint forall(t in TESTS) (
    start_times[t] <= makespan - durations[t]
);

% 5. Ensure the sum of all task durations is at least equal to the makespan
constraint sum(durations) >= makespan;

% 6. Ensure the maximum end time of any task is equal to the makespan
constraint max(end_times) = makespan;

% 7. Ensure the minimum start time plus the minimum duration is less than or equal to the makespan
constraint min(start_times) + min(durations) <= makespan;

% Search annotation
solve :: seq_search([
    int_search(assigned_machines, first_fail, indomain_min),
    int_search(start_times, smallest, indomain_split),
    int_search([makespan], input_order, indomain_min)
])
:: relax_and_reconstruct(start_times ++ assigned_machines, 70)
minimize makespan;

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
