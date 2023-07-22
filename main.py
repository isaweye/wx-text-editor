import wx
import wx.stc as stc
import os
import sys

STYLES = {
    "default": "fore:#000000,back:#FFFFFF,face:Courier New,size:10"
}

class SimpleTextEditor(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, size=(800, 600))

        self.panel = wx.Panel(self)
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

        # File Menu
        file_menu = wx.Menu()
        file_menu.Append(wx.ID_OPEN, "Open")
        file_menu.Append(wx.ID_SAVE, "Save")
        file_menu.Append(wx.ID_SAVEAS, "Save As")
        file_menu.AppendSeparator()
        file_menu.Append(wx.ID_EXIT, "Exit")
        menu_bar.Append(file_menu, "File")

        # View Menu
        view_menu = wx.Menu()
        theme_menu = wx.Menu()
        theme_menu.Append(10001, "Light Theme")
        theme_menu.Append(10002, "Dark Theme")
        view_menu.AppendSubMenu(theme_menu, "Theme")
        view_menu.Append(10003, "Multicursor")
        menu_bar.Append(view_menu, "View and Tools")

        # About Menu
        about_menu = wx.Menu()
        about_menu.Append(10004, "About")
        menu_bar.Append(about_menu, "About")

        self.SetMenuBar(menu_bar)

        # Bind Events
        self.Bind(wx.EVT_MENU, self.on_open, id=wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self.on_save, id=wx.ID_SAVE)
        self.Bind(wx.EVT_MENU, self.on_save_as, id=wx.ID_SAVEAS)
        self.Bind(wx.EVT_MENU, self.on_exit, id=wx.ID_EXIT)
        self.Bind(wx.EVT_MENU, self.on_theme_change, id=10001)
        self.Bind(wx.EVT_MENU, self.on_theme_change, id=10002)
        self.Bind(wx.EVT_MENU, self.on_toggle_multicursor, id=10003)
        self.Bind(wx.EVT_MENU, self.on_about, id=10004)

    def create_status_bar(self):
        self.statusbar = self.CreateStatusBar(3)
        self.update_status_bar()

    def on_window_resize(self, event):
        window_size = self.panel.GetSize()
        self.text_ctrl.SetSize(window_size)
        self.text_ctrl.Refresh()

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

        self.text_ctrl.SetLexer(stc.STC_LEX_PYTHON)
        self.text_ctrl.StyleSetSpec(stc.STC_STYLE_DEFAULT, STYLES["default"])
        self.text_ctrl.StyleClearAll()

        self.text_ctrl.Bind(wx.EVT_CHAR, self.on_char)

        self.text_ctrl.Bind(wx.stc.EVT_STC_UPDATEUI, self.on_update_ui)

    def on_open(self, event):
        openFileDialog = wx.FileDialog(self, "Open File", "", "", "All files (*.*)|*.*", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if openFileDialog.ShowModal() == wx.ID_CANCEL:
            return
        file_path = openFileDialog.GetPath()

        with open(file_path, "r") as file:
            content = file.read()

        self.text_ctrl.SetValue(content)
        self.current_file_path = file_path
        self.file_modified = False  # Reset file_modified after opening a file
        self.update_window_title()
        
    def open_arg(self, path):
        with open(path, "r") as file:
            content = file.read()

        self.text_ctrl.SetValue(content)
        self.current_file_path = path
        self.file_modified = False  # Reset file_modified after opening a file
        self.update_window_title()

    def on_save(self, event):
        if not self.current_file_path:
            self.on_save_as(event)
            return

        with open(self.current_file_path, "w") as file:
            file.write(self.text_ctrl.GetValue())

        self.file_modified = False  # Reset file_modified after successful save
        self.update_window_title()

    def on_save_as(self, event):
        saveFileDialog = wx.FileDialog(self, "Save File", "", "", "All files (*.*)|*.*", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if saveFileDialog.ShowModal() == wx.ID_CANCEL:
            return
        file_path = saveFileDialog.GetPath()

        with open(file_path, "w") as file:
            file.write(self.text_ctrl.GetValue())

        self.current_file_path = file_path
        self.file_modified = False  # Reset file_modified after successful save
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
        self.statusbar.SetStatusText("Multicursor: Disabled" if not self.multicursor_enabled else "Multicursor: Enabled", 2)

    def on_theme_change(self, event):
        theme = event.GetId()
        if theme == 10001:
            self.apply_light_theme()
        elif theme == 10002:
            self.apply_dark_theme()

    def apply_light_theme(self):
        self.text_ctrl.StyleSetBackground(stc.STC_STYLE_DEFAULT, wx.Colour(255, 255, 255))
        self.text_ctrl.StyleSetBackground(stc.STC_STYLE_LINENUMBER, wx.Colour(240, 240, 240))
        self.text_ctrl.StyleSetBackground(stc.STC_STYLE_INDENTGUIDE, wx.Colour(240, 240, 240))
        self.text_ctrl.StyleSetSpec(stc.STC_P_DEFAULT, "fore:#000000,back:#FFFFFF,face:Courier New,size:10")

        self.text_ctrl.StyleSetSpec(stc.STC_P_IDENTIFIER, "fore:#000000,back:#FFFFFF,size:10")
        self.text_ctrl.StyleSetSpec(stc.STC_P_DECORATOR, "fore:#800080,back:#FFFFFF,size:10")
        self.text_ctrl.StyleSetSpec(stc.STC_P_NUMBER, "fore:#0000FF,size:10,back:#FFFFFF")
        self.text_ctrl.StyleSetSpec(stc.STC_P_OPERATOR, "fore:#800000,size:10,back:#FFFFFF")
        self.text_ctrl.StyleSetSpec(stc.STC_P_CHARACTER, "fore:#800080,size:10,back:#FFFFFF")
        self.text_ctrl.StyleSetSpec(stc.STC_P_STRINGEOL, "fore:#800080,back:#FFFFFF,size:10")
        self.text_ctrl.StyleSetSpec(stc.STC_P_UUID, "fore:#800080,back:#FFFFFF,size:10")
        self.text_ctrl.StyleSetSpec(stc.STC_P_TRIPLE, "fore:#800080,size:10,back:#FFFFFF")
        self.text_ctrl.StyleSetSpec(stc.STC_P_TRIPLEDOUBLE, "fore:#800080,size:10,back:#FFFFFF")
        self.text_ctrl.StyleSetSpec(stc.STC_P_CLASSNAME, "fore:#0000FF,bold,underline,size:10,back:#FFFFFF")
        self.text_ctrl.StyleSetSpec(stc.STC_P_DEFNAME, "fore:#000000,bold,size:10,back:#FFFFFF")
        self.text_ctrl.StyleSetSpec(stc.STC_P_OPERATOR, "fore:#800000,size:10,back:#FFFFFF")
        self.text_ctrl.StyleSetSpec(stc.STC_P_COMMENTBLOCK, "fore:#008000,size:10,back:#FFFFFF")
        self.text_ctrl.StyleSetSpec(stc.STC_P_COMMENTLINE, "fore:#008000,size:10,back:#FFFFFF")
        self.text_ctrl.StyleSetSpec(stc.STC_P_COMMENTLINEDOC, "fore:#008000,size:10,back:#FFFFFF")
        
    def apply_dark_theme(self):
        self.text_ctrl.StyleSetBackground(stc.STC_STYLE_DEFAULT, wx.Colour(48, 48, 48))
        self.text_ctrl.StyleSetBackground(stc.STC_STYLE_LINENUMBER, wx.Colour(32, 32, 32))
        self.text_ctrl.StyleSetBackground(stc.STC_STYLE_INDENTGUIDE, wx.Colour(240, 240, 240))
        self.text_ctrl.StyleSetSpec(stc.STC_P_DEFAULT, "fore:#FFFFFF,back:#303030,face:Courier New,size:10")
        self.text_ctrl.StyleSetSpec(stc.STC_P_COMMENTLINE, "fore:#70A0C0,size:10")
        self.text_ctrl.StyleSetSpec(stc.STC_P_NUMBER, "fore:#FF8080,size:10,back:#303030")
        self.text_ctrl.StyleSetSpec(stc.STC_P_STRING, "fore:#80C080,size:10,back:#303030")
        self.text_ctrl.StyleSetSpec(stc.STC_P_CHARACTER, "fore:#80C080,size:10,back:#303030")
        self.text_ctrl.StyleSetSpec(stc.STC_P_OPERATOR, "fore:#FF8080,size:10,back:#303030")
        self.text_ctrl.StyleSetSpec(stc.STC_P_WORD, "fore:#C080FF,bold,size:10,back:#303030")
        self.text_ctrl.StyleSetSpec(stc.STC_P_WORD2, "fore:#C080FF,bold,size:10")
        self.text_ctrl.StyleSetSpec(stc.STC_P_TRIPLE, "fore:#FFC080,size:10")
        self.text_ctrl.StyleSetSpec(stc.STC_P_TRIPLEDOUBLE, "fore:#FFC080,size:10")
        self.text_ctrl.StyleSetSpec(stc.STC_P_CLASSNAME, "fore:#C080FF,bold,underline,size:10")
        self.text_ctrl.StyleSetSpec(stc.STC_P_DEFNAME, "fore:#FFFFFF,bold,size:10")
        self.text_ctrl.StyleSetSpec(stc.STC_P_IDENTIFIER, "fore:#FFFFFF,back:#303030,size:10")

    def on_toggle_multicursor(self, event):
        self.multicursor_enabled = not self.multicursor_enabled
        self.text_ctrl.SetMultipleSelection(self.multicursor_enabled)
        self.text_ctrl.SetAdditionalSelectionTyping(self.multicursor_enabled)
        self.update_status_bar()

    def on_key_down(self, event):
        if event.ControlDown() and event.GetKeyCode() == ord('S'):
            self.on_save(event)
        else:
            event.Skip()

    def on_about(self, event):
        dlg = wx.MessageDialog(self, "wxTextEditor\nAuthor: mqchinee (a.k.a. isaweye)\n\nSource code: https://github.com/isaweye/wx-text-editor", "About", wx.OK)
        dlg.ShowModal()
        dlg.Destroy()

if __name__ == "__main__":
    app = wx.App()
    frame = SimpleTextEditor(None, -1, "wxTextEditor")
    frame.Show()
    app.MainLoop()

