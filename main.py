import sys
from model_manager import *
from read_instance import read


def run(argv):
    if (len(argv) < 2):
        print("Needs instance name")
        exit(0)
    
    instance_data = read(argv[1])
    print(instance_data["items"])

    print(create_model())


if __name__ == "__main__":
    run(sys.argv)







