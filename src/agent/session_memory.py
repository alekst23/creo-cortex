from uuid import uuid4
import threading
from pymongo import MongoClient
from pymongo.collection import Collection
from bson import ObjectId

class SessionMemory():
    def __init__(self, session_id: str = None):
        if session_id is None:
            session_id = str(uuid4())[:8]
        self.session_id = session_id
        self.client = MongoClient("mongodb://localhost:27017/")
        self.db = self.client["aws-agent-session-memory"]

    def add_note(self, note):
        self.db["notes"].insert_one({"session_id": self.session_id, "note": note})

    def get_notes(self):
        return list(self.db["notes"].find({"session_id": self.session_id}))
    
    def get_messages(self):
        return list(self.db["messages"].find({"session_id": self.session_id}))
    
    def add_message(self, role, content):
        self.db["messages"].insert_one({"session_id": self.session_id, "role": role, "content": content})

    def get_working_dir(self):
        result = self.db["environment"].find_one({"session_id": self.session_id})
        if result:
            return result.get("working_dir", None)
        return None

    def set_working_dir(self, working_dir):
        self.db["environment"].update_one({"session_id": self.session_id}, {"$set": {"working_dir": working_dir}}, upsert=True)

    def set_goal(self, goal):
        self.db["environment"].update_one({"session_id": self.session_id}, {"$set": {"goal": goal}}, upsert=True)

    def get_goal(self):
        result = self.db["environment"].find_one({"session_id": self.session_id})
        if result:
            return result.get("goal", None)
        return None
    
    def add_task(self, task: str, sort_order: float=None):
        if sort_order is not None:
            self.db["tasks"].insert_one(dict(session_id=self.session_id, task=task, status="new", sort_order=sort_order))
        else:
            tasks = self.db["tasks"].find({"session_id": self.session_id})
            sort_order = 0.0
            for task in tasks:
                if task["sort_order"] > sort_order:
                    sort_order = task["sort_order"]
            sort_order += 1
            self.db["tasks"].insert_one(dict(session_id=self.session_id, task=task, status="new", sort_order=sort_order))

    def set_task_status(self, task_id, status):
        self.db["tasks"].update_one({"session_id": self.session_id, "_id": ObjectId(task_id)}, {"$set": {"status": status}})

    def get_tasks(self):
        tasks = self.db["tasks"].find({"session_id": self.session_id})
        sorted_tasks = sorted(tasks, key=lambda x: x["sort_order"])
        return sorted_tasks
    
    def set_open_file(self, file_path, data):
        self.db["files"].update_one({"session_id": self.session_id, "file_path": file_path}, {"$set": {"data": data}}, upsert=True)

    def get_open_files(self):
        return list(self.db["files"].find({"session_id": self.session_id}))
    

# Lazy initialization with thread-safety
_session_memory = None
_lock = threading.Lock()

def get_session_memory(session_id=None)->SessionMemory:
    global _session_memory
    if _session_memory is None:
        with _lock:  # Ensures thread-safe initialization
            if _session_memory is None:  # Double-checked locking
                _session_memory = SessionMemory(session_id)
    return _session_memory