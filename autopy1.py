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
INTERACTIVE_TYPES = {
    "Button", "CheckBox", "RadioButton", "MenuItem", "ListItem",
    "Hyperlink", "TabItem", "ComboBox", "Spinner", "SplitButton",
    "TreeItem", "Edit" 
}
INTERACTIVE_KEYWORDS = {"button", "icon", "click", "link", "select", "menu", "tab", "choose", "add", "remove", "edit", "go", "search", "play", "option"}

def get_screen_size():
    """Gets the primary screen resolution using ctypes."""
    try:
        user32 = ctypes.windll.user32
        screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        return screensize
    except Exception:
        print("Warning: Could not get screen size using ctypes.")
        return None

def sanitize_filename(name, max_length=50):
    """Removes invalid characters and truncates a string for use as a filename."""
    if not name: name = "unnamed"
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = re.sub(r'\s+', '_', name).strip('_')
    return name[:max_length]

def capture_interactive_elements(output_dir=OUTPUT_DIR):
    """
    Detects likely interactive and visible UI elements primarily in the foreground window,
    saves a screenshot of each, and prints coordinates.
    """
    print("Initializing UI Automation...")
    keyboard.wait('q')
    try:
        desktop = pywinauto.Desktop(backend="uia")
    except Exception as e:
        print(f"Error : {e}")
        return

    
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()

        if not hwnd:
            print("Nothing to capture.")
            return

        
        foreground_window = desktop.window(handle=hwnd)

        
        if not foreground_window.exists() or not foreground_window.is_visible():
            print("Foreground window handle found, but couldn't wrap or it's not visible.")

        window_title = foreground_window.window_text() or f"HWND_{hwnd}"
        print(f"Processing foreground window: '{window_title}' (HWND: {hwnd})")
        windows_to_process = [foreground_window] 

    except (RuntimeError, ElementNotFoundError, AttributeError) as e:
        try:
            top_windows = desktop.windows(visible_only=True, enabled_only=True, top_level_only=True)
            if not top_windows:
                print("No visible top-level windows found.")
                return
            foreground_window = top_windows[0]
            window_title = foreground_window.window_text()
            print(f"Processing likely top window as fallback: '{window_title}'")
            windows_to_process = [foreground_window]
        except Exception as fallback_e:
             print(f"Error : {fallback_e}.")
             return
    except Exception as e:
        print(f"error: {e}.")
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
            print(f"\n--- Analyzing Window: '{window.window_text()}' ---")
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
                    skipped_in_window += 1
                    continue

                
                rect = element.rectangle()
                if not rect or rect.width() <= 1 or rect.height() <= 1:
                    skipped_in_window += 1
                    continue 

               
                if rect.left < -50 or rect.top < -50:
                    skipped_in_window += 1
                    continue
                
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
                            
                            if keyword == "icon" and not re.search(r'\bicon\b', element_text):
                                continue
                            is_interactive = True
                            break

                if not is_interactive:
                    skipped_in_window += 1
                    continue


                coords = (rect.left, rect.top, rect.right, rect.bottom)
                try:
                    bbox = tuple(map(int, coords))
                    screenshot = ImageGrab.grab(bbox=bbox, include_layered_windows=False, all_screens=True)
                except (ValueError, OSError) as img_err: 
                    skipped_in_window += 1
                    continue
                except Exception as img_err:

                    skipped_in_window += 1
                    continue

                
                element_counter += 1
                saved_in_window += 1
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
                
                skipped_in_window += 1
                continue
            except Exception as e:
                
                skipped_in_window += 1
                continue

        total_skipped += skipped_in_window
        saved_count += saved_in_window
        print(f"   Finished window. Found interactive: {saved_in_window}, Skipped/Filtered: {skipped_in_window + (processed_in_window - skipped_in_window - saved_in_window)}")

    end_time = time.time()
    duration = end_time - start_time
    print("\n--- Scan Complete ---")
    print(f"Processed elements in foreground/top window(s): {total_processed}")
    print(f"Saved screenshots for potentially interactive elements: {saved_count}")
    print(f"Skipped non-interactive/invisible/error elements: {total_skipped}")
    print(f"Duration: {duration:.2f} seconds")
    print(f"Screenshots saved in: {os.path.abspath(output_dir)}")



if __name__ == "__main__":
    capture_interactive_elements()