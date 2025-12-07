import streamlit as st
import sqlite3
import pandas as pd
import json
from pandas import json_normalize

# --------------------- PAGE CONFIG ------------------------
st.set_page_config(
    page_title="BankSight Dashboard",
    page_icon="🏦",
    layout="wide",
)

# --------------------- CUSTOM CSS -------------------------
st.markdown("""
    <style>
        /* Background */
        [data-testid="stAppViewContainer"] {
            background: #2A2A40;
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

# --------------------- DATABASE CONNECTION ----------------
@st.cache_resource
def get_connection():
    return sqlite3.connect("bank_db", check_same_thread=False)

conn = get_connection()
cursor = conn.cursor()



# --------------------- SIDEBAR MENU -----------------------
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

# ===============================================================
#                     1️⃣ INTRODUCTION PAGE
# ===============================================================


def get_tables():
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
    )
    return [t[0] for t in cursor.fetchall()]


if choice == "🏠 Introduction":
    st.markdown("""
<h1 style='font-size: 45px; font-weight: 900;'>
🏛️ BankSight: Transaction Intelligence Dashboard
</h1>
""",True)


    st.subheader("Project Overview")
    st.markdown("""
<p style='font-size:20px;'>
<b>BankSight</b> is a financial analytics system built using <b>Python, Streamlit, and SQLite3</b>.
It allows users to explore customer, account, transaction, loan, and support data,
perform CRUD operations, simulate deposits/withdrawals, and view analytical insights.
</p>
""",True)

    st.subheader("Objectives:")
    st.markdown("""
    - Understand customer & transaction behavior  
    - Detect anomalies and potential fraud  
    - Enable CRUD operations on all datasets  
    - Provide meaningful financial analytics  
    """)

# ===============================================================
#                2️⃣ VIEW TABLES (LOCAL CSV + JSON FILES)
# ===============================================================
elif choice == "📋 View Tables":
    st.title("📋 View Database Tables")


    # Your 7 table names
  
    table_choice = st.selectbox("Select a Table", list(tables.keys()))

    file_path = tables[table_choice]

    try:
        # Detect file type
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path)

        elif file_path.endswith(".json"):
            df = pd.read_json(file_path)

        st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error(f"Error loading file: {e}")

# ===============================================================
#                     3️⃣ FILTER DATA (DYNAMIC)
# ===============================================================
elif choice == "🔍 Filter Data":
    st.title("🔎 Filter Data")
    st.subheader("Select Table to Filter")

    # File paths
    tables = {
        "customers": r"C:\\Users\\Aditya Sharma\\Downloads\\customers.csv",
        "accounts": r"C:\\Users\\Aditya Sharma\\Downloads\\accounts.csv",
        "transactions": r"C:\\Users\\Aditya Sharma\\Downloads\\transactions.csv",
        "loans": r"C:\\Users\\Aditya Sharma\\Downloads\\loans.json",
        "credit_cards": r"C:\\Users\\Aditya Sharma\\Downloads\\credit_cards.json",
        "branches": r"C:\\Users\\Aditya Sharma\\Downloads\\branches.csv",
        "support_tickets": r"C:\\Users\\Aditya Sharma\\Downloads\\support_tickets.json",
    }

    selected_table = st.selectbox("Select Table to Filter", list(tables.keys()))
    file_path = tables[selected_table]

    # Load the file
    try:
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path)
        elif file_path.endswith(".json"):
            with open(file_path) as f:
                data = json.load(f)
            df = json_normalize(data)
    except Exception as e:
        st.error(f"❌ Error loading file: {e}")
        st.stop()

    st.subheader("Select columns and values to filter:")
    filters = {}

    for col in df.columns:
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
                vals = [df[col].dtype.type(v) for v in vals]  # FIX
            except:
                st.warning(f"Invalid numeric value for {col}, skipping filter.")
                continue

        filtered_df = filtered_df[filtered_df[col].isin(vals)]

    st.subheader("Filtered Results")
    st.dataframe(filtered_df, use_container_width=True)

# ===============================================================
#                     4️⃣ CRUD OPERATIONS
# ===============================================================
elif choice == "✏️ CRUD Operations":
    st.title("✏️ CRUD Operations")

    # File paths


    selected_table = st.selectbox("Select Table", list(tables.keys()))
    file_path = tables[selected_table]

    # Load file
    try:
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path)
        elif file_path.endswith(".json"):
            with open(file_path) as f:
                data = json.load(f)
            df = json_normalize(data)
    except Exception as e:
        st.error(f"❌ Error loading file: {e}")
        st.stop()

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
            new_row[col] = st.text_input(f"Enter {col}")

        if st.button("➕ Insert Record"):
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)


            # Save back
            if file_path.endswith(".csv"):
                df.to_csv(file_path, index=False)
            else:
                df.to_json(file_path, orient="records", indent=4)

            st.success("✅ Record inserted successfully!")

    # ------------------------------
    # 3️⃣ UPDATE
    # ------------------------------
    elif action == "Update":
        st.subheader("✏️ Update Record")

        if df.empty:
            st.warning("No records to update.")
            st.stop()

        row_index = st.number_input("Enter row index to update:", min_value=0, max_value=len(df)-1, step=1)

        updated_row = {}
        for col in df.columns:
            updated_row[col] = st.text_input(f"Update {col}", value=str(df.at[row_index, col]))

        if st.button("✔ Save Changes"):
            for col in df.columns:
                df.at[row_index, col] = updated_row[col]

            # Save
            if file_path.endswith(".csv"):
                df.to_csv(file_path, index=False)
            else:
                df.to_json(file_path, orient="records", indent=4)

            st.success("✅ Record updated successfully!")

    # ------------------------------
    # 4️⃣ DELETE
    # ------------------------------
    elif action == "Delete":
        st.subheader("🗑 Delete Record")

        if df.empty:
            st.warning("No records to delete.")
            st.stop()

        delete_index = st.number_input("Enter row index to delete:", min_value=0, max_value=len(df)-1, step=1)

        if st.button("🗑 Delete"):
            df = df.drop(delete_index).reset_index(drop=True)

            # Save
            if file_path.endswith(".csv"):
                df.to_csv(file_path, index=False)
            else:
                df.to_json(file_path, orient="records", indent=4)

            st.success("✅ Record deleted successfully!")

# ===============================================================
#                     5️⃣ CREDIT / DEBIT SIMULATION
# ===============================================================
elif choice == "🪙 Credit / Debit Simulation":
    st.title("🪙 Credit / Debit Simulation")

    accounts_file = r"C:\\Users\\Aditya Sharma\\Downloads\\accounts.csv"

    # Load accounts table
    try:
        accounts_df = pd.read_csv(accounts_file)
    except Exception as e:
        st.error(f"❌ Unable to load accounts file: {e}")
        st.stop()

    st.subheader("Enter Account Details")

    # Input fields
    acc_id = st.text_input("Enter customer_id:")
    amount = st.number_input("Enter Amount (₹):", min_value=0.0, step=100.0)

    action = st.radio("Select Action", ["Check Balance", "Deposit", "Withdraw"])

    if st.button("Submit"):
        if acc_id.strip() == "":
            st.error("❌ Please enter a valid Account ID.")
            st.stop()

        # Check if account exists
        if acc_id not in accounts_df["customer_id"].astype(str).values:
            st.error("❌ Customer ID not found!")
            st.stop()

        # Get current balance
        row_index = accounts_df[accounts_df["customer_id"] == acc_id].index[0]
        current_balance = float(accounts_df.at[row_index, "account_balance"])

        # Perform actions
        if action == "Check Balance":
            st.success(f"💰 Current Balance for {acc_id}: ₹{current_balance:,.2f}")

        elif action == "Deposit":
            new_balance = current_balance + amount
            accounts_df.at[row_index, "account_balance"] = new_balance
            accounts_df.to_csv(accounts_file, index=False)

            st.success(f"✅ Deposited ₹{amount:,.2f}. New Balance: ₹{new_balance:,.2f}")

        elif action == "Withdraw":
            if amount > current_balance:
                st.error("❌ Insufficient balance!")
            else:
                new_balance = current_balance - amount
                accounts_df.at[row_index, "account_balance"] = new_balance
                accounts_df.to_csv(accounts_file, index=False)

                st.success(f"✅ Withdrawn ₹{amount:,.2f}. New Balance: ₹{new_balance:,.2f}")


# ===============================================================
#                     6️⃣ ANALYTICAL INSIGHTS
# ===============================================================
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


# ===============================================================
#                     7️⃣ ABOUT CREATOR
# ===============================================================
elif choice == "👨🏻‍💻 About Creator":
    st.title("👨‍💻 About the Creator")
    st.markdown("""
            **Name:** <b>ADITYA SHARMA</b><br>
            Student: Data Science<br>
            Batch code: DS-C-WD-E-B92<br>
            E-mail: adityashrma1821@gmail.com<br>

    """,True)

# Close DB
conn.close()

