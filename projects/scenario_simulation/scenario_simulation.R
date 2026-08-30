library(tidyverse)
library(tidyverse)
library(ompr)
library(ompr.roi)
library(ROI.plugin.glpk)
library(dplyr)
library(ggplot2)

set.seed(42)

# ---- 1. Employee types and their eligible task types ----
employee_types <- list(
  "Academic Advisor"  = c("General", "Academic"),
  "IT Support"         = c("General", "Technical"),
  "Financial Aid"      = c("General", "Financial"),
  "Senior Generalist"  = c("General", "Academic", "Technical")
)

employees <- tibble(
  employee_id = paste0("E", 1:10),
  type = c(rep("Academic Advisor", 3),
           rep("IT Support", 3),
           rep("Financial Aid", 3),
           "Senior Generalist")
)

# ---- 2. Capacity: base hours minus training/research/meetings ----
employees <- employees %>%
  mutate(
    base_hours       = 35,
    meeting_overhead = 4,                                   # everyone loses this
    training_hours   = c(6, 0, 0,  0, 5, 0,  0, 0, 4,  0),   # E1, E5, E9 are newer hires
    research_hours   = c(0, 0, 8,  0, 0, 0,  6, 0, 0,  0),   # E3, E7 on a research project
    available_hours  = base_hours - meeting_overhead - training_hours - research_hours
  )

# ---- 3. Eligibility (long format: one row per employee-tasktype pair they can do) ----
eligibility <- employees %>%
  mutate(skills = map(type, ~ employee_types[[.x]])) %>%
  select(employee_id, skills) %>%
  unnest(skills) %>%
  rename(task_type = skills)

# ---- 4. Preferences: 5 employees, 1-2 preferred types each, drawn from what they can do ----
set.seed(7)
pref_employees <- sample(employees$employee_id, 5)

preferences <- eligibility %>%
  filter(employee_id %in% pref_employees) %>%
  group_by(employee_id) %>%
  slice_sample(n = sample(1:2, 1)) %>%   # each prefers 1 or 2 of their eligible types
  ungroup() %>%
  rename(task_type_preferred = task_type)

# ---- 5. Weekly task instances ----
task_volume_weights <- c(General = 0.50, Academic = 0.20, Technical = 0.15, Financial = 0.15)
duration_ranges <- list(General = c(10, 20), Academic = c(30, 60),
                         Technical = c(30, 45), Financial = c(20, 50))

n_tasks <- 70
tasks <- tibble(
  task_id = paste0("T", 1:n_tasks),
  type = sample(names(task_volume_weights), n_tasks, replace = TRUE, prob = task_volume_weights)
) %>%
  rowwise() %>%
  mutate(duration_min = round(runif(1, duration_ranges[[type]][1], duration_ranges[[type]][2]))) %>%
  ungroup() %>%
  mutate(duration_hours = duration_min / 60)

# ---- 6. Sanity check: is this even feasible? ----
cat("Total available capacity:", sum(employees$available_hours), "hours\n")
cat("Total task workload:     ", round(sum(tasks$duration_hours), 1), "hours\n")

tasks %>% count(type) %>% print()

# ---- 7. Save for use in both R and Python ----
dir.create("Desktop/secrets/data", showWarnings = FALSE)
write_csv(employees, "projects/scenario_simulation/employees.csv")
write_csv(eligibility, "projects/scenario_simulation/eligibility.csv")
write_csv(preferences, "projects/scenario_simulation/preferences.csv")
write_csv(tasks, "projects/scenario_simulation/tasks.csv")

# ---- 6. Scenario multiplier ----
scenario_multiplier <- 1.0
tasks_scenario <- tasks %>%
  mutate(duration_hours = duration_hours * scenario_multiplier)

# ---- 7. Build indices ----
employee_index <- tibble(
  employee_id = employees$employee_id,
  e = seq_along(employees$employee_id)
)

task_index <- tibble(
  task_id = tasks_scenario$task_id,
  t = seq_along(tasks_scenario$task_id)
)

# ---- 8. FULL FEASIBILITY GRID (robust, no suffix issues) ----
feasible <- expand_grid(
  employee_id = employees$employee_id,
  task_id     = tasks_scenario$task_id
) %>%
  left_join(employee_index, by = "employee_id") %>%
  left_join(task_index,     by = "task_id") %>%
  left_join(tasks_scenario %>% 
              select(task_id, task_type = type, duration_hours),
            by = "task_id") %>%
  mutate(
    feasible = ifelse(
      paste(employee_id, task_type) %in%
        paste(eligibility$employee_id, eligibility$task_type),
      1, 0
    ),
    pref = ifelse(
      paste(employee_id, task_type) %in%
        paste(preferences$employee_id, preferences$task_type_preferred),
      1, 0
    )
  ) %>%
  arrange(e, t) %>%
  select(e, t, feasible, pref, duration_hours)

# ---- 9. Convert to matrices ----
nE <- length(employee_index$e)
nT <- length(task_index$t)

duration_mat <- matrix(feasible$duration_hours, nrow = nE, ncol = nT, byrow = TRUE)
feasible_mat <- matrix(feasible$feasible,       nrow = nE, ncol = nT, byrow = TRUE)
pref_mat     <- matrix(feasible$pref,           nrow = nE, ncol = nT, byrow = TRUE)

# ---- 10. Optimization model ----
balance_weight <- 0.1

model <- MIPModel() %>%
  # Creates a binary variable for every employee–task pair.
  add_variable(x[e, t], e = 1:nE, t = 1:nT, type = "binary") %>%

  # The solver tries to assign tasks to preferred employees where possible
  set_objective(sum_expr(pref_mat[e, t] * x[e, t], e = 1:nE, t = 1:nT), "max") %>%

  # For each task t, exactly one employee must be chosen.
  add_constraint(sum_expr(x[e, t], e = 1:nE) == 1, t = 1:nT) %>%
  
  # This prevents assigning tasks to employees who cannot perform them.
  add_constraint(x[e, t] <= feasible_mat[e, t], e = 1:nE, t = 1:nT) %>%
  
  # This enforces workload limits (workload <= available hours)
  add_constraint(
    sum_expr(duration_mat[e, t] * x[e, t], t = 1:nT) <= employees$available_hours[e],
    e = 1:nE
  )

# ---- 11. Solve ----
result <- solve_model(
  model,
  with_ROI(solver = "glpk", glpk_ctrl = list(tm_lim = 120000))
)

solution <- get_solution(result, x[e, t]) %>%
  filter(value > 0.5) %>%
  left_join(employee_index, by = "e") %>%
  left_join(task_index,     by = "t") %>%
  left_join(tasks_scenario, by = "task_id")

solution

# ---- 7. Optimisation model with min–max fairness ----
model <- MIPModel() %>%
  
  # Decision variables: assignment
  add_variable(x[e, t], e = 1:nE, t = 1:nT, type = "binary") %>%
  
  # New variable: maximum workload across all employees
  add_variable(L, type = "continuous", lb = 0) %>%
  
  # Objective: minimise the maximum workload (L)
  set_objective(L, "min") %>%
  
  # Each task must be assigned exactly once
  add_constraint(sum_expr(x[e, t], e = 1:nE) == 1, t = 1:nT) %>%
  
  # Only assign feasible tasks
  add_constraint(x[e, t] <= feasible_mat[e, t], e = 1:nE, t = 1:nT) %>%
  
  # Workload definition: workload of each employee must be ≤ L
  add_constraint(
    sum_expr(duration_mat[e, t] * x[e, t], t = 1:nT) <= L,
    e = 1:nE
  ) %>%
  
  # Capacity constraint: cannot exceed available hours
  add_constraint(
    sum_expr(duration_mat[e, t] * x[e, t], t = 1:nT) <= employees$available_hours[e],
    e = 1:nE
  )

  # ---- 11. Solve ----
result <- solve_model(
  model,
  with_ROI(solver = "glpk", glpk_ctrl = list(tm_lim = 120000))
)

solution <- get_solution(result, x[e, t]) %>%
  filter(value > 0.5) %>%
  left_join(employee_index, by = "e") %>%
  left_join(task_index,     by = "t") %>%
  left_join(tasks_scenario, by = "task_id")

solution


# ---- 8. Build workload dataset for stacked bar chart ----
assigned_workload <- solution %>%
  group_by(employee_id) %>%
  summarise(assigned_task_hours = sum(duration_hours), .groups = "drop")

workload_plot_data <- employees %>%
  left_join(assigned_workload, by = "employee_id") %>%
  mutate(
    assigned_hours = replace_na(assigned_task_hours, 0),
    training_hours = training_hours,
    meeting_hours  = meeting_overhead,
    research_hours = research_hours
  ) %>%
  select(employee_id, assigned_task_hours, training_hours, meeting_hours, research_hours, available_hours) %>%
  pivot_longer(
    cols = c(assigned_task_hours, training_hours, meeting_hours, research_hours),
    names_to = "component",
    values_to = "hours"
  )

# ---- 9. Stacked bar chart ----
ggplot(
  workload_plot_data %>%
    mutate(
      component = recode(
        component,
        assigned_hours = "Assigned Workload",
        training_hours = "Training",
        meeting_hours  = "Meetings",
        research_hours = "Research"
      )
    ),
  aes(x = employee_id, y = hours, fill = component)
) +
  geom_bar(stat = "identity") +
  geom_point(
    aes(y = available_hours),
    color = "red",
    size = 3
  ) +
  geom_segment(
    aes(
      x = as.numeric(factor(employee_id)) - 0.4,
      xend = as.numeric(factor(employee_id)) + 0.4,
      y = available_hours,
      yend = available_hours
    ),
    color = "red",
    linetype = "dashed"
  ) +
  labs(
    title = "Employee Workload vs Available Hours",
    subtitle = "Assigned workload + training + meetings + research vs capacity",
    x = "Employee",
    y = "Hours",
    fill = "Workload Component"
  ) +
  theme_minimal() +
  theme(axis.text.x = element_text(angle = 45, hjust = 1))

