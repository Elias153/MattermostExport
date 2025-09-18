import streamlit as st

from channelexport import export_data_postgres
from database import query_db_postgres
from datetime import datetime
import base64

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

def teams_name_dropdown_postgres():
    # fetch rows into lists
    teams_names_from_database = []
    teams_ids_from_database = []

    query = "select Id, DisplayName from Teams"

    for row in query_db_postgres(query,[],False):
        teams_id, teams_name = row
        if teams_name != "":
            teams_ids_from_database.append(teams_id)
            teams_names_from_database.append(teams_name)

    # create a dropdown selection box
    selected_option = st.selectbox(
        ':violet[Select a team to export:]',
        teams_names_from_database
    )

    # return the channel_id directly instead of the channel_name
    index = teams_names_from_database.index(
        selected_option)  # check the index in the list for the chosen channel name

    return teams_ids_from_database[index], teams_names_from_database[index]

def channel_name_dropdown_postgres():

    # Fetch rows into lists
    channel_names_from_database = []
    channel_ids_from_database = []

    query = "select Id, DisplayName, name from Channels"

    counter = 0
    for row in query_db_postgres(query,[],False):
        channel_id, channel_name, dm_name = row  # row returned is tuple ("id", "name"), we split it here
        if channel_name != "":
            channel_ids_from_database.append(channel_id)  # list with indexes matching those of the names
            channel_names_from_database.append(channel_name)  # list with indexes matching those of the id's
        else:
            # limit as you want
            if counter < 30 or dm_name=='j19nxo1zf7rr5gxgcopceof3ha__oahadhstffrwjpgbwf1w4ks1oc':
                # we have a dm - since they DO NOT have displaynames.
                channel_ids_from_database.append(channel_id)

                new_dm_name = ""
                first_user = True
                # since the name of the channel is the MATTERMOST IDs of the persons in the dm, query to get real names (they are unique anyways)
                query = "select username from users inner join channelmembers on users.id = channelmembers.userid inner join channels on channelmembers.channelid = channels.id where channelmembers.channelid = %s and channels.type = 'D'"
                rows = query_db_postgres(query,channel_id, True)
                for dm_row in rows:
                    new_dm_name += dm_row[0]
                    if first_user and not len(rows) == 1:
                        new_dm_name += ", "
                        first_user = False
                channel_names_from_database.append(new_dm_name)

                counter += 1

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

def select_default_timestamps(chan_id):
    query = """SELECT 
        to_char(to_timestamp(MAX(Posts.CreateAt) / 1000), 'YYYY-MM-DD') AS latest_date,
        to_char(to_timestamp(MIN(Posts.CreateAt) / 1000), 'YYYY-MM-DD') AS earliest_date
        FROM Posts INNER JOIN Users ON Posts.UserId = Users.Id WHERE ChannelId = %s;"""

    for row in query_db_postgres(query, chan_id, True):
        latestDate, earliestDate = row  # row returned is tuple ("latest_date", "earliest_date"), we split it here

    if latestDate is None:
        latestDate = datetime.now().strftime("%Y-%m-%d")

    if earliestDate is None:
        earliestDate = "1970-01-01"
    # needed to convert the previous output to datetime objects for further processing
    dt_latest = datetime.strptime(latestDate, "%Y-%m-%d")
    dt_earliest = datetime.strptime(earliestDate, "%Y-%m-%d")
    return dt_latest, dt_earliest

def timestamps_input(chan_id):

    dt_latest, dt_earliest = select_default_timestamps(chan_id)
    # Create two columns
    col1, col2 = st.columns(2)

    with col1:
        earliestdate = st.date_input(":violet[Start Date]", dt_earliest)

    with col2:
        latestdate = st.date_input(":violet[End Date]", dt_latest)

    return earliestdate, latestdate
