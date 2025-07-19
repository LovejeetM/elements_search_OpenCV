import pywinauto
from pywinauto.findwindows import ElementNotFoundError
from pywinauto.uia_defines import NoPatternInterfaceError 
from PIL import ImageGrab, Image
import os
import time
import re
import ctypes 
import keyboard

def get_screen_size():
    """Gets the primary screen resolution using ctypes."""
    try:
        user32 = ctypes.windll.user32
        screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        return screensize
    except Exception:
        print("Warning: Could not get screen size using ctypes. Falling back.")
        try:
            import pyautogui 
            return pyautogui.size()
        except ImportError:
            return None 

def sanitize_filename(name, max_length=50):
    """Removes invalid characters and truncates a string for use as a filename."""
    if not name:
        name = "unnamed"
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = re.sub(r'\s+', '_', name).strip('_')
    return name[:max_length]

def capture_visible_elements(output_dir="visible_elements_capture"):
    """
    Detects UI elements within currently visible top-level windows,
    saves a screenshot of each likely visible element, and prints coordinates.
    """
    print('press q')
    keyboard.wait('q')
    try:
        desktop = pywinauto.Desktop(backend="uia")
    except Exception as e:
        print(f"Error : {e}")
        return

    
    os.makedirs(output_dir, exist_ok=True)
    print(f" {os.path.abspath(output_dir)}")

    

    element_counter = 0
    start_time = time.time()

    try:
        
        top_windows = desktop.windows(visible_only=True, enabled_only=True, top_level_only=True)
    except Exception as e:
        print(f"Error : {e}")
        return

    print(f"Found {len(top_windows)} potentially visible top-level windows.")

    total_processed = 0
    total_skipped = 0

    for i, window in enumerate(top_windows):
        try:
            window_title = window.window_text()
            print(f"\n--- Processing Window {i+1}/{len(top_windows)}: '{window_title}' ---")
            window_rect = window.rectangle()
            
            if not window_rect or window_rect.width() <= 1 or window_rect.height() <= 1:
                print("   Skipping invalid or zero-size window.")
                continue

            
            window_elements = window.descendants()
            print(f"   Found {len(window_elements)} potential elements in this window.")

        except (ElementNotFoundError, NoPatternInterfaceError, RuntimeError, AttributeError) as win_err:
             
             print(f"   error : {win_err}")
             continue
        except Exception as e:
             print(f"   error  '{window_title}': {e}")
             continue

        processed_in_window = 0
        skipped_in_window = 0

        for element in window_elements:
            processed_in_window += 1
            total_processed += 1
            if processed_in_window % 200 == 0: 
                 print(f"      Processed {processed_in_window}/{len(window_elements)} in window '{window_title}'...")

            try:
                rect = element.rectangle()
                if not rect or rect.width() <= 1 or rect.height() <= 1:
                    skipped_in_window += 1
                    total_skipped += 1
                    continue

                
                if not element.is_visible():
                    skipped_in_window += 1
                    total_skipped += 1
                    continue

                
                if rect.left < -10 or rect.top < -10: 
                    skipped_in_window += 1
                    total_skipped += 1
                    continue
                

                
                element_info = element.element_info
                control_type = element_info.control_type
                name = element_info.name
                auto_id = element_info.automation_id

                
                coords = (rect.left, rect.top, rect.right, rect.bottom)


                try:
                    bbox = tuple(map(int, coords))
                    screenshot = ImageGrab.grab(bbox=bbox, include_layered_windows=False, all_screens=True)
                except ValueError as ve: 
                    skipped_in_window += 1
                    total_skipped += 1
                    continue
                except Exception as img_err:
                    
                    skipped_in_window += 1
                    total_skipped += 1
                    continue

                
                element_counter += 1
                clean_win_title = sanitize_filename(window_title, 20)
                base_filename = f"{element_counter:04d}_Win_{clean_win_title}_{control_type}_{sanitize_filename(name)}"
                if auto_id:
                    base_filename += f"_id_{sanitize_filename(auto_id)}"

                save_path = os.path.join(output_dir, f"{base_filename}.png")

                try:
                    screenshot.save(save_path)
                    
                except Exception as save_err:
                    print(f"    Warning: Could not save screenshot to {save_path}: {save_err}")
                    
                    skipped_in_window += 1 
                    total_skipped += 1


            except (ElementNotFoundError, NoPatternInterfaceError, AttributeError, RuntimeError, ValueError) as el_err:
                
                skipped_in_window += 1
                total_skipped += 1
                continue
            except Exception as e:
                
                skipped_in_window += 1
                total_skipped += 1
                continue

        print(f"   Finished window '{window_title}'. Saved {processed_in_window - skipped_in_window} elements, Skipped {skipped_in_window}.")


    end_time = time.time()
    duration = end_time - start_time

    print("\n--- Scan Complete ---")
    print(f"Processed {len(top_windows)} top-level windows.")
    print(f"Total elements considered across all windows: {total_processed}")
    print(f"Successfully captured screenshots for: {element_counter} elements")
    print(f"Skipped elements (filtered out or errors): {total_skipped}")
    print(f"Duration: {duration:.2f} seconds")
    print(f"Screenshots saved in: {os.path.abspath(output_dir)}")


if __name__ == "__main__":
    capture_visible_elements()