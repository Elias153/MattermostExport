import mysql.connector
from filefunctions import read_database_config
import streamlit as st
import psycopg2
from psycopg2 import Error

def query_db_postgres(query, params, expectedparams):
    # Establish a connection to the database

    try:
        # Accessing database information
        config = read_database_config('database.yaml')

        connection = psycopg2.connect(**config['database'])

        print("Connected to the database")
        # Create a cursor object to execute SQL queries
        cursor = connection.cursor()

        if connection.closed == 0 and query != "":

            if expectedparams :
                # Execute the query with passed parameters

                # if tuple, we can assume the arguments are already passed with correct syntax
                if isinstance(params, tuple):
                    cursor.execute(query, params)
                else:
                    # if not t
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
                print("Connection closed")

            return rows

    except Error as e:
        st.write("Error connecting to the database:", e)
    finally:
        print("Done")