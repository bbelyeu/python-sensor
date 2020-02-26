import sys
import threading
import copy

from .api_request import APIRequest
from .utils import timestamp, base64_encode
from ..log import logger


class MessageQueue(object):
    FLUSH_INTERVAL = 5;
    MESSAGE_TTL = 10 * 60


    def __init__(self, agent):
        self.apagent = agent
        self.queue = []
        self.queue_lock = threading.Lock()
        self.flush_timer = None
        self.backoff_seconds = 0
        self.last_flush_ts = 0


    def start(self):
        if self.apagent.get_option('auto_profiling'):
            self.flush_timer = self.apagent.schedule(self.FLUSH_INTERVAL, self.FLUSH_INTERVAL, self.flush)


    def stop(self):
        if self.flush_timer:
            self.flush_timer.cancel()
            self.flush_timer = None
            

    def add(self, topic, message):
        entry = {
            'topic': topic,
            'content': message,
            'added_at': timestamp()
        }

        with self.queue_lock:
            self.queue.append(entry)

        self.apagent.log('AutoProfile: Added message to the queue for topic: ' + topic)
        self.apagent.log(message)


    def flush(self, with_interval=False):
        if len(self.queue) == 0:
            return

        now = timestamp()
        if with_interval and self.last_flush_ts > now - self.FLUSH_INTERVAL:
            return

        # flush only if backoff time is elapsed
        if self.last_flush_ts + self.backoff_seconds > now:
            return

        # expire old messages
        with self.queue_lock:
            self.queue = [m for m in self.queue if m['added_at'] >= now - self.MESSAGE_TTL]
    
        # read queue
        outgoing = None
        with self.queue_lock:
            outgoing = self.queue
            self.queue = []

        # remove added_at
        outgoing_copy = copy.deepcopy(outgoing)
        for m in outgoing_copy:
            del m['added_at']

        payload = {
            'messages': outgoing_copy
        }

        self.last_flush_ts = now

        try:
            # api_request = APIRequest(self.apagent)
            # api_request.post('upload', payload)

            logger.debug("Reporting profiles: %s" % payload)
            from ..singletons import agent
            import os

            req_body = {
                'runtime': 'python',
                'pid': os.getpid(),
                'run_id': self.apagent.run_id,
                'run_ts': self.apagent.run_ts,
                'sent_at': timestamp(),
                'payload': payload,
            }

            agent.report_profiles(req_body)

            # reset backoff
            self.backoff_seconds = 0
        except Exception:
            self.apagent.log('AutoProfile: Error uploading messages to dashboard, backing off next upload')
            self.apagent.exception()

            self.queue_lock.acquire()
            self.queue[:0] = outgoing
            self.queue_lock.release()

            # increase backoff up to 1 minute
            if self.backoff_seconds == 0:
                self.backoff_seconds = 10
            elif self.backoff_seconds * 2 < 60:
                self.backoff_seconds *= 2

