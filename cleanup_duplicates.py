import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import hashlib
from PIL import Image, ImageTk
import psutil
from tqdm import tqdm
import threading
import json
from datetime import datetime
import time
import csv
import sys
from pathlib import Path

class Deduplicationator3000:
    def __init__(self, root):
        self.root = root
        self.root.title("Deduplicationator 3000")
        self.root.geometry("1000x800")
        
        # Set theme colors
        self.bg_color = "#1a1a1a"
        self.accent_color = "#00ff00"
        self.text_color = "#ffffff"
        self.button_color = "#2d2d2d"
        self.hover_color = "#3d3d3d"
        self.warning_color = "#ff0000"
        
        # Configure root window
        self.root.configure(bg=self.bg_color)
        
        # Configure ttk styles
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Configure colors for all widgets
        self.style.configure('.',
            background=self.bg_color,
            foreground=self.text_color,
            fieldbackground=self.button_color,
            troughcolor=self.button_color,
            selectbackground=self.accent_color,
            selectforeground=self.bg_color
        )
        
        # Configure specific widget styles
        self.style.configure('TFrame', background=self.bg_color)
        self.style.configure('TLabel', background=self.bg_color, foreground=self.text_color)
        self.style.configure('TLabelframe', background=self.bg_color, foreground=self.text_color)
        self.style.configure('TLabelframe.Label', background=self.bg_color, foreground=self.accent_color)
        
        # Configure button styles
        self.style.configure('TButton',
            background=self.button_color,
            foreground=self.text_color,
            padding=10,
            font=('Arial', 10)
        )
        self.style.map('TButton',
            background=[('active', self.hover_color)],
            foreground=[('active', self.accent_color)]
        )
        
        # Configure entry style
        self.style.configure('TEntry',
            fieldbackground=self.button_color,
            foreground=self.text_color,
            insertcolor=self.accent_color
        )
        
        # Configure progress bar
        self.style.configure('Horizontal.TProgressbar',
            background=self.accent_color,
            troughcolor=self.button_color,
            bordercolor=self.accent_color,
            lightcolor=self.accent_color,
            darkcolor=self.accent_color
        )
        
        # Create main frame with scrollbar
        self.main_canvas = tk.Canvas(root, bg=self.bg_color, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(root, orient="vertical", command=self.main_canvas.yview)
        self.scrollable_frame = ttk.Frame(self.main_canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
        )
        
        self.main_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.main_canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.main_canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Title with cyberpunk styling
        title_frame = ttk.Frame(self.scrollable_frame)
        title_frame.pack(fill=tk.X, pady=20)
        
        title_label = ttk.Label(
            title_frame,
            text="Deduplicationator 3000",
            font=("Arial", 24, "bold"),
            foreground=self.accent_color
        )
        title_label.pack()
        
        # Directory selection with cyberpunk styling
        dir_frame = ttk.Frame(self.scrollable_frame)
        dir_frame.pack(fill=tk.X, pady=10)
        
        self.dir_entry = ttk.Entry(dir_frame, width=70)
        self.dir_entry.pack(side=tk.LEFT, padx=5)
        
        browse_btn = ttk.Button(
            dir_frame,
            text="Browse",
            command=self.browse_directory
        )
        browse_btn.pack(side=tk.LEFT, padx=5)
        
        # Options frame with cyberpunk styling
        options_frame = ttk.LabelFrame(
            self.scrollable_frame,
            text="Options",
            padding=10
        )
        options_frame.pack(fill=tk.X, pady=10)
        
        # File size limits
        size_frame = ttk.Frame(options_frame)
        size_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(size_frame, text="Min Size (MB):").pack(side=tk.LEFT)
        self.min_size = ttk.Entry(size_frame, width=10)
        self.min_size.pack(side=tk.LEFT, padx=5)
        self.min_size.insert(0, "0")
        
        ttk.Label(size_frame, text="Max Size (MB):").pack(side=tk.LEFT, padx=(20,0))
        self.max_size = ttk.Entry(size_frame, width=10)
        self.max_size.pack(side=tk.LEFT, padx=5)
        self.max_size.insert(0, "1000")
        
        # File extensions
        ext_frame = ttk.Frame(options_frame)
        ext_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(ext_frame, text="Skip Extensions:").pack(side=tk.LEFT)
        self.skip_extensions = ttk.Entry(ext_frame, width=50)
        self.skip_extensions.pack(side=tk.LEFT, padx=5)
        self.skip_extensions.insert(0, ".tmp,.temp,.log")
        
        # Action options
        action_frame = ttk.Frame(options_frame)
        action_frame.pack(fill=tk.X, pady=5)
        
        self.auto_delete = tk.BooleanVar(value=False)
        self.auto_delete_cb = ttk.Checkbutton(
            action_frame,
            text="Auto-delete duplicates",
            variable=self.auto_delete
        )
        self.auto_delete_cb.pack(side=tk.LEFT, padx=5)
        
        self.export_csv = tk.BooleanVar(value=True)
        self.export_csv_cb = ttk.Checkbutton(
            action_frame,
            text="Export to CSV",
            variable=self.export_csv
        )
        self.export_csv_cb.pack(side=tk.LEFT, padx=5)
        
        # Progress frame
        progress_frame = ttk.LabelFrame(
            self.scrollable_frame,
            text="Progress",
            padding=10
        )
        progress_frame.pack(fill=tk.X, pady=10)
        
        # Progress bar
        self.progress = ttk.Progressbar(
            progress_frame,
            length=300,
            mode='determinate',
            style='Horizontal.TProgressbar'
        )
        self.progress.pack(fill=tk.X, pady=5)
        
        # Statistics labels
        self.stats_frame = ttk.Frame(progress_frame)
        self.stats_frame.pack(fill=tk.X, pady=5)
        
        # Files processed
        self.files_processed_label = ttk.Label(
            self.stats_frame,
            text="Files Processed: 0",
            foreground=self.accent_color
        )
        self.files_processed_label.pack(anchor="w")
        
        # Duplicates found
        self.duplicates_label = ttk.Label(
            self.stats_frame,
            text="Duplicates Found: 0",
            foreground=self.accent_color
        )
        self.duplicates_label.pack(anchor="w")
        
        # Space saved
        self.space_saved_label = ttk.Label(
            self.stats_frame,
            text="Space to be Saved: 0 MB",
            foreground=self.accent_color
        )
        self.space_saved_label.pack(anchor="w")
        
        # Processing speed
        self.speed_label = ttk.Label(
            self.stats_frame,
            text="Processing Speed: 0 files/sec",
            foreground=self.accent_color
        )
        self.speed_label.pack(anchor="w")
        
        # Time remaining
        self.time_remaining_label = ttk.Label(
            self.stats_frame,
            text="Time Remaining: --:--",
            foreground=self.accent_color
        )
        self.time_remaining_label.pack(anchor="w")
        
        # Current file
        self.current_file_label = ttk.Label(
            self.stats_frame,
            text="Current File: None",
            foreground=self.accent_color
        )
        self.current_file_label.pack(anchor="w")
        
        # Status label with cyberpunk styling
        self.status_label = ttk.Label(
            self.scrollable_frame,
            text="Ready to scan",
            foreground=self.accent_color,
            font=('Arial', 10)
        )
        self.status_label.pack(pady=10)
        
        # Start button with cyberpunk styling
        self.start_btn = ttk.Button(
            self.scrollable_frame,
            text="START SCAN",
            command=self.start_scan,
            style='Accent.TButton'
        )
        self.start_btn.pack(pady=20)
        
        # Configure accent button style
        self.style.configure('Accent.TButton',
            background=self.accent_color,
            foreground=self.bg_color,
            font=('Arial', 12, 'bold'),
            padding=15
        )
        self.style.map('Accent.TButton',
            background=[('active', self.hover_color)],
            foreground=[('active', self.accent_color)]
        )
        
        # Initialize statistics
        self.start_time = None
        self.files_processed = 0
        self.duplicates_found = 0
        self.space_saved = 0
        self.last_update = time.time()
        self.files_per_second = 0
        self.speed_samples = []  # For rolling average
        self.max_samples = 10    # Number of samples for rolling average
        
        # Add Documents folder path
        self.documents_folder = str(Path.home() / "Documents")
        
    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, directory)
    
    def update_statistics(self):
        current_time = time.time()
        elapsed = current_time - self.start_time
        
        # Calculate current speed
        if elapsed > 0:
            current_speed = self.files_processed / elapsed
            
            # Update rolling average
            self.speed_samples.append(current_speed)
            if len(self.speed_samples) > self.max_samples:
                self.speed_samples.pop(0)
            
            # Calculate average speed
            self.files_per_second = sum(self.speed_samples) / len(self.speed_samples)
        
        # Update labels
        self.files_processed_label.configure(
            text=f"Files Processed: {self.files_processed:,}"
        )
        self.duplicates_label.configure(
            text=f"Duplicates Found: {self.duplicates_found:,}"
        )
        self.space_saved_label.configure(
            text=f"Space to be Saved: {self.space_saved / (1024*1024):,.2f} MB"
        )
        self.speed_label.configure(
            text=f"Processing Speed: {self.files_per_second:.1f} files/sec",
            font=('Arial', 10, 'bold'),  # Make speed more prominent
            foreground=self.accent_color
        )
    
    def start_scan(self):
        directory = self.dir_entry.get()
        if not directory or not os.path.exists(directory):
            messagebox.showerror("Error", "Please select a valid directory")
            return
        
        # Reset statistics
        self.start_time = time.time()
        self.files_processed = 0
        self.duplicates_found = 0
        self.space_saved = 0
        self.last_update = time.time()
        self.files_per_second = 0
        self.speed_samples = []  # Reset speed samples
        
        # Disable start button during scan
        self.start_btn.configure(state='disabled')
        self.status_label.configure(text="Scanning...")
        
        # Start scan in a separate thread
        thread = threading.Thread(target=self.scan_directory, args=(directory,))
        thread.daemon = True
        thread.start()
    
    def get_safe_csv_path(self):
        """Get a safe path for the CSV file in the Documents folder."""
        try:
            # Create a Deduplicationator3000 folder in Documents if it doesn't exist
            output_dir = os.path.join(self.documents_folder, "Deduplicationator3000")
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate timestamp and filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"duplicates_{timestamp}.csv"
            
            # Return full path
            return os.path.join(output_dir, filename)
        except Exception as e:
            messagebox.showerror("Error", f"Could not create output directory: {str(e)}")
            return None

    def scan_directory(self, directory):
        try:
            # Get file size limits
            min_size = float(self.min_size.get()) * 1024 * 1024  # Convert MB to bytes
            max_size = float(self.max_size.get()) * 1024 * 1024
            
            # Get skip extensions
            skip_extensions = set(ext.strip() for ext in self.skip_extensions.get().split(','))
            
            # Initialize progress tracking
            self.files_processed = 0
            self.duplicates_found = 0
            self.space_saved = 0
            self.start_time = time.time()
            self.last_update = time.time()
            self.files_per_second = 0
            self.speed_samples = []  # Reset speed samples
            
            # Process files as we find them
            hashes = {}
            for root, _, filenames in os.walk(directory):
                for filename in filenames:
                    try:
                        filepath = os.path.join(root, filename)
                        size = os.path.getsize(filepath)
                        ext = os.path.splitext(filename)[1].lower()
                        
                        if min_size <= size <= max_size and ext not in skip_extensions:
                            # Update current file
                            self.current_file_label.configure(
                                text=f"Current File: {os.path.basename(filepath)}"
                            )
                            
                            with open(filepath, 'rb') as f:
                                file_hash = hashlib.sha256(f.read()).hexdigest()
                                if file_hash in hashes:
                                    hashes[file_hash].append(filepath)
                                    self.duplicates_found += 1
                                    self.space_saved += size
                                else:
                                    hashes[file_hash] = [filepath]
                            
                            self.files_processed += 1
                            
                            # Update statistics every 0.5 seconds
                            current_time = time.time()
                            if current_time - self.last_update >= 0.5:
                                self.update_statistics()
                                self.last_update = current_time
                            
                    except Exception as e:
                        print(f"Error processing {filepath}: {e}")
                        continue
            
            # Find duplicates
            duplicates = {h: files for h, files in hashes.items() if len(files) > 1}
            
            # Export to CSV if requested
            if self.export_csv.get():
                csv_path = self.get_safe_csv_path()
                if csv_path:
                    try:
                        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerow(['Hash', 'File Path', 'Size (bytes)', 'Last Modified'])
                            for hash_value, file_list in duplicates.items():
                                for filepath in file_list:
                                    writer.writerow([
                                        hash_value,
                                        filepath,
                                        os.path.getsize(filepath),
                                        datetime.fromtimestamp(os.path.getmtime(filepath))
                                    ])
                        self.status_label.configure(
                            text=f"Exported results to {csv_path}"
                        )
                    except Exception as e:
                        messagebox.showerror("Export Error", 
                            f"Could not export to CSV: {str(e)}\n\n"
                            f"Please ensure you have write permissions to:\n{csv_path}")
            
            # Auto-delete if requested
            if self.auto_delete.get() and duplicates:
                for hash_value, file_list in duplicates.items():
                    # Keep the most recently modified file
                    files_with_mtime = [(f, os.path.getmtime(f)) for f in file_list]
                    files_with_mtime.sort(key=lambda x: x[1], reverse=True)
                    for filepath, _ in files_with_mtime[1:]:  # Skip the first (most recent) file
                        try:
                            os.remove(filepath)
                        except Exception as e:
                            print(f"Error deleting {filepath}: {e}")
            
            # Update status
            if duplicates:
                self.status_label.configure(
                    text=f"Found {len(duplicates)} sets of duplicate files"
                )
                if self.auto_delete.get():
                    self.status_label.configure(
                        text=f"Deleted {self.duplicates_found} duplicate files"
                    )
                if self.export_csv.get():
                    self.status_label.configure(
                        text=f"Exported results to {csv_path}"
                    )
            else:
                self.status_label.configure(text="No duplicates found")
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            self.start_btn.configure(state='normal')
            self.current_file_label.configure(text="Current File: None")

if __name__ == "__main__":
    root = tk.Tk()
    app = Deduplicationator3000(root)
    root.mainloop() 