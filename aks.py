import streamlit as st
import sqlite3
import pandas as pd

# =================== PAGE CONFIG ===================
st.set_page_config(
    page_title="BankSight Dashboard",
    page_icon="🏦",
    layout="wide"
)

# =================== CUSTOM CSS ===================
st.markdown("""
    <style>
        /* Background */
        [data-testid="stAppViewContainer"] {
            background: #2A2A60;
        }
        /* Sidebar */
        [data-testid="stSidebar"] {
            width: 380px !important;
            background-color: #12453;
        }
        /* Title styling */
        .title-text {
            font-size: 40px !important;
            font-weight: 900 !important;
        }
    </style>
""", unsafe_allow_html=True)


# =================== DATABASE CONNECTION ===================
@st.cache_resource
def get_connection(db_path: str = "bank_db"):
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

conn = get_connection()
cursor = conn.cursor()

def get_tables():
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    return [t[0] for t in cursor.fetchall()]

def get_table_df(table_name: str):
    return pd.read_sql_query(f"SELECT * FROM \"{table_name}\"", conn)

# =================== SIDEBAR ===================
st.sidebar.title("📚 BankSight Navigation")
menu = [
    "🏠 Introduction",
    "📋 View Tables",
    "🔍 Filter Data",
    "✏️ CRUD Operations",
    "🪙 Credit / Debit Simulation",
    "🧠 Analytical Insights",
    "👨🏻‍💻 About Creator"
]
choice = st.sidebar.radio("Go to:", menu)

# =================== INTRODUCTION ===================
if choice == "🏠 Introduction":
    st.markdown("<h1 class='title-text'>🏦 BankSight: Transaction Intelligence Dashboard</h1>", unsafe_allow_html=True)
    st.subheader("Project Overview")
    st.markdown("""
        <div class='section'>
        <p><b>BankSight</b> is a financial analytics dashboard built with Python, Streamlit, and SQLite.
        Explore customers, accounts, transactions, loans, and support tickets.
        Perform CRUD, simulate deposits/withdrawals, and run SQL analytics queries.</p>
        </div>
    """, unsafe_allow_html=True)
    st.subheader("Objectives")
    st.markdown("""
        - Explore customer & transaction behavior  
        - Enable CRUD operations on all datasets  
        - Provide financial simulation  
        - Offer analytical insights via SQL queries
    """)

# =================== VIEW TABLES ===================
elif choice == "📋 View Tables":
    st.title("📋 View Database Tables")
    tables = get_tables()
    if not tables:
        st.error("No tables found in the database.")
        st.stop()
    table_choice = st.selectbox("Select Table", tables)
    try:
        df = get_table_df(table_choice)
        st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"Error loading table: {e}")

# =================== FILTER DATA ===================
elif choice == "🔍 Filter Data":
    st.title("🔎 Filter Data")
    st.subheader("Select Table to Filter")

    # Get all tables
    tables = [t[0] for t in cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()]

    if not tables:
        st.error("❌ No tables found in the database.")
        st.stop()

    # Select table
    selected_table = st.selectbox("Select Table to Filter", tables)

    # Load table into DataFrame
    try:
        df = pd.read_sql_query(f'SELECT rowid, * FROM "{selected_table}"', conn)
    except Exception as e:
        st.error(f"❌ Error loading table: {e}")
        st.stop()

    st.subheader("Select columns and values to filter:")
    filters = {}

    for col in df.columns:
        # Skip rowid for filtering
        if col == "rowid":
            continue

        unique_vals = df[col].dropna().unique().tolist()

        # MULTISELECT FOR ALL FIELDS
        value = st.multiselect(f"{col}:", unique_vals)
        if value:
            filters[col] = value

    # Apply filters
    filtered_df = df.copy()
    for col, vals in filters.items():
        # Numeric safe conversion
        if pd.api.types.is_numeric_dtype(df[col]):
            try:
                vals = [df[col].dtype.type(v) for v in vals]
            except:
                st.warning(f"Invalid numeric value for {col}, skipping filter.")
                continue

        filtered_df = filtered_df[filtered_df[col].isin(vals)]

    st.subheader("Filtered Results")
    st.dataframe(filtered_df, use_container_width=True)


# =================== CRUD OPERATIONS ===================
elif choice == "✏️ CRUD Operations":
    st.title("✏️ CRUD Operations")

    # Load all tables
    def get_tables():
        tables = cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        return [t[0] for t in tables]

    tables = get_tables()

    selected_table = st.selectbox("Select Table", tables)

    # Load table into DataFrame
    df = pd.read_sql_query(f'SELECT rowid, * FROM "{selected_table}"', conn)

    action = st.radio("Choose Action", ["Create", "Read", "Update", "Delete"])

    # ------------------------------
    # 1️⃣ READ
    # ------------------------------
    if action == "Read":
        st.subheader("📄 Table Data")
        st.dataframe(df, use_container_width=True)

    # ------------------------------
    # 2️⃣ CREATE (INSERT)
    # ------------------------------
    elif action == "Create":
        st.subheader("➕ Add New Record")

        new_row = {}
        for col in df.columns:
            if col != "rowid":  # Avoid inserting rowid
                new_row[col] = st.text_input(f"Enter {col}")

        if st.button("➕ Insert Record"):
            columns = ", ".join([f'"{c}"' for c in new_row.keys()])
            placeholders = ", ".join(["?"] * len(new_row))
            
            try:
                cursor.execute(
                    f'INSERT INTO "{selected_table}" ({columns}) VALUES ({placeholders})',
                    list(new_row.values()),
                )
                conn.commit()
                st.success("✅ Record inserted successfully!")
            except Exception as e:
                st.error(f"❌ Insert failed: {e}")

    # ------------------------------
    # 3️⃣ UPDATE
    # ------------------------------
    elif action == "Update":
        st.subheader("✏ Update Record")

        if df.empty:
            st.warning("No records to update.")
            st.stop()

        rowid_list = df["rowid"].tolist()
        selected_rowid = st.selectbox("Select rowid to update", rowid_list)

        # Load record
        row = cursor.execute(
            f'SELECT * FROM "{selected_table}" WHERE rowid = ?',
            (selected_rowid,)
        ).fetchone()

        if not row:
            st.warning("Record not found.")
            st.stop()

        columns = df.columns[1:]  # skip rowid
        updated_row = {}

        for i, col in enumerate(columns):
            updated_row[col] = st.text_input(col, value=str(row[i]))

        if st.button("✔ Save Changes"):
            set_clause = ", ".join([f'"{c}" = ?' for c in updated_row.keys()])
            values = list(updated_row.values()) + [selected_rowid]

            try:
                cursor.execute(
                    f'UPDATE "{selected_table}" SET {set_clause} WHERE rowid = ?',
                    values
                )
                conn.commit()
                st.success("✅ Record updated successfully!")
            except Exception as e:
                st.error(f"❌ Update failed: {e}")

    # ------------------------------
    # 4️⃣ DELETE
    # ------------------------------
    elif action == "Delete":
        st.subheader("🗑 Delete Record")

        if df.empty:
            st.warning("No records to delete.")
            st.stop()

        rowid_list = df["rowid"].tolist()
        delete_rowid = st.selectbox("Select rowid to delete", rowid_list)

        if st.button("🗑 Delete"):
            try:
                cursor.execute(
                    f'DELETE FROM "{selected_table}" WHERE rowid = ?',
                    (delete_rowid,)
                )
                conn.commit()
                st.success("🗑 Record deleted successfully!")
            except Exception as e:
                st.error(f"❌ Delete failed: {e}")


# =================== CREDIT / DEBIT SIMULATION ===================
elif choice == "🪙 Credit / Debit Simulation":
    st.title("🪙 Credit / Debit Simulation (accounts table)")
    tables = get_tables()
    if "accounts" not in tables:
        st.error("accounts table not found.")
        st.stop()
    acc_df = get_table_df("accounts")
    customer_ids = acc_df["customer_id"].astype(str).unique().tolist()
    acc_id = st.selectbox("Select customer_id:", customer_ids)
    amount = st.number_input("Enter Amount (₹):", min_value=0.0, step=100.0)
    action_sim = st.radio("Select Action", ["Check Balance", "Deposit", "Withdraw"])

    if st.button("Submit"):
        if acc_id.strip() == "":
            st.error("Enter customer_id.")
            st.stop()
        if acc_id not in acc_df["customer_id"].astype(str).values:
            st.error("Customer ID not found.")
            st.stop()
        row = acc_df[acc_df["customer_id"].astype(str) == acc_id].iloc[0]
        current_balance = float(row["account_balance"] or 0.0)

        if action_sim == "Check Balance":
            st.success(f"💰 Current Balance: ₹{current_balance:,.2f}")
        elif action_sim == "Deposit":
            new_balance = current_balance + amount
            cursor.execute("UPDATE accounts SET account_balance = ? WHERE customer_id = ?", (new_balance, acc_id))
            conn.commit()
            st.success(f"✅ Deposited ₹{amount:,.2f}. New Balance: ₹{new_balance:,.2f}")
        elif action_sim == "Withdraw":
            if amount > current_balance:
                st.error("❌ Insufficient balance")
            else:
                new_balance = current_balance - amount
                cursor.execute("UPDATE accounts SET account_balance = ? WHERE customer_id = ?", (new_balance, acc_id))
                conn.commit()
                st.success(f"✅ Withdrawn ₹{amount:,.2f}. New Balance: ₹{new_balance:,.2f}")

# =================== ANALYTICAL INSIGHTS ===================
elif choice == "🧠 Analytical Insights":
    st.title("🧠 Analytical Insights")
    st.markdown("""Explore key SQL-driven insights from the <b>BankSight Database</b>. Select any question below 
                to run its corresponding SQL queries<br> and view live results.""",True)

    # List of questions
    questions = {
        "Q1: Number of customers and their average balance by city":
        """
        SELECT 
            customers.city AS City,
            COUNT(customers.customer_id) AS Total_Customers,
            AVG(accounts.account_balance) AS Average_Account_Balance
        FROM customers
        JOIN accounts 
            ON customers.customer_id = accounts.customer_id
        GROUP BY customers.city
        ORDER BY Total_Customers DESC
        ;
        """,

        "Q2: Top 10 customers by highest account balance":
        """
        SELECT 
            customers.customer_id,
            customers.name,
            SUM(accounts.account_balance) AS total_balance
        FROM customers
        JOIN accounts ON customers.customer_id = accounts.customer_id
        GROUP BY customers.customer_id, customers.name
        ORDER BY total_balance DESC
        LIMIT 10;
        """,

        "Q3: Branch holds the highest total account balance":
        """
        SELECT 
            branches.branch_name,
            SUM(accounts.account_balance) AS total_balance
            FROM accounts
            JOIN customers 
                ON accounts.customer_id = customers.customer_id
            JOIN branches
                ON customers.city = branches.city
            GROUP BY branches.branch_name
            ORDER BY total_balance DESC
            LIMIT 10;
        """,

        "Q4: Issue categories have the longest average resolution time":
        """
        SELECT 
            Issue_Category,
            COUNT(*) AS total_tickets,
            ROUND(AVG(JULIANDAY(Date_Closed) - JULIANDAY(Date_Opened)), 2) AS avg_resolution_days
        FROM support_tickets
        WHERE Status IN ('Closed', 'Resolved')
          AND Date_Closed IS NOT NULL 
          AND Date_Opened IS NOT NULL
        GROUP BY Issue_Category
        ORDER BY avg_resolution_days DESC;
        """,

        "Q5: Show all transactions with amount greater than ₹50,000":
        """
        SELECT txn_id AS Transaction_ID, customer_id AS Customer_ID, amount AS Amount
        FROM transactions
        WHERE amount > 50000
        ORDER BY amount DESC;
        """,

        "Q6: List all loans and their types":
        """
        SELECT Loan_ID, Customer_ID, Loan_Type, Loan_Amount
        FROM loans
        ORDER BY Loan_Amount DESC;
        """,

        "Q7: Count total number of credit cards issued per card type":
        """
        SELECT Card_Type, COUNT(*) AS Total_Cards
        FROM credit_cards
        GROUP BY Card_Type;
        """,

        "Q8: List customers who have loans above ₹5,00,000":
        """
            SELECT Customer_ID, Loan_ID, Loan_Amount
            FROM loans
            WHERE Loan_Amount > 500000
            ORDER BY Loan_Amount DESC;
        """,

        "Q9: Show all customers older than 30 years":
        """
        SELECT name, age, city, account_type
        FROM customers
        WHERE age > 50
        ORDER BY age DESC;
        """,

        "Q10: Show branches with total employees greater than 50":
        """
        SELECT DISTINCT Branch_Name, City, Total_Employees
        FROM branches
        WHERE Total_Employees > 50
        ORDER BY Total_Employees DESC;
        """,

        "Q11: Show accounts with balance between 40,000 and 50,000 along with customer name":
        """
        SELECT customers.name, accounts.account_balance
        FROM accounts
        JOIN customers ON accounts.customer_id = customers.customer_id
        WHERE accounts.account_balance BETWEEN 40000 AND 50000
        ORDER BY accounts.account_balance;
        """,

        "Q12: Show customers with more than 3 transactions over 50,000":
        """
        SELECT customers.name, COUNT(transactions.txn_id)
        FROM customers
        JOIN transactions ON customers.customer_id = transactions.customer_id
        WHERE transactions.amount > 50000
        GROUP BY customers.name
        HAVING COUNT(transactions.txn_id) > 3
        ORDER BY COUNT(transactions.txn_id) DESC;
        """,

        "Q13: Top 5 customers with the highest outstanding (non-closed) loan amounts":
        """
        SELECT
            customer_id,
            SUM(loan_amount) AS total_outstanding_amount
        FROM loans
        WHERE LOWER(TRIM(loan_status)) != 'Closed'
        GROUP BY customer_id
        ORDER BY total_outstanding_amount DESC
        LIMIT 5;
        """,

        "Q14: Average loan amount and interest rate by loan type (Personal, Auto, Home, etc.)":
        """
        SELECT 
            loan_type,
            AVG(loan_amount) AS average_loan_amount,
            AVG(interest_rate) AS average_interest_rate
        FROM loans
        GROUP BY loan_type;
        """,

        "Q15: Total transaction volume (sum of amounts) by transaction type":
        """
        SELECT 
            txn_type,
            SUM(amount) AS total_transaction_volume
        FROM transactions
        WHERE status = 'success'
        GROUP BY txn_type
        ORDER BY total_transaction_volume DESC;
        """,
    }

    # Dropdown
    selected_q = st.selectbox("Select a Question to Explore:", list(questions.keys()))

    st.markdown(f"### 🌼 {selected_q}")

    # Show SQL Query Block
    st.code(questions[selected_q], language='sql')

    # Execute Query
    try:
        df = pd.read_sql_query(questions[selected_q], conn)
        st.subheader("📄 Results:")
        st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error running query: {e}")



# =================== ABOUT CREATOR ===================
elif choice == "👨🏻‍💻 About Creator":
    st.title("👨🏻‍💻 About the Creator")
    st.markdown("""
    **Name:** ADITYA SHARMA  
    **Program:** Data Science  
    **Email:** adityashrma1821@gmail.com
    """)

# =================== CLEANUP ===================
# SQLite connection will be closed automatically when Streamlit exits.


