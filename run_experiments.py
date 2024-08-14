import sys
import os
import gc
import signal
import multiprocessing
from main import run

def get_input_files(input_dir):
    '''Get the input files from input dir'''
    input_files = []
    for item in os.listdir(input_dir):
        item_path = os.path.join(input_dir, item)
        if (os.path.isfile(item_path)):
            input_files.append(item_path)
    
    input_files = sorted(input_files)
    return input_files
            

def run_model(input_files, output_dir, code, prefix=""):
    '''Run the model for all input files and save on output direcotry. The results will be saved on an output directory with 
    name = prefix + basename(input_file)'''
    i = 0
    for input_file in input_files:
        
        file_base_name = os.path.basename(input_file).split(".")[0]
        output_local = os.path.join(output_dir, prefix + "_" + file_base_name)
        args = (input_file, output_local, code)
        
        # Create a new process to avoid SIGKILL 
        # if gurobi have out of memory  error
        p = multiprocessing.Process(target=run, args=(args,))
        p.start()
        p.join()
        print(p)

        if (p.exitcode == signal.SIGKILL):
            file_name = os.path.join(output_local, "error.log")
            with open(file_name, "w") as out_err:
                out_err.write("Processo morto. Provavelmente memória estourou.")

        gc.collect()
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

    # Run model for standard formulation
    run_model(input_files, output_dir, 0, "standard")
    # Run model for benders formulation
    run_model(input_files, output_dir, 1, "benders")