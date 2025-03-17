# unlike the other functions defined in this class, this function selects ALL* channels and exports them.
# * meaning ALL direct messages OR group channels, or rather : channels which are not assigned to a specific team
from channelexport import export_data_postgres
from database import query_db_postgres
from webfunctions import select_default_timestamps

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

# export the data as a zip archive
def export_direct_messages():
    # placeholder
    p = 1