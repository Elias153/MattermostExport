from channelexport import export_data_postgres, export_metadata_json
from database import query_db_postgres
from filefunctions import create_zip_archive, export_to_json_clean
from webfunctions import select_default_timestamps
import streamlit as st
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set the logging level you desire (DEBUG, INFO, etc.)
    format='%(asctime)s - %(levelname)s - %(message)s',  # Include timestamp and level
    datefmt='%Y-%m-%d %H:%M:%S'  # Format for the timestamp
)

def export_data_postgres_team(team_id,team_name):
    download_links = []
    attachment_id_lists = []
    metadata_lists = []
    # retrieve the relevant channels from the selected team
    channel_ids, channel_names = get_channels_from_team(
        team_id
    )
    total_channels = len(channel_ids)
    # loop to export all channels of a team
    for i in range(total_channels):
        chan_id = channel_ids[i]
        chan_name = channel_names[i]
        latest_date, earliest_date = select_default_timestamps(chan_id)

        # determine the download link for the current channel
        # note that download_string is a tuple (filename,filedata)
        download_string, attachment_list = export_data_postgres(chan_id, chan_name, earliest_date, latest_date,True)

        metadata_json = export_metadata_json(chan_id)

        # a list of metadata (members,admins,private/public) of the respective channel

        metadata_lists.append(metadata_json)

        # a list of the download strings for the respective export files
        download_links.append(download_string)

        # a list of lists of file_ids of the attachments
        attachment_id_lists.append(attachment_list)

        logging.info(f"Prepared Export for Channel : {chan_name}")
        # Update progress every 10 channels or on the last iteration
        if (i + 1) % 10 == 0 or (i + 1) == total_channels:
            progress = ((i + 1) / total_channels) * 100
            print(f"Progress: {progress:.1f}% completed")

    team_metadata = retrieve_team_metadata(team_id)

    logging.info("Compiling zip-Archive")
    zip_bytes = create_zip_archive(download_links, attachment_id_lists, metadata_lists, team_metadata)
    st.download_button(
        label="Download Export of Team as zip",
        data=zip_bytes,
        file_name=f"{team_name}_export.zip",
        mime="application/zip"
    )

def get_channels_from_team(team_id):
    query="""select Id, DisplayName from Channels where TeamId = %s"""

    channel_names_from_database = []
    channel_ids_from_database = []
    for row in query_db_postgres(query,team_id,True):
        channel_id, channel_name = row
        if channel_name != "":
            channel_ids_from_database.append(channel_id)
            channel_names_from_database.append(channel_name)
    return channel_ids_from_database, channel_names_from_database

# this function extracts the members of the team, as well as the team description.
def retrieve_team_metadata(team_id):

    members_dict = {}

    query = """
    SELECT 
        users.username,
        users.id,
        teammembers.schemeadmin 
    FROM 
        teammembers 
        INNER JOIN users ON users.id = teammembers.userid 
    WHERE 
        teammembers.teamid = %s"""

    for row in query_db_postgres(query,team_id,True):
        username = row[0]
        user_id = row[1]
        scheme_admin = row[2]

        # Populate the members dictionary
        members_dict[username] = {
            "userid": user_id,
            "schemeadmin": scheme_admin
        }

    description = ""
    email = ""
    allow_open_invite = False

    query = """SELECT teams.description, teams.email, teams.allowopeninvite FROM teams WHERE teams.id = %s"""

    for row in query_db_postgres(query,team_id,True):
        description = row[0]
        email = row[1]
        allow_open_invite = row[2]

    metadata_dict = {
        "team_id": team_id,
        "team_description": description,
        "allow_open_invite": allow_open_invite,
        "email": email,
        "members": members_dict
    }

    metadata = export_to_json_clean(metadata_dict)

    return metadata
