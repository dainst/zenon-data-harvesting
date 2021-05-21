import sys
import os


def handle_error_and_raise(e):
    #print('Error! Code: {c}, Message, {m}'.format(c=type(e).__name__, m=str(e)))
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    #print(exc_type, fname, exc_tb.tb_lineno)
    raise e
