import json

from channelexport import export_data_postgres, export_channel_members, export_metadata_json
from database import query_db_postgres
from filefunctions import create_zip_archive
from webfunctions import select_default_timestamps
import streamlit as st

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
    for i in range(len(channel_ids)):
        chan_id = channel_ids[i]
        chan_name = channel_names[i]
        latest_date, earliest_date = select_default_timestamps(chan_id)

        # determine the download link for the current channel
        # note that download_string is a tuple (filename,filedata)
        download_string, attachment_list = export_data_postgres(chan_id, chan_name, earliest_date, latest_date,team_name)

        #metadata_csv = export_channel_members(chan_id)
        metadata_json = export_metadata_json(chan_id)

        # a list of metadata (members,admins,private/public) of the respective channel

        #metadata_lists.append(metadata_csv)
        metadata_lists.append(metadata_json)

        # a list of the download strings for the respective export files
        download_links.append(download_string)

        # a list of lists of file_ids of the attachments
        attachment_id_lists.append(attachment_list)

        # Update progress every 10 channels or on the last iteration
        #if (i + 1) % 10 == 0 or (i + 1) == total_channels:
        #    progress = ((i + 1) / total_channels) * 100
        #    print(f"Progress: {progress:.1f}% completed")

    zip_bytes = create_zip_archive(download_links, attachment_id_lists, metadata_lists)
    st.download_button(
        label="Download Export of Team as zip",
        data=zip_bytes,
        file_name="exported_files.zip",
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

