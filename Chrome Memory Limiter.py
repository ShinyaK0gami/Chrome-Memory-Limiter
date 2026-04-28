import customtkinter as ctk
import psutil
import threading
import time
import os
import sys
from tkinter import messagebox

# --- Helper function for PyInstaller to find bundled files ---
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Set the overall theme to look modern and Apple-like
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class GlassyRamLimiterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("RAM Guardian")
        self.geometry("380x540") # Slightly taller to fit the new text
        self.resizable(False, False)

        # The "frosted glass" transparency effect
        self.attributes('-alpha', 0.95)

        # --- SET THE WINDOW AND TASKBAR ICON ---
        # Change "your_icon.ico" to the exact name of your icon file
        try:
            self.iconbitmap(resource_path("your_icon.ico"))
        except Exception:
            pass # Ignores the error if it can't find the icon

        # --- DYNAMIC HARDWARE DETECTION ---
        # Fetch the exact total physical RAM of the PC in Gigabytes
        self.total_system_ram_gb = psutil.virtual_memory().total / (1024 ** 3)

        # Variables
        self.is_monitoring = False
        self.is_popup_open = False # NEW: State flag to track if popup is active
        
        # Set default slider to 4GB, or to the max RAM if the PC has less than 4GB
        default_limit = min(4.0, self.total_system_ram_gb)
        self.max_gb_limit = ctk.DoubleVar(value=default_limit)
        
        self.known_chrome_pids = set()
        self.last_warning_time = 0

        self.setup_ui()

    def setup_ui(self):
        # Fonts
        title_font = ("-apple-system", 22, "bold")
        num_font = ("-apple-system", 26, "bold")
        main_font = ("-apple-system", 13)
        small_font = ("-apple-system", 11)

        # Main App Title
        self.title_label = ctk.CTkLabel(self, text="RAM Guardian", font=title_font)
        self.title_label.pack(pady=(20, 10))

        # --- Card 1: Live Status ---
        self.status_card = ctk.CTkFrame(self, corner_radius=15)
        self.status_card.pack(fill="x", padx=20, pady=10)

        self.current_ram_label = ctk.CTkLabel(self.status_card, text="Chrome Usage:\n0.00 GB", font=num_font, text_color="#3b82f6")
        self.current_ram_label.pack(pady=(20, 5))

        # Hardware Info Label
        self.hardware_label = ctk.CTkLabel(self.status_card, text=f"Total System Hardware RAM: {self.total_system_ram_gb:.2f} GB", font=small_font, text_color="gray")
        self.hardware_label.pack(pady=(0, 15))

        # --- Card 2: Settings & Thresholds ---
        self.settings_card = ctk.CTkFrame(self, corner_radius=15)
        self.settings_card.pack(fill="x", padx=20, pady=5)

        self.slider_label = ctk.CTkLabel(self.settings_card, text=f"Allocation Limit: {self.max_gb_limit.get():.1f} GB", font=main_font)
        self.slider_label.pack(pady=(15, 5))

        # SLIDER DYNAMIC UPDATE: Max limit is now the PC's actual physical RAM
        self.slider = ctk.CTkSlider(self.settings_card, from_=1.0, to=self.total_system_ram_gb, variable=self.max_gb_limit, command=self.update_thresholds)
        self.slider.pack(fill="x", padx=20, pady=5)

        # Threshold texts
        self.warn_label = ctk.CTkLabel(self.settings_card, text="⚠️ Warns at: 0.00 GB", font=small_font, text_color="#f59e0b")
        self.warn_label.pack(anchor="w", padx=20, pady=(5, 0))

        self.block_label = ctk.CTkLabel(self.settings_card, text="🛑 Kills New Tabs at: 0.00 GB", font=small_font, text_color="#ef4444")
        self.block_label.pack(anchor="w", padx=20, pady=(0, 15))

        # --- Action Button ---
        self.toggle_btn = ctk.CTkButton(self, text="Start Monitoring", font=("-apple-system", 15, "bold"), 
                                        corner_radius=10, height=45, fg_color="#10b981", hover_color="#059669", 
                                        command=self.toggle_monitoring)
        self.toggle_btn.pack(fill="x", padx=20, pady=20)

        # --- Log Console ---
        self.log_text = ctk.CTkTextbox(self, height=80, corner_radius=10, font=("Consolas", 11), fg_color=("gray90", "gray12"))
        self.log_text.pack(fill="x", padx=20, pady=(0, 20))
        self.log_text.configure(state="disabled")

        self.update_thresholds()

    def log(self, message):
        """Appends a message to the UI log."""
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"{time.strftime('%H:%M:%S')} - {message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def update_thresholds(self, *args):
        """Updates the UI math when the slider moves."""
        val = self.max_gb_limit.get()
        self.slider_label.configure(text=f"Allocation Limit: {val:.1f} GB")
        self.warn_label.configure(text=f"⚠️ Warns at: {(val * 0.85):.2f} GB")
        self.block_label.configure(text=f"🛑 Kills New Tabs at: {val:.2f} GB")

    def toggle_monitoring(self):
        """Starts or stops the background monitoring thread."""
        if self.is_monitoring:
            self.is_monitoring = False
            self.toggle_btn.configure(text="Start Monitoring", fg_color="#10b981", hover_color="#059669")
            self.slider.configure(state="normal")
            self.log("Monitoring stopped.")
        else:
            self.is_monitoring = True
            self.toggle_btn.configure(text="Stop Monitoring", fg_color="#ef4444", hover_color="#dc2626")
            self.slider.configure(state="disabled")
            
            _, pids = self.get_chrome_stats()
            self.known_chrome_pids = pids
            self.log(f"Started. Tracking {len(self.known_chrome_pids)} processes.")
            
            threading.Thread(target=self.monitor_loop, daemon=True).start()

    def get_chrome_stats(self):
        """Sums up the memory of all Chrome processes and returns total GB and PID set."""
        total_ram_bytes = 0
        pids = set()
        
        # Removed 'memory_info' from process_iter to use the deeper memory_full_info() method
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                    pids.add(proc.info['pid'])
                    
                    # .uss (Unique Set Size) excludes shared memory. 
                    # This prevents double-counting and matches Task Manager's "Private" memory.
                    mem_info = proc.memory_full_info()
                    total_ram_bytes += mem_info.uss 
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
                
        return (total_ram_bytes / (1024 ** 3)), pids

    def monitor_loop(self):
        """Checks Chrome's RAM footprint and blocks new tabs if necessary."""
        while self.is_monitoring:
            try:
                chrome_gb, current_chrome_pids = self.get_chrome_stats()
                
                # Update UI safely
                self.after(0, lambda gb=chrome_gb: self.current_ram_label.configure(text=f"Chrome Usage:\n{gb:.2f} GB"))

                limit_gb = self.max_gb_limit.get()
                warn_threshold = limit_gb * 0.85
                new_pids = current_chrome_pids - self.known_chrome_pids

                # Apply Enforcement Logic
                if chrome_gb >= limit_gb:
                    if new_pids:
                        for pid in new_pids:
                            try:
                                psutil.Process(pid).terminate()
                                self.after(0, lambda p=pid: self.log(f"Blocked new tab (PID: {p})"))
                            except Exception:
                                pass
                else:
                    self.known_chrome_pids.update(new_pids)

                # Warning Logic
                if chrome_gb >= warn_threshold and chrome_gb < limit_gb:
                    now = time.time()
                    
                    # NEW: Only trigger if the popup is NOT currently open AND 3 minutes have passed since the last one
                    if not self.is_popup_open and (now - self.last_warning_time > 180): 
                        self.after(0, lambda gb=chrome_gb: self.show_warning(gb))

                # Clean up closed tabs
                closed_pids = self.known_chrome_pids - current_chrome_pids
                self.known_chrome_pids.difference_update(closed_pids)

            except Exception as e:
                self.after(0, lambda err=e: self.log(f"Error: {err}"))
            
            time.sleep(1.5)

    def show_warning(self, current_gb):
        """Displays an OS-level popup warning."""
        self.is_popup_open = True # Flag that the popup is actively on screen
        
        self.log("Warning displayed.")
        self.attributes('-topmost', True)
        
        # The program will pause on this line until the user clicks "OK"
        messagebox.showwarning(
            "RAM Guardian", 
            f"High Chrome Memory Usage!\nChrome is currently using {current_gb:.2f} GB. "
            "You are approaching your strict allocation limit."
        )
        
        # These lines run immediately after the user closes the popup
        self.attributes('-topmost', False)
        self.is_popup_open = False # Flag that the popup is gone
        self.last_warning_time = time.time() # Reset the 3-minute timer *after* it closes

if __name__ == "__main__":
    try:
        from ctypes import windll
        import ctypes
        
        # --- THE FIX: Tell Windows this is a unique App ---
        myappid = 'ramguardian.custom.app.v1'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        
        # DPI Awareness for sharp text
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    app = GlassyRamLimiterApp()
    app.mainloop()