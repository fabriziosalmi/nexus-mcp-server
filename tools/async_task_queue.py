# -*- coding: utf-8 -*-
# tools/async_task_queue.py
import asyncio
import threading
import uuid
import time
import json
import os
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass, asdict
from enum import Enum
import traceback

class TaskStatus(Enum):
    """Stati possibili per i task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class TaskInfo:
    """Informazioni di un task."""
    task_id: str
    name: str
    description: str
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    result: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Converte il task in dizionario per serializzazione."""
        data = asdict(self)
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        data['started_at'] = self.started_at.isoformat() if self.started_at else None
        data['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        return data

class AsyncTaskQueue:
    """Gestore della coda di task asincroni per operazioni a lunga esecuzione."""
    
    def __init__(self, max_workers: int = 4, storage_path: str = "safe_files/task_storage.json"):
        self.max_workers = max_workers
        self.storage_path = storage_path
        self.tasks: Dict[str, TaskInfo] = {}
        self.futures: Dict[str, Future] = {}
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self._lock = threading.Lock()
        self._load_tasks()
        
        # Cleanup timer per task completati/falliti
        self._cleanup_timer = None
        self._start_cleanup_timer()
    
    def _load_tasks(self):
        """Carica i task salvati dal file di storage."""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for task_data in data.get('tasks', []):
                        task = self._dict_to_task(task_data)
                        # Resetta task in esecuzione a falliti durante startup
                        if task.status == TaskStatus.RUNNING:
                            task.status = TaskStatus.FAILED
                            task.error = "Task interrotto durante riavvio server"
                            task.completed_at = datetime.now(timezone.utc)
                        self.tasks[task.task_id] = task
        except Exception as e:
            logging.warning(f"Errore nel caricamento task: {e}")
    
    def _save_tasks(self):
        """Salva i task nel file di storage."""
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            data = {
                'tasks': [task.to_dict() for task in self.tasks.values()],
                'saved_at': datetime.now(timezone.utc).isoformat()
            }
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Errore nel salvataggio task: {e}")
    
    def _dict_to_task(self, task_data: Dict[str, Any]) -> TaskInfo:
        """Converte un dizionario in TaskInfo."""
        return TaskInfo(
            task_id=task_data['task_id'],
            name=task_data['name'],
            description=task_data['description'],
            status=TaskStatus(task_data['status']),
            created_at=datetime.fromisoformat(task_data['created_at'].replace('Z', '+00:00')),
            started_at=datetime.fromisoformat(task_data['started_at'].replace('Z', '+00:00')) if task_data.get('started_at') else None,
            completed_at=datetime.fromisoformat(task_data['completed_at'].replace('Z', '+00:00')) if task_data.get('completed_at') else None,
            progress=task_data.get('progress', 0.0),
            result=task_data.get('result'),
            error=task_data.get('error'),
            metadata=task_data.get('metadata', {})
        )
    
    def _start_cleanup_timer(self):
        """Avvia timer per cleanup automatico dei task completati."""
        def cleanup_old_tasks():
            while True:
                time.sleep(300)  # Cleanup ogni 5 minuti
                self._cleanup_completed_tasks(max_age_hours=24)
        
        cleanup_thread = threading.Thread(target=cleanup_old_tasks, daemon=True)
        cleanup_thread.start()
    
    def submit_task(self, name: str, description: str, func: Callable, *args, **kwargs) -> str:
        """
        Sottomette un task alla coda per esecuzione asincrona.
        
        Args:
            name: Nome del task
            description: Descrizione del task
            func: Funzione da eseguire
            *args, **kwargs: Argomenti per la funzione
            
        Returns:
            ID del task
        """
        task_id = str(uuid.uuid4())
        
        with self._lock:
            task = TaskInfo(
                task_id=task_id,
                name=name,
                description=description,
                status=TaskStatus.PENDING,
                created_at=datetime.now(timezone.utc),
                metadata={'args': str(args), 'kwargs': str(kwargs)}
            )
            
            self.tasks[task_id] = task
            
            # Wrapper per esecuzione task
            def task_wrapper():
                try:
                    # Aggiorna status a running
                    with self._lock:
                        self.tasks[task_id].status = TaskStatus.RUNNING
                        self.tasks[task_id].started_at = datetime.now(timezone.utc)
                        self._save_tasks()
                    
                    # Esegui la funzione
                    result = func(*args, **kwargs)
                    
                    # Aggiorna con risultato
                    with self._lock:
                        self.tasks[task_id].status = TaskStatus.COMPLETED
                        self.tasks[task_id].completed_at = datetime.now(timezone.utc)
                        self.tasks[task_id].result = result
                        self.tasks[task_id].progress = 100.0
                        self._save_tasks()
                    
                    return result
                    
                except Exception as e:
                    # Aggiorna con errore
                    with self._lock:
                        self.tasks[task_id].status = TaskStatus.FAILED
                        self.tasks[task_id].completed_at = datetime.now(timezone.utc)
                        self.tasks[task_id].error = str(e)
                        self.tasks[task_id].result = traceback.format_exc()
                        self._save_tasks()
                    
                    raise
            
            # Sottometti al thread pool
            future = self.executor.submit(task_wrapper)
            self.futures[task_id] = future
            
            self._save_tasks()
            logging.info(f"Task sottomesso: {task_id} - {name}")
            
            return task_id
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Ottiene lo status di un task."""
        with self._lock:
            task = self.tasks.get(task_id)
            if not task:
                return None
            return task.to_dict()
    
    def list_tasks(self, status_filter: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """Lista tutti i task con filtri opzionali."""
        with self._lock:
            tasks = list(self.tasks.values())
            
            # Applica filtro status
            if status_filter:
                try:
                    filter_status = TaskStatus(status_filter.lower())
                    tasks = [t for t in tasks if t.status == filter_status]
                except ValueError:
                    return {
                        "success": False,
                        "error": f"Status non valido: {status_filter}"
                    }
            
            # Ordina per data di creazione (più recenti prima)
            tasks.sort(key=lambda t: t.created_at, reverse=True)
            
            # Applica limit
            tasks = tasks[:limit]
            
            # Statistiche
            all_tasks = list(self.tasks.values())
            stats = {
                "total": len(all_tasks),
                "pending": len([t for t in all_tasks if t.status == TaskStatus.PENDING]),
                "running": len([t for t in all_tasks if t.status == TaskStatus.RUNNING]),
                "completed": len([t for t in all_tasks if t.status == TaskStatus.COMPLETED]),
                "failed": len([t for t in all_tasks if t.status == TaskStatus.FAILED]),
                "cancelled": len([t for t in all_tasks if t.status == TaskStatus.CANCELLED])
            }
            
            return {
                "success": True,
                "statistics": stats,
                "tasks": [task.to_dict() for task in tasks],
                "returned_count": len(tasks),
                "filter_applied": status_filter
            }
    
    def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """Cancella un task."""
        with self._lock:
            task = self.tasks.get(task_id)
            if not task:
                return {
                    "success": False,
                    "error": f"Task {task_id} non trovato"
                }
            
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                return {
                    "success": False,
                    "error": f"Impossibile cancellare task con status: {task.status.value}"
                }
            
            # Cancella future se in esecuzione
            future = self.futures.get(task_id)
            if future and not future.done():
                future.cancel()
            
            # Aggiorna status
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now(timezone.utc)
            task.error = "Task cancellato dall'utente"
            
            self._save_tasks()
            
            return {
                "success": True,
                "task_id": task_id,
                "message": "Task cancellato con successo"
            }
    
    def remove_task(self, task_id: str) -> Dict[str, Any]:
        """Rimuove completamente un task."""
        with self._lock:
            task = self.tasks.get(task_id)
            if not task:
                return {
                    "success": False,
                    "error": f"Task {task_id} non trovato"
                }
            
            # Verifica che non sia in esecuzione
            if task.status == TaskStatus.RUNNING:
                return {
                    "success": False,
                    "error": "Impossibile rimuovere task in esecuzione. Cancellalo prima."
                }
            
            # Rimuovi future
            if task_id in self.futures:
                del self.futures[task_id]
            
            # Rimuovi task
            del self.tasks[task_id]
            self._save_tasks()
            
            return {
                "success": True,
                "task_id": task_id,
                "message": "Task rimosso con successo"
            }
    
    def _cleanup_completed_tasks(self, max_age_hours: int = 24):
        """Rimuove automaticamente task completati/falliti vecchi."""
        try:
            cutoff_time = datetime.now(timezone.utc).timestamp() - (max_age_hours * 3600)
            
            with self._lock:
                to_remove = []
                for task_id, task in self.tasks.items():
                    if (task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] and
                        task.completed_at and task.completed_at.timestamp() < cutoff_time):
                        to_remove.append(task_id)
                
                for task_id in to_remove:
                    if task_id in self.futures:
                        del self.futures[task_id]
                    del self.tasks[task_id]
                
                if to_remove:
                    self._save_tasks()
                    logging.info(f"Cleanup automatico: rimossi {len(to_remove)} task vecchi")
                    
        except Exception as e:
            logging.error(f"Errore durante cleanup task: {e}")
    
    def get_queue_info(self) -> Dict[str, Any]:
        """Ottiene informazioni sulla coda di task."""
        with self._lock:
            tasks = list(self.tasks.values())
            
            return {
                "success": True,
                "queue_info": {
                    "max_workers": self.max_workers,
                    "active_futures": len([f for f in self.futures.values() if not f.done()]),
                    "storage_path": self.storage_path,
                    "total_tasks": len(tasks),
                    "oldest_task": min(tasks, key=lambda t: t.created_at).created_at.isoformat() if tasks else None,
                    "newest_task": max(tasks, key=lambda t: t.created_at).created_at.isoformat() if tasks else None
                },
                "statistics": {
                    "pending": len([t for t in tasks if t.status == TaskStatus.PENDING]),
                    "running": len([t for t in tasks if t.status == TaskStatus.RUNNING]),
                    "completed": len([t for t in tasks if t.status == TaskStatus.COMPLETED]),
                    "failed": len([t for t in tasks if t.status == TaskStatus.FAILED]),
                    "cancelled": len([t for t in tasks if t.status == TaskStatus.CANCELLED])
                }
            }

# Istanza globale del task queue
_task_queue = AsyncTaskQueue()

def register_tools(mcp):
    """Registra i tool di gestione coda asincrona con l'istanza del server MCP."""
    logging.info("🔄 Registrazione tool-set: Async Task Queue")

    @mcp.tool()
    def queue_long_running_task(name: str, description: str, task_type: str = "sleep", 
                              duration: int = 10, custom_data: str = "") -> Dict[str, Any]:
        """
        Sottomette un task a lunga esecuzione alla coda asincrona.
        
        Args:
            name: Nome del task
            description: Descrizione del task
            task_type: Tipo di task ('sleep', 'cpu_intensive', 'io_intensive', 'custom')
            duration: Durata in secondi per task di tipo sleep
            custom_data: Dati personalizzati per il task
        """
        try:
            # Funzioni di esempio per diversi tipi di task
            def sleep_task(duration):
                """Task di attesa."""
                import time
                total = duration
                for i in range(total):
                    time.sleep(1)
                    # Simula aggiornamento progresso (in versione completa)
                return f"Task completato dopo {duration} secondi"
            
            def cpu_intensive_task(duration):
                """Task CPU-intensive."""
                import time
                start = time.time()
                end = start + duration
                count = 0
                while time.time() < end:
                    count += 1
                    # Operazione CPU-intensive
                    [x**2 for x in range(1000)]
                return f"Task CPU completato. Iterazioni: {count}"
            
            def io_intensive_task(duration):
                """Task IO-intensive."""
                import time
                import tempfile
                import os
                
                start = time.time()
                end = start + duration
                files_created = 0
                
                with tempfile.TemporaryDirectory() as temp_dir:
                    while time.time() < end:
                        file_path = os.path.join(temp_dir, f"test_{files_created}.txt")
                        with open(file_path, 'w') as f:
                            f.write("Test data " * 1000)
                        files_created += 1
                        time.sleep(0.1)
                
                return f"Task IO completato. File creati: {files_created}"
            
            def custom_task(custom_data):
                """Task personalizzato."""
                import time
                time.sleep(2)  # Simula lavoro
                return f"Task personalizzato completato con dati: {custom_data}"
            
            # Seleziona la funzione in base al tipo
            if task_type == "sleep":
                func = sleep_task
                args = (duration,)
            elif task_type == "cpu_intensive":
                func = cpu_intensive_task
                args = (duration,)
            elif task_type == "io_intensive":
                func = io_intensive_task
                args = (duration,)
            elif task_type == "custom":
                func = custom_task
                args = (custom_data,)
            else:
                return {
                    "success": False,
                    "error": f"Tipo task non supportato: {task_type}"
                }
            
            # Sottometti il task
            task_id = _task_queue.submit_task(name, description, func, *args)
            
            return {
                "success": True,
                "task_id": task_id,
                "name": name,
                "description": description,
                "task_type": task_type,
                "message": "Task sottomesso con successo alla coda asincrona"
            }
            
        except Exception as e:
            logging.error(f"Errore nella sottomissione task: {e}")
            return {
                "success": False,
                "error": f"Errore nella sottomissione task: {str(e)}"
            }

    @mcp.tool()
    def get_task_status(task_id: str) -> Dict[str, Any]:
        """
        Ottiene lo status e i dettagli di un task specifico.
        
        Args:
            task_id: ID del task da controllare
        """
        try:
            task_info = _task_queue.get_task_status(task_id)
            
            if not task_info:
                return {
                    "success": False,
                    "error": f"Task {task_id} non trovato"
                }
            
            return {
                "success": True,
                "task": task_info
            }
            
        except Exception as e:
            logging.error(f"Errore nel recupero status task: {e}")
            return {
                "success": False,
                "error": f"Errore nel recupero status: {str(e)}"
            }

    @mcp.tool()
    def list_all_tasks(status_filter: str = "", limit: int = 20) -> Dict[str, Any]:
        """
        Lista tutti i task nella coda con filtri opzionali.
        
        Args:
            status_filter: Filtra per status (pending, running, completed, failed, cancelled)
            limit: Numero massimo di task da restituire (1-100)
        """
        try:
            if limit < 1 or limit > 100:
                return {
                    "success": False,
                    "error": "Limit deve essere tra 1 e 100"
                }
            
            filter_value = status_filter.strip() if status_filter.strip() else None
            result = _task_queue.list_tasks(status_filter=filter_value, limit=limit)
            
            return result
            
        except Exception as e:
            logging.error(f"Errore nel listing task: {e}")
            return {
                "success": False,
                "error": f"Errore nel listing: {str(e)}"
            }

    @mcp.tool()
    def cancel_task(task_id: str) -> Dict[str, Any]:
        """
        Cancella un task in esecuzione o in attesa.
        
        Args:
            task_id: ID del task da cancellare
        """
        try:
            result = _task_queue.cancel_task(task_id)
            return result
            
        except Exception as e:
            logging.error(f"Errore nella cancellazione task: {e}")
            return {
                "success": False,
                "error": f"Errore nella cancellazione: {str(e)}"
            }

    @mcp.tool()
    def remove_task(task_id: str) -> Dict[str, Any]:
        """
        Rimuove completamente un task dalla coda (solo se non in esecuzione).
        
        Args:
            task_id: ID del task da rimuovere
        """
        try:
            result = _task_queue.remove_task(task_id)
            return result
            
        except Exception as e:
            logging.error(f"Errore nella rimozione task: {e}")
            return {
                "success": False,
                "error": f"Errore nella rimozione: {str(e)}"
            }

    @mcp.tool()
    def get_queue_info() -> Dict[str, Any]:
        """
        Ottiene informazioni generali sulla coda di task asincroni.
        """
        try:
            result = _task_queue.get_queue_info()
            return result
            
        except Exception as e:
            logging.error(f"Errore nel recupero info coda: {e}")
            return {
                "success": False,
                "error": f"Errore nel recupero info: {str(e)}"
            }

    @mcp.tool()
    def cleanup_completed_tasks(max_age_hours: int = 24) -> Dict[str, Any]:
        """
        Rimuove manualmente i task completati/falliti più vecchi di X ore.
        
        Args:
            max_age_hours: Età massima in ore per i task da mantenere (1-168)
        """
        try:
            if max_age_hours < 1 or max_age_hours > 168:  # Max 1 settimana
                return {
                    "success": False,
                    "error": "max_age_hours deve essere tra 1 e 168"
                }
            
            _task_queue._cleanup_completed_tasks(max_age_hours)
            
            return {
                "success": True,
                "message": f"Cleanup completato per task più vecchi di {max_age_hours} ore"
            }
            
        except Exception as e:
            logging.error(f"Errore nel cleanup task: {e}")
            return {
                "success": False,
                "error": f"Errore nel cleanup: {str(e)}"
            }