import json
import re
from copy import deepcopy

import pandas as pd
from PyQt5.QtCore import QThreadPool
from PyQt5.QtWidgets import QAction, QDialog, QFileDialog, QHBoxLayout, QInputDialog, QLabel, QMainWindow, QMessageBox, \
    QProgressBar, \
    QPushButton, \
    QVBoxLayout, QWidget
from mne_pipeline_hd.gui.base_widgets import EditList, SimpleDict, SimplePandasTable
from mne_pipeline_hd.gui.gui_utils import Worker, center, set_ratio_geometry

from french_origin_searcher import get_word_origin


class SearchPatternDlg(QDialog):
    def __init__(self, mw):
        super().__init__(mw)
        self.mw = mw

        self.init_ui()
        self.open()

    def init_ui(self):
        layout = QVBoxLayout()
        list_w = EditList(self.mw.search_patterns)
        layout.addWidget(list_w)
        self.setLayout(layout)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('French-Word-Searcher')

        self.line_dict = dict()
        self.search_website = 'https://www.oed.com'
        self.search_patterns = [
            'Origin:.{,500}[Ff]{1}rench',
            'Etymology:.{,500}[Ff]{1}rench',
            'Etymons:.{,500}[Ff]{1}rench'
        ]
        self.all_words = list()
        self.word_counts = dict()
        self.results_pd = pd.DataFrame([], columns=['Line Number', 'Count', 'Translation', 'Origin'])
        self.pg_cnt = 0
        self.worker = None

        self.setCentralWidget(QWidget())
        self.main_layout = QVBoxLayout()
        self.centralWidget().setLayout(self.main_layout)

        self.init_ui()
        self.init_menu()

        set_ratio_geometry(0.5, self)
        center(self)

    def init_menu(self):
        load_menu = self.menuBar().addMenu('&Load')
        load_menu.addAction('&Load File', self.load_file)
        load_menu.addAction('&Load Search-Patterns', self.load_search_patterns)

        save_menu = self.menuBar().addMenu('&Save')
        save_menu.addAction('&Save Results', self.save_results)
        save_menu.addAction('&Save Search-Patterns', self.save_search_patterns)

        settings_menu = self.menuBar().addMenu('&Settings')
        # settings_menu.addAction('Change Search-Website', self.change_search_website)
        settings_menu.addAction('Change Search-Patterns', self.change_search_patterns)

        self.show_not_found = QAction('Show not-Found')
        self.show_not_found.setCheckable(True)
        self.show_not_found.setChecked(True)
        settings_menu.addAction(self.show_not_found)

        self.save_not_found = QAction('Save not-Found')
        self.save_not_found.setCheckable(True)
        self.show_not_found.setChecked(False)
        settings_menu.addAction(self.save_not_found)

    def init_ui(self):
        viewer_layout = QHBoxLayout()
        self.line_viewer = SimpleDict(data=self.line_dict, title='Loaded Lines', resize_columns=True)
        viewer_layout.addWidget(self.line_viewer)

        self.results_viewer = SimplePandasTable(data=self.results_pd, title='Results', resize_columns=True)
        viewer_layout.addWidget(self.results_viewer)
        self.main_layout.addLayout(viewer_layout)

        self.pg_label = QLabel()
        self.main_layout.addWidget(self.pg_label)
        self.pgbar = QProgressBar()
        self.main_layout.addWidget(self.pgbar)

        bt_layout = QHBoxLayout()
        self.find_fr_bt = QPushButton('Find french origin')
        self.find_fr_bt.clicked.connect(self.find_french_words)
        bt_layout.addWidget(self.find_fr_bt)

        self.stop_bt = QPushButton('Stop')
        self.stop_bt.clicked.connect(self.stop)
        bt_layout.addWidget(self.stop_bt)

        clear_results_bt = QPushButton('Clear Results')
        clear_results_bt.clicked.connect(self.clear_results)
        bt_layout.addWidget(clear_results_bt)

        close_bt = QPushButton('Close')
        close_bt.clicked.connect(self.close)
        bt_layout.addWidget(close_bt)
        self.main_layout.addLayout(bt_layout)

    def load_file(self):
        file_path = QFileDialog.getOpenFileName(self, 'Select a english text-file', filter='Text-File (*.txt)')[0]
        if file_path:
            self.line_dict.clear()
            self.all_words.clear()
            with open(file_path, 'r') as file:
                lines = file.readlines()
                for line in lines:
                    # Find lines with a line number at start (original line, not translation)
                    line_pattern = r'([0-9]+)[ ]{2,}(.*)'
                    match = re.search(line_pattern, line)
                    if match:
                        # Find words in line
                        word_pattern = r'[a-zA-Z]+'
                        line_number = int(match.group(1))
                        # Return lowercase words
                        word_list = list()
                        for word_match in re.finditer(word_pattern, match.group(2)):
                            word = word_match.group().lower()
                            if word not in self.all_words:
                                word_list.append(word)
                            if word in self.word_counts:
                                self.word_counts[word] += 1
                            else:
                                self.word_counts[word] = 1
                        self.all_words += word_list
                        self.line_dict[line_number] = word_list

            self.line_viewer.content_changed()

    def stop(self):
        if self.worker:
            self.worker.cancel()
            self.pg_label.setText('Stopping...')

    def clear_results(self):
        self.results_pd.drop(self.results_pd.index, inplace=True)
        self.results_viewer.content_changed()

    def update_pgbar(self, n):
        self.pgbar.setValue(n)
        self.line_viewer.content_changed()
        self.results_viewer.content_changed()

    def change_search_website(self):
        result = QInputDialog().getText(self, 'Changing Search-Website',
                                        'Enter the website-url (ending with .com or similar):',
                                        text=self.search_website)[0]
        if result:
            self.search_website = result

    def change_search_patterns(self):
        SearchPatternDlg(self)

    def _find_wd(self, worker_signals):
        self.pg_cnt = 0
        self.pgbar.setMaximum(len(self.all_words))
        iter_dict = deepcopy(self.line_dict)
        for line_number in iter_dict:
            words = iter_dict[line_number]
            for word in words:
                if not worker_signals.was_canceled:
                    worker_signals.pgbar_text.emit(f'Searching origin for "{word}" ...')
                    search_url = f'{self.search_website}/search?searchType=dictionary&q={word}&_searchBtn=Search'
                    result = get_word_origin(search_url, word, self.search_patterns)
                    if result[0] is not None and (result[0] != 'Not found' or self.show_not_found.isChecked()):
                        translation, origin_type = result
                        self.results_pd.loc[word, 'Line Number'] = int(line_number)
                        self.results_pd.loc[word, 'Count'] = self.word_counts[word]
                        self.results_pd.loc[word, 'Translation'] = translation
                        self.results_pd.loc[word, 'Origin'] = origin_type
                    self.line_dict[line_number].remove(word)
                    worker_signals.pgbar_n.emit(self.pg_cnt)
                    self.pg_cnt += 1

            if not worker_signals.was_canceled:
                self.line_dict.pop(line_number)

    def error_happened(self, err):
        QMessageBox.warning(self, 'Oo, something happened', f'{err[0]}-{err[1]}-{err[2]}')
        self.finding_finished()

    def finding_finished(self):
        self.find_fr_bt.setEnabled(True)
        self.stop_bt.setEnabled(False)
        self.pg_label.setText('Finished!')

    def find_french_words(self):
        self.find_fr_bt.setEnabled(False)
        self.stop_bt.setEnabled(True)
        self.worker = Worker(self._find_wd)
        self.worker.signals.pgbar_text.connect(self.pg_label.setText)
        self.worker.signals.pgbar_n.connect(self.update_pgbar)
        self.worker.signals.error.connect(self.error_happened)
        self.worker.signals.finished.connect(self.finding_finished)
        QThreadPool.globalInstance().start(self.worker)

    def load_search_patterns(self):
        file_path = QFileDialog.getOpenFileName(self, 'Select a file to read text from',
                                                filter='JSON-File (*.json)')[0]
        if file_path:
            with open(file_path, 'r') as file:
                self.search_patterns = json.load(file)

    def save_search_patterns(self):
        file_path = QFileDialog.getSaveFileName(self, 'Select a file to save the search-patterns to',
                                                filter='JSON-File (*.json)')[0]
        if file_path:
            with open(file_path, 'w') as file:
                json.dump(self.search_patterns, file, indent=4)

    def save_results(self):
        file_path = QFileDialog.getSaveFileName(self, 'Select a file to save the search-patterns to',
                                                filter='CSV-File (*.csv)')[0]
        if file_path:
            if not self.save_not_found.isChecked():
                save_pd = self.results_pd.loc[self.results_pd['Origin'] != 'Not found']
            else:
                save_pd = self.results_pd
            save_pd.to_csv(file_path, sep=';')
