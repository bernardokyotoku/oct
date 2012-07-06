import logging
loglevel = "INFO"
numeric_level = getattr(logging, loglevel.upper(), None)
if not isinstance(numeric_level, int):
    raise ValueError('Invalid log level: %s' % loglevel)
logging.basicConfig(level=numeric_level)
logging.warning("what is this warning?")
logging.info("this is an info")

logger = logging.getLogger(__name__)
logger.warning("what is this warning?")
