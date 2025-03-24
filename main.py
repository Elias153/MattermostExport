import streamlit as st
import webfunctions as web
from channelexport import export_data_postgres
from database import query_db_postgres
from dmgroupexport import get_channels_from_dmgroup, export_direct_messages
from teamexport import export_data_postgres_team
from webfunctions import teams_name_dropdown_postgres

if __name__ == '__main__':

    web.show_background()

    st.title(":blue[MM.C.P.E.]")
    st.write(":green[The streamlit MatterMost Channel Post Exporter] ;-)")

    team_id, team_name = teams_name_dropdown_postgres()

    if st.button('Export Team'):
        export_data_postgres_team(team_id, team_name)

    # create the dropdown selection with channel names, as well as the selection of the
    # starting export-date and ending-export-date
    channel_id, channel_name,earliest_date,latest_date = web.channel_name_dropdown_postgres()

    #team_id, team_name = teams_name_dropdown_postgres()

    #if st.button('Export Team'):
    #    export_data_postgres_team(team_id, team_name)

    # Create a clickable export-button
    if st.button('Export Channel'):

        st.markdown(f""":orange[Button clicked, channel choice was] <span style='color: yellow;'>{channel_name}</span>
          :orange[with id] <span style='color: yellow;'> {channel_id}</span>""", unsafe_allow_html=True)
        # export the data with previously given arguments
        export_data_postgres(channel_id, channel_name, earliest_date, latest_date)

    if st.button('Export DMs/Groups'):
        channel_names, channel_ids = get_channels_from_dmgroup()
        export_direct_messages(channel_names, channel_ids)