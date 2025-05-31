import os
import logging
from pathlib import Path
from typing import Any
import tkinter as tk
from tkinter import filedialog, messagebox, Toplevel, ttk
import pandas as pd
from PIL import Image, ImageTk
import ttkbootstrap as ttk
from ttkbootstrap.tableview import Tableview
from ttkbootstrap.constants import *
import sqlite3
import bcrypt
from tkinter import PhotoImage
from ej import load_logs, process_transactions, merge_files, save_to_csv, is_trial_active, read_value_from_file

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ------------------ DATABASE FUNCTIONS ------------------
def initialize_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user'
        )
    ''')
    conn.commit()
    conn.close()

def register_user(username, password, role='user'):
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', (username, hashed_password, role))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def authenticate_user(username, password):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT password, role FROM users WHERE username = ?', (username,))
    result = cursor.fetchone()
    conn.close()
    if result and bcrypt.checkpw(password.encode('utf-8'), result[0]):
        return result[1]  # Return the user's role
    return None


class EJLogApp(ttk.Window):
    def __init__(self):
        super().__init__(themename="cosmo")
        self.title("EJ Log Processor")
        self.geometry("1200x700")
        self.center_window()
        initialize_db()  # Initialize database

        self.logo_image = None  # Initialize logo image
        self.current_user_role = None  # Track the role of the logged-in user

        self.all_transactions = []
        self.file_paths = set()  # Use set for membership checks
        self.filtered_transactions = []
        self.page_size = 45  # Set the fixed page size to 45 rows per page

        # self.setup_ui()
        self.setup_login_ui()

    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def setup_login_ui(self):
        self.clear_frames()
        self.login_frame = ttk.Frame(self, padding=20)
        self.login_frame.place(relx=0.5, rely=0.5, anchor=CENTER)

        # Add logo
        self.logo_image = PhotoImage(file="logo/netcon.png")  # Replace with your logo's path
        self.logo_label = ttk.Label(self.login_frame, image=self.logo_image, anchor=CENTER)
        self.logo_label.pack(pady=10)

        ttk.Label(self.login_frame, text="Username:", anchor=W).pack(pady=5, fill=X)
        self.username_entry = ttk.Entry(self.login_frame, width=30, font=("Arial", 12))
        self.username_entry.pack(pady=5)

        ttk.Label(self.login_frame, text="Password:", anchor=W).pack(pady=5, fill=X)
        self.password_entry = ttk.Entry(self.login_frame, show="*", width=30, font=("Arial", 12))
        self.password_entry.pack(pady=5)

        ttk.Button(self.login_frame, text="Login", command=self.login, width=20, bootstyle=PRIMARY).pack(pady=10)
        # ttk.Button(self.login_frame, text="Register", command=self.show_registration, width=20, bootstyle=INFO).pack()

    def setup_registration_ui(self):
        self.clear_frames()
        self.register_frame = ttk.Frame(self, padding=20)
        self.register_frame.place(relx=0.5, rely=0.5, anchor=CENTER)

        ttk.Label(self.register_frame, text="Register", font=("Arial", 16, "bold"), anchor=CENTER).pack(pady=10)

        ttk.Label(self.register_frame, text="Username:", anchor=W).pack(pady=5, fill=X)
        self.reg_username_entry = ttk.Entry(self.register_frame, width=30, font=("Arial", 12))
        self.reg_username_entry.pack(pady=5)

        ttk.Label(self.register_frame, text="Password:", anchor=W).pack(pady=5, fill=X)
        self.reg_password_entry = ttk.Entry(self.register_frame, show="*", width=30, font=("Arial", 12))
        self.reg_password_entry.pack(pady=5)

        ttk.Label(self.register_frame, text="Role (admin/user):", anchor=W).pack(pady=5, fill=X)
        self.role_entry = ttk.Combobox(self.register_frame, values=['admin', 'user'], state="readonly", width=28, font=("Arial", 12))
        self.role_entry.pack(pady=5)
        self.role_entry.set('user')

        ttk.Button(self.register_frame, text="Register", command=self.register, width=20, bootstyle=SUCCESS).pack(pady=10)
        ttk.Button(self.register_frame, text="Back to Login", command=self.show_login, width=20, bootstyle=INFO).pack()

    def setup_main_ui(self):
        self.clear_frames()
        self.setup_ui()


    def clear_frames(self):
        for widget in self.winfo_children():
            widget.destroy()

    def show_registration(self):
        self.setup_registration_ui()

    def show_login(self):
        self.setup_login_ui()

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        role = authenticate_user(username, password)
        if role:
            self.current_user_role = role
            # messagebox.showinfo("Success", f"Login successful! Role: {role}")
            self.setup_main_ui()
        else:
            messagebox.showerror("Error", "Invalid credentials!")

    def register(self):
        username = self.reg_username_entry.get()
        password = self.reg_password_entry.get()
        role = self.role_entry.get()
        if register_user(username, password, role):
            messagebox.showinfo("Success", "User registered successfully!")
            self.show_login()
        else:
            messagebox.showerror("Error", "Username already exists!")

    def admin_action(self):
        messagebox.showinfo("Admin Action", "This action is only accessible to admin users.")


    def setup_ui(self):
        """Set up the user interface components."""
        self.setup_title_frame()
        self.setup_sidebar()
        self.setup_search_frame()
        self.setup_right_frame()

    def setup_title_frame(self):
        """Set up the title frame with action buttons and logos."""
        title_frame = ttk.Frame(self, padding=10)
        title_frame.pack(side=TOP, fill=X, padx=20)  # Add top padding (pady=(10, 20))

        # Load logos and other components inside this frame
        self.load_logo(title_frame)
        self.load_second_logo(title_frame)

        self.contact_count = ttk.Label(title_frame, text="0 files", font=("Arial", 12))
        self.contact_count.pack(side=LEFT, padx=10)
        
        self.logout_button = ttk.Button(title_frame, text="Logout", bootstyle=DANGER, command=self.logout)
        self.logout_button.pack(side=RIGHT, padx=5)

        if self.current_user_role == 'admin':
            # ttk.Button(self.main_frame, text="Admin Action", command=self.admin_action, bootstyle=SUCCESS, width=20).pack(pady=10)
            self.register_button = ttk.Button(title_frame, text="Register", bootstyle=INFO, command=self.show_registration)
            self.register_button.pack(side=RIGHT, padx=5)
            
        self.process_button = ttk.Button(title_frame, text="Process Data", bootstyle=SUCCESS, command=self.process_data)
        self.process_button.pack(side=RIGHT, padx=5)

        self.merge_button = ttk.Button(title_frame, text="Merge Files", bootstyle=INFO, command=self.merge_files)
        self.merge_button.pack(side=RIGHT, padx=5)

        # self.save_button = ttk.Button(title_frame, text="Save to CSV", bootstyle=WARNING, command=self.save_to_csv)
        # self.save_button.pack(side=RIGHT, padx=5)

    def logout(self):
        """Handle user logout and return to the login page."""
        self.current_user_role = None  # Clear the logged-in user's role
        self.setup_login_ui()  # Show the login screen
        messagebox.showinfo("Logout", "You have been logged out.")


    def load_logo(self, title_frame: ttk.Frame):
        """Load and display the first logo on the left side."""
        try:
            logo_path = Path("logo/Eastern-Bank-PLC.png")  # Specify the local file path here
            self.logo_image = Image.open(logo_path).resize((200, 50))
            self.logo_image = ImageTk.PhotoImage(self.logo_image)
            logo_label = ttk.Label(title_frame, image=self.logo_image)
            logo_label.pack(side=LEFT, padx=0, pady=0)
        except Exception as e:
            logging.error(f"Error loading logo image: {e}")

    def load_second_logo(self, title_frame: ttk.Frame):
        """Load and display the second logo in the middle of the title row."""
        try:
            logo_path_middle = Path("logo/netcon.png")
            self.logo_image_middle = Image.open(logo_path_middle).resize((150, 50))
            self.logo_image_middle = ImageTk.PhotoImage(self.logo_image_middle)
            logo_label_middle = ttk.Label(title_frame, image=self.logo_image_middle)
            logo_label_middle.pack(side=LEFT, padx=10, expand=True)
        except Exception as e:
            logging.error(f"Error loading second logo image: {e}")

    def setup_sidebar(self):
        """Set up the sidebar for file upload."""
        sidebar_frame = ttk.Frame(self, padding=10)
        sidebar_frame.pack(side=LEFT, fill=Y, padx=20)

        ttk.Label(sidebar_frame, text="Uploaded Files").pack(anchor="w")
        self.file_listbox = tk.Listbox(sidebar_frame, width=40, height=25)
        self.file_listbox.pack(fill=Y, expand=True)

        upload_button = ttk.Button(sidebar_frame, text="Upload Files", bootstyle=PRIMARY, command=self.upload_files)
        upload_button.pack(fill=X, pady=10)

    def setup_search_frame(self):
        """Set up the search and filter frame."""
        search_frame = ttk.Frame(self, padding=2)
        search_frame.pack(side=TOP, fill=X, padx=20)

        clear_button = ttk.Button(search_frame, text="Clear", bootstyle=SECONDARY, command=self.clear_filters)
        clear_button.pack(side=RIGHT, padx=5)

        filter_button = ttk.Button(search_frame, text="Filter", bootstyle=PRIMARY, command=self.filter_data)
        filter_button.pack(side=RIGHT, padx=5)

        self.filter_var = tk.StringVar()
        self.filter_entry = ttk.Entry(search_frame, textvariable=self.filter_var)
        self.filter_entry.pack(side=RIGHT, padx=5)

        self.filter_column_var = tk.StringVar()
        self.filter_column = ttk.Combobox(search_frame, textvariable=self.filter_column_var, values=[], state="readonly")
        self.filter_column.pack(side=RIGHT, padx=5)

        ttk.Label(search_frame, text="Filter by Column:").pack(side=RIGHT, padx=5)

    def setup_right_frame(self):
        """Set up the right frame for data display."""
        right_frame = ttk.Frame(self, padding=10)
        right_frame.pack(side=RIGHT, fill=BOTH, expand=True, padx=20)

        # Create a frame for data grid
        self.data_frame = ttk.Frame(right_frame)
        self.data_frame.pack(fill=BOTH, expand=True)


    def upload_files(self):
        """Upload EJ log files and display them in the listbox."""
        file_paths = filedialog.askopenfilenames(title="Select EJ Log Files")
        new_files = [Path(file_path) for file_path in file_paths if Path(file_path) not in self.file_paths]
        if new_files:
            self.file_paths.update(new_files)
            for path in new_files:
                self.file_listbox.insert("end", path.name)
            self.contact_count.config(text=f"{len(self.file_paths)} files selected")

    def process_data(self):
        """Process the uploaded EJ log files and display the data."""
        if not self.file_paths:
            messagebox.showwarning("No Files", "Please upload files to process.")
            return

        log_contents = load_logs(list(self.file_paths))
        df_all_transactions = process_transactions(log_contents)

        self.all_transactions = df_all_transactions.to_dict(orient='records')
        self.filtered_transactions = self.all_transactions.copy()

        self.contact_count.config(text=f"{len(self.all_transactions)} transactions processed")
        self.display_data()

        # Update filter column options
        self.filter_column["values"] = list(df_all_transactions.columns)

    def display_data(self):
            """Display the processed data using a Tableview."""
            if not self.filtered_transactions:
                for widget in self.data_frame.winfo_children():
                    widget.destroy()
                ttk.Label(self.data_frame, text="No data to display.", anchor="center", bootstyle="danger").pack(expand=True)
                return

            # Prepare columns and rows for the table
            excluded_columns = {'ej_log', 'cash_dispensed', 'cash_rejected', 'cash_remaining'}
            columns = [{"text": col.capitalize(), "stretch": False} for col in self.filtered_transactions[0].keys() if col not in excluded_columns]

            rows = [
                tuple(row[col] for col in self.filtered_transactions[0].keys() if col not in excluded_columns)
                for row in self.filtered_transactions
            ]

            # Destroy existing table if it exists
            if hasattr(self, 'table'):
                self.table.destroy()

            colors = self.style.colors
            # Create a new Tableview
            self.table = Tableview(
                master=self.data_frame,
                coldata=columns,
                rowdata=rows,
                paginated=True,
                pagesize=self.page_size,
                searchable=True,
                autofit=True,
                bootstyle=PRIMARY,
                stripecolor=(colors.light, None),
            )
            self.table.pack(fill=tk.BOTH, expand=True)

            # Bind button clicks
            self.table.view.bind("<Double-1>", self.row_selected)

    
    def row_selected(self, event: Any) -> None:
        """Handle row selection to show 'ej_log' data in a popup."""
        selected_item = self.table.view.selection()  # Get the selected item
        if selected_item:
            # Retrieve the data of the selected row
            selected_row_values = self.table.view.item(selected_item[0], "values")
            
            # Match the selected row values with `filtered_transactions` to get the correct row data
            matched_row = None
            for row in self.filtered_transactions:
                row_values = tuple(
                    str(row[col]) for col in self.filtered_transactions[0].keys()
                    if col not in {'ej_log', 'cash_dispensed', 'cash_rejected', 'cash_remaining'}
                )
                if row_values == selected_row_values:
                    matched_row = row
                    break

            if matched_row is None:
                logging.error("Row data not found in filtered transactions")
                messagebox.showerror("Error", "Selected row data could not be found.")
                return

            ej_log_data = matched_row.get('ej_log', 'No Data Available')

            # Create a popup to display the 'ej_log' data
            popup = tk.Toplevel(self.data_frame)
            popup.title("EJ Log Data")
            popup.geometry("800x600")  # Set the popup size

            # Text widget for displaying the ej_log data
            text_field = tk.Text(popup, wrap='word', height=30, width=80)
            text_field.insert(tk.END, ej_log_data)
            text_field.config(state=tk.DISABLED)  # Make it read-only
            text_field.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

            # Frame for buttons
            button_frame = ttk.Frame(popup)
            button_frame.pack(pady=10)

            # Close button
            close_button = ttk.Button(button_frame, text="Close", command=popup.destroy)
            close_button.pack(side=tk.LEFT, padx=10)

            # Copy to clipboard button
            copy_button = ttk.Button(button_frame, text="Copy to Clipboard", command=lambda: self.copy_to_clipboard(ej_log_data))
            copy_button.pack(side=tk.LEFT, padx=10)
        else:
            logging.info("No row selected")
            messagebox.showinfo("Info", "Please select a row to view details.")

    


    # def save_to_txt(self, ej_log_data: list) -> None:
    #     """Save the EJ Log data to a .txt file."""
    #     save_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
    #     if save_path:
    #         with open(save_path, 'w') as file:
    #             file.write('\n'.join(ej_log_data))
    #         messagebox.showinfo("Saved", f"EJ Log data saved to {save_path}.")
    def save_to_txt(self, ej_log_data: list, popup: tk.Toplevel) -> None:
        """Save the EJ Log data to a .txt file and keep the popup on top."""
        save_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if save_path:
            with open(save_path, 'w') as file:
                file.write('\n'.join(ej_log_data))
            messagebox.showinfo("Saved", f"EJ Log data saved to {save_path}.")
            popup.lift()  # Bring the popup window back to the front

    
    def copy_to_clipboard(self, ej_log_data: list) -> None:
        """Copy the EJ Log data to the clipboard."""
        ej_log_data_str = '\n'.join(ej_log_data)
        self.clipboard_clear()
        self.clipboard_append(ej_log_data_str)
        self.update()
        messagebox.showinfo("Copied", "EJ Log data copied to clipboard.")


    def filter_data(self):
        column = self.filter_column_var.get()
        filter_term = self.filter_var.get().lower()
        if not column or not filter_term:
            messagebox.showwarning("Invalid Filter", "Please select a column and enter a filter value.")
            return
        try:
            column_values = [str(row.get(column, '')).lower() for row in self.all_transactions]
            self.filtered_transactions = [
                row for row, value in zip(self.all_transactions, column_values) if filter_term in value
            ]
            self.display_data()
        except Exception as e:
            messagebox.showerror("Filter Error", f"An error occurred while filtering: {e}")

    def clear_filters(self):
        self.filtered_transactions = self.all_transactions.copy()
        self.display_data()
        self.filter_entry.delete(0, tk.END)

    def save_to_csv(self):
        if self.all_transactions:
            try:
                df = pd.DataFrame(self.all_transactions)
                save_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
                if save_path:
                    df.to_csv(save_path, index=False)
                    messagebox.showinfo("Saved", f"Data successfully saved to {save_path}.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save data to CSV: {e}")
        else:
            messagebox.showwarning("No Data", "No transactions to save.")

    def merge_files(self):
        if not self.file_paths:
            messagebox.showwarning("No Files", "Please upload files to merge.")
            return
        save_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if save_path:
            merged_output_path = merge_files(list(self.file_paths), output_path=save_path)
            if merged_output_path:
                messagebox.showinfo("Merged", f"Files successfully merged and saved to {merged_output_path}.")
            else:
                messagebox.showerror("Error", "An error occurred while merging files.")


if __name__ == "__main__":
    file_path = Path('value.txt')
    if is_trial_active() and read_value_from_file(file_path):
        app = EJLogApp()
        app.mainloop()
    else:
        with file_path.open('r') as file:
            value = file.readline().strip()
        new_value = 'False' if value == 'True' else value
        with file_path.open('w') as file:
            file.write(new_value)
        messagebox.showinfo("Trial period has expired.", "Please contact Networld Technology Limited to extend your Trial.")