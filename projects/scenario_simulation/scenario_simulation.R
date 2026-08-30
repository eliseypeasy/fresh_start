library(tidyverse)
library(ompr)
library(ompr.roi)
library(ROI.plugin.glpk)

set.seed(42)

# Employee types and the task types each type is qualified to handle
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

# Available capacity per employee: base hours minus meetings, training, research commitments
employees <- employees %>%
  mutate(
    base_hours       = 35,
    meeting_overhead = 4,
    training_hours   = c(6, 0, 0,  0, 5, 0,  0, 0, 4,  0),  # E1, E5, E9 are newer hires
    research_hours   = c(0, 0, 8,  0, 0, 0,  6, 0, 0,  0),  # E3, E7 on a research project
    available_hours  = base_hours - meeting_overhead - training_hours - research_hours
  )

# Long-format eligibility: one row per employee-task_type pair they're qualified for
eligibility <- employees %>%
  mutate(skills = map(type, ~ employee_types[[.x]])) %>%
  select(employee_id, skills) %>%
  unnest(skills) %>%
  rename(task_type = skills)

# Soft preferences: 5 employees each prefer 1-2 of the task types they're eligible for
set.seed(7)
pref_employees <- sample(employees$employee_id, 5)

preferences <- eligibility %>%
  filter(employee_id %in% pref_employees) %>%
  group_by(employee_id) %>%
  slice_sample(n = sample(1:2, 1)) %>%
  ungroup() %>%
  rename(task_type_preferred = task_type)

# Simulated week of inquiries, weighted by realistic volume and duration per type
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

# Quick feasibility check before solving anything
cat("Total available capacity:", sum(employees$available_hours), "hours\n")
cat("Total task workload:     ", round(sum(tasks$duration_hours), 1), "hours\n")
tasks %>% count(type) %>% print()

dir.create("data", showWarnings = FALSE)
write_csv(employees,   "data/employees.csv")
write_csv(eligibility, "data/eligibility.csv")
write_csv(preferences, "data/preferences.csv")
write_csv(tasks,       "data/tasks.csv")

# Scenario multiplier lets you stress-test the model later (e.g. 1.3 = a 30% busier week)
scenario_multiplier <- 1.0
tasks_scenario <- tasks %>%
  mutate(duration_hours = duration_hours * scenario_multiplier)

# Integer indices for the solver (ompr works on e/t indices, not IDs directly)
employee_index <- tibble(employee_id = employees$employee_id, e = seq_along(employees$employee_id))
task_index     <- tibble(task_id = tasks_scenario$task_id, t = seq_along(tasks_scenario$task_id))

# Build the full employee x task grid with feasibility and preference flags
feasible <- expand_grid(
  employee_id = employees$employee_id,
  task_id     = tasks_scenario$task_id
) %>%
  left_join(employee_index, by = "employee_id") %>%
  left_join(task_index,     by = "task_id") %>%
  left_join(tasks_scenario %>% select(task_id, task_type = type, duration_hours), by = "task_id") %>%
  mutate(
    feasible = ifelse(
      paste(employee_id, task_type) %in% paste(eligibility$employee_id, eligibility$task_type),
      1, 0
    ),
    pref = ifelse(
      paste(employee_id, task_type) %in% paste(preferences$employee_id, preferences$task_type_preferred),
      1, 0
    )
  ) %>%
  arrange(e, t) %>%
  select(e, t, feasible, pref, duration_hours)

nE <- nrow(employee_index)
nT <- nrow(task_index)

duration_mat <- matrix(feasible$duration_hours, nrow = nE, ncol = nT, byrow = TRUE)
feasible_mat <- matrix(feasible$feasible,       nrow = nE, ncol = nT, byrow = TRUE)
pref_mat     <- matrix(feasible$pref,           nrow = nE, ncol = nT, byrow = TRUE)

# --- Version 1: maximize preference matches, ignore balance ---
model_preference <- MIPModel() %>%
  add_variable(x[e, t], e = 1:nE, t = 1:nT, type = "binary") %>%
  set_objective(sum_expr(pref_mat[e, t] * x[e, t], e = 1:nE, t = 1:nT), "max") %>%
  add_constraint(sum_expr(x[e, t], e = 1:nE) == 1, t = 1:nT) %>%
  add_constraint(x[e, t] <= feasible_mat[e, t], e = 1:nE, t = 1:nT) %>%
  add_constraint(
    sum_expr(duration_mat[e, t] * x[e, t], t = 1:nT) <= employees$available_hours[e],
    e = 1:nE
  )

result_preference <- result <- solve_model(
  model_preference,
  with_ROI(solver = "glpk", tm_limit = 120000, verbose = TRUE, mip_gap = 0.02)
)

solution_preference <- get_solution(result_preference, x[e, t]) %>%
  filter(value > 0.5) %>%
  left_join(feasible %>% select(e, t, pref), by = c("e", "t")) %>%
  left_join(employee_index, by = "e") %>%
  left_join(task_index,     by = "t") %>%
  left_join(tasks_scenario, by = "task_id") %>%
  mutate(model = "Preference-maximizing")

# --- Version 2: minimize the maximum workload across employees, ignore preference ---
model_fairness <- MIPModel() %>%
  add_variable(x[e, t], e = 1:nE, t = 1:nT, type = "binary") %>%
  add_variable(L, type = "continuous", lb = 0) %>%
  set_objective(L, "min") %>%
  add_constraint(sum_expr(x[e, t], e = 1:nE) == 1, t = 1:nT) %>%
  add_constraint(x[e, t] <= feasible_mat[e, t], e = 1:nE, t = 1:nT) %>%
  add_constraint(sum_expr(duration_mat[e, t] * x[e, t], t = 1:nT) <= L, e = 1:nE) %>%
  add_constraint(
    sum_expr(duration_mat[e, t] * x[e, t], t = 1:nT) <= employees$available_hours[e],
    e = 1:nE
  )

result_fairness <- solve_model(
  model_fairness,
  with_ROI(solver = "glpk", tm_limit = 120000, verbose = TRUE, mip_gap = 0.02)
)

solution_fairness <- get_solution(result_fairness, x[e, t]) %>%
  filter(value > 0.5) %>%
  left_join(feasible %>% select(e, t, pref), by = c("e", "t")) %>%
  left_join(employee_index, by = "e") %>%
  left_join(task_index,     by = "t") %>%
  left_join(tasks_scenario, by = "task_id") %>%
  mutate(model = "Fairness (min-max)")

# ---- Comparison chart 1: workload composition per employee, faceted by model ----
all_solutions <- bind_rows(solution_preference, solution_fairness)

assigned_workload <- all_solutions %>%
  group_by(model, employee_id) %>%
  summarise(assigned_task_hours = sum(duration_hours), .groups = "drop")

workload_plot_data <- employees %>%
  select(employee_id, training_hours, meeting_overhead, research_hours, available_hours) %>%
  cross_join(tibble(model = c("Preference-maximizing", "Fairness (min-max)"))) %>%
  left_join(assigned_workload, by = c("employee_id", "model")) %>%
  mutate(assigned_task_hours = replace_na(assigned_task_hours, 0)) %>%
  rename(meeting_hours = meeting_overhead) %>%
  pivot_longer(
    cols = c(assigned_task_hours, training_hours, meeting_hours, research_hours),
    names_to = "component",
    values_to = "hours"
  ) %>%
  mutate(component = recode(component,
    assigned_task_hours = "Assigned Workload",
    training_hours      = "Training",
    meeting_hours        = "Meetings",
    research_hours       = "Research"
  ))

component_colors <- c(
  "Assigned Workload" = "#2C7FB8",
  "Training"           = "#7FCDBB",
  "Meetings"           = "#FEB24C",
  "Research"           = "#F03B20"
)

ggplot(workload_plot_data, aes(x = employee_id, y = hours, fill = component)) +
  geom_col(width = 0.7) +
  geom_point(aes(y = available_hours), color = "grey20", size = 2.2) +
  geom_segment(
    aes(
      x = as.numeric(factor(employee_id)) - 0.35,
      xend = as.numeric(factor(employee_id)) + 0.35,
      y = available_hours, yend = available_hours
    ),
    color = "grey20", linetype = "dashed", linewidth = 0.4
  ) +
  facet_wrap(~model, ncol = 1) +
  scale_fill_manual(values = component_colors) +
  labs(
    title = "Employee Workload vs Available Hours",
    subtitle = "Dashed line marks each employee's available capacity",
    x = NULL, y = "Hours", fill = NULL
  ) +
  theme_minimal(base_size = 12) +
  theme(
    axis.text.x = element_text(angle = 45, hjust = 1),
    strip.text = element_text(face = "bold"),
    panel.grid.minor = element_blank(),
    legend.position = "bottom"
  )

# ---- Comparison chart 2: what each model actually traded off ----
model_summary <- all_solutions %>%
  group_by(model) %>%
  summarise(
    preference_satisfaction = mean(pref, na.rm = TRUE),
    workload_imbalance_hrs  = {
      hrs <- assigned_workload %>% filter(model == first(model)) %>% pull(assigned_task_hours)
      max(hrs) - min(hrs)
    },
    .groups = "drop"
  ) %>%
  pivot_longer(cols = c(preference_satisfaction, workload_imbalance_hrs),
               names_to = "metric", values_to = "value") %>%
  mutate(metric = recode(metric,
    preference_satisfaction = "Preference Satisfaction Rate",
    workload_imbalance_hrs  = "Workload Imbalance (max - min hrs)"
  ))

ggplot(model_summary, aes(x = model, y = value, fill = model)) +
  geom_col(width = 0.6) +
  facet_wrap(~metric, scales = "free_y") +
  scale_fill_manual(values = c("Preference-maximizing" = "#2C7FB8", "Fairness (min-max)" = "#F03B20")) +
  labs(
    title = "Trade-off Between the Two Model Versions",
    subtitle = "Maximizing preference matches comes at the cost of balance, and vice versa",
    x = NULL, y = NULL
  ) +
  theme_minimal(base_size = 12) +
  theme(legend.position = "none", strip.text = element_text(face = "bold"))