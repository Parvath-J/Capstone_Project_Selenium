# filename: gui.py
import customtkinter as ctk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
import csv
from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from database import DB
from models import (User, Account, SavingsAccount, create_account_for_user, submit_feedback,
                    admin_login, get_all_users, delete_user,
                    get_users_by_balance, get_users_by_transaction_count)


# --- NEW DATA FETCHING FUNCTION ---
# This function retrieves all accounts and joins them with user details for the admin view.
def get_all_accounts_details(db: DB):
    """Fetches all customer accounts with their owner's name and balance."""
    query = """
            SELECT u.fullname, \
                   a.account_number, \
                   a.account_type, \
                   a.balance
            FROM accounts a \
                     JOIN \
                 users u ON a.user_id = u.id
            ORDER BY u.fullname, a.account_type \
            """
    return db.query(query)


# --- END OF NEW FUNCTION ---

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")


class CreateAccountDialog(ctk.CTkToplevel):
    # ... (This custom dialog class is unchanged) ...
    def __init__(self, master, existing_account_types):
        super().__init__(master)
        self.geometry("400x300");
        self.title("Create New Account");
        self.transient(master);
        self.grab_set()
        self._result = None;
        self._existing = existing_account_types
        self.grid_columnconfigure(0, weight=1);
        self.grid_rowconfigure(3, weight=1)
        ctk.CTkLabel(self, text="Select Account Type", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0,
                                                                                                      pady=10)
        self.radio_var = ctk.StringVar(value="")
        self.savings_rb = ctk.CTkRadioButton(self, text="Savings Account (Default)", variable=self.radio_var,
                                             value="Savings", state="disabled");
        self.savings_rb.grid(row=1, column=0, padx=50, pady=10, sticky="w")
        self.salary_rb = ctk.CTkRadioButton(self, text="Salary Account", variable=self.radio_var, value="Salary")
        if "Salary" in self._existing: self.salary_rb.configure(state="disabled")
        self.salary_rb.grid(row=2, column=0, padx=50, pady=10, sticky="w")
        ctk.CTkLabel(self, text="Initial Deposit:").grid(row=3, column=0, padx=20, pady=(10, 0), sticky="sw")
        self.deposit_entry = ctk.CTkEntry(self, placeholder_text="0.00");
        self.deposit_entry.grid(row=4, column=0, padx=20, pady=(0, 20), sticky="ew")
        button_frame = ctk.CTkFrame(self, fg_color="transparent");
        button_frame.grid(row=5, column=0, pady=10)
        ctk.CTkButton(button_frame, text="Create", command=self._on_ok).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Cancel", command=self.destroy, fg_color="gray").pack(side="left", padx=10)

    def _on_ok(self):
        selected_type = self.radio_var.get();
        deposit_str = self.deposit_entry.get()
        if not selected_type: messagebox.showwarning("Selection Required", "Please select an account type.",
                                                     parent=self); return
        try:
            deposit = float(deposit_str) if deposit_str else 0.0
            if deposit < 0: raise ValueError("Deposit cannot be negative.")
        except ValueError as e:
            messagebox.showerror("Invalid Input", f"Please enter a valid deposit amount.\n{e}", parent=self);
            return
        self._result = (selected_type, deposit);
        self.destroy()

    def get_input(self):
        self.master.wait_window(self);
        return self._result


class BankingApp(ctk.CTk):
    # ... (This class is unchanged) ...
    def __init__(self, db: DB):
        super().__init__()
        # self.iconphoto(False, ctk.CTkImage(Image.open("applogo.png")))
        self.db = db
        self.title("Ascendion Bank")
        self.geometry("1280x720")
        self.current_user = None
        try:
            # Resized logo for better fit in the new header
            logo_image_data = Image.open("logo.png")
            # Increase logo size a bit to match new header height, maintaining aspect ratio
            self.logo_image = ctk.CTkImage(logo_image_data, size=(350, 88))  # Adjusted logo size
        except FileNotFoundError:
            self.logo_image = ctk.CTkImage(Image.new('RGB', (280, 70), 'grey'), size=(280, 70))  # Adjusted placeholder
        self.frames = {}
        self._create_frames()
        self.show_frame(WelcomeFrame)

    def _create_frames(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        for F in (WelcomeFrame, LoginFrame, RegisterFrame, DashboardFrame, QuickPayFrame,
                  ViewBalanceFrame, CustomerCareFrame, ForgotPasswordFrame,
                  AdminLoginFrame, AdminDashboardFrame):
            frame = F(self, self.db, logo_image=self.logo_image)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

    def show_frame(self, frame_class):
        frame = self.frames[frame_class]
        if hasattr(frame, 'on_show'):
            frame.on_show()
        frame.tkraise()

    def login_success(self, user: User):
        self.current_user = user
        dashboard_frame = self.frames[DashboardFrame]
        dashboard_frame.set_user(user)
        self.show_frame(DashboardFrame)


class WelcomeFrame(ctk.CTkFrame):
    # ... (This class is unchanged) ...
    def __init__(self, master, db: DB, logo_image):
        super().__init__(master)
        self.master = master
        self.image_paths = [];
        self.current_image_index = 0;

        # Configure grid for new layout with header
        self.grid_rowconfigure(0, weight=0)  # Header row (fixed size)
        self.grid_rowconfigure(1, weight=1)  # Slideshow row (will now respect min_height for images)
        self.grid_rowconfigure(2, weight=0)  # Nav buttons row (fixed size)
        self.grid_rowconfigure(3, weight=0)  # Footer row (fixed size)
        self.grid_columnconfigure(0, weight=1)  # Center content horizontally

        # Black Header Frame - Increased height
        header = ctk.CTkFrame(self, fg_color="black", corner_radius=0, height=150);  # Increased height for header
        header.grid(row=0, column=0, sticky="ew")
        header.pack_propagate(False)  # Prevent frame from shrinking
        ctk.CTkLabel(header, text="", image=logo_image).pack(expand=True)

        # Slideshow Frame (now in row 1) - Reduced vertical padding to make it smaller
        self.slideshow_frame = ctk.CTkFrame(self);  # Renamed for easier reference
        self.slideshow_frame.grid(row=1, column=0, sticky="nsew", padx=150, pady=70);  # Reduced pady
        self.slideshow_frame.grid_columnconfigure(1, weight=1)

        # We will dynamically set the minsize of the slideshow frame based on the image size
        # This will be handled in _get_resized_image and update_slideshow

        self.slideshow_label = ctk.CTkLabel(self.slideshow_frame, text="");
        self.slideshow_label.grid(row=0, column=1, sticky="nsew")  # Image will be centered within this cell

        # Left and Right arrow buttons
        left_arrow = ctk.CTkButton(self.slideshow_frame, text="<", command=self.prev_image, width=40, height=40);
        left_arrow.grid(row=0, column=0, padx=5, sticky="w")  # Sticky "w" to keep it left
        right_arrow = ctk.CTkButton(self.slideshow_frame, text=">", command=self.next_image, width=40, height=40);
        right_arrow.grid(row=0, column=2, padx=5, sticky="e")  # Sticky "e" to keep it right

        # Navigation Frame (now in row 2) - Enlarged buttons
        nav_frame = ctk.CTkFrame(self, fg_color="transparent");
        nav_frame.grid(row=2, column=0, pady=20)
        buttons = {"Login": LoginFrame, "Register": RegisterFrame, "Quick Pay": QuickPayFrame,
                   "View Balance": ViewBalanceFrame}
        for i, (text, frame_class) in enumerate(buttons.items()):
            ctk.CTkButton(nav_frame, text=text, command=lambda fc=frame_class: self.master.show_frame(fc),
                          width=200, height=60).grid(row=0, column=i, padx=15)  # Enlarged buttons: width 200, height 60

        # Footer Frame (now in row 3)
        footer_frame = ctk.CTkFrame(self, fg_color="transparent");
        footer_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=10)
        ctk.CTkButton(footer_frame, text="Customer Care", command=lambda: self.master.show_frame(CustomerCareFrame),
                      width=120).pack(side="left")
        ctk.CTkButton(footer_frame, text="Admin", command=self.admin_login, width=120).pack(side="right")

        self._load_images()
        # Bind the <Configure> event to the slideshow_frame to trigger image resizing when the frame changes size
        self.slideshow_frame.bind("<Configure>", self._on_slideshow_frame_configure)
        self.update_slideshow()  # Initial call

    def _on_slideshow_frame_configure(self, event=None):
        # This function will be called whenever the slideshow_frame is resized
        # We need to ensure images are re-rendered at the correct size
        self.update_slideshow(force_resize=True)

    def admin_login(self):
        self.master.show_frame(AdminLoginFrame)

    def _get_resized_image(self, path):
        # Get the available width from the slideshow label's parent frame
        # We call update_idletasks to ensure winfo_width returns the correct, updated value
        self.slideshow_frame.update_idletasks()  # Ensure frame dimensions are up-to-date

        # Consider a maximum desired width for the image if the frame gets too wide
        max_image_width = 900  # Maximum width for the image within the frame

        # Calculate available width within the slideshow_label's grid cell (accounting for padding/arrows)
        # We use the slideshow_frame's actual width and subtract static elements if any
        container_width = self.slideshow_frame.winfo_width() - 40  # Account for padx of arrows (2*10 for arrows)

        if container_width <= 1:  # Fallback if window not fully drawn or too small
            container_width = 800  # Default reasonable width

        # Limit the image width to max_image_width, but don't exceed container_width
        target_width = min(container_width, max_image_width)

        original_img = Image.open(path)
        original_width, original_height = original_img.size

        # Calculate the new height to maintain the aspect ratio
        aspect_ratio = original_height / original_width
        new_height = int(target_width * aspect_ratio)

        # Ensure height is at least a minimum to prevent extremely thin images
        min_image_height = 250  # Minimum height for the image
        if new_height < min_image_height:
            new_height = min_image_height
            # Recalculate width to maintain aspect ratio if height was forced
            target_width = int(new_height / aspect_ratio)

        # Create the CTkImage with the calculated size
        return ctk.CTkImage(light_image=original_img, size=(target_width, new_height))

    def _load_images(self):
        self.image_paths = []  # Store paths to reload on resize
        for i in range(1, 4):
            try:
                img_path = f"ad{i}.png"
                if os.path.exists(img_path):
                    self.image_paths.append(img_path)  # Save the path
            except Exception as e:
                print(f"Error loading image {img_path}: {e}")

        if not self.image_paths:
            print("No ad images found.")

    def update_slideshow(self, force_resize=False):
        if self.image_paths:
            # Only change image index if not a force_resize (which happens on window resize)
            if not force_resize:
                self.current_image_index = (self.current_image_index + 1) % len(self.image_paths)

            path = self.image_paths[self.current_image_index]
            resized_image = self._get_resized_image(path)

            # Configure the slideshow label to display the resized image
            self.slideshow_label.configure(image=resized_image)
            self.slideshow_label.image = resized_image  # Keep reference!

            # Dynamically adjust the min height of the slideshow_frame to fit the image
            # This helps prevent cutting if the frame is too short
            self.slideshow_frame.grid_propagate(False)  # Stop frame from shrinking to label size
            self.slideshow_frame.configure(height=resized_image._size[1] + 20)  # image height + padding
            self.slideshow_frame.grid_propagate(True)  # Allow it to grow if needed

        # Schedule the next update only if not a force_resize (to avoid double scheduling)
        if not force_resize:
            self.after(4000, self.update_slideshow)

    def next_image(self):
        # Stop pending slideshow updates to prevent conflicts
        self.after_cancel(self.update_slideshow_id) if hasattr(self, 'update_slideshow_id') else None

        if self.image_paths:
            self.current_image_index = (self.current_image_index + 1) % len(self.image_paths)
            path = self.image_paths[self.current_image_index]
            resized_image = self._get_resized_image(path)
            self.slideshow_label.configure(image=resized_image)
            self.slideshow_label.image = resized_image  # Keep reference!
            # Dynamically adjust the min height of the slideshow_frame to fit the image
            self.slideshow_frame.grid_propagate(False)
            self.slideshow_frame.configure(height=resized_image._size[1] + 20)
            self.slideshow_frame.grid_propagate(True)

        # Restart the slideshow timer
        self.update_slideshow_id = self.after(4000, self.update_slideshow)

    def prev_image(self):
        # Stop pending slideshow updates to prevent conflicts
        self.after_cancel(self.update_slideshow_id) if hasattr(self, 'update_slideshow_id') else None

        if self.image_paths:
            self.current_image_index = (self.current_image_index - 1 + len(self.image_paths)) % len(self.image_paths)
            path = self.image_paths[self.current_image_index]
            resized_image = self._get_resized_image(path)
            self.slideshow_label.configure(image=resized_image)
            self.slideshow_label.image = resized_image  # Keep reference!
            # Dynamically adjust the min height of the slideshow_frame to fit the image
            self.slideshow_frame.grid_propagate(False)
            self.slideshow_frame.configure(height=resized_image._size[1] + 20)
            self.slideshow_frame.grid_propagate(True)

        # Restart the slideshow timer
        self.update_slideshow_id = self.after(4000, self.update_slideshow)


class LoginFrame(ctk.CTkFrame):
    # ... (This class is unchanged) ...
    def __init__(self, master, db: DB, logo_image):
        super().__init__(master)
        self.master = master
        self.db = db

        # Centering container on the light background
        center_container = ctk.CTkFrame(self, fg_color="transparent");
        center_container.pack(expand=True)

        # Dark frame to wrap the login form
        dark_frame = ctk.CTkFrame(center_container, fg_color="gray14", corner_radius=10)
        dark_frame.pack(pady=20, padx=20)

        ctk.CTkLabel(dark_frame, text="", image=logo_image).pack(pady=(20, 20))
        ctk.CTkLabel(dark_frame, text="Customer Login", font=ctk.CTkFont(size=24, weight="bold"),
                     text_color="white").pack(pady=(0, 30))

        form_frame = ctk.CTkFrame(dark_frame, fg_color="transparent");
        form_frame.pack(pady=20, padx=40)

        ctk.CTkLabel(form_frame, text="Username", text_color="white").pack(anchor="w", padx=15, pady=(15, 0))
        self.username_entry = ctk.CTkEntry(form_frame, width=250, height=35);
        self.username_entry.pack(pady=(0, 10), padx=15)

        ctk.CTkLabel(form_frame, text="Password", text_color="white").pack(anchor="w", padx=15)
        self.password_entry = ctk.CTkEntry(form_frame, show="*", width=250, height=35);
        self.password_entry.pack(pady=(0, 10), padx=15)

        ctk.CTkButton(form_frame, text="Forgot Password?", command=lambda: self.master.show_frame(ForgotPasswordFrame),
                      fg_color="transparent", text_color="#5dade2", hover=False).pack(anchor="e", padx=15, pady=(0, 10))

        ctk.CTkButton(dark_frame, text="Login", command=self.login, width=250, height=35).pack(pady=10)
        ctk.CTkButton(dark_frame, text="< Back to Home", command=lambda: self.master.show_frame(WelcomeFrame),
                      width=250, height=35, fg_color="transparent", border_width=1, border_color="gray50").pack(
            pady=(0, 20))

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        user = User.login(self.db, username, password)
        if user:
            self.master.login_success(user)
        else:
            messagebox.showerror("Login Failed", "Invalid credentials")

    def clear_fields(self):
        self.username_entry.delete(0, 'end')
        self.password_entry.delete(0, 'end')

    def on_show(self):
        self.clear_fields()


class RegisterFrame(ctk.CTkFrame):
    # ... (This class is unchanged) ...
    def __init__(self, master, db: DB, logo_image):
        super().__init__(master)
        self.master = master
        self.db = db

        center_container = ctk.CTkFrame(self, fg_color="transparent");
        center_container.pack(expand=True)

        dark_frame = ctk.CTkFrame(center_container, fg_color="gray14", corner_radius=10)
        dark_frame.pack(pady=20, padx=20)

        ctk.CTkLabel(dark_frame, text="", image=logo_image).pack(pady=(20, 20))
        ctk.CTkLabel(dark_frame, text="Create Your Account", font=ctk.CTkFont(size=24, weight="bold"),
                     text_color="white").pack(
            pady=(0, 20))

        form_frame = ctk.CTkFrame(dark_frame, fg_color="transparent");
        form_frame.pack(pady=10, padx=40)

        labels = ["Full Name", "Username", "Phone Number", "PAN Number", "Password", "Re-enter Password",
                  "4-Digit UPI PIN"]
        self.entries = {}
        for i, label_text in enumerate(labels):
            ctk.CTkLabel(form_frame, text=label_text, text_color="white").grid(row=i, column=0, sticky="w", padx=15,
                                                                               pady=(10, 0))
            is_password = "Password" in label_text or "PIN" in label_text
            entry = ctk.CTkEntry(form_frame, width=250, height=35, show="*" if is_password else None)
            entry.grid(row=i, column=1, padx=15, pady=(10, 5))
            self.entries[label_text] = entry

        ctk.CTkButton(dark_frame, text="Create Account", command=self.register, width=250, height=35).pack(pady=20)
        ctk.CTkButton(dark_frame, text="< Back to Home", command=lambda: self.master.show_frame(WelcomeFrame),
                      width=250, height=35, fg_color="transparent", border_width=1, border_color="gray50").pack(
            pady=(0, 20))

    def register(self):
        # ... (register logic is unchanged) ...
        vals = {label: entry.get().strip() for label, entry in self.entries.items()}
        if not all(vals.values()): return messagebox.showerror("Error", "All fields are required.")
        if vals["Password"] != vals["Re-enter Password"]: return messagebox.showerror("Error",
                                                                                      "Passwords do not match.")
        if not vals["4-Digit UPI PIN"].isdigit() or len(vals["4-Digit UPI PIN"]) != 4: return messagebox.showerror(
            "Error", "UPI PIN must be 4 digits.")
        success = User.register(self.db, vals["Username"], vals["Full Name"], vals["Phone Number"], vals["PAN Number"],
                                vals["Password"], vals["4-Digit UPI PIN"])
        if success:
            messagebox.showinfo("Success",
                                "Account created successfully! A default Savings account has been added. You can now log in.")
            self.master.show_frame(LoginFrame)
        else:
            messagebox.showerror("Error", "Registration failed. Username, Phone, or PAN may already be in use.")

    def clear_fields(self):
        for entry in self.entries.values():
            entry.delete(0, 'end')

    def on_show(self):
        self.clear_fields()


class DashboardFrame(ctk.CTkFrame):
    # ... (This class is unchanged) ...
    def __init__(self, master, db: DB, logo_image):
        super().__init__(master, fg_color="transparent")
        self.master = master
        self.db = db
        self.logo_image = logo_image
        self.user = None;
        self.accounts = [];
        self.selected_account = None
        self.grid_columnconfigure(1, weight=1);
        self.grid_rowconfigure(0, weight=1)
        self.sidebar_frame = ctk.CTkFrame(self, width=250, corner_radius=0);
        self.sidebar_frame.grid(row=0, column=0, sticky="nsw")
        self.main_content_frame = ctk.CTkFrame(self, fg_color="transparent");
        self.main_content_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    def set_user(self, user: User):
        self.user = user;
        self.style_treeview();
        self._build_sidebar();
        self.refresh_accounts();
        self._display_welcome_message()

    def _build_sidebar(self):
        for widget in self.sidebar_frame.winfo_children(): widget.destroy()
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        ctk.CTkLabel(self.sidebar_frame, text="", image=self.logo_image, compound="left").grid(row=0, column=0, padx=20,
                                                                                               pady=(20, 10))
        ctk.CTkLabel(self.sidebar_frame, text=f"Hi, {self.user.fullname}", anchor="w").grid(row=1, column=0, padx=20,
                                                                                            pady=(10, 20), sticky="ew")
        ctk.CTkLabel(self.sidebar_frame, text="My Accounts", anchor="w", font=ctk.CTkFont(weight="bold")).grid(row=2,
                                                                                                               column=0,
                                                                                                               padx=20,
                                                                                                               pady=(10,
                                                                                                                     5),
                                                                                                               sticky="ew")
        self.accounts_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent");
        self.accounts_frame.grid(row=3, column=0, sticky="nsew", padx=10)
        ctk.CTkButton(self.sidebar_frame, text="＋ Create New Account", command=self.create_account_dialog).grid(row=5,
                                                                                                                column=0,
                                                                                                                padx=20,
                                                                                                                pady=10)
        ctk.CTkButton(self.sidebar_frame, text="Logout", command=self.logout).grid(row=6, column=0, padx=20, pady=10)

    def create_account_dialog(self):
        existing_types = [acc.account_type for acc in self.accounts]
        if len(existing_types) >= 2:
            messagebox.showinfo("Limit Reached", "You already have the maximum of two accounts (Savings and Salary).")
            return
        dialog = CreateAccountDialog(self, existing_account_types=existing_types)
        result = dialog.get_input()
        if result:
            account_type, initial_deposit = result
            interest_rate = 0.00
            new_account = create_account_for_user(self.db, self.user.id, account_type, initial_deposit, interest_rate)
            messagebox.showinfo("Success",
                                f"{account_type} account created successfully with number {new_account.account_number}.")
            self.refresh_accounts()

    def _clear_main_content(self):
        for widget in self.main_content_frame.winfo_children(): widget.destroy()

    def _display_welcome_message(self):
        self._clear_main_content()
        ctk.CTkLabel(self.main_content_frame, text="Welcome to Your Dashboard",
                     font=ctk.CTkFont(size=28, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(self.main_content_frame, text="Select an account from the sidebar to view details.",
                     font=ctk.CTkFont(size=16)).pack(anchor="w")

    def _display_account_details(self, acc: Account):
        self.selected_account = acc;
        self._clear_main_content()
        header_frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent");
        header_frame.pack(fill="x", pady=(0, 20))
        # ctk.CTkLabel(header_frame, text=f"{acc.account_type} Account", font=ctk.CTkFont(size=24, weight="bold")).pack(
        #    side="left")
        ctk.CTkLabel(header_frame, text=f"{acc.account_type} Account - {acc.account_number}",
                     font=ctk.CTkFont(size=24, weight="bold")).pack(
            side="left")
        balance_frame = ctk.CTkFrame(self.main_content_frame);
        balance_frame.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(balance_frame, text="Available Balance", font=ctk.CTkFont(size=14)).pack(pady=(10, 0), padx=20,
                                                                                              anchor="w")
        ctk.CTkLabel(balance_frame, text=f"₹{acc.balance:,.2f}", font=ctk.CTkFont(size=32, weight="bold")).pack(
            pady=(0, 10), padx=20, anchor="w")
        btn_frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent");
        btn_frame.pack(pady=5, fill="x")
        actions = {"＋ Deposit": self.deposit_dialog, "－ Withdraw": self.withdraw_dialog,
                   "→ Transfer": self.transfer_dialog, "％ Apply Interest": self.apply_interest_selected,
                   "📄 View Statement": self.show_statement}
        for i, (text, cmd) in enumerate(actions.items()): ctk.CTkButton(btn_frame, text=text, command=cmd).grid(row=0,
                                                                                                                column=i,
                                                                                                                padx=(0,
                                                                                                                      10))
        ctk.CTkLabel(self.main_content_frame, text="Recent Transactions",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20, 10), anchor="w")
        self.txn_table = ttk.Treeview(self.main_content_frame, columns=("time", "type", "amount", "note"),
                                      show="headings", height=15)
        self.txn_table.heading("time", text="Timestamp");
        self.txn_table.heading("type", text="Type");
        self.txn_table.heading("amount", text="Amount");
        self.txn_table.heading("note", text="Note")
        self.txn_table.column("time", width=160);
        self.txn_table.column("type", width=100);
        self.txn_table.column("amount", width=120, anchor="e");
        self.txn_table.column("note", width=300)
        self.txn_table.pack(fill="both", expand=True)
        self.load_transactions(acc)

    def refresh_accounts(self):
        for widget in self.accounts_frame.winfo_children(): widget.destroy()
        self.accounts = self.user.get_accounts()
        for acc in self.accounts:
            btn = ctk.CTkButton(self.accounts_frame, text=f"{acc.account_type}\n₹{acc.balance:,.2f}", anchor="w",
                                command=lambda a=acc: self._display_account_details(a), height=50)
            btn.pack(fill="x", pady=(0, 5))

    def load_transactions(self, acc: Account):
        for i in self.txn_table.get_children(): self.txn_table.delete(i)
        for r in acc.get_transactions(100): self.txn_table.insert("", "end", values=(r["timestamp"], r["type"],
                                                                                     f"₹{r['amount']:,.2f}",
                                                                                     r["note"] or ""))

    def style_treeview(self):
        style = ttk.Style()
        bg_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
        text_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkLabel"]["text_color"])
        header_bg = "#E0E0E0"
        style.theme_use("default")
        style.configure("Treeview", background=bg_color, foreground=text_color, fieldbackground=bg_color, borderwidth=0,
                        rowheight=25)
        style.configure("Treeview.Heading", background=header_bg, foreground="black", relief="flat",
                        font=('Calibri', 10, 'bold'))
        style.map("Treeview.Heading", background=[('active', "#CCCCCC")])

    def logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.master.current_user = None
            self.master.show_frame(WelcomeFrame)

    def _get_input(self, title, prompt):
        dialog = ctk.CTkInputDialog(text=prompt, title=title)
        return dialog.get_input()

    def deposit_dialog(self):
        if not self.selected_account: return messagebox.showwarning("Warning", "Select an account first.")
        amt_str = self._get_input("Deposit", "Enter amount to deposit:")
        note = self._get_input("Note", "Optional note:")
        try:
            amt = float(amt_str)
            self.selected_account.deposit(amt, note)
            messagebox.showinfo("Success", "Deposit completed.")
            self.refresh_accounts();
            self._display_account_details(self.selected_account)
        except (ValueError, TypeError):
            messagebox.showerror("Error", "Invalid amount.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def withdraw_dialog(self):
        if not self.selected_account: return messagebox.showwarning("Warning", "Select an account first.")
        amt_str = self._get_input("Withdraw", "Enter amount to withdraw:")
        note = self._get_input("Note", "Optional note:")
        try:
            self.selected_account.withdraw(float(amt_str), note)
            messagebox.showinfo("Success", "Withdrawal completed.")
            self.refresh_accounts();
            self._display_account_details(self.selected_account)
        except (ValueError, TypeError) as e:
            messagebox.showerror("Error", str(e))

    def transfer_dialog(self):
        if not self.selected_account: return messagebox.showwarning("Warning", "Select an account first.")
        target_num = self._get_input("Transfer", "Enter target account number:")
        amt_str = self._get_input("Amount", "Enter amount to transfer:")
        note = self._get_input("Note", "Optional note:")
        try:
            amt = float(amt_str)
            rows = self.db.query("SELECT * FROM accounts WHERE account_number = %s", (target_num,))
            if not rows: raise ValueError("Target account not found.")
            target_acc = Account.from_row(self.db, rows[0])
            self.selected_account.withdraw(amt, f"Transfer to {target_acc.account_number}. {note or ''}")
            target_acc.deposit(amt, f"Transfer from {self.selected_account.account_number}. {note or ''}")
            messagebox.showinfo("Success", "Transfer completed.")
            self.refresh_accounts();
            self._display_account_details(self.selected_account)
        except (ValueError, TypeError) as e:
            messagebox.showerror("Transfer Failed", str(e))

    def apply_interest_selected(self):
        if not self.selected_account: return messagebox.showwarning("Warning", "Select an account first.")
        if self.selected_account.account_type.lower() != 'savings': return messagebox.showinfo("Info",
                                                                                               "Interest only applies to Savings accounts.")
        sav = SavingsAccount(self.db, self.selected_account.id, self.selected_account.user_id,
                             self.selected_account.account_number, self.selected_account.account_type,
                             self.selected_account.balance, self.selected_account.interest_rate)
        interest = sav.apply_interest()
        if interest > 0:
            messagebox.showinfo("Interest Applied", f"₹{interest:,.2f} has been applied.")
            self.refresh_accounts();
            self._display_account_details(self.selected_account)
        else:
            messagebox.showinfo("No Interest", "No interest was applied.")

    def show_statement(self):
        if not self.selected_account: return messagebox.showwarning("Warning", "Select an account first.")
        win = ctk.CTkToplevel(self);
        win.title(f"Statement - {self.selected_account.account_number}");
        win.geometry("800x600")
        tree = ttk.Treeview(win, columns=("time", "type", "amount", "note", "related"), show='headings');
        tree.pack(fill='both', expand=True, padx=10, pady=10)
        self.style_treeview()
        for col in tree["columns"]: tree.heading(col, text=col.title())
        for r in self.selected_account.get_transactions(limit=1000): tree.insert('', 'end',
                                                                                 values=(r['timestamp'], r['type'],
                                                                                         f"₹{r['amount']:,.2f}",
                                                                                         r['note'] or '',
                                                                                         r['related_account'] or ''))


class QuickPayFrame(ctk.CTkFrame):
    # ... (This class is unchanged) ...
    def __init__(self, master, db: DB, logo_image):
        super().__init__(master)
        self.master = master;
        self.db = db
        center_container = ctk.CTkFrame(self, fg_color="transparent");
        center_container.pack(expand=True)

        dark_frame = ctk.CTkFrame(center_container, fg_color="gray14", corner_radius=10)
        dark_frame.pack(pady=20, padx=20)

        ctk.CTkLabel(dark_frame, text="", image=logo_image).pack(pady=(20, 20))
        ctk.CTkLabel(dark_frame, text="Quick Pay", font=ctk.CTkFont(size=24, weight="bold"), text_color="white").pack(
            pady=(0, 20))

        form_frame = ctk.CTkFrame(dark_frame, fg_color="transparent");
        form_frame.pack(pady=20, padx=40)

        ctk.CTkLabel(form_frame, text="Your UPI ID (phonenumber@asc)", text_color="white").pack(anchor="w", padx=15,
                                                                                                pady=(15, 0))
        self.upi_id_entry = ctk.CTkEntry(form_frame, width=300, height=35);
        self.upi_id_entry.pack(pady=(0, 10), padx=15)
        ctk.CTkLabel(form_frame, text="Your 4-Digit UPI PIN", text_color="white").pack(anchor="w", padx=15)
        self.pin_entry = ctk.CTkEntry(form_frame, width=300, height=35, show="*");
        self.pin_entry.pack(pady=(0, 10), padx=15)
        ctk.CTkLabel(form_frame, text="Recipient's UPI ID", text_color="white").pack(anchor="w", padx=15)
        self.recipient_entry = ctk.CTkEntry(form_frame, width=300, height=35);
        self.recipient_entry.pack(pady=(0, 10), padx=15)
        ctk.CTkLabel(form_frame, text="Amount", text_color="white").pack(anchor="w", padx=15)
        self.amount_entry = ctk.CTkEntry(form_frame, width=300, height=35);
        self.amount_entry.pack(pady=(0, 20), padx=15)

        ctk.CTkButton(dark_frame, text="Pay Now", command=self.pay, width=250, height=35).pack(pady=10)
        ctk.CTkButton(dark_frame, text="< Back to Home", command=lambda: self.master.show_frame(WelcomeFrame),
                      width=250, height=35, fg_color="transparent", border_width=1, border_color="gray50").pack(
            pady=(0, 20))

    def pay(self):
        # ... (pay logic is unchanged) ...
        upi_id = self.upi_id_entry.get().strip();
        pin = self.pin_entry.get().strip();
        recipient_upi = self.recipient_entry.get().strip();
        amount_str = self.amount_entry.get().strip()
        if not all([upi_id, pin, recipient_upi, amount_str]): return messagebox.showerror("Error",
                                                                                          "All fields are required.")
        try:
            amount = float(amount_str)
        except ValueError:
            return messagebox.showerror("Error", "Invalid amount.")
        phone = upi_id.split('@')[0];
        sender = User.verify_upi_pin(self.db, phone, pin)
        if not sender: return messagebox.showerror("Auth Failed", "Invalid UPI ID or PIN.")
        recipient_phone = recipient_upi.split('@')[0];
        recipient = User.get_user_by_phone(self.db, recipient_phone)
        if not recipient: return messagebox.showerror("Error", "Recipient UPI ID not found.")
        sender_account = sender.get_primary_account();
        recipient_account = recipient.get_primary_account()
        if not sender_account or not recipient_account: return messagebox.showerror("Error", "Account error.")
        try:
            sender_account.withdraw(amount, f"UPI Pay to {recipient.fullname}")
            recipient_account.deposit(amount, f"UPI Rcvd from {sender.fullname}")
            messagebox.showinfo("Success", f"Successfully paid ₹{amount:,.2f} to {recipient.fullname}.")
            self.master.show_frame(WelcomeFrame)
        except ValueError as e:
            messagebox.showerror("Payment Failed", str(e))

    def clear_fields(self):
        self.upi_id_entry.delete(0, 'end')
        self.pin_entry.delete(0, 'end')
        self.recipient_entry.delete(0, 'end')
        self.amount_entry.delete(0, 'end')

    def on_show(self):
        self.clear_fields()


class ViewBalanceFrame(ctk.CTkFrame):
    # ... (This class is unchanged) ...
    def __init__(self, master, db: DB, logo_image):
        super().__init__(master)
        self.master = master;
        self.db = db
        center_container = ctk.CTkFrame(self, fg_color="transparent");
        center_container.pack(expand=True)

        dark_frame = ctk.CTkFrame(center_container, fg_color="gray14", corner_radius=10)
        dark_frame.pack(pady=20, padx=20)

        ctk.CTkLabel(dark_frame, text="", image=logo_image).pack(pady=(20, 20))
        ctk.CTkLabel(dark_frame, text="Check Balance via UPI", font=ctk.CTkFont(size=24, weight="bold"),
                     text_color="white").pack(
            pady=(0, 20))

        form_frame = ctk.CTkFrame(dark_frame, fg_color="transparent");
        form_frame.pack(pady=20, padx=40)

        ctk.CTkLabel(form_frame, text="Your UPI ID (phonenumber@asc)", text_color="white").pack(anchor="w", padx=15,
                                                                                                pady=(15, 0))
        self.upi_id_entry = ctk.CTkEntry(form_frame, width=300, height=35);
        self.upi_id_entry.pack(pady=(0, 10), padx=15)

        ctk.CTkLabel(form_frame, text="Your 4-Digit UPI PIN", text_color="white").pack(anchor="w", padx=15)
        self.pin_entry = ctk.CTkEntry(form_frame, width=300, height=35, show="*");
        self.pin_entry.pack(pady=(0, 20), padx=15)

        ctk.CTkButton(dark_frame, text="View Balance", command=self.check_balance, width=250, height=35).pack(pady=10)
        ctk.CTkButton(dark_frame, text="< Back to Home", command=lambda: self.master.show_frame(WelcomeFrame),
                      width=250, height=35, fg_color="transparent", border_width=1, border_color="gray50").pack(
            pady=(0, 20))

    def check_balance(self):
        # ... (check_balance logic is unchanged) ...
        upi_id = self.upi_id_entry.get().strip();
        pin = self.pin_entry.get().strip()
        phone = upi_id.split('@')[0];
        user = User.verify_upi_pin(self.db, phone, pin)
        if not user: return messagebox.showerror("Auth Failed", "Invalid UPI ID or PIN.")
        account = user.get_primary_account()
        if account:
            messagebox.showinfo("Balance", f"Your primary account balance is: ₹{account.balance:,.2f}")
        else:
            messagebox.showerror("Error", "No account found for this user.")

    def clear_fields(self):
        self.upi_id_entry.delete(0, 'end')
        self.pin_entry.delete(0, 'end')

    def on_show(self):
        self.clear_fields()


class CustomerCareFrame(ctk.CTkFrame):
    # ... (This class is unchanged) ...
    def __init__(self, master, db: DB, logo_image):
        super().__init__(master)
        self.master = master;
        self.db = db
        center_container = ctk.CTkFrame(self, fg_color="transparent");
        center_container.pack(expand=True)

        dark_frame = ctk.CTkFrame(center_container, fg_color="gray14", corner_radius=10)
        dark_frame.pack(pady=20, padx=20)

        ctk.CTkLabel(dark_frame, text="", image=logo_image).pack(pady=(20, 20))
        ctk.CTkLabel(dark_frame, text="Customer Care", font=ctk.CTkFont(size=24, weight="bold"),
                     text_color="white").pack(pady=(0, 20))
        ctk.CTkLabel(dark_frame, text="Please describe your issue or feedback below.", text_color="white").pack()
        self.textbox = ctk.CTkTextbox(dark_frame, width=500, height=200);
        self.textbox.pack(pady=10, padx=20)

        ctk.CTkButton(dark_frame, text="Submit Feedback", command=self.submit, width=250, height=35).pack(pady=10)
        ctk.CTkButton(dark_frame, text="< Back to Home", command=lambda: self.master.show_frame(WelcomeFrame),
                      width=250, height=35, fg_color="transparent", border_width=1, border_color="gray50").pack(
            pady=(0, 20))

    def submit(self):
        # ... (submit logic is unchanged) ...
        message = self.textbox.get("1.0", "end-1c").strip()
        if not message: return messagebox.showerror("Error", "Feedback cannot be empty.")
        user_id = self.master.current_user.id if self.master.current_user else None
        submit_feedback(self.db, message, user_id)
        messagebox.showinfo("Success", "Your feedback has been submitted. Thank you!")
        self.master.show_frame(WelcomeFrame)

    def clear_fields(self):
        self.textbox.delete("1.0", 'end')

    def on_show(self):
        self.clear_fields()


class ForgotPasswordFrame(ctk.CTkFrame):
    # ... (This class is unchanged) ...
    def __init__(self, master, db: DB, logo_image):
        super().__init__(master)
        self.master = master;
        self.db = db;
        self.logo_image = logo_image
        self.verified_username = None
        self._show_verification_step()

    def on_show(self):
        # This resets the frame to the first step every time it's shown
        self.verified_username = None
        self._show_verification_step()

    def _clear(self):
        for widget in self.winfo_children(): widget.destroy()

    def _show_verification_step(self):
        self._clear()
        center_container = ctk.CTkFrame(self, fg_color="transparent");
        center_container.pack(expand=True)

        dark_frame = ctk.CTkFrame(center_container, fg_color="gray14", corner_radius=10)
        dark_frame.pack(pady=20, padx=20)

        ctk.CTkLabel(dark_frame, text="", image=self.logo_image).pack(pady=(20, 20))
        ctk.CTkLabel(dark_frame, text="Forgot Password", font=ctk.CTkFont(size=24, weight="bold"),
                     text_color="white").pack(pady=(0, 20))

        form_frame = ctk.CTkFrame(dark_frame, fg_color="transparent");
        form_frame.pack(pady=20, padx=40)

        ctk.CTkLabel(form_frame, text="Username", text_color="white").pack(anchor="w", padx=15, pady=(15, 0))
        self.username_entry = ctk.CTkEntry(form_frame, width=250, height=35);
        self.username_entry.pack(pady=(0, 10), padx=15)

        ctk.CTkLabel(form_frame, text="Registered Phone Number", text_color="white").pack(anchor="w", padx=15)
        self.phone_entry = ctk.CTkEntry(form_frame, width=250, height=35);
        self.phone_entry.pack(pady=(0, 20), padx=15)

        ctk.CTkButton(dark_frame, text="Verify", command=self.verify, width=250, height=35).pack(pady=10)
        ctk.CTkButton(dark_frame, text="< Back to Login", command=lambda: self.master.show_frame(LoginFrame),
                      width=250, height=35, fg_color="transparent", border_width=1, border_color="gray50").pack(
            pady=(0, 20))

    def verify(self):
        # ... (verify is unchanged) ...
        username = self.username_entry.get().strip();
        phone = self.phone_entry.get().strip()
        if User.verify_phone_for_reset(self.db, username, phone):
            self.verified_username = username;
            self._show_reset_step()
        else:
            messagebox.showerror("Failed", "Username and phone number do not match our records.")

    def _show_reset_step(self):
        self._clear()
        center_container = ctk.CTkFrame(self, fg_color="transparent");
        center_container.pack(expand=True)

        dark_frame = ctk.CTkFrame(center_container, fg_color="gray14", corner_radius=10)
        dark_frame.pack(pady=20, padx=20)

        ctk.CTkLabel(dark_frame, text="", image=self.logo_image).pack(pady=(20, 20))
        ctk.CTkLabel(dark_frame, text="Reset Your Password", font=ctk.CTkFont(size=24, weight="bold"),
                     text_color="white").pack(
            pady=(0, 20))

        form_frame = ctk.CTkFrame(dark_frame, fg_color="transparent");
        form_frame.pack(pady=20, padx=40)

        ctk.CTkLabel(form_frame, text="New Password", text_color="white").pack(anchor="w", padx=15, pady=(15, 0))
        self.new_pass_entry = ctk.CTkEntry(form_frame, width=250, height=35, show="*");
        self.new_pass_entry.pack(pady=(0, 10), padx=15)

        ctk.CTkLabel(form_frame, text="Confirm New Password", text_color="white").pack(anchor="w", padx=15)
        self.confirm_pass_entry = ctk.CTkEntry(form_frame, width=250, height=35, show="*");
        self.confirm_pass_entry.pack(pady=(0, 20), padx=15)

        ctk.CTkButton(dark_frame, text="Reset Password", command=self.reset_password, width=250, height=35).pack(
            padx=40, pady=(0, 20))

    def reset_password(self):
        # ... (reset_password is unchanged) ...
        new_pass = self.new_pass_entry.get();
        confirm_pass = self.confirm_pass_entry.get()
        if not new_pass or not confirm_pass: return messagebox.showerror("Error", "Password fields cannot be empty.")
        if new_pass != confirm_pass: return messagebox.showerror("Error", "Passwords do not match.")
        User.update_password(self.db, self.verified_username, new_pass)
        messagebox.showinfo("Success", "Password has been reset successfully. Please log in.")
        self.master.show_frame(LoginFrame)


class AdminLoginFrame(ctk.CTkFrame):
    # ... (This class is unchanged) ...
    def __init__(self, master, db: DB, logo_image):
        super().__init__(master)
        self.master = master;
        self.db = db
        center_container = ctk.CTkFrame(self, fg_color="transparent");
        center_container.pack(expand=True)

        dark_frame = ctk.CTkFrame(center_container, fg_color="gray14", corner_radius=10)
        dark_frame.pack(pady=20, padx=20)

        ctk.CTkLabel(dark_frame, text="", image=logo_image).pack(pady=(20, 20))
        ctk.CTkLabel(dark_frame, text="Admin Portal Login", font=ctk.CTkFont(size=24, weight="bold"),
                     text_color="white").pack(
            pady=(0, 30))

        form_frame = ctk.CTkFrame(dark_frame, fg_color="transparent");
        form_frame.pack(pady=20, padx=40)

        ctk.CTkLabel(form_frame, text="Admin Username", text_color="white").pack(anchor="w", padx=15, pady=(15, 0))
        self.username_entry = ctk.CTkEntry(form_frame, width=250, height=35);
        self.username_entry.pack(pady=(0, 10), padx=15)

        ctk.CTkLabel(form_frame, text="Password", text_color="white").pack(anchor="w", padx=15)
        self.password_entry = ctk.CTkEntry(form_frame, show="*", width=250, height=35);
        self.password_entry.pack(pady=(0, 20), padx=15)

        ctk.CTkButton(dark_frame, text="Login", command=self.login, width=250, height=35).pack(pady=10)
        ctk.CTkButton(dark_frame, text="< Back to Home", command=lambda: self.master.show_frame(WelcomeFrame),
                      width=250, height=35, fg_color="transparent", border_width=1, border_color="gray50").pack(
            pady=(0, 20))

    def login(self):
        # ... (login logic is unchanged) ...
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if admin_login(self.db, username, password):
            self.master.show_frame(AdminDashboardFrame)
        else:
            messagebox.showerror("Login Failed", "Invalid admin credentials.")

    def clear_fields(self):
        self.username_entry.delete(0, 'end')
        self.password_entry.delete(0, 'end')

    def on_show(self):
        self.clear_fields()


class AdminDashboardFrame(ctk.CTkFrame):
    # --- THIS CLASS HAS BEEN MODIFIED ---
    def __init__(self, master, db: DB, logo_image):
        super().__init__(master, fg_color="transparent")
        self.master = master;
        self.db = db;
        self.current_view = None
        self.grid_columnconfigure(1, weight=1);
        self.grid_rowconfigure(0, weight=1)
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0);
        self.sidebar.grid(row=0, column=0, sticky="nsw")
        ctk.CTkLabel(self.sidebar, text="Admin Menu", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)
        ctk.CTkButton(self.sidebar, text="Customer Management", command=self.show_customer_management).pack(pady=10,
                                                                                                            padx=20,
                                                                                                            fill="x")
        # --- NEW BUTTON ADDED HERE ---
        ctk.CTkButton(self.sidebar, text="View All Accounts", command=self.show_accounts_view).pack(pady=10, padx=20,
                                                                                                    fill="x")
        # --- END OF NEW BUTTON ---
        ctk.CTkButton(self.sidebar, text="Analytics", command=self.show_analytics).pack(pady=10, padx=20, fill="x")
        ctk.CTkButton(self.sidebar, text="Logout", command=lambda: self.master.show_frame(WelcomeFrame)).pack(
            side="bottom", pady=20, padx=20, fill="x")
        self.main_content = ctk.CTkFrame(self, fg_color="transparent");
        self.main_content.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    def on_show(self):
        self.show_customer_management()

    def _clear_content(self):
        for widget in self.main_content.winfo_children(): widget.destroy()

    def show_customer_management(self):
        self._clear_content()
        ctk.CTkLabel(self.main_content, text="Customer Management", font=ctk.CTkFont(size=24, weight="bold")).pack(
            anchor="w")
        controls_frame = ctk.CTkFrame(self.main_content, fg_color="transparent");
        controls_frame.pack(fill="x", pady=10)
        ctk.CTkButton(controls_frame, text="Delete Selected User", command=self.delete_selected_user).pack(side="left")
        columns = ("id", "fullname", "username", "phone_number", "pan_number")
        self.user_table = ttk.Treeview(self.main_content, columns=columns, show="headings")
        for col in columns: self.user_table.heading(col, text=col.title().replace("_", " "))
        self.user_table.pack(fill="both", expand=True, pady=10)
        self.refresh_user_table()

    def refresh_user_table(self):
        for i in self.user_table.get_children(): self.user_table.delete(i)
        for user in get_all_users(self.db): self.user_table.insert("", "end", values=(user['id'], user['fullname'],
                                                                                      user['username'],
                                                                                      user['phone_number'],
                                                                                      user['pan_number']))

    # --- NEW METHODS FOR VIEWING ACCOUNTS ---
    def show_accounts_view(self):
        """Clears the main content and displays a table of all customer accounts."""
        self._clear_content()
        ctk.CTkLabel(self.main_content, text="All Customer Accounts", font=ctk.CTkFont(size=24, weight="bold")).pack(
            anchor="w", pady=(0, 10))

        # Create the Treeview widget to display accounts
        columns = ("fullname", "account_number", "type", "balance")
        self.account_table = ttk.Treeview(self.main_content, columns=columns, show="headings")

        # Define column headings
        self.account_table.heading("fullname", text="Customer Name")
        self.account_table.heading("account_number", text="Account Number")
        self.account_table.heading("type", text="Account Type")
        self.account_table.heading("balance", text="Balance")

        # Configure column properties
        self.account_table.column("fullname", width=250)
        self.account_table.column("account_number", width=200)
        self.account_table.column("type", width=120)
        self.account_table.column("balance", width=150, anchor="e")  # Right-align the balance

        self.account_table.pack(fill="both", expand=True, pady=10)
        self.refresh_accounts_table()

    def refresh_accounts_table(self):
        """Fetches all account data and populates the account table."""
        # Clear any existing items in the table
        for item in self.account_table.get_children():
            self.account_table.delete(item)

        # Get data using the new function
        all_accounts = get_all_accounts_details(self.db)

        # Insert each account into the table
        for acc in all_accounts:
            # Format the balance with a currency symbol and comma separators
            balance_formatted = f"₹{acc['balance']:,.2f}"
            self.account_table.insert("", "end", values=(
                acc['fullname'],
                acc['account_number'],
                acc['account_type'],
                balance_formatted
            ))

    # --- END OF NEW METHODS ---

    def delete_selected_user(self):
        selected_item = self.user_table.selection()
        if not selected_item: return messagebox.showwarning("Warning", "Please select a user to delete.")
        user_id = self.user_table.item(selected_item[0])['values'][0]
        if messagebox.askyesno("Confirm Deletion",
                               f"Are you sure you want to delete user ID {user_id}? This is irreversible."):
            delete_user(self.db, user_id)
            self.refresh_user_table()
            messagebox.showinfo("Success", "User has been deleted.")

    # Replace the existing show_analytics method in AdminDashboardFrame with this one.

    def show_analytics(self):
        self._clear_content()
        ctk.CTkLabel(self.main_content, text="Bank Analytics", font=ctk.CTkFont(size=24, weight="bold")).pack(
            anchor="w")
        plot_frame = ctk.CTkFrame(self.main_content, fg_color="transparent");
        plot_frame.pack(fill="both", expand=True, pady=10)

        balance_data = get_users_by_balance(self.db)
        if balance_data:
            df_balance = pd.DataFrame(balance_data)

            # --- FIX APPLIED HERE ---
            # Ensure the 'balance' column is a numeric type before plotting
            df_balance['balance'] = pd.to_numeric(df_balance['balance'])
            # --- END OF FIX ---

            fig1, ax1 = plt.subplots(figsize=(6, 4))
            df_balance.plot(kind='bar', x='fullname', y='balance', ax=ax1, legend=False, color='#3b8ed0')
            ax1.set_title('Top 5 Customers by Balance');
            ax1.set_ylabel('Balance (₹)');
            ax1.set_xlabel('')
            plt.tight_layout()
            canvas1 = FigureCanvasTkAgg(fig1, master=plot_frame)
            canvas1.draw();
            canvas1.get_tk_widget().pack(side="left", fill="both", expand=True, padx=10)

        txn_data = get_users_by_transaction_count(self.db)
        if txn_data:
            df_txn = pd.DataFrame(txn_data)

            # --- FIX APPLIED HERE (for consistency) ---
            # Also ensure the 'transaction_count' column is numeric
            df_txn['transaction_count'] = pd.to_numeric(df_txn['transaction_count'])
            # --- END OF FIX ---

            fig2, ax2 = plt.subplots(figsize=(6, 4))
            df_txn.plot(kind='bar', x='fullname', y='transaction_count', ax=ax2, legend=False, color='#5cb85c')
            ax2.set_title('Top 5 Most Active Customers');
            ax2.set_ylabel('Number of Transactions');
            ax2.set_xlabel('')
            plt.tight_layout()
            canvas2 = FigureCanvasTkAgg(fig2, master=plot_frame)
            canvas2.draw();
            canvas2.get_tk_widget().pack(side="left", fill="both", expand=True, padx=10)