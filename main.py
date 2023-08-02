import wx
import wx.stc as stc
import os
import sys

STYLES = {
    "default": "fore:#000000,back:#FFFFFF,face:Courier New,size:10"
}

PYTHON_KEYWORDS = [
    "and", "as", "assert", "async", "await", "break", "class", "continue",
    "def", "del", "elif", "else", "except", "False", "finally", "for",
    "from", "global", "if", "import", "in", "is", "lambda", "None",
    "nonlocal", "not", "or", "pass", "raise", "return", "True", "try",
    "while", "with", "yield"
]

JAVA_KEYWORDS = [
    "abstract", "assert", "boolean", "break", "byte", "case", "catch",
    "char", "class", "const", "continue", "default", "do", "double",
    "else", "enum", "extends", "final", "finally", "float", "for",
    "if", "implements", "import", "instanceof", "int", "interface",
    "long", "native", "new", "package", "private", "protected",
    "public", "return", "short", "static", "strictfp", "super",
    "switch", "synchronized", "this", "throw", "throws", "transient",
    "try", "void", "volatile", "while"
]


class FindReplaceDialog(wx.Dialog):
    def __init__(self, *args, **kw):
        super(FindReplaceDialog, self).__init__(*args, **kw)

        self.find_text_ctrl = wx.TextCtrl(self)
        self.replace_text_ctrl = wx.TextCtrl(self)
        self.find_button = wx.Button(self, label="Find Next")
        self.replace_button = wx.Button(self, label="Replace")
        self.replace_all_button = wx.Button(self, label="Replace All")

        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        self.SetTitle("Find and Replace")
        self.find_text_ctrl.SetFocus()

    def __do_layout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.SetMinSize((400, 200))
        sizer.Add(wx.StaticText(self, label="Find what:"), 0, wx.ALL, 5)
        sizer.Add(self.find_text_ctrl, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(wx.StaticText(self, label="Replace with:"), 0, wx.ALL, 5)
        sizer.Add(self.replace_text_ctrl, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.find_button, 0, wx.ALL | wx.ALIGN_RIGHT, 5)
        sizer.Add(self.replace_button, 0, wx.ALL | wx.ALIGN_RIGHT, 5)
        sizer.Add(self.replace_all_button, 0, wx.ALL | wx.ALIGN_RIGHT, 5)
        self.SetSizer(sizer)
        sizer.Fit(self)

class SimpleTextEditor(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, size=(800, 600))

        self.dark_theme = True
        self.panel = wx.Panel(self)
        self.find_replace_dialog = None
        self.create_menu_bar()
        self.create_text_ctrl()
        self.multicursor_enabled = False
        self.file_modified = False
        self.current_file_path = None

        self.create_status_bar()
        self.apply_dark_theme()

        self.text_ctrl.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        self.text_ctrl.Bind(wx.stc.EVT_STC_CHANGE, self.on_text_change)

        try:
            if not sys.argv[1] == None:
                self.open_arg(sys.argv[1])
        except:
            pass

    def create_menu_bar(self):
        menu_bar = wx.MenuBar()

        file_menu = wx.Menu()
        file_menu.Append(wx.ID_OPEN, "Open")
        file_menu.Append(wx.ID_SAVE, "Save")
        file_menu.Append(wx.ID_SAVEAS, "Save As")
        file_menu.AppendSeparator()
        file_menu.Append(wx.ID_EXIT, "Exit")
        menu_bar.Append(file_menu, "File")

        edit_menu = wx.Menu()
        edit_menu.Append(wx.ID_FIND, "Find\tCtrl+F")
        edit_menu.AppendSeparator()
        edit_menu.Append(wx.ID_UNDO, "Undo\tCtrl+Z")
        edit_menu.Append(wx.ID_REDO, "Redo\tCtrl+Y")
        menu_bar.Append(edit_menu, "Edit")

        self.Bind(wx.EVT_MENU, self.on_find, id=wx.ID_FIND)

        view_menu = wx.Menu()
        theme_menu = wx.Menu()
        theme_menu.Append(10001, "Light Theme")
        theme_menu.Append(10002, "Dark Theme")
        view_menu.AppendSubMenu(theme_menu, "Theme")
        view_menu.Append(10003, "Multicursor")
        menu_bar.Append(view_menu, "View and Tools")

        about_menu = wx.Menu()
        about_menu.Append(10004, "About")
        menu_bar.Append(about_menu, "About")

        self.SetMenuBar(menu_bar)

        self.Bind(wx.EVT_MENU, self.on_open, id=wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self.on_save, id=wx.ID_SAVE)
        self.Bind(wx.EVT_MENU, self.on_save_as, id=wx.ID_SAVEAS)
        self.Bind(wx.EVT_MENU, self.on_exit, id=wx.ID_EXIT)
        self.Bind(wx.EVT_MENU, self.on_theme_change, id=10001)
        self.Bind(wx.EVT_MENU, self.on_theme_change, id=10002)
        self.Bind(wx.EVT_MENU, self.on_toggle_multicursor, id=10003)
        self.Bind(wx.EVT_MENU, self.on_about, id=10004)

    def on_find(self, event):
        if not self.find_replace_dialog:
            self.find_replace_dialog = FindReplaceDialog(self, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
                                                         size=(400, 220))

        self.find_replace_dialog.find_button.Bind(wx.EVT_BUTTON, self.on_find_next,
                                                  self.find_replace_dialog.find_button)
        self.find_replace_dialog.replace_button.Bind(wx.EVT_BUTTON, self.on_replace,
                                                     self.find_replace_dialog.replace_button)
        self.find_replace_dialog.replace_all_button.Bind(wx.EVT_BUTTON, self.on_replace_all,
                                                         self.find_replace_dialog.replace_all_button)

        self.find_replace_dialog.ShowModal()

    def on_find_next(self, event):
        if self.find_replace_dialog:
            find_text = self.find_replace_dialog.find_text_ctrl.GetValue()
            current_pos = self.text_ctrl.GetCurrentPos()

            start_pos = current_pos + 1

            next_pos_start, next_pos_end = self.text_ctrl.FindText(start_pos, self.text_ctrl.GetTextLength(), find_text,
                                                                   wx.stc.STC_FIND_MATCHCASE)
            if next_pos_start == -1:
                next_pos_start, next_pos_end = self.text_ctrl.FindText(0, current_pos, find_text,
                                                                       wx.stc.STC_FIND_MATCHCASE)

            if next_pos_start != -1:
                self.text_ctrl.GotoPos(next_pos_start)
                self.text_ctrl.SetSelection(next_pos_start, next_pos_end)

    def on_replace(self, event):
        if self.find_replace_dialog:
            find_text = self.find_replace_dialog.find_text_ctrl.GetValue()
            replace_text = self.find_replace_dialog.replace_text_ctrl.GetValue()

            start, end = self.text_ctrl.GetSelection()

            if start != end:
                self.text_ctrl.ReplaceSelection(replace_text)

    def on_replace_all(self, event):
        if self.find_replace_dialog:
            find_text = self.find_replace_dialog.find_text_ctrl.GetValue()
            replace_text = self.find_replace_dialog.replace_text_ctrl.GetValue()

            start_pos = 0
            replacements_count = 0

            while True:
                next_pos_start, next_pos_end = self.text_ctrl.FindText(start_pos, self.text_ctrl.GetTextLength(),
                                                                       find_text, wx.stc.STC_FIND_MATCHCASE)

                if next_pos_start == -1:
                    break


                self.text_ctrl.SetTargetStart(next_pos_start)
                self.text_ctrl.SetTargetEnd(next_pos_end)
                self.text_ctrl.ReplaceTarget(replace_text)

                start_pos = next_pos_start + len(replace_text)

                replacements_count += 1

            if replacements_count > 0:
                wx.MessageBox(f"Replaced {replacements_count} occurrences.", "Replace All", wx.OK | wx.ICON_INFORMATION)
            else:
                wx.MessageBox("No occurrences found.", "Replace All", wx.OK | wx.ICON_INFORMATION)

    def create_status_bar(self):
        self.statusbar = self.CreateStatusBar(3)
        self.update_status_bar()

    def create_text_ctrl(self):
        self.text_ctrl = wx.stc.StyledTextCtrl(self.panel, style=wx.TE_MULTILINE)
        self.panel.Bind(wx.EVT_SIZE, self.on_window_resize)
        self.text_ctrl.SetTabWidth(4)

        self.text_ctrl.SetMarginType(1, stc.STC_MARGIN_NUMBER)
        self.text_ctrl.SetMarginWidth(1, 50)
        self.text_ctrl.SetMarginSensitive(1, True)
        self.text_ctrl.SetWrapMode(stc.STC_WRAP_WORD)
        self.text_ctrl.SetEdgeColumn(0)
        self.text_ctrl.SetEdgeMode(stc.STC_EDGE_LINE)
        self.text_ctrl.SetCaretForeground(wx.WHITE)
        self.text_ctrl.SetCaretLineVisible(True)
        self.text_ctrl.SetCaretLineBackground(wx.Colour(0, 102, 204))

        self.text_ctrl.StyleSetSpec(stc.STC_STYLE_DEFAULT, STYLES["default"])
        self.text_ctrl.StyleClearAll()

        self.text_ctrl.Bind(wx.EVT_CHAR, self.on_char)
        self.text_ctrl.Bind(wx.stc.EVT_STC_UPDATEUI, self.on_update_ui)

    def on_open(self, event):
        openFileDialog = wx.FileDialog(
            self, "Open File", "", "", "All files (*.*)|*.*", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        )
        if openFileDialog.ShowModal() == wx.ID_CANCEL:
            return
        file_path = openFileDialog.GetPath()

        with open(file_path, "r") as file:
            content = file.read()

        self.text_ctrl.SetValue(content)
        self.current_file_path = file_path
        self.file_modified = False
        self.update_window_title()

        filename, file_extension = os.path.splitext(file_path)
        if file_extension == ".py":
            self.text_ctrl.SetLexer(stc.STC_LEX_PYTHON)
            if self.dark_theme:
                self.apply_python_syntax_dark()
            else:
                self.apply_python_syntax_light()
        elif file_extension == ".java":
            self.text_ctrl.SetLexer(stc.STC_LEX_CPP)
            if self.dark_theme:
                self.apply_java_syntax_dark()
            else:
                self.apply_java_syntax_light()

    def apply_python_syntax_dark(self):

        self.text_ctrl.StyleSetSpec(stc.STC_P_DEFAULT, "fore:#FFFFFF,back:#303030,face:Courier New,size:10")
        self.text_ctrl.StyleSetSpec(stc.STC_P_STRING, "fore:#80C080,size:10,back:#303030")
        self.text_ctrl.SetKeyWords(0, " ".join(PYTHON_KEYWORDS))

    def apply_python_syntax_light(self):
        # Python syntax highlighting settings for light theme
        self.text_ctrl.StyleSetSpec(stc.STC_P_DEFAULT, "fore:#000000,back:#FFFFFF,face:Courier New,size:10")
        self.text_ctrl.StyleSetSpec(stc.STC_P_STRING, "fore:#000000,back:#FFFFFF,size:10")
        self.text_ctrl.SetKeyWords(0, " ".join(PYTHON_KEYWORDS))

    def apply_java_syntax_dark(self):
        self.text_ctrl.StyleSetSpec(stc.STC_C_DEFAULT, "fore:#FFFFFF,back:#303030,face:Courier New,size:10")
        self.text_ctrl.StyleSetSpec(stc.STC_C_STRING, "fore:#FFFFFF,back:#303030,size:10")
        self.text_ctrl.SetKeyWords(0, " ".join(JAVA_KEYWORDS))

    def apply_java_syntax_light(self):
        # Java syntax highlighting settings for light theme
        self.text_ctrl.StyleSetSpec(stc.STC_C_DEFAULT, "fore:#000000,back:#FFFFFF,face:Courier New,size:10")
        self.text_ctrl.StyleSetSpec(stc.STC_C_STRING, "fore:#000000,back:#FFFFFF,size:10")
        self.text_ctrl.SetKeyWords(0, " ".join(JAVA_KEYWORDS))

    def open_arg(self, path):
        with open(path, "r") as file:
            content = file.read()

        self.text_ctrl.SetValue(content)
        self.current_file_path = path
        self.file_modified = False
        self.update_window_title()

    def on_save(self, event):
        if not self.current_file_path:
            self.on_save_as(event)
            return

        with open(self.current_file_path, "w") as file:
            file.write(self.text_ctrl.GetValue())

        self.file_modified = False
        self.update_window_title()

    def on_save_as(self, event):
        saveFileDialog = wx.FileDialog(self, "Save File", "", "", "All files (*.*)|*.*",
                                       wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if saveFileDialog.ShowModal() == wx.ID_CANCEL:
            return
        file_path = saveFileDialog.GetPath()

        with open(file_path, "w") as file:
            file.write(self.text_ctrl.GetValue())

        self.current_file_path = file_path
        self.file_modified = False
        self.update_window_title()

    def update_window_title(self):
        if not self.current_file_path:
            self.SetTitle("Undefined - wxTextEditor")
        else:
            filename = os.path.basename(self.current_file_path)
            if self.file_modified == True:
                title = f"{filename}* - wxTextEditor"
            else:
                title = f"{filename} - wxTextEditor"
            self.SetTitle(title)

    def on_exit(self, event):
        self.Close()

    def on_char(self, event):
        keycode = event.GetKeyCode()

        if keycode == wx.WXK_RETURN:
            line, col = self.text_ctrl.GetCurrentLine(), self.text_ctrl.GetColumn(self.text_ctrl.GetCurrentPos())
            self.text_ctrl.AddCaret(self.text_ctrl.PositionFromLine(line) + col)
            event.Skip()
        else:
            event.Skip()

    def on_text_change(self, event):
        self.file_modified = True
        self.update_window_title()

    def on_update_ui(self, event):
        self.update_status_bar()

    def update_status_bar(self):
        line, col = self.text_ctrl.GetCurrentLine() + 1, self.text_ctrl.GetColumn(self.text_ctrl.GetCurrentPos()) + 1
        length = len(self.text_ctrl.GetValue())
        self.statusbar.SetStatusText(f"Line: {line}, Column: {col}", 0)
        self.statusbar.SetStatusText(f"Total Characters: {length}", 1)
        self.statusbar.SetStatusText(
            "Multicursor: Disabled" if not self.multicursor_enabled else "Multicursor: Enabled", 2)

    def on_theme_change(self, event):
        theme = event.GetId()
        if theme == 10001:
            self.apply_light_theme()
        elif theme == 10002:
            self.apply_dark_theme()

    def apply_dark_theme(self):
        self.dark_theme = True
        self.text_ctrl.StyleSetBackground(stc.STC_STYLE_DEFAULT, wx.Colour(48, 48, 48))
        self.text_ctrl.StyleSetBackground(stc.STC_STYLE_LINENUMBER, wx.Colour(32, 32, 32))
        self.text_ctrl.StyleSetBackground(stc.STC_STYLE_INDENTGUIDE, wx.Colour(240, 240, 240))
        self.text_ctrl.StyleSetSpec(stc.STC_P_COMMENTLINE,
                                    "fore:#808080,size:10,back:#303030")  # Changed the foreground color

        self.text_ctrl.StyleSetForeground(stc.STC_STYLE_LINENUMBER, wx.Colour(240, 240, 240))

        self.text_ctrl.StyleSetSpec(stc.STC_P_DEFAULT, "fore:#FFFFFF,back:#303030,face:Courier New,size:10")
        self.text_ctrl.StyleSetSpec(stc.STC_P_NUMBER, "fore:#FF8080,size:10,back:#303030")
        self.text_ctrl.StyleSetSpec(stc.STC_P_STRING, "fore:#80C080,size:10,back:#303030")
        self.text_ctrl.StyleSetSpec(stc.STC_P_CHARACTER, "fore:#80C080,size:10,back:#303030")
        self.text_ctrl.StyleSetSpec(stc.STC_P_OPERATOR, "fore:#FF8080,size:10,back:#303030")
        self.text_ctrl.StyleSetSpec(stc.STC_P_WORD, "fore:#C080FF,bold,size:10,back:#303030")
        self.text_ctrl.StyleSetSpec(stc.STC_P_WORD2, "fore:#C080FF,back:#303030,bold,size:10")
        self.text_ctrl.StyleSetSpec(stc.STC_P_TRIPLE, "fore:#FFC080,back:#303030,size:10")
        self.text_ctrl.StyleSetSpec(stc.STC_P_TRIPLEDOUBLE, "fore:#FFC080,back:#303030,size:10")
        self.text_ctrl.StyleSetSpec(stc.STC_P_CLASSNAME, "fore:#C080FF,back:#303030,bold,underline,size:10")
        self.text_ctrl.StyleSetSpec(stc.STC_P_DEFNAME, "fore:#FFFFFF,back:#303030,bold,size:10")
        self.text_ctrl.StyleSetSpec(stc.STC_P_IDENTIFIER, "fore:#FFFFFF,back:#303030,size:10")

        self.apply_python_syntax_dark()
        self.apply_java_syntax_dark()

    def apply_light_theme(self):
        self.dark_theme = False
        self.text_ctrl.StyleSetBackground(stc.STC_STYLE_DEFAULT, wx.Colour(255, 255, 255))
        self.text_ctrl.StyleSetBackground(stc.STC_STYLE_LINENUMBER, wx.Colour(240, 240, 240))
        self.text_ctrl.StyleSetBackground(stc.STC_STYLE_INDENTGUIDE, wx.Colour(240, 240, 240))
        self.text_ctrl.StyleSetSpec(stc.STC_P_DEFAULT, "fore:#000000,back:#FFFFFF,face:Courier New,size:10")
        self.text_ctrl.StyleSetSpec(stc.STC_P_WORD,
                                    "fore:#C080FF,bold,size:10,back:#FFFFFF")
        self.text_ctrl.StyleSetForeground(stc.STC_STYLE_LINENUMBER, wx.Colour(0, 0, 0))

        self.text_ctrl.StyleSetSpec(stc.STC_P_IDENTIFIER, "fore:#000000,back:#FFFFFF,size:10")
        self.text_ctrl.StyleSetSpec(stc.STC_P_DECORATOR, "fore:#800080,back:#FFFFFF,size:10")
        self.text_ctrl.StyleSetSpec(stc.STC_P_NUMBER, "fore:#0000FF,size:10,back:#FFFFFF")
        self.text_ctrl.StyleSetSpec(stc.STC_P_OPERATOR, "fore:#800000,size:10,back:#FFFFFF")
        self.text_ctrl.StyleSetSpec(stc.STC_P_CHARACTER, "fore:#800080,size:10,back:#FFFFFF")
        self.text_ctrl.StyleSetSpec(stc.STC_P_STRINGEOL, "fore:#800080,back:#FFFFFF,size:10")
        self.text_ctrl.StyleSetSpec(stc.STC_P_TRIPLE, "fore:#800080,size:10,back:#FFFFFF")
        self.text_ctrl.StyleSetSpec(stc.STC_P_TRIPLEDOUBLE, "fore:#800080,size:10,back:#FFFFFF")
        self.text_ctrl.StyleSetSpec(stc.STC_P_CLASSNAME, "fore:#0000FF,bold,underline,size:10,back:#FFFFFF")
        self.text_ctrl.StyleSetSpec(stc.STC_P_DEFNAME, "fore:#000000,bold,size:10,back:#FFFFFF")
        self.text_ctrl.StyleSetSpec(stc.STC_P_OPERATOR, "fore:#800000,size:10,back:#FFFFFF")
        self.text_ctrl.StyleSetSpec(stc.STC_P_COMMENTBLOCK, "fore:#008000,size:10,back:#FFFFFF")
        self.text_ctrl.StyleSetSpec(stc.STC_P_COMMENTLINE, "fore:#008000,size:10,back:#FFFFFF")

        self.apply_python_syntax_light()
        self.apply_java_syntax_light()

    def on_toggle_multicursor(self, event):
        self.multicursor_enabled = not self.multicursor_enabled
        self.text_ctrl.SetMultipleSelection(self.multicursor_enabled)
        self.text_ctrl.SetAdditionalSelectionTyping(self.multicursor_enabled)
        self.update_status_bar()

    def on_key_down(self, event):
        keycode = event.GetKeyCode()
        if event.ControlDown() and keycode == ord('S'):  # Save shortcut, you can change this
            self.on_save(event)
        elif event.ControlDown() and keycode == ord('F'): # and this (meni poxyi, mit license)
            self.on_find(event)
        else:
            event.Skip()
    def on_about(self, event):
        dlg = wx.MessageDialog(self,
                               "wxTextEditor\nVersion: 1.1\nAuthor: mqchinee (a.k.a. isaweye)\n\nSource code: https://github.com/isaweye/wx-text-editor",
                               "About", wx.OK)
        dlg.ShowModal()
        dlg.Destroy()

    def on_window_resize(self, event):
        window_size = self.panel.GetSize()
        self.text_ctrl.SetSize(window_size)
        self.text_ctrl.Refresh()

if __name__ == "__main__":
    app = wx.App(False)
    frame = SimpleTextEditor(None, wx.ID_ANY, "wxTextEditor")
    frame.Show()
    app.MainLoop()
