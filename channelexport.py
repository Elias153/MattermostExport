import ast
import json
import os
import re
from datetime import datetime

import filetype
import pandas as pd
import requests
import streamlit as st
from database import query_db_postgres
from filefunctions import string_to_filename, read_database_config, determine_file_extension, \
    export_to_csv_clean, export_to_json_clean


def export_channel_members(chan_id):
    query = """SELECT Users.username,Users.id FROM ChannelMembers INNER JOIN ChannelMemberHistory ON ChannelMembers.channelid = ChannelMemberHistory.channelid
    AND ChannelMemberHistory.userid = ChannelMembers.userid INNER JOIN Users ON ChannelMemberHistory.userid = Users.id AND 
    ChannelMembers.userid = Users.id WHERE ChannelMembers.channelid = %s AND ChannelMemberHistory.leavetime IS NULL"""

    users = []

    headers = ["Username", "User ID"]
    users.append(headers)

    for row in query_db_postgres(query,chan_id,True):
        users.append(row)

    query="""SELECT publicchannels.displayname FROM publicchannels WHERE publicchannels.id = %s"""
    isconstrained = True
    for row in query_db_postgres(query,chan_id,True):
        isconstrained = False

    members_data = export_to_csv_clean(users)

    return members_data, isconstrained

def export_metadata_json(chan_id):
    query = """SELECT Users.username,Users.id,ChannelMembers.schemeadmin FROM ChannelMembers INNER JOIN ChannelMemberHistory ON ChannelMembers.channelid = ChannelMemberHistory.channelid
    AND ChannelMemberHistory.userid = ChannelMembers.userid INNER JOIN Users ON ChannelMemberHistory.userid = Users.id AND 
    ChannelMembers.userid = Users.id WHERE ChannelMembers.channelid = %s AND ChannelMemberHistory.leavetime IS NULL"""

    usernames = []
    userids = []
    schemeadmins = []

    for row in query_db_postgres(query,chan_id,True):
        usernames.append(row[0])
        userids.append(row[1])
        schemeadmins.append(row[2])

    query="""SELECT publicchannels.displayname FROM publicchannels WHERE publicchannels.id = %s"""
    isconstrained = True
    for row in query_db_postgres(query,chan_id,True):
        isconstrained = False

    # Create the structured dictionary
    metadata_dict = {
        "members": {
            "usernames": usernames,
            "userids": userids,
            "schemeadmins": schemeadmins,
        },
        "is_private": isconstrained

    }

    metadata = export_to_json_clean(metadata_dict)

    return metadata

def export_data_postgres(chan_id, chan_name, earliest_date, latest_date, teams_name = None):
    # please note that to_timestamp in the select criteria can be omitted, as it only serves the purpose
    # on making the export more readable to a human.

    # comparisons between dates using sql assume, that if there's not a specific time specified,
    # the time is 00:00:00 ('2025-03-05 00:00:00'), so the comparison (see last line) has to be adjusted a bit, to not
    # accidentally exclude the last day when something was posted in the channel.
    query = """SELECT Posts.CreateAt/1000, UserName, Message, fileids, Posts.type FROM Posts INNER JOIN Users
            ON Posts.UserId = Users.Id WHERE Posts.editat = 0 AND ChannelId = %s AND to_timestamp(Posts.CreateAt/1000) >= %s 
            AND editat = 0 AND to_timestamp(Posts.CreateAt/1000) < %s + interval '1 day' ORDER BY Posts.CreateAt"""

    fileidlist = []
    # Fetch rows into lists
    posts = []

    headers = ["Date", "User", "Message", "Attachments", "Type"]
    posts.append(headers)

    for row in query_db_postgres(query,(chan_id,earliest_date,latest_date),True):
        posts.append(row)
        fileidlist.append(row[3])

    # Create a download button for the CSV file
    current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    if teams_name is None:
        file_export_data = export_to_csv_clean(posts)
        with open("channel_export/"+current_datetime + "_" + string_to_filename(chan_name) + ".csv", 'wb') as file:
            file.write(file_export_data)

        #metadata,isconstrained = export_channel_members(chan_id)
        metadata = export_metadata_json(chan_id)

        # change accordingly if csv export needed
        member_file_name = f'channel_export/{current_datetime}_{string_to_filename(chan_name)}_metadata.json'
        #if isconstrained:
        #    member_file_name = f'channel_export/{current_datetime}_{string_to_filename(chan_name)}_members_private.csv'

        with open(member_file_name, 'wb') as file:
            file.write(metadata)

        st.success(
            "Download Complete with " + current_datetime + "_" + string_to_filename(chan_name) + ".csv"
        )
        # Convert the list to a DataFrame
        df = pd.DataFrame(posts)

        # function to color the text in the dataframe
        def color_text(val):
            return 'color: white'

        # Apply the styling to the DataFrame using Style.map
        styled_df = df.style.map(color_text)

        # Display results
        st.table(styled_df)

        export_attachments(fileidlist,False)
    else:
        download_data = export_to_csv_clean(posts)

        # note that downloadstring is now a tuple !
        downloadstring = (string_to_filename(chan_name) + ".csv", download_data)

        # fileid-list also exported instead of directly calling "export_attachments" as we need
        # to store the attachments in the correct location of the zip export
        return downloadstring, fileidlist

def export_attachments(file_ids, teams_export):
    # setup api-connection
    config = read_database_config('connection.yaml')
    connection = config['connection']
    url = connection['url']  # hostname
    auth_token = ""
    login_url = url + "/api/v4/users/login"

    payload = {
        "login_id": connection['login_id'],
        "password": connection['password']
    }

    headers = {"content-type": "application/json"}
    s = requests.Session()
    r = s.post(login_url, data=json.dumps(payload), headers=headers)
    auth_token = r.headers.get("Token")
    hed = {'Authorization': 'Bearer ' + auth_token}

    output = []
    # retrieve and export files via mattermost api
    for ids in file_ids:
        if ids == "[]":
            # if there is no id for a given message, nothing needs to be done
            pass
        else:
            # Safely evaluate the string to extract the file ID
            # The IDs are stored in following format: ["myid"], we only need the literal myid
            try:
                formatted_id = ast.literal_eval(ids)[0]
            except ValueError:
                # Fallback: extract the content between square brackets (e.g. from [myid])
                match = re.search(r'\[(.*?)\]', ids)
                if match:
                    formatted_id = match.group(1).strip().strip('"').strip("'")
                else:
                    # Handle the error or skip this entry
                    continue

            file_url = url + "/api/v4/files/" + formatted_id

            # retrieve the file via api
            response = requests.get(file_url, headers=hed)
            file_data = response.content
            # Determine the extension from the file content
            kind = filetype.guess(file_data)
            if kind:
                # the extension could be guessed using the filetype lib, which is more precise
                final_filename = f"{formatted_id}.{kind.extension}"
            else:
                # if the extension could not be detected, we use the mime-type library
                final_filename = f"{formatted_id}{determine_file_extension(file_data)}"

            if not teams_export:
                open(final_filename, 'wb').write(file_data)
                print("Download Complete with " + final_filename)
            else:
                output.append((final_filename,file_data))

    if teams_export:
        return output

    # signal that there are no attachments found through this return value
    return None