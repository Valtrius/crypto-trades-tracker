from PyQt6.QtGui import QDoubleValidator, QValidator
from PyQt6.QtCore import QLocale


class CustomDoubleValidator(QDoubleValidator):
    def __init__(self, bottom=float('-inf'), top=float('inf'), decimals=2, parent=None):
        super().__init__(bottom, top, decimals, parent)
        self.setLocale(QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))

    def validate(self, input_str, pos):
        # Strip spaces for the purpose of validation
        input_str_no_spaces = input_str.replace(" ", "")
        return super().validate(input_str_no_spaces, pos)
