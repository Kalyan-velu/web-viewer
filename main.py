import asyncio
import itertools
import json
import random
import tkinter as tk
import time
import threading
from collections import defaultdict
from tkinter import messagebox
from typing import Literal, List
from fake_useragent import UserAgent
from playwright.async_api import Error, Page, async_playwright, Browser

# Constants
MAX_FILE_PATH_DISPLAY_LENGTH = 100
GREY = "#aaaaaa"
BUTTON_COLOURS = {"bg": GREY, "activebackground": GREY, "activeforeground": "#52487e"}
PROXY_FILE_PATH = 'proxies.txt'

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

useragent = UserAgent()


async def track_tasks(tasks, start_times):
    while True:
        for i, task in enumerate(tasks):
            if task.done():
                tasks.remove(task)
                end_time = time.time()
                start_time = start_times.pop(task)
                elapsed_time = end_time - start_time
        if not tasks:
            break
        await asyncio.sleep(1)


# Asynchronous Helper Function
async def async_retry(coroutine_func, *args, retries=2):
    """
    Retry an async function a specified number of times.

    :param coroutine_func: The async function to be retried.
    :type coroutine_func: Callable[..., Awaitable]
    :param args: The arguments to be passed to the async function.
    :type args: Any
    :param retries: The number of times to retry the async function. Default is 2.
    :type retries: int
    :return: The result of the successful execution of the async function.
    :rtype: Any
    :raises: Exception - If all retries fail.
    """
    for i in range(retries):
        try:
            return await coroutine_func(*args)  # call the function here
        except Exception as ex:
            print(f"Attempt {i + 1} failed with error: {ex}")
            if i == retries - 1:
                raise


async def setup_browser(browser_chosen, user_agent_chosen, server, proxy_parts):
    await asyncio.sleep(1)
    # Create browser and context objects
    browser = await browser_chosen.launch(headless=True, proxy={"server": server})
    custom_headers = {
        'User-Agent': user_agent_chosen,
        'Accept-Language': 'en-US,en;q=0.5'
    }
    if len(proxy_parts) >= 4:
        username = proxy_parts[2]
        password = proxy_parts[3]
        context = await browser.new_context(
            proxy={
                "server": server,
                "username": username,
                "password": password
            },
            locale='en-US',
        )
    else:
        context = await browser.new_context(
            proxy={
                "server": server
            },
            locale='en-US',
        )
    page = await context.new_page()
    await page.set_extra_http_headers(custom_headers)
    await page.set_viewport_size({"width": 1600, "height": 1200})
    await page.goto('https://ipinfo.io/json', wait_until="domcontentloaded")
    await page.reload(wait_until='domcontentloaded')
    await asyncio.sleep(1)
    return browser, context, page, server


class TaskManager:
    concurrent_task_limit = 2

    def __init__(self, main_self):
        self.main = main_self
        self.user_data = main_self.user_data
        self.semaphore = asyncio.Semaphore(self.concurrent_task_limit)
        self.stop_event = threading.Event()
        self.tasks_completed_event = asyncio.Event()
        self.domain = self.main.selected_domain
        self.retries = 0
        self.proxies = self.main.get_proxies()
        self.proxy_cycle = itertools.cycle(self.proxies)

    def log_proxy_error(self, server, error_message, user_id=None):
        log_message = f"Error while using proxy: {server}:{error_message}"
        if user_id is not None:
            log_message = f"User {user_id}: {log_message}"
        self.main.log_print(log_message)

    async def main_task(self, start_times=None):
        if start_times is None:
            start_times = defaultdict(float)
        try:

            if not self.proxies:
                raise FileNotFoundError("Proxy list is empty.")
            async with async_playwright() as playwright:
                tasks = []

                for view in range(self.main.input_number):
                    async with self.semaphore:
                        self.retries = 0
                        await asyncio.sleep(1)
                        if self.main.stop_event.is_set():
                            break
                        self.main.views += 1
                        user_id = view + 1
                        self.retries += 1
                        self.user_data[user_id] = {"start_time": None, "retries": self.retries, "last_error": None,
                                                   "end_time": None, "task": None,
                                                   "ip": None}
                        self.main.log_print(f"User {user_id} is being assigned")
                        self.main.log_to_total_view()
                        task = asyncio.create_task(
                            self.browser_manager(playwright, user_id, self.proxies)
                        )
                        start_times[task] = time.time()
                        await asyncio.sleep(1)
                        tasks.append(task)
                        await asyncio.sleep(random.uniform(10, 20))
                        if self.main.stop_event.is_set():
                            break
                monitor = asyncio.create_task(track_tasks(tasks, start_times))
                await asyncio.gather(monitor)
                self.tasks_completed_event.set()  # Signal that all tasks are completed
                self.main.root.after(0, lambda: messagebox.showinfo("Info", message="Task Finished"))
        except Error as e:
            self.main.root.after(0, lambda: messagebox.showwarning("Warning", message=f"Something went wrong {e}"))
            return
        except Exception as ex:
            self.main.root.after(0, lambda: messagebox.showerror("Error", message=f"Something went wrong"))
            return

    async def browser_manager(self, playwright, user_id, proxies):
        while not self.main.stop_event.is_set() and self.main.stated < self.main.input_number:
            await asyncio.sleep(1)
            if self.main.stop_event.is_set():
                self.main.log_print(f"User {user_id} task stopped due to the Stop button press.")
                break
            if self.user_data[user_id].get("end_time") is not None:
                return
            browser_instance = await self.browser_setup(playwright, user_id, proxies)
            if browser_instance is None:
                self.main.stated += 1
                continue
            browser, context, page, server = browser_instance
            try:
                await asyncio.wait_for(self.crawl_page(page, user_id, server), timeout=250)
            except Error as e:
                self.main.log_print(f"user {user_id} : {e}")
                break
            except asyncio.TimeoutError:
                self.main.log_print(f"Timeout for user {user_id}, retrying...")
                break
            except Exception as e:
                self.main.log_print(f"Exceptional Error while crawling {e}")
                break
            finally:
                # Ensure context is closed if it is not None
                if context:
                    await context.close()
                    self.main.log_print(f"User {user_id} context closed.")
                # Ensure browser is closed, even if an exception occurs
                await browser.close()
                self.main.log_print(f"User {user_id} browser closed.")

    async def browser_setup(self, playwright, user_id, proxies):
        browser_and_user_agent_pairs = [(playwright.firefox, useragent.firefox),
                                        (playwright.chromium, useragent.chrome)]

        browser_chosen, user_agent_chosen = random.choice(browser_and_user_agent_pairs)

        for _ in range(3):  # Retry a maximum of 3 times
            await asyncio.sleep(1)
            if self.main.stop_event.is_set() or self.retries >= 3:
                return
            if self.user_data[user_id].get("end_time") is not None:
                return
            proxy_server = next(self.proxy_cycle)  # Get the next proxy in the circular fashion
            proxy_parts = proxy_server.strip().split(":")
            server = proxy_parts[0] + ":" + proxy_parts[1]
            coroutine_func = setup_browser
            try:
                self.main.log_print(f"User {user_id} using proxy: {proxy_parts[0]}.")
                return await async_retry(coroutine_func, browser_chosen, user_agent_chosen, server, proxy_parts)
            except Exception as e:
                self.retries += 1
                self.log_proxy_error(server, e, user_id)
                if self.retries >= 3:
                    self.main.error += 1
                    self.main.log_to_total_view()
                    return

    async def crawl_page(self, page: Page, user_id, ip_used):
        while not self.main.stop_event.is_set() and self.main.stated < self.main.input_number:
            await asyncio.sleep(1)
            if self.user_data[user_id].get("end_time") is not None:
                return
            if self.main.stated >= self.main.input_number:
                return
            if self.retries >= 3:
                return
            try:

                self.main.stated += 1
                self.main.log_to_started(user_id)

                self.main.log_to_total_view()
                self.main.log_print(f' User {user_id} entered ({ip_used})')
                await page.goto(self.main.selected_domain, wait_until="networkidle")
                await page.wait_for_load_state("networkidle")
                # await page.screenshot(full_page=True, path=f"homepage_by_{user_id}.png")
                await page.wait_for_selector(".blue_btn")
                start_btn = await page.query_selector(".blue_btn")
                if start_btn is not None:
                    await start_btn.click()
                else:
                    self.main.log_print('Start button not found')
                    return
                await asyncio.sleep(1)
                await page.get_by_role("button", name="OK").click()
                await page.wait_for_url('**/payment', wait_until='networkidle')
                await page.wait_for_load_state('networkidle')
                timeout = self.main.wait_time
                print(timeout)
                await asyncio.sleep(1)
                if self.main.stop_event.is_set():
                    self.main.log_print(f"User {user_id} task stopped due to Stop button press.")
                    return
                await page.wait_for_timeout(timeout)
                await asyncio.sleep(1)
                if self.main.stop_event.is_set():
                    self.main.log_print(f"User {user_id} task stopped due to Stop button press.")
                    return
                end_time = time.time()
                self.user_data[user_id]["end_time"] = end_time
                self.main.ended += 1
                self.main.log_to_ended_view(user_id)
                self.main.log_to_total_view()
                self.retries = 0
            except Error as e:
                self.main.log_print(f"user {user_id}: Playwright error while crawling,{e}")
                self.retries += 1
                if self.retries >= 3:
                    self.main.error += 1

            except Exception as e:
                self.main.log_print(f"user {user_id}: Exceptional Error while crawling {e}")
                return

    def stop(self):
        """
        Stops the execution of the task manager.
        :return: None
        """
        self.stop_event.set()


class Main(tk.Frame):
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
        self.stop_event = threading.Event()

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

        self.wait_time_label = tk.Label(self, text="waiting \n time(ms)")
        self.wait_time_label.grid(row=4, column=2)
        self.wait_time = 0
        self.wait_time_var = tk.StringVar()
        self.wait_time_var.set(str(self.wait_time))  # Initialize with default value
        self.wait_time_entry = tk.Entry(self, textvariable=self.wait_time_var)
        self.wait_time_entry.grid(row=5, column=2)
        self.wait_time_entry.bind('<Return>', self.save_wait_time_entry)

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

    def save_wait_time_entry(self, *args):
        try:
            self.wait_time = int(self.wait_time_var.get())
            self.log_print(f'Wait time set to {self.wait_time} ms')
        except ValueError:
            self.log_print("Invalid input for wait time")
            self.wait_time = 0  # Default value (if invalid input)

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

    def check_wait_time(self):
        if not self.wait_time or self.wait_time <= 0:
            self.root.after(0, lambda: messagebox.showerror("Error", message="waiting time should be greater than 0"))
            self.reset_views()  # Set all your counts back to 0.
            self.start_stop_button.config(text="Start", state="normal")
            self.running.set(False)

    def start_stop_session(self):
        if not self.running.get():
            self.reset_views()
            self.selected_domain = self.domain_var.get()
            self.input_number = self.get_input_number()
            self.wait_time = self.get_waiting_time()
            self.check_input_value()
            self.check_wait_time()
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

    def get_waiting_time(self):
        temp = self.wait_time
        try:
            temp = int(self.wait_time_var.get())
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


def run_tkinter():
    root = tk.Tk()
    Main(root).pack()
    root.mainloop()


if __name__ == "__main__":
    run_tkinter()