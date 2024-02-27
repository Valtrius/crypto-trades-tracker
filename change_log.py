class ChangeLog:
    def __init__(self):
        self.changes = []  # List to store change records

    def add(self, change_type, original_data=None, new_data=None):
        self.changes.append({
            'change_type': change_type,
            'original_data': original_data,
            'new_data': new_data
        })

    def process(self, original_data):
        processed_data = original_data.copy()

        for change in self.changes:
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

        return processed_data

    def clear(self):
        self.changes = []

    def get_last(self):
        return self.changes[-1]

    def get_log(self):
        return self.changes

    def remove_last(self):
        self.changes.pop()

    def restore(self, log):
        self.changes = log
