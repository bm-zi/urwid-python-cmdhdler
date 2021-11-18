import urwid
import os, sys, subprocess, pathlib
import sqlite3

__author__ = "bmzi"
__version__ = "1.0"
__status__ = "Under Development"

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
            list named as CMDLIST at the end of the script.
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
        # return self._db.cursor().execute("SELECT item FROM items").fetchall()
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
    

    # Not used yet
    def update_current_item(self, item):
        if self.current_id is None:
            self.add(item)
        else:
    
            self._db.cursor().execute(
                    "UPDATE items SET item=:item WHERE id=:id", 
                    {"item":item, "id": self.current_id}
                )
        self._db.commit()


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
        val = self.edit.edit_text
        if val == '' or val == ' ' or val == None:
            return self.model.list_items()
        else:
            cmds = self.model.filter_item(str(self.edit.edit_text).strip())
            main(cmds)
            raise urwid.ExitMainLoop()
            

# -----------
# MAIN WIDGET
# -----------
class MainWidget(urwid.WidgetWrap):
    def __init__(self, labels):
        self.model = CommandModel()
        self.edit = SearchWidget()
        self.labels = labels
        self.sw = urwid.LineBox(urwid.Filler(self.edit))
        self.lw = urwid.SimpleFocusListWalker([
            urwid.AttrMap(urwid.SelectableIcon(label), 'unselected', focus_map='selected') for label in self.labels
            ])
        self.lb = urwid.Pile(self.lw)
        self.ew = [urwid.Edit(u": ", command, wrap='clip') for command in self.labels]
        self.body = urwid.Filler(self.ew[0])
        self.btns = self.create_buttons()
        self.pile = self.piler()
        super().__init__(self.pile)
        self.update_focus(new_focus_position=0)


    def update_focus(self, new_focus_position=None):
        self.lb.focus_item.set_attr_map({None: 'unselected'})
        try:
            self.lb.focus_position = new_focus_position
            self.body = urwid.Filler(self.ew[new_focus_position])
        except IndexError:
            pass
        self.lb.focus_item.set_attr_map({None: 'selected'})
        self.pile = self.piler()
        super().__init__(urwid.LineBox(self.pile, "COMMAND HANDLER"))


    def piler(self):
        return urwid.Pile([
                            ('fixed', 3, self.sw),
                            ('weight', 90, urwid.ListBox(self.lw)),
                            ('fixed', 1, urwid.Filler(urwid.Divider())),
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
            self.update_focus(new_focus_position=self.lb.focus_position - 1)
        elif key == 'down':
            self.update_focus(new_focus_position=self.lb.focus_position + 1)
        elif key == 'ctrl x':
            OutputWidget(self.body.base_widget.edit_text)
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
        elif key == 'ctrl e':
            Utils.exit_program()
        elif key == 'f1':
            def resume_app(key):
                if key:
                    Utils.restart_script() 

            help_text = u'''
            |||||||||||||||||||| SHORTCUT KEYS |||||||||||||||||||||

            tab ............. Goes to prompt. prompt is ": " and is
                              located at the bottom of commands list.

            ctrl up ......... Goes to search field.
            ctrl down ....... Goes to function window at the bottom.
            f5 .............. Restarts the app.
            ctrl x .......... Runs selected command.
            ctrl e .......... Exits app. (or use Quit button)

            
            |||||||||||||||||||| BUTTONS |||||||||||||||||||||||||||

            Update .......... Edits and updates selected command, 
                              in vim editor.

            Add ............. Adds the command typed in prompt.
            Remove .......... Removes selected command.
            Doownload ....... Downloads all commands to file download.
            Upload .......... Uploads file download into database.

            Quit ............ Quits app and removes temp files.


            Press any key to exit this page!
            '''
            h = urwid.Filler(urwid.Text(help_text))
            urwid.MainLoop(h, unhandled_input=resume_app).run()
        super().keypress(size, key)


    def create_buttons(self):
        def edit_cmd(button):
            cmd = self.body.base_widget.edit_text
            with open('cmdedit', 'w') as f:
                f.write(cmd)
            self.model.delete_item(cmd)
            os.system('vim cmdedit')
            with open('cmdedit') as f:
                self.model.add(f.read().strip())
            Utils.restart_script()

        def add_cmd(button):
            cmd = self.body.base_widget.edit_text
            self.model.add(cmd)
            Utils.restart_script()


        def remove_cmd(button):
            cmd = self.body.base_widget.edit_text
            self.model.delete_item(cmd)
            Utils.restart_script()


        def download(button):
            cmds_list = self.model.list_items()
            with open('download', 'w') as f:
                for el in cmds_list:
                    f.write(el + "\n")
            Utils.restart_script()


        def upload(button):
            self.model.upload_file_to_db('download')
            

        def exit_program(button):
            Utils.exit_program()

        all_buttons = []
        actions = ['Update','Add', 'Remove', 'Download', 'Upload', 'Quit']
        for b in actions:
            button = urwid.LineBox(urwid.Filler(urwid.Button(b)))
            if b == 'Update':
                urwid.connect_signal(button.base_widget, 'click', edit_cmd)
            elif b == 'Add':
                urwid.connect_signal(button.base_widget, 'click', add_cmd)
            elif b == 'Remove':
                urwid.connect_signal(button.base_widget, 'click', remove_cmd)
            elif b == 'Download':
                urwid.connect_signal(button.base_widget, 'click', download)
            elif b == 'Upload':
                urwid.connect_signal(button.base_widget, 'click', upload)
            elif b == 'Quit':
                urwid.connect_signal(button.base_widget, 'click', exit_program)
            all_buttons.append(button)
        return urwid.Columns(all_buttons, dividechars=1, min_width=10)


# ---------------------
# COMMAND OUTPUT WIDGET
# ---------------------
class OutputWidget(urwid.WidgetWrap):
    def __init__(self, cmd):
        self.cmd_str = cmd
        self.cmd_list = list(str(cmd).split())
        self.term = urwid.Terminal(['/usr/bin/sh', 'cmdfile'], encoding='utf-8')
        self.btn = urwid.Button('EXIT')
        self._w = self.show_output()
        
    def show_output(self):
        Utils.command_to_file(self.cmd_str)
        urwid.set_encoding('utf8')
        exitbtn = urwid.Filler(self.btn, valign='middle')
        term_widget = urwid.LineBox(self.term, title=self.cmd_str, title_align='left')
        frame = urwid.LineBox(urwid.Pile([
                                            ('weight', 70, term_widget),
                                            ('fixed', 1, exitbtn),
                                            ], focus_item=1
                                            ),
                                    title='OUTPUT')
        def exitbtn(btn):
            Utils.restart_script()

        urwid.connect_signal(self.btn, 'click', exitbtn)
        loop = urwid.MainLoop(frame)
        loop.screen.set_terminal_properties(256)
        loop.run()


# ------------------------
# BUNDLE OF UTIL FUNCTIONS
# ------------------------
class Utils:
    def commands_list():
        myfile = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'cmds')
        l = []
        with open(myfile)as f:
            for line in f.readlines():
                l.append(line.strip())
            return l

    def command_to_file(cmd):
        with open('output', 'a') as f:
            f.write("\n\n\n")
            f.write(f"$ {cmd}")

        with open('cmdfile', 'w') as f:
            cmd = cmd + ' | tee -a output'
            f.write(cmd)
    
    def restart_script():
        os.system('stty echo')  # os.system('reset')
        os.execv(sys.executable, ['python'] + sys.argv)


    def exit_program():
        if os.path.isfile('cmdedit'):
            os.remove('cmdedit')
        if os.path.isfile('cmdfile'):
            os.remove('cmdfile')
        if os.path.isfile("output"):
            os.remove('output')
        if os.path.isfile("download"):
            os.remove('download')
        raise urwid.ExitMainLoop()  



# -----------------------------------------
# BACKUP OF COMMANDS LIST, IF DB IS EMPTY,
# WILL AUTOMATICALLY WILL BE UPLOADED TO DB.  
# -----------------------------------------
CMDLIST ="""
ls -ltr
tree -L 1 --dirsfirst
df -h / /home
cal
sensors
lastlog
route
ip addr show wlp2s0
ps -ef
du -sh .
netstat
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
df
uname -a
ps -efa
echo end of the file!
"""


# ------------
# MAIN PROGRAM
# ------------
def main(cmds):
    cmd_list = CMDLIST.split('\n')

    CURRENT_DIR = os. getcwd()
    cm = CommandModel()
    cm.populate_db(cmd_list)

    if cmds:
        cmdlist = cmds
    else:
        cmdlist = cm.list_items()


    palette = [('unselected', 'default', 'default'),
            ('selected', 'standout', 'default', 'bold')]
    subprocess.call('clear') 


    mw = urwid.Padding(MainWidget(cmdlist), left=2, right=2)
    top = urwid.Overlay(mw, urwid.SolidFill(u'\N{MEDIUM SHADE}'),
                    align='center', width=('relative', 80),
                    valign='middle', height=('relative', 80),
                    min_width=20, min_height=9)
    urwid.MainLoop(top, palette=palette).run()



main(cmds=None)