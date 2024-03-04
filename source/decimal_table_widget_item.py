from decimal import Decimal
from PyQt6.QtWidgets import QTableWidgetItem


class DecimalTableWidgetItem(QTableWidgetItem):
    def __init__(self, value, *args, **kwargs):
        super().__init__(str(value), *args, **kwargs)
        self.value = Decimal(value)

    def __lt__(self, other):
        if isinstance(other, DecimalTableWidgetItem):
            return self.value < other.value
        return super().__lt__(other)
