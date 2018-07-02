import os


def get_dir_struct(target):
    struct = {}
    for item in os.listdir(target):
        path = os.path.join(target, item)
        if os.path.isdir(path):
            struct[item] = get_dir_struct(path)
        else:
            struct[item] = None

    return struct
