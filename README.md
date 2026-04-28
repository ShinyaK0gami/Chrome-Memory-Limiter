# 🛡️ RAM Guardian

**A modern, lightweight desktop application that strictly limits Google Chrome's memory footprint.**

RAM Guardian acts as a strict "bouncer" for your system memory. Instead of blindly killing your active workflow, it allows you to allocate a hard Gigabyte (GB) limit specifically for Chrome. Once Chrome hits that limit, RAM Guardian intercepts and blocks any *new* tabs from opening until memory is freed up, ensuring your PC never crashes from browser memory leaks again.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![CustomTkinter](https://img.shields.io/badge/UI-CustomTkinter-success.svg)
![OS](https://img.shields.io/badge/OS-Windows-lightgrey.svg)

---

## ✨ Features
* **Modern "Glassy" UI:** Built with CustomTkinter for a sleek, Apple-inspired interface with translucent window effects and native dark/light mode support.
* **True Chrome Isolation:** Uses `psutil` to calculate the Unique Set Size (USS) of all `chrome.exe` processes, completely ignoring shared memory to give you hyper-accurate, Task-Manager-aligned memory tracking.
* **Dynamic Hardware Detection:** Automatically detects your motherboard's physical RAM and scales the UI limits to match your specific machine.
* **Proactive Warnings:** Triggers a native Windows popup warning when Chrome reaches 85% of your allocated limit.
* **Strict Tab Blocking:** Instantly terminates newly spawned Chrome processes the millisecond they open if you are over your limit, protecting your existing tabs and your operating system.
* **Standalone Executable:** Fully packaged into a single `.exe` file with custom taskbar and window icons.

---

## 🛠️ How It Works (The "Bouncer" Method)
RAM Guardian is designed to be safe for your workflow. 

If you allocate 4GB to Chrome, and Chrome hits 4.0GB, RAM Guardian **will not** randomly kill your open tabs (which could cause you to lose unsaved work). Instead, it takes a snapshot of your currently open tabs. If you try to open a *new* tab, RAM Guardian instantly kills that new specific process (resulting in an "Aw, Snap!" page on the new tab), leaving your existing workflow entirely untouched.

> **💡 Pro-Tip:** For the ultimate setup, pair RAM Guardian with Chrome's native **Memory Saver** (`chrome://settings/performance`). RAM Guardian stops new tabs from overwhelming your system, while Chrome's Memory Saver quietly puts your background tabs to sleep!

---

## 🚀 Installation & Usage

### Option 1: Run the Pre-Compiled Executable (Easiest)
1. Go to the **Releases** tab on the right side of this GitHub page.
2. Download `RAM_Guardian.exe`.
3. Double-click to run! (Note: Windows Defender might show a "Windows protected your PC" popup since the app is new. Click **More Info** -> **Run Anyway**).

### Option 2: Run from Source
If you prefer to run the raw Python script:
1. Clone this repository:
   ```bash
   git clone [https://github.com/yourusername/RAM-Guardian.git](https://github.com/yourusername/RAM-Guardian.git)
