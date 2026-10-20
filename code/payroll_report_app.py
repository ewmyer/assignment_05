"""
payroll_report_app.py — the quarter at a glance, for someone who never opens
a terminal.

Every Friday since September the office manager at Salt City Coffee has downloaded
a payroll export from the Assignment 04 app; before that she typed the same file
by hand. The owner now wants to know where the hours went this quarter, the
accountant wants pay by month and department, and the manager wants to see who
has been missing shifts. This page answers all three from the pile of exports.

Same shape as Assignment 04: the page *assembles* the pipeline — one call to
`build_history` does the cleaning — and then shows the reports, filtered by the
department and dates the user picks.

Run it:  Run and Debug -> "Streamlit Run: Current File"
Test it: pytest tests/test_pipeline.py -k app
"""
import streamlit as st

from payroll import (
    build_history,
    hours_grid,
    load_employees,
    load_export,
    missed_weeks,
    pay_by_month,
    summarize_employees,
)

st.title("Salt City Coffee — Quarterly Payroll Report")
st.write("Upload payroll exports to review hours, pay, and missed weeks.")

employees = load_employees()
uploads = st.file_uploader(
    "Upload weekly payroll exports",
    type="csv",
    accept_multiple_files=True,
    key="exports",
)

if uploads:
    history = build_history([load_export(upload) for upload in uploads], employees)
    unmatched = history.loc[
        history["department"].isna(), "employeeid"
    ].dropna().unique()
    if len(unmatched):
        st.warning(f"These employee IDs are not on the roster: {', '.join(unmatched)}")

    matched = history.loc[history["department"].notna()]
    departments = ["All", *sorted(matched["department"].unique())]
    department = st.selectbox("Department", departments, key="department")

    first_date = matched["pay_date"].min().date()
    last_date = matched["pay_date"].max().date()
    date_range = st.date_input(
        "Pay date range",
        value=(first_date, last_date),
        key="dates",
    )
    start_date, end_date = date_range

    selected = matched.loc[
        matched["pay_date"].dt.date.between(start_date, end_date)
    ]
    if department != "All":
        selected = selected.loc[selected["department"] == department]

    st.subheader(f"{department} payroll")
    metric_columns = st.columns(4)
    metric_columns[0].metric("Weeks", selected["week_ending"].nunique())
    metric_columns[1].metric("Employees", selected["employee_id"].nunique())
    metric_columns[2].metric("Total hours", f"{selected['hours_worked'].sum():,.2f}")
    metric_columns[3].metric("Total gross pay", f"${selected['gross_pay'].sum():,.2f}")

    monthly_pay = pay_by_month(selected)
    st.bar_chart(monthly_pay, x="month")
    st.dataframe(summarize_employees(selected))
    grid = hours_grid(selected)
    st.dataframe(grid)
    st.dataframe(missed_weeks(grid))
    st.download_button(
        "Download pay by month",
        data=monthly_pay.to_csv(index=False),
        file_name="pay_by_month.csv",
        mime="text/csv",
        key="download",
    )
