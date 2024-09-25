include "globals.mzn";

% PARAMETERS
int: M;  % Number of machines
int: N;  % Number of tests
int: R;  % Number of resources

array[1..N] of int: durations;
array[1..N] of set of 1..M: machines;
array[1..N] of set of 1..R: resources;

% Calculate the maximum possible makespan
int: max_makespan = sum(durations);

% VARIABLES
array[1..N] of var 0..max_makespan: start_times;
array[1..N] of var 1..M: assigned_machine;

var 0..max_makespan: makespan;

% DERIVED VARIABLES
array[1..N] of var 0..max_makespan: end_times;
constraint forall(t in 1..N) (end_times[t] = start_times[t] + durations[t]);

% Priority scores for search heuristic
array[1..N] of int: priority_scores = [
    durations[t] * 100 + 
    card(resources[t]) * 10 + 
    (M - card(machines[t]))
    | t in 1..N
];

% Custom disjunctive predicate
predicate custom_disjunctive(array[int] of var bool: b,
                             array[int] of var int: s,
                             array[int] of int: d) =
    forall (i,j in index_set(s) where i<j) (
        not b[i] \/ not b[j] \/
        s[i] + d[i] <= s[j] \/
        s[j] + d[j] <= s[i]
    );

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

% Makespan definition
constraint makespan = max(end_times);

% No overlapping on the same machine (using custom_disjunctive)
constraint
    forall(m in 1..M) (
        let {
            array[1..N] of var bool: on_machine = [assigned_machine[t] = m | t in 1..N]
        } in
        custom_disjunctive(on_machine, start_times, durations)
    );

% No overlap of tasks using the same resource across all machines
constraint
    forall(r in 1..R) (
        let {
            array[1..N] of var bool: uses_resource = [r in resources[t] | t in 1..N]
        } in
        custom_disjunctive(uses_resource, start_times, durations)
    );

% Redundant constraint: cumulative for better machine utilization
constraint
    cumulative(start_times, durations, [1 | i in 1..N], M);

% Symmetry breaking: order tasks on the same machine
constraint
    forall(m in 1..M) (
        forall(t1, t2 in 1..N where t1 < t2 /\ card(machines[t1]) = 1 /\ card(machines[t2]) = 1 /\ machines[t1] = machines[t2]) (
            assigned_machine[t1] = m /\ assigned_machine[t2] = m -> start_times[t1] < start_times[t2]
        )
    );

% Lower bound on makespan
constraint
    makespan >= max([sum([durations[t] | t in 1..N where r in resources[t]]) | r in 1..R] ++ 
                    [sum([durations[t] | t in 1..N where m in machines[t]]) | m in 1..M]);

% Define the priority order
array[1..N] of int: priority_order = 
    reverse(sort_by([i | i in 1..N], [priority_scores[i] | i in 1..N]));

% Custom search annotation based on priority order
ann: priority_search(array[int] of var int: x) = 
    let {
        array[int] of var int: sorted_x = 
            [x[priority_order[i]] | i in 1..N where priority_order[i] in index_set(x)]
    } in
    int_search(sorted_x, dom_w_deg, indomain_min);

% SEARCH STRATEGY
solve :: seq_search([
    priority_search(start_times),
    priority_search([assigned_machine[t] | t in 1..N])
])
     :: relax_and_reconstruct(start_times ++ [assigned_machine[t] | t in 1..N], 30)
     minimize makespan;

% OUTPUT
output [
  "makespan = ", show(makespan), ";\n",
  "priority_order = ", show(priority_order), ";\n",
  "start_times = ", show(start_times), ";\n",
  "assigned_machine = ", show(assigned_machine), ";\n"
];