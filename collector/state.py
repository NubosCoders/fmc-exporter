import time
from threading import Lock


# Время запуска процесса collector.
START_TIME = time.time()


collector_state = {
    "status": "STARTING",
    "healthy": False,
    "fmc_connected": False,
    "last_attempt": 0,
    "last_success": 0,
    "last_error": "",
    "last_error_time": 0,
    "consecutive_failures": 0,
    "total_failures": 0,
    "version": "1.4.0",
}
state_lock = Lock()


def get_state():
    with state_lock:
        return collector_state.copy()


def set_attempt():
    """Сохранить время начала очередной попытки опроса FMC."""
    with state_lock:
        collector_state["last_attempt"] = int(time.time())


def set_success():
    """Отметить успешно завершённый цикл сбора данных."""
    now = int(time.time())

    with state_lock:
        collector_state["status"] = "HEALTHY"
        collector_state["healthy"] = True
        collector_state["fmc_connected"] = True
        collector_state["last_success"] = now
        collector_state["last_error"] = ""
        collector_state["last_error_time"] = 0
        collector_state["consecutive_failures"] = 0


def set_error(error):
    """Сохранить ошибку последнего цикла сбора данных."""
    now = int(time.time())

    with state_lock:
        collector_state["status"] = "DEGRADED"
        collector_state["healthy"] = False
        collector_state["fmc_connected"] = False
        collector_state["last_error"] = str(error)
        collector_state["last_error_time"] = now
        collector_state["consecutive_failures"] += 1
        collector_state["total_failures"] += 1
