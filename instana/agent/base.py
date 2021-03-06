"""
Base class for all the agent flavors
"""
import logging
import requests
from ..log import logger


class BaseAgent(object):
    """ Base class for all agent flavors """
    client = None
    sensor = None
    options = None

    def __init__(self):
        self.client = requests.Session()

    def update_log_level(self):
        """ Uses the value in <self.log_level> to update the global logger  """
        if self.options is None or self.options.log_level not in [logging.DEBUG,
                                                                  logging.INFO,
                                                                  logging.WARN,
                                                                  logging.ERROR]:
            logger.warning("BaseAgent.update_log_level: Unknown log level set")
            return

        logger.setLevel(self.options.log_level)

