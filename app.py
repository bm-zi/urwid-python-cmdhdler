# app.py

__author__ = "bmzi"
__version__ = "1.1"
__status__ = "Under Development"

import urwid
from subprocess import call
import subprocess
import os, sys

import sqlite3
import pathlib


# -------------- 
# DATABASE MODEL
# --------------
class CommandModel(object):
    def __init__(self):
        self._db = sqlite3.connect('data.db')
        self._db.row_factory = sqlite3.Row
        self._db.cursor().execute('''
            CREATE TABLE IF NOT EXISTS items(
                id INTEGER PRIMARY KEY,
                item TEXT,
                UNIQUE(item) ON CONFLICT REPLACE)
        ''')
        self._db.commit()
        self.current_id = None


    def add(self, item):
        '''Add an item to databse into the table items'''
        self._db.cursor().execute(
            '''INSERT INTO items(item) VALUES(:item)''', 
            (item,))
        self._db.commit()


    def upload_list_to_db(self, cmd_list):
        '''
            Populate table items with lines taken from a
            list named as SAMPLE_COMMANDS at the end of the script.
        '''
        try:
            for cmd in cmd_list:
                self.add(cmd.strip())
        except:
            print('Error uploading list') 
                

    def upload_file_to_db(self, file_name):
        '''
            Populate table items with lines taken from a
            file in current directory.
        '''
        try:
            self._db.cursor().execute('''DELETE FROM items''')
            with open(file_name) as f:
                for line in f.readlines():
                    self.add(line.strip())
        except:
            print('File "{}" does not exist in {}'.format(file_name, 
                pathlib.Path(__file__).parent.resolve()))


    def list_items(self):
        '''
            Get list of rows in table items, 
            each row as an object of class row_factory
        '''
        all = self._db.cursor().execute("SELECT item FROM items ORDER BY id DESC").fetchall()
        rows = []
        for el in all:
            rows.append(el[0])
        return rows


    def list_items_dict(self):
        '''
            Get list of rows in table items, 
            each row with format of a dictionary
        '''
        rows = []
        for row in self.list_items():
            rows.append(dict(row))
        return rows


    def get_item(self, item):
        return self._db.cursor().execute(
            "SELECT item FROM items WHERE item=:item",
            {"item": item}).fetchone()


    def get_item_by_id(self, item_id):
        return self._db.cursor().execute(
            "SELECT item FROM items WHERE id=:id",
            {"id": item_id}).fetchone()


    def get_current_item(self):
        if self.current_id is None:
            return {"item": ""}
        else:
            return self.get_item(self.current_id)
    

    def delete_item(self, item):
        self._db.cursor().execute('''
            DELETE FROM items WHERE item=:item''', {"item": item})
        self._db.commit()


    def filter_item(self, pattern):
        listitems = self.list_items()
        result = []
        for item in listitems:
            if pattern in item:
                result.append(item)
        return result 
                        

    def populate_db(self, cmd_list):
        result = self._db.cursor().execute('''SELECT COUNT(*) from items''').fetchall()
        if result[0][0] == 0:
            self.upload_list_to_db(cmd_list)
        else:
            print("Database not empty, list not uploaded.")

# ------------------------------
# You may need to run followings:
# -------------------------------
# im = CommandModel()
# im.upload_file_to_db('cmds')
# im.add('item number 1000')
# im.delete_item(280)
# im.upload_file_to_db('cmds')
# im.current_id = 10
# im.update_current_item('the last new item')
# print(dict(im.get_current_item()))
# print(im.list_items_dict())
# for el in im.list_items_dict():
#     print(dict(el)['id'], "\t" , dict(el)['item'])


from pyperclip import copy


# -----------------
# Search Box Widget
# -----------------
class SearchWidget(urwid.WidgetWrap):
    def __init__(self):
        self.model = CommandModel()
        self.edit = urwid.Edit(u"Search: ")
        self._w = self.edit


    def keypress(self, size, key):
        if key == 'enter':
            self.get_cmd_list()
        super().keypress(size, key)


    def get_cmd_list(self):
        searchfield_value = self.edit.edit_text
        if searchfield_value == '' or searchfield_value == ' ' or searchfield_value == None:
            return self.model.list_items()
        else:
            cmds = self.model.filter_item(str(self.edit.edit_text).strip())
            # main(cmds)
            if cmds:
                palette = [('unselected', 'default', 'default'),
                ('selected', 'standout', 'default', 'bold')]
                mw = urwid.Padding(MainWidget(cmds), left=2, right=2)
                top = urwid.Overlay(mw, urwid.SolidFill(u'\N{MEDIUM SHADE}'),
                                align='center', width=('relative', 80),
                                valign='middle', height=('relative', 80),
                                min_width=20, min_height=9)
                urwid.MainLoop(top, palette=palette).run()
            else:
                Utils.restart_script()


# -----------
# MAIN WIDGET
# -----------
class MainWidget(urwid.WidgetWrap):
    def __init__(self, labels):
        self.model = CommandModel()
        self.edit = SearchWidget()
        self.labels = labels
        self.search_widget = urwid.LineBox(urwid.Filler(self.edit))
        self.list_walker = urwid.SimpleFocusListWalker([
            urwid.AttrMap(urwid.SelectableIcon(label), 'unselected', focus_map='selected') for label in self.labels
            ])
        self.list_box = urwid.Pile(self.list_walker)
        self.ew = [urwid.Edit(u": ", command, wrap='clip') for command in self.labels]
        self.body = urwid.Filler(self.ew[0])
        self.btns = self.create_buttons()
        self.pile = self.piler()
        super().__init__(self.pile)
        self.update_focus(new_focus_position=0)


    def update_focus(self, new_focus_position=None):
        self.list_box.focus_item.set_attr_map({None: 'unselected'})
        try:
            self.list_box.focus_position = new_focus_position
            self.body = urwid.Filler(self.ew[new_focus_position])
        except IndexError:
            pass
        self.list_box.focus_item.set_attr_map({None: 'selected'})
        self.pile = self.piler()
        super().__init__(urwid.LineBox(self.pile, "COMMAND HANDLER"))


    def piler(self):
        return urwid.Pile([
                            ('fixed', 3, self.search_widget),
                            ('weight', 89, urwid.ListBox(self.list_walker)),
                            ('fixed', 2, urwid.Filler(urwid.Divider())),
                            ('fixed', 2, self.body),
                            ('fixed', 3, self.btns),
                            ('fixed', 1, urwid.Filler(
                                urwid.Text(u"Press <F1> key for help")
                                )
                            )
                        ],  focus_item=1
                    )


    def keypress(self, size, key):
        if key == 'up':
            self.update_focus(new_focus_position=self.list_box.focus_position - 1)
        elif key == 'down':
            self.update_focus(new_focus_position=self.list_box.focus_position + 1)
        elif key == 'ctrl e':
            Utils.run_cmd(self.body.base_widget.edit_text)
        elif key == 'ctrl x':
            cmd = self.body.base_widget.edit_text
            prompt = 'echo  Press \<Enter\> to continue!'
            os.system(f"gnome-terminal --tab -- bash -c \"{cmd} ; echo; echo; {prompt} ; read line \" ")
        elif key == 'ctrl o':
            if Utils.is_tool('vim'):
                os.system("vim \"+normal G$\" output")       
                Utils.restart_script()
        elif key == 'ctrl u':
            if self.body.base_widget.edit_text:
                self.body.base_widget.edit_text = ''   
        elif key == 'tab':
            self.pile.focus_item = 3
        elif key == 'ctrl home':
            self.pile.focus_item = 0
        elif key == 'ctrl end':
            self.pile.focus_item = 4
        elif key in {'l', 'c', 'r', 't', 'x', ' '}:
            return super().keypress(size, key)
        elif key == 'f5':
            Utils.restart_script()
        elif key == 'f6':
            Utils.remove_temp_files()
        elif key == 'f8':
            Utils.exit_program()
        elif key == 'f1':
            def resume_app(key):
                if key:
                    Utils.restart_script()
            help_text = u'''
            |||||||||||||||||||| SHORTCUT KEYS |||||||||||||||||||||

            tab ............. Goes to prompt. prompt is ": " and is
                              located at the bottom of command menu.

            ctrl up ............ Goes to search field.
            ctrl down .......... Goes to function window at the bottom.

            f5 ................. Restarts the app.
            f6 ................. Removes all temp files, used by app
            f8 ................. Exits app. (or use Quit button)
            
            ctrl e ............. Runs command and logs output.
            ctrl x ............. Runs command in a separate terminal.
            ctrl o ............. Open commands history.

            Copy ............... Command is copied into clipboard
            Update ............. Updates the command typed in prompt.
            Add ................ Adds the command typed in prompt.
            Remove ............. Removes selected command.
            Doownload .......... Downloads all commands to file download.
            Upload ............. Uploads file download into database.


            Press any key to exit this page!
            '''    
            h = urwid.Filler(urwid.Text(help_text))
            urwid.MainLoop(h, unhandled_input=resume_app).run()

        super().keypress(size, key)


    def create_buttons(self):
        '''Creates function buttons with click event handlers,
           in class MainWidget
        '''

        def upload(button):
            self.model.upload_file_to_db('download')

        def download(button):
            cmds_list = self.model.list_items()
            with open('download', 'w') as f:
                for el in cmds_list:
                    f.write(el + "\n")
            Utils.restart_script()

        def remove_cmd(button):
            cmd = self.body.base_widget.edit_text
            self.model.delete_item(cmd)
            Utils.restart_script()

        def add_cmd(button):
            cmd = self.body.base_widget.edit_text
            self.model.add(cmd)
            Utils.restart_script()

        def edit_cmd(button):
            cmd = self.body.base_widget.edit_text
            with open('cmdedit', 'w') as f:
                f.write(cmd)
            self.model.delete_item(cmd)
            os.system('vim cmdedit')
            with open('cmdedit') as f:
                self.model.add(f.read().strip())
            Utils.restart_script()

        def copy_to_clipboard(button):
            cmd = self.body.base_widget.edit_text
            copy (cmd)
            # os.system("gnome-terminal --tab -- bash")
            Utils.restart_script()

        all_buttons = []
        actions = ['Copy', 'Update','Add', 'Remove', 'Download', 'Upload']
        for b in actions:
            button = urwid.LineBox(urwid.Filler(MyButton(b)))
            if b == 'Copy':
                urwid.connect_signal(button.base_widget, 'click', copy_to_clipboard)
            elif b == 'Update':
                urwid.connect_signal(button.base_widget, 'click', edit_cmd)
            elif b == 'Add':
                urwid.connect_signal(button.base_widget, 'click', add_cmd)
            elif b == 'Remove':
                urwid.connect_signal(button.base_widget, 'click', remove_cmd)
            elif b == 'Download':
                urwid.connect_signal(button.base_widget, 'click', download)
            elif b == 'Upload':
                urwid.connect_signal(button.base_widget, 'click', upload)
            
            all_buttons.append(button)
        return urwid.Columns(all_buttons, dividechars=1, min_width=10)

class MyButton(urwid.Button):
    button_left = urwid.Text("")
    button_right = urwid.Text("")
    def __init__(self, label, on_press=None, user_data=None):
        super().__init__(label, on_press=on_press, user_data=user_data)


# ------------------------
# BUNDLE OF UTIL FUNCTIONS
# ------------------------
class Utils:

    def run_cmd(cmd):
        with open('cmdfile', 'w') as f:
            f.write(cmd)
        try:
            out = subprocess.Popen(['/usr/bin/sh', 'cmdfile'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            cmd_output, _ = out.communicate()

            cmd_output_str = cmd_output.decode(encoding='utf-8')
            _output = list(cmd_output_str.split('\n'))

            org_stdout = sys.stdout
            sys.stdout = open('output', 'a', encoding='utf-8')
            
            print(f"$ {cmd}")
            for line in _output:
                print(line)
            print()

            sys.stdout.close()
            sys.stdout = org_stdout

        except Exception as e:
            with open('output.txt', 'w', encoding='utf-8') as f:
                f.write(str(e))
                    
        if Utils.is_tool('vim'):
            os.system("vim \"+normal G$\" output")       
            Utils.restart_script()
        elif Utils.is_tool('gedit'):
            os.system("gedit output +")
            Utils.restart_script()
        else:
            Utils.restart_script()


    def restart_script():  # used by <f5> key
        os.system('stty echo')  # os.system('reset')
        os.execv(sys.executable, ['python'] + sys.argv)


    def is_tool(name):
        """Check whether `name` is in the PATH and marked as executable."""
        from shutil import which
        return which(name) is not None


    def remove_temp_files(): # used by <f6> key
        files = ['cmdedit', 'cmdfile', 'output', 'download']
        for f in files:
            if os.path.isfile(f):
                os.remove(f)
    

    def exit_program(): # used by <F8> key
        Utils.remove_temp_files()
        raise urwid.ExitMainLoop()


# -----------------------------------------
# BACKUP OF COMMANDS LIST, IF DB IS EMPTY,
# WILL AUTOMATICALLY WILL BE UPLOADED TO DB.  
# -----------------------------------------
SAMPLE_COMMANDS ="""
tree -L 1 --dirsfirst
df -h / /home
cal
sensors
lastlog
route
ip addr show wlp2s0
ps -efa
du -sh .
netstat -n
last
groups
iostat
mpstat
manpath
cat /etc/os-release
cat /etc/hosts
dpkg -l
systemctl list-sockets
systemctl list-unit-files
stat -c %a /etc/passwd
df -t ext4 -h
uname -a
echo end of the file!"""


# ------------
# MAIN PROGRAM
# ------------
def main(cmds):
    sample_cmds_list = SAMPLE_COMMANDS.split('\n')

    cm = CommandModel()
    cm.populate_db(sample_cmds_list)

    if cmds:
        cmdlist = cmds
    else:
        cmdlist = cm.list_items()

    palette = [('unselected', 'default', 'default'),
            ('selected', 'standout', 'default', 'bold')]

    call('clear')

    mw = urwid.Padding(MainWidget(cmdlist), left=2, right=2)
    top = urwid.Overlay(mw, urwid.SolidFill(u'\N{MEDIUM SHADE}'),
                    align='center', width=('relative', 90),
                    valign='middle', height=('relative', 85),
                    min_width=20, min_height=9)
    urwid.MainLoop(top, palette=palette).run()

if __name__ == '__main__':
    main(cmds=None)