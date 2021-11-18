# Linux Command Handler
> Written in Python 3 using urwid(https://urwid.org) and Sqlite3 as database

This is a simple terminal-based application to manage Linux commands, on any Linux host.

You can search, run, add, update, remove any Linux command from a sqlite database.
The application also can handle uploading a file with the list of commands
into the dabase, or download all commands from database, into the same file named as
'download'.


### Requirements:
- Python 3.5 or up 
- urwid package needed to be installed by:<br>
```shell
$ pip install urwid
```

Simply copy app.py into a directory(preferably, an empty one) and then let the application run by: <br>
```shell
$ python3 app.py
```

### Note:
If no database file provided, application will automatically creates a sample databse file with some elementary commands as demo. 
You can populate the initialized database by click on upload button while you provide a file named as 'download' with your list of commands in the same directory leval as file app.py.

Here's an image of the application main screen:
![urwid-python-cmdhdler](screenshot.png)

