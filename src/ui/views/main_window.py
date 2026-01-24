"""Main Window View."""

import tkinter as tk
from tkinter import ttk
import sv_ttk
import darkdetect

from ui.viewmodels.main_viewmodel import MainViewModel
from domain.models import ProcessStatus


import sys
import os

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def start_app(viewModel: MainViewModel):
    root = tk.Tk()
    root.title("BDO Monitor")
    root.geometry("600x340")
    
    # Set Icon
    try:
        icon_path = resource_path("resources/icon.ico")
        root.iconbitmap(icon_path)
    except Exception:
        pass # Fail silently if icon not found
    
    # Apply Theme
    theme = darkdetect.theme()
    sv_ttk.set_theme(theme.lower() if theme else "dark")
    
    app = MainWindow(root, viewModel)
    root.mainloop()


class MainWindow(ttk.Frame):
    def __init__(self, root: tk.Tk, viewModel: MainViewModel):
        super().__init__(root)
        self.root = root
        self.vm = viewModel
        
        self.setup_ui()
        self.pack(fill=tk.BOTH, expand=True)
        
        # Start refresh loop
        self.refresh_loop()

    def setup_ui(self):
        # Configure Style for denser table
        style = ttk.Style()
        style.configure("Treeview", rowheight=20)  # Compact row height

        # Header
        self.header_frame = ttk.Frame(self, padding=15)
        self.header_frame.pack(side=tk.TOP, fill=tk.X)
        
        # Top Row: Ping and Optimize Button
        self.top_row = ttk.Frame(self.header_frame)
        self.top_row.pack(fill=tk.X)
        
        self.ping_label = ttk.Label(
            self.top_row, 
            text="Ping: -- ms", 
            font=("Segoe UI", 24, "bold"),
            foreground="#ffffff"
        )
        self.ping_label.pack(side=tk.LEFT)
        
        # Optimize Control Container (Button + Label)
        self.optimize_frame = ttk.Frame(self.top_row)
        self.optimize_frame.pack(side=tk.RIGHT)
        
        self.optimize_btn = ttk.Button(
            self.optimize_frame, 
            text="Optimize",
            command=self.on_optimize,
            width=15
        )
        self.optimize_btn.pack(side=tk.TOP, anchor="e")
        
        self.admin_label = ttk.Label(
            self.optimize_frame,
            text="Admin Required",
            font=("Segoe UI", 8),
            foreground="#ff4c4c"
        )
        # We pack it but might hide it later, or just update text/color
        self.admin_label.pack(side=tk.TOP, anchor="e")

        # Bottom Row: Process Details (Secondary)
        self.details_frame = ttk.Frame(self.header_frame)
        self.details_frame.pack(anchor="w", pady=(5, 0))
        
        # Process Info (Grey)
        self.proc_label = ttk.Label(
            self.details_frame,
            text="Initializing...",
            font=("Segoe UI", 9),
            foreground="#888888"
        )
        self.proc_label.pack(side=tk.LEFT)
        
        # Divider
        ttk.Label(self.details_frame, text=" | ", foreground="#666666").pack(side=tk.LEFT)

        # Priority Labels
        ttk.Label(self.details_frame, text="Priority: ", foreground="#888888").pack(side=tk.LEFT)
        self.priority_val_label = ttk.Label(
            self.details_frame, 
            text="...", 
            font=("Segoe UI", 9, "bold"), 
            foreground="#ffffff"
        )
        self.priority_val_label.pack(side=tk.LEFT)

        # Divider
        ttk.Label(self.details_frame, text=" | ", foreground="#666666").pack(side=tk.LEFT)

        # Affinity Labels
        ttk.Label(self.details_frame, text="Affinity: ", foreground="#888888").pack(side=tk.LEFT)
        self.affinity_val_label = ttk.Label(
            self.details_frame, 
            text="...", 
            font=("Segoe UI", 9, "bold"), 
            foreground="#ffffff"
        )
        self.affinity_val_label.pack(side=tk.LEFT)

        # Footer (Packed BEFORE Treeview uses remaining space)
        self.footer_label = ttk.Label(
            self, 
            text="by: JasonREDUX", 
            foreground="#555555",
            font=("Segoe UI", 9)
        )
        self.footer_label.pack(side=tk.BOTTOM, anchor="se", padx=5, pady=2)

        # Content (Network Table)
        self.tree_frame = ttk.Frame(self, padding=10)
        self.tree_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        columns = ("ip", "port", "service", "latency")
        self.tree = ttk.Treeview(self.tree_frame, columns=columns, show="headings")
        
        self.tree.heading("ip", text="Remote IP")
        self.tree.heading("port", text="Port")
        self.tree.heading("service", text="Service")
        self.tree.heading("latency", text="Latency")
        
        self.tree.column("ip", width=150)
        self.tree.column("port", width=80)
        self.tree.column("service", width=150)
        self.tree.column("latency", width=80)
        
        self.tree.pack(fill=tk.BOTH, expand=True)

    def on_optimize(self):
        if self.vm.optimize_process():
            self.optimized_success = True
            self.update_view()

    def refresh_loop(self):
        self.vm.refresh()
        self.update_view()
        self.root.after(1000, self.refresh_loop)

    def update_view(self):
        # Update Ping (Main Protagonist)
        if self.vm.game_latency is not None:
            self.ping_label.config(text=f"Ping: {self.vm.game_latency:.0f} ms")
        else:
            self.ping_label.config(text="Ping: -- ms")

        # Update Secondary Details
        status_str = "Running" if self.vm.status == ProcessStatus.RUNNING else "Not Running"
        pid_str = f"PID: {self.vm.pid}" if self.vm.pid else "PID: -"
        affinity_count = len(self.vm.affinity) if self.vm.affinity else 0
        
        # Process Info
        self.proc_label.config(text=f"{self.vm.settings.process_name} ({pid_str}) | {status_str}")
        
        # Priority Value
        self.priority_val_label.config(text=self.vm.priority)
        
        # Affinity Value
        self.affinity_val_label.config(text=f"{affinity_count} cores")
        
        # Update Optimize Button & Admin Label
        if not self.vm.is_admin:
            self.optimize_btn.state(["disabled"])
            self.admin_label.config(text="Admin Required", foreground="#ff4c4c") # Red warning
            self.admin_label.pack(side=tk.TOP, anchor="e") # Ensure visible
        else:
            self.admin_label.pack_forget() # Hide if admin
            
            # Disable if not running OR if successfully optimized
            if self.vm.status != ProcessStatus.RUNNING or getattr(self, "optimized_success", False):
                self.optimize_btn.state(["disabled"])
            else:
                self.optimize_btn.state(["!disabled"])

            # Colorize Priority/Affinity if optimized
            is_optimized = getattr(self, "optimized_success", False)
            success_color = "#00ff00" # Bright Green
            default_color = "#ffffff"
            
            # Priority Color
            # If manually set to High outside app, also show green? 
            # User request: "appear in green the result".
            # We'll use the flag for consistency with the button behavior.
            p_color = success_color if is_optimized else default_color
            self.priority_val_label.config(foreground=p_color)

            # Affinity Color
            a_color = success_color if is_optimized else default_color
            self.affinity_val_label.config(foreground=a_color)

        # Update Table
        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Configure tag for highlighting
        self.tree.tag_configure("gamerow", foreground="#4cc2ff") # Light blue accent
            
        # Add new
        for conn in self.vm.connections:
            latency = f"{conn.latency_ms:.0f} ms" if conn.latency_ms else "N/A"
            
            # Determine if this row should be highlighted
            tags = ()
            if "Game Server" in conn.service_name:
                tags = ("gamerow",)

            self.tree.insert("", tk.END, values=(
                conn.remote_ip,
                str(conn.remote_port),
                conn.service_name,
                latency
            ), tags=tags)
