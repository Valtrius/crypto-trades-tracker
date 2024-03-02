import os
import json
from decimal_encoder import DecimalEncoder
from decimal import Decimal

CHANGE_LOG_FILE = 'ctt_change_log.json'


class ChangeLog:
    def __init__(self):
        self.changes = []

    def all_applied(self):
        return all(change.get('applied', False) for change in self.changes)

    def load(self, file_path):
        try:
            with open(CHANGE_LOG_FILE, 'r') as f:
                data = json.load(f)
                # Check if the specific file_path key exists in the data
                if file_path in data:
                    applied = True
                    # Process each change to convert specific columns to Decimal
                    for change in data[file_path]:
                        if 'new_data' in change and change['new_data'] is not None:
                            change['new_data'][4] = Decimal(change['new_data'][4])
                            change['new_data'][5] = Decimal(change['new_data'][5])
                        if 'original_data' in change and change['original_data'] is not None:
                            change['original_data'][4] = Decimal(change['original_data'][4])
                            change['original_data'][5] = Decimal(change['original_data'][5])
                        if 'applied' in change and change['applied'] is False:
                            applied = False
                    self.changes = data[file_path]

                    return applied
                else:
                    # If file_path is not in data, initialize it with an empty list
                    data[file_path] = []
                    self.changes = data[file_path]
                    # Save the updated data back to the file
                    with open(CHANGE_LOG_FILE, 'w') as fw:
                        json.dump(data, fw, indent=2, cls=DecimalEncoder)
        except FileNotFoundError:
            # If the file does not exist, create it with an empty list for file_path
            data = {file_path: []}
            with open(CHANGE_LOG_FILE, 'w') as f:
                json.dump(data, f, indent=2, cls=DecimalEncoder)
            self.changes = data[file_path]
        except json.JSONDecodeError:
            # Handle case where file is not valid JSON
            print(f"Error reading {CHANGE_LOG_FILE}. File is not valid JSON.")
            # Optionally, create/reset the file with empty data for file_path
            data = {file_path: []}
            with open(CHANGE_LOG_FILE, 'w') as f:
                json.dump(data, f, indent=2, cls=DecimalEncoder)
            self.changes = data[file_path]

        return True

    def add(self, file_path, change_type, original_data=None, new_data=None):
        self.changes.append({
            'change_type': change_type,
            'original_data': original_data,
            'new_data': new_data,
            'applied': False
        })
        self.write_changes(file_path)

    def write_changes(self, file_path):
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
        processed_data = original_data.copy()
        applied_changes = []

        for change in self.changes:
            if not change['applied']:
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

                if change_applied:
                    applied_changes.append(change)
            else:
                # Collect already applied changes in case they're needed for pruning
                applied_changes.append(change)

        # Prune to keep only the last 10 applied changes, maintaining all unapplied changes
        last_applied_changes = applied_changes[-10:]
        unapplied_changes = [change for change in self.changes if not change['applied']]
        self.changes = last_applied_changes + unapplied_changes

        self.write_changes(file_path)

        return processed_data

    def clear_not_applied(self, file_path):
        self.changes = [change for change in self.changes if change.get('applied', False)]
        self.write_changes(file_path)
