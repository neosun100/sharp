"""GPU Manager with auto-offload for SHARP model."""

import gc
import logging
import threading
import time
from pathlib import Path
from typing import Callable, Optional

import torch

LOGGER = logging.getLogger(__name__)


class GPUManager:
    """Manages GPU resources with automatic offloading."""

    def __init__(self, idle_timeout: int = 300):
        self.idle_timeout = idle_timeout
        self.model = None
        self.device = None
        self.last_used = 0
        self.lock = threading.Lock()
        self._monitor_thread = None
        self._stop_monitor = False

    def _detect_device(self) -> torch.device:
        if torch.cuda.is_available():
            return torch.device("cuda")
        elif hasattr(torch, "mps") and torch.mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")

    def get_model(self, load_func: Callable) -> torch.nn.Module:
        """Get model, loading if necessary."""
        with self.lock:
            self.last_used = time.time()
            if self.model is None:
                LOGGER.info("Loading model to GPU...")
                self.device = self._detect_device()
                self.model = load_func(self.device)
                self._start_monitor()
            return self.model

    def _start_monitor(self):
        if self._monitor_thread is None or not self._monitor_thread.is_alive():
            self._stop_monitor = False
            self._monitor_thread = threading.Thread(target=self._monitor_idle, daemon=True)
            self._monitor_thread.start()

    def _monitor_idle(self):
        while not self._stop_monitor:
            time.sleep(30)
            with self.lock:
                if self.model and (time.time() - self.last_used) > self.idle_timeout:
                    LOGGER.info("GPU idle timeout, offloading model...")
                    self._offload_internal()
                    break

    def _offload_internal(self):
        """Internal offload without lock."""
        if self.model:
            del self.model
            self.model = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()

    def force_offload(self):
        """Force offload model from GPU."""
        with self.lock:
            self._offload_internal()
            LOGGER.info("Model offloaded from GPU")

    def get_status(self) -> dict:
        """Get GPU status."""
        status = {
            "model_loaded": self.model is not None,
            "device": str(self.device) if self.device else None,
            "idle_timeout": self.idle_timeout,
        }
        if torch.cuda.is_available():
            status["gpu_memory_allocated_mb"] = round(torch.cuda.memory_allocated() / 1024**2, 2)
            status["gpu_memory_reserved_mb"] = round(torch.cuda.memory_reserved() / 1024**2, 2)
        return status


# Global instance
gpu_manager = GPUManager(idle_timeout=int(__import__("os").environ.get("GPU_IDLE_TIMEOUT", 300)))
