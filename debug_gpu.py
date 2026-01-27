import pynvml
import psutil

def debug_gpu():
    try:
        pynvml.nvmlInit()
        count = pynvml.nvmlDeviceGetCount()
        print(f"NVML Initialized. Device Count: {count}")
        
        for i in range(count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            name = pynvml.nvmlDeviceGetName(handle)
            print(f"\nGPU {i}: {name}")
            
            # Compute
            try:
                print("  Compute Processes:")
                procs = pynvml.nvmlDeviceGetComputeRunningProcesses(handle)
                for p in procs:
                    try:
                        name = psutil.Process(p.pid).name()
                    except:
                        name = "Unknown"
                    print(f"    PID: {p.pid} ({name}) - Mem: {p.usedGpuMemory}")
            except Exception as e:
                print(f"    Error getting compute processes: {e}")

            # Graphics
            try:
                print("  Graphics Processes:")
                procs = pynvml.nvmlDeviceGetGraphicsRunningProcesses(handle)
                for p in procs:
                    try:
                        name = psutil.Process(p.pid).name()
                    except:
                        name = "Unknown"
                    print(f"    PID: {p.pid} ({name}) - Mem: {p.usedGpuMemory}")
            except Exception as e:
                print(f"    Error getting graphics processes: {e}")
                
    except Exception as e:
        print(f"NVML Init/Error: {e}")

if __name__ == "__main__":
    debug_gpu()
