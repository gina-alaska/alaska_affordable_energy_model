"""
plot.py

ross spicer

plotting functions
"""
import matplotlib.pyplot as plt
from pylab import rand
import numpy as np
from colors import colors, red, jet
from pandas import DataFrame 


def test():
    """
    test some of the function
    """
    x = np.linspace(0,10)
    
    fig, axes = setup_fig('test','x','y1')
    ax2 = add_yaxis(fig,'y2')
    
    add_line(axes, x, x, 'y = x', colors[0], fill = True)
    add_line(axes, x, 2*x, 'y = 2x', colors[1], fill = x)
    add_line(axes, x, x*3, 'y = 3x', colors[2], fill = 2*x)
    
    add_vertical_line(axes, 3)
    
    add_line(ax2, x, -1*x, 'y = -x on a second y-axis', colors[3])

    add_bars(axes, [1,3,5,7,9], [2,4,6,8,10], color = colors[4])
    
    # named bars --------------------------------------------------------------
    #~ add_named_bars(axes, ('a', 'b', 'c', 'd', 'd'),
                      #~ 3+10*rand(4), colors[5])
    # -------------------------------------------------------------------------
    
    # annotations ---------- in development -----------------------------------
    #~ axes.annotate('a line', xy=(3, 25), xytext=(4, 25.1),
            #~ arrowprops=dict(facecolor='black', shrink=0.05, width=1,headwidth=4),
            #~ )
    # -------------------------------------------------------------------------
    
    # dataframe ---------------------------------------------------------------
    #~ df = DataFrame({"year":[2001,2002,2003,2004,2005],
                    #~ "d1":  [1,2,3,4,5],
                    #~ "d2":  [1,4,9,16,25],
                    #~ "d3":  [3,4,6,7,8]}).set_index("year")
    #~ plot_dataframe(ax2,df,axes,["d1"])
    # -------------------------------------------------------------------------
    
    create_legend(fig)
    plt.show()
    
    fig.savefig("polt_test.png")
    
    return fig
    
def plot_dataframe(ax, dataframe, ax0 = None, ax0_cols = None):
    c_index = 0
    keys = set(dataframe.keys())
    
    x = dataframe.index
    if ax0:
        for col in ax0_cols:
            add_line(ax0,x,dataframe[col].values,col,color=colors[c_index])
            c_index += 1
        keys = keys.difference(ax0_cols)

    for col in  keys:
        add_line(ax,x,dataframe[col].values,col,color=colors[c_index])
        c_index += 1
            
    
    
def setup_fig(title, x_label, y_label):
    """
    set-up the figure for the the plots
    
    pre-conditions:
        title: <string> the title of the plot
        x_label: <string> x axis label
        y_label: <string> y axis label
    post-conditions:
        returns the figure and the axes 
    """
    fig, axes = plt.subplots()
    axes.set_title(title)
    axes.set_xlabel(x_label)
    axes.set_ylabel(y_label, color='black')
    return fig, axes
    
def add_yaxis (fig, label):
    """
    adds a second y axis 
    
    pre:
        fig: <matplotlib figure> the figure
        label: <string> new axis label
    post:
        returns the new axis and the figure has been updated with it.
    """
    fig.subplots_adjust(left=.1)
    ax = fig.get_axes()[0]
    new_ax = ax.twinx()
    new_ax.set_ylabel(label, color='black')
    return new_ax

def add_line(ax, x, y, label='test', color=red, marker='o', fill = False):
    """
    add a line to the axes 
    
    pre:
        ax: <matplotlib axes> axes to plot on
        x: <array like> the x values
        y: <array like> the y values
        label: <string> label for the line
        color: <rgb triplet> a color rgb values between 0,1
        marker: <matplotlib marker> a marker
        fill: <bool or array like> If true fills to y = 0, otherwise fills 
                                                        to line y[n] = fill[n] 
    post:
        line is plotted on axis
    """
    ax.plot(x, y, label = label, color = color, marker = marker)
    
    if type(fill) is not bool or fill == True:
        if type(fill) is bool:
            fill = 0
        ax.fill_between(x,y,fill,color=color, alpha = .5)

def add_bars (ax, nums, heights, width = 1, 
              color = red, direction = 'vertical', error = None):
    """
    add bars to axes 
    
    pre:
        ax: <matplotlib axes> axes to plot on
        numbers: <array like> the numbers to start bars at
        heights: <array like> the heights of the bars
        width: <number> width of the bar (defaults to 1)
        color: <rgb triplet> a color rgb values between 0,1 (defaults to red)
        direction: <sting> 'horizontal' or 'vertical'
        error: error values
    post:
        bars are plotted on axis
    """
    if direction == 'horizontal':
        ax.barh(nums, heights, width, color = color, yerr = error)
    else:
        ax.bar(nums, heights, width, color = color, yerr = error)
    
def add_named_bars (ax, labels, values, color=red, direction = 'horizontal'):
    """
    add named bars to axes 
    
    pre:
        ax: <matplotlib axes> axes to plot on
        labels: <array>  labels of bars
        values: <array like> values of each label
        color: <rgb triplet> a color rgb values between 0,1 (defaults to red)
        direction: <sting> 'horizontal' or 'vertical'
    post:
        bars are plotted on axis and labeled
    """
    pos = np.arange(len(labels)) + .5
    if direction == 'vertical':
        ax.bar(pos, values, color=color,align='center')
        ax.set_xticks(pos)
        ax.set_xticklabels(labels)
    else:
        ax.barh(pos, values, color=color,align='center')
        ax.set_yticks(pos)
        ax.set_yticklabels(labels)
        
def create_legend(fig):
    """
    create a legend form the line labels and place it below the plot
    
    pre:
        fig: the figure
    post:
        legend is placed below the plot
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

def add_vertical_line (ax, position):
    """
    add a vertical line to the plot
    
    pre:
        ax: <matplotlib axes> the axes
        position: <number> the position
    post:
        line is added to axes at potions( x= position)
    """
    ax.axvline(position, color=jet, linestyle='--')
