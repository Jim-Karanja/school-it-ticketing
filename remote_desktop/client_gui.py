"""
Remote Desktop Client GUI
Simple desktop application for end users to connect to remote sessions
"""
import tkinter as tk
from tkinter import messagebox, ttk
import webbrowser
from threading import Thread

class RemoteDesktopClient:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("School IT Remote Desktop Client")
        self.root.geometry("500x450")
        self.root.resizable(False, False)
        
        # Center window
        self.root.eval('tk::PlaceWindow . center')
        
        self.setup_ui()
        
    def setup_ui(self):
        # Header
        header_frame = tk.Frame(self.root, bg="#007bff", height=70)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        header_label = tk.Label(
            header_frame,
            text="🎓 School IT Remote Desktop",
            font=("Arial", 16, "bold"),
            bg="#007bff",
            fg="white"
        )
        header_label.pack(expand=True)
        
        # Main content
        main_frame = tk.Frame(self.root, padx=25, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        # Instructions
        tk.Label(
            main_frame,
            text="This tool allows IT staff to remotely access your computer to help resolve issues.\nOnly use when instructed by IT support staff.",
            font=("Arial", 11),
            justify="center",
            wraplength=450
        ).pack(pady=(0, 20))
        
        # Status
        status_frame = tk.LabelFrame(main_frame, text="Status", font=("Arial", 10, "bold"), padx=10, pady=10)
        status_frame.pack(fill="x", pady=(0, 20))
        
        self.status_var = tk.StringVar(value="Ready to connect")
        self.status_label = tk.Label(
            status_frame,
            textvariable=self.status_var,
            font=("Arial", 10),
            fg="green"
        )
        self.status_label.pack()
        
        # Connection details
        details_frame = tk.LabelFrame(main_frame, text="Connection Details", font=("Arial", 10, "bold"), padx=10, pady=10)
        details_frame.pack(fill="x", pady=(0, 20))
        
        tk.Label(details_frame, text="Session ID:", font=("Arial", 9)).pack(anchor="w")
        self.session_id_var = tk.StringVar()
        tk.Entry(
            details_frame,
            textvariable=self.session_id_var,
            font=("Arial", 11),
            width=50
        ).pack(fill="x", pady=(2, 10))
        
        tk.Label(details_frame, text="Access Token:", font=("Arial", 9)).pack(anchor="w")
        self.token_var = tk.StringVar()
        tk.Entry(
            details_frame,
            textvariable=self.token_var,
            font=("Arial", 11),
            width=50,
            show="*"
        ).pack(fill="x", pady=(2, 0))
        
        # Buttons
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=(20, 10))
        
        tk.Button(
            btn_frame,
            text="Connect",
            font=("Arial", 12, "bold"),
            bg="#28a745",
            fg="white",
            pady=8,
            command=self.connect
        ).pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        tk.Button(
            btn_frame,
            text="Disconnect",
            font=("Arial", 12),
            bg="#dc3545",
            fg="white",
            pady=8,
            command=self.disconnect
        ).pack(side="right", fill="x", expand=True, padx=(5, 0))
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        
        # Help section
        help_frame = tk.LabelFrame(main_frame, text="Important Information", font=("Arial", 10, "bold"), padx=10, pady=10)
        help_frame.pack(fill="x", pady=(10, 0))
        
        tk.Label(
            help_frame,
            text="• Only connect when instructed by IT staff\n"
                 "• IT staff can see and control your screen\n"
                 "• Keep this window open during the session\n"
                 "• You can disconnect at any time",
            font=("Arial", 9),
            justify="left"
        ).pack(anchor="w")
        
        # Contact button
        tk.Button(
            help_frame,
            text="Contact IT: (555) 123-4567",
            font=("Arial", 9, "underline"),
            bg="white",
            fg="#007bff",
            relief="flat",
            command=self.show_contact
        ).pack(pady=(10, 0))
    
    def connect(self):
        session_id = self.session_id_var.get().strip()
        token = self.token_var.get().strip()
        
        if not session_id or not token:
            messagebox.showerror(
                "Missing Information",
                "Please enter both Session ID and Access Token from IT staff."
            )
            return
        
        if len(session_id) < 10:
            messagebox.showerror(
                "Invalid Session ID",
                "Please check the Session ID with IT staff."
            )
            return
        
        # Show connecting status
        self.progress.pack(pady=10)
        self.progress.start()
        self.status_var.set("Connecting...")
        self.status_label.config(fg="orange")
        
        # Connect in background
        Thread(target=self._do_connect, args=(session_id, token), daemon=True).start()
    
    def _do_connect(self, session_id, token):
        try:
            # Build client URL
            server_url = "http://localhost:5000"
            client_url = f"{server_url}/remote_client/{session_id}/{token}"
            
            # Open browser
            webbrowser.open(client_url)
            
            # Update UI
            self.root.after(1000, self._connect_success)
            
        except Exception as e:
            self.root.after(0, self._connect_failed, str(e))
    
    def _connect_success(self):
        self.progress.stop()
        self.progress.pack_forget()
        self.status_var.set("Connected - Remote session active")
        self.status_label.config(fg="green")
        
        messagebox.showinfo(
            "Connected",
            "Remote session started in your web browser!\n\n"
            "IT staff can now help with your computer issue.\n"
            "Keep this window open during the session."
        )
    
    def _connect_failed(self, error):
        self.progress.stop()
        self.progress.pack_forget()
        self.status_var.set("Connection failed")
        self.status_label.config(fg="red")
        
        messagebox.showerror(
            "Connection Failed",
            f"Could not connect to remote session.\n\n"
            f"Please check with IT staff.\n\nError: {error}"
        )
    
    def disconnect(self):
        if messagebox.askyesno("Disconnect", "End the remote session?"):
            self.status_var.set("Disconnected")
            self.status_label.config(fg="red")
            messagebox.showinfo("Disconnected", "Remote session ended.")
    
    def show_contact(self):
        messagebox.showinfo(
            "IT Support Contact",
            "School IT Support\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📞 Phone: (555) 123-4567\n"
            "📧 Email: it-support@school.edu\n"
            "🏢 Office: Room 110\n"
            "🕒 Hours: Mon-Fri, 8AM-4PM"
        )
    
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()
    
    def on_close(self):
        if messagebox.askokcancel("Exit", "Close Remote Desktop Client?"):
            self.root.destroy()

if __name__ == "__main__":
    app = RemoteDesktopClient()
    app.run()
