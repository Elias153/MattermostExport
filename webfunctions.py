import streamlit as st
from database import query_db_postgres
from datetime import datetime
from filefunctions import export_to_csv
from filefunctions import string_to_filename
import base64
import pandas as pd

def get_base64(bin_file):
    # Decode binary files like images
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def show_background():
    # decode the binary
    bin_str = get_base64("img/background.jpg")
    # set the style element
    page_bg_img = '''
    <style>
    .stApp {
    background-image: url("data:image/png;base64,%s");
    background-size: cover;
    }
    </style>
    ''' % bin_str
    # render the background
    st.markdown(page_bg_img, unsafe_allow_html=True)

def export_data_postgres(chan_id, chan_name, earliest_date, latest_date):
    # please note that to_timestamp is not needed for the actual exporting, it only serves testing
    # purposes.

    # comparisons between dates using sql assume, that if there's not a specific time specified,
    # the time is 00:00:00 ('2025-03-05 00:00:00'), so the comparison has to be adjusted a bit, to not
    # accidentally exclude the last day when something was posted in the channel.
    query = """SELECT to_timestamp((Posts.CreateAt/1000)), UserName, Message FROM Posts INNER JOIN Users
            ON Posts.UserId = Users.Id WHERE ChannelId = %s AND to_timestamp(Posts.CreateAt/1000) >= %s 
            AND to_timestamp(Posts.CreateAt/1000) < %s + interval '1 day' ORDER BY Posts.CreateAt"""

    # Fetch rows into lists
    posts = []
    for row in query_db_postgres(query,(chan_id,earliest_date,latest_date),True):
        posts.append(row)

    # Create a download button for the CSV file
    current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    export_to_csv(posts, current_datetime + "_" + string_to_filename(chan_name) + ".csv")

    # Convert the list to a DataFrame
    df = pd.DataFrame(posts)

    # function to color the text in the dataframe
    def color_text(val):
        return 'color: white'

    # Apply the styling to the DataFrame using Style.map
    styled_df = df.style.map(color_text)

    # Display results
    st.table(styled_df)

def channel_name_dropdown_postgres():

    # Fetch rows into lists
    channel_names_from_database = []
    channel_ids_from_database = []

    query = "select Id, DisplayName from Channels"

    for row in query_db_postgres(query,[],False):
        channel_id, channel_name = row  # row returned is tuple ("id", "name"), we split it here
        if channel_name != "":
            channel_ids_from_database.append(channel_id)  # list with indexes matching those of the names
            channel_names_from_database.append(channel_name)  # list with indexes matching those of the id's

    # Create a dropdown selection box
    selected_option = st.selectbox(
        ':violet[Select a channel to export:]',
        channel_names_from_database
    )

    # return the channel_id directly instead of the channel_name
    index = channel_names_from_database.index(
        selected_option)  # check the index in the list for the chosen channel name

    # timestamps
    earliestdate, latestdate = timestamps_input(channel_ids_from_database[index])
    # return the channel ID and name (and then the timeframe, from which the posts are to be exported)
    return channel_ids_from_database[index], \
        channel_names_from_database[index], \
        earliestdate, latestdate

def timestamps_input(chan_id):

    query = """SELECT 
    to_char(to_timestamp(MAX(Posts.CreateAt) / 1000), 'YYYY-MM-DD') AS latest_date,
    to_char(to_timestamp(MIN(Posts.CreateAt) / 1000), 'YYYY-MM-DD') AS earliest_date
    FROM Posts INNER JOIN Users ON Posts.UserId = Users.Id WHERE ChannelId = %s;"""

    for row in query_db_postgres(query,chan_id,True):
        latestDate, earliestDate = row  # row returned is tuple ("latest_date", "earliest_date"), we split it here

    # needed to convert the previous output to datetime objects for further processing
    dt_latest = datetime.strptime(latestDate, "%Y-%m-%d")
    dt_earliest = datetime.strptime(earliestDate, "%Y-%m-%d")

    # Create two columns
    col1, col2 = st.columns(2)

    with col1:
        earliestdate = st.date_input(":violet[Start Date]", dt_earliest)

    with col2:
        latestdate = st.date_input(":violet[End Date]", dt_latest)

    return earliestdate, latestdate