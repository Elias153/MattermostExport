import mysql.connector
from filefunctions import read_database_config
import streamlit as st
import psycopg2
from psycopg2 import Error

def query_db(query):
    # Establish a connection to the database
    try:
        # Accessing database information
        config = read_database_config('database.yaml')
        ## postgres : connection = psycopg.connect(
        connection = mysql.connector.connect(
            host=config['database']['host'],
            user=config['database']['user'],
            password=config['database']['password'],
            database=config['database']['database']
        )

        print("Connected to the database")
        # Create a cursor object to execute SQL queries
        cursor = connection.cursor()

        if connection.is_connected() and query != "":

            # Execute the query
            cursor.execute(query)

            # Fetch all rows
            rows = cursor.fetchall()

            # Close the connection
            if connection is not None and connection.is_connected():
                cursor.close()
                connection.close()
                print("Connection closed")

            return rows

    except mysql.connector.Error as e:
        st.write("Error connecting to the database:", e)
    ## except Error as e:
    finally:
        print("Done")

# --------------------------------------------------------------------------------------
# Rewritten functions via postgres
# --------------------------------------------------------------------------------------

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