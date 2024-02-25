import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter.ttk import Treeview
import json
from datetime import datetime


def load_data():
    file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if file_path:
        with open(file_path, 'r') as file:
            history_data = json.load(file)
            for row in history_data:
                # Convert 'quantity' and 'price' to floats before calculating 'value'
                quantity = float(row[-2])
                price = float(row[-1])
                value = round(quantity * price, 8)  # Recalculate 'value'
                # Append the calculated 'value' to the row data
                full_row = row + [value]
                history_table.insert('', 'end', values=full_row, tags=(row[1].lower(),))  # Adjust tag index based on your structure
            update_open_positions()


def save_data():
    file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
    if file_path:
        rows = history_table.get_children()
        # First, extract the data along with the row ID to preserve it for later reordering
        data_with_id = [(row, history_table.item(row)['values']) for row in rows]

        # Convert the date string to a datetime object for proper comparison, assuming the date is at index 2
        # Adjust the index if your date is in a different column
        data_with_id.sort(key=lambda x: datetime.strptime(x[1][2], '%Y-%m-%d'))

        # Exclude the last column (value) from each row and prepare the data to be saved
        data_to_save = [item[1][:-1] for item in data_with_id]

        with open(file_path, 'w') as file:
            json.dump(data_to_save, file)


def add_trade(trade_data=None, selected_item=None, index=None):
    trade_window = tk.Toplevel(root)
    trade_window.title("Edit Trade" if trade_data else "Add New Trade")
    trade_window.transient(root)
    trade_window.grab_set()
    trade_window.resizable(False, False)

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
            if selected_item:  # Indicates edit mode
                history_table.delete(selected_item)
                # Insert at the original position
                history_table.insert('', index, values=(pair, side, date, quantity, price, value), tags=(side.lower(),))
            else:
                # Add mode
                history_table.insert('', 'end', values=(pair, side, date, quantity, price, value), tags=(side.lower(),))
            trade_window.destroy()
            update_open_positions()
        except ValueError as e:
            messagebox.showerror("Validation Error", str(e))

    button_text = "Edit Trade" if trade_data else "Add Trade"
    add_button = tk.Button(trade_window, text=button_text, command=validate_and_save_trade)
    add_button.grid(row=len(labels) + 1, columnspan=3)


def delete_trade():
    selected_item = history_table.selection()
    if selected_item:
        if messagebox.askyesno("Delete Confirmation", "Are you sure you want to delete the selected trade?"):
            history_table.delete(selected_item)
            update_open_positions()


def update_open_positions():
    open_positions_table.delete(*open_positions_table.get_children())
    history = {}
    for row in history_table.get_children():
        pair, side, _, quantity, price, _ = history_table.item(row)['values']
        # Convert quantity and price to floats
        quantity = float(quantity)
        price = float(price)
        if pair not in history:
            history[pair] = []
        history[pair].append((side, quantity, price))

    for pair, trades in history.items():
        total_quantity, total_value = 0, 0
        for side, quantity, price in sorted(trades, key=lambda x: x[2]):  # Sort by date assumed as third element
            if side == 'Buy':
                total_quantity += quantity
                total_value += quantity * price
            else:
                total_quantity -= quantity
                total_value -= quantity * price
            if total_quantity == 0:
                total_value = 0

        if total_quantity > 0:
            average_price = total_value / total_quantity
            open_positions_table.insert('', 'end', values=(pair, round(total_quantity, 8), round(average_price, 8), round(total_quantity * average_price, 8)))


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
    treeview.heading(col, command=lambda col=col: sort_by_column(treeview, col, not descending))


root = tk.Tk()
root.title("Crypto Trades Tracker")

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
open_button = tk.Button(button_bar, text="Open", command=load_data)
save_button = tk.Button(button_bar, text="Save", command=save_data)
add_button = tk.Button(button_bar, text="+", command=add_trade)
open_button.pack(side="left")
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

# Bind double click to edit a trade
history_table.bind("<Double-1>", edit_trade)

# Add delete function to delete key press
root.bind("<Delete>", lambda e: delete_trade())

root.mainloop()
