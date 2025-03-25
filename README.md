# MM.C.P.E.
_The Streamlit Mattermost Channel Post Exporter_ 
- credits to https://github.com/datadelft/MM.C.P.E./tree/master (base of the script)
> Script has been extended to include export of attachments and teams, and include support for postgres instead of mysql.

## Introduction

The MM.C.P.E. is a little program that connects to your mattermost database 
directly. It reads the channels and presents them as a dropdown box. Selecting 
a channel allows you to export all messages in that channel together with the 
name of the poster. Exports will also be downloaded in CSV format.


## Installation
- Create database.yaml 
  - _see below: Configuration_
- Create connection.yaml
  - _see below: Configuration_
- Create virtual environment 
  - _python3 -m venv venv_
- Activate the virtual environment 
  - _source venv/bin/activate_
- Install dependencies 
  - _pip install -r requirements.txt_
- Run the program 
  - _streamlit run main.py_

Open your web-browser http://localhost:8501 
or over the network: http://xxx.xxx.xxx.xxx:8501


## Configuration

database.yaml should contain:

```
database: 
  host: <hostname or ip> 
  user: <database_username>
  password: <database_password> 
  database: <database_name, ie mattermost> 
```

connection.yaml should contain:

```
connection:
  url: "<mattermost server>"
  login_id: "<your_username>"
  password: "<your_password>"
```

connection.yaml is needed configuration for connection to the mattermost server for subsequent api requests for export of attachments
## Notes

1. This code only works if you are working with a postgres-database
2. Upon installing the requirements, you might come across the error : "**WARNING: Failed to activate VS environment: Could not parse vswhere.exe output**"
- The error you're encountering is likely due to a missing or improperly configured C++ build tools on your system, which are required for building some Python packages from source.
- To fix, download Microsoft Build Tools for Visual Studio from the official Microsoft website. During installation, make sure to select the "C++ build tools" workload.

| ![screenshot1](https://github.com/datadelft/MM.C.P.E./assets/56151011/7de1226e-784b-47b7-994c-d740fcf82db5) | ![screenshot2](https://github.com/datadelft/MM.C.P.E./assets/56151011/14cbf540-7c1d-4ceb-bd00-f0b73337a646) | ![screenshot3](https://github.com/datadelft/MM.C.P.E./assets/56151011/f5df9c61-af8a-4cbb-aab9-ab775e93fb76)|








