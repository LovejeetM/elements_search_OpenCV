import pywinauto
from pywinauto.findwindows import ElementNotFoundError
from pywinauto.uia_defines import NoPatternInterfaceError
from PIL import ImageGrab, Image
import os
import time
import re
import ctypes
import keyboard


OUTPUT_DIR = "interactive_visible_elements"
TASKBAR_CLASS_NAME = "Shell_TrayWnd" 
INTERACTIVE_TYPES = {
    "Button", "CheckBox", "RadioButton", "MenuItem", "ListItem",
    "Hyperlink", "TabItem", "ComboBox", "Spinner", "SplitButton",
    "TreeItem", "Edit"
}
INTERACTIVE_KEYWORDS = {"button", "icon", "click", "link", "select", "menu", "tab", "choose", "add", "remove", "edit", "go", "search", "play", "option"}



def get_screen_size():
    try:
        user32 = ctypes.windll.user32
        screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        return screensize
    except Exception:
        print("Warning: Could not get screen size using ctypes.")
        return None

def sanitize_filename(name, max_length=50):
    if not name: name = "unnamed"
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = re.sub(r'\s+', '_', name).strip('_')
    return name[:max_length]


def capture_interactive_elements(output_dir=OUTPUT_DIR):
    """
    Detects likely interactive and visible UI elements primarily in the foreground window,
    skipping the taskbar, saves a screenshot of each, and prints coordinates.
    """
    print("Initializing UI Automation...")
    keyboard.wait('q')
    try:
        desktop = pywinauto.Desktop(backend="uia")
    except Exception as e:
        print(f"Error initializing pywinauto Desktop: {e}")
        return

    windows_to_process = [] 

    print("Identifying foreground window...")
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()

        if hwnd:
            
            potential_window = desktop.window(handle=hwnd)

        
            if potential_window.exists() and potential_window.is_visible():
                window_class = potential_window.class_name()
                if window_class == TASKBAR_CLASS_NAME:
                    print(f"Foreground window is the Taskbar (Class: {TASKBAR_CLASS_NAME}). Skipping.")
                else:
                    window_title = potential_window.window_text() or f"HWND_{hwnd}"
                    print(f"Processing foreground window: '{window_title}' (Class: {window_class}, HWND: {hwnd})")
                    windows_to_process.append(potential_window)
            else:
                print("Foreground window handle found, it's not visible.")

        else:
            print("Could not get foreground window handle.")

    except (AttributeError, RuntimeError, ElementNotFoundError) as e:
        print(f"Error : {e}.")
        
    except Exception as e:
        print(f"Unexpected error getting foreground window: {e}.")
        

    
    if not windows_to_process:
        try:
            top_windows = desktop.windows(visible_only=True, enabled_only=True, top_level_only=True)
            found_fallback = False
            for top_win in top_windows:
                 win_class = top_win.class_name()
                 if win_class != TASKBAR_CLASS_NAME:
                     window_title = top_win.window_text() or f"HWND_{top_win.handle}"
                     print(f"Processing top window as fallback: '{window_title}' (Class: {win_class}, HWND: {top_win.handle})")
                     windows_to_process.append(top_win)
                     found_fallback = True
                     break 
                 else:
                     print(f"   Skipping Taskbar (Class: {win_class}).")

            if not found_fallback:
                 print("No non-taskbar top-level windows found.")
                 return 

        except Exception as fallback_e:
             print(f"Error getting top-level windows: {fallback_e}.")
             return

    
    if not windows_to_process:
        print("No target window selected for processing. Exiting.")
        return

    
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output will be saved in: {os.path.abspath(output_dir)}")
    screen_size = get_screen_size()
    screen_width, screen_height = screen_size if screen_size else (None, None)

    element_counter = 0
    start_time = time.time()
    total_processed = 0
    total_skipped = 0
    saved_count = 0

    
    for window in windows_to_process:
        try:
            current_title = window.window_text() or f"HWND_{window.handle}"
            print(f"\n--- Analyzing Window: '{current_title}' ---")
            window_rect = window.rectangle()
            if not window_rect or window_rect.width() <= 1 or window_rect.height() <= 1:
                 print("   Window has invalid dimensions. Skipping.")
                 continue

            window_elements = window.descendants()
            print(f"   Found {len(window_elements)} potential elements. Filtering...")

        except (ElementNotFoundError, NoPatternInterfaceError, RuntimeError, AttributeError) as win_err:
             print(f"   Skipping window due to error accessing properties: {win_err}")
             continue
        except Exception as e:
             print(f"   Unexpected error processing window '{window.window_text()}': {e}")
             continue

        processed_in_window = 0
        skipped_in_window = 0
        saved_in_window = 0

        for element in window_elements:
            processed_in_window += 1
            total_processed += 1

            try:
                if not element.is_visible():
                    skipped_in_window += 1; continue
                rect = element.rectangle()
                if not rect or rect.width() <= 1 or rect.height() <= 1:
                    skipped_in_window += 1; continue
                if rect.left < -50 or rect.top < -50:
                    skipped_in_window += 1; continue
                
                is_interactive = False
                element_info = element.element_info
                control_type = element_info.control_type
                name = (element_info.name or "").lower()
                auto_id = (element_info.automation_id or "").lower()
                class_name = (element_info.class_name or "").lower()

                if control_type in INTERACTIVE_TYPES:
                    is_interactive = True
                else:
                    element_text = f"{name} {auto_id} {class_name}"
                    for keyword in INTERACTIVE_KEYWORDS:
                        if keyword in element_text:
                             if keyword == "icon" and not re.search(r'\bicon\b', element_text): continue
                             is_interactive = True; break

                if not is_interactive:
                    skipped_in_window += 1; continue

                # --- Capture ---
                coords = (rect.left, rect.top, rect.right, rect.bottom)
                try:
                    bbox = tuple(map(int, coords))
                    screenshot = ImageGrab.grab(bbox=bbox, include_layered_windows=False, all_screens=True)
                except (ValueError, OSError) as img_err:
                    skipped_in_window += 1; continue
                except Exception as img_err:
                    skipped_in_window += 1; continue

                
                element_counter += 1; saved_in_window += 1
                base_filename = f"{element_counter:04d}_{control_type}_{sanitize_filename(element_info.name)}"
                if element_info.automation_id:
                     base_filename += f"_id_{sanitize_filename(element_info.automation_id)}"
                save_path = os.path.join(output_dir, f"{base_filename}.png")
                try:
                    screenshot.save(save_path)
                except Exception as save_err:
                    print(f"    Warning: Could not save screenshot {save_path}: {save_err}")
                    skipped_in_window += 1 

            except (ElementNotFoundError, NoPatternInterfaceError, AttributeError, RuntimeError, ValueError) as el_err:
                skipped_in_window += 1; continue
            except Exception as e:
                skipped_in_window += 1; continue
        

        total_skipped += skipped_in_window
        saved_count += saved_in_window
        filtered_count = processed_in_window - saved_in_window 
        print(f"   Finished window. Found interactive: {saved_in_window}, Skipped/Filtered: {filtered_count}")
    


    end_time = time.time()
    duration = end_time - start_time
    print("\n--- Scan Complete ---")
    print(f"Processed elements in foreground/top window(s): {total_processed}")
    print(f"Saved screenshots for potentially interactive elements: {saved_count}")
    print(f"Skipped non-interactive/invisible/error elements: {total_processed - saved_count}")
    print(f"Duration: {duration:.2f} seconds")
    print(f"Screenshots saved in: {os.path.abspath(output_dir)}")


if __name__ == "__main__":
    capture_interactive_elements()