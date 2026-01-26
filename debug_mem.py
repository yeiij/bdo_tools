import psutil
import time

def find_process(name):
    for proc in psutil.process_iter(['name', 'pid']):
        try:
            if proc.info['name'] and proc.info['name'].lower() == name.lower():
                return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return None

def print_mem(proc):
    try:
        mem = proc.memory_info()
        print(f"--- Standard Memory Info ---")
        print(f"RSS: {mem.rss / (1024**3):.2f} GB ({mem.rss / (1024**2):.0f} MB)")
        if hasattr(mem, 'vms'): print(f"VMS: {mem.vms / (1024**3):.2f} GB")
        if hasattr(mem, 'num_page_faults'): print(f"Page Faults: {mem.num_page_faults}")
        if hasattr(mem, 'peak_wset'): print(f"Peak WSet: {mem.peak_wset / (1024**2):.0f} MB")
        if hasattr(mem, 'wset'): print(f"WSet: {mem.wset / (1024**2):.0f} MB")
        if hasattr(mem, 'peak_paged_pool'): print(f"Peak Paged Pool: {mem.peak_paged_pool / (1024**2):.0f} MB")
        if hasattr(mem, 'paged_pool'): print(f"Paged Pool: {mem.paged_pool / (1024**2):.0f} MB")
        if hasattr(mem, 'peak_nonpaged_pool'): print(f"Peak NonPaged Pool: {mem.peak_nonpaged_pool / (1024**2):.0f} MB")
        if hasattr(mem, 'nonpaged_pool'): print(f"NonPaged Pool: {mem.nonpaged_pool / (1024**2):.0f} MB")
        if hasattr(mem, 'pagefile'): print(f"Pagefile: {mem.pagefile / (1024**2):.0f} MB")
        if hasattr(mem, 'peak_pagefile'): print(f"Peak Pagefile: {mem.peak_pagefile / (1024**2):.0f} MB")
        if hasattr(mem, 'private'): print(f"Private: {mem.private / (1024**2):.0f} MB")

        print(f"\n--- Full Memory Info (slower) ---")
        full = proc.memory_full_info()
        if hasattr(full, 'uss'): print(f"USS: {full.uss / (1024**2):.0f} MB")
        if hasattr(full, 'pss'): print(f"PSS: {full.pss / (1024**2):.0f} MB")
        if hasattr(full, 'swap'): print(f"Swap: {full.swap / (1024**2):.0f} MB")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    proc = find_process("BlackDesert64.exe")
    if proc:
        print(f"Found {proc.name()} (PID: {proc.pid})")
        print_mem(proc)
    else:
        print("BlackDesert64.exe not found.")
