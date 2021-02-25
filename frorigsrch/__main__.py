import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from mne_pipeline_hd.gui.gui_utils import StdoutStderrStream
from mne_pipeline_hd.pipeline_functions import ismac

from frorigsrch.gui import MainWindow


def main():
    app_name = 'french-word-searcher'
    organization_name = 'marsipu'

    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    app.setApplicationName(app_name)
    app.setOrganizationName(organization_name)

    try:
        app.setAttribute(Qt.AA_DisableWindowContextHelpButton, True)
    except AttributeError:
        print('pyqt-Version is < 5.12')

    if ismac:
        app.setAttribute(Qt.AA_DontShowIconsInMenus, True)
        # Workaround for MAC menu-bar-focusing issue
        app.setAttribute(Qt.AA_DontUseNativeMenuBar, True)
        # Workaround for not showing with PyQt < 5.15.2
        os.environ['QT_MAC_WANTS_LAYER'] = '1'

    mw = MainWindow()
    mw.show()

    sys.exit(app.exec())

if __name__ == '__main__':
    main()
