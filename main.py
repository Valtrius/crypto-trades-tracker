import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter.ttk import Treeview
from tkinter import font as tkFont
import json
from datetime import datetime
import uuid
from decimal import Decimal, ROUND_HALF_UP

# Set the desired precision: 8 decimal places
decimal_places = Decimal('1E-8')
# Initialize a list to store all history data
full_history_data = []
# Dictionary to map Treeview item IDs to trade unique IDs
treeview_id_to_trade_id = {}

# Assign identifiers to each Treeview
open_positions_table_id = 'open_positions_table'
history_table_id = 'history_table'

# Dictionaries to remember the sort and filter state of each table
sort_filter_states = {
    open_positions_table_id: {'col': 'pair', 'order': False, 'filter': "All"},
    history_table_id: {'col': 'pair', 'order': False, 'filter': "All"}
}


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)  # Convert Decimal to string
        # Let the base class default method raise the TypeError
        return super(DecimalEncoder, self).default(obj)


def load_data(file_path=None):
    if file_path is None:
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if file_path:
        try:
            with open(file_path, 'r') as file:
                global full_history_data
                data = json.load(file)
                # Convert specific fields back to Decimal
                for row in data:
                    row[4] = Decimal(row[4])  # Assuming quantity is at index 4
                    row[5] = Decimal(row[5])  # Assuming price is at index 5
                full_history_data = data
                filter_history('All')
                update_open_positions()
                save_last_used_file_path(file_path)
                # Sort again
                sort_by_column(history_table, sort_filter_states[history_table_id]['col'], sort_filter_states[history_table_id]['order'], history_table_id)
        except Exception as e:
            print("Error loading file:", e)


def save_data():
    file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
    if file_path:
        with open(file_path, 'w') as file:
            json.dump(full_history_data, file, cls=DecimalEncoder)  # Use the custom encoder
            save_last_used_file_path(file_path)


def add_trade(trade_data=None, selected_item=None):
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

    selected_open_position = open_positions_table.selection()
    prefill_pair = None
    if selected_open_position:
        # The first column in the open positions table is 'pair'
        prefill_pair = open_positions_table.item(selected_open_position[0])['values'][0]

    for i, label in enumerate(labels):
        tk.Label(trade_window, text=label).grid(row=i, column=0)
        entry = tk.Entry(trade_window)
        entry.grid(row=i, column=1)
        if prefill_pair and label == 'Pair':
            entry.insert(0, prefill_pair)
        elif trade_data:
            # Adjusting for the difference in indices due to 'Side' being a radio button
            entry.insert(0, trade_data[i + 1] if label != 'Pair' else trade_data[0])
        entries[label] = entry

    if prefill_pair:
        # Set focus to the 'Date' entry if 'Pair' was pre-filled
        entries['Date'].focus_set()
    else:
        # Otherwise, focus on the 'Pair' entry
        entries['Pair'].focus_set()

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
            datetime.strptime(date.replace(" ", ""), '%Y-%m-%d')  # Validates date format
            quantity = Decimal(entries['Quantity'].get().replace(" ", ""))
            price = Decimal(entries['Price'].get().replace(" ", ""))
            value = (quantity * price).quantize(decimal_places, ROUND_HALF_UP)
            trade_id = str(uuid.uuid4()) if not selected_item else treeview_id_to_trade_id[selected_item]
            new_row = [trade_id, pair, side, date, quantity, price, value]
            if selected_item:  # Indicates edit mode
                history_table.item(selected_item, values=new_row[1:])
                # Update the corresponding entry in full_history_data
                for i, row in enumerate(full_history_data):
                    if trade_id == row[0]:
                        full_history_data[i] = new_row[:-1]
                        break
            else:
                # Add mode
                full_history_data.append(new_row[:-1])  # Exclude calculated value

            filter_history(sort_filter_states[history_table_id]['filter'])  # Apply the current filter if implemented
            trade_window.destroy()
            update_open_positions()  # Refresh the Treeview based on full_history_data
            # Sort again
            sort_by_column(history_table, sort_filter_states[history_table_id]['col'], sort_filter_states[history_table_id]['order'], history_table_id)
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
                # Get the trade_id of the selected item
                trade_id = treeview_id_to_trade_id[selected_item]
                # Remove the trade from full_history_data based on trade_id
                full_history_data[:] = [row for row in full_history_data if row[0] != trade_id]
                # Now delete from the Treeview
                history_table.delete(selected_item)
            update_open_positions()

            # Sort again
            sort_by_column(history_table, sort_filter_states[history_table_id]['col'], sort_filter_states[history_table_id]['order'], history_table_id)


def update_open_positions():
    # Sort full_history_data by date (assuming date is at index 3)
    sorted_history_data = sorted(full_history_data, key=lambda x: datetime.strptime(x[3], '%Y-%m-%d'))

    open_positions_table.delete(*open_positions_table.get_children())
    history = {}

    for row in sorted_history_data:
        # Assuming the format is [trade_id, pair, side, date, quantity, price]
        _, pair, side, _, quantity, price = row
        quantity = Decimal(str(quantity))
        price = Decimal(str(price))

        if pair not in history:
            history[pair] = {'trades': [], 'total_pnl': Decimal('0'), 'total_quantity': Decimal('0'), 'total_value': Decimal('0')}

        # Accumulate quantity and value for buy trades to calculate average buy price
        if side.lower() == 'buy':
            history[pair]['total_quantity'] += quantity
            history[pair]['total_value'] += quantity * price
        elif side.lower() == 'sell' and history[pair]['total_quantity'] > 0:
            # Calculate PnL based on the difference from the average buy price
            average_buy_price = (history[pair]['total_value'] / history[pair]['total_quantity']).quantize(decimal_places, ROUND_HALF_UP)
            pnl = ((price - average_buy_price) * quantity).quantize(decimal_places, ROUND_HALF_UP)
            history[pair]['total_pnl'] += pnl
            # Adjust total quantity and value after sell
            history[pair]['total_quantity'] -= quantity
            # Optionally adjust total_value if you want to track value after sells
            history[pair]['total_value'] -= quantity * average_buy_price

    for pair, info in history.items():
        total_quantity = info['total_quantity']
        if total_quantity > Decimal('0'):
            average_price = info['total_value'] / total_quantity
            open_positions_table.insert('', 'end', values=(pair, total_quantity, average_price.quantize(decimal_places, ROUND_HALF_UP), info['total_value'].quantize(decimal_places, ROUND_HALF_UP), info['total_pnl']))
        else:
            # If there's no open position, show '-' in quantity, average price, and value columns, but still show the total PnL
            open_positions_table.insert('', 'end', values=(pair, '-', '-', '-', info['total_pnl']))

    # Sort again
    if sort_filter_states[open_positions_table_id]['col']:
        sort_by_column(open_positions_table, sort_filter_states[open_positions_table_id]['col'], sort_filter_states[open_positions_table_id]['order'], open_positions_table_id)


def edit_trade(event):
    if not history_table.selection():
        return
    selected_item = history_table.selection()[0]
    trade_data = history_table.item(selected_item)['values']
    add_trade(trade_data, selected_item)

    # Sort again
    if sort_filter_states[open_positions_table_id]['col']:
        sort_by_column(open_positions_table, sort_filter_states[open_positions_table_id]['col'], sort_filter_states[open_positions_table_id]['order'], open_positions_table_id)


def sort_by_column(treeview, col, descending, treeview_id):
    """Sort tree view contents when a column header is clicked on."""
    # Update the sort state for this specific treeview
    sort_filter_states[treeview_id]['col'] = col
    sort_filter_states[treeview_id]['order'] = descending

    # Retrieve data from the column
    data_list = [(treeview.set(child_id, col), child_id) for child_id in treeview.get_children('')]
    # If the data to be sorted is numeric, we convert it to a float for sorting
    try:
        data_list.sort(key=lambda t: float(t[0]), reverse=descending)
    except ValueError:
        # If conversion to float fails, sort as strings
        data_list.sort(reverse=descending)

    for index, (data, child_id) in enumerate(data_list):
        treeview.move(child_id, '', index)

    # Switch the heading so that it will sort in the opposite direction
    treeview.heading(col, command=lambda _col=col: sort_by_column(treeview, _col, not descending, treeview_id))

    # Update the headings on all columns
    for column in treeview["columns"]:
        if column == col:
            # Update the heading of the sorted column to include an arrow
            heading_text = col.replace('_', ' ').title()
            if descending:
                heading_text += ' \u25BC'  # Downward arrow symbol
            else:
                heading_text += ' \u25B2'  # Upward arrow symbol
            treeview.heading(column, text=heading_text, command=lambda _col=column: sort_by_column(treeview, _col, not descending, treeview_id))
        else:
            # Reset the heading text for all other columns to remove arrows
            heading_text = column.replace('_', ' ').title()
            treeview.heading(column, text=heading_text, command=lambda _col=column: sort_by_column(treeview, _col, True, treeview_id))


def show_filter_menu(event):
    # Clear the existing menu
    filter_menu.delete(0, tk.END)
    filter_menu.add_command(label="All", command=lambda: filter_history('All'))

    # Find unique pairs in the full history data
    unique_pairs = set(item[1] for item in full_history_data)

    for pair in sorted(unique_pairs):
        filter_menu.add_command(label=pair, command=lambda p=pair: filter_history(p))

    # Show the menu at the cursor's position
    filter_menu.post(event.x_root, event.y_root)


def filter_history(selected_pair):
    global treeview_id_to_trade_id

    # Clear the current view
    for child in history_table.get_children():
        history_table.delete(child)

    treeview_id_to_trade_id = {}

    # Apply filter
    if selected_pair == 'All':
        filtered_data = full_history_data
    else:
        filtered_data = [item for item in full_history_data if item[1] == selected_pair]

    # Repopulate the Treeview with filtered data
    for item in filtered_data:
        # Assuming 'side' is at a specific index, adjust based on your data structure
        side = item[2].lower()  # This should be 'buy' or 'sell', adjust the index as necessary
        # Calculate 'value' if necessary or use existing value
        quantity, price = Decimal(str(item[4])), Decimal(str(item[5]))  # Adjust index based on your data structure
        value = (quantity * price).quantize(decimal_places, ROUND_HALF_UP)
        full_row = item + [value]  # Adjust as necessary if 'value' is already included
        # Insert row with appropriate tag for coloring
        item_id = history_table.insert('', 'end', values=full_row[1:], tags=(side,))
        treeview_id_to_trade_id[item_id] = item[0]  # Map Treeview item ID to trade ID

    # Reapply tag configurations for background colors
    history_table.tag_configure('buy', background='pale green')
    history_table.tag_configure('sell', background='light coral')

    sort_filter_states[history_table_id]['filter'] = selected_pair


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


def deselect_all(event):
    # Deselect all lines in open_positions_table
    for item in open_positions_table.selection():
        open_positions_table.selection_remove(item)

    # Deselect all lines in history_table
    for item in history_table.selection():
        history_table.selection_remove(item)


def save_last_used_file_path(file_path):
    with open('last_file.txt', 'w') as f:
        f.write(file_path)


def load_last_used_file():
    try:
        with open('last_file.txt', 'r') as f:
            file_path = f.read().strip()
            if file_path:
                load_data(file_path)
    except Exception as e:
        print("Error loading last used file:", e)


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
open_positions_label = tk.Label(left_frame, text="OPEN POSITIONS", font=tkFont.Font(weight="bold"))
open_positions_label.pack(fill="x")
open_positions_table = Treeview(left_frame, columns=("pair", "quantity", "average_price", "value", "pnl"), show='headings', name=open_positions_table_id)
open_positions_table.heading("pair", text="Pair")
open_positions_table.heading("quantity", text="Quantity")
open_positions_table.heading("average_price", text="Average Price")
open_positions_table.heading("value", text="Value")
open_positions_table.heading("pnl", text="PnL")
# Set initial width and enable stretching for each column
for col in open_positions_table['columns']:
    open_positions_table.heading(col, command=lambda _col=col: sort_by_column(open_positions_table, _col, False, open_positions_table_id))
    open_positions_table.column(col, width=100, stretch=tk.YES)
# Create a vertical scrollbar for the open_positions_table
open_positions_vscroll = tk.Scrollbar(left_frame, orient="vertical", command=open_positions_table.yview)
open_positions_vscroll.pack(side="right", fill="y")
# Configure the treeview to update the scrollbar
open_positions_table.configure(yscrollcommand=open_positions_vscroll.set)
open_positions_table.pack(fill="both", expand=True)

# HISTORY table setup
history_label = tk.Label(right_frame, text="HISTORY", font=tkFont.Font(weight="bold"))
history_label.pack(fill="x")
history_table = Treeview(right_frame, columns=("pair", "side", "date", "quantity", "price", "value"), show='headings', name=history_table_id)
history_table.heading("pair", text="Pair")
history_table.heading("side", text="Side")
history_table.heading("date", text="Date")
history_table.heading("quantity", text="Quantity")
history_table.heading("price", text="Price")
history_table.heading("value", text="Value")
history_table.tag_configure('buy', background='pale green')
history_table.tag_configure('sell', background='light coral')
# Set initial width and enable stretching for each column
for col in history_table['columns']:
    history_table.heading(col, command=lambda _col=col: sort_by_column(history_table, _col, False, history_table_id))
    history_table.column(col, width=100, stretch=tk.YES)
# Create a vertical scrollbar for the history_table
history_vscroll = tk.Scrollbar(right_frame, orient="vertical", command=history_table.yview)
history_vscroll.pack(side="right", fill="y")
# Configure the treeview to update the scrollbar
history_table.configure(yscrollcommand=history_vscroll.set)
history_table.pack(fill="both", expand=True)

# Create a popup menu for filtering by pair
filter_menu = tk.Menu(root, tearoff=0)
filter_menu.add_command(label="All", command=lambda: filter_history('All'))

# Bind double click to edit a trade
history_table.bind("<Double-1>", edit_trade)

# Bind right-click on the history table to show the filter menu
history_table.bind("<Button-3>", lambda event: show_filter_menu(event))

# Add delete function to delete key press
root.bind("<Delete>", lambda e: delete_trade())

# Bind the Escape key to the deselect_all function
root.bind('<Escape>', deselect_all)

load_last_used_file()  # Automatically load the last used file

root.mainloop()
