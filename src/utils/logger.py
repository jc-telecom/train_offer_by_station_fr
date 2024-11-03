import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Vérifier si le logger a déjà des handlers pour éviter les doublons
if logger.handlers:
    logger.handlers.clear()

handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)


def log_message(message, logger_container=False):
    if logger_container:
        logger_container.code(message)
    logger.info(message)
