import sys
import os
from main import run

def get_input_files(input_dir):
    input_files = []
    for item in os.listdir(input_dir):
        item_path = os.path.join(input_dir, item)
        if (os.path.isfile(item_path)):
            input_files.append(item_path)
    
    input_files = sorted(input_files)
    return input_files


def print_arguments(args):
    print("ARGUMENTS: ")
    print("\tINPUT FILE:\t", args[0]) 
    print("\tCONFIGURATION FILE:\t", args[1])
    print("\tOUTPUT RESULT PATH:\t", args[2])
    print("\tOUTPUT MODEL PATH:\t", args[3])
    print("\tLOG FILE PATH:\t", args[4])
            

def run_model(input_files, output_dir, code, prefix=""):
    i = 0
    for input_file in input_files:
        file_base_name = os.path.basename(input_file).split(".")[0]
        output_local = os.path.join(output_dir, prefix + "_" + file_base_name)
        run([input_file, output_local, code])
        i += 1

if __name__=="__main__":
    if (len(sys.argv) < 3):
        print("Needs:")
        print(" 1. Inputs Directory")
        print(" 2. Outputs Directory")
        exit(0)

    input_dir = sys.argv[1]
    output_dir = sys.argv[2]

    input_files = get_input_files(input_dir)


    run_model(input_files, output_dir, 0, "standard")
    run_model(input_files, output_dir, 1, "benders")