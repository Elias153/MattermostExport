import base64
import csv
import io
import mimetypes
import zipfile
from io import StringIO
import yaml
import streamlit as st
import magic
import streamlit.components.v1 as components

def create_zip_archive(file_tuples):
    """
    Given a list of tuples (file_name, file_data), create a ZIP archive in memory
    and return its bytes.
    """
    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_name, file_data in file_tuples:
            # file_data should be bytes (e.g., CSV data encoded in utf-8)
            zf.writestr(file_name, file_data)
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
    st.download_button(
        label="Download CSV",
        data=csv_data_str,
        file_name=file_name,
        mime="text/csv"
    )

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

def determine_file_extension(file_name):
    mime = magic.Magic(mime=True)
    mime = mime.from_file(file_name)
    extension = mimetypes.guess_extension(mime)

    return extension

def generate_zip(file_name, data):
    """
    Returns a tuple (file_name, base64_data, mime) for later use.
    """
    #b64 = base64.b64encode(data).decode()
    return file_name, data