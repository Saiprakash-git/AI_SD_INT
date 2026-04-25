"""
Background task queue using ThreadPoolExecutor - no Celery needed.
Lightweight async task processing for OSINT investigations.
"""

import uuid
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


class TaskQueue:
    """Thread-pool based task queue."""
    
    _instance = None
    _lock = threading.Lock()
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = TaskQueue()
        return cls._instance
    
    def __init__(self, max_workers: int = 5):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.tasks = {}
        self._db = None

    def set_db(self, db):
        self._db = db

    def submit(self, fn, *args, task_name: str = "task", **kwargs) -> str:
        """Submit task and return task_id."""
        task_id = str(uuid.uuid4())
        
        task_info = {
            "task_id": task_id,
            "name": task_name,
            "status": TaskStatus.PENDING,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "started_at": None,
            "completed_at": None,
            "result": None,
            "error": None,
        }
        self.tasks[task_id] = task_info
        self._save_task(task_info)
        
        def _wrapper():
            self.tasks[task_id]["status"] = TaskStatus.RUNNING
            self.tasks[task_id]["started_at"] = datetime.now(timezone.utc).isoformat()
            self._save_task(self.tasks[task_id])
            try:
                result = fn(*args, **kwargs)
                self.tasks[task_id]["status"] = TaskStatus.COMPLETE
                self.tasks[task_id]["result"] = str(result)[:500] if result else "done"
            except Exception as e:
                self.tasks[task_id]["status"] = TaskStatus.FAILED
                self.tasks[task_id]["error"] = traceback.format_exc()[-500:]
            finally:
                self.tasks[task_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
                self._save_task(self.tasks[task_id])
        
        self.executor.submit(_wrapper)
        return task_id

    def get_status(self, task_id: str) -> dict:
        return self.tasks.get(task_id) or self._load_task(task_id) or {"error": "not found"}

    def _save_task(self, task_info: dict):
        if self._db is not None:
            try:
                self._db.tasks.replace_one(
                    {"task_id": task_info["task_id"]},
                    task_info,
                    upsert=True
                )
            except:
                pass

    def _load_task(self, task_id: str) -> dict:
        if self._db is not None:
            try:
                return self._db.tasks.find_one({"task_id": task_id}, {"_id": 0})
            except:
                pass
        return None
