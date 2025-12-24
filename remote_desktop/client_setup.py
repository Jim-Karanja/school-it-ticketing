"""
Remote Desktop Client Setup Tool
Simplified client for end users to enable remote desktop sessions
"""
import tkinter as tk
from tkinter import messagebox, ttk
import subprocess
import sys
import os
import webbrowser
from threading import Thread
import time

class RemoteDesktopClientSetup:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("School IT Remote Desktop Client")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        # Center the window
        self.root.eval('tk::PlaceWindow . center')
        
        self.setup_ui()
        
    def setup_ui(self):
        # Title
        title_frame = tk.Frame(self.root, bg="#007bff", height=80)
        title_frame.pack(fill="x")
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame, 
            text="🎓 School IT Remote Desktop", 
            font=("Arial", 16, "bold"),
            bg="#007bff",
            fg="white"
        )
        title_label.pack(expand=True)
        
        # Main content
        main_frame = tk.Frame(self.root, padx=30, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        # Instructions
        instructions = tk.Label(
            main_frame,
            text="This tool allows IT staff to remotely help with your computer issues.\n"
                 "Only use this when instructed by IT support staff.",
            font=("Arial", 11),
            justify="left",
            wraplength=400
        )
        instructions.pack(pady=(0, 20))
        
        # Status section
        status_frame = tk.LabelFrame(main_frame, text="Connection Status", font=("Arial", 10, "bold"))
        status_frame.pack(fill="x", pady=(0, 20))
        
        self.status_label = tk.Label(
            status_frame,
            text="Ready to connect",
            font=("Arial", 10),
            fg="green"
        )
        self.status_label.pack(pady=10)
        
        # Session ID input
        id_frame = tk.LabelFrame(main_frame, text="Session Information", font=("Arial", 10, "bold"))
        id_frame.pack(fill="x", pady=(0, 20))
        
        tk.Label(id_frame, text="Session ID (provided by IT staff):", font=("Arial", 9)).pack(anchor="w", padx=10, pady=(10, 0))
        
        self.session_id_var = tk.StringVar()
        session_id_entry = tk.Entry(
            id_frame,
            textvariable=self.session_id_var,
            font=("Arial", 11),
            width=40
        )
        session_id_entry.pack(padx=10, pady=(5, 10))
        
        tk.Label(id_frame, text="Access Token (provided by IT staff):", font=("Arial", 9)).pack(anchor="w", padx=10, pady=(0, 0))
        
        self.token_var = tk.StringVar()
        token_entry = tk.Entry(
            id_frame,
            textvariable=self.token_var,
            font=("Arial", 11),
            width=40,
            show="*"
        )
        token_entry.pack(padx=10, pady=(5, 10))
        
        # Control buttons
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(0, 10))\n        \n        connect_btn = tk.Button(\n            button_frame,\n            text="Connect to IT Support",\n            font=("Arial", 11, "bold"),\n            bg="#28a745",\n            fg="white",\n            pady=10,\n            command=self.connect_session\n        )\n        connect_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))\n        \n        disconnect_btn = tk.Button(\n            button_frame,\n            text="Disconnect",\n            font=("Arial", 11),\n            bg="#dc3545",\n            fg="white",\n            pady=10,\n            command=self.disconnect_session\n        )\n        disconnect_btn.pack(side="right", fill="x", expand=True, padx=(5, 0))\n        \n        # Help section\n        help_frame = tk.LabelFrame(main_frame, text="Need Help?", font=("Arial", 10, "bold"))\n        help_frame.pack(fill="x")\n        \n        help_text = tk.Label(\n            help_frame,\n            text="• Only connect when asked by IT support staff\\n"\n                 "• Keep this window open during the session\\n"\n                 "• IT staff can see and control your screen\\n"\n                 "• You can disconnect at any time",\n            font=("Arial", 9),\n            justify="left"\n        )\n        help_text.pack(padx=10, pady=10, anchor="w")\n        \n        # Contact info\n        contact_btn = tk.Button(\n            help_frame,\n            text="Contact IT Support: (555) 123-4567",\n            font=("Arial", 9, "underline"),\n            bg="white",\n            fg="#007bff",\n            relief="flat",\n            command=self.show_contact_info\n        )\n        contact_btn.pack(pady=(0, 10))\n        \n        # Progress bar (initially hidden)\n        self.progress = ttk.Progressbar(\n            main_frame,\n            mode='indeterminate'\n        )\n        \n    def connect_session(self):\n        session_id = self.session_id_var.get().strip()\n        token = self.token_var.get().strip()\n        \n        if not session_id or not token:\n            messagebox.showerror(\n                "Missing Information",\n                "Please enter both Session ID and Access Token provided by IT staff."\n            )\n            return\n        \n        # Validate session ID format (basic check)\n        if len(session_id) < 10:\n            messagebox.showerror(\n                "Invalid Session ID",\n                "The Session ID appears to be invalid. Please check with IT staff."\n            )\n            return\n        \n        # Show progress\n        self.progress.pack(pady=10)\n        self.progress.start()\n        self.status_label.config(text="Connecting...", fg="orange")\n        \n        # Start connection in separate thread\n        connect_thread = Thread(target=self._connect_to_server, args=(session_id, token))\n        connect_thread.daemon = True\n        connect_thread.start()\n    \n    def _connect_to_server(self, session_id, token):\n        try:\n            # Build the client URL\n            server_url = "http://localhost:5000"  # This should be configurable\n            client_url = f"{server_url}/remote_client/{session_id}/{token}"\n            \n            # Open the web-based client\n            webbrowser.open(client_url)\n            \n            # Update UI on main thread\n            self.root.after(1000, self._connection_success)\n            \n        except Exception as e:\n            # Update UI on main thread\n            self.root.after(0, self._connection_failed, str(e))\n    \n    def _connection_success(self):\n        self.progress.stop()\n        self.progress.pack_forget()\n        self.status_label.config(text="Connected! Remote session is active in your web browser.", fg="green")\n        \n        messagebox.showinfo(\n            "Connection Successful",\n            "Remote desktop session started!\\n\\n"\n            "The remote session is now active in your web browser. "\n            "IT staff can now see and control your screen to help resolve your issue.\\n\\n"\n            "Keep this window open during the session."\n        )\n    \n    def _connection_failed(self, error_msg):\n        self.progress.stop()\n        self.progress.pack_forget()\n        self.status_label.config(text="Connection failed", fg="red")\n        \n        messagebox.showerror(\n            "Connection Failed",\n            f"Could not connect to the remote session.\\n\\n"\n            f"Error: {error_msg}\\n\\n"\n            f"Please check your Session ID and Token, or contact IT support."\n        )\n    \n    def disconnect_session(self):\n        result = messagebox.askyesno(\n            "Disconnect Session",\n            "Are you sure you want to disconnect from the remote session?\\n\\n"\n            "This will end IT support assistance."\n        )\n        \n        if result:\n            self.status_label.config(text="Disconnected", fg="red")\n            messagebox.showinfo(\n                "Disconnected",\n                "Remote desktop session has been disconnected.\\n\\n"\n                "You can close this window or start a new session if needed."\n            )\n    \n    def show_contact_info(self):\n        messagebox.showinfo(\n            "IT Support Contact",\n            "School IT Support\\n"\n            "━━━━━━━━━━━━━━━━━━━━━━\\n"\n            "📞 Phone: (555) 123-4567\\n"\n            "📧 Email: it-support@school.edu\\n"\n            "🏢 Office: Room 110\\n"\n            "🕐 Hours: Mon-Fri, 8AM-4PM\\n\\n"\n            "For urgent issues outside business hours,\\n"\n            "call the main office."\n        )\n    \n    def run(self):\n        # Handle window close\n        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)\n        self.root.mainloop()\n    \n    def on_closing(self):\n        if messagebox.askokcancel("Quit", "Do you want to quit the Remote Desktop Client?"):\n            self.root.destroy()\n\ndef main():\n    # Check if running as administrator (Windows)\n    try:\n        import ctypes\n        is_admin = ctypes.windll.shell32.IsUserAnAdmin()\n        if not is_admin:\n            messagebox.showwarning(\n                "Administrator Rights Needed",\n                "This application may need administrator rights to function properly.\\n\\n"\n                "If you experience issues, please right-click and \\'Run as Administrator\\'."\n            )\n    except:\n        pass  # Not Windows or unable to check\n    \n    # Start the application\n    app = RemoteDesktopClientSetup()\n    app.run()\n\nif __name__ == "__main__":\n    main()
