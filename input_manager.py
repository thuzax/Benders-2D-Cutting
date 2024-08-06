import os
import copy


def read(file_name):
    '''
    :param file_name: 2d-bpp or 2d-csp file path.

    All values are considered to be integer. The instance format must follow the 2DPackLib format (https://site.unibo.it/operations-research/en/research/2dpacklib).

    :return (instance_data, items_id_mapping): dictionary with the instance data and a dictionary mapping the ids of the original input with fake ids to consider demand 1 for all items
        
        The instance_data dictionary is structured as follow:
        - instance_data["name"]: instance name
        - instance_data["width"]: width of each bin
        - instance_data["height"]: height of each bin
        - instance_data["items"]: list containing dictionaries that represents the items

        An item dictionary is structured as follow:
        - instance_data["items"]["id"]: item id
        - instance_data["items"]["width"]: width of the item
        - instance_data["items"]["height"]: height of the item
        - instance_data["items"]["demand"]: number of repetitions of the item
    '''

    instance_data = {}
    
    items_id_mapping = {}

    with open(file_name, "r") as input_file:
    
        instance_data["name"] = os.path.basename(file_name)
    
        line = input_file.readline()
        instance_data["number_of_items"] = int(line.strip())
    
        line = input_file.readline()
        instance_data["width"] = int(line.split()[0].strip())
        instance_data["height"] = int(line.split()[1].strip())
    
        instance_data["items"] = []
        fake_id = 1
        
        for i in range(instance_data["number_of_items"]):

            line = input_file.readline()
            line = line.split()

            if (len(line) < 1):
                continue
            
            data = {}
            
            true_id = int(line[0].strip())
            
            data["width"] = int(line[1].strip())
            data["height"] = int(line[2].strip())
            demand = int(line[3].strip())

            for j in range(demand):
                
                items_id_mapping[fake_id] = true_id
                data["id"] = fake_id
                fake_id += 1
                instance_data["items"].append(copy.deepcopy(data))

    return (instance_data, items_id_mapping)
