"""
plot.py

ross spicer

plotting functions
"""
import matplotlib.pyplot as plt
import numpy as np
from colors import colors



def test():
    x = np.linspace(0,10)
    
    fig, axes = setup_fig('test','x','y1')

    ax2 = add_yaxis(fig,axes,'y2')

    
    add_line(x,x,axes, 'y = x',colors[0])
    add_line(x,20*x,axes, 'y = 20x',colors[4])
    add_line(x,x*3,axes, 'y = 3x',colors[6])
    
    add_line(x,-1*x,ax2,'y = -x on a seond set of axes',colors[10])
    
    create_legend(fig)
    plt.show()
    #~ plt.savefig("polt_test.png")
    
    return fig
    
def setup_fig(title,x_label,y_label):
    """ """
    fig, axes = plt.subplots()
    axes.set_title(title)
    axes.set_xlabel(x_label)
    axes.set_ylabel(y_label, color='black')
    return fig, axes
    
def add_yaxis (fig, ax, label ):
    """"""
    fig.subplots_adjust(left=.1)
    new_ax = ax.twinx()
    new_ax.set_ylabel(label, color='black')
    return new_ax

def add_line(x,y, ax, label = 'test', color = 'red', marker = 'o', fill = False):
    """
    """
    ax.plot(x,y, label = label, color = color, marker = marker)
    
    if fill:
        ax.fill_between(x,y,color=color, alpha = .5)
        
def create_legend(fig):
    """
    """
    axes = fig.get_axes()
    
    ax0 = axes[0]
    lines, labels = ax0.get_legend_handles_labels()
    pos = ax0.get_position()
    ax0.set_position([pos.x0, pos.y0+.15*pos.height, pos.width, pos.height*.85])
    
    for ax in axes[1:]:
        lines += ax.get_legend_handles_labels()[0]
        labels += ax.get_legend_handles_labels()[1]
        ax.set_position(ax0.get_position())
        
    ax0.legend(lines, labels, 
               bbox_to_anchor = (0.5, -.31),loc='lower center',
               ncol=2)
    
