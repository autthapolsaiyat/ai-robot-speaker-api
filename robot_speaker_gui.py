#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import requests
import time
import webbrowser
from threading import Thread

API_URL = "http://192.168.1.59:4187"

class RobotSpeakerApp:
    def __init__(self, root):
        self.root = root
        root.title("AI Robot Speaker - Desktop")
        root.geometry("900x700")
        root.configure(bg='#f0f0f0')
        
        # Header
        header = tk.Frame(root, bg='#667eea', height=60)
        header.pack(fill='x')
        title = tk.Label(header, text="AI Robot Speaker API", 
                        font=('Arial', 20, 'bold'), bg='#667eea', fg='white')
        title.pack(pady=15)
        
        # Main frame
        main = tk.Frame(root, bg='#f0f0f0')
        main.pack(padx=20, pady=20, fill='both', expand=True)
        
        # Text input
        tk.Label(main, text="Text to Speak:", font=('Arial', 12, 'bold'), bg='#f0f0f0').pack(anchor='w', pady=(0,5))
        self.text_input = scrolledtext.ScrolledText(main, height=8, font=('Arial', 11), wrap='word')
        self.text_input.pack(fill='both', expand=True, pady=(0,10))
        
        # Options frame
        opts = tk.Frame(main, bg='#f0f0f0')
        opts.pack(fill='x', pady=10)
        
        # Language
        tk.Label(opts, text="Language:", font=('Arial', 10, 'bold'), bg='#f0f0f0').grid(row=0, column=0, sticky='w', padx=(0,10))
        self.lang_var = tk.StringVar(value="en")
        tk.Radiobutton(opts, text="English", variable=self.lang_var, value="en", bg='#f0f0f0').grid(row=0, column=1)
        tk.Radiobutton(opts, text="Thai", variable=self.lang_var, value="th", bg='#f0f0f0').grid(row=0, column=2)
        
        # Voice
        tk.Label(opts, text="Voice:", font=('Arial', 10, 'bold'), bg='#f0f0f0').grid(row=1, column=0, sticky='w', padx=(0,10), pady=(10,0))
        self.voice_var = tk.StringVar(value="default")
        voices = ttk.Combobox(opts, textvariable=self.voice_var, state='readonly', width=20)
        voices['values'] = ('default', 'thai_male', 'thai_female')
        voices.grid(row=1, column=1, columnspan=2, sticky='w', pady=(10,0))
        
        # Buttons frame
        btn_frame = tk.Frame(main, bg='#f0f0f0')
        btn_frame.pack(pady=15)
        
        self.gen_btn = tk.Button(btn_frame, text="Generate Video", command=self.generate,
                                 bg='#667eea', fg='white', font=('Arial', 12, 'bold'),
                                 padx=20, pady=10, relief='flat', cursor='hand2')
        self.gen_btn.pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="Check Server", command=self.check_health,
                 bg='#6c757d', fg='white', font=('Arial', 12, 'bold'),
                 padx=20, pady=10, relief='flat', cursor='hand2').pack(side='left', padx=5)
        
        # Status frame
        status_frame = tk.Frame(main, bg='white', relief='solid', borderwidth=1)
        status_frame.pack(fill='both', expand=True, pady=(10,0))
        
        tk.Label(status_frame, text="Status", font=('Arial', 11, 'bold'), bg='white').pack(anchor='w', padx=10, pady=(10,5))
        
        self.status_text = scrolledtext.ScrolledText(status_frame, height=6, font=('Courier', 9), 
                                                     state='disabled', bg='#f8f9fa')
        self.status_text.pack(fill='both', expand=True, padx=10, pady=(0,10))
        
        self.progress = ttk.Progressbar(status_frame, mode='indeterminate')
        self.progress.pack(fill='x', padx=10, pady=(0,10))
        
        self.job_id = None
        self.log("Ready. Server: " + API_URL)
        
    def log(self, msg):
        self.status_text.config(state='normal')
        self.status_text.insert('end', f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.status_text.see('end')
        self.status_text.config(state='disabled')
        
    def check_health(self):
        try:
            resp = requests.get(f"{API_URL}/health", timeout=5)
            data = resp.json()
            cuda = "Yes" if data['checks'].get('cuda_available') else "No"
            self.log(f"Server OK! CUDA: {cuda}, Disk free: {data['checks']['disk_free_gb']}GB")
            messagebox.showinfo("Health Check", f"Server is healthy!\nCUDA: {cuda}")
        except Exception as e:
            self.log(f"ERROR: Cannot connect - {e}")
            messagebox.showerror("Error", f"Cannot connect to server:\n{e}")
    
    def generate(self):
        text = self.text_input.get('1.0', 'end-1c').strip()
        if not text:
            messagebox.showerror("Error", "Please enter text")
            return
        
        self.gen_btn.config(state='disabled')
        self.progress.start()
        Thread(target=self._generate_thread, args=(text,), daemon=True).start()
    
    def _generate_thread(self, text):
        try:
            self.log(f"Submitting job...")
            
            resp = requests.post(f"{API_URL}/api/v1/speak", json={
                "text": text,
                "lang": self.lang_var.get(),
                "voice": self.voice_var.get(),
                "mode": "robot_only"
            }, timeout=10)
            
            self.job_id = resp.json()['job_id']
            self.log(f"Job created: {self.job_id}")
            
            # Poll status
            while True:
                time.sleep(2)
                status_resp = requests.get(f"{API_URL}/api/v1/jobs/{self.job_id}", timeout=5)
                status = status_resp.json()
                
                self.log(f"Status: {status['status']} ({status['progress']}%)")
                
                if status['status'] == 'completed':
                    self.progress.stop()
                    self.gen_btn.config(state='normal')
                    video_url = f"{API_URL}/api/v1/jobs/{self.job_id}/result"
                    self.log(f"SUCCESS! Video ready at: {video_url}")
                    
                    result = messagebox.askyesno("Success", 
                        f"Video is ready!\n\nJob ID: {self.job_id}\n\nOpen video in browser?")
                    if result:
                        webbrowser.open(video_url)
                    break
                    
                elif status['status'] == 'failed':
                    self.progress.stop()
                    self.gen_btn.config(state='normal')
                    error = status.get('error', 'Unknown error')
                    self.log(f"FAILED: {error}")
                    messagebox.showerror("Error", f"Job failed:\n{error}")
                    break
                    
        except Exception as e:
            self.progress.stop()
            self.gen_btn.config(state='normal')
            self.log(f"ERROR: {e}")
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = RobotSpeakerApp(root)
    root.mainloop()
