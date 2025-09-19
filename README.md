# MM.C.P.E.
_The Streamlit Mattermost Channel Post Exporter_ 
- credits to https://github.com/datadelft/MM.C.P.E./tree/master (base of the script)
> Script has been extended to include export of attachments (and respective filenames) and teams, and include support for postgres instead of mysql.
> Also now exports metadata such as channelmembers, whether the channel is private/public, and channeladmins in JSON format

## Introduction

The MM.C.P.E. is a little program that connects to your mattermost database 
directly. It reads the channels and presents them as a dropdown box. Selecting 
a channel allows you to export all messages in that channel together with the 
name of the poster. Exports will also be downloaded in CSV format. 

It is encouraged and recommended to read through the whole document here, as it is also explained what will be exported and what will be not exported at the moment.


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
ps: do not forget the `https://` in front of your URL !

connection.yaml is needed configuration for connection to the mattermost server for subsequent api requests for export of attachments

requirements.txt should also contain `python-magic-bin` (Windows) or `python-magic` (Linux) depending on your OS.

## Important

### What is not (currently) exported ?
- Threads : If user1 replied to user2 for example; this is not exported.
- Reactions (see notes down below)
- Bot Messages : As they are making use of some sort of plugins to show something, and are not "actual" messages
- Messages made with other kinds of API / Plugins ; most prominent example being messages with type "slack-attachment". 
- Team-Icons (as I am unsure where that data (-> their image id) is stored in the database)
- Other user-specific data; this script currently only intends to export specifically chat-data as of now

TODO : Add some indicator that content is not exported (e.g. as the message itself)

## Notes

1. This code only works if you are working with a postgres-database
2. Reactions are not currently exported, as there is a concern as to how (in which form) to export them. Also questionable whether there is a 1-to-1 translation of the emoji-names to the other chat platforms.
3. The requirement only currently requires installation of the binary of psycopg2. For own purposes, you may want to install this package from source.
4. This Script is currently not intended to be available for third party use, and it may need to be modified if that is the intended purpose.

| ![screenshot1](https://github.com/datadelft/MM.C.P.E./assets/56151011/7de1226e-784b-47b7-994c-d740fcf82db5) | ![screenshot2](https://github.com/datadelft/MM.C.P.E./assets/56151011/14cbf540-7c1d-4ceb-bd00-f0b73337a646) | ![screenshot3](https://github.com/datadelft/MM.C.P.E./assets/56151011/f5df9c61-af8a-4cbb-aab9-ab775e93fb76)|








