import json
from decimal_encoder import DecimalEncoder
from decimal import Decimal

CHANGE_LOG_FILE = 'ctt_change_log.json'
CHANGE_LOG_VERSION = '1'


class ChangeLog:
    def __init__(self):
        """
        Initializes the object with an empty list to track changes.
        """
        self.changes = []

    def all_applied(self):
        """
        Determines if all changes in the list have been applied and not undone, returning True if so.
        """
        return all(change.get('applied', True) != change.get('undone', True) for change in self.changes)

    def load(self, file_path):
        """
        Loads change log data from a file, handling version compatibility and data integrity, and initializes changes for the specific file path, creating or resetting the file if necessary.
        """
        try:
            with open(CHANGE_LOG_FILE, 'r') as f:
                data = json.load(f)
                # If version isn't correct, erase file and start from scratch, it doesn't matter for change log
                if 'version' in data and data['version'] != CHANGE_LOG_VERSION:
                    self.create_new_file(file_path)
                elif 'version' not in data:
                    data['version'] = CHANGE_LOG_VERSION

                # Check if the specific file_path key exists in the data
                if file_path in data:
                    # Process each change to convert specific columns to Decimal
                    for change in data[file_path]:
                        if 'new_data' in change and change['new_data'] is not None:
                            change['new_data'][4] = Decimal(change['new_data'][4])
                            change['new_data'][5] = Decimal(change['new_data'][5])
                        if 'original_data' in change and change['original_data'] is not None:
                            change['original_data'][4] = Decimal(change['original_data'][4])
                            change['original_data'][5] = Decimal(change['original_data'][5])
                    self.changes = data[file_path]
                else:
                    # If file_path is not in data, initialize it with an empty list
                    data[file_path] = []
                    self.changes = data[file_path]
                    # Save the updated data back to the file
                    with open(CHANGE_LOG_FILE, 'w') as fw:
                        json.dump(data, fw, indent=2, cls=DecimalEncoder)
        except FileNotFoundError:
            # If the file does not exist, create it with an empty list for file_path
            self.create_new_file(file_path)
        except json.JSONDecodeError:
            # Handle case where file is not valid JSON
            print(f"Error reading {CHANGE_LOG_FILE}. File is not valid JSON.")
            # Reset the file with empty data for file_path
            self.create_new_file(file_path)

    def create_new_file(self, file_path):
        """
        Creates a new change log file with the current version and an empty list of changes for the given file path.
        """
        data = {"version": CHANGE_LOG_VERSION, file_path: []}
        with open(CHANGE_LOG_FILE, 'w') as f:
            json.dump(data, f, indent=2, cls=DecimalEncoder)
        self.changes = data[file_path]

    def add(self, file_path, change_type, original_data=None, new_data=None):
        """
        Adds a new change to the change log, removing any undone changes, and saves the updated log for the given file path.
        """
        self.changes = [change for change in self.changes if not change['undone']]
        self.changes.append({
            'change_type': change_type,
            'original_data': original_data,
            'new_data': new_data,
            'applied': False,
            'undone': False
        })
        self.write_changes(file_path)

    def write_changes(self, file_path):
        """
        Writes the changes in the change log to a JSON file, storing them under the specified file path.
        """
        try:
            with open(CHANGE_LOG_FILE, 'r') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Initialize an empty dictionary if the file does not exist or contains invalid JSON
            data = {}

        # Assign the current state of self.changes to the specified file_path key
        data[file_path] = self.changes

        # Write the updated data back to CHANGE_LOG_FILE
        with open(CHANGE_LOG_FILE, 'w') as f:
            json.dump(data, f, indent=2, cls=DecimalEncoder)

    def process(self, file_path, original_data, change_applied=False):
        """
        Processes the original data according to the changes recorded in the change log,
        applying, unapplying, and pruning changes as necessary, and returns the processed data.
        """
        processed_data = original_data.copy()
        applied_changes = []

        for change in self.changes:
            # Not applied and not undone -> apply them
            if not change['applied'] and not change['undone']:
                change_type = change['change_type']
                original = change['original_data']
                new = change['new_data']

                if change_type == 'add':
                    # For 'add', append the new data to the processed list
                    processed_data.append(new)
                elif change_type == 'edit':
                    # For 'edit', find the original data in the list and replace it with the new data
                    for i, record in enumerate(processed_data):
                        if record[0] == original[0]:  # The first element is a unique identifier, like UUID
                            processed_data[i] = new
                            break
                elif change_type == 'delete':
                    # For 'delete', remove the original data from the list
                    processed_data = [record for record in processed_data if record[0] != original[0]]

                change['applied'] = change_applied

            # Applied and not undone -> pruning
            elif change['applied'] and not change['undone']:
                applied_changes.append(change)

            # Applied and undone -> unapply
            elif change['applied'] and change['undone']:
                change['applied'] = False

            # Not applied and undone -> do nothing

        # Prune to keep only the last 10 applied changes, maintaining all unapplied changes
        last_applied_changes = applied_changes[-10:]
        unapplied_changes = [change for change in self.changes if not change['applied']]
        self.changes = last_applied_changes + unapplied_changes

        self.write_changes(file_path)

        return processed_data

    def clear_not_applied(self, file_path):
        """
        Clears all unapplied changes in the change log for the specified file path.
        """
        for change in self.changes:
            if not change.get('applied', False):
                change['undone'] = True
        self.write_changes(file_path)

    def get_last_to_undo(self):
        """
        Returns the last change in the change log that has not been undone, which can be undone.
        """
        # Iterate through self.changes in reverse to find the last change that has not been undone
        for change in reversed(self.changes):
            if not change.get('undone', False):
                return change
        return None

    def get_next_to_redo(self):
        """
        Returns the next change in the change log that has been undone, which can be redone.
        """
        # Iterate through self.changes to find the last change that has been undone
        for change in self.changes:
            if change.get('undone', True):
                return change
        return None

    def undo(self):
        """
        Marks the last change in the change log that has not been undone as undone.
        """
        last_change_to_undo = self.get_last_to_undo()
        if last_change_to_undo is not None:
            last_change_to_undo['undone'] = True

    def redo(self):
        """
        Marks the last change in the change log that has been undone as not undone, effectively redoing the change.
        """
        last_change_to_undo = self.get_next_to_redo()
        if last_change_to_undo is not None:
            last_change_to_undo['undone'] = False
