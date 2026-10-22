
"""Few-shot examples for read-only PostgreSQL SQL generation.

The examples are illustrative patterns, not a description of the user's
real database. SQLPromptBuilder may inject SQL_EXAMPLES_PROMPT into the
SQL-generation prompt.
"""

SQL_EXAMPLES_PROMPT = r"""
POSTGRESQL EXAMPLES

IMPORTANT:
- These are illustrative patterns only, not actual tables in the user's database.
- Use a table, column, or relationship from an example only if it also exists
  in the schema supplied for the current request.
- Replace illustrative identifiers with exact identifiers from the supplied schema.
- Never invent tables, columns, relationships, stored values, or business metrics.
- If no schema object supports the requested answer, follow the unsupported-question
  rule from the system prompt and return:
  SELECT 'NOT_SUPPORTED' AS status;
- Return SQL only. All examples below are read-only PostgreSQL statements.
- Do not copy an example's schema into a real query unless that schema is supplied.
- Every query must pass the application's SQL validator before execution.

Example 1 — Retrieve a small number of records

Question: Show the first 10 customers.

Illustrative schema: customers(id, name, created_at)

SQL:
SELECT id, name, created_at
FROM customers
ORDER BY id
LIMIT 10;


Example 2 — Filter records by a value

Question: Show customers from Sana'a.

Illustrative schema: customers(id, name, city)

SQL:
SELECT id, name, city
FROM customers
WHERE city = 'Sana''a'
ORDER BY name
LIMIT 100;


Example 3 — Count records

Question: How many customers are there?

Illustrative schema: customers(id, name)

SQL:
SELECT COUNT(*) AS customer_count
FROM customers;


Example 4 — Group and aggregate

Question: Count customers in each city.

Illustrative schema: customers(id, city)

SQL:
SELECT
    city,
    COUNT(*) AS customer_count
FROM customers
GROUP BY city
ORDER BY customer_count DESC, city ASC;


Example 5 — Join using an explicitly declared foreign key

Question: Show each order with its customer's name.

Illustrative schema:
- customers(id, name)
- orders(id, customer_id, order_date)
- Foreign key: orders.customer_id references customers.id

SQL:
SELECT
    o.id AS order_id,
    c.name AS customer_name,
    o.order_date
FROM orders AS o
JOIN customers AS c
    ON c.id = o.customer_id
ORDER BY o.order_date DESC, o.id DESC
LIMIT 100;


Example 6 — Top results

Question: Which 5 products have the highest sales total?

Illustrative schema:
- order_items(product_id, quantity, unit_price)
- products(id, name)
- Foreign key: order_items.product_id references products.id

SQL:
SELECT
    p.id AS product_id,
    p.name AS product_name,
    SUM(oi.quantity * oi.unit_price) AS sales_total
FROM order_items AS oi
JOIN products AS p
    ON p.id = oi.product_id
GROUP BY p.id, p.name
ORDER BY sales_total DESC, p.id ASC
LIMIT 5;


Example 7 — Date range filter

Question: Count orders created during January 2026.

Illustrative schema: orders(id, created_at)

SQL:
SELECT COUNT(*) AS order_count
FROM orders
WHERE created_at >= DATE '2026-01-01'
  AND created_at < DATE '2026-02-01';


Example 8 — Find records with missing values

Question: Show customers whose email is missing.

Illustrative schema: customers(id, name, email)

SQL:
SELECT id, name
FROM customers
WHERE email IS NULL
ORDER BY id
LIMIT 100;


Example 9 — Average and maximum

Question: Show the average and highest salary by department.

Illustrative schema: employees(id, department, salary)

SQL:
SELECT
    department,
    AVG(salary) AS average_salary,
    MAX(salary) AS highest_salary
FROM employees
GROUP BY department
ORDER BY average_salary DESC, department ASC;


Example 10 — Unsupported request

Question: Show each customer's credit score.

Illustrative schema: customers(id, name, city)

SQL:
SELECT 'NOT_SUPPORTED' AS status;


Example 11 — Count records by department

Question: Count students in each department.

Illustrative schema: students(id, department)

SQL:
SELECT
    department,
    COUNT(*) AS student_count
FROM students
GROUP BY department
ORDER BY student_count DESC, department ASC;


Example 12 — Calculate a percentage of the total

Question: Show the number and percentage of students in each department.

Illustrative schema: students(id, department)

SQL:
SELECT
    department,
    COUNT(*) AS student_count,
    ROUND(
        COUNT(*) * 100.0
        / NULLIF((SELECT COUNT(*) FROM students), 0),
        2
    ) AS percentage
FROM students
GROUP BY department
ORDER BY student_count DESC, department ASC;


Example 13 — Use a CTE to calculate group counts

Question: Calculate the number of students in each department, then
return departments with more than 10 students.

Illustrative schema: students(id, department)

SQL:
WITH department_counts AS (
    SELECT
        department,
        COUNT(*) AS student_count
    FROM students
    GROUP BY department
)
SELECT
    department,
    student_count
FROM department_counts
WHERE student_count > 10
ORDER BY student_count DESC, department ASC;


Example 14 — Compare each group with the overall average

Question: Count students per department, calculate the average number
of students per department, and identify departments above average.

Illustrative schema: students(id, department)

SQL:
WITH department_counts AS (
    SELECT
        department,
        COUNT(*) AS student_count
    FROM students
    GROUP BY department
),
department_analysis AS (
    SELECT
        department,
        student_count,
        AVG(student_count) OVER () AS average_per_department
    FROM department_counts
)
SELECT
    department,
    student_count,
    ROUND(average_per_department::numeric, 2)
        AS average_per_department,
    student_count > average_per_department AS above_average
FROM department_analysis
ORDER BY student_count DESC, department ASC;


Example 15 — Filter groups using HAVING

Question: Show departments containing at least 5 students.

Illustrative schema: students(id, department)

SQL:
SELECT
    department,
    COUNT(*) AS student_count
FROM students
GROUP BY department
HAVING COUNT(*) >= 5
ORDER BY student_count DESC, department ASC;


Example 16 — Calculate a percentage without integer division

Question: Show the percentage of active customers among all customers.

Illustrative schema: customers(id, status)

SQL:
SELECT
    COUNT(*) FILTER (WHERE status = 'active') AS active_customers,
    COUNT(*) AS total_customers,
    ROUND(
        COUNT(*) FILTER (WHERE status = 'active') * 100.0
        / NULLIF(COUNT(*), 0),
        2
    ) AS active_percentage
FROM customers;


Example 17 — Use a subquery for a multi-stage calculation

Question: Find departments whose student count is above the average
student count across departments.

Illustrative schema: students(id, department)

SQL:
SELECT
    dc.department,
    dc.student_count
FROM (
    SELECT
        department,
        COUNT(*) AS student_count
    FROM students
    GROUP BY department
) AS dc
WHERE dc.student_count > (
    SELECT AVG(group_counts.student_count)
    FROM (
        SELECT COUNT(*) AS student_count
        FROM students
        GROUP BY department
    ) AS group_counts
)
ORDER BY dc.student_count DESC, dc.department ASC;


Example 18 — Rank grouped results

Question: Rank departments by student count.

Illustrative schema: students(id, department)

SQL:
WITH department_counts AS (
    SELECT
        department,
        COUNT(*) AS student_count
    FROM students
    GROUP BY department
)
SELECT
    department,
    student_count,
    RANK() OVER (ORDER BY student_count DESC) AS department_rank
FROM department_counts
ORDER BY department_rank ASC, department ASC;


Example 19 — Calculate average and total in one grouped query

Question: Show the number of employees, total salary, and average
salary for each department.

Illustrative schema: employees(id, department, salary)

SQL:
SELECT
    department,
    COUNT(*) AS employee_count,
    SUM(salary) AS total_salary,
    AVG(salary) AS average_salary
FROM employees
GROUP BY department
ORDER BY total_salary DESC NULLS LAST, department ASC;


Example 20 — Avoid dividing by zero

Question: Calculate the average order value for each customer.

Illustrative schema: orders(id, customer_id, total_amount)

SQL:
SELECT
    customer_id,
    SUM(total_amount) AS total_order_value,
    COUNT(*) AS order_count,
    SUM(total_amount) / NULLIF(COUNT(*), 0) AS average_order_value
FROM orders
GROUP BY customer_id
ORDER BY average_order_value DESC NULLS LAST, customer_id ASC;


Example 21 — Latest record per entity

Question: Show the latest order for each customer.

Illustrative schema: orders(id, customer_id, order_date)

SQL:
WITH ranked_orders AS (
    SELECT
        id,
        customer_id,
        order_date,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY order_date DESC NULLS LAST, id DESC
        ) AS row_num
    FROM orders
)
SELECT
    id,
    customer_id,
    order_date
FROM ranked_orders
WHERE row_num = 1
ORDER BY customer_id ASC;


Example 22 — Grouped results with a date filter

Question: Count orders per customer during January 2026.

Illustrative schema: orders(id, customer_id, created_at)

SQL:
SELECT
    customer_id,
    COUNT(*) AS order_count
FROM orders
WHERE created_at >= DATE '2026-01-01'
  AND created_at < DATE '2026-02-01'
GROUP BY customer_id
ORDER BY order_count DESC, customer_id ASC;


Example 23 — Compare each group with a calculated threshold

Question: Show departments whose student count exceeds the overall
average department size, including their difference from the average.

Illustrative schema: students(id, department)

SQL:
WITH department_counts AS (
    SELECT
        department,
        COUNT(*) AS student_count
    FROM students
    GROUP BY department
),
department_metrics AS (
    SELECT
        department,
        student_count,
        AVG(student_count) OVER () AS average_student_count
    FROM department_counts
)
SELECT
    department,
    student_count,
    ROUND(average_student_count::numeric, 2)
        AS average_student_count,
    ROUND(
        (student_count - average_student_count)::numeric,
        2
    ) AS difference_from_average
FROM department_metrics
WHERE student_count > average_student_count
ORDER BY difference_from_average DESC, department ASC;


FINAL REQUIREMENTS
- Follow the schema provided for the actual request, not the illustrative
  schemas above.
- Never infer a join from similarly named columns; require a declared
  relationship or an explicitly supplied schema relationship.
- Do not assume that example business metrics, values, date ranges, or columns
  exist in the real database.
- Use the simplest valid query that correctly answers the user's question.
- Use CTEs or subqueries when calculations require multiple aggregation levels.
- Do not mix aggregated and non-aggregated columns incorrectly.
- Do not nest aggregate functions at the same query level.
- Use window functions only when their semantics match the requested analysis.
- Return exactly one complete PostgreSQL read-only statement and no surrounding
  text, Markdown, explanations, or alternative queries.
- The application's SQL validator must validate the generated query before
  execution. These examples do not replace validation or authorization.
""".strip()
