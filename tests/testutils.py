import os


def create_dir_struct(structure, target='.'):
    for name, item in structure.items():
        if isinstance(name, str):
            name = name.encode()

        path = os.path.join(os.path.abspath(target).encode(), name)

        if item is None:
            open(path, 'a').close()

        elif isinstance(item, dict):
            os.makedirs(path)
            if len(item) > 0:
                create_dir_struct(item, path.decode())


def get_dir_struct(target):
    struct = {}
    for item in os.listdir(target):
        path = os.path.join(target, item)
        if os.path.isdir(path):
            struct[item] = get_dir_struct(path)
        else:
            struct[item] = None

    return struct
