import os
import sys
import json
from decimal import Decimal, ROUND_HALF_UP
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QTableWidget, QHeaderView, QFileDialog, QMessageBox, QLabel, QLineEdit, QTableWidgetItem, QAbstractItemView
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QColor

from decimal_table_widget_item import DecimalTableWidgetItem
from decimal_encoder import DecimalEncoder
from trade_dialog import TradeDialog
from change_log import ChangeLog
from datetime import datetime

CRYPTO_TRADES_TRACKER_VERSION = '1.0.0'
SETTINGS_FILE = 'ctt_settings.json'
CHANGE_LOG_FILE = 'ctt_change_log.json'

UUIDRole = Qt.ItemDataRole.UserRole + 1

# Define pastel colors
dark_green = QColor(0, 100, 0)
dark_red = QColor(139, 0, 0)
pastel_green = QColor(152, 251, 152)
pastel_red = QColor(255, 182, 193)

# Set the desired precision: 8 decimal places
decimal_places = Decimal('1E-8')
# Initialize a list to store all history data
full_history_data = []


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Crypto Trades Tracker - " + CRYPTO_TRADES_TRACKER_VERSION)
        self.setGeometry(0, 0, 1280, 720)  # x, y, width, height
        self.center_window()

        self.change_log = ChangeLog()

        # Main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # Setup UI components
        self.setup_button_bar()
        self.setup_tables()

        # Load settings
        self.load_settings()

        # Load last data
        self.load_last_used_file()

    def center_window(self):
        # Get the screen's resolution
        screen = QApplication.primaryScreen().geometry()
        # Calculate the x and y positions to center the window
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def setup_button_bar(self):
        self.button_bar = QWidget()
        self.button_bar_layout = QHBoxLayout(self.button_bar)

        self.load_button = QPushButton("Load")
        self.save_button = QPushButton("Save")
        self.add_button = QPushButton("Add Trade")

        # Connect buttons to placeholder functions
        self.load_button.clicked.connect(lambda: self.load_data(None))
        self.save_button.clicked.connect(self.save_data)
        self.add_button.clicked.connect(self.add_trade)

        self.button_bar_layout.addWidget(self.load_button)
        self.button_bar_layout.addWidget(self.save_button)
        self.button_bar_layout.addWidget(self.add_button)

        self.main_layout.addWidget(self.button_bar)

    def setup_tables(self):
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
        positions_font.setBold(True)
        positions_title.setFont(positions_font)
        positions_layout.addWidget(positions_title)

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
        history_font.setBold(True)
        history_title.setFont(history_font)
        history_layout.addWidget(history_title)

        # Filter UI for History Table
        self.filter_label = QLabel("Filter:")
        self.filter_text_box = QLineEdit()
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(self.filter_label)
        filter_layout.addWidget(self.filter_text_box)
        history_layout.addLayout(filter_layout)

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
        self.filter_text_box.textChanged.connect(lambda: self.filter_table(self.history_table, self.filter_text_box.text()))

    def load_data(self, file_path=None):
        if file_path is None:
            file_path, _ = QFileDialog.getOpenFileName(self, "Open JSON File", "", "JSON files (*.json)")
        if file_path:
            try:
                with open(file_path, 'r') as file:
                    global full_history_data
                    full_history_data = json.load(file)

                    # Convert specific fields back to Decimal
                    for row in full_history_data:
                        row[4] = Decimal(row[4])  # Quantity is at index 4
                        row[5] = Decimal(row[5])  # Price is at index 5

                    self.update_data()
                    self.save_last_used_file_path(file_path)
                    self.setWindowTitle(f"Crypto Trades Tracker - {CRYPTO_TRADES_TRACKER_VERSION} - {os.path.basename(file_path)}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error loading file: {e}")

    def save_data(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save JSON File", "", "JSON files (*.json)")
        if file_path:
            try:
                with open(file_path, 'w') as file:
                    json.dump(full_history_data, file, cls=DecimalEncoder)
                    self.save_last_used_file_path(file_path)

                    self.setWindowTitle(f"Crypto Trades Tracker - {CRYPTO_TRADES_TRACKER_VERSION} - {os.path.basename(file_path)}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error saving file: {e}")

    def add_trade(self):
        # Get the currently selected pair from positions_table
        selected_rows = self.positions_table.selectionModel().selectedRows()
        selected_pair = None
        if selected_rows:
            selected_row_index = selected_rows[0].row()
            selected_pair_item = self.positions_table.item(selected_row_index, 0)
            selected_pair = selected_pair_item.text()

        trade_dialog = TradeDialog(self, selected_pair)
        if trade_dialog.exec():
            new_data = trade_dialog.new_data
            if new_data:
                self.change_log.add('add', None, new_data)
                self.update_data()

    def edit_trade(self):
        selected_items = self.history_table.selectedItems()
        if not selected_items:
            return
        selected_row = self.history_table.currentRow()
        trade_data = [self.history_table.item(selected_row, col).text() for col in range(self.history_table.columnCount())]

        trade_dialog = TradeDialog(self, None, trade_data[:-1], self.get_trade_id_from_row(selected_row))
        trade_data[3] = Decimal(trade_data[3])
        trade_data[4] = Decimal(trade_data[4])

        if trade_dialog.exec():
            edited_data = trade_dialog.new_data
            if edited_data and edited_data[1:] != trade_data[:-1]:
                self.change_log.add('edit', [edited_data[0]] + trade_data[:-1], edited_data)
                self.update_data()

    def delete_trade(self):
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

                        self.change_log.add('delete', original_data, None)

                self.update_data()

    def add_history_row(self, row):
        value = (Decimal(row[4]) * Decimal(row[5])).quantize(decimal_places, ROUND_HALF_UP)

        table_row = self.history_table.rowCount()
        self.history_table.insertRow(table_row)

        # Determine the color based on the 'Side' value
        row_color = dark_green if row[2] == 'Buy' else dark_red if row[2] == 'Sell' else None

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
        self.history_table.setSortingEnabled(False)
        self.history_table.setRowCount(0)

        for row in history_data:
            self.add_history_row(row)

        self.history_table.setSortingEnabled(True)

    def update_positions(self, history_data):
        self.positions_table.setSortingEnabled(False)
        self.positions_table.setRowCount(0)  # Clear existing rows

        # Sort full_history_data by date (assuming date is at index 3)
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
        try:
            # Attempt to read existing settings
            with open(SETTINGS_FILE, 'r') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # If the file doesn't exist or is not valid JSON, start fresh
            data = {}

        # Update the last file path setting
        data['last_file_path'] = file_path

        # Write the updated settings back to the file
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(data, f)

    def load_settings(self):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # If the file doesn't exist or is not valid JSON, start fresh
            data = {}
        except Exception as e:
            print("Error loading settings file:", e)
            return

        version = data.get('version', '')
        if not version:
            data['version'] = CRYPTO_TRADES_TRACKER_VERSION
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(data, f)
        elif version != CRYPTO_TRADES_TRACKER_VERSION:
            QMessageBox.critical(self, "Error", f"Settings version: {version}\nCurrent version: {CRYPTO_TRADES_TRACKER_VERSION}")

    def load_last_used_file(self):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                data = json.load(f)
            last_file_path = data.get('last_file_path', '')
            if last_file_path:
                self.load_data(last_file_path)
        except Exception as e:
            print("Error loading last used file:", e)

    def filter_table(self, table_widget, filter_text):
        for row in range(table_widget.rowCount()):
            item = table_widget.item(row, 0)
            # Ensure there's an item and filter_text is not empty to avoid hiding everything by default
            if item and filter_text:
                table_widget.setRowHidden(row, filter_text.lower() not in item.text().lower())

    def get_trade_id_from_row(self, row):
        # UUID is stored in the first column
        item = self.history_table.item(row, 0)
        if item:
            return item.data(UUIDRole)
        return None

    def get_row_from_trade_id(self, trade_id):
        row_count = self.history_table.rowCount()
        for row in range(row_count):
            item = self.history_table.item(row, 0)  # UUID is stored in the first column
            if item and item.data(UUIDRole) == trade_id:
                return row
        return None

    def eventFilter(self, source, event):
        if event.type() == QEvent.Type.KeyPress and source is self.history_table:
            if event.key() == Qt.Key.Key_Delete:
                self.delete_trade()
                return True  # Indicates that the event has been handled
        return super().eventFilter(source, event)  # Pass the event to the base class method

    def update_data(self):
        processed_history = self.change_log.process(full_history_data)
        self.update_history(processed_history)
        self.update_positions(processed_history)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
