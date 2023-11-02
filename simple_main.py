import asyncio
import tkinter as tk
import random
from collections import defaultdict
from fake_useragent import UserAgent
from playwright.async_api import async_playwright, Error, Page
from typing import Literal, List

# Constants
BUTTON_COLOURS = {"bg": "#aaaaaa", "activebackground": "#aaaaaa", "activeforeground": "#52487e"}
DomainLiteral = Literal[
    "https://www.safemlo.org/",
    "https://www.passcarebrokerexam.com/",
    "https://www.passcaresalespersonexam.com/",
]

urls: List[DomainLiteral] = [
    "https://www.safemlo.org/",
    "https://www.passcarebrokerexam.com/",
    "https://www.passcaresalespersonexam.com/",
]

async def visit_website(page, domain, user_id):
    try:
        await page.goto(domain)
        await page.wait_for_selector(".blue_btn")
        start_btn = await page.query_selector(".blue_btn")
        if start_btn:
            await start_btn.click()
            await page.wait_for_selector("button[name=OK]")
            await page.click("button[name=OK]")
            await page.wait_for_timeout(180)
    except Error as e:
        print(f"User {user_id} error: {e}")
    except Exception as e:
        print(f"User {user_id} exception: {e}")


async def main_task(view, domain, user_data, semaphore):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        user_id = view + 1
        async with semaphore:
            await visit_website(page, domain, user_id)
        await browser.close()
        user_data[user_id] = "Done"


class SimpleMain(tk.Frame):
    def __init__(self, root: tk.Tk) -> None:
        super().__init__(root)
        self.selected_domain = None
        self.root = root
        self.root.title("Visitor")

        self.views = 0
        self.user_data = defaultdict(dict)
        self.ended = 0
        self.error = 0
        self.stated = 0
        self.running = tk.BooleanVar(value=False)
        self.running_tasks = []
        # self.stop_event = threading.Event()

        self.start_stop_button = tk.Button(
            self, text="Start", width=15,
            background=BUTTON_COLOURS['activebackground'],
            foreground=BUTTON_COLOURS['activeforeground'],
            state="normal", command=self.start_stop_session
        )
        self.log_text = tk.Text(self, height=20, width=60)
        self.log_text.grid(row=1, column=0, columnspan=4)

        self.start_stop_button.grid(row=4, column=1)

        self.log_started_label = tk.Label(self, text="Ongoing \n Sessions")
        self.log_started_label.grid(row=2, column=0)
        self.log_started = tk.Text(self, height=3, width=20)
        self.log_started.grid(row=3, column=0)

        # self.log_errored_label = tk.Label(self, text="Paused \n Due to Error")
        # self.log_errored_label.grid(row=2, column=3)
        # self.log_errored = tk.Text(self, height=3, width=20)
        # self.log_errored.grid(row=3, column=3)

        self.log_exited_label = tk.Label(self, text="Finished \n Sessions")
        self.log_exited_label.grid(row=2, column=1)
        self.log_exited = tk.Text(self, height=3, width=20)
        self.log_exited.grid(row=3, column=1)

        self.input_number = 0
        self.num_var = tk.StringVar()
        self.num_entry = tk.Entry(self, textvariable=self.num_var)
        self.num_entry.grid(row=4, column=0)
        self.num_entry.bind('<Return>', self.save_entry)

        self.log_total_label = tk.Label(self, text="Total \n Counts")
        self.log_total_label.grid(row=2, column=3)
        self.log_total = tk.Text(self, height=4, width=24)
        self.log_total.grid(row=3, column=3)

        self.domain_var = tk.StringVar()
        self.domain_var.set(urls[0])
        self.stop_yes = False
        self.domain_radio_buttons = []

        for i, domain in enumerate(urls):
            radiobutton = tk.Radiobutton(self, text=domain, variable=self.domain_var, value=domain)
            radiobutton.grid(row=5 + i, column=0, sticky="w")
            self.domain_radio_buttons.append(radiobutton)

    async def run_tasks(self, domain, num_tasks):
        semaphore = asyncio.Semaphore(num_tasks)
        tasks = [main_task(i, domain, self.user_data, semaphore) for i in range(num_tasks)]
        await asyncio.gather(*tasks)

    def start_tasks(self):
        self.views = int(self.num_var.get())
        self.log_text.delete('1.0', tk.END)
        self.run_tasks("https://www.example.com/", self.views)
        self.root.after(0, self.show_result)

    def show_result(self):
        self.log_text.insert(tk.END, f"Tasks completed: {len(self.user_data)}\n")
        for user_id, status in self.user_data.items():
            self.log_text.insert(tk.END, f"User {user_id}: {status}\n")


    def append_to_log(self, text, message_type='info'):
        self.log_text.insert(tk.END, text + "\n", message_type)
        self.log_text.see(tk.END)

    def append_to_started_log(self, text, message_type='info'):
        self.log_started.insert(tk.END, f"User {text} started\n ")
        self.log_started.see(tk.END)

    def append_to_exited_log(self, text, message_type='info'):
        self.log_exited.insert(tk.END, f"User {text} exited \n")
        self.log_exited.see(tk.END)

    # def append_to_error_log(self, text, message_type='info'):
    #     self.log_errored.insert(tk.END, f"User {text} failed \n")
    #     self.log_errored.see(tk.END)

    def append_to_total_log(self):
        self.log_total.delete('1.0', tk.END)
        self.log_total.insert(tk.END,
                              f"Total {self.views} user created\n"
                              f"Total {self.ended} user exited\n"
                              f"Total {self.error} user failed")
        self.log_total.see(tk.END)

    def log_print(self, *args, message_type='info'):
        log_message = " ".join(map(str, args))
        print(log_message)
        self.append_to_log(log_message, message_type)

    def log_to_started(self, *args, message_type='info'):
        log_message = " ".join(map(str, args))
        self.append_to_started_log(log_message)

    def log_to_ended_view(self, *args, message_type='info'):
        log_message = " ".join(map(str, args))
        self.append_to_exited_log(log_message)

    def log_to_error_view(self, *args, message_type='info'):
        log_message = " ".join(map(str, args))
        # self.append_to_error_log(log_message)

    def log_to_total_view(self, *args, message_type='info'):
        log_message = " ".join(map(str, args))
        self.append_to_total_log()

    def check_input(self):
        if self.domain_var.get() and not self.running.get():
            self.start_stop_button.config(state="normal")
        else:
            self.start_stop_button.config(state="disabled")

    def save_entry(self, *args):
        try:
            self.input_number = int(self.num_var.get())
            self.log_print(f'Adding {self.input_number} views to \n {self.selected_domain}')
        except ValueError:
            self.input_number = 0

    def reset_views(self):
        self.views = 0
        self.user_data = {}
        self.ended = 0
        self.error = 0
        self.stated = 0

    def check_input_value(self):
        if not self.input_number or self.input_number <= 0:
            self.root.after(0, lambda: messagebox.showerror("Error", message="Input should be greater than 0"))
            self.reset_views()  # Set all your counts back to 0.
            self.start_stop_button.config(text="Start", state="normal")
            self.running.set(False)

    def start_stop_session(self):
        if not self.running.get():
            self.reset_views()
            self.selected_domain = self.domain_var.get()
            self.input_number = self.get_input_number()
            self.check_input_value()
            self.stop_event.clear()

            def start_main_task():
                task_manager = TaskManager(self)
                asyncio.run(task_manager.main_task())
                self.start_stop_button.config(text="Start", state="normal")
                self.running.set(False)
            self.log_print("Starting")
            threading.Thread(target=start_main_task, daemon=True).start()
            self.start_stop_button.config(text="Stop", state="normal")
            self.running.set(True)
        else:
            self.stop_event.set()
            self.start_stop_button.config(text="Start", state="normal")
            self.clear_log()
            self.running.set(False)
            self.check_input()

    def get_input_number(self):
        temp = self.input_number
        try:
            temp = int(self.num_var.get())
        except ValueError:
            temp = 0
        return temp

    def get_proxies(self):
        try:
            with open(PROXY_FILE_PATH, 'r') as file:
                proxies = file.read().splitlines()
            return proxies
        except Exception as e:
            self.log_print(f"Error loading proxies from file: {e}")
            return

    def clear_log(self):
        self.log_text.delete('1.0', tk.END)
        self.log_started.delete('1.0', tk.END)
        self.log_exited.delete('1.0', tk.END)
        # self.log_errored.delete('1.0', tk.END)
        self.log_total.delete('1.0', tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = SimpleMain(root)
    app.mainloop()
