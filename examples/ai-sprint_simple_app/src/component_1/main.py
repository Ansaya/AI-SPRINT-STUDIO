import os

from aisprint.annotations import annotation

@annotation({'component_name': {'name': 'C1'}, 'exec_time': {'local_time_thr': 5}})
def main(args):
    print("Hello! I'm an example component C1!")

if __name__ == '__main__':
    main({})
