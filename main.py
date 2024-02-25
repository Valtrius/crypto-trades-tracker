import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter.ttk import Treeview
import json
from datetime import datetime

# Initialize a list to store all history data
full_history_data = []


def load_data():
    global full_history_data
    file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if file_path:
        with open(file_path, 'r') as file:
            full_history_data = json.load(file)
            history_table.delete(*history_table.get_children())  # Clear existing entries
            for row in full_history_data:
                # Assuming 'quantity' and 'price' are at specific indices
                quantity = float(row[3])  # Adjust index based on your data structure
                price = float(row[4])  # Adjust index based on your data structure
                value = round(quantity * price, 8)
                row.append(value)  # Append calculated value
                history_table.insert('', 'end', values=row, tags=(row[1].lower(),))
            update_open_positions()


def save_data():
    file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
    if file_path:
        # Exclude the last column (value) when saving
        data_to_save = [row[:-1] for row in full_history_data]
        with open(file_path, 'w') as file:
            json.dump(data_to_save, file)


def add_trade(trade_data=None, selected_item=None, index=None):
    trade_window = tk.Toplevel(root)
    trade_window.title("Edit Trade" if trade_data else "Add New Trade")
    trade_window.transient(root)
    trade_window.grab_set()
    trade_window.resizable(False, False)

    # Function to center the trade_window relative to its parent
    def center_trade_window():
        trade_window.update_idletasks()  # Update "requested size" from geometry manager
        width = trade_window.winfo_width()
        height = trade_window.winfo_height()
        # Get parent window size and position
        parent_x = root.winfo_x()
        parent_y = root.winfo_y()
        parent_width = root.winfo_width()
        parent_height = root.winfo_height()
        # Calculate position relative to parent
        x = parent_x + (parent_width // 2) - (width // 2)
        y = parent_y + (parent_height // 2) - (height // 2)
        trade_window.geometry('+{}+{}'.format(x, y))

    # Call the function to center the trade_window
    center_trade_window()

    # Adjusted labels to exclude 'Side' because it's handled separately by radio buttons
    labels = ['Pair', 'Date', 'Quantity', 'Price']
    entries = {}
    side_var = tk.StringVar(value=trade_data[1] if trade_data else 'Buy')

    for i, label in enumerate(labels):
        tk.Label(trade_window, text=label).grid(row=i, column=0)
        entry = tk.Entry(trade_window)
        entry.grid(row=i, column=1)
        # Skip index 1 ('Side') if editing existing trade data
        if trade_data:
            # Adjusting for the difference in indices due to 'Side' being a radio button
            entry.insert(0, trade_data[i + 1] if label != 'Pair' else trade_data[0])
        entries[label] = entry

    # Radio buttons for Side
    tk.Label(trade_window, text='Side').grid(row=len(labels), column=0)
    tk.Radiobutton(trade_window, text='Buy', variable=side_var, value='Buy').grid(row=len(labels), column=1)
    tk.Radiobutton(trade_window, text='Sell', variable=side_var, value='Sell').grid(row=len(labels), column=2)
    if trade_data:
        side_var.set(trade_data[1])  # Set radio button value

    def validate_and_save_trade():
        try:
            pair = entries['Pair'].get().upper()
            side = side_var.get()  # Get the value from radio button
            date = entries['Date'].get()
            datetime.strptime(date, '%Y-%m-%d')  # Validates date format
            quantity = float(entries['Quantity'].get())
            price = float(entries['Price'].get())
            value = round(quantity * price, 8)
            new_row = [pair, side, date, quantity, price, value]
            if selected_item:  # Indicates edit mode
                # Find and replace the item in full_history_data
                index = history_table.index(selected_item)
                full_history_data[index] = new_row[:-1]  # Exclude calculated value
            else:
                # Add mode
                full_history_data.append(new_row[:-1])  # Exclude calculated value
            # Refresh the Treeview based on full_history_data
            filter_history('All')  # Or apply the current filter if implemented
        except ValueError as e:
            messagebox.showerror("Validation Error", str(e))

    button_text = "Edit Trade" if trade_data else "Add Trade"
    add_button = tk.Button(trade_window, text=button_text, command=validate_and_save_trade)
    add_button.grid(row=len(labels) + 1, columnspan=3)


def delete_trade():
    selected_items = history_table.selection()
    if selected_items:
        response = messagebox.askyesno("Delete Confirmation", "Are you sure you want to delete the selected trade(s)?")
        if response:
            for selected_item in selected_items:
                # Find the item in full_history_data by matching it with the values in the selected row
                values = history_table.item(selected_item)['values']
                # Assuming the 'date' and 'pair' uniquely identify a trade, adjust as necessary
                pair, side, date, quantity, price = values[0], values[1], values[2], values[3], values[4]
                full_history_data[:] = [row for row in full_history_data if not (row[0] == pair and row[1] == side and row[2] == date and row[3] == quantity and row[3] == price)]
                # Now delete from the Treeview
                history_table.delete(selected_item)
            update_open_positions()


def update_open_positions():
    open_positions_table.delete(*open_positions_table.get_children())
    history = {}

    for row in history_table.get_children():
        row_data = history_table.item(row)['values']

        # Check if the row data matches the expected format
        if len(row_data) == 6:
            pair, side, _, quantity, price, _ = row_data
            # Convert quantity and price to floats
            quantity = float(quantity)
            price = float(price)
            if pair not in history:
                history[pair] = []
            history[pair].append((side, quantity, price))

    for pair, trades in history.items():
        total_quantity, total_value = 0, 0
        for side, quantity, price in trades:  # Assuming sorting by date is handled elsewhere or not needed here
            if side.lower() == 'buy':
                total_quantity += quantity
                total_value += quantity * price
            elif side.lower() == 'sell':
                total_quantity -= quantity
                total_value -= quantity * price

        if total_quantity > 0:
            average_price = total_value / total_quantity
            open_positions_table.insert('', 'end', values=(
                pair, round(total_quantity, 8), round(average_price, 8), round(total_quantity * average_price, 8)))


def edit_trade(event):
    if not history_table.selection():
        return
    selected_item = history_table.selection()[0]
    # Find the index of the selected item
    index = history_table.index(selected_item)
    trade_data = history_table.item(selected_item)['values']
    # Pass both selected_item and its index to add_trade
    add_trade(trade_data, selected_item, index)


def sort_by_column(treeview, col, descending):
    """Sort tree view contents when a column header is clicked on."""
    # Retrieve data from the column
    data_list = [(treeview.set(child_id, col), child_id) for child_id in treeview.get_children('')]
    # Sort the data
    data_list.sort(reverse=descending)

    for index, (data, child_id) in enumerate(data_list):
        treeview.move(child_id, '', index)

    # Switch the heading so that it will sort in the opposite direction
    treeview.heading(col, command=lambda _col=col: sort_by_column(treeview, _col, not descending))


def show_filter_menu(event):
    # Clear the existing menu
    filter_menu.delete(0, tk.END)
    filter_menu.add_command(label="All", command=lambda: filter_history('All'))

    # Find unique pairs in the full history data
    unique_pairs = set(item[0] for item in full_history_data)

    for pair in sorted(unique_pairs):
        filter_menu.add_command(label=pair, command=lambda p=pair: filter_history(p))

    # Show the menu at the cursor's position
    filter_menu.post(event.x_root, event.y_root)


def filter_history(selected_pair):
    # Clear the current view
    for child in history_table.get_children():
        history_table.delete(child)

    # Apply filter
    if selected_pair == 'All':
        filtered_data = full_history_data
    else:
        filtered_data = [item for item in full_history_data if item[0] == selected_pair]

    # Repopulate the Treeview with filtered data
    for item in filtered_data:
        # Assuming 'side' is at a specific index, adjust based on your data structure
        side = item[1].lower()  # This should be 'buy' or 'sell', adjust the index as necessary
        # Calculate 'value' if necessary or use existing value
        quantity, price = float(item[3]), float(item[4])  # Adjust index based on your data structure
        value = round(quantity * price, 8)
        full_row = item + [value]  # Adjust as necessary if 'value' is already included
        # Insert row with appropriate tag for coloring
        history_table.insert('', 'end', values=full_row, tags=(side,))

    # Reapply tag configurations for background colors
    history_table.tag_configure('buy', background='pale green')
    history_table.tag_configure('sell', background='light coral')


# Function to center the window on the screen with a specified size
def center_window(window, width, height):
    # Set initial size
    window.geometry('{}x{}'.format(width, height))

    window.update_idletasks()  # Update "requested size" from geometry manager

    # Calculate center position
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)

    # Apply the calculated position
    window.geometry('+{}+{}'.format(x, y))


root = tk.Tk()
root.title("Crypto Trades Tracker")

# Specify desired initial size
initial_width = 1280
initial_height = 720

# Use the function to center the main window with the specified size
center_window(root, initial_width, initial_height)

# Configure the root window's grid
root.columnconfigure(0, weight=1)
root.rowconfigure(1, weight=1)  # Adjust for the button bar and labels

# Create frames for the button bar and tables
button_bar = tk.Frame(root)
button_bar.grid(row=0, column=0, columnspan=2, sticky="ew")

# Create separate frames for each table
left_frame = tk.Frame(root)
right_frame = tk.Frame(root)
left_frame.grid(row=1, column=0, sticky="nsew")
right_frame.grid(row=1, column=1, sticky="nsew")

# Configure grid weights for resizing
root.columnconfigure(1, weight=1)
left_frame.columnconfigure(0, weight=1)
left_frame.rowconfigure(1, weight=1)
right_frame.columnconfigure(0, weight=1)
right_frame.rowconfigure(1, weight=1)

# Button bar setup
load_button = tk.Button(button_bar, text="Load", command=load_data)
save_button = tk.Button(button_bar, text="Save", command=save_data)
add_button = tk.Button(button_bar, text="+", command=add_trade)
load_button.pack(side="left")
save_button.pack(side="left")
add_button.pack(side="left")

# OPEN POSITIONS table setup
open_positions_label = tk.Label(left_frame, text="OPEN POSITIONS")
open_positions_label.pack(fill="x")
open_positions_table = Treeview(left_frame, columns=("pair", "quantity", "average_price", "value"), show='headings')
open_positions_table.heading("pair", text="Pair")
open_positions_table.heading("quantity", text="Quantity")
open_positions_table.heading("average_price", text="Average Price")
open_positions_table.heading("value", text="Value")
open_positions_table.pack(fill="both", expand=True)
# Set initial width and enable stretching for each column
for col in open_positions_table['columns']:
    open_positions_table.heading(col, text=col.capitalize(), command=lambda _col=col: sort_by_column(open_positions_table, _col, False))
    open_positions_table.column(col, width=100, stretch=tk.YES)

# HISTORY table setup
history_label = tk.Label(right_frame, text="HISTORY")
history_label.pack(fill="x")
history_table = Treeview(right_frame, columns=("pair", "side", "date", "quantity", "price", "value"), show='headings')
history_table.heading("pair", text="Pair")
history_table.heading("side", text="Side")
history_table.heading("date", text="Date")
history_table.heading("quantity", text="Quantity")
history_table.heading("price", text="Price")
history_table.heading("value", text="Value")
history_table.tag_configure('buy', background='pale green')
history_table.tag_configure('sell', background='light coral')
history_table.pack(fill="both", expand=True)

for col in history_table['columns']:
    history_table.heading(col, text=col.capitalize(), command=lambda _col=col: sort_by_column(history_table, _col, False))
    history_table.column(col, width=100, stretch=tk.YES)

# Create a popup menu for filtering by pair
filter_menu = tk.Menu(root, tearoff=0)
filter_menu.add_command(label="All", command=lambda: filter_history('All'))

# Bind double click to edit a trade
history_table.bind("<Double-1>", edit_trade)

# Bind right-click on the history table to show the filter menu
history_table.bind("<Button-3>", lambda event: show_filter_menu(event))

# Add delete function to delete key press
root.bind("<Delete>", lambda e: delete_trade())

root.mainloop()
