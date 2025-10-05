import tkinter as tk
from tkinter import ttk, messagebox

DAYS = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"]

class Job:
    def __init__(self, day, arrival, duration):
        self.day = day
        self.arrival = arrival
        self.duration = duration
        self.start_time = None
        self.delay = None
        self.tree_id = None  # Added to track treeview item

class SchedulerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ole's Cobbler Shop Scheduler")
        self.jobs_by_day = {day: [] for day in DAYS}
        self.setup_styles()
        self.setup_ui()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TCombobox",
                        fieldbackground="#ffffff",
                        background="#d9eaf7",
                        foreground="#000000")
        style.configure("Treeview",
                        background="#e6f2ff",
                        fieldbackground="#e6f2ff",
                        foreground="#000000",
                        rowheight=24,
                        font=('Arial', 10))
        style.map("Treeview",
                  background=[('selected', '#a3c9f1')])

    def setup_ui(self):
        self.root.configure(bg="#f9fbfd")
        self.root.geometry("700x600")

        form_frame = tk.LabelFrame(self.root, text="Add Job", bg="#f9fbfd", padx=10, pady=10, font=('Arial', 10, 'bold'))
        form_frame.pack(padx=10, pady=10, fill="x")

        tk.Label(form_frame, text="Day:", bg="#f9fbfd", font=('Arial', 10)).grid(row=0, column=0, sticky="e", pady=2)
        self.day_var = tk.StringVar(value=DAYS[0])
        ttk.Combobox(form_frame, textvariable=self.day_var, values=DAYS, state="readonly", width=20).grid(row=0, column=1, pady=2)

        tk.Label(form_frame, text="Arrival Time (min past 8:00 AM):", bg="#f9fbfd", font=('Arial', 10)).grid(row=1, column=0, sticky="e", pady=2)
        self.arrival_var = tk.DoubleVar(value=0.0)
        tk.Entry(form_frame, textvariable=self.arrival_var, width=22, bg="#ffffff").grid(row=1, column=1, pady=2)

        tk.Label(form_frame, text="Job Duration (min):", bg="#f9fbfd", font=('Arial', 10)).grid(row=2, column=0, sticky="e", pady=2)
        self.duration_var = tk.DoubleVar(value=0.0)
        tk.Entry(form_frame, textvariable=self.duration_var, width=22, bg="#ffffff").grid(row=2, column=1, pady=2)

        tk.Button(form_frame, text="Add Job", bg="#cce5ff", font=('Arial', 10, 'bold'), command=self.add_job).grid(row=3, column=0, columnspan=2, pady=6, sticky="ew")
        tk.Button(form_frame, text="Compute Delay", bg="#d4edda", font=('Arial', 10, 'bold'), command=self.compute_delay).grid(row=4, column=0, columnspan=2, pady=4, sticky="ew")
        tk.Button(form_frame, text="Clear All", bg="#f8d7da", font=('Arial', 10, 'bold'), command=self.clear_all).grid(row=5, column=0, columnspan=2, pady=4, sticky="ew")

        job_frame = tk.LabelFrame(self.root, text="Job List", bg="#f9fbfd", font=('Arial', 10, 'bold'))
        job_frame.pack(padx=10, pady=(0,10), fill="both", expand=False)

        self.tree = ttk.Treeview(job_frame, columns=("Day", "Arrival", "Duration", "Start", "Delay"), show="headings")
        for col in ("Day", "Arrival", "Duration", "Start", "Delay"):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")
        self.tree.pack(fill="both", padx=10, pady=6)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(job_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        output_frame = tk.LabelFrame(self.root, text="Average Delay Report", bg="#f9fbfd", font=('Arial', 10, 'bold'))
        output_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.output_text = tk.Text(output_frame, height=8, bg="#fff8dc", fg="#000000", font=('Courier New', 10))
        self.output_text.pack(fill="both", padx=10, pady=6)

    def add_job(self):
        try:
            day = self.day_var.get()
            arrival = float(self.arrival_var.get())
            duration = float(self.duration_var.get())
            if arrival < 0 or duration <= 0:
                raise ValueError("Negative time/duration")
        except ValueError:
            messagebox.showerror("Invalid input", "Please enter valid positive numbers for time and duration.")
            return

        job = Job(day, arrival, duration)
        self.jobs_by_day[day].append(job)

        # Store tree item ID in job object
        job.tree_id = self.tree.insert('', 'end', values=(
            day, f"{arrival:.2f}", f"{duration:.2f}", "", ""
        ))

        # Clear inputs
        self.arrival_var.set(0.0)
        self.duration_var.set(0.0)

    def compute_delay(self):
        self.output_text.delete("1.0", tk.END)
        for item in self.tree.get_children():
            self.tree.set(item, "Start", "")
            self.tree.set(item, "Delay", "")

        result = "Average Delay per Day:\n"
        result += "----------------------\n"
        for day in DAYS:
            jobs = sorted(self.jobs_by_day[day], key=lambda x: x.arrival)
            queue = []
            current_minute = 0.0
            working_job = None
            delay_total = 0.0
            count = 0
            i = 0  # index for next job to arrive

            while i < len(jobs) or queue or working_job:
                # Add all jobs that have arrived by current time
                while i < len(jobs) and jobs[i].arrival <= current_minute:
                    job = jobs[i]
                    if job.duration <= 5:
                        queue.insert(0, job)  # Short jobs to front
                    else:
                        queue.append(job)  # Long jobs to back
                    i += 1

                # Check if working job has finished
                if working_job and current_minute >= working_job.start_time + working_job.duration:
                    working_job = None

                # Start a new job if machine is free
                if working_job is None and queue:
                    working_job = queue.pop(0)
                    working_job.start_time = current_minute
                    working_job.delay = max(0, current_minute - working_job.arrival)
                    delay_total += working_job.delay
                    count += 1

                # Find next event time
                next_event = None
                
                # Next arrival (if any)
                if i < len(jobs):
                    next_event = jobs[i].arrival
                
                # Current job completion (if any)
                if working_job:
                    completion_time = working_job.start_time + working_job.duration
                    if next_event is None or completion_time < next_event:
                        next_event = completion_time
                
                if next_event is not None:
                    current_minute = next_event
                else:
                    break  # No more events

            # Calculate average delay
            avg_delay = delay_total / count if count > 0 else 0.0
            result += f"{day:<10} {avg_delay:.2f} minutes\n"

            # Update TreeView using stored tree_id
            for job in self.jobs_by_day[day]:
                if job.start_time is not None and job.delay is not None:
                    self.tree.set(job.tree_id, "Start", f"{job.start_time:.2f}")
                    self.tree.set(job.tree_id, "Delay", f"{job.delay:.2f}")

        self.output_text.insert(tk.END, result)
        
    def clear_all(self):
        # Clear job data
        for day in DAYS:
            self.jobs_by_day[day] = []
        
        # Clear treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Clear output
        self.output_text.delete("1.0", tk.END)
        
        # Reset input fields
        self.day_var.set(DAYS[0])
        self.arrival_var.set(0.0)
        self.duration_var.set(0.0)

if __name__ == "__main__":
    root = tk.Tk()
    app = SchedulerApp(root)
    root.mainloop()