import streamlit as st
import webfunctions as web
from database import query_db_postgres

if __name__ == '__main__':

    web.show_background()

    st.title(":blue[MM.C.P.E.]")
    st.write(":green[The streamlit MatterMost Channel Post Exporter] ;-)")

    # create the dropdown selection with channel names, as well as the selection of the
    # starting export-date and ending-export-date
    channel_id, channel_name,earliest_date,latest_date = web.channel_name_dropdown_postgres()

    # Create a clickable export-button
    if st.button('Export'):

        st.markdown(f""":orange[Button clicked, channel choice was] <span style='color: yellow;'>{channel_name}</span>
          :orange[with id] <span style='color: yellow;'> {channel_id}</span>""", unsafe_allow_html=True)
        # export the data with previously given arguments
        web.export_data_postgres(channel_id, channel_name, earliest_date, latest_date)
