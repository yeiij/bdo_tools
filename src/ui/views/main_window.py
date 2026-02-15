"""Main Window View."""

import os
import sys
import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox, ttk

import darkdetect
import sv_ttk

from ui.tray import SystemTrayIcon
from ui.viewmodels.main_viewmodel import MainViewModel


def resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS

        base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class UIConstants:
    """Standard UI constants for the application."""

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


class ProcessControlBar(ttk.Frame):
    """A modular bar for controlling a process's priority and affinity."""

    def __init__(self, parent, process_name: str, on_priority_change: Callable, on_affinity_click: Callable):
        super().__init__(parent, padding=(10, 5))
        self.process_name = process_name
        self.on_priority_change = on_priority_change
        self.on_affinity_click = on_affinity_click

        self.header_label = ttk.Label(self, text=process_name, font=UIConstants.FONT_HEADER)
        self.header_label.pack(side=tk.TOP, anchor="w", pady=(0, 5))

        details = ttk.Frame(self)
        details.pack(fill=tk.X)

        ttk.Label(details, text="Priority: ", foreground=UIConstants.FG_GREY).pack(side=tk.LEFT)
        self.priority_combo = ttk.Combobox(
            details,
            values=["Idle", "Below Normal", "Normal", "Above Normal", "High", "Realtime"],
            state="readonly",
            width=11,
        )
        self.priority_combo.pack(side=tk.LEFT)
        self.priority_combo.bind("<<ComboboxSelected>>", self._handle_priority_change)

        ttk.Label(parent, text=" | ", foreground="#666666").pack(in_=details, side=tk.LEFT, padx=5)

        ttk.Label(details, text="Affinity: ", foreground=UIConstants.FG_GREY).pack(side=tk.LEFT)
        self.affinity_val_label = ttk.Label(details, text="...", font=UIConstants.FONT_BOLD)
        self.affinity_val_label.pack(side=tk.LEFT)
        self.affinity_button = ttk.Button(details, text="⚙️", width=3, command=on_affinity_click)
        self.affinity_button.pack(side=tk.LEFT, padx=(5, 0))

    def _handle_priority_change(self, event):
        val = self.priority_combo.get()
        if val:
            ok = self.on_priority_change(val)
            if ok is False:
                messagebox.showerror("Error", "Failed to set priority. Run as Administrator and try again.")

    def update_state(self, pid: int | None, priority: str, affinity: list[int], cpu_count: int, is_admin: bool):
        exists = bool(pid)
        can_modify = exists and is_admin
        state = "readonly" if can_modify else "disabled"
        btn_state = "normal" if can_modify else "disabled"

        self.priority_combo.config(state=state)
        self.affinity_button.config(state=btn_state)
        self.header_label.config(foreground=UIConstants.FG_ACCENT if exists else UIConstants.FG_GREY)

        if priority != self.priority_combo.get():
            self.priority_combo.set(priority)

        is_high = priority in ["Above Normal", "High", "Realtime"]
        self.priority_combo.configure(style="Success.TCombobox" if is_high else "TCombobox")
        self.priority_combo["foreground"] = UIConstants.FG_SUCCESS if is_high else UIConstants.FG_WHITE

        aff_len = len(affinity) if affinity else 0
        self.affinity_val_label.config(text=f"{aff_len} cores")
        is_mod = 0 < aff_len < cpu_count
        self.affinity_val_label.config(foreground=UIConstants.FG_SUCCESS if is_mod else UIConstants.FG_WHITE)


class MetricCell(ttk.Frame):
    """A single cell in the metrics grid."""

    def __init__(self, parent, label: str, font_val=None):
        super().__init__(parent)
        self.title_label = ttk.Label(self, text=label, font=UIConstants.FONT_BOLD, foreground=UIConstants.FG_GREY)
        self.title_label.pack(side=tk.TOP, anchor="w")
        self.value_label = ttk.Label(
            self,
            text="--",
            font=font_val or UIConstants.FONT_METRIC_VALUE,
            foreground=UIConstants.FG_WHITE,
        )
        self.value_label.pack(side=tk.TOP, anchor="w")

    def set_value(self, value: str, title: str | None = None):
        self.value_label.config(text=value)
        if title:
            self.title_label.config(text=title)


class MainWindow(ttk.Frame):
    def __init__(self, root: tk.Tk, viewModel: MainViewModel):
        super().__init__(root, padding=10)
        self.root = root
        self.vm = viewModel
        self.tray_icon: SystemTrayIcon | None = None

        self._setup_styles()
        self._setup_ui()
        self.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self._setup_tray()
        self.root.bind("<Unmap>", self._on_window_state_change)
        self.root.protocol("WM_DELETE_WINDOW", self._quit_app)
        self.refresh_loop()

    def _setup_styles(self):
        style = ttk.Style()
        style.configure(
            "TCombobox",
            foreground=UIConstants.FG_WHITE,
            selectbackground=UIConstants.BG_COLOR,
            fieldbackground=UIConstants.BG_COLOR,
        )
        style.map(
            "TCombobox",
            selectbackground=[("readonly", UIConstants.BG_COLOR)],
            selectforeground=[("readonly", UIConstants.FG_WHITE)],
        )

        style.configure(
            "Success.TCombobox",
            foreground=UIConstants.FG_SUCCESS,
            selectforeground=UIConstants.FG_SUCCESS,
            selectbackground=UIConstants.BG_COLOR,
            fieldbackground=UIConstants.BG_COLOR,
        )
        style.map(
            "Success.TCombobox",
            foreground=[("readonly", UIConstants.FG_SUCCESS)],
            selectforeground=[("readonly", UIConstants.FG_SUCCESS)],
        )

    def _setup_ui(self):
        # 1. Process Controls
        self.game_bar = ProcessControlBar(
            self,
            self.vm.settings.game_process_name,
            self.vm.set_manual_priority,
            lambda: self.open_affinity_dialog(
                f"{self.vm.settings.game_process_name} Affinity",
                self.vm.affinity,
                self.vm.set_affinity,
            ),
        )
        self.game_bar.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        self.network_bar = ProcessControlBar(
            self,
            self.vm.settings.network_process_name,
            self.vm.set_network_manual_priority,
            lambda: self.open_affinity_dialog(
                f"{self.vm.settings.network_process_name} Affinity",
                self.vm.network_affinity,
                self.vm.set_network_affinity,
            ),
        )
        self.network_bar.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        # 2. Metrics Grid
        grid = ttk.Frame(self, padding=(20, 5))
        grid.pack(fill=tk.BOTH, expand=True)

        self.cell_ping = MetricCell(grid, "Ping Now", UIConstants.FONT_PING_VALUE)
        self.cell_ping.grid(row=0, column=0, sticky="w", padx=10, pady=5)

        self.cell_ping_low = MetricCell(grid, "Ping Low")
        self.cell_ping_low.grid(row=0, column=1, sticky="w", padx=10, pady=5)

        self.cell_ping_peak = MetricCell(grid, "Ping Peak")
        self.cell_ping_peak.grid(row=0, column=2, sticky="w", padx=10, pady=5)

        self.cell_gpu = MetricCell(grid, "GPU")
        self.cell_gpu.grid(row=1, column=0, sticky="w", padx=10, pady=5)

        self.cell_vram = MetricCell(grid, "/0GB vRAM")
        self.cell_vram.grid(row=1, column=1, sticky="w", padx=10, pady=5)

        self.cell_gpu_temp = MetricCell(grid, "GPU Temp")
        self.cell_gpu_temp.grid(row=1, column=2, sticky="w", padx=10, pady=5)

        self.cell_cpu = MetricCell(grid, "CPU")
        self.cell_cpu.grid(row=2, column=0, sticky="w", padx=10, pady=5)

        self.cell_ram = MetricCell(grid, "/0GB RAM")
        self.cell_ram.grid(row=2, column=1, sticky="w", padx=10, pady=5)

        self.cell_cpu_temp = MetricCell(grid, "CPU Temp")
        self.cell_cpu_temp.grid(row=2, column=2, sticky="w", padx=10, pady=5)

        for i in range(3):
            grid.columnconfigure(i, weight=1)
        for i in range(3):
            grid.rowconfigure(i, weight=1)

        # 3. Footer
        ttk.Label(self, text="by: JasonREDUX", foreground="#555555").pack(side=tk.BOTTOM, anchor="se", padx=5)

    def _setup_tray(self):
        try:
            icon_path = resource_path("resources/icon.ico")
            self.tray_icon = SystemTrayIcon(icon_path, on_show=self.show_window, on_quit=self._quit_app)
        except Exception:
            pass

    def _on_window_state_change(self, event):
        if event.widget == self.root and self.root.state() == "iconic":
            self.hide_to_tray()

    def hide_to_tray(self):
        self.root.withdraw()
        if self.tray_icon:
            self.tray_icon.run()

    def show_window(self):
        self.root.after(0, self._restore_window)

    def _restore_window(self):
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.deiconify()
        self.root.state("normal")
        self.root.lift()
        self.root.focus_force()

    def _quit_app(self):
        try:
            reload_settings = getattr(self.vm, "_reload_settings_if_changed", None)
            if callable(reload_settings):
                reload_settings()
            save_settings = getattr(self.vm, "_save_settings", None)
            if callable(save_settings):
                save_settings()
            else:
                self.vm.settings.save()
        except Exception:
            # Best-effort persistence; shutdown should still proceed.
            pass
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.destroy()
        sys.exit(0)

    def open_affinity_dialog(self, title: str, current: list[int], callback: Callable):
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        try:
            dialog.iconbitmap(resource_path("resources/icon.ico"))
        except Exception:
            pass

        # Sizing and centering is handled at the end of the method
        dialog.transient(self.root)
        dialog.grab_set()

        container = ttk.Frame(dialog, padding=10)
        container.pack(fill=tk.BOTH, expand=True)
        ttk.Label(container, text="Select CPU Cores:", font=UIConstants.FONT_BOLD).pack(anchor="w", pady=(0, 10))

        canvas = tk.Canvas(container, highlightthickness=0)
        scrollable = ttk.Frame(canvas)
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")

        vars = []
        cpu_count = self.vm.cpu_count or 1
        for i in range(cpu_count):
            v = tk.BooleanVar(value=(i in current))
            vars.append(v)
            cb = ttk.Checkbutton(scrollable, text=f"CPU {i}", variable=v)
            cb.grid(row=i // 2, column=i % 2, sticky="w", padx=15, pady=2)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Only show scrollbar if we have many rows (e.g. > 16 cores / 2 = 8 rows)
        if cpu_count > 20:
            scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
            canvas.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        def apply():
            selected = [i for i, v in enumerate(vars) if v.get()]
            if not selected:
                messagebox.showwarning("Warning", "Select at least one core!")
                return
            if callback(selected):
                dialog.destroy()
            else:
                messagebox.showerror("Error", "Failed to set affinity.")

        btns = ttk.Frame(dialog, padding=10)
        btns.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Button(btns, text="Apply", command=apply).pack(side=tk.RIGHT)
        ttk.Button(btns, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)

        self._center_dialog(dialog)

    def _center_dialog(self, dialog):
        """Auto-size and center the dialog relative to the main window."""
        dialog.update_idletasks()
        # Add some padding to the requested size
        w = dialog.winfo_reqwidth() + 20
        h = dialog.winfo_reqheight() + 20

        rx, ry, rw, rh = (
            self.root.winfo_x(),
            self.root.winfo_y(),
            self.root.winfo_width(),
            self.root.winfo_height(),
        )
        cx, cy = rx + (rw // 2) - (w // 2), ry + (rh // 2) - (h // 2)

        dialog.geometry(f"{w}x{h}+{cx}+{cy}")
        dialog.resizable(False, False)

    def refresh_loop(self):
        self.vm.refresh()
        self.update_view()
        self.root.after(self.vm.settings.interval, self.refresh_loop)

    def update_view(self):
        """Update all widgets from VM state."""
        # Title
        self.root.title(f"GamerMonitor{' - Admin Required' if not self.vm.is_admin else ''}")

        # Bars
        self.game_bar.update_state(self.vm.pid, self.vm.priority, self.vm.affinity, self.vm.cpu_count, self.vm.is_admin)
        self.network_bar.update_state(
            self.vm.network_pid,
            self.vm.network_priority,
            self.vm.network_affinity,
            self.vm.cpu_count,
            self.vm.is_admin,
        )

        # Cells
        ping_title = "Ping Now"
        if self.vm.network_pid and self.vm.settings.network_process_name:
            ping_title = f"Ping Now ({self.vm.settings.network_process_name})"
        now_latency = self._format_ping(getattr(self.vm, "game_latency_current", self.vm.game_latency))
        low_latency = self._format_ping(getattr(self.vm, "game_latency_low", self.vm.game_latency))
        peak_latency = self._format_ping(getattr(self.vm, "game_latency_peak", self.vm.game_latency))

        self.cell_ping.set_value(now_latency, ping_title)
        self.cell_ping_low.set_value(low_latency)
        self.cell_ping_peak.set_value(peak_latency)
        self.cell_ping.value_label.config(foreground=UIConstants.FG_WHITE)
        self.cell_gpu.set_value(self.vm.gpu_usage_str)
        self.cell_vram.set_value(self.vm.vram_display_str, self.vm.vram_total_label)
        self.cell_gpu_temp.set_value(self.vm.gpu_temp_str)
        self.cell_cpu.set_value(self.vm.cpu_usage_str)
        self.cell_ram.set_value(self.vm.ram_used_str, self.vm.ram_total_label)
        self.cell_cpu_temp.set_value(self.vm.cpu_temp_str)

    @staticmethod
    def _format_ping(value) -> str:
        if isinstance(value, (int, float)):
            return f"{value:.0f}"
        return "--"


def start_app(viewModel: MainViewModel):
    root = tk.Tk()
    root.title("GamerMonitor")
    root.resizable(False, False)

    try:
        root.iconbitmap(resource_path("resources/icon.ico"))
    except Exception:
        pass

    sv_ttk.set_theme(darkdetect.theme().lower() if darkdetect.theme() else "dark")
    MainWindow(root, viewModel)
    root.mainloop()
