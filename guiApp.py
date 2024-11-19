import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
from threading import Thread
import sys
import json
import os
from datetime import datetime, timedelta
import csv
import time
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sqlite3
from DownloadProducts import main as web_scraping_main
from UploadProduts import main as uploading_main
import sqlite_utils
import webbrowser
import logging

def is_number(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

def update_message_text_scraping(message):
    message_text_scraping.config(state=tk.NORMAL)
    message_text_scraping.insert(tk.END, message + "\n")
    message_text_scraping.see(tk.END)
    message_text_scraping.config(state=tk.DISABLED)

def update_message_text_uploading(message):
    message_text_uploading.config(state=tk.NORMAL)
    message_text_uploading.insert(tk.END, message + "\n")
    message_text_uploading.see(tk.END)
    message_text_uploading.config(state=tk.DISABLED)

def create_default_values_table():
    db = sqlite_utils.Database("uploaded_products.db")
    try:
        if "default_values" not in db.table_names():
            db["default_values"].create({
                "name": str,
                "value": str
            }, pk="name")
    except Exception as e:
        print(f"Error creating default_values table: {str(e)}")
    finally:
        db.close()

def save_default_value(key, value):
    db = sqlite_utils.Database("uploaded_products.db")
    try:
        db["default_values"].upsert({"name": key, "value": value}, ["name"])
    except Exception as e:
        print(f"Error saving default value: {str(e)}")
    finally:
        db.close()

def create_statistics_table():
    db = sqlite_utils.Database("uploaded_products.db")
    try:
        if "statistics" not in db.table_names():
            db["statistics"].create({
                "timestamp": str,
                "operation": str,
                "category": str,
                "sub_category": str,
                "products_count": int,
                "success": bool,
                "duration": float,
                "error": str
            })
    except Exception as e:
        print(f"Error creating statistics table: {str(e)}")
    finally:
        db.close()

def save_statistics(operation, category, sub_category, products_count, success, duration, error=""):
    db = sqlite_utils.Database("uploaded_products.db")
    try:
        db["statistics"].insert({
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "category": category,
            "sub_category": sub_category,
            "products_count": products_count,
            "success": success,
            "duration": duration,
            "error": error
        })
    except Exception as e:
        print(f"Error saving statistics: {str(e)}")
    finally:
        db.close()

def export_statistics():
    try:
        db = sqlite_utils.Database("uploaded_products.db")
        stats = list(db["statistics"].rows)
        
        if not stats:
            messagebox.showinfo("Export Statistics", "No statistics available to export.")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Export Statistics"
        )
        
        if file_path:
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=stats[0].keys())
                writer.writeheader()
                writer.writerows(stats)
            messagebox.showinfo("Export Complete", f"Statistics exported to {file_path}")
    except Exception as e:
        messagebox.showerror("Export Error", f"Error exporting statistics: {str(e)}")

def view_product_preview():
    try:
        products_dir = os.path.join(os.getcwd(), "products")
        if not os.path.exists(products_dir):
            messagebox.showinfo("Preview", "No products available to preview.")
            return
            
        categories = [d for d in os.listdir(products_dir) 
                     if os.path.isdir(os.path.join(products_dir, d))]
        
        if not categories:
            messagebox.showinfo("Preview", "No products available to preview.")
            return
            
        preview_window = tk.Toplevel(app)
        preview_window.title("Product Preview")
        preview_window.geometry("800x600")
        
        tree = ttk.Treeview(preview_window, columns=("Category", "Subcategory", "Products"), show="headings")
        tree.heading("Category", text="Category")
        tree.heading("Subcategory", text="Subcategory")
        tree.heading("Products", text="Products")
        
        scrollbar = ttk.Scrollbar(preview_window, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        for category in categories:
            category_path = os.path.join(products_dir, category)
            subcategories = [d for d in os.listdir(category_path) 
                           if os.path.isdir(os.path.join(category_path, d))]
            
            for subcategory in subcategories:
                subcategory_path = os.path.join(category_path, subcategory)
                products = len([f for f in os.listdir(subcategory_path) 
                              if os.path.isdir(os.path.join(subcategory_path, f))])
                
                tree.insert("", "end", values=(category, subcategory, products))
    
    except Exception as e:
        messagebox.showerror("Preview Error", f"Error showing preview: {str(e)}")

def open_products_folder():
    products_dir = os.path.join(os.getcwd(), "products")
    if os.path.exists(products_dir):
        webbrowser.open(products_dir)
    else:
        messagebox.showinfo("Open Folder", "Products folder does not exist yet.")

class StdoutRedirector:
    def __init__(self, text_widget, status_label=None):
        self.text_widget = text_widget
        self.status_label = status_label
        self.buffer = ""

    def write(self, message):
        self.buffer += message
        if '\n' in self.buffer:
            lines = self.buffer.split('\n')
            self.buffer = lines[-1]
            complete_lines = '\n'.join(lines[:-1])
            if complete_lines:
                self.text_widget.configure(state='normal')
                self.text_widget.insert(tk.END, complete_lines + '\n')
                self.text_widget.see(tk.END)
                self.text_widget.configure(state='disabled')
                if self.status_label:
                    self.status_label.configure(text=complete_lines.strip())

    def flush(self):
        if self.buffer:
            self.text_widget.configure(state='normal')
            self.text_widget.insert(tk.END, self.buffer)
            self.text_widget.see(tk.END)
            self.text_widget.configure(state='disabled')
            self.buffer = ""

def create_progress_frame(parent):
    frame = ttk.Frame(parent, style='Card.TFrame')
    frame.pack(fill='x', padx=20, pady=(0, 20))
    
    status_label = ttk.Label(frame, text="Ready", font=('Segoe UI', 10))
    status_label.pack(fill='x', padx=10, pady=(10, 5))
    
    progress = ttk.Progressbar(frame, mode='indeterminate', style='Accent.Horizontal.TProgressbar')
    progress.pack(fill='x', padx=10, pady=(0, 10))
    
    return frame, status_label, progress

def start_web_scraping(category, sub_category, url, class_name, count_class_name, exchange_rate):
    start_time = datetime.now()
    products_count = 0
    success = False
    error_msg = ""
    
    try:
        save_default_value("class_name", class_name)
        save_default_value("count_class_name", count_class_name)
        save_default_value("exchange_rate", exchange_rate)
        
        status_label_scraping.configure(text="Starting web scraping...")
        progress_bar_scraping.start(10)
        
        original_stdout = sys.stdout
        sys.stdout = StdoutRedirector(log_text, status_label_scraping)
        
        web_scraping_main(category, sub_category, url, class_name, count_class_name, exchange_rate)
        
        products_dir = os.path.join("products", category, sub_category)
        if os.path.exists(products_dir):
            products_count = len([d for d in os.listdir(products_dir) 
                                if os.path.isdir(os.path.join(products_dir, d))])
        
        success = True
        status_label_scraping.configure(text="Web scraping completed successfully!", foreground=COLORS['success'])
    except Exception as e:
        error_msg = str(e)
        status_label_scraping.configure(text=f"Error: {error_msg}", foreground=COLORS['danger'])
        messagebox.showerror("Error", f"An error occurred: {error_msg}")
    finally:
        duration = (datetime.now() - start_time).total_seconds()
        save_statistics("scraping", category, sub_category, products_count, success, duration, error_msg)
        update_statistics_view()
        sys.stdout = original_stdout
        progress_bar_scraping.stop()

def start_uploading(category, sub_category, max_products):
    start_time = datetime.now()
    success = False
    error_msg = ""
    
    try:
        status_label_uploading.configure(text="Starting product upload...")
        progress_bar_uploading.start(10)
        
        original_stdout = sys.stdout
        sys.stdout = StdoutRedirector(log_text, status_label_uploading)
        
        uploading_main(category, sub_category, max_products)
        
        success = True
        status_label_uploading.configure(text="Product upload completed successfully!", foreground=COLORS['success'])
    except Exception as e:
        error_msg = str(e)
        status_label_uploading.configure(text=f"Error: {error_msg}", foreground=COLORS['danger'])
        messagebox.showerror("Error", f"An error occurred: {error_msg}")
    finally:
        duration = (datetime.now() - start_time).total_seconds()
        save_statistics("uploading", category, sub_category, int(max_products), success, duration, error_msg)
        update_statistics_view()
        sys.stdout = original_stdout
        progress_bar_uploading.stop()

def start_web_scraping_in_thread():
    category = category_entry_scraping.get().strip()
    sub_category = sub_category_entry_scraping.get().strip()
    url = url_entry_scraping.get().strip()
    class_name = class_name_entry_scraping.get().strip()
    count_class_name = total_count_entry_scraping.get().strip()
    exchange_rate = exchange_rate_entry_scraping.get().strip()

    if not category or not sub_category or not url:
        messagebox.showwarning("Warning", "Please enter Category, Sub-Category, and URL.")
        return

    if not class_name:
        messagebox.showwarning("Warning", "Please enter Class Name.")
        return

    if not count_class_name:
        messagebox.showwarning("Warning", "Please enter Class Name.")
        return

    if not exchange_rate or not is_number(exchange_rate):
        messagebox.showwarning("Warning", "Exchange Rate must be a valid number.")
        return

    thread = Thread(target=start_web_scraping, args=(category, sub_category, url, class_name, count_class_name, exchange_rate))
    thread.start()

def start_uploading_in_thread():
    category = category_entry_uploading.get().strip()
    sub_category = sub_category_entry_uploading.get().strip()
    max_products = max_products_entry_uploading.get().strip()

    if not category or not sub_category or not max_products:
        messagebox.showwarning("Warning", "Please enter Category, Sub-Category, and Maximum Products.")
        return

    if not is_number(max_products):
        messagebox.showwarning("Warning", "Maximum products must be a valid number.")
        return

    thread = Thread(target=start_uploading, args=(category, sub_category, int(max_products)))
    thread.start()

def process_batch_file():
    file_path = filedialog.askopenfilename(
        title="Select Batch File",
        filetypes=[("CSV files", "*.csv")]
    )
    
    if not file_path:
        return
        
    try:
        df = pd.read_csv(file_path)
        batch_window = tk.Toplevel(app)
        batch_window.title("Batch Processing")
        batch_window.geometry("600x400")
        
        tree = ttk.Treeview(batch_window, columns=("Category", "Subcategory", "URL", "Status"), show="headings")
        tree.heading("Category", text="Category")
        tree.heading("Subcategory", text="Subcategory")
        tree.heading("URL", text="URL")
        tree.heading("Status", text="Status")
        
        tree.column("Category", width=100)
        tree.column("Subcategory", width=100)
        tree.column("URL", width=250)
        tree.column("Status", width=100)
        
        for _, row in df.iterrows():
            tree.insert("", "end", values=(row['category'], row['subcategory'], row['url'], "Pending"))
        
        tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        def start_batch():
            for item in tree.get_children():
                values = tree.item(item)['values']
                category, subcategory, url = values[:3]
                
                try:
                    tree.item(item, values=(category, subcategory, url, "Processing"))
                    batch_window.update()
                    
                    start_web_scraping(category, subcategory, url, 
                                    class_name_entry_scraping.get(),
                                    total_count_entry_scraping.get(),
                                    exchange_rate_entry_scraping.get())
                    
                    tree.item(item, values=(category, subcategory, url, "Complete"))
                except Exception as e:
                    tree.item(item, values=(category, subcategory, url, "Failed"))
                
                batch_window.update()
        
        ttk.Button(batch_window, text="Start Batch", command=start_batch).pack(pady=10)
        
    except Exception as e:
        messagebox.showerror("Batch Error", f"Error processing batch file: {str(e)}")

def show_analytics():
    analytics_window = tk.Toplevel(app)
    analytics_window.title("Analytics Dashboard")
    analytics_window.geometry("800x600")
    
    notebook = ttk.Notebook(analytics_window)
    notebook.pack(fill="both", expand=True, padx=10, pady=10)
    
    success_frame = ttk.Frame(notebook)
    notebook.add(success_frame, text="Success Rate")
    
    db = sqlite_utils.Database("uploaded_products.db")
    stats = list(db["statistics"].rows)
    df = pd.DataFrame(stats)
    
    if not df.empty:
        fig, ax = plt.subplots(figsize=(6, 4))
        success_counts = df['success'].value_counts()
        ax.pie(success_counts, labels=['Success', 'Failed'], autopct='%1.1f%%')
        ax.set_title('Operation Success Rate')
        
        canvas = FigureCanvasTkAgg(fig, success_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
    
    products_frame = ttk.Frame(notebook)
    notebook.add(products_frame, text="Products per Category")
    
    if not df.empty:
        fig, ax = plt.subplots(figsize=(6, 4))
        df.groupby('category')['products_count'].sum().plot(kind='bar', ax=ax)
        ax.set_title('Products per Category')
        plt.xticks(rotation=45)
        
        canvas = FigureCanvasTkAgg(fig, products_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

def show_settings():
    settings_window = tk.Toplevel(app)
    settings_window.title("Settings")
    settings_window.geometry("400x500")
    
    ttk.Label(settings_window, text="Application Settings", 
             font=('Segoe UI', 14, 'bold')).pack(pady=10)
    
    theme_frame = ttk.LabelFrame(settings_window, text="Theme")
    theme_frame.pack(fill="x", padx=10, pady=5)
    
    theme_var = tk.StringVar(value="light")
    ttk.Radiobutton(theme_frame, text="Light Theme", 
                    variable=theme_var, value="light").pack(padx=10, pady=5)
    ttk.Radiobutton(theme_frame, text="Dark Theme", 
                    variable=theme_var, value="dark").pack(padx=10, pady=5)
    
    autosave_frame = ttk.LabelFrame(settings_window, text="Auto-save")
    autosave_frame.pack(fill="x", padx=10, pady=5)
    
    autosave_var = tk.BooleanVar(value=True)
    ttk.Checkbutton(autosave_frame, text="Enable auto-save", 
                    variable=autosave_var).pack(padx=10, pady=5)
    
    def save_settings():
        db = sqlite_utils.Database("uploaded_products.db")
        if "settings" not in db.table_names():
            db["settings"].create({
                "name": str,
                "value": str
            }, pk="name")
        
        db["settings"].upsert({
            "name": "theme",
            "value": theme_var.get()
        }, pk="name")
        
        db["settings"].upsert({
            "name": "autosave",
            "value": str(autosave_var.get())
        }, pk="name")
        
        messagebox.showinfo("Settings", "Settings saved successfully!")
        settings_window.destroy()
    
    ttk.Button(settings_window, text="Save Settings", 
               command=save_settings).pack(pady=10)

def update_statistics_view():
    for item in stats_tree.get_children():
        stats_tree.delete(item)
    
    try:
        db = sqlite_utils.Database("uploaded_products.db")
        stats = list(db["statistics"].rows)
        
        for stat in stats:
            status = "Success" if stat["success"] else "Failed"
            stats_tree.insert("", "end", values=(
                stat["timestamp"],
                stat["operation"],
                f"{stat['category']}/{stat['sub_category']}",
                stat["products_count"],
                status,
                f"{stat['duration']:.2f}"
            ))
    except Exception as e:
        print(f"Error updating statistics view: {str(e)}")

logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s',
                   datefmt='%Y-%m-%d %H:%M:%S')

class TextHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text_widget.configure(state='normal')
            self.text_widget.insert(tk.END, msg + '\n')
            self.text_widget.see(tk.END)
            self.text_widget.configure(state='disabled')
        self.text_widget.after(0, append)

app = tk.Tk()
app.title("YOKI - Product Management Suite")
app.geometry("900x700")
app.configure(bg="#f0f0f0")

COLORS = {
    'primary': '#2557a7',
    'secondary': '#6c757d',
    'success': '#28a745',
    'warning': '#ffc107',
    'danger': '#dc3545',
    'background': '#f8f9fa',
    'card': '#ffffff',
    'text': '#212529',
    'border': '#dee2e6'
}

style = ttk.Style()
style.theme_use('clam')

style.configure('Card.TFrame',
                background=COLORS['card'],
                relief='solid',
                borderwidth=1)

style.configure('Tab.TFrame',
                background=COLORS['background'])

style.configure('Primary.TButton',
                font=('Segoe UI', 11),
                background=COLORS['primary'],
                foreground='white',
                padding=(20, 10))

style.configure('Secondary.TButton',
                font=('Segoe UI', 11),
                background=COLORS['secondary'],
                foreground='white',
                padding=(20, 10))

style.configure('Accent.Horizontal.TProgressbar',
                troughcolor=COLORS['background'],
                background=COLORS['primary'],
                thickness=6)

style.configure('Header.TLabel', 
                font=('Segoe UI', 24, 'bold'), 
                foreground=COLORS['primary'],
                background=COLORS['background'])

style.configure('Subheader.TLabel',
                font=('Segoe UI', 12),
                foreground=COLORS['secondary'],
                background=COLORS['background'])

main_container = ttk.Frame(app, style='Tab.TFrame')
main_container.pack(fill='both', expand=True, padx=20, pady=20)

header_frame = ttk.Frame(main_container, style='Tab.TFrame')
header_frame.pack(fill='x', pady=(0, 20))

header_label = ttk.Label(header_frame, 
                        text="YOKI", 
                        style='Header.TLabel')
header_label.pack(side='left')

subheader_label = ttk.Label(header_frame,
                           text="Product Management Suite",
                           style='Subheader.TLabel')
subheader_label.pack(side='left', padx=(10, 0), pady=(10, 0))

notebook = ttk.Notebook(main_container)
notebook.pack(fill='both', expand=True)

scraping_frame = ttk.Frame(notebook, style='Tab.TFrame')

scraping_inputs = ttk.Frame(scraping_frame, style='Card.TFrame')
scraping_inputs.pack(fill='x', padx=20, pady=20)

row = 0
paddings = {'padx': 15, 'pady': 10}

ttk.Label(scraping_inputs, text="Web Scraping Configuration", 
          font=('Segoe UI', 16, 'bold'),
          foreground=COLORS['primary']).grid(row=row, column=0, columnspan=2, **paddings)
row += 1

ttk.Label(scraping_inputs, text="Category:", 
          font=('Segoe UI', 11)).grid(row=row, column=0, sticky='w', **paddings)
category_entry_scraping = ttk.Entry(scraping_inputs, font=('Segoe UI', 11))
category_entry_scraping.grid(row=row, column=1, sticky='ew', **paddings)
row += 1

ttk.Label(scraping_inputs, text="Sub-Category:", 
          font=('Segoe UI', 11)).grid(row=row, column=0, sticky='w', **paddings)
sub_category_entry_scraping = ttk.Entry(scraping_inputs, font=('Segoe UI', 11))
sub_category_entry_scraping.grid(row=row, column=1, sticky='ew', **paddings)
ttk.Label(scraping_inputs, text="Use '.' to separate multiple sub-categories",
          font=('Segoe UI', 9), foreground=COLORS['secondary']).grid(row=row+1, column=1, sticky='w', padx=15)
row += 2

ttk.Label(scraping_inputs, text="URL:", 
          font=('Segoe UI', 11)).grid(row=row, column=0, sticky='w', **paddings)
url_entry_scraping = ttk.Entry(scraping_inputs, font=('Segoe UI', 11))
url_entry_scraping.grid(row=row, column=1, sticky='ew', **paddings)
row += 1

class_names_frame = ttk.LabelFrame(scraping_inputs, text="Class Names", padding=10)
class_names_frame.grid(row=row, column=0, columnspan=2, sticky='ew', **paddings)

ttk.Label(class_names_frame, text="Total Count:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
total_count_entry_scraping = ttk.Entry(class_names_frame)
total_count_entry_scraping.grid(row=0, column=1, sticky='ew', padx=5, pady=5)

ttk.Label(class_names_frame, text="Sponsored Product:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
class_name_entry_scraping = ttk.Entry(class_names_frame)
class_name_entry_scraping.grid(row=1, column=1, sticky='ew', padx=5, pady=5)
row += 1

ttk.Label(scraping_inputs, text="Exchange Rate (AED to ETB):", 
          font=('Segoe UI', 11)).grid(row=row, column=0, sticky='w', **paddings)
exchange_rate_entry_scraping = ttk.Entry(scraping_inputs, font=('Segoe UI', 11))
exchange_rate_entry_scraping.grid(row=row, column=1, sticky='ew', **paddings)
row += 1

scraping_inputs.grid_columnconfigure(1, weight=1)

button_frame = ttk.Frame(scraping_frame, style='Tab.TFrame')
button_frame.pack(fill='x', padx=20, pady=10)

start_button_scraping = ttk.Button(button_frame, 
                                 text="Start Web Scraping", 
                                 command=start_web_scraping_in_thread,
                                 style='Primary.TButton')
start_button_scraping.pack(side='left', padx=5)

progress_frame_scraping, status_label_scraping, progress_bar_scraping = create_progress_frame(scraping_frame)

uploading_frame = ttk.Frame(notebook, style='Tab.TFrame')

uploading_inputs = ttk.Frame(uploading_frame, style='Card.TFrame')
uploading_inputs.pack(fill='x', padx=20, pady=20)

row = 0
ttk.Label(uploading_inputs, text="Product Upload Configuration", 
          font=('Segoe UI', 16, 'bold'),
          foreground=COLORS['primary']).grid(row=row, column=0, columnspan=2, **paddings)
row += 1

ttk.Label(uploading_inputs, text="Category:", 
          font=('Segoe UI', 11)).grid(row=row, column=0, sticky='w', **paddings)
category_entry_uploading = ttk.Entry(uploading_inputs, font=('Segoe UI', 11))
category_entry_uploading.grid(row=row, column=1, sticky='ew', **paddings)
row += 1

ttk.Label(uploading_inputs, text="Sub-Category:", 
          font=('Segoe UI', 11)).grid(row=row, column=0, sticky='w', **paddings)
sub_category_entry_uploading = ttk.Entry(uploading_inputs, font=('Segoe UI', 11))
sub_category_entry_uploading.grid(row=row, column=1, sticky='ew', **paddings)
ttk.Label(uploading_inputs, text="Use '.' to separate multiple sub-categories",
          font=('Segoe UI', 9), foreground=COLORS['secondary']).grid(row=row+1, column=1, sticky='w', padx=15)
row += 2

ttk.Label(uploading_inputs, text="Max Products:", 
          font=('Segoe UI', 11)).grid(row=row, column=0, sticky='w', **paddings)
max_products_entry_uploading = ttk.Entry(uploading_inputs, font=('Segoe UI', 11))
max_products_entry_uploading.grid(row=row, column=1, sticky='ew', **paddings)
row += 1

uploading_inputs.grid_columnconfigure(1, weight=1)

button_frame_upload = ttk.Frame(uploading_frame, style='Tab.TFrame')
button_frame_upload.pack(fill='x', padx=20, pady=10)

start_button_uploading = ttk.Button(button_frame_upload, 
                                  text="Start Uploading", 
                                  command=start_uploading_in_thread,
                                  style='Primary.TButton')
start_button_uploading.pack(side='left', padx=5)

progress_frame_uploading, status_label_uploading, progress_bar_uploading = create_progress_frame(uploading_frame)

logging_frame = ttk.Frame(notebook, style='Tab.TFrame')

log_container = ttk.Frame(logging_frame, style='Card.TFrame')
log_container.pack(fill='both', expand=True, padx=20, pady=20)

ttk.Label(log_container, 
         text="Process Output", 
         font=('Segoe UI', 16, 'bold'),
         foreground=COLORS['primary']).pack(pady=(0, 10))

log_text = scrolledtext.ScrolledText(log_container,
                                   wrap=tk.WORD,
                                   width=80,
                                   height=20,
                                   font=('Consolas', 10),
                                   bg='white',
                                   relief='flat')
log_text.pack(fill='both', expand=True, padx=10, pady=10)
log_text.configure(state='disabled')

button_frame_log = ttk.Frame(log_container)
button_frame_log.pack(fill='x', padx=10, pady=(0, 10))

def clear_logs():
    log_text.configure(state='normal')
    log_text.delete(1.0, tk.END)
    log_text.configure(state='disabled')
    status_label_scraping.configure(text="Ready", foreground=COLORS['text'])
    status_label_uploading.configure(text="Ready", foreground=COLORS['text'])

clear_button = ttk.Button(button_frame_log,
                         text="Clear Output",
                         command=clear_logs,
                         style='Secondary.TButton')
clear_button.pack(side='right', padx=5)

statistics_frame = ttk.Frame(notebook, style='Tab.TFrame')

stats_container = ttk.Frame(statistics_frame, style='Card.TFrame')
stats_container.pack(fill='both', expand=True, padx=20, pady=20)

ttk.Label(stats_container, 
         text="Operation Statistics", 
         font=('Segoe UI', 16, 'bold'),
         foreground=COLORS['primary']).pack(pady=(0, 10))

stats_tree = ttk.Treeview(stats_container, 
                         columns=("Timestamp", "Operation", "Category", "Products", "Status", "Duration"),
                         show="headings",
                         height=10)

stats_tree.heading("Timestamp", text="Timestamp")
stats_tree.heading("Operation", text="Operation")
stats_tree.heading("Category", text="Category")
stats_tree.heading("Products", text="Products")
stats_tree.heading("Status", text="Status")
stats_tree.heading("Duration", text="Duration (s)")

stats_tree.column("Timestamp", width=150)
stats_tree.column("Operation", width=100)
stats_tree.column("Category", width=150)
stats_tree.column("Products", width=80)
stats_tree.column("Status", width=80)
stats_tree.column("Duration", width=100)

stats_scroll = ttk.Scrollbar(stats_container, orient="vertical", command=stats_tree.yview)
stats_tree.configure(yscrollcommand=stats_scroll.set)

stats_tree.pack(side="left", fill="both", expand=True)
stats_scroll.pack(side="right", fill="y")

refresh_button = ttk.Button(stats_container,
                          text="Refresh",
                          command=update_statistics_view,
                          style='Secondary.TButton')
refresh_button.pack(pady=10)

menu_bar = tk.Menu(app)
app.config(menu=menu_bar)

file_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Export Statistics", command=export_statistics)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=app.quit)

view_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="View", menu=view_menu)
view_menu.add_command(label="Product Preview", command=view_product_preview)
view_menu.add_command(label="Open Products Folder", command=open_products_folder)

create_default_values_table()
create_statistics_table()

notebook.add(scraping_frame, text="Web Scraping")
notebook.add(uploading_frame, text="Upload Products")
notebook.add(statistics_frame, text="Statistics")
notebook.add(logging_frame, text="Process Output")

style.configure('TNotebook.Tab', padding=[12, 8], font=('Segoe UI', 10))
style.map('TNotebook.Tab', background=[('selected', COLORS['primary'])],
          foreground=[('selected', 'white')])

db = sqlite_utils.Database("uploaded_products.db")
class_name_row = db["default_values"].get("class_name")
if class_name_row and "value" in class_name_row:
    class_name_entry_scraping.insert(0, class_name_row["value"])

count_class_name_row = db["default_values"].get("count_class_name")
if count_class_name_row and "value" in count_class_name_row:
    total_count_entry_scraping.insert(0, count_class_name_row["value"])

exchange_rate_row = db["default_values"].get("exchange_rate")
if exchange_rate_row and "value" in exchange_rate_row:
    exchange_rate_entry_scraping.insert(0, exchange_rate_row["value"])

db.close()

tools_menu = tk.Menu(menu_bar, tearoff=0)
tools_menu.add_command(label="Batch Processing", command=process_batch_file)
menu_bar.add_cascade(label="Tools", menu=tools_menu)

settings_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Settings", menu=settings_menu)
settings_menu.add_command(label="Preferences", command=show_settings)

app.mainloop()
