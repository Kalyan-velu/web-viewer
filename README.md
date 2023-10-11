# Web Crawler

This is a Python script that automates interacting with the provided URLs. It uses Python 3.11.5, Tkinter for building a User Interface, and Playwright, a browser automation library to visit the URLs and interact with the pages in an automated manner.

## How to Setup to Run the App

1. Make sure Python 3.11.5 is installed: Check version using `python --version`.
2. Install Required Packages: You can install the required packages using the command.
```bash
pip install -r requirements.txt
```
3. Add Proxies: This program makes use of proxies which it gets from a file named `proxies.txt` in the same directory. You need to provide this file with each proxy on a new line.
4. Run the Script: After installing the required packages and setting up the proxy file, you can run the script using the command: `python script_name.py`

## Setup

1. Clone the project repository
2. Set up a Python virtual environment:
   ```
   python -m venv env
   ```
3. Activate the created Python virtual environment:
   - On Windows, run:
     ```
     .\env\Scripts\activate
     ```
   - On Unix or MacOS, run:
     ```
     source env/bin/activate
     ```
4. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```
5. Install the required browsers using Playwright:
   ```
   python -m playwright install
   ```

## Note

Upon running our code, Playwright might need to download certain browser binaries, which would require internet access. These binaries are necessary for browser automation. If your organization uses firewalls or some form of network security protocols, you might need to seek help from your IT department to allow these downloads.


# Caution

Ensure that the script is being run in a controlled and ethical manner and that you have the necessary permissions to automate interactions with the websites. Misuse may violate the terms of service of the website and might result in being blocked. Act responsibly.
