import os
import numpy
from matplotlib import pyplot as plt


def draw_solution(
    items, 
    items_ids_mapping, 
    x, 
    y, 
    max_width, 
    max_height, 
    output_directory,
    bin_id,
    prefix
):
    '''Plot the solution by drawing the items on the bins'''

    figures_path = file_path = os.path.join(
        output_directory, 
        "out_figures"
    )

    if (not os.path.exists(figures_path)):
        os.mkdir(figures_path)
    
    if (len(x) > 0):
        plt.axis('equal')

        figure, ax = plt.subplots()

        figure.set_figwidth(max_width)
        figure.set_figheight(max_height)
        ax.grid(True)

        ax.set_xticks(range(max_width+1))
        ax.set_yticks(range(max_height+1))

        for i in items.keys():
            item_id = items[i]["id"]
            
            axis_x = [
                x[item_id], x[item_id] + items[i]["width"],  
                x[item_id] + items[i]["width"], x[item_id], x[item_id]
            ]
            
            axis_y = [
                y[item_id], y[item_id], y[item_id] + items[i]["height"], 
                y[item_id] + items[i]["height"], y[item_id]
            ]

            axis_x = numpy.array(axis_x)
            axis_y = numpy.array(axis_y)

            plt.xlim(0, max_width)
            plt.ylim(0, max_height)

            plt.plot(axis_x, axis_y, linewidth=2, color="black")
            plt.fill(axis_x, axis_y, alpha=0.7, color="gray")
                
            plt.text(
                x[item_id] + (items[i]["width"]/2) - (items[i]["width"]/50), 
                y[item_id] + (items[i]["height"]/2) - (items[i]["height"]/50), 
                items_ids_mapping[item_id], 
                size=20, 
                color='black'
            )

        
        file_path = os.path.join(
            figures_path,
            prefix + str(bin_id) + ".png"
        )

        plt.savefig(file_path)
        plt.close()
        plt.clf()

    return