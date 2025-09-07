# -*- coding: utf-8 -*-
# tools/async_task_queue.py
import asyncio
import threading
import uuid
import time
import json
import os
import logging
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass, asdict, field
from enum import Enum
import traceback
import heapq
from functools import wraps

class TaskStatus(Enum):
    """Stati possibili per i task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

class TaskPriority(Enum):
    """Priorità dei task."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

@dataclass
class TaskInfo:
    """Informazioni di un task."""
    task_id: str
    name: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    result: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 0
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Converte il task in dizionario per serializzazione."""
        data = asdict(self)
        data['status'] = self.status.value
        data['priority'] = self.priority.value
        data['created_at'] = self.created_at.isoformat()
        data['started_at'] = self.started_at.isoformat() if self.started_at else None
        data['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        # Serialize result safely
        try:
            json.dumps(data['result'])
        except (TypeError, ValueError):
            data['result'] = str(data['result']) if data['result'] is not None else None
        return data

    def update_progress(self, progress: float, message: str = ""):
        """Aggiorna il progresso del task."""
        self.progress = max(0.0, min(100.0, progress))
        if message:
            if 'progress_messages' not in self.metadata:
                self.metadata['progress_messages'] = []
            self.metadata['progress_messages'].append({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'progress': self.progress,
                'message': message
            })

class ProgressCallback:
    """Callback per aggiornamento progresso task."""
    def __init__(self, task_queue, task_id: str):
        self.task_queue = task_queue
        self.task_id = task_id
    
    def update(self, progress: float, message: str = ""):
        """Aggiorna il progresso del task."""
        with self.task_queue._lock:
            if self.task_id in self.task_queue.tasks:
                self.task_queue.tasks[self.task_id].update_progress(progress, message)

class AsyncTaskQueue:
    """Gestore della coda di task asincroni per operazioni a lunga esecuzione."""
    
    def __init__(self, max_workers: int = 4, storage_path: str = "safe_files/task_storage.json"):
        self.max_workers = max_workers
        self.storage_path = storage_path
        self.tasks: Dict[str, TaskInfo] = {}
        self.futures: Dict[str, Future] = {}
        self.priority_queue = []  # heap per priorità
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self._lock = threading.Lock()
        self._running_count = 0
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
                        if task.status in [TaskStatus.RUNNING, TaskStatus.RETRYING]:
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
        def parse_datetime(dt_str):
            if not dt_str:
                return None
            # Handle different datetime formats
            dt_str = dt_str.replace('Z', '+00:00')
            if '+' in dt_str or dt_str.endswith('Z'):
                return datetime.fromisoformat(dt_str)
            else:
                # Assume UTC if no timezone info
                return datetime.fromisoformat(dt_str).replace(tzinfo=timezone.utc)
        
        return TaskInfo(
            task_id=task_data['task_id'],
            name=task_data['name'],
            description=task_data['description'],
            status=TaskStatus(task_data['status']),
            priority=TaskPriority(task_data.get('priority', TaskPriority.NORMAL.value)),
            created_at=parse_datetime(task_data['created_at']),
            started_at=parse_datetime(task_data.get('started_at')),
            completed_at=parse_datetime(task_data.get('completed_at')),
            progress=task_data.get('progress', 0.0),
            result=task_data.get('result'),
            error=task_data.get('error'),
            metadata=task_data.get('metadata', {}),
            retry_count=task_data.get('retry_count', 0),
            max_retries=task_data.get('max_retries', 0),
            tags=task_data.get('tags', [])
        )
    
    def _start_cleanup_timer(self):
        """Avvia timer per cleanup automatico dei task completati."""
        def cleanup_old_tasks():
            while True:
                time.sleep(300)  # Cleanup ogni 5 minuti
                self._cleanup_completed_tasks(max_age_hours=24)
        
        cleanup_thread = threading.Thread(target=cleanup_old_tasks, daemon=True)
        cleanup_thread.start()
    
    def submit_task(self, name: str, description: str, func: Callable, *args, 
                   priority: TaskPriority = TaskPriority.NORMAL, max_retries: int = 0, 
                   tags: List[str] = None, **kwargs) -> str:
        """
        Sottomette un task alla coda per esecuzione asincrona.
        
        Args:
            name: Nome del task
            description: Descrizione del task
            func: Funzione da eseguire
            priority: Priorità del task
            max_retries: Numero massimo di retry
            tags: Tag per categorizzare il task
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
                priority=priority,
                created_at=datetime.now(timezone.utc),
                max_retries=max_retries,
                tags=tags or [],
                metadata={'args': str(args), 'kwargs': str(kwargs)}
            )
            
            self.tasks[task_id] = task
            
            # Aggiungi alla coda con priorità
            heapq.heappush(self.priority_queue, (-priority.value, task_id))
            
            # Avvia il task se ci sono worker disponibili
            self._try_start_next_task()
            
            self._save_tasks()
            logging.info(f"Task sottomesso: {task_id} - {name} (priorità: {priority.name})")
            
            return task_id
    
    def _try_start_next_task(self):
        """Avvia il prossimo task dalla coda se ci sono worker disponibili."""
        if self._running_count >= self.max_workers or not self.priority_queue:
            return
        
        # Prendi il task con priorità più alta
        while self.priority_queue:
            _, task_id = heapq.heappop(self.priority_queue)
            task = self.tasks.get(task_id)
            
            if task and task.status == TaskStatus.PENDING:
                self._start_task(task_id)
                break
    
    def _start_task(self, task_id: str):
        """Avvia l'esecuzione di un task specifico."""
        task = self.tasks[task_id]
        
        # Wrapper per esecuzione task
        def task_wrapper():
            try:
                # Aggiorna status a running
                with self._lock:
                    self.tasks[task_id].status = TaskStatus.RUNNING
                    self.tasks[task_id].started_at = datetime.now(timezone.utc)
                    self._running_count += 1
                    self._save_tasks()
                
                # Crea progress callback
                progress_callback = ProgressCallback(self, task_id)
                
                # Esegui la funzione con callback per progresso
                func_args = eval(task.metadata.get('args', '()'))
                func_kwargs = eval(task.metadata.get('kwargs', '{}'))
                
                # Aggiungi progress callback se la funzione lo supporta
                if 'progress_callback' in func_kwargs or hasattr(func_kwargs.get('func'), '__code__'):
                    func_kwargs['progress_callback'] = progress_callback
                
                result = func(*func_args, **func_kwargs)
                
                # Aggiorna con risultato
                with self._lock:
                    self.tasks[task_id].status = TaskStatus.COMPLETED
                    self.tasks[task_id].completed_at = datetime.now(timezone.utc)
                    self.tasks[task_id].result = result
                    self.tasks[task_id].progress = 100.0
                    self._running_count -= 1
                    self._save_tasks()
                    
                    # Avvia prossimo task
                    self._try_start_next_task()
                
                return result
                
            except Exception as e:
                # Gestione retry
                with self._lock:
                    task = self.tasks[task_id]
                    if task.retry_count < task.max_retries:
                        task.retry_count += 1
                        task.status = TaskStatus.RETRYING
                        task.error = f"Tentativo {task.retry_count}/{task.max_retries}: {str(e)}"
                        
                        # Riaggiunge alla coda per retry
                        heapq.heappush(self.priority_queue, (-task.priority.value, task_id))
                        
                        self._running_count -= 1
                        self._save_tasks()
                        
                        # Avvia prossimo task
                        self._try_start_next_task()
                    else:
                        # Fallimento definitivo
                        task.status = TaskStatus.FAILED
                        task.completed_at = datetime.now(timezone.utc)
                        task.error = str(e)
                        task.result = traceback.format_exc()
                        self._running_count -= 1
                        self._save_tasks()
                        
                        # Avvia prossimo task
                        self._try_start_next_task()
                
                raise
        
        # Sottometti al thread pool
        future = self.executor.submit(task_wrapper)
        self.futures[task_id] = future
    
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
                              duration: int = 10, custom_data: str = "", 
                              priority: str = "normal", max_retries: int = 0,
                              tags: str = "") -> Dict[str, Any]:
        """
        Sottomette un task a lunga esecuzione alla coda asincrona.
        
        Args:
            name: Nome del task
            description: Descrizione del task
            task_type: Tipo di task ('sleep', 'cpu_intensive', 'io_intensive', 'custom', 'progress_demo')
            duration: Durata in secondi per task di tipo sleep
            custom_data: Dati personalizzati per il task
            priority: Priorità del task ('low', 'normal', 'high', 'urgent')
            max_retries: Numero massimo di tentativi in caso di fallimento
            tags: Tag separati da virgola per categorizzare il task
        """
        try:
            # Parse priority
            try:
                priority_enum = TaskPriority[priority.upper()]
            except KeyError:
                return {"success": False, "error": f"Priorità non valida: {priority}"}
            
            # Parse tags
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()] if tags else []
            
            # Funzioni di esempio per diversi tipi di task
            def sleep_task(duration, progress_callback=None):
                """Task di attesa con progresso."""
                import time
                total = duration
                for i in range(total):
                    if progress_callback:
                        progress_callback.update((i / total) * 100, f"Dormendo... {i+1}/{total}")
                    time.sleep(1)
                return f"Task completato dopo {duration} secondi"
            
            def progress_demo_task(duration, progress_callback=None):
                """Demo di task con aggiornamenti di progresso dettagliati."""
                import time
                import random
                
                phases = [
                    ("Inizializzazione", 0.1),
                    ("Preparazione dati", 0.3),
                    ("Elaborazione", 0.5),
                    ("Finalizzazione", 0.1)
                ]
                
                current_progress = 0
                
                for phase_name, phase_duration in phases:
                    phase_steps = int(duration * phase_duration)
                    if progress_callback:
                        progress_callback.update(current_progress, f"Avvio fase: {phase_name}")
                    
                    for step in range(phase_steps):
                        time.sleep(1)
                        step_progress = ((step + 1) / phase_steps) * (phase_duration * 100)
                        current_progress += step_progress / len(phases)
                        
                        if progress_callback:
                            progress_callback.update(
                                current_progress, 
                                f"{phase_name}: {step+1}/{phase_steps}"
                            )
                
                if progress_callback:
                    progress_callback.update(100, "Task completato con successo!")
                
                return {
                    "message": "Demo progresso completata",
                    "phases_completed": len(phases),
                    "total_duration": duration
                }
            
            # Seleziona la funzione in base al tipo
            if task_type == "sleep":
                func = sleep_task
                args = (duration,)
            elif task_type == "progress_demo":
                func = progress_demo_task
                args = (duration,)
            # ...existing task type handling...
            else:
                return {"success": False, "error": f"Tipo task non supportato: {task_type}"}
            
            # Sottometti il task
            task_id = _task_queue.submit_task(
                name, description, func, *args,
                priority=priority_enum, max_retries=max_retries, tags=tag_list
            )
            
            return {
                "success": True,
                "task_id": task_id,
                "name": name,
                "description": description,
                "task_type": task_type,
                "priority": priority,
                "max_retries": max_retries,
                "tags": tag_list,
                "message": "Task sottomesso con successo alla coda asincrona"
            }
            
        except Exception as e:
            logging.error(f"Errore nella sottomissione task: {e}")
            return {"success": False, "error": f"Errore nella sottomissione task: {str(e)}"}

    @mcp.tool()
    def search_tasks(query: str = "", tags: str = "", status_filter: str = "") -> Dict[str, Any]:
        """
        Cerca task per nome, descrizione, tag o status.
        
        Args:
            query: Testo da cercare in nome e descrizione
            tags: Tag separati da virgola da cercare
            status_filter: Filtra per status specifico
        """
        try:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()] if tags else None
            status = status_filter.strip() if status_filter.strip() else None
            
            result = _task_queue.search_tasks(query=query, tags=tag_list, status_filter=status)
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def batch_cancel_tasks(task_ids: str) -> Dict[str, Any]:
        """
        Cancella multipli task in una sola operazione.
        
        Args:
            task_ids: ID dei task separati da virgola
        """
        try:
            id_list = [tid.strip() for tid in task_ids.split(',') if tid.strip()]
            if not id_list:
                return {"success": False, "error": "Nessun task ID fornito"}
            
            result = _task_queue.batch_cancel_tasks(id_list)
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def get_task_logs(task_id: str) -> Dict[str, Any]:
        """
        Ottiene i log dettagliati e la cronologia di un task.
        
        Args:
            task_id: ID del task
        """
        try:
            result = _task_queue.get_task_logs(task_id)
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ...existing tools...