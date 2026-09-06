"""
Python fundamentals warm-up, built around the same data you're using
in the assignment model. Work through top to bottom — later sections
assume earlier ones are filled in correctly.
"""

import pandas as pd

# ============================================================
# 1. CREATING A DATASET FROM SCRATCH
# ============================================================
# In R: tibble(col1 = c(...), col2 = c(...))
# In Python: a dictionary of lists, passed to pd.DataFrame()

# FILL IN: create a small dataset of 3 employees with columns
# 'employee_id' (E1, E2, E3) and 'hours' (any 3 numbers)
mini_employees = pd.DataFrame({
    "employee_id": ("E1", "E2", "E3"),
    "hours": ("24", "32", "36")
})

print(mini_employees)


# ============================================================
# 2. READING A CSV
# ============================================================
# In R: read_csv("data/employees.csv")
# In Python: pd.read_csv(...) — note the path is relative to
# wherever you RUN the script from, not where the file lives

# FILL IN: the path to the employees CSV you wrote from R
employees = pd.read_csv("input_data/employees.csv")

# Basic inspection — the pandas equivalents of R's glimpse()/str()
print(employees.head())       # first 5 rows, like head() in R
print(employees.shape)        # (rows, columns), like dim() in R
print(employees.dtypes)       # column types, like str() in R


# ============================================================
# 3. SUBSETTING / FILTERING
# ============================================================
# In R (dplyr): employees %>% filter(available_hours > 25)
# In Python (pandas): employees[employees['available_hours'] > 25]
# The condition inside the brackets creates a True/False mask,
# and pandas returns only the rows where it's True.

# FILL IN: filter employees to only those with more than 25 available hours
high_capacity = employees[employees['available_hours'] > 25]
print(high_capacity)

# In R: employees %>% select(employee_id, type)
# In Python: pass a LIST of column names in double brackets
# FILL IN: select just 'employee_id' and 'type' columns
id_and_type = employees[['employee_id', 'type']]
print(id_and_type)

# Combining both — filter rows AND select columns in one line
# FILL IN: employees with type == "IT Support", showing only employee_id and available_hours
it_support = employees[employees["type"] == "IT Support"][['employee_id', 'available_hours']]
print(it_support)


# ============================================================
# 4. GROUPING AND SUMMARISING
# ============================================================
# In R: employees %>% group_by(type) %>% summarise(avg = mean(available_hours))
# In Python: .groupby(...)[...].mean() — chain it step by step

# FILL IN: average available_hours per employee type
avg_by_type = employees.groupby('type')['available_hours'].mean()
print(avg_by_type)

avg_and_count = employees.groupby('type').agg(
    avg_available_hours=('available_hours', 'mean'),
    count=('available_hours', 'count')
)

print(avg_and_count)

# ============================================================
# 5. WRITING A FUNCTION
# ============================================================
# In R: my_func <- function(x, y) { x + y }
# In Python: def my_func(x, y): return x + y
# Indentation IS the function body in Python — there's no { } to mark it,
# so a wrong indent level is a real bug, not just a style issue.

def net_capacity(base_hours, meeting_overhead, training_hours, research_hours):
    """Return hours actually available after overheads are subtracted."""
    # FILL IN: the same subtraction you used in the R script
    return base_hours - meeting_overhead - training_hours - research_hours

# Test it against a row you can check by hand
print(net_capacity(35, 4, 6, 0))   # should match E1's available_hours in the CSV


# Now apply that function across every row of a DataFrame.
# In R: employees %>% mutate(check = base_hours - meeting_overhead - ...)
# In Python: employees.apply(lambda row: ..., axis=1)  — axis=1 means "one row at a time"

employees["net_check"] = employees.apply(
    # FILL IN: call net_capacity() using the right columns from `row`
    lambda row: net_capacity(row["base_hours"], row["meeting_overhead"], row["training_hours"], row["research_hours"]),
    axis=1
)

# This should be all True if your function and the CSV agree
print((employees["net_check"] == employees["available_hours"]).all())


# ============================================================
# 6. DICTIONARIES AND LIST/DICT COMPREHENSIONS
# ============================================================
# This is the biggest syntax jump from R, and it's used heavily in the
# solver script, so it's worth building comfort with it here first.
#
# A dictionary is like a NAMED LIST in R: lookup by key instead of position.
# lookup <- list(E1 = 29, E2 = 35) in R  ==  {"E1": 29, "E2": 35} in Python

# FILL IN: build a dictionary mapping employee_id -> available_hours
# Hint: pandas has a shortcut for this —
# df.set_index("key_col")["value_col"].to_dict()
hours_lookup = employees.set_index("employee_id")["available_hours"].to_dict()
print(hours_lookup)
print(hours_lookup["E1"])   # look up a single value by key, like lookup[["E1"]] in R

# A dict comprehension builds a dictionary in one line from a loop.
# This is the pattern behind `feasible = {(e, t): ... for e in ... for t in ...}`
# in the solver script — it looks dense at first, so build up to it:

# Step 1: an ordinary loop
doubled = {}
for emp_id, hrs in hours_lookup.items():
    doubled[emp_id] = hrs * 2

# Step 2: the same thing as a one-line comprehension
# FILL IN: rewrite the loop above as a dict comprehension
doubled_v2 = {emp_id: hrs * 2 for emp_id, hrs in hours_lookup.items()}

print(doubled == doubled_v2)   # should print True — same result, two ways of writing it


# ============================================================
# 7. PUTTING IT TOGETHER
# ============================================================
# Write a function that takes an employee type and returns their
# average available hours — combining sections 3, 4, and 5.

def avg_hours_for_type(df, employee_type):
    """Return the average available_hours for a given employee type."""
    # FILL IN: filter df to rows matching employee_type, then average available_hours
    subset = df[____]
    return subset[____].mean()

# Test it
print(avg_hours_for_type(employees, "Academic Advisor"))