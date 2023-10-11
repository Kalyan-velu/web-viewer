import asyncio
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


class TaskManager:
    """Class responsible for managing tasks.

    Args:
        main_self: The main class instance.

    Attributes:
        main: The main class instance.
        log_print: The log_print method from the main class.
        selected_domain: The selected domain from the main class.
        input_number: The input number from the main class.
        user_data: A dictionary to store user task data.
        stop_event: A threading Event used to stop the tasks.

    """

    def __init__(self, main_self):
        self.main = main_self
        self.log_print = main_self.log_print
        self.selected_domain = main_self.selected_domain
        self.input_number = main_self.input_number
        self.user_data = defaultdict(dict)
        self.stop_event = threading.Event()

    async def main_task(self):
        try:
            if not self.input_number:
                raise ValueError("Execution number should be more than 0")
            proxies = self.main.get_proxies()
            if not proxies:
                raise FileNotFoundError("Proxy list is empty.")

            async with async_playwright() as playwright:
                tasks = []
                start_times = defaultdict(float)

                for view in range(self.input_number):
                    await asyncio.sleep(1)
                    if self.main.stop_event.is_set():
                        break

                    user_id = view + 1
                    self.main.views += 1
                    proxy_server = proxies[view % len(proxies)]

                    self.user_data[user_id] = {"start_time": None, "end_time": None, "task": None, "ip": proxy_server}

                    task = asyncio.create_task(
                        self.browser_manager(playwright, self.selected_domain, proxy_server, user_id)
                    )
                    await asyncio.sleep(1)
                    self.user_data[user_id]["task"] = task
                    start_times[task] = time.time()
                    tasks.append(task)
                    self.log_print(f"\n A browser has been assigned to User {user_id}. \n The total number of created "
                                   f"browsers is now {len(tasks)}.")
                    self.main.log_to_total_view()
                    await asyncio.sleep(random.uniform(10, 30))

                    if self.main.stop_event.is_set():
                        break  # Check the stop event after adding a task

                monitor = asyncio.create_task(self.track_tasks(tasks, start_times))
                await asyncio.sleep(1)
                await asyncio.gather(monitor)
                json_data = json.dumps(self.user_data, default=str)
                with open("user_data.json", "w") as outfile:
                    outfile.write(json_data)
                self.log_print("All tasks finished!")
                self.main.root.after(0, lambda: messagebox.showinfo("Information", "All tasks finished!"))

        except Error as e:
            self.main.log_print(f"Playwright Error: {e}")
        except Exception as ex:
            self.log_print(f"An unexpected error occurred in the main_task function: {ex}")

    def run(self):
        """
        Run the main task using asyncio.

        This method starts a new event loop, sets it as the current event loop, and runs the main task using asyncio.
        After the completion of the main task, the event loop is closed.

        :return: None
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.main_task())
        loop.close()

    async def browser_manager(self, playwright, domain, proxy_server, user_id):
        """
        Manages the browser instance for a user task.

        :param playwright: The `playwright` instance.
        :param domain: The domain to crawl.
        :param proxy_server: The proxy server to be used.
        :param user_id: The ID of the user task.
        :return: None
        """
        while not self.main.stop_event.is_set():
            await asyncio.sleep(1)
            if self.main.stop_event.is_set():
                self.log_print(f"User {user_id} task stopped due to Stop button press.")
                break
            start_time = time.time()
            self.user_data[user_id]["start_time"] = start_time
            if self.user_data[user_id].get("end_time") is not None:
                break
            browser_instance = await self.browser_setup(playwright, user_id, domain, proxy_server)

            if browser_instance is None:
                return

            browser, context, page = browser_instance

            if not browser or not page or not context:
                self.main.log_print("No browsers with proxies available")
                return

            try:
                await asyncio.wait_for(self.crawl_page(page, domain, start_time, user_id), timeout=350)
                await context.close()
                if self.main.ended >= self.input_number:
                    return
                await asyncio.sleep(1)
            except Error as e:
                self.main.log_print(f"Error while using proxy {proxy_server}: {e}", message_type="error")
                await context.close()
                return None
            except Exception as e:
                self.main.log_print(f"Error occurred while crawling the page: {e}", message_type="error")
                await asyncio.sleep(1)  # wait a bit before retrying

    async def browser_setup(self, playwright, user_id, domain, proxy_server):
        """
        Set up the browser for a given user.

        :param playwright: The playwright instance.
        :type playwright: `playwright.async_api.AsyncPlaywright`
        :param user_id: The ID of the user.
        :type user_id: Any
        :param domain: The domain of the website.
        :type domain: str
        :param proxy_server: The proxy server to use.
        :type proxy_server: str
        :return: The browser, context, and page objects.
        :rtype: `playwright.async_api.Browser`, `playwright.async_api.BrowserContext`, `playwright.async_api.Page` or None
        """
        await asyncio.sleep(1)
        # Pair up the browsers and user agents
        browser_and_user_agent_pairs = [(playwright.firefox, useragent.firefox),
                                        (playwright.chromium, useragent.chrome)]

        # Randomly select a pair
        browser_chosen, user_agent_chosen = random.choice(browser_and_user_agent_pairs)

        proxy_parts = proxy_server.strip().split(":")
        server = proxy_parts[0] + ":" + proxy_parts[1]
        browser: Browser = await browser_chosen.launch(headless=True, proxy={"server": server})

        custom_headers = {
            'User-Agent': user_agent_chosen,
            'Accept-Language': 'en-US,en;q=0.5'
        }

        try:
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

            try:
                self.log_print(f"\nUser {user_id} using proxy: \n {server}")
                return browser, context, page
            except Error as e:
                self.log_print(f"Error while using proxy {proxy_server}: {e}", message_type="error")
                await context.close()
                return None
        except Error as e:
            self.log_print(f'Error while creating a new browser context: {e}', message_type="error")
            return None

    async def crawl_page(self, page: Page, domain, start_time, user_id):
        """

        """
        try:
            while not self.main.stop_event.is_set() or self.main.ended <= self.input_number:
                await asyncio.sleep(1)
                if self.user_data[user_id].get("end_time") is not None:
                    break
                ip_used = self.user_data[user_id].get("ip")
                self.main.log_to_started(user_id)
                await page.goto(domain, wait_until="networkidle")
                await page.wait_for_load_state("networkidle")
                self.main.log_print(f' User {user_id} entered ({ip_used})')

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
                timeout = 180000
                self.main.log_print(f"\n User {user_id} ({ip_used}) waiting for 3 minutes", message_type="info")

                if self.main.stop_event.is_set():
                    self.log_print(f"User {user_id} task stopped due to Stop button press.")
                    return

                await page.wait_for_timeout(timeout)
                end_time = time.time()
                self.user_data[user_id]["end_time"] = end_time
                elapsed_time = self.user_data[user_id]["end_time"] - self.user_data[user_id]["start_time"]
                self.main.log_print(f" User {user_id} exited", message_type="info")

                # Check if all desired views have exited and exit the loop.
                if self.main.ended >= self.input_number:
                    return
                self.main.ended += 1
                self.main.log_to_ended_view(user_id)
                self.main.log_to_total_view()
                await asyncio.sleep(1)
        except Error as e:
            self.main.error += 1
            self.main.log_to_total_view()
            self.main.log_to_error_view(user_id)
            self.log_print(f"Playwright Error for User {user_id}: {e}", message_type="error")
        except Exception as e:
            self.main.error += 1
            self.main.log_to_total_view()
            self.main.log_to_error_view(user_id)
            self.log_print(f"Unexpected error for User {user_id}: {e}", message_type="error")

    async def track_tasks(self, tasks, start_times):
        """
        Track the progress of tasks.

        :param tasks: A list of asyncio.Task objects representing the tasks to track.
        :param start_times: A defaultdict containing the start times of each task.
        :return: None
        """
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

    def stop(self):
        """
        Stops the execution of the task manager.

        :return: None
        """
        self.stop_event.set()


class Main(tk.Frame):
    """
    Class representing the main application window.

    Attributes:
        selected_domain (str): The selected domain.
        root (tk.Tk): The root Tkinter window.
        views (int): The total number of views.
        user_data (dict): A dictionary containing user data.
        ended (int): The total number of ended sessions.
        error (int): The total number of sessions paused due to error.
        stated (int): The total number of started sessions.
        running (tk.BooleanVar): A Boolean variable indicating if the application is running.
        running_tasks (list): A list of running tasks.
        stop_event (threading.Event): An event to signal to stop the application.
        start_stop_button (tk.Button): The start/stop button.
        log_text (tk.Text): The log text widget.
        log_started_label (tk.Label): The label for ongoing sessions.
        log_started (tk.Text): The text widget for ongoing sessions.
        log_errored_label (tk.Label): The label for sessions paused due to error.
        log_errored (tk.Text): The text widget for sessions paused due to error.
        log_exited_label (tk.Label): The label for finished sessions.
        log_exited (tk.Text): The text widget for finished sessions.
        input_number (int): The input number.
        num_var (tk.StringVar): The string variable for the input number.
        num_entry (tk.Entry): The entry widget for the input number.
        log_total_label (tk.Label): The label for the total sessions.
        log_total (tk.Text): The text widget for the total sessions.
        domain_var (tk.StringVar): The string variable for the selected domain.
        stop_yes (bool): A flag indicating if stopping a session is confirmed.
        domain_radio_buttons (list): A list of domain radio buttons.

    Methods:
        append_to_log(text: str, message_type: str = 'info') -> None:
            Append text to the log text widget.

        append_to_started_log(text: str, message_type: str = 'info') -> None:
            Append text to the ongoing sessions log.

        append_to_exited_log(text: str, message_type: str = 'info') -> None:
            Append text to the finished sessions log.

        append_to_error_log(text: str, message_type: str = 'info') -> None:
            Append text to the sessions paused due to error log.

        append_to_total_log() -> None:
            Update the total sessions log.

        log_print(*args, message_type: str = 'info') -> None:
            Print log message to console and append it to the log text widget.

        log_to_started(*args, message_type: str = 'info') -> None:
            Log message to the ongoing sessions log.

        log_to_ended_view(*args, message_type: str = 'info') -> None:
            Log message to the finished sessions log.

        log_to_error_view(*args, message_type: str = 'info') -> None:
            Log message to the sessions paused due to error log.

        log_to_total_view(*args, message_type: str = 'info') -> None:
            Update the total sessions log.

        check_input() -> None:
            Check if the input is valid and enable/disable the start/stop button accordingly.

        save_entry(*args) -> None:
            Save the value entered in the input number entry widget.

        start_stop_session() -> None:
            Start or stop the application.

        get_input_number() -> int:
            Get the input number as an integer.

        get_proxies() -> List[str]:
            Get the list of proxies from the proxy file.

    """

    def __init__(self, root: tk.Tk) -> None:
        super().__init__(root)
        self.selected_domain = None
        self.root = root
        self.root.title("Visitor")

        self.views = 0
        self.user_data = {}
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

        self.log_errored_label = tk.Label(self, text="Paused \n Due to Error")
        self.log_errored_label.grid(row=2, column=3)
        self.log_errored = tk.Text(self, height=3, width=20)
        self.log_errored.grid(row=3, column=3)

        self.log_exited_label = tk.Label(self, text="Finished \n Sessions")
        self.log_exited_label.grid(row=2, column=1)
        self.log_exited = tk.Text(self, height=3, width=20)
        self.log_exited.grid(row=3, column=1)

        self.input_number = 1
        self.num_var = tk.StringVar()
        self.num_entry = tk.Entry(self, textvariable=self.num_var)
        self.num_entry.grid(row=4, column=0)
        self.num_entry.bind('<Return>', self.save_entry)

        self.log_total_label = tk.Label(self, text="Total \n Counts")
        self.log_total_label.grid(row=5, column=3)
        self.log_total = tk.Text(self, height=4, width=24)
        self.log_total.grid(row=4, column=3)

        self.domain_var = tk.StringVar()
        self.domain_var.set(urls[0])
        self.stop_yes = False
        self.domain_radio_buttons = []

        for i, domain in enumerate(urls):
            radiobutton = tk.Radiobutton(self, text=domain, variable=self.domain_var, value=domain)
            radiobutton.grid(row=5 + i, column=0)
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

    def append_to_error_log(self, text, message_type='info'):
        self.log_errored.insert(tk.END, f"User {text} paused \n")
        self.log_errored.see(tk.END)

    def append_to_total_log(self):
        self.log_total.delete('1.0', tk.END)
        self.log_total.insert(tk.END,
                              f"Total {self.views} user created\n"
                              f"Total {self.ended} user exited\n"
                              f"Total {self.error} user paused")
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
        self.append_to_error_log(log_message)

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
            print(self.input_number)
        except ValueError:
            self.input_number = 0

    def start_stop_session(self):
        if not self.running.get():
            self.selected_domain = self.domain_var.get()
            self.log_print("Starting Application...")
            self.input_number = self.get_input_number()
            self.stop_event.clear()
            task_manager = TaskManager(self)
            threading.Thread(target=task_manager.run, daemon=True).start()
            self.start_stop_button.config(text="Stop", state="normal")
            self.running.set(True)
        else:
            self.stop_event.set()
            self.start_stop_button.config(text="Start", state="normal")
            self.running.set(False)  # Set the running state to False
            self.check_input()  # Recheck and enable/disable the button

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
            return []


def run_tkinter():
    root = tk.Tk()
    Main(root).pack()
    root.mainloop()


if __name__ == "__main__":
    run_tkinter()
