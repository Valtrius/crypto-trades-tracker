from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QFont
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QTableWidget, QHeaderView, QComboBox
from datetime import datetime
from decimal import Decimal

from constants import red, green, light_gray
from custom_double_validator import CustomDoubleValidator


class EditTradeDialog(QDialog):
    def __init__(self, trade_data, uuid, parent=None):
        """
        Initialize the dialog for editing a trade with the provided trade data and UUID.
        """
        super().__init__(parent)
        self.setWindowTitle(f"Edit trade")
        self.setFixedSize(600, 220)

        self.new_data = None
        self.uuid = uuid

        layout = QVBoxLayout(self)

        # Tables to show change details
        table = self.create_table(trade_data, True)
        layout.addWidget(table)

        arrow_label = QLabel("↓")
        font = QFont()
        font.setPointSize(24)
        font.setBold(True)
        arrow_label.setFont(font)
        arrow_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center align the arrow
        layout.addWidget(arrow_label)

        self.table = self.create_table(trade_data)
        layout.addWidget(self.table)

        # Buttons
        btn_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.validate_and_save_trade)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)

        btn_layout.addWidget(ok_button)
        btn_layout.addWidget(cancel_button)

        layout.addLayout(btn_layout)

    def create_table(self, trade_data, read_only=False):
        """
        Create a table for displaying trade data. If read_only is False, the table is editable; otherwise, it's read-only.
        """
        table = QTableWidget(1, 5)  # Single row, 5 columns
        table.setHorizontalHeaderLabels(["Pair", "Side", "Date", "Quantity", "Price"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        if read_only:
            table.setEnabled(False)

        # Set up a QDoubleValidator for the "Quantity" and "Price" columns
        double_validator = CustomDoubleValidator()

        # Set up the widgets for each column
        for col in range(table.columnCount()):
            if col == 1 and not read_only:  # "Side" column
                combo_box = QComboBox()
                combo_box.addItems(["Buy", "Sell"])
                combo_box.setCurrentText(trade_data[col])
                combo_box.currentTextChanged.connect(lambda text, row=0: self.update_row_color(table, row, text))
                table.setCellWidget(0, col, combo_box)
            elif col in [3, 4]:  # "Quantity" and "Price" columns
                line_edit = QLineEdit()
                line_edit.setValidator(double_validator)
                line_edit.setText(trade_data[col])
                table.setCellWidget(0, col, line_edit)
            else:
                line_edit = QLineEdit()
                line_edit.setText(trade_data[col])
                table.setCellWidget(0, col, line_edit)

        if not read_only:
            self.update_row_color(table, 0, combo_box.currentText())
        else:
            self.update_row_color(table, 0, table.cellWidget(0, 1).text())

        return table

    def update_row_color(self, table, row, text):
        """
        Update the row color in the table based on the text value. The row color is green for 'Buy', red for 'Sell', and light gray otherwise.
        """
        color = green if text == 'Buy' else red if text == 'Sell' else light_gray

        for col in range(table.columnCount()):
            widget = table.cellWidget(row, col)
            if widget is not None:
                palette = widget.palette()
                palette.setColor(QPalette.ColorRole.Base, color)
                widget.setPalette(palette)

    def validate_and_save_trade(self):
        """
        Validate the trade data entered in the table cells and save it if valid. If any validation error occurs, display a critical message box.
        """
        try:
            trade_id = self.uuid
            # First column (0) is "Pair", and it's a line edit widget
            pair_cell_widget = self.table.cellWidget(0, 0)
            pair = pair_cell_widget.text().upper()

            # Second column (1) is "Side", and it's a combobox widget
            side_widget = self.table.cellWidget(0, 1)
            side = side_widget.currentText()

            # Third column (2) is "Date", and it's a line edit widget
            date_cell_widget = self.table.cellWidget(0, 2)
            date = date_cell_widget.text()
            datetime.strptime(date.replace(" ", ""), '%Y-%m-%d')  # Validates date format

            # For "Quantity" and "Price", they are line edit widgets
            quantity_cell_widget = self.table.cellWidget(0, 3)
            quantity = Decimal(quantity_cell_widget.text().replace(" ", ""))

            price_cell_widget = self.table.cellWidget(0, 4)
            price = Decimal(price_cell_widget.text().replace(" ", ""))

            self.new_data = [trade_id, pair, side, date, quantity, price]

            self.accept()  # Close the dialog successfully
        except ValueError as e:
            QMessageBox.critical(self, "Validation Error", str(e))
