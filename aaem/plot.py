"""
plot.py

ross spicer

plotting functions
"""
import matplotlib.pyplot as plt
import numpy as np
from colors import colors, red, jet
from pandas import DataFrame ,read_csv


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
    
    add_vertical_line(axes, 3,'a line')
    
    add_line(ax2, x, -1*x, 'y = -x on a second y-axis', colors[3])

    add_bars(axes, [1,3,5,7,9], [2,4,6,8,10], None, color = colors[4])
    
    # named bars --------------------------------------------------------------
    #~ add_named_bars(axes, ('a', 'b', 'c', 'd', '3'),
                      #~ (1,2,3,4,5), 'bar test', colors[5])
    #~ # -------------------------------------------------------------------------
    
    #~ # annotations ---------- in development -----------------------------------
    #~ axes.annotate('a line', xy=(3, 25), xytext=(4, 25.1),
            #~ arrowprops=dict(facecolor='black', shrink=0.05, width=1,headwidth=4),
            #~ )
    #~ # -------------------------------------------------------------------------
    
    # dataframe ---------------------------------------------------------------
    #~ df = DataFrame({"year":[2001,2002,2003,2004,2005],
                    #~ "d1":  [1,2,3,4,5],
                    #~ "d2":  [1,4,9,16,25],
                    #~ "d3":  [3,4,6,7,8]}).set_index("year")
    #~ plot_dataframe(ax2,df,axes,["d1"])
    # -------------------------------------------------------------------------
    
    #~ add_bars_2(axes,('a','b','c','d','e'),{'gr1':(1,2,3,4,5),
                                           #~ 'gr2':(3,2,5,7,1),
                                           #~ 'gr3':(5,4,3,2,1),
                                           #~ 'gr4':(5,4,3,2,1)})

    axes.set_yticklabels(axes.get_yticks(), verticalalignment = 'bottom')
    ax2.set_yticklabels(ax2.get_yticks(), verticalalignment = 'bottom')
    
    create_legend(fig)
    #~ plt.show()
    show(fig)
    save(fig, "polt_test.png")
    
    return fig
    
def test_elec (e_file, com):
    df = read_csv(e_file,comment = '#',index_col = 0)
    df2 = df[['population','total_electricity_consumed [kWh/year]',
              'total_electricity_generation [kWh/year]']]
    fig, ax = setup_fig( com + ' Electricity Forecast','years','population')
  
    
    ax1 = add_yaxis(fig,'kWh')
    #~ fig, axes = plt.subplots(2,1)
    #~ plot_dataframe(axes[1],df2,axes[0],['population'],
                   #~ col_map = {'population':'population',
                #~ 'total_electricity_consumed [kWh/year]':'consumption',
                #~ 'total_electricity_generation [kWh/year]':'generation'})
    
    plot_dataframe(ax1,df2,ax,['population'],
                   column_map = {'population':'population',
                'total_electricity_consumed [kWh/year]':'consumption',
                'total_electricity_generation [kWh/year]':'generation'})
    ax1.set_yticklabels(ax1.get_yticks().astype(int),rotation=0)
    fig.subplots_adjust(right=.85)
    fig.subplots_adjust(left=.12)
    add_vertical_line(ax,2015, 'forecasting starts' )
    
    ax.set_yticklabels(ax.get_yticks().astype(int), 
                       verticalalignment = 'bottom')
    ax1.set_yticklabels(ax1.get_yticks().astype(int),
                        verticalalignment = 'bottom')
    
    create_legend(fig)
    plt.show()
    fig.savefig(com+".png")
    
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

def add_line(ax, x, y, label, 
             color=red, marker='o', fill = False):
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
    ax.plot(x, y, label = label, color = color, marker = marker, linewidth=1.5)
    
    if type(fill) is not bool or fill == True:
        if type(fill) is bool:
            fill = 0
        ax.fill_between(x,y,fill,color=color, alpha = .5)

def add_bars (ax, nums, heights, label, 
              width = 1, color = red, direction = 'vertical', error = None):
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
        ax.barh(nums, heights, width, label=label, color = color, yerr = error)
    else:
        ax.bar(nums, heights, width, label=label, color = color, yerr = error)
        
def add_vertical_bars(ax, categories, values):
    """
    create a bar graph with vertical bars 
    
    pre:
        ax: <matplotlib axes> axes to plot on
        categories: <list> list of categories to plot
        values: <dict> a dictionary of sets of values. {"label 1":[values],
                                                        "label 2":[values],
                                                        ...}
    post:
        plots a bar graph on ax
    """
    num = len(categories)
    pos = np.arange(num)
    count = 0
    width = .80/len(values) 
    for key in values:
        ax.bar(.10+ pos + count*width, values[key],width,
               color = colors[count],label = key) 
        count += 1
    ax.set_xticks(.10+ pos + .8/2)
    ax.set_xticklabels(categories)
    
def add_named_bars (ax, categories, values, label, 
                    color=red, direction = 'horizontal'):
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
    pos = np.arange(len(categories)) + .5
    if direction == 'vertical':
        ax.bar(pos, values, label = label, color=color,align='center')
        ax.set_xticks(pos)
        ax.set_xticklabels(categories)
    else:
        ax.barh(pos, values, label=label,color=color,align='center')
        ax.set_yticks(pos)
        ax.set_yticklabels(categories)
        
def create_legend(fig,space = .15):
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
    ax0.set_position([pos.x0, pos.y0+space*pos.height, pos.width, pos.height*(1-space)])
    
    for ax in axes[1:]:
        lines += ax.get_legend_handles_labels()[0]
        labels += ax.get_legend_handles_labels()[1]
        ax.set_position(ax0.get_position())
        
    ax0.legend(lines, labels, 
               bbox_to_anchor = (0.5, -.1),loc='upper center',
               ncol=2)

def add_vertical_line (ax, position,text = None):
    """
    add a vertical line to the plot
    
    pre:
        ax: <matplotlib axes> the axes
        position: <number> the position
    post:
        line is added to axes at potions( x= position)
    """
    ax.axvline(position, color=jet, linestyle='--')
    if text:
        ypos = (ax.get_ylim()[1] - ax.get_ylim()[0])*.10 + ax.get_ylim()[0]
        xpos = (ax.get_xlim()[1] - ax.get_xlim()[0])*.10
        ax.annotate(text, xy=(position, ypos), xytext=(position +xpos, ypos),
        arrowprops=dict(facecolor='black', shrink=0.05, width=1,headwidth=4),
        )

def plot_dataframe(ax, dataframe, 
                   ax0 = None, ax0_cols = None, 
                   column_map = None):
    """
        Plots the columns in a pandas.DataFrame on ax. If ax0 and ax0_cols are 
    provided dataframe[ax0_cols] will be plotted on ax0 before all columns not 
    in ax0_cols are plotted on ax.
    
    pre:
        ax: <matplotlib axes> axes to plot on
        dataframe: <pandas.DataFrame> dataframe to plot. 
                   Values in columns must be numbers.
        ax0: (optional) <matplotlib axes> axes to plot on. 
        ax0_cols: (optional) <list like> columns to plot on ax0
        column_map: (optional) <dict> map of column names to labels
        
    post:
        Plots the columns in a pandas.DataFrame on ax. If ax0 and ax0_cols are 
    provided dataframe[ax0_cols] will be plotted on ax0 before all columns not 
    in ax0_cols are plotted on ax.
    """
    c_index = 0
    keys = set(dataframe.keys())
    
    if column_map is None:
        column_map = {} 
        for c in keys:
            column_map[c] = c
    
    x = dataframe.index
    if ax0:
        for col in ax0_cols:
            add_line(ax0,x,dataframe[col].values,column_map[col],
                           color=colors[c_index],marker='o')
            c_index += 1
        ax0.set_ylabel(ax0.get_ylabel()+' (circles)')
        keys = keys.difference(ax0_cols)

    for col in  keys:
        add_line(ax,x,dataframe[col].values,column_map[col],
                      color=colors[c_index],marker='^')
        c_index += 1
    ax.set_ylabel(ax.get_ylabel()+' (triangles)')

def save (fig, filename):
    """ 
    saves the figure
    
    pre: 
        fig: <matplotlib figure> the figure to save
        filename: <string> a file name that is a valid image type
    psot:
        the figure is saved as filename
    """
    axes = fig.get_axes()
    for ax in axes:
        ax.set_yticklabels(ax.get_yticks().astype(int), 
                       verticalalignment = 'bottom')
    fig.savefig(filename)
    
def show (fig):
    """
    show the figure to the screen. can olny be done once
    
    pre: 
        fig: <matplotlib figure> the figure to save
    post:
        figure is displayed.
    """
    fig.show()
    

def clear(fig):
    """
    clear the figure
    
    pre:
        fig: <matplotlib figure> the figure 
    post:
        the figure is cleared and deleted.
    """
    fig.clear()
    del(fig)
    
