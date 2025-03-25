# ALL direct messages OR group channels are exported here, or rather : channels which are not assigned to a specific team
from channelexport import export_data_postgres, export_channel_members, export_metadata_json
from database import query_db_postgres
from filefunctions import create_zip_archive
from webfunctions import select_default_timestamps
import streamlit as st

def get_channels_from_dmgroup():
    channel_names_from_database = []
    channel_ids_from_database = []

    query = """SELECT Channels.id, Channels.DisplayName FROM Channels WHERE Channels.type = 'D' OR Channels.type = 'G'"""

    for row in query_db_postgres(query, [], False):
        ids, name = row
        if name == "":
            name = "Direct Message"
        channel_names_from_database.append(name)
        channel_ids_from_database.append(ids)

        #earliest_date, latest_date = select_default_timestamps(ids)
        #export_data_postgres(ids, name, earliest_date, latest_date, None)
    return channel_names_from_database, channel_ids_from_database

# export the data as a zip archive
def export_direct_messages(channel_names_from_database, channel_ids_from_database):
    download_links = []
    attachment_id_lists = []
    metadata_lists = []

    for i in range(len(channel_ids_from_database)):
        chan_id = channel_ids_from_database[i]
        chan_name = channel_names_from_database[i]

        latest_date, earliest_date = select_default_timestamps(chan_id)
        download_string, attachment_list = export_data_postgres(chan_id, chan_name, earliest_date, latest_date, True)
        #file_member_data = export_channel_members(chan_id)
        metadata_json = export_metadata_json(chan_id)

        # a list of usernames/userids of the members of the respective channel
        metadata_lists.append(metadata_json)

        # a list of the download strings for the respective export files
        download_links.append(download_string)

        # a list of lists of file_ids of the attachments
        attachment_id_lists.append(attachment_list)

    zip_bytes = create_zip_archive(download_links, attachment_id_lists, metadata_lists)

    print("Export Complete")
    st.download_button(
        label="Download Export of Direct Messages and Groups as zip",
        data=zip_bytes,
        file_name="dm_group.zip",
        mime="application/zip"
    )