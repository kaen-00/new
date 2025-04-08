import sys, os, re, subprocess, json
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, \
                            QPushButton, QLabel, QPlainTextEdit, QStatusBar, QToolBar, \
                            QVBoxLayout, QAction, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt, QSize, QTimer           
from PyQt5.QtGui import QFontDatabase, QIcon, QKeySequence
from PyQt5.QtPrintSupport import QPrintDialog
from PyQt5.QtWidgets import QDockWidget
from PyQt5.QtCore import QObject, QRunnable, QThreadPool, pyqtSlot
from PyQt5.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QMessageBox, QLineEdit, QLabel
)
from predict_ner import extract_and_append_entities

def update_ner_tags(filename):
        tag = filename.strip()
        tag_entry = f"[[{tag}]]"

        try:
            if os.path.exists("ner_tags.json"):
                with open("ner_tags.json", "r") as f:
                    ner_tags = json.load(f)
            else:
                ner_tags = {}

            if tag_entry not in ner_tags:
                ner_tags[tag_entry] = tag
                with open("ner_tags.json", "w") as f:
                    json.dump(ner_tags, f, indent=4)
                print(f"✅ Added tag: {tag_entry} -> {tag}")
        except Exception as e:
            print(f"❌ Failed to update ner_tags.json: {e}")

class AppDemo(QMainWindow):
    def __init__(self, file_path = None):
        super().__init__()
        self.enable_ner = False
        self.last_processed_text = ""
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

        #4 sentance prediction
        self.previous_sentence_count = 0
        self.threadpool = QThreadPool()
        self.editor.textChanged.connect(self.check_for_new_sentences)
        #

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
        self.link_widget = LinkEditorWidget()
        dock.setWidget(self.link_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

        ###########################################
        self.path = None
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    text = f.read()
                self.path = file_path
                self.editor.setPlainText(text)

                # ✅ Reset sentence count after file is loaded
                self.previous_sentence_count = len(re.findall(r'[.!?](?=\s)', text))
                self.enable_ner = True  # ✅ Enable NER only after loading file

                self.update_title()
            except Exception as e:
                self.dialog_message(str(e))
        else:
            self.enable_ner = True  # ✅ Enable NER only if no file loaded
        ###########################################
        # Refresh link widget every 1 second
        self.link_refresh_timer = QTimer(self)
        self.link_refresh_timer.timeout.connect(self.link_widget.refresh)
        self.link_refresh_timer.start(1000)  # every 1000 milliseconds = 1 second

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
                filename = os.path.splitext(os.path.basename(path))[0]
                update_ner_tags(filename)
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

                filename = os.path.splitext(os.path.basename(self.path))[0]
                update_ner_tags(filename)
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
            except Exception as e:
                self.dialog_message(str(e))
            else:
                self.path = path
                self.update_title()
                filename = os.path.splitext(os.path.basename(self.path))[0]
                update_ner_tags(filename)


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

    def check_for_new_sentences(self):
        if not self.enable_ner:
            return  # 🚫 Skip NER if disabled

        text = self.editor.toPlainText()

        # Count sentence endings using punctuation
        sentence_endings = re.findall(r'[.!?](?=\s)', text)
        current_count = len(sentence_endings)

        if current_count - self.previous_sentence_count >= 4:
            # Get only the new portion of the text
            new_text = text[len(self.last_processed_text):].strip()
            self.last_processed_text = text  # 🔁 Update the checkpoint
            self.previous_sentence_count = current_count

            last_lines = self.get_last_n_lines(new_text, 4)  # 🔍 Extract only new 4 lines
            self.run_ner_in_background(last_lines)

    def get_last_n_lines(self, text, n=4):
        lines = text.strip().splitlines()
        return "\n".join(lines[-n:])
    
    def run_ner_in_background(self, text):
        worker = NERWorker(text, self.handle_ner_results)
        self.threadpool.start(worker)

    def handle_ner_results(self, tags):
        print("✅ NER tags extracted:", tags)
        # Optional: update UI
        #self.tag_view.clear()
        #self.tag_view.addItems(tags)

class LinkEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

    def load_link_aliases(self):
        try:
            with open("ner_tags.json", "r") as f:
                return json.load(f)
        except Exception as e:
            print("Error loading links.json:", e)
            return {}
        
    def save_link_aliases(self):
        try:
            with open("ner_tags.json", "w") as f:
                json.dump(self.link_aliases, f, indent=2)
                print("✅ Updated ner_tags.json")
        except Exception as e:
            print("❌ Error saving ner_tags.json:", e)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)

        # Only trigger on right-click
        if event.button() != Qt.RightButton:
            return

        self.link_aliases = self.load_link_aliases()
        cursor = self.cursorForPosition(event.pos())
        full_text = self.toPlainText()
        click_pos = cursor.position()

        # Match all [[link]] patterns
        for match in re.finditer(r'\[\[([^\[\]]+)\]\]', full_text):
            start, end = match.span()
            if start <= click_pos < end:
                tag = match.group(1).strip()
                print(f"🖱️ Right-clicked on tag: [[{tag}]]")

                filename = self.link_aliases.get(tag)

                if not filename:
                    # 🔧 Create new link entry if it doesn't exist
                    filename = tag  # Keep filename same as tag for now
                    self.link_aliases["[[" +tag+ "]]"] =  filename 
                    self.save_link_aliases()

                self.open_linked_file(filename)
                return

    def open_linked_file(self, filename):
        filename=filename+".txt"
        if not os.path.exists(filename):
            with open(filename, 'w') as f:
                f.write("")  # Create an empty file if it doesn't exist

        subprocess.Popen([sys.executable, sys.argv[0], filename])

class LinkEditorWidget(QWidget):
    def __init__(self, json_path="ner_tags.json"):
        super().__init__()
        self.json_path = json_path

        self.layout = QVBoxLayout(self)
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Alias", "Tag"])
        self.layout.addWidget(self.table)

        # Search bar
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self.filter_rows)  # ✅ Trigger search filter
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        self.layout.addLayout(search_layout)

        self.search_input.textChanged.connect(self.filter_rows)

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
        self.table.setRowCount(0)  # Clear previous rows
        if not os.path.exists(self.json_path):
            return
        try:
            with open(self.json_path, "r") as f:
                data = json.load(f)
            for alias, filename in data.items():
                self.add_row(alias, filename)
        except Exception as e:
            print("Error loading JSON:", e)

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

    def filter_rows(self):
        text = self.search_input.text().lower()
        for row in range(self.table.rowCount()):
            alias_item = self.table.item(row, 0)
            filename_item = self.table.item(row, 1)

            alias = alias_item.text().lower() if alias_item else ''
            filename = filename_item.text().lower() if filename_item else ''

            match = text in alias or text in filename
            self.table.setRowHidden(row, not match)

    def refresh(self):
        self.load_json()
        self.filter_rows()

def handle_ner_extraction(self, text):
    tags = extract_and_append_entities(text)

    print("✅ Tags extracted from text:")
    print(tags)

    # Optional: update the dock widget or UI with tags
    self.tag_view.clear()
    self.tag_view.addItems(tags)

class NERWorker(QRunnable):
    def __init__(self, text, callback):
        super().__init__()
        self.text = text
        self.callback = callback

    @pyqtSlot()
    def run(self):
        print("🧠 NER extraction starting with text:", repr(self.text))
        tags = extract_and_append_entities(self.text)
        self.callback(tags)


app = QApplication(sys.argv)
file_path = sys.argv[1] if len(sys.argv) > 1 else None
notePade = AppDemo(file_path)
notePade.show()
sys.exit(app.exec_())