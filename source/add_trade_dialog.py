from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QPalette
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QMessageBox, QTableWidget, QHeaderView, QComboBox
from datetime import datetime
from decimal import Decimal
import uuid

from constants import red, green, light_gray
from custom_double_validator import CustomDoubleValidator


class AddTradeDialog(QDialog):
    def __init__(self, parent=None, pair=None):
        super().__init__(parent)
        self.setWindowTitle(f"Add new trade")
        self.setFixedSize(600, 100)

        self.new_data = None

        layout = QVBoxLayout(self)

        # Tables to show change details
        self.table = self.create_table(pair)
        layout.addWidget(self.table)

        # Buttons
        btn_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.validate_and_save_trade)
        ok_button.setDefault(True)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)

        btn_layout.addWidget(ok_button)
        btn_layout.addWidget(cancel_button)

        layout.addLayout(btn_layout)

    def create_table(self, pair):
        table = QTableWidget(1, 7)
        table.setHorizontalHeaderLabels(["", "Pair", "Side", "Date", "Quantity", "Price", ""])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        table.setColumnWidth(0, 23)
        table.setColumnWidth(6, 23)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        self.setup_row(table, 0, pair)
        if pair:
            QTimer.singleShot(0, lambda: table.cellWidget(0, 3).setFocus())
        return table

    def setup_row(self, table, row, pair):
        double_validator = CustomDoubleValidator()
        for col in range(0, 7):
            if col == 0:
                button = QPushButton("+")
                button.clicked.connect(self.add_row)
                table.setCellWidget(row, col, button)
            elif col == 2:
                combo_box = QComboBox()
                combo_box.addItems(["Buy", "Sell"])
                combo_box.currentTextChanged.connect(lambda text: self.update_row_color(table, self.table.currentRow(), text))
                table.setCellWidget(row, col, combo_box)
            elif col in [4, 5]:
                line_edit = QLineEdit()
                line_edit.setValidator(double_validator)
                table.setCellWidget(row, col, line_edit)
            elif col == 6:
                button = QPushButton("-")
                button.clicked.connect(lambda: self.delete_row(table.currentRow()))
                table.setCellWidget(row, col, button)
            else:
                line_edit = QLineEdit()
                if col == 1 and pair:
                    line_edit.setText(pair)
                elif col == 3:
                    line_edit.setPlaceholderText("YYYY-MM-DD")
                table.setCellWidget(row, col, line_edit)

        self.update_row_color(table, row, combo_box.currentText())
        if not pair:
            QTimer.singleShot(0, lambda: table.cellWidget(row, 1).setFocus())

    def add_row(self):
        row_index = self.table.rowCount()
        self.table.setCellWidget(row_index - 1, 0, None)
        self.table.insertRow(row_index)
        self.setup_row(self.table, row_index, None)

        # Adjust dialog height as needed
        self.adjust_dialog_height()

    def delete_row(self, row_index):
        row_count = self.table.rowCount()
        if row_count != 1:
            self.table.removeRow(row_index)
            self.adjust_dialog_height()
        if row_index == row_count - 1:
            button = QPushButton("+")
            button.clicked.connect(self.add_row)
            self.table.setCellWidget(row_index - 1, 0, button)

    def adjust_dialog_height(self):
        # Adjust the dialog's height based on the number of rows
        row_height = 23  # Assuming a fixed row height, adjust as needed
        base_height = 100
        new_height = base_height + row_height * (self.table.rowCount() - 1)
        self.setFixedHeight(new_height)

    def update_row_color(self, table, row, text):
        color = green if text == 'Buy' else red if text == 'Sell' else light_gray

        for col in range(1, 7):
            widget = table.cellWidget(row, col)
            if widget is not None:
                palette = widget.palette()
                palette.setColor(QPalette.ColorRole.Base, color)
                widget.setPalette(palette)

    def validate_and_save_trade(self):
        self.new_data = []

        try:
            for row in range(self.table.rowCount()):
                trade_id = str(uuid.uuid4())
                # First column (0) is "Pair", and it's a line edit widget
                pair_cell_widget = self.table.cellWidget(row, 1)
                pair = pair_cell_widget.text().upper()

                # Second column (1) is "Side", and it's a combobox widget
                side_widget = self.table.cellWidget(row, 2)
                side = side_widget.currentText()

                # Third column (2) is "Date", and it's a line edit widget
                date_cell_widget = self.table.cellWidget(row, 3)
                date = date_cell_widget.text()
                datetime.strptime(date.replace(" ", ""), '%Y-%m-%d')  # Validates date format

                # For "Quantity" and "Price", they are line edit widgets
                quantity_cell_widget = self.table.cellWidget(row, 4)
                quantity = Decimal(quantity_cell_widget.text().replace(" ", ""))

                price_cell_widget = self.table.cellWidget(row, 5)
                price = Decimal(price_cell_widget.text().replace(" ", ""))

                self.new_data.append([trade_id, pair, side, date, quantity, price])

            self.accept()  # Close the dialog successfully
        except ValueError as e:
            QMessageBox.critical(self, "Validation Error", str(e))
