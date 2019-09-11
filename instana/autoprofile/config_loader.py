from .api_request import APIRequest
from .utils import timestamp


class ConfigLoader(object):
    LOAD_DELAY = 2
    LOAD_INTERVAL = 120


    def __init__(self, agent):
        self.apagent = agent
        self.load_timer = None
        self.last_load_ts = 0


    def start(self):
        if self.apagent.get_option('auto_profiling'):
            self.load_timer = self.apagent.schedule(self.LOAD_DELAY, self.LOAD_INTERVAL, self.load)


    def stop(self):
        if self.load_timer:
            self.load_timer.cancel()
            self.load_timer = None


    def load(self, with_interval=False):
        now = timestamp()
        if with_interval and self.last_load_ts > now - self.LOAD_INTERVAL:
            return
    
        self.last_load_ts = now;


        try:
            api_request = APIRequest(self.apagent)
            config = api_request.post('config', {})

            # agent_enabled yes|no
            if 'agent_enabled' in config:
                self.apagent.config.set_agent_enabled(config['agent_enabled'] == 'yes')
            else:
                self.apagent.config.set_agent_enabled(False)

            # profiling_disabled yes|no
            if 'profiling_disabled' in config:
                self.apagent.config.set_profiling_disabled(config['profiling_disabled'] == 'yes')
            else:
                self.apagent.config.set_profiling_disabled(False)


            if self.apagent.config.is_agent_enabled() and not self.apagent.config.is_profiling_disabled():        
                self.apagent.cpu_reporter.start()
                self.apagent.allocation_reporter.start()
                self.apagent.block_reporter.start()
            else:
                self.apagent.cpu_reporter.stop()
                self.apagent.allocation_reporter.stop()
                self.apagent.block_reporter.stop()

            if self.apagent.config.is_agent_enabled():        
                self.apagent.error_reporter.start()
                self.apagent.span_reporter.start()
                self.apagent.process_reporter.start()
                self.apagent.log('AutoProfile Agent activated')
            else:
                self.apagent.error_reporter.stop()
                self.apagent.span_reporter.stop()
                self.apagent.process_reporter.stop()
                self.apagent.log('AutoProfile Agent deactivated')


        except Exception:
            self.apagent.log('AutoProfile Error loading config')
            self.apagent.exception()
