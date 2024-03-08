import os
import sys
import json
from decimal import Decimal, ROUND_HALF_UP
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QHeaderView, QFileDialog, QMessageBox, QLabel, QLineEdit, QTableWidgetItem, QAbstractItemView, QStyle, QCheckBox, QToolBar, QSizePolicy, QDialog, QPushButton
from PyQt6.QtCore import Qt, QEvent, QCoreApplication, QSettings
from PyQt6.QtGui import QShortcut, QKeySequence, QIcon, QPixmap, QAction

from decimal_table_widget_item import DecimalTableWidgetItem
from decimal_encoder import DecimalEncoder
from add_trade_dialog import AddTradeDialog
from edit_trade_dialog import EditTradeDialog
from change_log import ChangeLog
from datetime import datetime
from confirm_change_dialog import ConfirmChangeDialog
from constants import red, green

CRYPTO_TRADES_TRACKER_VERSION = '1.0.0'
DATA_FILE_VERSION = '1'
SETTINGS_FILE = 'ctt_settings.ini'

UUIDRole = Qt.ItemDataRole.UserRole + 1

# Set the desired precision: 8 decimal places
decimal_places = Decimal('1E-8')


class MainWindow(QMainWindow):
    def __init__(self):
        """
        Initializes the main window of the application, setting its size, icon, and positioning it at the center of the screen. It also initializes the main layout, UI components, loads settings, the last used file, and installs an event filter.
        """
        super().__init__()
        self.setGeometry(0, 0, 1280, 720)  # x, y, width, height
        icon = QIcon()
        icon.addPixmap(QPixmap("../resource/bitcoin.png"), QIcon.Mode.Normal, QIcon.State.Off)
        self.setWindowIcon(icon)
        self.center_window()

        self.full_history_data = []
        self.change_log = ChangeLog()
        self.file_path = ''

        self.update_title()

        # Main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Setup UI components
        self.setup_button_bar()
        self.setup_tables()
        self.setup_shortcuts()

        # Load settings
        self.read_settings()

        # Load last data
        self.load_last_used_file()

        # Install event filter
        self.installEventFilter(self)

    def center_window(self):
        """
        Centers the window on the screen based on the current screen's resolution.
        """
        # Get the screen's resolution
        screen = QApplication.primaryScreen().geometry()
        # Calculate the x and y positions to center the window
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def setup_button_bar(self):
        """
        Configures the toolbar with actions for new file, open, save, save as, add trade, and help, including shortcuts and connections for their respective functionalities.
        """
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        # Actions
        new_action = QAction("New", self)
        load_action = QAction("Open", self)
        save_action = QAction("Save", self)
        save_as_action = QAction("Save As...", self)
        add_trade_action = QAction("Add Trade", self)
        help_action = QAction("?", self)

        # Shortcuts
        new_action.setShortcut(QKeySequence.StandardKey.New)
        load_action.setShortcut(QKeySequence.StandardKey.Open)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_as_action.setShortcut("CTRL+SHIFT+S")
        help_action.setShortcut(QKeySequence.StandardKey.HelpContents)

        # Connect actions
        new_action.triggered.connect(self.new)
        load_action.triggered.connect(lambda: self.load_data(None))
        save_action.triggered.connect(self.save)
        save_as_action.triggered.connect(self.save_as)
        add_trade_action.triggered.connect(self.add_trade)
        help_action.triggered.connect(self.help)

        # Left-aligned actions
        toolbar.addAction(new_action)
        toolbar.addAction(load_action)
        toolbar.addAction(save_action)
        toolbar.addAction(save_as_action)
        toolbar.addAction(add_trade_action)

        # Spacer widget
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        toolbar.addWidget(spacer)

        # Right-aligned actions
        toolbar.addAction(help_action)

    def setup_tables(self):
        """
        Sets up the tables for displaying positions and trade history, including their layout, titles, filters, and clear button functionalities, and integrates them into the main layout of the application.
        """
        # Main container for all tables and their titles
        self.tables_container = QWidget()
        self.tables_layout = QHBoxLayout(self.tables_container)

        # Positions Section
        positions_section = QWidget()
        positions_layout = QVBoxLayout(positions_section)

        # Positions Title
        positions_title = QLabel("POSITIONS")
        positions_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        positions_font = positions_title.font()
        positions_font.setPointSize(16)
        positions_font.setBold(True)
        positions_title.setFont(positions_font)
        positions_layout.addWidget(positions_title)

        # Filter UI for Positions Table
        self.positions_filter_label = QLabel("Filter:")
        self.positions_filter_text_box = QLineEdit()
        self.hide_closed_positions_checkbox = QCheckBox("Hide Closed Positions")
        positions_filter_layout = QHBoxLayout()
        positions_filter_layout.addWidget(self.positions_filter_label)
        positions_filter_layout.addWidget(self.positions_filter_text_box)
        positions_filter_layout.addWidget(self.hide_closed_positions_checkbox)
        positions_layout.addLayout(positions_filter_layout)

        # Add clear button inside QLineEdit for Positions Filter
        positions_clear_action = self.positions_filter_text_box.addAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_LineEditClearButton),
            QLineEdit.ActionPosition.TrailingPosition
        )
        positions_clear_action.triggered.connect(lambda: self.clear_filter(self.positions_table, self.positions_filter_text_box))

        # Positions Table
        self.positions_table = QTableWidget(0, 5)
        self.positions_table.setHorizontalHeaderLabels(["Pair", "Quantity", "Average Price", "Value", "PnL"])
        self.positions_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.positions_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.positions_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.positions_table.sortItems(0, Qt.SortOrder.AscendingOrder)
        positions_layout.addWidget(self.positions_table)

        # Add Positions Section to Main Layout
        self.tables_layout.addWidget(positions_section)

        # History Section
        history_section = QWidget()
        history_layout = QVBoxLayout(history_section)

        # Trade History Title
        history_title = QLabel("TRADE HISTORY")
        history_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        history_font = history_title.font()
        history_font.setPointSize(16)
        history_font.setBold(True)
        history_title.setFont(history_font)
        history_layout.addWidget(history_title)

        # Filter UI for History Table
        self.history_filter_label = QLabel("Filter:")
        self.history_filter_text_box = QLineEdit()
        history_filter_layout = QHBoxLayout()
        history_filter_layout.addWidget(self.history_filter_label)
        history_filter_layout.addWidget(self.history_filter_text_box)
        history_layout.addLayout(history_filter_layout)

        # Add clear button inside QLineEdit
        history_clear_action = self.history_filter_text_box.addAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_LineEditClearButton),
            QLineEdit.ActionPosition.TrailingPosition
        )
        history_clear_action.triggered.connect(lambda: self.clear_filter(self.history_table, self.history_filter_text_box))

        # History Table
        self.history_table = QTableWidget(0, 6)
        self.history_table.setHorizontalHeaderLabels(["Pair", "Side", "Date", "Quantity", "Price", "Value"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.history_table.sortItems(0, Qt.SortOrder.AscendingOrder)
        self.history_table.installEventFilter(self)
        history_layout.addWidget(self.history_table)

        # Connect double-click signal to edit_trade
        self.history_table.itemDoubleClicked.connect(self.edit_trade)

        # Add History Section to Main Layout
        self.tables_layout.addWidget(history_section)

        # Add the tables container to the main window layout
        self.main_layout.addWidget(self.tables_container)

        # Connect the filter's textChanged signal to the filtering function
        self.positions_filter_text_box.textChanged.connect(lambda: self.filter_table(self.positions_table, self.positions_filter_text_box.text(), self.hide_closed_positions_checkbox.isChecked()))
        self.history_filter_text_box.textChanged.connect(lambda: self.filter_table(self.history_table, self.history_filter_text_box.text()))
        self.hide_closed_positions_checkbox.stateChanged.connect(lambda: self.filter_table(self.positions_table, self.positions_filter_text_box.text(), self.hide_closed_positions_checkbox.isChecked()))

        self.positions_table.setFocus()

    def setup_shortcuts(self):
        """
        Configures keyboard shortcuts for undo and redo actions within the application.
        """
        # Undo shortcut: CTRL-Z
        undo_shortcut = QShortcut(QKeySequence('Ctrl+Z'), self)
        undo_shortcut.activated.connect(self.undo_last_change)

        # Undo shortcut: CTRL-Y
        redo_shortcut = QShortcut(QKeySequence('Ctrl+Y'), self)
        redo_shortcut.activated.connect(self.redo_next_change)

    def clear_filter(self, table_widget, filter_text_box):
        """
        Clears the filter text box and applies the updated (empty) filter to the specified table widget.
        """
        filter_text_box.clear()
        self.filter_table(table_widget, filter_text_box.text())

    def load_data(self, file_path=None):
        """
        Loads trading data from a JSON file, updates the application's data structures, and refreshes the UI, handling any errors that occur during the file loading process.
        """
        if file_path is None:
            file_path, _ = QFileDialog.getOpenFileName(self, "Open JSON File", "", "JSON files (*.json)")

        if file_path:
            self.save_last_used_file_path(file_path)

            if not self.check_data_file_version(file_path):
                return

            try:
                with open(self.file_path, 'r') as file:
                    data = json.load(file)
                    self.full_history_data = data['data'] if data['data'] else []

                    # Convert specific fields back to Decimal
                    for row in self.full_history_data:
                        row[4] = Decimal(row[4])  # Quantity is at index 4
                        row[5] = Decimal(row[5])  # Price is at index 5

                    self.load_changes_with_prompt()
                    self.update_data()
                    self.update_title()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error loading file: {e}")

    def new(self):
        """
        Resets the application to a new state, clearing historical data and any associated file path references.
        """
        self.full_history_data = []

        self.save_last_used_file_path("")
        self.load_changes_with_prompt()
        self.update_data()
        self.update_title()

    def save(self):
        """
        Saves the current data to the existing file path, or prompts the user to select a file path if none is set.
        """
        if self.file_path:
            self.save_data(self.file_path)
        else:
            self.save_as()

    def save_as(self):
        """
        Prompts the user to select a file path and saves the current data to the specified JSON file.
        """
        file_path, _ = QFileDialog.getSaveFileName(self, "Save JSON File", "", "JSON files (*.json)")
        if file_path:
            self.save_data(file_path)

    def save_data(self, file_path):
        """
        Saves the current application data to a specified file path in JSON format, handling exceptions and updating the application title with the new file path.
        """
        self.check_data_file_version(file_path)

        try:
            with open(file_path, 'w') as file:
                processed_history = self.change_log.process(self.file_path, self.full_history_data, True)
                data = {"version": DATA_FILE_VERSION, "data": processed_history}
                json.dump(data, file, indent=2, cls=DecimalEncoder)
                self.save_last_used_file_path(file_path)
                self.update_title()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving file: {e}")

    def add_trade(self):
        """
        Opens a dialog to add a new trade, updates the change log with the new trade data, and refreshes the application's data and title.
        """
        # Get the currently selected pair from positions_table
        selected_rows = self.positions_table.selectionModel().selectedRows()
        selected_pair = None
        if selected_rows:
            selected_row_index = selected_rows[0].row()
            selected_pair_item = self.positions_table.item(selected_row_index, 0)
            selected_pair = selected_pair_item.text()

        trade_dialog = AddTradeDialog(self, selected_pair)
        if trade_dialog.exec():
            new_data = trade_dialog.new_data
            for data in new_data:
                self.change_log.add(self.file_path, 'add', None, data)
            self.update_data()

        self.update_title()

    def edit_trade(self):
        """
        Opens a dialog to edit a selected trade, updates the change log if changes are made, and refreshes the displayed data and title.
        """
        selected_items = self.history_table.selectedItems()
        if not selected_items:
            return
        selected_row = self.history_table.currentRow()
        trade_data = [self.history_table.item(selected_row, col).text() for col in range(self.history_table.columnCount())]

        trade_dialog = EditTradeDialog(trade_data[:-1], self.get_trade_id_from_row(selected_row), self)
        trade_data[3] = Decimal(trade_data[3])
        trade_data[4] = Decimal(trade_data[4])

        if trade_dialog.exec():
            edited_data = trade_dialog.new_data
            if edited_data and edited_data[1:] != trade_data[:-1]:
                self.change_log.add(self.file_path, 'edit', [edited_data[0]] + trade_data[:-1], edited_data)
                self.update_data()

        self.update_title()

    def delete_trade(self):
        """
        Deletes the selected trade(s) after confirmation, updates the change log, and refreshes the application data and title.
        """
        selected_rows = self.history_table.selectionModel().selectedRows()
        if selected_rows:
            response = QMessageBox.question(self, "Delete Confirmation", "Are you sure you want to delete the selected trade(s)?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if response == QMessageBox.StandardButton.Yes:
                for model_index in selected_rows:
                    row = model_index.row()
                    trade_id = self.get_trade_id_from_row(row)
                    if trade_id is not None:
                        pair_item = self.history_table.item(row, 0)
                        side_item = self.history_table.item(row, 1)
                        date_item = self.history_table.item(row, 2)
                        quantity_item = self.history_table.item(row, 3)
                        price_item = self.history_table.item(row, 4)

                        # Convert quantity and price back to Decimal
                        quantity = Decimal(quantity_item.text())
                        price = Decimal(price_item.text())

                        original_data = [trade_id, pair_item.text(), side_item.text(), date_item.text(), quantity, price]

                        self.change_log.add(self.file_path, 'delete', original_data, None)

                self.update_data()

        self.update_title()

    def add_history_row(self, row):
        """
        Inserts a new row into the trade history table, including calculated trade value and color-coding based on the trade type, while also storing the trade's UUID.
        """
        value = (Decimal(row[4]) * Decimal(row[5])).quantize(decimal_places, ROUND_HALF_UP)

        table_row = self.history_table.rowCount()
        self.history_table.insertRow(table_row)

        # Determine the color based on the 'Side' value
        row_color = green if row[2] == 'Buy' else red if row[2] == 'Sell' else None

        # Insert cells, skipping UUID
        for col_index in range(1, 7):  # Adjust for skipping UUID and include Value
            if col_index in (4, 5):  # Quantity or Price
                item = DecimalTableWidgetItem(row[col_index])
            elif col_index == 6:  # Value, calculated
                item = DecimalTableWidgetItem(value)
            else:
                item = QTableWidgetItem(str(row[col_index]))

            if row_color:
                item.setBackground(row_color)

            # If this is the first column, store the UUID
            if col_index == 1:
                item.setData(UUIDRole, row[0])

            self.history_table.setItem(table_row, col_index - 1, item)

    def update_history(self, history_data):
        """
        Clears and repopulates the trade history table with provided data, temporarily disabling sorting to improve performance.
        """
        self.history_table.setSortingEnabled(False)
        self.history_table.setRowCount(0)

        for row in history_data:
            self.add_history_row(row)

        self.history_table.setSortingEnabled(True)

    def update_positions(self, history_data):
        """
        Updates the positions table by calculating and displaying the accumulated quantity, average price, total value, and total profit/loss for each trading pair based on the provided trade history.
        """
        self.positions_table.setSortingEnabled(False)
        self.positions_table.setRowCount(0)  # Clear existing rows

        # Sort self.full_history_data by date (date is at index 3)
        sorted_history_data = sorted(history_data, key=lambda x: datetime.strptime(x[3], '%Y-%m-%d'))

        history = {}

        for row in sorted_history_data:
            # Assuming the format is [trade_id, pair, side, date, quantity, price]
            _, pair, side, _, quantity, price = row
            quantity = Decimal(str(quantity))
            price = Decimal(str(price))

            if pair not in history:
                history[pair] = {'trades': [], 'total_pnl': Decimal('0'), 'total_quantity': Decimal('0'), 'total_value': Decimal('0')}

            # Accumulate quantity and value for buy trades to calculate average buy price
            if side.lower() == 'buy':
                history[pair]['total_quantity'] += quantity
                history[pair]['total_value'] += quantity * price
            elif side.lower() == 'sell' and history[pair]['total_quantity'] > 0:
                # Calculate PnL based on the difference from the average buy price
                average_buy_price = (history[pair]['total_value'] / history[pair]['total_quantity']).quantize(decimal_places, ROUND_HALF_UP)
                pnl = ((price - average_buy_price) * quantity).quantize(decimal_places, ROUND_HALF_UP)
                history[pair]['total_pnl'] += pnl
                # Adjust total quantity and value after sell
                history[pair]['total_quantity'] -= quantity
                # Optionally adjust total_value if you want to track value after sells
                history[pair]['total_value'] -= quantity * average_buy_price

        for pair, info in history.items():
            row_position = self.positions_table.rowCount()
            self.positions_table.insertRow(row_position)

            if info['total_quantity'] > Decimal('0'):
                average_price = info['total_value'] / info['total_quantity']
                values = [pair, info['total_quantity'].quantize(decimal_places, ROUND_HALF_UP), average_price.quantize(decimal_places, ROUND_HALF_UP), info['total_value'].quantize(decimal_places, ROUND_HALF_UP), info['total_pnl']]
            else:
                values = [pair, '-', '-', '-', info['total_pnl']]

            for col, value in enumerate(values):
                if col in [1, 2, 3, 4] and value != '-':
                    item = DecimalTableWidgetItem(value)
                else:
                    item = QTableWidgetItem(str(value))
                self.positions_table.setItem(row_position, col, item)

        self.positions_table.setSortingEnabled(True)

    def save_last_used_file_path(self, file_path):
        """
        Stores the last used file path in the application settings for future access.
        """
        self.file_path = file_path
        settings = QSettings(SETTINGS_FILE, QSettings.Format.IniFormat)
        settings.setValue("lastUsedFile", self.file_path)

    def load_last_used_file(self):
        """
        Loads data from the last used file path if available, otherwise prompts for changes, and updates the application's data and title accordingly.
        """
        if self.file_path:
            self.load_data(self.file_path)
        else:
            self.load_changes_with_prompt()
        self.update_data()
        self.update_title()

    def load_changes_with_prompt(self):
        """
        Loads and prompts the user about unapplied changes from the change log, offering an option to recover or discard these modifications.
        """
        self.change_log.load(self.file_path)
        if not self.change_log.all_applied():
            # Ask the user if they want to keep where they left off
            response = QMessageBox.question(
                self,
                "Unapplied Changes Detected",
                "Oopsie, you were doing something that hasn't been saved!\n"
                "Would you like to recover the modifications?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )

            if response == QMessageBox.StandardButton.No:
                self.change_log.clear_not_applied(self.file_path)

    def filter_table(self, table_widget, filter_text, hide_closed=False):
        """
        Filters the rows of a given table widget based on a text filter and an option to hide rows with closed positions.
        """
        for row in range(table_widget.rowCount()):
            item = table_widget.item(row, 0)
            quantity_item = table_widget.item(row, 1)

            show_row = True
            if item:
                if filter_text and filter_text.lower() not in item.text().lower():
                    show_row = False
                if hide_closed and quantity_item and quantity_item.text() == '-':
                    show_row = False

            table_widget.setRowHidden(row, not show_row)

    def get_trade_id_from_row(self, row):
        """
        Retrieves the trade ID (UUID) stored in the first column of a specified row in the history table.
        """
        # UUID is stored in the first column
        item = self.history_table.item(row, 0)
        if item:
            return item.data(UUIDRole)
        return None

    def eventFilter(self, source, event):
        """
        Implements an event filter to clear table selections with the Escape key and to delete a trade with the Delete key when focused on the history table.
        """
        if event.type() == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Escape:
            self.positions_table.clearSelection()
            self.history_table.clearSelection()
            return True
        if event.type() == QEvent.Type.KeyPress and source is self.history_table:
            if event.key() == Qt.Key.Key_Delete:
                self.delete_trade()
                return True  # Indicates that the event has been handled
        return super().eventFilter(source, event)  # Pass the event to the base class method

    def update_data(self):
        """
        Processes changes to the trade history, then updates both the history and positions tables with the processed data.
        """
        processed_history = self.change_log.process(self.file_path, self.full_history_data)
        self.update_history(processed_history)
        self.update_positions(processed_history)

    def update_title(self):
        """
        Updates the window title to reflect the current state, including the version, loaded file name, and unsaved changes indicator.
        """
        title = f"Crypto Trades Tracker - {CRYPTO_TRADES_TRACKER_VERSION}"
        if self.file_path:
            title += f" - {os.path.basename(self.file_path)}"
        if not self.change_log.all_applied():
            title += f"*"

        self.setWindowTitle(title)

    def closeEvent(self, event):
        """
        Handles the window's close event by prompting the user to save unapplied changes, clearing unapplied changes if chosen, and saving current settings before closing.
        """
        # Check if there are unapplied changes
        if not self.change_log.all_applied():
            # Ask the user if they want to save the changes
            response = QMessageBox.question(
                self,
                "Save Changes",
                "You have unsaved changes. Would you like to save them before exiting?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
            )

            if response == QMessageBox.StandardButton.Yes:
                self.save()
            elif response == QMessageBox.StandardButton.No:
                self.change_log.clear_not_applied(self.file_path)

        self.write_settings()
        super().closeEvent(event)

    def write_settings(self):
        """
        Saves the application's current settings, including version, last used file path, and window geometry and state, to a configuration file.
        """
        settings = QSettings(SETTINGS_FILE, QSettings.Format.IniFormat)
        settings.setValue("version", CRYPTO_TRADES_TRACKER_VERSION)
        settings.setValue("lastUsedFile", self.file_path)
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())

    def read_settings(self):
        """
        Reads and applies the application's saved settings, including last used file path and window geometry and state, with a version check for compatibility.
        """
        settings = QSettings(SETTINGS_FILE, QSettings.Format.IniFormat)
        version = settings.value("version")
        if version and version != CRYPTO_TRADES_TRACKER_VERSION:
            # Merge with new version???
            QMessageBox.critical(self, "Error", f"Settings version: {version}\nCurrent version: {CRYPTO_TRADES_TRACKER_VERSION}")
        self.file_path = settings.value("lastUsedFile")
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        window_state = settings.value("windowState")
        if geometry:
            self.restoreState(window_state)

    def undo_last_change(self):
        """
        Undoes the last change in the change log after confirmation, then updates the data and title to reflect this action.
        """
        last_change = self.change_log.get_last_to_undo()
        if last_change is not None:
            dialog = ConfirmChangeDialog(last_change, "undo")

            if dialog.get_result():
                self.change_log.undo()
                self.update_data()
                self.update_title()

    def redo_next_change(self):
        """
        Redoes the next change in the change log after confirmation, updating the data and title accordingly.
        """
        next_change = self.change_log.get_next_to_redo()
        if next_change is not None:
            dialog = ConfirmChangeDialog(next_change, "redo")

            if dialog.get_result():
                self.change_log.redo()
                self.update_data()
                self.update_title()

    def check_data_file_version(self, file_path):
        """
        Checks and updates the version of the data file, ensuring compatibility or initializing the file if necessary, and handles version mismatch errors.
        """
        # Try to read the existing data
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
        except FileNotFoundError:
            # File doesn't exist, create a new structure
            data = {}
        except json.JSONDecodeError:
            # File exists but is not valid JSON, start afresh
            data = {}

        # Check and update the version
        if "version" not in data:
            data["version"] = DATA_FILE_VERSION
            with open(file_path, 'w') as file:
                json.dump(data, file, indent=2, cls=DecimalEncoder)
            return True
        elif data["version"] == DATA_FILE_VERSION:
            return True
        else:
            QMessageBox.critical(self, "Error", f"Wrong file version: {file_path} - {data["version"]} instead of {DATA_FILE_VERSION}")
            return False
            # Eventually add migration to future versions

    def help(self):
        """
        Displays a help dialog with instructions and keyboard shortcuts for the application.
        """
        dialog = QDialog(self)
        dialog.setWindowTitle("Help")
        dialog.setFixedSize(400, 300)

        layout = QVBoxLayout()

        help_text = """
        <b>Tip:</b> Selecting a position before adding a new trade auto-fills the pair.</b><br><br>
        <b>Program Shortcuts:</b><br><br>
        - <b>F1:</b> Help<br><br>
        - <b>Ctrl+N:</b> New File<br>
        - <b>Ctrl+O:</b> Open File<br>
        - <b>Ctrl+S:</b> Save<br>
        - <b>Ctrl+Shift+S:</b> Save As<br>
        <br>
        - <b>Ctrl+Z:</b> Undo<br>
        - <b>Ctrl+Y:</b> Redo
        """

        help_label = QLabel(help_text)
        help_label.setTextFormat(Qt.TextFormat.RichText)  # To enable HTML styling
        layout.addWidget(help_label)

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)

        dialog.setLayout(layout)
        dialog.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    QCoreApplication.setOrganizationName("Valtrius")
    QCoreApplication.setApplicationName("CryptoTradesTracker")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
