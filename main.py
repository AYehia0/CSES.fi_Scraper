"""
CSES.fi offline.

requirements : 
- bs4
- requests

"""

import json
import time
from bs4 import BeautifulSoup
import requests
import os

from requests.sessions import session

CRED = {"username" : "TestMe", "password": "testtest123"}
BASE_URL = "https://cses.fi"
URL = f"{BASE_URL}/problemset/list/"
LOGIN_URL = "https://cses.fi/login"
PROBLEM_DIR = "CSES_Problems"
SUBMIT_URL = "https://cses.fi/course/send.php"
PROBLEM_RESULT_JSON = "./problems.json"


def login():
   session = requests.Session()

   # get the csrf_token
   resp = session.get(LOGIN_URL)
   soup = BeautifulSoup(resp.content, "html.parser")
   csrf_token = soup.find("input")["value"]

   payload = {
       "csrf_token": csrf_token,
       "nick": "TestMe",
       "pass": "testtest123"
    }
   resp = session.post(LOGIN_URL, data=payload)

   return session


def get_data(session):
   """Get problems as dict with names, urls and scores"""
   data = {}
   resp = session.get(URL)
   soup = BeautifulSoup(resp.content, "html.parser")
   content = soup.find("div", class_="content")
   headers = content.find_all("h2")[1:]
   for header in headers:
       data[header.text] = []
   task_list = content.find_all("ul", class_="task-list")[1:]
   for (tasks, header) in zip(task_list, headers):
       for task in tasks.find_all("li"):
           problem_url = task.find("a")["href"]
           problem_name = task.find("a").text
           problem_score = task.find("span", class_="detail").text
           submit_url = submit_soultion(session, BASE_URL + problem_url)
           tests = get_test_cases(session, submit_url)
           data[header.text].append({
               "name": problem_name,
               "url" : BASE_URL + "/" + problem_url,
               "score" : problem_score,
               "tests": tests 
           })
           time.sleep(3)
   return data


def get_problem_desc(url):
   resp = requests.get(url)
   soup = BeautifulSoup(resp.content, "html.parser")
   content = soup.find("div", class_="content")
   return content.text

def download_textfile(session, url, filepath):
    response = session.get(url)
    if response.status_code == 200:
        # Save the file with the extracted filename
        with open(filepath, 'w') as file:
            file.write(response.text)

def save_problems(session, data):
    base_dir = PROBLEM_DIR
    os.makedirs(base_dir, exist_ok=True)  # Create main directory if it doesn't exist
    for k, v in data.items():
        category_dir = os.path.join(base_dir, k)
        os.makedirs(category_dir, exist_ok=True)  # Create category directory if it doesn't exist
        for problem in v:
            dir_name = problem["name"]
            print(f"Downloading: {dir_name}")
            problem_dir = os.path.join(category_dir, dir_name)
            # TODO: check if the test cases were downloaded
            if not os.path.exists(problem_dir):  # Check if problem directory already exists
                os.mkdir(problem_dir)
                problem_desc = get_problem_desc(problem["url"])
                # Write to a text file
                file_path = os.path.join(problem_dir, dir_name)
                with open(file_path, "w+", encoding="utf-8") as f:
                    f.write(problem_desc)

                # download the testcases
                tests = problem['tests']
                for ind, test in enumerate(tests, 1):
                    input_test, output_test = test
                    download_textfile(session, input_test, os.path.join(problem_dir, f"INP{ind}.txt"))
                    download_textfile(session, output_test, os.path.join(problem_dir, f"OUT{ind}.txt"))

          
def submit_soultion(session, problem_url):
    problem_id = problem_url.split("/")[-1]
    resp = session.get(f"https://cses.fi/problemset/submit/{problem_id}")

    soup = BeautifulSoup(resp.content, "html.parser")
    csrf_token = soup.find("input")["value"]

    sub_url = BASE_URL + soup.find_all("a")[-1]["href"]

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Origin': 'https://cses.fi',
        'Referer': f'https://cses.fi/problemset/submit/{problem_id}',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
    }

    files = [('file',('hello_world.py',open('./hello_world.py','rb'),'multipart/form-data'))]

    data = {
        'csrf_token': csrf_token,
        'task': problem_id,
        'lang': 'Python3',
        'option': 'CPython3',
        'type': 'course',
        'target': 'problemset',
    }
    resp = session.post(SUBMIT_URL, headers=headers, files=files, data=data)

    soup = BeautifulSoup(resp.content, "html.parser")
    sub_url = BASE_URL + soup.find_all("a")[-1]["href"]

    return sub_url

# return a list of the input and output urls of the test cases
def get_test_cases(session, url):
    tests = []
    resp = session.get(url)
    soup = BeautifulSoup(resp.content, "html.parser")
    all_tables = soup.find_all("table")[2:]
    for ind, t in enumerate(all_tables, 1):
        if ind % 3 == 0:
            continue
        file_url = t.find("a", class_="save")
        tests.append(BASE_URL+ file_url["href"])

    # group of 2s : (input, correct_output)
    tests = [tuple(tests[i:i+2]) for i in range(0, len(tests), 2)]
    return tests

def save_result_json(problems):
    with open(PROBLEM_RESULT_JSON, "w") as file:
        json.dump(problems, file)

def main():
    s = login()
    if os.path.exists(PROBLEM_RESULT_JSON):
       with open(PROBLEM_RESULT_JSON, "r") as f:
           problems = json.load(f)
    else:
        problems = get_data(s)
        save_result_json(problems)

    save_problems(s, problems)

main()
