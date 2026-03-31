---
created_at: '2026-03-31T10:27:56.931707'
modified_at: '2026-03-31T10:42:27.226836'
published: true
title: When To Thread Python
---

### First, The GIL

The Global Interpreter Lock (GIL). To protect the values of the objects stored, only one thread at a time can execute Python code that reads or modifies variables in memory. The GIL fundamentally shapes how threading behaves in Python. When multiple threads are running, only one thread can actively execute Python bytecode at a time. Other threads must wait their turn and interpreter rapidly switches between threads to simulate concurrency. This matters most when your threads are doing CPU work:

```python
import time
import concurrent.futures as cf

data = range(5)

def cpu_heavy_task(n):
    total = 0
    for _ in range(10_000_000):
        total += 1
    return total

# Single-threaded
start = time.time()
results = [cpu_heavy_task(x) for x in data]
end = time.time()
print(f"Single-threaded: {end - start:.2f}s")


# Multi-threaded
start = time.time()
with cf.ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(cpu_heavy_task, data))
end = time.time()
print(f"Multi-threaded: {end - start:.2f}s")
```

Threads didn't make things go faster because the GIL could only do one at a time (rapidly modifying the value of total), sequentially instead of in parallel.

### When Threads Help

Threads become useful when your program spends time waiting (more technically known as I/O-bound task), not computing. Making HTTP requests (requests.get), reading files from disk, querying a database, waiting on APIs, and sleeping (time.sleep) are I/O-bound tasks that require time before the next line of code can be executed. While waiting,  the CPU is not needed, the GIL isn't locking that thread, and Python can switch to another thread. Here I think it is worth noting that even if you think you aren't using threads, there is always a main thread. So yes, you are. Multiple threads are productive when they can do CPU work while other threads are waiting. Instead of wait, work, wait, work, on and on however many times... you can put your waiting tasks on the back burner metaphorically, queued up to return to later, while the CPU is working on a different thread that is ready to do work, then continue to work through the queue of unfinished threads. Which is another important part of multi-threading, that you can't know for sure the order of completion.

Let's look at a simple example of web scraping, where I had saved the urls in a separate json file:

```python
import requests
from bs4 import BeautifulSoup
import concurrent.futures as cf
import time, json

with open('threading/urls_data.json') as f:
    urls = json.load(f)

def fetch_and_parse(url):
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.content, 'html.parser')
        return url, soup.title.text.strip()
    except Exception as e:
        return url, str(e)

start = time.time()

with cf.ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(fetch_and_parse, urls))

end = time.time()
print(f"Total time taken: {end - start:.2f} seconds")
```

In our fetch_and_parse task, the HTTP request is I/O-bound, but then parsing is CPU. So if CPU is going to be locked, why include it in the multi-threaded work? Well, compare it to if you thread the I/O-bound but still sequentially parse:

```python
import requests
from bs4 import BeautifulSoup
import concurrent.futures as cf
import time, json

with open('threading/urls_data.json') as f:
    urls = json.load(f)
		
def fetch_only(url):
    try:
        response = requests.get(url, timeout=5)
        return url, response
    except Exception as e:
        return url, str(e)

def parse_only(url, response):
    try:
        soup = BeautifulSoup(response.content, 'html.parser')
        return url, soup.title.text.strip()
    except Exception as e:
        return url, str(e)

start = time.time()

# Step 1: Fetch concurrently
with cf.ThreadPoolExecutor(max_workers=5) as executor:
    responses = list(executor.map(fetch_only, urls))

# Step 2: Parse sequentially
results = [parse_only(url, response) for url, response in responses]

end = time.time()
print(f"Total time taken with separate fetching and parsing: {end - start:.2f} seconds")
```

Well it isn't super heavy use of CPU but it is also giving python something to do while it is waiting. In the second version, our main thread requires Step 1 to complete before Step 2. In our first version, combining fetching and parsing in one task, when some workers are not using the GIL and still waiting on network requests, another worker that is ready to parse is able to run. Threading doesn't speed up parsing, it just helps time it better so the CPU will be put to use instead of being idle. Then the overall result is everything gets done faster. I only used about 20 urls and saw a big difference in performance. The performance gain from multiple threads comes from overlapping waiting with useful work. Don't think that you need to leave the CPU tasks out of your threaded tasks.