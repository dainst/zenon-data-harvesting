import os


def create_path(path: str):
    path_string = ''
    for directory in path.split('/'):
        if not path_string:
            if directory not in os.listdir('.'):
                os.mkdir(directory)
        else:
            if directory not in os.listdir(path_string):
                os.mkdir(path_string + directory)
        path_string += directory + '/'
