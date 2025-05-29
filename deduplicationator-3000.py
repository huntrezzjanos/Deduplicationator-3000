"""
Deduplicationator 3000

A futuristic GUI application that helps users find and remove duplicate files efficiently.
The application uses advanced file size and SHA-256 hashing to identify duplicates,
with configurable size limits and file extension filters.

Key Features:
- Cyberpunk-inspired GUI interface
- Configurable file size limits
- Customizable file extension filters
- Real-time progress tracking with retro effects
- Batch processing for better performance
- Multi-threaded file hashing
- Detailed progress and statistics
- CSV export of duplicate files
"""

import os
import hashlib
import logging
from collections import defaultdict
import time
from pathlib import Path
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
import psutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from datetime import datetime
from PIL import Image, ImageTk, ImageDraw
import math
import csv

# Custom colors
CYBER_PINK = "#FF00FF"
CYBER_GREEN = "#00FF00"
CYBER_ORANGE = "#FF6B00"
CYBER_PURPLE = "#9D00FF"
CYBER_BLACK = "#0A0A0A"
CYBER_WHITE = "#FFFFFF"

def calculate_file_hash(filepath, chunk_size=1024*1024*4):  # 4MB chunks
    """
    Calculate SHA-256 hash of a file using chunked reading for memory efficiency.
    
    Args:
        filepath (str): Path to the file to hash
        chunk_size (int): Size of chunks to read (default: 4MB)
        
    Returns:
        str: SHA-256 hash of the file, or None if an error occurs
    """
    try:
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(chunk_size), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logging.error(f"Error calculating hash for {filepath}: {str(e)}")
        return None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    filename="dedup_debug.log",
    filemode='w',
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default configuration values
MIN_FILE_SIZE = 1024 * 1024 * 1024 * 10  # 10GB
MAX_FILE_SIZE = 1024 * 1024 * 1024 * 300  # 300GB
CHUNK_SIZE = 1024 * 1024 * 4  # 4MB chunks for better performance
SKIP_EXTENSIONS = {'.tmp', '.temp', '.log', '.cache'}
BATCH_SIZE = 1000  # Process files in batches of 1000
NUM_WORKERS = max(1, multiprocessing.cpu_count() - 1)  # Leave one core free

class CyberButton(tk.Canvas):
    """Custom circular button with cyberpunk style and animations"""
    def __init__(self, parent, text, command, radius=50, color=CYBER_PINK, hover_color=CYBER_ORANGE, **kwargs):
        super().__init__(parent, width=radius*2+10, height=radius*2+10,  # Added padding
                        bg=CYBER_BLACK, highlightthickness=0, **kwargs)
        self.radius = radius
        self.color = color
        self.hover_color = hover_color
        self.command = command
        self.animation_id = None
        self.glow_radius = 0
        self.glow_direction = 1
        
        # Create outer glow
        self.glow = self.create_oval(2, 2, radius*2+8, radius*2+8,
                                   fill="", outline=color, width=3)
        
        # Create circular button
        self.circle = self.create_oval(5, 5, radius*2+5, radius*2+5,
                                     fill=color, outline=CYBER_WHITE, width=2)
        
        # Add text
        self.text = self.create_text(radius+5, radius+5, text=text,
                                   fill=CYBER_WHITE, font=('Cyberpunk', 12, 'bold'))
        
        # Bind events
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)
        self.bind('<Button-1>', self.on_click)
        
        # Start glow animation
        self.animate_glow()
        
    def animate_glow(self):
        """Animate the button's glow effect"""
        if self.glow_radius >= 5:
            self.glow_direction = -1
        elif self.glow_radius <= 0:
            self.glow_direction = 1
            
        self.glow_radius += 0.2 * self.glow_direction
        self.itemconfig(self.glow, outline=self.color)
        self.animation_id = self.after(50, self.animate_glow)
        
    def on_enter(self, event):
        """Change color on hover and intensify glow"""
        self.itemconfig(self.circle, fill=self.hover_color)
        self.itemconfig(self.glow, outline=self.hover_color)
        
    def on_leave(self, event):
        """Restore original color"""
        self.itemconfig(self.circle, fill=self.color)
        self.itemconfig(self.glow, outline=self.color)
        
    def on_click(self, event):
        """Execute command on click with click animation"""
        if self.command:
            # Flash effect on click
            original_color = self.itemcget(self.circle, "fill")
            self.itemconfig(self.circle, fill=CYBER_WHITE)
            self.after(100, lambda: self.itemconfig(self.circle, fill=original_color))
            self.command()

class CyberProgressBar(tk.Canvas):
    """Custom progress bar with cyberpunk style and animations"""
    def __init__(self, parent, width=300, height=20, **kwargs):
        super().__init__(parent, width=width, height=height,
                        bg=CYBER_BLACK, highlightthickness=0, **kwargs)
        self.width = width
        self.height = height
        self.progress = 0
        self.scan_pos = 0
        self.scan_direction = 1
        
        # Create background
        self.bg = self.create_rectangle(2, 2, width-2, height-2,
                                      fill=CYBER_BLACK, outline=CYBER_PINK, width=2)
        
        # Create progress bar
        self.bar = self.create_rectangle(2, 2, 2, height-2,
                                       fill=CYBER_GREEN, outline="")
        
        # Create scanning effect
        self.scan_line = self.create_line(2, 2, 2, height-2,
                                        fill=CYBER_ORANGE, width=2)
        
        # Start scanning animation
        self.animate_scan()
        
    def animate_scan(self):
        """Animate the scanning effect"""
        if self.scan_pos >= self.width - 4:
            self.scan_direction = -1
        elif self.scan_pos <= 2:
            self.scan_direction = 1
            
        self.scan_pos += 5 * self.scan_direction
        self.coords(self.scan_line, self.scan_pos, 2, self.scan_pos, self.height-2)
        self.after(50, self.animate_scan)
        
    def set_progress(self, value):
        """Update progress bar value (0-100)"""
        self.progress = max(0, min(100, value))
        width = (self.width - 4) * (self.progress / 100)
        self.coords(self.bar, 2, 2, width + 2, self.height - 2)

class DuplicateFinderGUI:
    """
    Main GUI class for the Deduplicationator 3000 application.
    Handles the user interface and coordinates the duplicate finding process.
    """
    
    def __init__(self, root):
        """
        Initialize the GUI application.
        
        Args:
            root (tk.Tk): The root Tkinter window
        """
        self.root = root
        self.root.title("Deduplicationator 3000")
        self.root.geometry("1200x900")  # Increased from 1000x800
        self.root.minsize(1000, 800)    # Set minimum window size
        self.root.configure(bg=CYBER_BLACK)
        
        # Set custom font
        self.root.option_add("*Font", "Cyberpunk")
        
        # Make window movable
        self.root.bind('<Button-1>', self.start_move)
        self.root.bind('<B1-Motion>', self.on_move)
        
        # Initialize variables
        self.target_dir = tk.StringVar()
        self.min_size = tk.StringVar(value="0")
        self.max_size = tk.StringVar(value="100")
        self.size_unit = tk.StringVar(value="GB")
        self.skip_extensions = tk.StringVar(value=".tmp,.temp,.log,.cache")
        self.is_running = False
        self.auto_delete = tk.BooleanVar(value=False)
        self.export_csv = tk.BooleanVar(value=False)  # New variable for CSV export
        
        # Initialize statistics
        self.stats = {
            'processed': 0,    # Total files processed
            'skipped': 0,      # Files skipped due to size or extension
            'hashed': 0,       # Files successfully hashed
            'duplicates': 0,   # Number of duplicate groups found
            'deleted': 0,      # Number of duplicate files deleted
            'size_saved': 0,   # Total space saved by deleting duplicates
            'total_size': 0    # Total size of all processed files
        }
        
        # Store duplicate information for CSV export
        self.duplicate_groups = []
        
        self.create_widgets()
        
    def start_move(self, event):
        """Start moving the window"""
        self.x = event.x
        self.y = event.y

    def on_move(self, event):
        """Move the window"""
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def create_widgets(self):
        """Create and arrange all GUI widgets."""
        # Main container with rounded corners
        main_frame = tk.Frame(self.root, bg=CYBER_BLACK, padx=30, pady=30)
        main_frame.pack(fill="both", expand=True)
        
        # Title bar
        title_bar = tk.Frame(main_frame, bg=CYBER_PURPLE, height=40)
        title_bar.pack(fill="x", pady=(0, 20))  # Reduced bottom padding
        
        # Title with animation
        title_label = tk.Label(title_bar, 
                             text="DEDUPLICATIONATOR 3000",
                             font=('Cyberpunk', 20, 'bold'),
                             fg=CYBER_WHITE,
                             bg=CYBER_PURPLE)
        title_label.pack(side="left", padx=15)
        
        # Animate title
        def animate_title():
            colors = [CYBER_WHITE, CYBER_PINK, CYBER_GREEN, CYBER_ORANGE]
            current_color = title_label.cget("fg")
            next_color = colors[(colors.index(current_color) + 1) % len(colors)]
            title_label.configure(fg=next_color)
            self.root.after(1000, animate_title)
        animate_title()
        
        # Close button
        close_btn = tk.Label(title_bar, text="×", font=('Cyberpunk', 20),
                           fg=CYBER_WHITE, bg=CYBER_PURPLE, cursor="hand2")
        close_btn.pack(side="right", padx=10)
        close_btn.bind('<Button-1>', lambda e: self.root.quit())
        
        # Directory Selection
        dir_frame = tk.LabelFrame(main_frame, text="Directory Selection", 
                                font=('Cyberpunk', 12),
                                fg=CYBER_GREEN,
                                bg=CYBER_BLACK,
                                padx=10, pady=10)
        dir_frame.pack(fill="x", pady=5)
        
        entry = tk.Entry(dir_frame, textvariable=self.target_dir, 
                       width=70, font=('Cyberpunk', 10),
                       bg=CYBER_BLACK, fg=CYBER_WHITE,
                       insertbackground=CYBER_PINK)
        entry.pack(side="left", padx=5)
        
        browse_btn = CyberButton(dir_frame, "BROWSE", self.browse_directory,
                               color=CYBER_PURPLE, hover_color=CYBER_ORANGE)
        browse_btn.pack(side="left", padx=5)
        
        # Size Settings
        size_frame = tk.LabelFrame(main_frame, text="File Size Settings",
                                 font=('Cyberpunk', 12),
                                 fg=CYBER_GREEN,
                                 bg=CYBER_BLACK,
                                 padx=10, pady=10)
        size_frame.pack(fill="x", pady=5)
        
        # Create size inputs with cyber style
        for i, (label, var) in enumerate([("Min Size:", self.min_size),
                                        ("Max Size:", self.max_size)]):
            tk.Label(size_frame, text=label, font=('Cyberpunk', 10),
                    fg=CYBER_WHITE, bg=CYBER_BLACK).grid(row=0, column=i*2, padx=5)
            tk.Entry(size_frame, textvariable=var, width=10,
                    font=('Cyberpunk', 10),
                    bg=CYBER_BLACK, fg=CYBER_WHITE,
                    insertbackground=CYBER_PINK).grid(row=0, column=i*2+1, padx=5)
        
        # Size unit combobox
        tk.Label(size_frame, text="Size Unit:", font=('Cyberpunk', 10),
                fg=CYBER_WHITE, bg=CYBER_BLACK).grid(row=0, column=4, padx=5)
        unit_combo = ttk.Combobox(size_frame, textvariable=self.size_unit,
                                values=["KB", "MB", "GB", "TB"],
                                width=5, font=('Cyberpunk', 10))
        unit_combo.grid(row=0, column=5, padx=5)
        
        # Skip Extensions
        ext_frame = tk.LabelFrame(main_frame, text="Skip Extensions",
                                font=('Cyberpunk', 12),
                                fg=CYBER_GREEN,
                                bg=CYBER_BLACK,
                                padx=10, pady=10)
        ext_frame.pack(fill="x", pady=5)
        
        tk.Entry(ext_frame, textvariable=self.skip_extensions,
                width=70, font=('Cyberpunk', 10),
                bg=CYBER_BLACK, fg=CYBER_WHITE,
                insertbackground=CYBER_PINK).pack(fill="x", padx=5)
        
        # Options
        options_frame = tk.LabelFrame(main_frame, text="Options",
                                    font=('Cyberpunk', 12),
                                    fg=CYBER_GREEN,
                                    bg=CYBER_BLACK,
                                    padx=10, pady=10)
        options_frame.pack(fill="x", pady=5)
        
        tk.Checkbutton(options_frame,
                      text="Auto-delete duplicates (without confirmation)",
                      font=('Cyberpunk', 10),
                      fg=CYBER_WHITE, bg=CYBER_BLACK,
                      selectcolor=CYBER_BLACK,
                      activebackground=CYBER_BLACK,
                      activeforeground=CYBER_WHITE,
                       variable=self.auto_delete).pack(anchor="w", padx=5)
        
        # CSV export checkbox
        tk.Checkbutton(options_frame,
                      text="Export duplicate files to CSV",
                      font=('Cyberpunk', 10),
                      fg=CYBER_WHITE, bg=CYBER_BLACK,
                      selectcolor=CYBER_BLACK,
                      activebackground=CYBER_BLACK,
                      activeforeground=CYBER_WHITE,
                      variable=self.export_csv).pack(anchor="w", padx=5)
        
        # Control Buttons - Moved up before progress frame
        control_frame = tk.Frame(main_frame, bg=CYBER_BLACK)
        control_frame.pack(fill="x", pady=15)  # Reduced padding
        
        # Center the buttons
        button_container = tk.Frame(control_frame, bg=CYBER_BLACK)
        button_container.pack(expand=True)
        
        self.start_button = CyberButton(button_container, "START SCAN",
                                      self.start_scan,
                                      color=CYBER_GREEN,
                                      hover_color=CYBER_ORANGE,
                                      radius=50)
        self.start_button.pack(side="left", padx=30)
        
        self.stop_button = CyberButton(button_container, "STOP",
                                     self.stop_scan,
                                     color=CYBER_PINK,
                                     hover_color=CYBER_ORANGE,
                                     radius=50)
        self.stop_button.pack(side="left", padx=30)
        
        # Progress
        progress_frame = tk.LabelFrame(main_frame, text="Progress",
                                     font=('Cyberpunk', 12),
                                     fg=CYBER_GREEN,
                                     bg=CYBER_BLACK,
                                     padx=15, pady=15)
        progress_frame.pack(fill="both", expand=True, pady=5)
        
        # Progress bar
        self.progress_bar = CyberProgressBar(progress_frame, width=1100)
        self.progress_bar.pack(pady=10)
        
        # Progress text with scrollbar
        scrollbar = ttk.Scrollbar(progress_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.progress_text = tk.Text(progress_frame, height=12, width=120,
                                   font=('Cyberpunk', 10),
                                   bg=CYBER_BLACK, fg=CYBER_WHITE,
                                   insertbackground=CYBER_PINK,
                                   yscrollcommand=scrollbar.set)
        self.progress_text.pack(fill="both", expand=True, pady=5)
        scrollbar.config(command=self.progress_text.yview)
        
        # Status Bar
        self.status_var = tk.StringVar()
        self.status_bar = tk.Label(self.root,
                                 textvariable=self.status_var,
                                 font=('Cyberpunk', 10),
                                 fg=CYBER_GREEN,
                                 bg=CYBER_BLACK,
                                 relief="flat")
        self.status_bar.pack(fill="x", side="bottom", padx=10, pady=5)
        
    def browse_directory(self):
        """Open directory selection dialog and update target directory."""
        directory = filedialog.askdirectory()
        if directory:
            self.target_dir.set(directory)
            self.update_progress(f"Selected directory: {directory}")
            
    def format_size(self, size_bytes):
        """
        Format size in bytes to human readable format.
        
        Args:
            size_bytes (int): Size in bytes
            
        Returns:
            str: Formatted size string (e.g., "1.5GB")
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f}TB"
    
    def update_progress(self, message):
        """
        Update progress text with timestamp and scroll to bottom.
        
        Args:
            message (str): Message to display
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.progress_text.insert("end", f"[{timestamp}] {message}\n")
        self.progress_text.see("end")
        self.root.update_idletasks()
        
        # Update progress bar based on processed files
        if hasattr(self, 'total_files'):
            progress = (self.stats['processed'] / self.total_files) * 100
            self.progress_bar.set_progress(progress)

    def update_status(self):
        """Update status bar with current statistics."""
        if self.is_running:
            stats = self.stats
            elapsed = time.time() - self.start_time
            speed = stats['processed'] / elapsed if elapsed > 0 else 0
            total_size = self.format_size(stats['total_size'])
            size_saved = self.format_size(stats['size_saved'])
            
            status = (f"Files: {stats['processed']} | Size: {total_size} | "
                     f"Skipped: {stats['skipped']} | Hashed: {stats['hashed']} | "
                     f"Duplicates: {stats['duplicates']} | Deleted: {stats['deleted']} | "
                     f"Saved: {size_saved} | Speed: {speed:.1f} files/s")
            
            self.status_var.set(status)
            self.root.after(1000, self.update_status)
    
    def get_size_in_bytes(self, size_str, unit):
        """
        Convert size string to bytes.
        
        Args:
            size_str (str): Size value as string
            unit (str): Unit of size (KB, MB, GB, TB)
            
        Returns:
            int: Size in bytes
        """
        size = float(size_str)
        units = {"KB": 1024, "MB": 1024**2, "GB": 1024**3, "TB": 1024**4}
        return int(size * units.get(unit, 1))
    
    def start_scan(self):
        """Start the duplicate file scanning process."""
        if not self.target_dir.get():
            messagebox.showerror("Error", "Please select a directory to scan")
            return
            
        try:
            min_size = self.get_size_in_bytes(self.min_size.get(), self.size_unit.get())
            max_size = self.get_size_in_bytes(self.max_size.get(), self.size_unit.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid size values")
            return
            
        self.is_running = True
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        
        # Reset statistics
        self.stats = {
            'processed': 0,
            'skipped': 0,
            'hashed': 0,
            'duplicates': 0,
            'deleted': 0,
            'size_saved': 0,
            'total_size': 0
        }
        self.start_time = time.time()
        
        # Start the scan in a separate thread
        self.scan_thread = threading.Thread(
            target=self.run_scan,
            args=(self.target_dir.get(), min_size, max_size)
        )
        self.scan_thread.start()
        
        # Start status updates
        self.update_status()
        
    def stop_scan(self):
        """Stop the scanning process."""
        self.is_running = False
        self.stop_button.config(state="disabled")
        self.update_progress("\nScan stopped by user")
        
    def run_scan(self, directory, min_size, max_size):
        """
        Run the main scanning process.
        
        Args:
            directory (str): Directory to scan
            min_size (int): Minimum file size in bytes
            max_size (int): Maximum file size in bytes
        """
        try:
            self.update_progress(f"Starting scan in: {directory}")
            self.update_progress(f"File size range: {self.format_size(min_size)} - {self.format_size(max_size)}")
            self.update_progress(f"Using {NUM_WORKERS} CPU cores for processing")
            
            # Get extensions to skip
            skip_extensions = set(ext.strip().lower() for ext in self.skip_extensions.get().split(','))
            self.update_progress(f"Skipping extensions: {', '.join(skip_extensions)}")
            
            # Initialize size dictionary
            size_dict = defaultdict(list)
            
            # Process files in batches
            batch_size = BATCH_SIZE
            current_batch = []
            total_files = 0
            
            self.update_progress("\nScanning directory structure...")
            for root, _, files in os.walk(directory):
                if not self.is_running:
                    return
                    
                total_files += len(files)
                self.update_progress(f"Found {total_files} files so far...")
                
                for filename in files:
                    if not self.is_running:
                        return
                        
                    filepath = os.path.join(root, filename)
                    try:
                        # Skip files with specified extensions
                        if any(filename.lower().endswith(ext) for ext in skip_extensions):
                            self.stats['skipped'] += 1
                            continue
                            
                        # Get file size
                        size = os.path.getsize(filepath)
                        self.stats['total_size'] += size
                        
                        # Skip files outside size range
                        if size < min_size or size > max_size:
                            self.stats['skipped'] += 1
                            continue
                            
                        # Add to current batch
                        current_batch.append((filepath, size))
                        self.stats['processed'] += 1
                        
                        # Process batch when it reaches batch_size
                        if len(current_batch) >= batch_size:
                            self.update_progress(f"Processing batch of {len(current_batch)} files...")
                            self.process_batch(current_batch, size_dict)
                            current_batch = []
                            
                    except (PermissionError, OSError) as e:
                        self.update_progress(f"Error accessing {filepath}: {str(e)}")
                        continue
                        
            # Process remaining files
            if current_batch:
                self.update_progress(f"Processing final batch of {len(current_batch)} files...")
                self.process_batch(current_batch, size_dict)
                
            # Find and handle duplicates
            self.update_progress("\nAnalyzing potential duplicates...")
            self.handle_duplicates(size_dict)
            
            if not self.is_running:
                return
                
            # Display final statistics
            self.update_progress("\n=== Scan Complete ===")
            self.update_progress(f"Total files found: {total_files}")
            self.update_progress(f"Files processed: {self.stats['processed']}")
            self.update_progress(f"Total size processed: {self.format_size(self.stats['total_size'])}")
            self.update_progress(f"Files skipped: {self.stats['skipped']}")
            self.update_progress(f"Files hashed: {self.stats['hashed']}")
            self.update_progress(f"Duplicate groups found: {self.stats['duplicates']}")
            self.update_progress(f"Duplicate files deleted: {self.stats['deleted']}")
            self.update_progress(f"Total space saved: {self.format_size(self.stats['size_saved'])}")
            
        except Exception as e:
            self.update_progress(f"Error: {str(e)}")
        finally:
            self.is_running = False
            self.root.after(0, lambda: self.start_button.config(state="normal"))
            self.root.after(0, lambda: self.stop_button.config(state="disabled"))
            
    def process_batch(self, batch, size_dict):
        """
        Process a batch of files and update size dictionary.
        
        Args:
            batch (list): List of (filepath, size) tuples
            size_dict (defaultdict): Dictionary to store files by size
        """
        for filepath, size in batch:
            if not self.is_running:
                return
                
            try:
                # Calculate file hash
                file_hash = calculate_file_hash(filepath)
                if file_hash:
                    self.stats['hashed'] += 1
                    size_dict[size].append((filepath, file_hash))
            except Exception as e:
                self.update_progress(f"Error processing {filepath}: {str(e)}")
                
    def handle_duplicates(self, size_dict):
        """
        Find and handle duplicate files.
        
        Args:
            size_dict (defaultdict): Dictionary of files grouped by size
        """
        self.duplicate_groups = []  # Reset duplicate groups for new scan
        
        for size, files in size_dict.items():
            if not self.is_running:
                return

            if len(files) < 2:
                continue
                
            # Group files by hash
            hash_groups = defaultdict(list)
            for filepath, file_hash in files:
                hash_groups[file_hash].append(filepath)
                
            # Handle duplicate groups
            for file_hash, filepaths in hash_groups.items():
                if len(filepaths) < 2:
                    continue
                    
                self.stats['duplicates'] += 1
                self.update_progress(f"\nFound duplicate group ({self.format_size(size)}):")
                
                # Keep the most recently modified file
                filepaths.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                keep_file = filepaths[0]
                
                # Store duplicate information for CSV export
                group_info = {
                    'size': size,
                    'keep_file': keep_file,
                    'duplicate_files': filepaths[1:],
                    'modified_time': datetime.fromtimestamp(os.path.getmtime(keep_file))
                }
                self.duplicate_groups.append(group_info)
                
                # Show files in group
                for i, filepath in enumerate(filepaths, 1):
                    mod_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                    self.update_progress(f"{i}. {filepath} (Modified: {mod_time})")
                
                # Delete duplicates
                if self.auto_delete.get():
                    self.delete_duplicates(filepaths[1:], keep_file, size)
                else:
                    # Ask for confirmation
                    msg = f"Found {len(filepaths)} duplicate files. Keep the most recent one and delete the rest?"
                    if messagebox.askyesno("Confirm Deletion", msg):
                        self.delete_duplicates(filepaths[1:], keep_file, size)
                    else:
                        self.update_progress("Skipping this group...")
        
        # Export to CSV if enabled
        if self.export_csv.get() and self.duplicate_groups:
            self.export_duplicates_to_csv()
            
    def delete_duplicates(self, files_to_delete, keep_file, size):
        """
        Delete duplicate files.
        
        Args:
            files_to_delete (list): List of file paths to delete
            keep_file (str): Path of the file to keep
            size (int): Size of each file in bytes
        """
        for filepath in files_to_delete:
            if not self.is_running:
                return
                
            try:
                os.remove(filepath)
                self.stats['deleted'] += 1
                self.stats['size_saved'] += size
                self.update_progress(f"Deleted: {filepath}")
            except Exception as e:
                self.update_progress(f"Error deleting {filepath}: {str(e)}")
                
        self.update_progress(f"Kept: {keep_file}")

    def export_duplicates_to_csv(self):
        """Export duplicate file information to a CSV file."""
        try:
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"duplicate_files_{timestamp}.csv"
            
            # Get save location from user
            filepath = filedialog.asksaveasfilename(
                defaultextension=".csv",
                initialfile=filename,
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            
            if not filepath:  # User cancelled
                return
                
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                # Write header
                writer.writerow(['Group', 'File Path', 'Size', 'Modified Time', 'Status'])
                
                # Write data
                for i, group in enumerate(self.duplicate_groups, 1):
                    # Write the file to keep
                    writer.writerow([
                        i,
                        group['keep_file'],
                        self.format_size(group['size']),
                        group['modified_time'],
                        'KEEP'
                    ])
                    # Write the duplicates
                    for dup_file in group['duplicate_files']:
                        writer.writerow([
                            i,
                            dup_file,
                            self.format_size(group['size']),
                            datetime.fromtimestamp(os.path.getmtime(dup_file)),
                            'DUPLICATE'
                        ])
            
            self.update_progress(f"\nExported duplicate information to: {filepath}")
            messagebox.showinfo("Export Complete", f"Duplicate information has been exported to:\n{filepath}")
            
        except Exception as e:
            self.update_progress(f"Error exporting to CSV: {str(e)}")
            messagebox.showerror("Export Error", f"Failed to export duplicate information:\n{str(e)}")

def main():
    """Initialize and start the application."""
    root = tk.Tk()
    
    # Set custom font
    try:
        # Try to load custom font
        root.tk.call('font', 'create', 'Cyberpunk', '-family', 'Orbitron')
    except:
        # Fallback to system font
        root.tk.call('font', 'create', 'Cyberpunk', '-family', 'Arial')
    
    app = DuplicateFinderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 