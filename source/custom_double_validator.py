from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import QLocale


class CustomDoubleValidator(QDoubleValidator):
    def __init__(self, bottom=float('-inf'), top=float('inf'), decimals=8, parent=None):
        """
        Initialize a custom double validator with optional bottom and top limits, decimals, and parent widget.
        """
        super().__init__(bottom, top, decimals, parent)
        self.setLocale(QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))

    def validate(self, input_str, pos):
        """
        Validate the input string by removing spaces and invoking the validation method of the parent class.
        """
        input_str_no_spaces = input_str.replace(" ", "")
        return super().validate(input_str_no_spaces, pos)
