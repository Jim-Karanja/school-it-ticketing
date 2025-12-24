"""
Input Handler for Remote Desktop
Handles remote mouse and keyboard input from IT staff
"""
import pyautogui
import keyboard
import time
import logging
from threading import Lock

logger = logging.getLogger(__name__)

class InputHandler:
    def __init__(self):
        # Disable pyautogui failsafe to allow programmatic control
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.01  # Small pause between actions
        
        self.input_lock = Lock()
        self.authorized_sessions = set()  # Track authorized remote sessions
        
        # Get screen size
        self.screen_width, self.screen_height = pyautogui.size()
        
        logger.info(f"Input handler initialized. Screen size: {self.screen_width}x{self.screen_height}")
    
    def authorize_session(self, session_id):
        """Authorize a session for remote input"""
        self.authorized_sessions.add(session_id)
        logger.info(f"Session {session_id} authorized for remote input")
    
    def revoke_session(self, session_id):
        """Revoke session authorization"""
        self.authorized_sessions.discard(session_id)
        logger.info(f"Session {session_id} authorization revoked")
    
    def is_authorized(self, session_id):
        """Check if session is authorized"""
        return session_id in self.authorized_sessions
    
    def handle_mouse_move(self, session_id, x, y, screen_width, screen_height):
        """Handle mouse movement"""
        if not self.is_authorized(session_id):
            return False
            
        with self.input_lock:
            try:
                # Scale coordinates to actual screen size
                actual_x = int((x / screen_width) * self.screen_width)
                actual_y = int((y / screen_height) * self.screen_height)
                
                # Ensure coordinates are within bounds
                actual_x = max(0, min(actual_x, self.screen_width - 1))
                actual_y = max(0, min(actual_y, self.screen_height - 1))
                
                pyautogui.moveTo(actual_x, actual_y)
                return True
                
            except Exception as e:
                logger.error(f"Mouse move error: {e}")
                return False
    
    def handle_mouse_click(self, session_id, x, y, screen_width, screen_height, button='left', click_type='single'):
        """Handle mouse clicks"""
        if not self.is_authorized(session_id):
            return False
            
        with self.input_lock:
            try:
                # Scale coordinates
                actual_x = int((x / screen_width) * self.screen_width)
                actual_y = int((y / screen_height) * self.screen_height)
                
                # Ensure coordinates are within bounds
                actual_x = max(0, min(actual_x, self.screen_width - 1))
                actual_y = max(0, min(actual_y, self.screen_height - 1))
                
                if click_type == 'single':
                    pyautogui.click(actual_x, actual_y, button=button)
                elif click_type == 'double':
                    pyautogui.doubleClick(actual_x, actual_y, button=button)
                elif click_type == 'down':
                    pyautogui.mouseDown(actual_x, actual_y, button=button)
                elif click_type == 'up':
                    pyautogui.mouseUp(actual_x, actual_y, button=button)
                
                logger.debug(f"Mouse {click_type} {button} at ({actual_x}, {actual_y})")
                return True
                
            except Exception as e:
                logger.error(f"Mouse click error: {e}")
                return False
    
    def handle_mouse_scroll(self, session_id, x, y, screen_width, screen_height, delta):
        """Handle mouse scroll"""
        if not self.is_authorized(session_id):
            return False
            
        with self.input_lock:
            try:
                # Scale coordinates
                actual_x = int((x / screen_width) * self.screen_width)
                actual_y = int((y / screen_height) * self.screen_height)
                
                pyautogui.scroll(int(delta), actual_x, actual_y)
                return True
                
            except Exception as e:
                logger.error(f"Mouse scroll error: {e}")
                return False
    
    def handle_key_press(self, session_id, key, action='press'):
        """Handle keyboard input"""
        if not self.is_authorized(session_id):
            return False
            
        with self.input_lock:
            try:
                # Map special keys
                key_mapping = {
                    'Enter': 'enter',
                    'Backspace': 'backspace',
                    'Delete': 'delete',
                    'Tab': 'tab',
                    'Escape': 'esc',
                    'Space': 'space',
                    'ArrowUp': 'up',
                    'ArrowDown': 'down',
                    'ArrowLeft': 'left',
                    'ArrowRight': 'right',
                    'Home': 'home',
                    'End': 'end',
                    'PageUp': 'pageup',
                    'PageDown': 'pagedown',
                    'Insert': 'insert',
                    'F1': 'f1', 'F2': 'f2', 'F3': 'f3', 'F4': 'f4',
                    'F5': 'f5', 'F6': 'f6', 'F7': 'f7', 'F8': 'f8',
                    'F9': 'f9', 'F10': 'f10', 'F11': 'f11', 'F12': 'f12'
                }
                
                # Get the actual key to press
                actual_key = key_mapping.get(key, key.lower())
                
                if action == 'press':
                    pyautogui.press(actual_key)
                elif action == 'down':
                    pyautogui.keyDown(actual_key)
                elif action == 'up':
                    pyautogui.keyUp(actual_key)
                
                logger.debug(f"Key {action}: {actual_key}")
                return True
                
            except Exception as e:
                logger.error(f"Key press error: {e}")
                return False
    
    def handle_key_combination(self, session_id, keys):
        """Handle key combinations (like Ctrl+C)"""
        if not self.is_authorized(session_id):
            return False
            
        with self.input_lock:
            try:
                # Convert keys to pyautogui format
                converted_keys = []
                for key in keys:
                    if key.lower() == 'ctrl':
                        converted_keys.append('ctrl')
                    elif key.lower() == 'alt':
                        converted_keys.append('alt')
                    elif key.lower() == 'shift':
                        converted_keys.append('shift')
                    elif key.lower() == 'win' or key.lower() == 'cmd':
                        converted_keys.append('win')
                    else:
                        converted_keys.append(key.lower())
                
                pyautogui.hotkey(*converted_keys)
                logger.debug(f"Key combination: {' + '.join(converted_keys)}")
                return True
                
            except Exception as e:
                logger.error(f"Key combination error: {e}")
                return False
    
    def handle_text_input(self, session_id, text):
        """Handle text input"""
        if not self.is_authorized(session_id):
            return False
            
        with self.input_lock:
            try:
                pyautogui.write(text, interval=0.01)
                logger.debug(f"Text input: {text[:50]}{'...' if len(text) > 50 else ''}")
                return True
                
            except Exception as e:
                logger.error(f"Text input error: {e}")
                return False
    
    def get_mouse_position(self):
        """Get current mouse position"""
        try:
            x, y = pyautogui.position()
            return {'x': x, 'y': y}
        except Exception as e:
            logger.error(f"Get mouse position error: {e}")
            return {'x': 0, 'y': 0}
    
    def get_stats(self):
        """Get input handler statistics"""
        return {
            'screen_size': {'width': self.screen_width, 'height': self.screen_height},
            'authorized_sessions': len(self.authorized_sessions),
            'mouse_position': self.get_mouse_position()
        }

# Global input handler instance
input_handler = InputHandler()
