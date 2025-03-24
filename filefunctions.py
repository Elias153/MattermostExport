import base64
import csv
import io
import mimetypes
import os
import zipfile
from datetime import datetime
from io import StringIO
import yaml
import streamlit as st
import magic

def create_zip_archive(file_tuples,attachment_id_lists, member_lists):
    from channelexport import export_attachments
    """
    Given a list of tuples (file_name, file_data), create a ZIP archive in memory.
    For each tuple, a folder is created based on the file name (without extension),
    and within that folder an empty "attachments" folder is created.
    The CSV file is written in the parent folder, leaving the attachments folder empty.

    a file_tuple in file_tuples at e.g. index 1 also corresponds to the list of attachment_ids at index 1 in attachment_id_lists,
    analog to the index in member_lists
    """
    index = 0
    attachments = []
    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_name, file_data in file_tuples:
            # Create a folder based on the file's base name (e.g., "report.csv" -> "report")
            folder_name, _ = os.path.splitext(file_name)
            folder_path = folder_name + "/"  # e.g., "report/"
            attachments_path = folder_path + "attachments/"  # e.g., "report/attachments/"

            # Add the parent folder and the empty attachments folder to the ZIP
            zf.writestr(folder_path, "")
            zf.writestr(attachments_path, "")

            # Write the CSV file in the parent folder (outside of attachments)
            file_path = folder_path + file_name  # e.g., "report/report.csv"
            try:
                zf.writestr(file_path, file_data)
                #file_data = file_data.encode('utf-8')
            except TypeError:
                print(str(file_data) + " is a tuple.. ?")
                exit(1)
            #zf.writestr(file_path, file_data)

            # channel-member export
            file_member_data,is_constrained = member_lists[index]
            try:
                member_file_name = f'members.csv'
                if is_constrained:
                    member_file_name = f'members_private.csv'
                zf.writestr(folder_path+f"{member_file_name}",file_member_data)
            except TypeError:
                print(str(file_member_data) + " is a tuple.. ?")
                exit(1)

            # attachment export
            file_attachment_ids = attachment_id_lists[index]
            attachments = export_attachments(file_attachment_ids,True)

            # "None" is the return value if either the attachment export is not part of a team-export
            # OR (here) there was not an attachment found in the current channel.
            if attachments is not None:
                for att_file_name, att_file_data in attachments:
                    #print("This worked.")
                    att_file_path = attachments_path + att_file_name
                    zf.writestr(att_file_path, att_file_data)
                    print("Saved Attachment: " + att_file_path)
            index+=1

    mem_zip.seek(0)
    return mem_zip.read()

def read_database_config(file_path):
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config


def export_to_csv(data, file_name):
    # Create a CSV string from the data
    csv_data = StringIO()
    writer = csv.writer(csv_data, delimiter=';')
    writer.writerows(data)

    # Prepend BOM for UTF-8
    bom = '\ufeff'
    csv_data_str = (bom + csv_data.getvalue()).encode('utf-8').strip()

    with open(f'{file_name}', 'wb') as file:
        file.write(csv_data_str)

    #st.download_button(
    #    label="Download CSV",
    #    data=csv_data_str,
    #    file_name=file_name,
    #    mime="text/csv"
    #)

def export_to_csv_clean(data):
    # Create a CSV string from the data
    csv_data = StringIO()
    writer = csv.writer(csv_data, delimiter=';')
    writer.writerows(data)

    # Prepend BOM for UTF-8
    bom = '\ufeff'
    csv_data_str = (bom + csv_data.getvalue()).encode('utf-8').strip()
    return csv_data_str

def string_to_filename(s):
    # Replace invalid characters with underscores
    valid_chars = '-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    filename = ''.join(c if c in valid_chars else '_' for c in s)
    # Remove leading/trailing spaces and double underscores
    filename = filename.strip().replace('__', '_')
    return filename

def determine_file_extension(file_data):
    mime = magic.Magic(mime=True)
    mime_type = mime.from_buffer(file_data)
    return mimetypes.guess_extension(mime_type)