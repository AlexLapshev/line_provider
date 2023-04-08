import os


class QueueSettings:
    port = os.getenv("RMQ_PORT", 5672)
    host = os.getenv("RMQ_PORT", "localhost")
    queue_name_events = os.getenv("RMQ_Q_NAME_EVENTS", "events")
    queue_name_bets = os.getenv("RMQ_Q_NAME_BETS", "bets")
    username = os.getenv("RMQ_USER", "guest")
    password = os.getenv("RMQ_PASS", "guest")
