from decimal import Decimal
from PyQt6.QtWidgets import QTableWidgetItem


class DecimalTableWidgetItem(QTableWidgetItem):
    def __init__(self, value, *args, **kwargs):
        """
        Initialize the DecimalTableWidgetItem with the string representation of the given value, and store the Decimal value separately.
        """
        super().__init__(str(value), *args, **kwargs)
        self.value = Decimal(value)

    def __lt__(self, other):
        """
        Override the less than comparison method (__lt__) to compare DecimalTableWidgetItem objects based on their Decimal values.
        """
        if isinstance(other, DecimalTableWidgetItem):
            return self.value < other.value
        return super().__lt__(other)
