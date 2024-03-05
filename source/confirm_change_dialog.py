from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QHBoxLayout, QTableWidget, QTableWidgetItem, QLabel, QHeaderView
from decimal_table_widget_item import DecimalTableWidgetItem

from constants import red, green, light_gray


class ConfirmChangeDialog(QDialog):
    def __init__(self, change_data, change_string, parent=None):
        """
        Initializes a confirmation dialog for a change operation, displaying the details of the change for user confirmation.
        """
        super().__init__(parent)
        self.setWindowTitle(f"Confirm {change_string}")
        self.setFixedSize(600, 230)

        # Determine change type and adjust the dialog accordingly
        change_type = change_data.get("change_type", "")
        original_data = change_data.get("original_data")
        new_data = change_data.get("new_data")

        layout = QVBoxLayout(self)

        # Header
        header_label = QLabel(f"{change_string.capitalize()} {change_type.capitalize()}")
        header_font = header_label.font()
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header_label)

        # Tables to show change details
        if change_type == "add" and new_data:
            table1 = self.create_table(None)
            table2 = self.create_table(new_data[1:])
        elif change_type == "delete" and original_data:
            table1 = self.create_table(original_data[1:])
            table2 = self.create_table(None)
        elif change_type == "edit" and original_data and new_data:
            table1 = self.create_table(original_data[1:])
            table2 = self.create_table(new_data[1:])

        if table1:
            layout.addWidget(table1)

        arrow_label = QLabel("↓")
        font = QFont()
        font.setPointSize(24)
        font.setBold(True)
        arrow_label.setFont(font)
        arrow_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center align the arrow
        layout.addWidget(arrow_label)

        if table2:
            layout.addWidget(table2)

        # Buttons
        btn_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)

        btn_layout.addWidget(ok_button)
        btn_layout.addWidget(cancel_button)

        layout.addLayout(btn_layout)

    def create_table(self, change_data):
        """
        Creates a table widget to display change details in the confirmation dialog.
        """
        table = QTableWidget(1, 5)  # Single row, 5 columns
        table.setHorizontalHeaderLabels(["Pair", "Side", "Date", "Quantity", "Price"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        table.setEnabled(False)

        if change_data:
            row_color = green if change_data[1] == 'Buy' else red if change_data[1] == 'Sell' else None

            for i, value in enumerate(change_data, start=0):
                if i in [4, 5]:
                    item = DecimalTableWidgetItem(str(value))
                    table.setItem(0, i, DecimalTableWidgetItem(str(value)))
                else:
                    item = QTableWidgetItem(str(value))

                if row_color:
                    item.setBackground(row_color)

                table.setItem(0, i, item)
        else:
            for col in range(table.columnCount()):
                item = QTableWidgetItem()
                item.setBackground(light_gray)
                table.setItem(0, col, item)

        return table

    def get_result(self):
        """
        Returns True if the user accepted the dialog, False otherwise.
        """
        return self.exec() == QDialog.DialogCode.Accepted
