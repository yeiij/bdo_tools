"""Main Window View."""

import tkinter as tk
from tkinter import ttk
import sv_ttk
import darkdetect

from ui.viewmodels.main_viewmodel import MainViewModel
from domain.models import ProcessStatus


import sys
import os
from typing import Literal

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


class UIConstants:
    BG_COLOR = "#2f2f2f"
    FG_WHITE = "#ffffff"
    FG_GREY = "#888888"
    FG_ERROR = "#ff4c4c"
    FG_SUCCESS = "#00ff00"
    FG_ACCENT = "#4cc2ff"
    FONT_HEADER = ("Segoe UI", 24, "bold")
    FONT_NORMAL = ("Segoe UI", 9)
    FONT_BOLD = ("Segoe UI", 9, "bold")
    FONT_SMALL = ("Segoe UI", 8)


from ui.tray import SystemTrayIcon

class MainWindow(ttk.Frame):
    def __init__(self, root: tk.Tk, viewModel: MainViewModel):
        super().__init__(root)
        self.root = root
        self.vm = viewModel
        
        self.setup_ui()
        self.pack(fill=tk.BOTH, expand=True)
        
        # Tray Icon Setup
        self.tray_icon = None
        self._setup_tray()
        
        # Bind Minimize Event
        # Note: Unmap can fire for multiple reasons (switching desktops), 
        # checking state() == 'iconic' is key.
        self.root.bind("<Unmap>", self.on_window_state_change)
        
        # Handle correct shutdown
        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)
        
        # Start refresh loop
        self.refresh_loop()

    def _setup_tray(self):
        try:
            icon_path = resource_path("resources/icon.ico")
            self.tray_icon = SystemTrayIcon(
                icon_path, 
                on_show=self.show_window, 
                on_quit=self.quit_app
            )
        except Exception:
            pass

    def on_window_state_change(self, event):
        # Verify it's the root window and it is minimized
        if event.widget == self.root and self.root.state() == 'iconic':
            self.hide_to_tray()

    def hide_to_tray(self):
        self.root.withdraw() # Hide window
        if self.tray_icon:
            self.tray_icon.run()

    def show_window(self):
        # Must schedule on main thread since this is called from tray thread
        self.root.after(0, self._restore_window)
        
    def _restore_window(self):
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.deiconify() # Show window
        self.root.state('normal') # Restore from minimized state
        self.root.lift()
        self.root.focus_force()

    def quit_app(self):
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.destroy()
        sys.exit(0)

    def setup_ui(self):
        self._setup_styles()
        self._setup_header()
        self._setup_network_table()
        self._setup_footer()

    def _setup_styles(self):
        style = ttk.Style()
        style.configure("Treeview", rowheight=20)
        
        # Combobox Styles
        style.configure("TCombobox", foreground=UIConstants.FG_WHITE, 
                       selectbackground=UIConstants.BG_COLOR, fieldbackground=UIConstants.BG_COLOR)
        style.map("TCombobox", 
            selectbackground=[("readonly", UIConstants.BG_COLOR)],
            selectforeground=[("readonly", UIConstants.FG_WHITE)]
        )
        
        style.configure("Success.TCombobox", foreground=UIConstants.FG_SUCCESS, 
                       selectforeground=UIConstants.FG_SUCCESS, 
                       selectbackground=UIConstants.BG_COLOR, 
                       fieldbackground=UIConstants.BG_COLOR)
                       
        style.map("Success.TCombobox", 
            foreground=[("readonly", UIConstants.FG_SUCCESS)], 
            selectforeground=[("readonly", UIConstants.FG_SUCCESS)],
            selectbackground=[("readonly", UIConstants.BG_COLOR)]
        )

    def _setup_header(self):
        # Header Container
        self.header_frame = ttk.Frame(self, padding=15)
        self.header_frame.pack(side=tk.TOP, fill=tk.X)
        
        # Top Row (Ping & Admin)
        self._setup_top_row()
        
        # Bottom Row (Process Details)
        self._setup_details_row()

    def _setup_top_row(self):
        top_row = ttk.Frame(self.header_frame)
        top_row.pack(fill=tk.X)
        
        self.ping_label = ttk.Label(
            top_row, 
            text="Ping: -- ms", 
            font=UIConstants.FONT_HEADER,
            foreground=UIConstants.FG_WHITE
        )
        self.ping_label.pack(side=tk.LEFT)
        
        self.admin_label = ttk.Label(
            top_row,
            text="Admin Required (Limited Controls)",
            font=UIConstants.FONT_SMALL,
            foreground=UIConstants.FG_ERROR
        )
        if not self.vm.is_admin:
            self.admin_label.pack(side=tk.RIGHT, anchor="e")

    def _setup_details_row(self):
        details_frame = ttk.Frame(self.header_frame)
        details_frame.pack(anchor="w", pady=(5, 0))
        
        # Process Info
        self.proc_label = ttk.Label(
            details_frame,
            text="Initializing...",
            font=UIConstants.FONT_NORMAL,
            foreground=UIConstants.FG_GREY
        )
        self.proc_label.pack(side=tk.LEFT)
        
        # Divider
        self._add_divider(details_frame)

        # Priority
        ttk.Label(details_frame, text="Priority: ", foreground=UIConstants.FG_GREY).pack(side=tk.LEFT)
        self.priority_combo = ttk.Combobox(
            details_frame, 
            values=["Idle", "Below Normal", "Normal", "Above Normal", "High", "Realtime"],
            state="readonly",
            width=11
        )
        self.priority_combo.pack(side=tk.LEFT)
        self.priority_combo.bind("<<ComboboxSelected>>", self.on_priority_change)

        # Divider
        self._add_divider(details_frame)

        # Affinity
        ttk.Label(details_frame, text="Affinity: ", foreground=UIConstants.FG_GREY).pack(side=tk.LEFT)
        self.affinity_val_label = ttk.Label(
            details_frame, 
            text="...", 
            font=UIConstants.FONT_BOLD, 
            foreground=UIConstants.FG_WHITE
        )
        self.affinity_val_label.pack(side=tk.LEFT)
        
        # Affinity Edit Button
        ttk.Button(
            details_frame,
            text="⚙️",
            width=3,
            command=self.open_affinity_dialog
        ).pack(side=tk.LEFT, padx=(5, 0))

    def _add_divider(self, parent):
        ttk.Label(parent, text=" | ", foreground="#666666").pack(side=tk.LEFT)

    def _setup_network_table(self):
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
        # Configure tag for highlighting
        self.tree.tag_configure("gamerow", foreground=UIConstants.FG_ACCENT)

    def _setup_footer(self):
        ttk.Label(
            self, 
            text="by: JasonREDUX", 
            foreground="#555555",
            font=UIConstants.FONT_NORMAL
        ).pack(side=tk.BOTTOM, anchor="se", padx=5, pady=2)

    def open_affinity_dialog(self):
        if not self.vm.pid:
            return
            
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Cores")
        
        try:
            icon_path = resource_path("resources/icon.ico")
            dialog.iconbitmap(icon_path)
        except Exception:
            pass
        
        self._center_dialog(dialog, 500, 400)
        
        dialog.transient(self.root)
        dialog.grab_set()
        
        self._build_affinity_ui(dialog)

    def _center_dialog(self, dialog, width, height):
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_w = self.root.winfo_width()
        root_h = self.root.winfo_height()
        
        center_x = root_x + (root_w // 2) - (width // 2)
        center_y = root_y + (root_h // 2) - (height // 2)
        
        dialog.geometry(f"{width}x{height}+{center_x}+{center_y}")
        dialog.resizable(False, False)

    def _build_affinity_ui(self, dialog):
        frame = ttk.Frame(dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Select CPU Cores allowed for BDO:", font=("Segoe UI", 10)).pack(anchor="w", pady=(0, 10))
        
        canvas, scroll_frame = self._create_scrollable_area(frame)
        core_vars = self._populate_core_checkboxes(scroll_frame)
        self._setup_dialog_buttons(dialog, core_vars)

    def _create_scrollable_area(self, parent):
        canvas = tk.Canvas(parent, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)
        
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        parent.winfo_toplevel().bind("<Destroy>", lambda e: canvas.unbind_all("<MouseWheel>"))
        
        return canvas, scroll_frame

    def _populate_core_checkboxes(self, parent):
        core_vars = []
        cpu_count = self.vm.cpu_count
        current_affinity = self.vm.affinity or list(range(cpu_count))
        
        COLUMNS = 2
        for i in range(cpu_count):
            var = tk.BooleanVar(value=(i in current_affinity))
            chk = ttk.Checkbutton(parent, text=f"CPU {i}", variable=var)
            chk.grid(row=i // COLUMNS, column=i % COLUMNS, sticky="w", padx=10, pady=2)
            core_vars.append((i, var))
            
        for i in range(COLUMNS):
            parent.columnconfigure(i, weight=1)
            
        return core_vars

    def _setup_dialog_buttons(self, dialog, core_vars):
        btn_frame = ttk.Frame(dialog, padding=10)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        def apply():
            selected = [i for i, var in core_vars if var.get()]
            if not selected:
                tk.messagebox.showwarning("Warning", "Select at least one core!", parent=dialog)
                return
            if self.vm.set_affinity(selected):
                self.vm.refresh()
                dialog.destroy()
            else:
                tk.messagebox.showerror("Error", "Failed to set affinity.", parent=dialog)
                
        def optimize():
            for i, var in core_vars:
                var.set(i not in [0, 1])
                
        def select_all():
            for _, var in core_vars:
                var.set(True)

        ttk.Button(btn_frame, text="Apply", command=apply).pack(side=tk.RIGHT)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Recommended (No 0/1)", command=optimize).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="All Cores", command=select_all).pack(side=tk.LEFT, padx=5)

    def on_priority_change(self, event):
        val = self.priority_combo.get()
        if val:
            self.vm.set_manual_priority(val)
        self.root.focus()

    def refresh_loop(self):
        self.vm.refresh()
        self.update_view()
        self.root.after(self.vm.settings.poll_interval_ms, self.refresh_loop)

    def update_view(self):
        # Update Ping
        ping_text = f"Ping: {self.vm.game_latency:.0f} ms" if self.vm.game_latency is not None else "Ping: -- ms"
        self.ping_label.config(text=ping_text)

        # Update Info
        status_str = "Running" if self.vm.status == ProcessStatus.RUNNING else "Not Running"
        pid_str = f"PID: {self.vm.pid}" if self.vm.pid else "PID: -"
        self.proc_label.config(text=f"{self.vm.settings.process_name} ({pid_str}) | {status_str}")
        
        # Update Priority
        if self.vm.priority != self.priority_combo.get():
             self.priority_combo.set(self.vm.priority)
             
        is_high = self.vm.priority in ["Above Normal", "High", "Realtime"]
        self.priority_combo.configure(style="Success.TCombobox" if is_high else "TCombobox")
        self.priority_combo['foreground'] = UIConstants.FG_SUCCESS if is_high else UIConstants.FG_WHITE
             
        # Update Affinity
        aff_len = len(self.vm.affinity) if self.vm.affinity else 0
        self.affinity_val_label.config(text=f"{aff_len} cores")
        
        # Check optimization (No 0/1)
        is_optimized = bool(self.vm.affinity) and (0 not in self.vm.affinity) and (1 not in self.vm.affinity)
        self.affinity_val_label.config(foreground=UIConstants.FG_SUCCESS if is_optimized else UIConstants.FG_WHITE)

        # Update Admin Label
        if self.vm.is_admin:
            self.admin_label.pack_forget()
        else:
            self.admin_label.pack(side=tk.RIGHT, anchor="e")

        # Update Table
        self._update_table()

    def _update_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for conn in self.vm.connections:
            latency = f"{conn.latency_ms:.0f} ms" if conn.latency_ms else "N/A"
            tags = ("gamerow",) if "Game Server" in conn.service_name else ()
            
            self.tree.insert("", tk.END, values=(
                conn.remote_ip,
                str(conn.remote_port),
                conn.service_name,
                latency
            ), tags=tags)
