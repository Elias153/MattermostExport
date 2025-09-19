from filefunctions import read_database_config
import streamlit as st
import psycopg2
from psycopg2 import Error

# pass parameters the query should be executed with (as tuple), as well as a boolean if there are any parameters
# expected at all. You can also pass a single parameter not formatted as a tuple, the function handles that.
def query_db_postgres(query, params, expectedparams):
    # Establish a connection to the database

    try:
        # Accessing database information
        config = read_database_config('database.yaml')

        connection = psycopg2.connect(**config['database'], keepalives=1, keepalives_idle=30,
                            keepalives_interval=10, keepalives_count=3)

        # Create a cursor object to execute SQL queries
        cursor = connection.cursor()
        if connection.closed == 0 and query != "":
            # Execute the query with passed parameters if there are any
            if expectedparams :
                # if tuple, we can assume the arguments are already passed with correct syntax
                if isinstance(params, tuple):
                    cursor.execute(query, params)
                else:
                    # manually build 1-tuple before passing parameter
                    cursor.execute(query, (params,))

            else :
                # Execute the query with no parameters
                cursor.execute(query)

            # Fetch all rows
            rows = cursor.fetchall()

            # Close the connection
            if connection is not None and connection.closed == 0:
                cursor.close()
                connection.close()

            return rows

    except Error as e:
        st.write("Error connecting to the database:", e)
    finally:
        pass