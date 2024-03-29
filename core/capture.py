import os
import platform
from PIL import Image

if platform.system() == 'Windows':
    import win32gui
    from PIL import ImageGrab
    import ctypes
    # Fix for high-DPI displays (prevents cropped screenshots)
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
else:
    # Linux/Mac - use mss for screenshots
    try:
        import mss
    except ImportError:
        mss = None

def get_open_windows():
    """Returns a list of (hwnd, title) for all visible windows."""
    if platform.system() == 'Windows':
        winlist = []
        def enum_cb(hwnd, results):
            if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                winlist.append((hwnd, win32gui.GetWindowText(hwnd)))
        win32gui.EnumWindows(enum_cb, winlist)
        return winlist
    else:
        # Linux: Try to use wmctrl if available
        try:
            import subprocess
            result = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True)
            if result.returncode == 0:
                windows = []
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split(None, 3)
                        if len(parts) >= 4:
                            hwnd = parts[0]
                            title = parts[3]
                            windows.append((hwnd, title))
                return windows
        except (FileNotFoundError, subprocess.SubprocessError):
            pass
        return []

def find_browser_window(custom_target=None):
    """
    Finds a window handle (hwnd or window_id).
    Priority:
    1. 'custom_target' if provided (e.g., "Discord").
    2. Any common browser (Chrome, Firefox, Edge, Opera, Brave).
    """
    windows = get_open_windows()
    
    # If user asked for a specific app
    if custom_target:
        for hwnd, title in windows:
            if custom_target.lower() in title.lower():
                return hwnd, title

    # Fallback: Search for common browsers
    COMMON_BROWSERS = ['chrome', 'firefox', 'msedge', 'opera', 'brave', 'vivaldi']
    for browser in COMMON_BROWSERS:
        for hwnd, title in windows:
            if browser in title.lower():
                return hwnd, title
                
    return None, None

def grab_screen(target_name=None):
    """
    Finds the browser, brings it to front, and captures it.
    Cross-platform: Windows uses win32gui, Linux uses mss.
    """
    if platform.system() == 'Windows':
        hwnd, title = find_browser_window(target_name)
        
        if not hwnd:
            print("No browser or target window found!")
            return None

        print(f"Capturing window: {title}")

        try:
            # Bring window to front
            win32gui.ShowWindow(hwnd, 5)  # SW_SHOW
            win32gui.SetForegroundWindow(hwnd)
            
            # Get dimensions
            bbox = win32gui.GetWindowRect(hwnd)
            img = ImageGrab.grab(bbox)
            return img
        except Exception as e:
            print(f"Error capturing window: {e}")
            return None
    else:
        # Linux/Mac path
        if mss is None:
            print("Warning: 'mss' package not installed. Installing it...")
            print("Please run: pip install mss")
            # Fallback: try to use ImageGrab if available (works on some Linux setups)
            try:
                from PIL import ImageGrab
                print("Using PIL ImageGrab as fallback (full screen)")
                img = ImageGrab.grab()
                return img
            except Exception:
                print("Error: Cannot capture screen. Please install 'mss' package.")
                return None
        
        # Try to find and focus the browser window
        window_id, title = find_browser_window(target_name)
        
        if not window_id:
            print("No browser or target window found!")
            # Fallback to full screen
            try:
                with mss.mss() as sct:
                    monitor = sct.monitors[1]
                    screenshot = sct.grab(monitor)
                    img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                    print("Captured full screen (no specific window found)")
                    return img
            except Exception as e:
                print(f"Error capturing screen: {e}")
                return None
        
        print(f"Found window: {title}")
        
        # Get window geometry on Linux
        window_geometry = None
        tools_available = {'xdotool': False, 'wmctrl': False}
        
        if platform.system() == 'Linux':
            # Check which tools are available
            import subprocess
            try:
                subprocess.run(['xdotool', '--version'], capture_output=True, timeout=1, check=True)
                tools_available['xdotool'] = True
            except (FileNotFoundError, subprocess.SubprocessError, subprocess.TimeoutExpired):
                pass
            
            try:
                subprocess.run(['wmctrl', '-v'], capture_output=True, timeout=1, check=True)
                tools_available['wmctrl'] = True
            except (FileNotFoundError, subprocess.SubprocessError, subprocess.TimeoutExpired):
                pass
            
            if not tools_available['xdotool'] and not tools_available['wmctrl']:
                print("Warning: Neither 'xdotool' nor 'wmctrl' is installed.")
                print("To capture specific windows, install one of them:")
                print("  sudo apt-get install xdotool wmctrl")
                print("Falling back to full screen capture...")
            else:
                # Try xdotool first (more reliable)
                if tools_available['xdotool']:
                    try:
                        result = subprocess.run(['xdotool', 'getwindowgeometry', window_id], 
                                              capture_output=True, text=True, timeout=2)
                        if result.returncode == 0:
                            # Parse geometry output
                            for line in result.stdout.split('\n'):
                                if 'Geometry:' in line:
                                    # Format: Geometry: 1920x1080
                                    parts = line.split('Geometry:')[1].strip().split('x')
                                    if len(parts) == 2:
                                        width, height = int(parts[0]), int(parts[1])
                                        # Get window position
                                        pos_result = subprocess.run(['xdotool', 'getwindowgeometry', '--shell', window_id],
                                                                  capture_output=True, text=True, timeout=2)
                                        if pos_result.returncode == 0:
                                            x, y = None, None
                                            for pos_line in pos_result.stdout.split('\n'):
                                                if pos_line.startswith('X='):
                                                    x = int(pos_line.split('=')[1])
                                                elif pos_line.startswith('Y='):
                                                    y = int(pos_line.split('=')[1])
                                            if x is not None and y is not None:
                                                window_geometry = {'left': x, 'top': y, 'width': width, 'height': height}
                    except (subprocess.SubprocessError, subprocess.TimeoutExpired, ValueError) as e:
                        print(f"xdotool failed: {e}")
                
                # Fallback to wmctrl if xdotool failed
                if window_geometry is None and tools_available['wmctrl']:
                    try:
                        result = subprocess.run(['wmctrl', '-lG'], capture_output=True, text=True, timeout=2)
                        if result.returncode == 0:
                            for line in result.stdout.strip().split('\n'):
                                parts = line.split()
                                if len(parts) >= 7 and parts[0] == window_id:
                                    # Format: 0x01234567  0 1920 1080 1920 1080 workspace title
                                    x, y, width, height = int(parts[2]), int(parts[3]), int(parts[4]), int(parts[5])
                                    window_geometry = {'left': x, 'top': y, 'width': width, 'height': height}
                                    break
                    except (subprocess.SubprocessError, subprocess.TimeoutExpired, ValueError, IndexError) as e:
                        print(f"wmctrl failed: {e}")
            
            # Try to bring window to front
            try:
                import subprocess
                subprocess.run(['wmctrl', '-i', '-a', window_id], 
                             capture_output=True, timeout=1)
            except (FileNotFoundError, subprocess.SubprocessError, subprocess.TimeoutExpired):
                pass
        
        # Capture the specific window or full screen
        try:
            with mss.mss() as sct:
                if window_geometry:
                    # Capture specific window region
                    monitor = {
                        'left': window_geometry['left'],
                        'top': window_geometry['top'],
                        'width': window_geometry['width'],
                        'height': window_geometry['height']
                    }
                    screenshot = sct.grab(monitor)
                    img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                    print(f"Captured window: {title} ({window_geometry['width']}x{window_geometry['height']})")
                else:
                    # Fallback to full screen
                    monitor = sct.monitors[1]
                    screenshot = sct.grab(monitor)
                    img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                    print(f"Captured full screen (could not get window geometry for: {title})")
                return img
        except Exception as e:
            print(f"Error capturing screen: {e}")
            return None