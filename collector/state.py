import time


# Время запуска процесса collector.
START_TIME = time.time()


collector_state = {
    "status": "STARTING",
    "healthy": False,
    "last_success": 0,
    "last_attempt": 0,
    "last_error": "",
    "last_error_time": 0,
    "version": "1.3.0",
}


def set_attempt():
    """Сохранить время начала очередной попытки опроса FMC."""
    collector_state["last_attempt"] = int(time.time())


def set_success():
    """Отметить успешно завершённый цикл сбора данных."""
    now = int(time.time())

    collector_state["status"] = "HEALTHY"
    collector_state["healthy"] = True
    collector_state["last_attempt"] = now
    collector_state["last_success"] = now
    collector_state["last_error"] = ""
    collector_state["last_error_time"] = 0


def set_error(error):
    """Сохранить ошибку последнего цикла сбора данных."""
    now = int(time.time())

    collector_state["status"] = "DEGRADED"
    collector_state["healthy"] = False
    collector_state["last_error"] = str(error)
    collector_state["last_error_time"] = now
