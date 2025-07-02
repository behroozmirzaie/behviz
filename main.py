import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import OperationalError
import plotly.express as px
from langchain_ollama.chat_models import ChatOllama
import json
import sqlglot
import time


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
        parsed = sqlglot.parse_one(query, read="postgres")

        # Collect all table names used in the query
        tables_in_query = {table.name for table in parsed.find_all(sqlglot.exp.Table)}

        # Check for required join between sales and products
        if 'sales' in tables_in_query and 'products' in tables_in_query:
            join_conditions = parsed.find_all(sqlglot.exp.Join)
            join_on_product_id = False
            for join in join_conditions:
                if 'sales.product_id' in str(join.on) and 'products.id' in str(join.on):
                    join_on_product_id = True
                    break
            if not join_on_product_id:
                return False, "Query involves 'sales' and 'products' tables but does not join on 'sales.product_id = products.id'."

        for column in parsed.find_all(sqlglot.exp.Column):
            column_name = column.name
            table_name = column.table
            if not table_name:
                # Try to infer table name for columns without explicit table prefix
                for table in tables_in_query:
                    if column_name in schema['public'].get(table, []):
                        table_name = table
                        break

            if not table_name:
                # If table is still unknown, it might be a derived column, which is harder to validate statically.
                # For simplicity, we'll assume it's okay if we can't resolve the table.
                continue

            if table_name not in schema['public']:
                return False, f"Table '{table_name}' not found in the database schema."

            if column_name not in schema['public'][table_name]:
                return False, f"Column '{column_name}' not found in table '{table_name}'."

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

    with st.spinner("Generating and validating SQL query..."):
        st.info("User prompt received: " + prompt)

        system_prompt = f'''You are an expert SQL data analyst. A user will ask a question in natural language. You must generate a JSON object with two keys: 'sql_query' and 'chart_info'.

        **IMPORTANT**: The SQL query MUST be for PostgreSQL. Do NOT use functions like `INSTR` which are not available in PostgreSQL. For string splitting, use `split_part`.

        Use the following database schema to construct the query:
        {json.dumps(schema, indent=2)}

        When a query requires information from both the `sales` and `products` tables, you MUST join them using `sales.product_id = products.id`.

        1.  `sql_query`: A valid PostgreSQL query that answers the user's question based on the provided schema.
        2.  `chart_info`: A JSON object with three keys:
            *   `type`: The best chart type (bar, line, scatter, pie).
            *   `x_axis`: The column name for the X-axis.
            *   `y_axis`: The column name for the Y-axis.

        Example:

        User prompt: "What is the distribution of users by country?"

        {{
          "sql_query": "SELECT country, COUNT(*) AS user_count FROM users GROUP BY country;",
          "chart_info": {{
            "type": "bar",
            "x_axis": "country",
            "y_axis": "user_count"
          }}
        }}
        '''

        response = llm.invoke(system_prompt + "\n\nUser prompt: " + prompt)
        response_data = json.loads(response.content)

        original_query = response_data["sql_query"]
        chart_info = response_data["chart_info"]

        st.info("Original Generated SQL Query: " + original_query)

        # Translate the query to PostgreSQL dialect to fix dialect-specific function errors
        try:
            # Assuming the LLM might default to a more generic or MySQL-like dialect
            translated_query = sqlglot.transpile(original_query, write="postgres", read="mysql")[0]
            st.info("Translated PostgreSQL Query: " + translated_query)
            query = translated_query
        except Exception as e:
            st.error(f"Error translating SQL query to PostgreSQL dialect: {e}")
            st.stop()

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
                    # Find a likely candidate for the y-axis (the other column)
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
