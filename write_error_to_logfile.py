import sys
import os
#from source import main
import logging
from datetime import datetime

logging.getLogger('chardet.charsetprober').setLevel(logging.INFO)

dateTimeObj = datetime.now()
timestampStr = dateTimeObj.strftime("%d-%b-%Y")

logfile = 'logfiles_debugging/logfile_' + timestampStr

#main.initialize_logger(logfile, 'debug', 'debug', allow_override=True)
logger = logging.getLogger()

# logger default setzen?

def write(e):
    exc_type, _exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    error_message = 'Error! Code: {c}, Message, {m}, Type, {t}, File, {f}, Line {line}'.format(c=type(e).__name__, m=str(e), t=exc_type, f=fname, line=exc_tb.tb_lineno)
    logger.debug(error_message)


def comment(comment_string):
    logger.debug(comment_string)

# logger mit Pfadübergabe setzen!!!
