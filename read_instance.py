import os


def read(file_name):
    '''
    Returns a dictionary with the following keys for a 2D-BPP or 2D-CSP instance:
        1. name: instance name
        2. width: width of each bin
        3. height: height of each bin
        4. items: list containing a dictionary with the following keys:
            4.1. id: item id
            4.2. width: width of the item
            4.3. height: height of the item
            4.4. demand: number of repetitions of the item
    All values are considered to be integer. The instance format must follow the 2DPackLib format (https://site.unibo.it/operations-research/en/research/2dpacklib).
    '''
    instance_data = {}
    with open(file_name, "r") as input_file:
        instance_data["name"] = os.path.basename(file_name)
        line = input_file.readline()
        instance_data["number_of_items"] = int(line.strip())
        line = input_file.readline()
        instance_data["width"] = int(line.split()[0].strip())
        line = input_file.readline()
        instance_data["height"] = int(line.split()[1].strip())
        instance_data["items"] = []
        for i in range(instance_data["number_of_items"]):
            line = input_file.readline()
            line = line.split()
            if (len(line) < 1):
                continue
            data = {}
            data["id"] = int(line[0].strip())
            data["width"] = int(line[1].strip())
            data["height"] = int(line[2].strip())
            data["demand"] = int(line[3].strip())

            instance_data["items"].append(data)

    return instance_data
