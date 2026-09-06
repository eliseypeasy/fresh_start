import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pulp import LpProblem, LpVariable, LpMaximize, LpMinimize, lpSum, PULP_CBC_CMD, LpStatus
from pathlib import Path
import os

os.chdir(Path("Desktop/secrets/data/fresh_start/projects/scenario_simulation/"))
os.getcwd()

# Load the shared data written by the R script (run R first if this errors)
employees   = pd.read_csv("input_data/employees.csv")
eligibility = pd.read_csv("input_data/eligibility.csv")
preferences = pd.read_csv("input_data/preferences.csv")
tasks       = pd.read_csv("input_data/tasks.csv")

# Quick feasibility check, same as the R sanity check
print(f"Total available capacity: {employees['available_hours'].sum():.1f} hours")
print(f"Total task workload:      {tasks['duration_hours'].sum():.1f} hours")
print(tasks['type'].value_counts())

# Scenario multiplier, same idea as the R version
scenario_multiplier = 1.0
tasks_scenario = tasks.copy()
tasks_scenario['duration_hours'] *= scenario_multiplier

employee_ids = employees['employee_id'].tolist()
task_ids = tasks_scenario['task_id'].tolist()

# Fast membership lookups instead of R's paste()-based matching
eligible_pairs = set(zip(eligibility['employee_id'], eligibility['task_type']))
preferred_pairs = set(zip(preferences['employee_id'], preferences['task_type_preferred']))

task_type = tasks_scenario.set_index('task_id')['type'].to_dict()
task_duration = tasks_scenario.set_index('task_id')['duration_hours'].to_dict()
available_hours = employees.set_index('employee_id')['available_hours'].to_dict()

feasible = {(e, t): int((e, task_type[t]) in eligible_pairs) for e in employee_ids for t in task_ids}
pref = {(e, t): int((e, task_type[t]) in preferred_pairs) for e in employee_ids for t in task_ids}


def extract_solution(x, model_name):
    rows = [
        {"employee_id": e, "task_id": t, "task_type": task_type[t],
         "duration_hours": task_duration[t], "pref": pref[(e, t)], "model": model_name}
        for (e, t), var in x.items() if var.value() > 0.5
    ]
    return pd.DataFrame(rows)


# --- Version 1: maximize preference matches ---
prob_pref = LpProblem("Preference_Maximizing", LpMaximize)

# Only creating variables for feasible pairs enforces eligibility directly —
# no separate constraint needed (this replaces x[e,t] <= feasible_mat[e,t] in R)
x_pref = {(e, t): LpVariable(f"x_{e}_{t}", cat="Binary")
          for e in employee_ids for t in task_ids if feasible[(e, t)] == 1}

prob_pref += lpSum(pref[(e, t)] * x_pref[(e, t)] for (e, t) in x_pref)

for t in task_ids:
    prob_pref += lpSum(x_pref[(e, t)] for e in employee_ids if (e, t) in x_pref) == 1

for e in employee_ids:
    prob_pref += lpSum(task_duration[t] * x_pref[(e, t)]
                        for t in task_ids if (e, t) in x_pref) <= available_hours[e]

# timeLimit (seconds) + gapRel accept a near-optimal answer instead of grinding forever —
# the Python equivalent of the tm_limit/mip_gap fix from the R side
prob_pref.solve(PULP_CBC_CMD(msg=True, timeLimit=120, gapRel=0.02))
print("Preference model status:", LpStatus[prob_pref.status])

solution_preference = extract_solution(x_pref, "Preference-maximizing")

# --- Version 2: min-max fairness ---
prob_fair = LpProblem("Fairness_MinMax", LpMinimize)

x_fair = {(e, t): LpVariable(f"y_{e}_{t}", cat="Binary")
          for e in employee_ids for t in task_ids if feasible[(e, t)] == 1}
L = LpVariable("L", lowBound=0, cat="Continuous")

prob_fair += L

for t in task_ids:
    prob_fair += lpSum(x_fair[(e, t)] for e in employee_ids if (e, t) in x_fair) == 1

for e in employee_ids:
    workload_e = lpSum(task_duration[t] * x_fair[(e, t)] for t in task_ids if (e, t) in x_fair)
    prob_fair += workload_e <= L
    prob_fair += workload_e <= available_hours[e]

prob_fair.solve(PULP_CBC_CMD(msg=True, timeLimit=120, gapRel=0.02))
print("Fairness model status:", LpStatus[prob_fair.status])

solution_fairness = extract_solution(x_fair, "Fairness (min-max)")

all_solutions = pd.concat([solution_preference, solution_fairness], ignore_index=True)

# ---- Comparison chart 1: workload composition per employee, faceted by model ----
assigned_workload = (
    all_solutions.groupby(['model', 'employee_id'])['duration_hours']
    .sum().reset_index().rename(columns={'duration_hours': 'assigned_task_hours'})
)

models = ["Preference-maximizing", "Fairness (min-max)"]
base_cols = employees[['employee_id', 'training_hours', 'meeting_overhead',
                        'research_hours', 'available_hours']].rename(
    columns={'meeting_overhead': 'meeting_hours'})

plot_frames = []
for m in models:
    df = base_cols.copy()
    df['model'] = m
    df = df.merge(
        assigned_workload[assigned_workload['model'] == m][['employee_id', 'assigned_task_hours']],
        on='employee_id', how='left'
    )
    df['assigned_task_hours'] = df['assigned_task_hours'].fillna(0)
    plot_frames.append(df)

workload_plot_data = pd.concat(plot_frames, ignore_index=True)

component_colors = {"Assigned Workload": "#2C7FB8", "Training": "#7FCDBB",
                     "Meetings": "#FEB24C", "Research": "#F03B20"}
component_map = {"assigned_task_hours": "Assigned Workload", "training_hours": "Training",
                  "meeting_hours": "Meetings", "research_hours": "Research"}

fig, axes = plt.subplots(2, 1, figsize=(10, 9), sharex=True, sharey=True)

for ax, m in zip(axes, models):
    sub = workload_plot_data[workload_plot_data['model'] == m].set_index('employee_id').loc[employee_ids]
    bottom = np.zeros(len(sub))
    for col, label in component_map.items():
        ax.bar(sub.index, sub[col], bottom=bottom, label=label, color=component_colors[label], width=0.7)
        bottom += sub[col].values
    ax.scatter(sub.index, sub['available_hours'], color='grey', zorder=5, s=40)
    for i in range(len(sub)):
        ax.hlines(sub['available_hours'].iloc[i], i - 0.35, i + 0.35, colors='grey', linestyles='dashed')
    ax.set_title(m, fontweight='bold')
    ax.set_ylabel("Hours")

axes[-1].set_xticklabels(sub.index, rotation=45, ha='right')
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, loc='lower center', ncol=4, bbox_to_anchor=(0.5, -0.02))
fig.suptitle("Employee Workload vs Available Hours", fontsize=14, fontweight='bold')
plt.tight_layout(rect=[0, 0.03, 1, 0.97])
plt.savefig("workload_comparison.png", dpi=150, bbox_inches='tight')
plt.show()

# ---- Comparison chart 2: what each model actually traded off ----
summary_rows = []
for m in models:
    sub_sol = all_solutions[all_solutions['model'] == m]
    hrs = assigned_workload[assigned_workload['model'] == m]['assigned_task_hours']
    summary_rows.append({
        "model": m,
        "Preference Satisfaction Rate": sub_sol['pref'].mean(),
        "Workload Imbalance (max - min hrs)": hrs.max() - hrs.min()
    })
summary_df = pd.DataFrame(summary_rows)

fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
colors = {"Preference-maximizing": "#2C7FB8", "Fairness (min-max)": "#F03B20"}

axes[0].bar(summary_df['model'], summary_df['Preference Satisfaction Rate'],
            color=[colors[m] for m in summary_df['model']])
axes[0].set_title("Preference Satisfaction Rate")
axes[0].yaxis.set_major_formatter(mticker.PercentFormatter(1.0))

axes[1].bar(summary_df['model'], summary_df['Workload Imbalance (max - min hrs)'],
            color=[colors[m] for m in summary_df['model']])
axes[1].set_title("Workload Imbalance (max - min hrs)")

for ax in axes:
    ax.tick_params(axis='x', rotation=15)

fig.suptitle("Trade-off Between the Two Model Versions", fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig("tradeoff_comparison.png", dpi=150, bbox_inches='tight')
plt.show()
