import logging

logging.basicConfig(filename="logs.log",
                    format='%(asctime)s %(message)s',
                    filemode='w')


logger = logging.getLogger()

logger.setLevel(logging.DEBUG)


def ErrorLogger(exception: str) -> Exception:
    logger.error(exception)
    raise Exception(exception)


def EventLogger(message: str) -> None:
    logger.info(message)
