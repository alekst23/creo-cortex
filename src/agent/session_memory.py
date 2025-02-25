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
    
    def remove_note(self, note_id):
        self.db["notes"].delete_one({"session_id": self.session_id, "_id": ObjectId(note_id)})

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
            for t in tasks:
                if t["sort_order"] > sort_order:
                    sort_order = t["sort_order"]
            sort_order += 1
            self.db["tasks"].insert_one(dict(session_id=self.session_id, task=task, status="new", sort_order=sort_order))

    def set_task_status(self, task_id, status):
        self.db["tasks"].update_one({"session_id": self.session_id, "_id": ObjectId(task_id)}, {"$set": {"status": status}})

    def update_task(self, task_id, status, result):
        self.db["tasks"].update_one({"session_id": self.session_id, "_id": ObjectId(task_id)}, {"$set": {"status": status, "result": result}})
        
    def get_tasks(self):
        tasks = self.db["tasks"].find({"session_id": self.session_id})
        sorted_tasks = sorted(tasks, key=lambda x: x["sort_order"])
        return sorted_tasks
    
    def clear_tasks(self):
        self.db["tasks"].delete_many({"session_id": self.session_id})

    def set_open_file(self, file_path, data):
        self.db["files"].update_one({"session_id": self.session_id, "file_path": file_path}, {"$set": {"data": data}}, upsert=True)

    def get_open_files(self):
        return list(self.db["files"].find({"session_id": self.session_id}))
    
    def remove_open_file(self, file_path):
        self.db["files"].delete_one({"session_id": self.session_id, "file_path": file_path})
    
    def get_boost_state(self):
        result = self.db["environment"].find_one({"session_id": self.session_id})
        if result:
            return result.get("boost_state", False)
        return False
    
    def set_boost_state(self, state):
        self.db["environment"].update_one({"session_id": self.session_id}, {"$set": {"boost_state": state}}, upsert=True)
    

# Lazy initialization with thread-safety
_session_memory = {}
_lock = threading.Lock()

def get_session_memory(session_id=None)->SessionMemory:
    global _session_memory
    if _session_memory is None or session_id not in _session_memory:
        with _lock:  # Ensures thread-safe initialization
            _session_memory[session_id] = SessionMemory(session_id)
    return _session_memory[session_id]