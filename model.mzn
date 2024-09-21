% Number of machines
int: M;  % Number of machines

% Number of tasks
int: N;  % Number of tasks

% Number of resources
int: R;  % Number of resources

% Task durations
array[1..N] of int: durations;  % Task durations

% Machines each task can run on (array of sets)
array[1..N] of set of int: machines;  % Machines available for each task

% Resource usage for each task (set of resources each task uses)
array[1..N] of set of int: resources;  % Resources used by each task

% Makespan upper bound
int: max_makespan;  % Maximum makespan

% Decision variables: start time and machine assignment for each task
array[1..N] of var 0..max_makespan: start_times;
array[1..N] of var 1..M: assigned_machines;

% End times of the tasks
array[1..N] of var 0..max_makespan: end_times;

% Constraint: end time is start time plus duration
constraint forall(task in 1..N) (
  end_times[task] = start_times[task] + durations[task]
);

% Constraint: makespan is the maximum of the end times
var 0..max_makespan: makespan;
constraint makespan = max(end_times);

% Constraint: while the task is running on a machine, no other task can use that machine
constraint forall(m in 1..M) (
  forall(task1 in 1..N, task2 in 1..N where task1 < task2) (
    (assigned_machines[task1] = m /\ assigned_machines[task2] = m) ->
    (start_times[task1] >= end_times[task2] \/ start_times[task2] >= end_times[task1])
  )
);

% Modified Constraint: task must be assigned to one of its executable machines,
% or if the machine set is empty, it can run on any machine
constraint forall(task in 1..N) (
  (machines[task] = {}) -> (assigned_machines[task] >= 1 /\ assigned_machines[task] <= M) /\
  (machines[task] != {}) -> (assigned_machines[task] in machines[task])
);

% Modified Constraint: no two tasks that use a global resource can overlap
% If the resource set is empty, no constraint applies
constraint forall(t1 in 1..N, t2 in 1..N where t1 < t2) (
  (resources[t1] != {} /\ resources[t2] != {} /\ (resources[t1] intersect resources[t2] != {})) ->
  (start_times[t1] >= end_times[t2] \/ start_times[t2] >= end_times[t1])
);

solve minimize makespan;
