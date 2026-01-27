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
    # Geometry removed to allow auto-sizing
    root.resizable(False, False)
    
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
    FONT_HEADER = ("Segoe UI", 10, "bold")
    FONT_METRIC_VALUE = ("Segoe UI", 24, "bold")
    FONT_PING_VALUE = ("Segoe UI", 32, "bold")
    FONT_METRIC_LABEL = ("Segoe UI", 12, "bold")
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
        self.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
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
        # Top Compact Info Bar
        self._setup_top_info_bar()
        # Main Grid Metrics
        self._setup_metrics_grid()
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

    def _setup_top_info_bar(self):
        self.info_bar = ttk.Frame(self, padding=(10, 5), relief="flat")
        self.info_bar.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        # Details inside a single frame
        details_inner = ttk.Frame(self.info_bar)
        details_inner.pack(fill=tk.X)

        # Priority
        ttk.Label(details_inner, text="Priority: ", foreground=UIConstants.FG_GREY).pack(side=tk.LEFT)
        self.priority_combo = ttk.Combobox(
            details_inner, 
            values=["Idle", "Below Normal", "Normal", "Above Normal", "High", "Realtime"],
            state="readonly",
            width=11
        )
        self.priority_combo.pack(side=tk.LEFT)
        self.priority_combo.bind("<<ComboboxSelected>>", self.on_priority_change)

        self._add_divider(details_inner)

        # Affinity
        ttk.Label(details_inner, text="Affinity: ", foreground=UIConstants.FG_GREY).pack(side=tk.LEFT)
        self.affinity_val_label = ttk.Label(
            details_inner, 
            text="...", 
            font=UIConstants.FONT_BOLD, 
            foreground=UIConstants.FG_WHITE
        )
        self.affinity_val_label.pack(side=tk.LEFT)
        
        # Affinity Edit Button
        ttk.Button(
            details_inner,
            text="⚙️",
            width=3,
            command=self.open_affinity_dialog
        ).pack(side=tk.LEFT, padx=(5, 0))

    def _setup_metrics_grid(self):
        grid_container = ttk.Frame(self, padding=(20, 5)) 
        grid_container.pack(fill=tk.BOTH, expand=True)

        # Layout 3x3 (approx)
        # Row 0: Ping
        # Row 1: GPU, vRAM, GPU Temp
        # Row 2: CPU, RAM, CPU Temp

        # Row 0
        self.ping_frame = self._create_metric_cell(grid_container, "Ping", "0", row=0, col=0, val_font=UIConstants.FONT_PING_VALUE)
        self.ping_val_label = self.ping_frame.val_label
        
        # Row 1
        self.gpu_frame = self._create_metric_cell(grid_container, "GPU", "0%", row=1, col=0)
        self.gpu_val_label = self.gpu_frame.val_label
        
        self.vram_frame = self._create_metric_cell(grid_container, "/0GB vRAM", "0GB", row=1, col=1)
        self.vram_val_label = self.vram_frame.val_label
        self.vram_label = self.vram_frame.tit_label

        self.gpu_temp_frame = self._create_metric_cell(grid_container, "GPU Temp", "N/A", row=1, col=2)
        self.gpu_temp_val_label = self.gpu_temp_frame.val_label

        # Row 2
        # Renamed Proc -> CPU as requested
        self.cpu_frame = self._create_metric_cell(grid_container, "CPU", "0%", row=2, col=0)
        self.cpu_val_label = self.cpu_frame.val_label

        self.ram_frame = self._create_metric_cell(grid_container, "/0GB RAM", "0GB", row=2, col=1)
        self.ram_val_label = self.ram_frame.val_label
        self.ram_label = self.ram_frame.tit_label

        self.cpu_temp_frame = self._create_metric_cell(grid_container, "CPU Temp", "N/A", row=2, col=2)
        self.cpu_temp_val_label = self.cpu_temp_frame.val_label

        for i in range(3): grid_container.columnconfigure(i, weight=1)
        for i in range(3): grid_container.rowconfigure(i, weight=1)

    def _create_metric_cell(self, parent, label_text, initial_val, row, col, val_font=None):
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=col, sticky="w", padx=10, pady=5)
        
        if val_font is None:
            val_font = UIConstants.FONT_METRIC_VALUE

        # Stacked: Label on top, Value below
        lbl = ttk.Label(frame, text=label_text, font=UIConstants.FONT_BOLD, foreground=UIConstants.FG_GREY)
        lbl.pack(side=tk.TOP, anchor="w")
        
        val_lbl = ttk.Label(frame, text=initial_val, font=val_font, foreground=UIConstants.FG_WHITE)
        val_lbl.pack(side=tk.TOP, anchor="w")
        
        frame.tit_label = lbl
        frame.val_label = val_lbl
        return frame

    def _add_divider(self, parent):
        ttk.Label(parent, text=" | ", foreground="#666666").pack(side=tk.LEFT, padx=5)

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
        print(f"DEBUG: on_priority_change val={val} vm={self.vm}")
        if val:
            self.vm.set_manual_priority(val)
        self.root.focus()

    def refresh_loop(self):
        self.vm.refresh()
        self.update_view()
        self.root.after(self.vm.settings.poll_interval_ms, self.refresh_loop)

    def update_view(self):
        # Update Ping
        ping_val = f"{self.vm.game_latency:.0f}" if self.vm.game_latency is not None else "--"
        self.ping_val_label.config(text=ping_val)

        # Update Title with Process Info
        base_title = "BDO Monitor"
        if self.vm.pid:
            base_title += f" - {self.vm.settings.process_name} ({self.vm.pid})"
        
        if not self.vm.is_admin:
             self.root.title(f"{base_title} - Admin Required (Limited Controls)")
        else:
             self.root.title(base_title)
             
        # Update Priority
        if self.vm.priority != self.priority_combo.get():
             self.priority_combo.set(self.vm.priority)
             
        is_high = self.vm.priority in ["Above Normal", "High", "Realtime"]
        self.priority_combo.configure(style="Success.TCombobox" if is_high else "TCombobox")
        self.priority_combo['foreground'] = UIConstants.FG_SUCCESS if is_high else UIConstants.FG_WHITE
        
        # Update Stats (Clean format from ViewModel)
        self.ram_val_label.config(text=self.vm.ram_used_str)
        self.ram_label.config(text=self.vm.ram_total_label)
        
        self.gpu_val_label.config(text=self.vm.gpu_usage_str)

        self.vram_val_label.config(text=self.vm.vram_display_str)
        self.vram_label.config(text=self.vm.vram_total_label)
        
        self.cpu_val_label.config(text=self.vm.cpu_usage_str)
        
        # Update Temps
        self.cpu_temp_val_label.config(text=self.vm.cpu_temp_str)
        self.gpu_temp_val_label.config(text=self.vm.gpu_temp_str)
             
        aff_len = len(self.vm.affinity) if self.vm.affinity else 0
        self.affinity_val_label.config(text=f"{aff_len} cores")
        
        is_optimized = bool(self.vm.affinity) and (0 not in self.vm.affinity) and (1 not in self.vm.affinity)
        self.affinity_val_label.config(foreground=UIConstants.FG_SUCCESS if is_optimized else UIConstants.FG_WHITE)

