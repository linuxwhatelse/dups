import os


def create_dir_struct(structure, target='.'):
    for name, item in structure.items():
        path = os.path.join(os.path.abspath(target).encode(), name.encode())

        if item is None:
            open(path, 'a').close()

        elif isinstance(item, dict):
            os.makedirs(path)
            if len(item) > 0:
                create_dir_struct(path.decode(), item)


def get_dir_struct(target):
    struct = {}
    for item in os.listdir(target):
        path = os.path.join(target, item)
        if os.path.isdir(path):
            struct[item] = get_dir_struct(path)
        else:
            struct[item] = None

    return struct
