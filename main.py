import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import OperationalError
import plotly.express as px
from langchain_ollama.chat_models import ChatOllama
import json
import sqlglot
import time
import re


def get_data(query: str) -> pd.DataFrame:
    """Connects to the database using SQLAlchemy, runs a query, and returns a DataFrame."""
    db_url = "postgresql://user:password@postgres:5432/mydatabase"
    engine = create_engine(db_url)
    for i in range(5):
        try:
            df = pd.read_sql_query(query, engine)
            return df
        except OperationalError:
            st.warning(f"Database not ready, retrying in 5 seconds... (Attempt {i+1}/5)")
            time.sleep(5)
        except Exception as e:
            st.error(f"Error connecting to database: {e}")
            return pd.DataFrame()
    st.error("Could not connect to the database after several retries.")
    return pd.DataFrame()


@st.cache_data
def get_db_schema():
    """Connects to the database and inspects its schema, with retries."""
    db_url = "postgresql://user:password@postgres:5432/mydatabase"
    engine = create_engine(db_url)
    for i in range(5):
        try:
            inspector = inspect(engine)
            schema_info = {}
            schemas = inspector.get_schema_names()
            for schema in schemas:
                if schema not in ('pg_catalog', 'information_schema', 'pg_toast'):
                    for table_name in inspector.get_table_names(schema=schema):
                        if schema not in schema_info:
                            schema_info[schema] = {}
                        columns = []
                        for column in inspector.get_columns(table_name, schema=schema):
                            columns.append(column['name'])
                        schema_info[schema][table_name] = columns
            return schema_info
        except OperationalError:
            st.warning(f"Database not ready, retrying in 5 seconds... (Attempt {i+1}/5)")
            time.sleep(5)
        except Exception as e:
            st.error(f"Error inspecting database schema: {e}")
            return None
    st.error("Could not connect to the database after several retries.")
    return None


def validate_query(query, schema):
    try:
        st.info(f"Debug - Validating query: {query}")
        
        # Simple regex approach to extract table aliases
        alias_to_table = {}
        
        # Pattern: FROM table_name [AS] alias_name
        # This handles both "FROM users u" and "FROM users AS u"
        from_pattern = r'FROM\s+(\w+)(?:\s+AS)?\s+(\w+)(?:\s|$|,|JOIN|WHERE|GROUP|ORDER|LIMIT)'
        from_matches = re.findall(from_pattern, query, re.IGNORECASE)
        for table_name, alias_name in from_matches:
            # Skip if alias_name is a SQL keyword
            if alias_name.upper() not in ['WHERE', 'GROUP', 'ORDER', 'LIMIT', 'HAVING', 'JOIN', 'ON']:
                alias_to_table[alias_name] = table_name
                st.info(f"Debug - FROM: {alias_name} -> {table_name}")
        
        # Pattern: JOIN table_name [AS] alias_name  
        # This handles both "JOIN users u" and "JOIN users AS u"
        join_pattern = r'JOIN\s+(\w+)(?:\s+AS)?\s+(\w+)(?:\s|$|,|ON|WHERE|GROUP|ORDER|LIMIT)'
        join_matches = re.findall(join_pattern, query, re.IGNORECASE)
        for table_name, alias_name in join_matches:
            # Skip if alias_name is a SQL keyword
            if alias_name.upper() not in ['ON', 'WHERE', 'GROUP', 'ORDER', 'LIMIT', 'HAVING']:
                alias_to_table[alias_name] = table_name
                st.info(f"Debug - JOIN: {alias_name} -> {table_name}")
        
        st.info(f"Debug - Alias mapping: {alias_to_table}")
        
        # Now use SQLGlot to validate the structure
        parsed = sqlglot.parse_one(query, read="postgres")
        
        # Get all actual table names from the query
        actual_tables = set()
        for table in parsed.find_all(sqlglot.exp.Table):
            actual_tables.add(table.name)
        
        # Check for required join between sales and products
        if 'sales' in actual_tables and 'products' in actual_tables:
            join_conditions = parsed.find_all(sqlglot.exp.Join)
            join_on_product_id = False
            for join in join_conditions:
                join_str = str(join.on)
                if ('product_id' in join_str and 'id' in join_str):
                    join_on_product_id = True
                    break
            if not join_on_product_id:
                return False, ("Query involves 'sales' and 'products' tables "
                               "but does not join on proper keys.")

        # Validate columns
        for column in parsed.find_all(sqlglot.exp.Column):
            column_name = column.name
            table_ref = column.table
            
            # Resolve alias to actual table name
            if table_ref and table_ref in alias_to_table:
                table_ref = alias_to_table[table_ref]
                st.info(f"Debug - Resolved {column.table}.{column_name} -> {table_ref}.{column_name}")
            
            if not table_ref:
                # Try to infer table name for columns without explicit table prefix
                for table in actual_tables:
                    if column_name in schema.get('public', {}).get(table, []):
                        table_ref = table
                        break

            if not table_ref:
                # If table is still unknown, skip validation for this column
                st.warning(f"Debug - Could not resolve table for column: {column_name}")
                continue

            # Check if table exists in schema
            if table_ref not in schema.get('public', {}):
                return False, f"Table '{table_ref}' not found in the database schema."

            # Check if column exists in table
            if column_name not in schema.get('public', {}).get(table_ref, []):
                return False, f"Column '{column_name}' not found in table '{table_ref}'."

        return True, ""
    except Exception as e:
        return False, f"Error parsing SQL query: {e}"


llm = ChatOllama(
    base_url="http://host.docker.internal:11434",
    model="llama3.2:latest",
    temperature=0,
    format="json",
)

st.title("Beh App:SQL To Visualization")

prompt = st.text_input("Enter your data question:", "Show me the number of users per email domain")

if st.button("Generate Visualization"):
    with st.spinner("Fetching database schema..."):
        schema = get_db_schema()
        if not schema:
            st.error("Could not retrieve database schema. Cannot continue.")
            st.stop()
        st.info("Database schema loaded successfully.")
        with st.expander("View Database Schema"):
            st.json(schema)
        
        # Debug: Show schema structure
        if schema:
            st.info(f"Schema keys: {list(schema.keys())}")
            if 'public' in schema:
                st.info(f"Public schema tables: {list(schema['public'].keys())}")
                for table_name, columns in schema['public'].items():
                    st.info(f"Table '{table_name}' columns: {columns}")
        else:
            st.error("Schema is None!")

    with st.spinner("Generating and validating SQL query..."):
        st.info("User prompt received: " + prompt)

        system_prompt = f'''You are an expert SQL data analyst. A user will ask a question in natural language. You must generate a JSON object with two keys: 'sql_query' and 'chart_info'.

        **IMPORTANT**: The SQL query MUST be for PostgreSQL. Use ONLY these PostgreSQL functions:
        - For string splitting: split_part(string, delimiter, field_number)
        - For email domains: split_part(email, '@', 2)
        - For dates: EXTRACT(YEAR FROM date_column), DATE_TRUNC('month', date_column)
        - For counting: COUNT(*), COUNT(DISTINCT column)
        - For aggregation: SUM, AVG, MIN, MAX
        - DO NOT use: INSTR, SUBSTRING_INDEX, DOMAIN, or any MySQL-specific functions

        Use the following database schema to construct the query:
        {json.dumps(schema, indent=2)}

        When a query requires information from both the `sales` and `products` tables, you MUST join them using `sales.product_id = products.id`.

        1.  `sql_query`: A valid PostgreSQL query that answers the user's question based on the provided schema.
        2.  `chart_info`: A JSON object with three keys:
            *   `type`: The best chart type (bar, line, scatter, pie).
            *   `x_axis`: The column name for the X-axis.
            *   `y_axis`: The column name for the Y-axis.

        Example for email domain extraction:

        User prompt: "Show me the number of users per email domain"

        {{
          "sql_query": "SELECT split_part(email, '@', 2) AS email_domain, COUNT(*) AS user_count FROM users GROUP BY split_part(email, '@', 2);",
          "chart_info": {{
            "type": "bar",
            "x_axis": "email_domain",
            "y_axis": "user_count"
          }}
        }}
        '''

        try:
            # Try using proper message format for ChatOllama
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
            response = llm.invoke(messages)
            response_data = json.loads(response.content)

            original_query = response_data["sql_query"]
            chart_info = response_data["chart_info"]

            st.info("Original Generated SQL Query: " + original_query)
        except Exception as e:
            st.error(f"Error calling LLM or parsing response: {e}")
            if 'response' in locals():
                st.error(f"LLM Response: {response.content}")
            st.stop()

        # Translate the query to PostgreSQL dialect and fix common issues
        try:
            # First, fix common PostgreSQL syntax issues
            query_fixed = original_query
            
            # Fix EXTRACT(DOMAIN FROM email) -> split_part(email, '@', 2)
            domain_pattern = r'EXTRACT\s*\(\s*DOMAIN\s+FROM\s+(\w+)\s*\)'
            query_fixed = re.sub(domain_pattern, r"split_part(\1, '@', 2)", query_fixed, flags=re.IGNORECASE)
            
            # Fix SUBSTRING_INDEX -> split_part
            substring_pattern = r'SUBSTRING_INDEX\s*\(\s*(\w+)\s*,\s*([\'"])([^\'"]+)\2\s*,\s*(\d+)\s*\)'
            query_fixed = re.sub(substring_pattern, r'split_part(\1, \2\3\2, \4)', query_fixed, flags=re.IGNORECASE)
            
            if query_fixed != original_query:
                st.info(f"Fixed PostgreSQL syntax: {query_fixed}")
            
            # Then transpile to ensure proper PostgreSQL dialect
            translated_query = sqlglot.transpile(query_fixed, write="postgres", read="mysql")[0]
            st.info("Translated PostgreSQL Query: " + translated_query)
            query = translated_query
        except Exception as e:
            st.error(f"Error translating SQL query to PostgreSQL dialect: {e}")
            # Fall back to the fixed query if transpilation fails
            query = query_fixed if 'query_fixed' in locals() else original_query
            st.info(f"Using fallback query: {query}")

        st.info("Validating query against schema...")
        is_valid, error_message = validate_query(query, schema)
        if not is_valid:
            st.error(f"Generated query is invalid: {error_message}")
            st.stop()

        st.success("Query validated successfully.")

    with st.spinner("Executing query and generating visualization..."):
        data = get_data(query)

        if not data.empty:
            st.info("Query executed successfully. Generating chart...")
            st.write("### Query Results")
            st.write(data)

            if len(data.columns) > 1:
                st.write("### Visualization")
                chart_type = chart_info["type"]
                x_axis = chart_info["x_axis"]
                y_axis = chart_info["y_axis"]

                # Self-correction for y-axis column name
                if y_axis not in data.columns:
                    st.warning(f"Y-axis '{y_axis}' not found in query results. Attempting to self-correct.")
                    potential_y_axes = [col for col in data.columns if col != x_axis]
                    if len(potential_y_axes) == 1:
                        y_axis = potential_y_axes[0]
                        st.info(f"Self-corrected Y-axis to '{y_axis}'.")
                    else:
                        st.error("Could not determine the correct Y-axis column.")
                        st.stop()

                if chart_type == "bar":
                    fig = px.bar(data, x=x_axis, y=y_axis)
                elif chart_type == "line":
                    fig = px.line(data, x=x_axis, y=y_axis)
                elif chart_type == "scatter":
                    fig = px.scatter(data, x=x_axis, y=y_axis)
                elif chart_type == "pie":
                    fig = px.pie(data, names=x_axis, values=y_axis)
                else:
                    st.warning(f"Unsupported chart type: {chart_type}. Defaulting to scatter plot.")
                    fig = px.scatter(data, x=x_axis, y=y_axis)

                st.plotly_chart(fig)
                st.info("Visualization complete.")
            else:
                st.warning("Query result must have at least two columns to create a graph.")
        else:
            st.error("No data returned from the query.")
