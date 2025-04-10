import os
import sys
import re
import json
import subprocess

from PyQt5.QtCore import Qt, QSize, QTimer, QObject, QRunnable, QThreadPool, pyqtSlot
from PyQt5.QtGui import QFontDatabase, QIcon, QKeySequence, QTextCursor
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPlainTextEdit,
    QPushButton, QLabel, QStatusBar, QToolBar, QAction,
    QFileDialog, QMessageBox, QDockWidget, QHBoxLayout, QLineEdit,
    QTableWidget, QTableWidgetItem
)

from predict_ner import extract_and_append_entities
from string_to_tag_matching import find_and_replace_tags

# If a tag is deleted, then subsequent text-tag detections should remove [[]] from deleted tags
# Change the implementation of 'refresh tags' button so that tags are auto updated every time 'ner_tags.json' changes
# Change how 'extract_and_append_entities' and 'find_and_replace_tags' are triggered. 4 sentences triggering seems inconsistent
# Implement a graph view of the tags

def update_ner_tags(filename):
    tag_entry = f"[[{filename.strip()}]]"
    try:
        ner_tags = {}
        if os.path.exists("ner_tags.json"):
            with open("ner_tags.json", "r") as f:
                ner_tags = json.load(f)
        if tag_entry not in ner_tags:
            ner_tags[tag_entry] = filename.strip()
            with open("ner_tags.json", "w") as f:
                json.dump(ner_tags, f, indent=4)
            print(f"✅ Added tag: {tag_entry}")
    except Exception as e:
        print(f"❌ Failed to update ner_tags.json: {e}")


class AppDemo(QMainWindow):
    def __init__(self, file_path=None):
        super().__init__()
        self.setWindowIcon(QIcon('./Icons/notepad.ico'))
        self.setWindowTitle("NotepadX")

        self.enable_ner = False
        self.path = None
        self.last_processed_text = ""
        self.previous_sentence_count = 0
        self.threadpool = QThreadPool()
        self.filterTypes = 'Text Document (*.txt);; Python (*.py);; Markdown (*.md)'

        # Font
        fixedFont = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        fixedFont.setPointSize(12)

        # Editor
        self.editor = LinkEditor()
        self.editor.setFont(fixedFont)
        self.editor.textChanged.connect(self.check_for_new_sentences)

        # Layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.editor)
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Status Bar
        self.statusBar()

        # Toolbars and Menus
        self.init_menus_and_toolbars()

        # Dock Widget (NER Tag Editor)
        self.link_widget = LinkEditorWidget()
        dock = QDockWidget("Tools", self)
        dock.setWidget(self.link_widget)
        dock.setAllowedAreas(Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

        #ui
        self.refresh_button = QPushButton("Refresh Tags")
        self.refresh_button.clicked.connect(self.link_widget.refresh)
        main_layout.addWidget(self.refresh_button)

        # Load file if passed
        if file_path:
            self.load_file(file_path)
        else:
            self.enable_ner = True

    def init_menus_and_toolbars(self):
        # File Menu/Toolbar
        file_menu = self.menuBar().addMenu('&File')
        file_toolbar = QToolBar('File')
        file_toolbar.setIconSize(QSize(60, 60))
        self.addToolBar(Qt.BottomToolBarArea, file_toolbar)

        open_action = self.create_action('./Icons/file_open.ico', 'Open File...', 'Open file', self.file_open)
        open_action.setShortcut(QKeySequence.Open)
        save_action = self.create_action('./Icons/save_file.ico', 'Save File', 'Save file', self.file_save)
        save_action.setShortcut(QKeySequence.Save)

        file_menu.addActions([open_action, save_action])
        file_toolbar.addActions([open_action, save_action])

        # Edit Menu/Toolbar
        edit_menu = self.menuBar().addMenu('&Edit')
        edit_toolbar = QToolBar('Edit')
        edit_toolbar.setIconSize(QSize(60, 60))
        self.addToolBar(Qt.BottomToolBarArea, edit_toolbar)

        undo_action = self.create_action('./Icons/undo.ico', 'Undo', 'Undo', self.editor.undo)
        undo_action.setShortcut(QKeySequence.Undo)
        redo_action = self.create_action('./Icons/redo.ico', 'Redo', 'Redo', self.editor.redo)
        redo_action.setShortcut(QKeySequence.Redo)

        edit_menu.addActions([undo_action, redo_action])
        edit_menu.addSeparator()
        edit_toolbar.addActions([undo_action, redo_action])
        edit_toolbar.addSeparator()

    def create_action(self, icon_path, name, tip, method):
        action = QAction(QIcon(icon_path), name, self)
        action.setStatusTip(tip)
        action.triggered.connect(method)
        return action

    def file_open(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Open file', '', self.filterTypes)
        if path:
            filename = os.path.splitext(os.path.basename(path))[0]
            update_ner_tags(filename)
            subprocess.Popen([sys.executable, sys.argv[0], path])

    def file_save(self):
        if self.path is None:
            self.file_saveAs()
        else:
            try:
                with open(self.path, 'w') as f:
                    f.write(self.editor.toPlainText())
                update_ner_tags(os.path.splitext(os.path.basename(self.path))[0])
            except Exception as e:
                self.dialog_message(str(e))

    def file_saveAs(self):
        path, _ = QFileDialog.getSaveFileName(self, 'Save file as', '', self.filterTypes)
        if path:
            try:
                with open(path, 'w') as f:
                    f.write(self.editor.toPlainText())
                self.path = path
                update_ner_tags(os.path.splitext(os.path.basename(path))[0])
                self.update_title()
            except Exception as e:
                self.dialog_message(str(e))

    def load_file(self, file_path):
        try:
            with open(file_path, 'r') as f:
                text = f.read()
            self.editor.setPlainText(text)
            self.path = file_path
            self.previous_sentence_count = len(re.findall(r'[.!?](?=\s)', text))
            self.enable_ner = True
            self.update_title()
        except Exception as e:
            self.dialog_message(str(e))

    def update_title(self):
        name = os.path.basename(self.path) if self.path else "Untitled"
        self.setWindowTitle(f"{name} - NotepadX")

    def dialog_message(self, message):
        QMessageBox.critical(self, "Error", message)

    def check_for_new_sentences(self):
        if not self.enable_ner:
            return
        text = self.editor.toPlainText()
        sentence_endings = re.findall(r'[.!?](?=\s)', text)
        current_count = len(sentence_endings)

        if current_count - self.previous_sentence_count >= 4:
            self.editor.blockSignals(True)
            new_text = text[len(self.last_processed_text):].strip()
            self.last_processed_text = text
            self.previous_sentence_count = current_count
            last_lines = self.get_last_n_lines(new_text, 4)
            self.run_ner_in_background(last_lines)
            self.link_widget.refresh
            updated_text = find_and_replace_tags(text, "ner_tags.json")
            self.editor.blockSignals(True)
            self.editor.setPlainText(updated_text)
            self.editor.blockSignals(False)
            cursor = self.editor.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.editor.setTextCursor(cursor)

    def get_last_n_lines(self, text, n=4):
        return "\n".join(text.strip().splitlines()[-n:])

    def run_ner_in_background(self, text):
        worker = NERWorker(text, self.handle_ner_results)
        self.threadpool.start(worker)

    def handle_ner_results(self, tags):
        print("✅ NER tags extracted:", tags)


class LinkEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if event.button() != Qt.RightButton:
            return
        cursor = self.cursorForPosition(event.pos())
        pos = cursor.position()
        text = self.toPlainText()

        for match in re.finditer(r'\[\[([^\[\]]+)\]\]', text):
            if match.start() <= pos < match.end():
                tag = match.group(1).strip()
                print(f"🖱️ Right-clicked on tag: [[{tag}]]")
                self.open_link(tag)
                break

    def open_link(self, tag):
        try:
            with open("ner_tags.json", "r") as f:
                tags = json.load(f)
        except Exception:
            tags = {}

        filename = tags.get(tag)
        if not filename:
            filename = tag
            tags[f"[[{tag}]]"] = filename
            with open("ner_tags.json", "w") as f:
                json.dump(tags, f, indent=2)

        full_path = f"{filename}.txt"
        if not os.path.exists(full_path):
            with open(full_path, 'w') as f:
                f.write("")
        subprocess.Popen([sys.executable, sys.argv[0], full_path])


class LinkEditorWidget(QWidget):
    def __init__(self, json_path="ner_tags.json"):
        super().__init__()
        self.json_path = json_path
        self.layout = QVBoxLayout(self)

        # Table
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Alias", "Tag"])
        self.layout.addWidget(self.table)

        # Search bar
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self.filter_rows)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        self.layout.addLayout(search_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Add")
        self.btn_delete = QPushButton("Delete")
        self.btn_save = QPushButton("Save")
        for btn in (self.btn_add, self.btn_delete, self.btn_save):
            btn_layout.addWidget(btn)
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
                for alias, tag in json.load(f).items():
                    self.add_row(alias, tag)
        except Exception as e:
            print("Error loading JSON:", e)

    def save_json(self):
        data = {}
        for row in range(self.table.rowCount()):
            alias = self.table.item(row, 0).text().strip()
            tag = self.table.item(row, 1).text().strip()
            if alias and tag:
                data[alias] = tag
        try:
            with open(self.json_path, "w") as f:
                json.dump(data, f, indent=2)
            QMessageBox.information(self, "Saved", "Links saved successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save: {e}")

    def add_row(self, alias='', tag=''):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(alias))
        self.table.setItem(row, 1, QTableWidgetItem(tag))

    def delete_selected(self):
        for index in sorted(self.table.selectionModel().selectedRows(), reverse=True):
            self.table.removeRow(index.row())

    def filter_rows(self):
        query = self.search_input.text().lower()
        for row in range(self.table.rowCount()):
            alias = self.table.item(row, 0).text().lower()
            tag = self.table.item(row, 1).text().lower()
            self.table.setRowHidden(row, query not in alias and query not in tag)

    def refresh(self):
        self.load_json()
        self.filter_rows()


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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    file_path = sys.argv[1] if len(sys.argv) > 1 else None
    window = AppDemo(file_path)
    window.show()
    sys.exit(app.exec_())
