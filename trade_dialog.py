from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, QRadioButton, QPushButton, QMessageBox
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
import uuid


class TradeDialog(QDialog):
    def __init__(self, parent=None, pair=None, trade_data=None, uuid=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Trade" if trade_data else "Add New Trade")
        self.setModal(True)
        self.resize(320, 180)  # Adjust size as needed

        self.pair = pair
        self.trade_data = trade_data
        self.new_data = None
        self.uuid = uuid

        # Initialize UI components
        self.init_ui()

        # Center the dialog relative to its parent
        self.center_trade_window()

        # Make the window non-resizable
        self.setFixedSize(self.size())

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Form layout for labels and entries
        form_layout = QGridLayout()
        labels = ['Pair', 'Date', 'Quantity', 'Price']
        self.entries = {}
        self.side_var = 'Buy' if not self.trade_data else self.trade_data[1]

        for i, label in enumerate(labels):
            form_layout.addWidget(QLabel(label), i, 0)
            entry = QLineEdit(self)
            form_layout.addWidget(entry, i, 1)
            if self.trade_data:
                entry.setText(self.trade_data[i + 1] if label != 'Pair' else self.trade_data[0])
            elif self.pair and label == 'Pair':
                entry.setText(self.pair)
            self.entries[label] = entry

        # Set focus on the QLineEdit associated with the next label
        if self.pair:
            pair_index = labels.index('Pair')
            next_label = labels[pair_index + 1] if pair_index + 1 < len(labels) else None
            if next_label:
                self.entries[next_label].setFocus()

        layout.addLayout(form_layout)

        # Radio buttons for Side
        side_layout = QHBoxLayout()
        self.buy_button = QRadioButton("Buy")
        self.sell_button = QRadioButton("Sell")
        self.buy_button.setChecked(self.side_var == 'Buy')
        self.sell_button.setChecked(self.side_var == 'Sell')
        side_layout.addWidget(QLabel('Side'))
        side_layout.addWidget(self.buy_button)
        side_layout.addWidget(self.sell_button)
        layout.addLayout(side_layout)

        # Buttons for save and cancel
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.validate_and_save_trade)
        button_layout.addWidget(save_button)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.close)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

    def center_trade_window(self):
        if self.parent():
            parent_geometry = self.parent().geometry()
            self.move(parent_geometry.center() - self.rect().center())

    def validate_and_save_trade(self):
        try:
            trade_id = str(uuid.uuid4()) if not self.uuid else self.uuid
            pair = self.entries['Pair'].text().upper()
            side = 'Buy' if self.buy_button.isChecked() else 'Sell'
            date = self.entries['Date'].text()
            datetime.strptime(date.replace(" ", ""), '%Y-%m-%d')  # Validates date format
            quantity = Decimal(self.entries['Quantity'].text().replace(" ", ""))
            price = Decimal(self.entries['Price'].text().replace(" ", ""))

            self.new_data = [trade_id, pair, side, date, quantity, price]

            self.accept()  # Close the dialog successfully
        except ValueError as e:
            QMessageBox.critical(self, "Validation Error", str(e))
