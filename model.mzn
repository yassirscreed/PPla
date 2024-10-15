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

array[MACHINES] of var 0..max_makespan: machine_end_times;
array[RESOURCES] of var 0..max_makespan: resource_end_times;


% Constraints
% End times calculation
constraint forall(t in TESTS) (
    end_times[t] = start_times[t] + durations[t]
);

% Makespan definition
constraint makespan = max(end_times);

constraint forall(j in 1..N) (
    assigned_machines[j] in machines[j]
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

% Machine end times
constraint forall(m in MACHINES) (
    machine_end_times[m] = max([end_times[t] | t in TESTS where assigned_machines[t] = m] ++ [0])
);

% Resource end times
constraint forall(r in RESOURCES) (
    resource_end_times[r] = max([end_times[t] | t in TESTS where r in resources[t]] ++ [0])
);

% Makespan constraints
constraint makespan = max(machine_end_times);
constraint makespan = max(resource_end_times);

% Redundant constraint: total duration must be less than or equal to makespan * number of machines
constraint sum(durations) <= makespan * M;

% Lower bound constraint
constraint makespan >= max(resource_end_times);
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
solve %:: seq_search([
 % int_search(assigned_machines, first_fail, indomain_min),
 % int_search(start_times, smallest, indomain_split),
%  int_search([makespan], input_order, indomain_min)
%])
%:: restart_linear(1000)
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