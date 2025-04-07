import sys, os, re, subprocess, json
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, \
                            QPushButton, QLabel, QPlainTextEdit, QStatusBar, QToolBar, \
                            QVBoxLayout, QAction, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt, QSize                          
from PyQt5.QtGui import QFontDatabase, QIcon, QKeySequence
from PyQt5.QtPrintSupport import QPrintDialog
from PyQt5.QtWidgets import QDockWidget

from PyQt5.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QMessageBox
)

class AppDemo(QMainWindow):
    def __init__(self, file_path = None):
        super().__init__()

        self.setWindowIcon(QIcon('./Icons/notepad.ico'))
        self.screen_width, self.screen_height = self.geometry().width(), self.geometry().height()
        self.resize(self.screen_width * 2, self.screen_height * 2) 

        self.filterTypes = 'Text Document (*.txt);; Python (*.py);; Markdown (*.md)'

        self.path = None

        fixedFont = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        fixedFont.setPointSize(12)

        mainLayout = QVBoxLayout()

        # editor
        self.editor = LinkEditor()
        self.setCentralWidget(self.editor)
        self.editor.setFont(fixedFont)
        mainLayout.addWidget(self.editor)

        # stautsBar
        self.statusBar = self.statusBar()

        # app container
        container = QWidget()
        container.setLayout(mainLayout)
        self.setCentralWidget(container)

        #----------------------------------
        # File Menu
        #----------------------------------
        file_menu = self.menuBar().addMenu('&File')

        #----------------------------------
        # File ToolBar
        #----------------------------------
        file_toolbar = QToolBar('File')
        file_toolbar.setIconSize(QSize(60, 60))
        self.addToolBar(Qt.BottomToolBarArea, file_toolbar)

        """
        open, save
        """
        open_file_action = QAction(QIcon('./Icons/file_open.ico'), 'Open File...', self)
        open_file_action.setStatusTip('Open file')
        open_file_action.setShortcut(QKeySequence.Open)
        open_file_action.triggered.connect(self.file_open) #TODO

        save_file_action = self.create_action(self, './Icons/save_file.ico', 'Save File', 'Save file', self.file_save)
        save_file_action.setShortcut(QKeySequence.Save)

        file_menu.addActions([open_file_action, save_file_action])
        file_toolbar.addActions([open_file_action, save_file_action])


        #----------------------------------
        # Edit Menu
        #----------------------------------
        edit_menu = self.menuBar().addMenu('&Edit')

        #----------------------------------
        # Edit ToolBar
        #----------------------------------
        edit_toolbar =QToolBar('Edit')
        edit_toolbar.setIconSize(QSize(60, 60))
        self.addToolBar(Qt.BottomToolBarArea, edit_toolbar)

        # Undo, Redo Actions
        undo_action = self.create_action(self, './Icons/undo.ico', 'Undo', 'Undo', self.editor.undo)
        undo_action.setShortcut(QKeySequence.Undo)

        redo_action = self.create_action(self, './Icons/redo.ico', 'Redo', 'Redo', self.editor.redo)
        redo_action.setShortcut(QKeySequence.Redo)

        edit_menu.addActions([undo_action, redo_action])
        edit_toolbar.addActions([undo_action, redo_action])

        # add separator
        edit_menu.addSeparator()
        edit_toolbar.addSeparator()

        # Dockable right panel
        dock = QDockWidget("Tools", self)
        dock.setAllowedAreas(Qt.RightDockWidgetArea)
        dock.setWidget(LinkEditorWidget())
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

        ###########################################
        self.path = None
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    text = f.read()
                self.path = file_path
                self.editor.setPlainText(text)
                self.update_title()
            except Exception as e:
                self.dialog_message(str(e))
        ###########################################

    def insert_link(self, filename):
        cursor = self.editor.textCursor()
        cursor.insertText(f"[[{filename}]]")

    def file_open(self):
        path, _ = QFileDialog.getOpenFileName(
            parent=self,
            caption='Open file',
            directory='',
            filter=self.filterTypes
        )

        if path:
            try:
                # Launch a new instance of the current script with the file path
                subprocess.Popen([sys.executable, sys.argv[0], path])
            except Exception as e:
                self.dialog_message(str(e))

    def file_save(self):
        if self.path is None:
            self.file_saveAs()
        else:
            try:
                text = self.editor.toPlainText()
                with open(self.path, 'w') as f:
                    f.write(text)
                    f.close()
            except Exception as e:  
                self.dialog_message(str(e))

    def file_saveAs(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            'Save file as',
            '',
            self.filterTypes
        )                               

        text = self.editor.toPlainText()

        if not path:
            return
        else:
            try:
                with open(path, 'w') as f:
                    f.write(text)
                    f.close()
            except Exception as e:
                self.dialog_message(str(e))
            else:
                self.path = path
                self.update_title()
    
    def update_title(self):
        print(f"Updating title with path: {self.path}")
        self.setWindowTitle('{0} - NotepadX'.format(os.path.basename(self.path) if self.path else 'Unititled'))

    def dialog_message(self, message):
        dlg = QMessageBox(self)
        dlg.setText(message)
        dlg.setIcon(QMessageBox.Critical)
        dlg.show()

    def create_action(self, parent, icon_path, action_name, set_status_tip, triggered_method)   :
        action = QAction(QIcon(icon_path), action_name, parent)
        action.setStatusTip(set_status_tip)
        action.triggered.connect(triggered_method)
        return action
    
    def dialog_message(self, msg):
        # Show error messages here (e.g., QMessageBox)
        print(msg)


class LinkEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

    def load_link_aliases(self):
        try:
            with open("links.json", "r") as f:
                return json.load(f)
        except Exception as e:
            print("Error loading links.json:", e)
            return {}
        
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.link_aliases = self.load_link_aliases()
        cursor = self.cursorForPosition(event.pos())
        full_text = self.toPlainText()
        click_pos = cursor.position()

        for alias, filename in self.link_aliases.items():
            for match in re.finditer(re.escape(alias), full_text):
                start, end = match.span()
                if start <= click_pos < end:
                    print(f"Clicked link: {alias} -> {filename}")
                    self.open_linked_file(filename + ".txt")
                    return

    def open_linked_file(self, filename):
        if not os.path.exists(filename):
            with open(filename, 'w') as f:
                f.write("")  # Create an empty file if it doesn't exist

        subprocess.Popen([sys.executable, sys.argv[0], filename])

class LinkEditorWidget(QWidget):
    def __init__(self, json_path="links.json"):
        super().__init__()
        self.json_path = json_path

        self.layout = QVBoxLayout(self)
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Alias", "Tag"])
        self.layout.addWidget(self.table)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Add")
        self.btn_delete = QPushButton("Delete")
        self.btn_save = QPushButton("Save")

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addWidget(self.btn_save)
        self.layout.addLayout(btn_layout)

        self.btn_add.clicked.connect(self.add_row)
        self.btn_delete.clicked.connect(self.delete_selected)
        self.btn_save.clicked.connect(self.save_json)

        self.load_json()

    def load_json(self):
        self.table.setRowCount(0)
        if not os.path.exists(self.json_path):
            return
        try:
            with open(self.json_path, "r") as f:
                data = json.load(f)
            for alias, filename in data.items():
                self.add_row(alias, filename)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load JSON: {e}")

    def save_json(self):
        data = {}
        for row in range(self.table.rowCount()):
            alias_item = self.table.item(row, 0)
            file_item = self.table.item(row, 1)
            if alias_item and file_item:
                alias = alias_item.text().strip()
                filename = file_item.text().strip()
                if alias and filename:
                    data[alias] = filename
        try:
            with open(self.json_path, "w") as f:
                json.dump(data, f, indent=2)
            QMessageBox.information(self, "Saved", "Links saved successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save: {e}")

    def add_row(self, alias='', filename=''):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(alias))
        self.table.setItem(row, 1, QTableWidgetItem(filename))

    def delete_selected(self):
        selected = self.table.selectionModel().selectedRows()
        for index in sorted(selected, reverse=True):
            self.table.removeRow(index.row())

app = QApplication(sys.argv)
file_path = sys.argv[1] if len(sys.argv) > 1 else None
notePade = AppDemo(file_path)
notePade.show()
sys.exit(app.exec_())