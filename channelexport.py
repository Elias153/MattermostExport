import ast
import json
import re
import os
from datetime import datetime

import pandas as pd
import requests
import streamlit as st
from database import query_db_postgres
from filefunctions import string_to_filename, read_database_config, \
    export_to_csv_clean, export_to_json_clean

def export_metadata_json(chan_id):
    query = """
    SELECT 
        Users.username,
        Users.id,
        ChannelMembers.schemeadmin,
        channels.creatorid,
        channels.purpose 
    FROM 
        ChannelMembers 
        INNER JOIN ChannelMemberHistory ON ChannelMembers.channelid = ChannelMemberHistory.channelid AND ChannelMemberHistory.userid = ChannelMembers.userid 
        INNER JOIN Users ON ChannelMemberHistory.userid = Users.id AND ChannelMembers.userid = Users.id 
        INNER JOIN channels ON ChannelMembers.channelid = channels.id 
    WHERE 
        ChannelMembers.channelid = %s 
        AND ChannelMemberHistory.leavetime IS NULL"""

    members_dict = {}
    creator_id = ""
    description = ""
    for row in query_db_postgres(query,chan_id,True):
        username = row[0]
        user_id = row[1]
        scheme_admin = row[2]
        creator_id = row[3]
        description = row[4]

        # Populate the members dictionary
        members_dict[username] = {
            "userid": user_id,
            "schemeadmin": scheme_admin
        }

    channel_is_private = is_channel_private(chan_id)

    current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    # Create the structured dictionary
    metadata_dict = {
        "is_private": channel_is_private,
        "channel_id": chan_id,
        "creator_id": creator_id,
        "export_date": current_datetime,
        "description": description,
        "members": members_dict
    }

    metadata = export_to_json_clean(metadata_dict)

    return metadata

def is_channel_private(chan_id):
    query = """SELECT publicchannels.displayname FROM publicchannels WHERE publicchannels.id = %s"""
    channel_is_private = True
    for row in query_db_postgres(query,chan_id,True):
        channel_is_private = False

    return channel_is_private

def export_data_postgres(chan_id, chan_name, earliest_date, latest_date, teams_export = False):
    # use to_timestamp for the select criteria as a wrapper for the timestamp if needed for export.

    # comparisons between dates using sql assume, that if there's not a specific time specified,
    # the time is 00:00:00 ('2025-03-05 00:00:00'), so the comparison (see last line) has to be adjusted a bit, to not
    # accidentally exclude the last day when something was posted in the channel.
    query = """
    SELECT 
        Posts.CreateAt/1000,
        UserName, 
        Message, 
        Posts.type, 
        reactions.emojiname, 
        CASE
            WHEN length(Posts.fileids) <= 2 THEN NULL
        ELSE Posts.fileids
        END AS fileids, 
        fileinfo.name 
    FROM 
        Posts 
        INNER JOIN Users ON Posts.UserId = Users.Id 
        LEFT JOIN fileinfo ON Posts.id = fileinfo.postid 
        LEFT JOIN reactions ON Posts.ChannelId = reactions.ChannelId AND Posts.id = reactions.postid
    WHERE 
        Posts.editat = 0 
        AND Posts.ChannelId = %s 
        AND to_timestamp(Posts.CreateAt/1000) >= %s 
        AND editat = 0 AND to_timestamp(Posts.CreateAt/1000) < %s + interval '1 day' 
    ORDER BY Posts.CreateAt"""

    fileidlist = []
    # Fetch rows into lists
    posts = []

    headers = ["Date", "User", "Message", "Type", "Reactions", "Attachments", "Filename"]
    posts.append(headers)

    for row in query_db_postgres(query,(chan_id,earliest_date,latest_date),True):

        file_id = row[5]

        posts.append(row)
        fileidlist.append(file_id)

    if not teams_export :

        export_dir_name = f"{string_to_filename(chan_name)}_export"
        os.makedirs(f"{export_dir_name}", exist_ok=True)

        file_export_data = export_to_csv_clean(posts)
        with open(f"{export_dir_name}/{export_dir_name}.csv", 'wb') as file:
            file.write(file_export_data)

        metadata = export_metadata_json(chan_id)

        member_file_name = f'{export_dir_name}/{string_to_filename(chan_name)}_metadata.json'

        with open(member_file_name, 'wb') as file:
            file.write(metadata)

        st.success(
            "Download Complete with " + string_to_filename(chan_name) + ".csv"
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

        export_attachments(fileidlist,False, export_dir_name)
    else:
        download_data = export_to_csv_clean(posts)

        # note that downloadstring is now a tuple !
        downloadstring = (string_to_filename(chan_name) + ".csv", download_data)

        # fileid-list also exported instead of directly calling "export_attachments" as we need
        # to store the attachments in the correct location of the zip export
        return downloadstring, fileidlist

def export_attachments(file_ids, teams_export, export_dir_name = None):
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

    # prepare the query for retrieving the file mimetype / extension
    # you can also retrieve the original file name if you want.
    query = """SELECT fileinfo.extension FROM fileinfo WHERE fileinfo.id = %s"""
    filetype_extension = ""

    output = []
    # retrieve and export files via mattermost api
    for ids in file_ids:
        if ids is None:
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
            for row in query_db_postgres(query,formatted_id,True):
                filetype_extension = row[0]

            final_filename = f"{formatted_id}.{filetype_extension}"

            # attachments in teams export must be saved in the exported zip file, thus they will be returned
            if not teams_export:
               # output directory
                attachment_dir = f"{export_dir_name}/attachments"
                # ensure the root directory exists
                os.makedirs(f"{export_dir_name}", exist_ok=True)
                # ensure the attachment output directory exists
                os.makedirs(f"{attachment_dir}", exist_ok=True)

                # adjust the output path
                final_filename = f"{attachment_dir}/{final_filename}"

                # check if the file already exists prior to download
                if os.path.exists(final_filename):
                    print(f"{final_filename} already exists. Skipping download.")
                else:
                    with open(final_filename, 'wb') as f:
                        f.write(file_data)
                    print("Download Complete with " + final_filename)
            else:
                output.append((final_filename,file_data))

    # note that this value only serves a purpose for team-exports
    return output