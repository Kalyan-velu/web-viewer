Certainly, here is the user guide with the added warning about running a large number of browser instances:

# User Guide: Web Crawling Script

This user guide provides instructions for using the web crawling script efficiently. The script utilizes Playwright and asyncio to perform web crawling tasks. It is essential to understand the workflow and error handling mechanisms to use the script effectively.

## Web Crawling Flow

### Initialization
- The `TaskManager` class manages web crawling tasks.
- It initializes with the main application instance and sets up various attributes.

### Main Task Execution
- The `main_task` method is the entry point for web crawling.
- It verifies that the execution number is greater than 0 and the proxy list is not empty.
- Multiple browser instances are launched asynchronously using Playwright based on the execution number.

### Browser Management Loop
- For each user session (represented by a browser instance):
  - A new browser instance starts and assigns a proxy server.
  - Custom headers and user agents are set.
  - A random duration (between 10 to 30 seconds) is awaited before proceeding.
  - A new asyncio task is created to manage this browser instance.

### Browser Setup
- Inside the `browser_setup` method:
  - A random browser (Firefox or Chromium) and a corresponding user agent are chosen.
  - The proxy server is set for the browser instance.
  - A new browser context is created with the proxy settings.
  - A new browser page is opened with custom headers and viewport settings.

### Crawling Page
- The `crawl_page` method handles the web crawling process.
- The browser navigates to the selected domain and waits for network activity to stabilize.
- It locates and clicks on a "Start" button if available on the page.
- The script waits for the page to transition to a payment page and waits for a predefined timeout (180 seconds).

### Data Logging
- Information about the start time, end time, and IP address (proxy) for each user session is logged.
- Errors and exceptions are caught and logged.

### Track Tasks
- The `track_tasks` method continuously monitors the status of asyncio tasks.
- Completed tasks are removed from the list.

### Session Termination
- Sessions are considered finished when they reach the predefined timeout or encounter an error.
- Session end times are recorded.

### Data Storage
- User data, including start and end times, is stored in a JSON file named "user_data.json."

### Task Completion
- Once all desired sessions have finished, the script marks the main execution as complete.

## Handling Proxy Errors

The script is equipped to handle proxy errors effectively:

### Proxy Server Selection
- The script selects a proxy server from a list of available proxies to assign to each web browser instance.

### Browser Setup
- The `browser_setup` method attempts to create a new browser instance with the selected proxy server.
- If the proxy server is not accessible or there is an issue with the proxy configuration, an exception may be raised, indicating a proxy error.

### Error Handling
- If a proxy error occurs during browser setup, it is caught in an `except` block.
- The error message is logged, indicating which proxy server encountered the error.

### Context Closure
- If a proxy error is encountered, the browser context associated with the problematic proxy is closed to release resources.
- This ensures that the script continues with other available proxy servers and does not block due to a single problematic proxy.

### Retry Mechanism
- After encountering a proxy error, the script continues to the next available proxy and attempts to create a new browser instance.
- It waits for a short duration (1 second) before retrying to avoid immediate retries and potential rate limiting from proxy servers.

### Logging Errors
- Proxy errors are logged in the script's log with details about the specific proxy server that encountered the error.
- This logging provides visibility into which proxies may be problematic.

## Storage Space Considerations

The script is unlikely to cause storage (disk space) to run out under typical usage conditions. However, some factors to keep in mind include:

### Data Logging
- The script logs user session information and stores it in a JSON file. Regularly cleaning up old log files can help manage storage usage.

### Browser Cache
- Each browser instance may use local storage and cache. Modern web browsers manage and clear their caches, limiting the impact on storage.

### Proxy Files
- The script reads proxy server information from a text file. Large or numerous entries in the proxy file may consume storage space.

### Temporary Files
- Temporary files created during script execution are typically managed by the operating system and cleaned up automatically.

Ensure that your system has sufficient available disk space to accommodate any potential storage usage by the script. Regularly monitoring and managing log files can help prevent storage space issues.

## Warning: Running a Large Number of Browser Instances

Please exercise caution when specifying a high number of views (browsers) for simultaneous execution. Running a large number of browser instances, such as 4000, may lead to the following challenges:

- **Resource Usage**: Creating and managing numerous browser instances can consume significant system resources, potentially affecting the performance and stability of your computer.

- **Proxy Servers**: Ensure that you have access to a sufficient number of working proxy servers if you intend to use them. Managing a large number of unique proxies can be complex.

- **Network Traffic**: Generating a high volume of network traffic may impact your internet connection's stability and performance.

- **Website Considerations**: Some websites may have security measures to detect and block automated traffic. Be aware of the websites you are targeting.

- **Script Execution Time**: Executing tasks for a large number of browsers may take a considerable amount of time.

- **Error Handling**: With more browser instances, the likelihood of encountering errors increases. Robust error handling is essential.

Before running the script with a large number of views, consider your computer's capabilities and the practicality of your use case. It's recommended to start with a smaller number of views and gradually increase it as needed.