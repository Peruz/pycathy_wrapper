#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Plotting functions for pyCATHY (2D and 3D)

Plotting:
    - output files
    - inputs files 
    - petro/pedophysical relationships
    - Data assimilation results
"""

import glob
import os

import pyvista as pv

pv.set_plot_theme("document")

import datetime
import math

import imageio

# import panel as pn
import ipywidgets as widgets
import matplotlib as mpl
import matplotlib.dates as mdates
import matplotlib.font_manager
import matplotlib.pyplot as plt
import matplotlib.style
import natsort
import numpy as np
import pandas as pd
from matplotlib import cm
from matplotlib.colors import LogNorm
from matplotlib.ticker import FormatStrFormatter

from scipy.interpolate import griddata
# from scipy.spatial import Delaunay
from shapely.geometry import Polygon, MultiPoint, Point


from pyCATHY.cathy_utils import (
    change_x2date,
    convert_time_units,
    label_units,
    transform2_time_delta,
)
from pyCATHY.importers import cathy_inputs as in_CT
from pyCATHY.importers import cathy_outputs as out_CT

# mpl.style.use('default')
mpl.rcParams["grid.color"] = "k"
mpl.rcParams["grid.linestyle"] = ":"
mpl.rcParams["grid.linewidth"] = 0.25
# mpl.rcParams['font.family'] = 'Avenir'
plt.rcParams["font.size"] = 12
plt.rcParams["axes.linewidth"] = 0.75

# nice_fonts = {
#     # "font.family": "serif",
#     "font.serif": "Times New Roman",
# }
# matplotlib.rcParams.update(nice_fonts)


#%% ---------------------------------------------------------------------------
# -----------------Plot OUTPUTS CATHY -----------------------------------------
# -----------------------------------------------------------------------------

def create_gridded_mask(x,y,**kwargs):
    
    buffer = False
    if 'buffer' in kwargs:
        buffer = kwargs['buffer']
        
    # points = MultiPoint(np.column_stack((x, y)))
    points = np.column_stack((x, y))
    multi_point = MultiPoint(points)
    boundary = Polygon(points)

    # interval =100
    
    if buffer:
        interval = int(x[1]- x[0])*4
        boundary = multi_point.buffer(interval/2).buffer(-interval/2)

    # boundary_coords
    # Extract the boundary coordinates and create a boolean mask for the region inside the boundary
    boundary_coords = np.array(boundary.exterior.coords)
    xmin, ymin = boundary_coords.min(axis=0)
    xmax, ymax = boundary_coords.max(axis=0)
    xi, yi = np.meshgrid(np.linspace(xmin, xmax, 50), np.linspace(ymin, ymax, 50))
    xx, yy = xi.flatten(), yi.flatten()
    mask = [Point(coord).within(boundary) for coord in zip(xx, yy)]
    mask = np.array(mask).reshape(xi.shape)
    
    return xi, yi, mask
    
    
def plot_WTD(XYZsurface,WT,**kwargs):
    
    #  FLAG, flag for what has happened
    # - 1 watertable calculated correctly
    # - 2 unstaturated zone above saturated zone above unsaturated zone
    # - 3 watertable not encountered, fully saturated vertical profile
    # - 4 watertable not encountered, unsaturated profile
    
    if "ax" not in kwargs:
        fig, ax = plt.subplots()
    else:
        ax = kwargs["ax"]
    
    
    colorbar = True
    if 'colorbar' in kwargs:
        colorbar = kwargs['colorbar']
        
        
    ti = 0
    if 'ti' in kwargs:
        ti = kwargs['ti']
    
    scatter=False
    if 'scatter' in kwargs:
        scatter = kwargs['scatter']
        
    if scatter:
        valid_kwargs = ['vmin', 'vmax']
        relevant_kwargs = {key: value for key, value in kwargs.items() if key in valid_kwargs}
        cmap = ax.scatter(XYZsurface[:,0], XYZsurface[:,1], c=WT[ti],
                          **relevant_kwargs)
        ax.grid()
        # cbar = plt.colorbar(cmap,ax=ax)
        # cbar.set_label('GWD (m)')

    else:
        x = XYZsurface[:,0]
        y = XYZsurface[:,1]
        
        cmap = 'viridis'
        if type(ti) is list:
            z = WT[ti[1]]-WT[ti[0]]
            cmap = 'bwr'
        else:
            z = WT[ti]
        
        
        xi, yi, mask = create_gridded_mask(x,y)
        xx, yy = xi.flatten(), yi.flatten()
    
        zi = griddata((x, y), z, (xx, yy), method='nearest')
    
        # Apply the mask to the gridded data
        zi_masked = np.ma.masked_where(~mask, zi.reshape(xi.shape))
    
        # Plot the masked data
        cmap = ax.contourf(xi, yi, zi_masked, cmap=cmap)
    
    ax.set_xlabel('x (m)')
    ax.set_ylabel('y (m)')
    ax.axis('equal')
    ax.grid(True, linestyle='-.')
    
    if colorbar:
        cbar = plt.colorbar(cmap,ax=ax)
        
        if type(ti) is list:
            cbar.set_label(r'$\Delta$ GWD (m)')
        else:
            cbar.set_label('GWD (m)')
        
    return cmap

    
    
        
    
def show_spatialET(df_fort777,**kwargs):
    
    # df_fort777 = out_CT.read_fort777(os.path.join(simu.workdir,simu.project_name,'fort.777'),
    #                                   )

    ti = 0
    if 'ti' in kwargs:
        ti = kwargs['ti']

    scatter=False
    if 'scatter' in kwargs:
        scatter = kwargs['scatter']
        
        
    df_fort777_indexes = df_fort777.set_index('time_sec').index.unique().to_numpy()

    df_fort777_select_t = df_fort777.set_index('time_sec').loc[df_fort777_indexes[ti]]
    # df_fort777 = df_fort777.loc[9327600]


    # Generate some random scattered points
    x = df_fort777_select_t['X'].values
    y = df_fort777_select_t['Y'].values
    z = df_fort777_select_t['ACT. ETRA'].values
    
    
    # #%%
    
    if "ax" not in kwargs:
        fig, ax = plt.subplots()
    else:
        ax = kwargs["ax"]
        
    # df_fort777.columns
    # ax.imshow(df_fort777['ACT. ETRA'])

    if scatter:
        cmap = ax.scatter(x=df_fort777_select_t['X'], 
                    y=df_fort777_select_t['Y'], 
                    c=df_fort777_select_t['ACT. ETRA']
                    )
    else:
        # Create a grid of points and evaluate a function on the grid
    
        xi, yi, mask = create_gridded_mask(x,y,**kwargs)
        xx, yy = xi.flatten(), yi.flatten()
    
        zi = griddata((x, y), z, (xx, yy), method='cubic')
    
        # Apply the mask to the gridded data
        zi_masked = np.ma.masked_where(~mask, zi.reshape(xi.shape))
    
        # Plot the masked data
        cmap = ax.contourf(xi, yi, zi_masked, cmap='viridis')
        
    ax.set_title('Actual evapotranspiration')
    ax.set_xlabel('x (m)')
    ax.set_ylabel('y (m)')
    ax.axis('equal')
    ax.grid(True, linestyle='-.')
    cbar = plt.colorbar(cmap,ax=ax)
    cbar.set_label('actual ET (mm/s)')
    
    return cmap



def show_wtdepth(df_wtdepth=[], workdir=[], project_name=[], **kwargs):
    """
    plot NET SEEPFACE VOL and NET SEEPFACE FLX over the time t
    """
    # read hgraph file if df_hgraph not existing
    # ------------------------------------------------------------------------
    if len(df_wtdepth) == 0:
        df_wtdepth = out_CT.read_wtdepth(filename="wtdepth")

    # fig, ax = plt.subplots(2,1)
    # if 'delta_t' in kwargs:
    #     df_wtdepth['time'] = pd.to_timedelta(df_wtdepth['time'],unit='s')
    if "ax" not in kwargs:
        fig, ax = plt.subplots()
    else:
        ax = kwargs["ax"]

    ax.plot(df_wtdepth["time (s)"], df_wtdepth["water table depth (m)"])
    ax.set_title("Water table depth")
    ax.set(xlabel="Time (s)", ylabel="Water table depth (m)")
    # ax.legend(["Total flow volume", "nansfdir flow volume"])

    pass


def show_hgsfdet(df_hgsfdeth=[], workdir=[], project_name=[], **kwargs):
    """
    plot NET SEEPFACE VOL and NET SEEPFACE FLX over the time t.
    """
    # read hgraph file if df_hgraph not existing
    # ------------------------------------------------------------------------
    if len(df_hgsfdeth) == 0:
        df_hgsfdeth = out_CT.read_hgsfdet(filename="hgsfdeth")

    fig, ax = plt.subplots(2, 1)
    if "delta_t" in kwargs:
        df_hgsfdeth["time"] = pd.to_timedelta(df_hgsfdeth["time"], unit="s")

    df_hgsfdeth.pivot_table(values="NET SEEPFACE VOL", index="time").plot(
        ax=ax[0], ylabel="NET SEEPFACE VOL", xlabel="time (s)"
    )
    df_hgsfdeth.pivot_table(values="NET SEEPFACE FLX", index="time").plot(
        ax=ax[1], ylabel="NET SEEPFACE FLX", xlabel="time (s)"
    )
    return fig, ax


def show_dtcoupling(
    df_dtcoupling=[], workdir=[], project_name=[], x="time", yprop="Atmact-vf", **kwargs
):
    """
    plot dtcoupling
    """

    if "yprop" in kwargs:
        yprop = kwargs["yprop"]

    # read hgraph file if df_hgraph not existing
    # ------------------------------------------------------------------------
    if "ax" not in kwargs:
       fig, ax = plt.subplots()
    else:
       ax = kwargs["ax"]
       
    if len(df_dtcoupling) == 0:
        df_dtcoupling = out_CT.read_dtcoupling(filename="dtcoupling")
    nstep = len(df_dtcoupling["Atmpot-d"])
    jmax = max(df_dtcoupling["Atmact-vf"])
    timeatm = [df_dtcoupling["Deltat"][0]]
    for i in np.arange(1, nstep):
        timeatm.append(timeatm[i - 1] + df_dtcoupling["Deltat"][i - 1])
    len(timeatm)
    plt.step(timeatm, df_dtcoupling[yprop], color="green", where="post", label=yprop)
    # plt.step(timeatm, df_dtcoupling[yprop[1]], color="blue", where="post", label=yprop[1])

    ax.set_xlabel("time (s)")
    ax.set_ylabel(label_units(yprop))
    plt.legend()


def show_hgraph(df_hgraph=[], workdir=[], project_name=[], x="time", y="SW", **kwargs):
    """
    plot hgraph
    """
    # read hgraph file if df_hgraph not existing
    # ------------------------------------------------------------------------
    if len(df_hgraph) == 0:
        df_hgraph = out_CT.read_hgraph(filename="hgraph")

    if "ax" not in kwargs:
        fig, ax = plt.subplots()
    else:
        ax = kwargs["ax"]

    if "delta_t" in kwargs:
        df_hgraph["time"] = pd.to_timedelta(df_hgraph["time"], unit="s")
    df_hgraph.pivot_table(values="streamflow", index="time").plot(
        ax=ax, ylabel="streamflow ($m^3/s$)", xlabel="time (s)", marker="."
    )


def show_COCumflowvol(df_cumflowvol=[], workdir=None, project_name=None, **kwargs):
    """
    plot COCumflowvol
    """
    # read file if df_cumflowvol not existing
    # ------------------------------------------------------------------------
    if len(df_cumflowvol) == 0:
        df_cumflowvol = out_CT.read_cumflowvol(
            os.path.join(workdir, project_name, "output", "cumflowvol")
        )
    # plot Net Flow Volume (m^3) = f(time)
    # ------------------------------------------------------------------------
    if "ax" not in kwargs:
        fig, ax = plt.subplots()
    else:
        ax = kwargs["ax"]

    ax.plot(df_cumflowvol[:, 2], -df_cumflowvol[:, 7], "b-.")
    ax.plot(df_cumflowvol[:, 2] / 3600, df_cumflowvol[:, 7])
    ax.set_title("Cumulative flow volume")
    ax.set(xlabel="Time (s)", ylabel="Net Flow Volume (m^3)")
    ax.legend(["Total flow volume", "nansfdir flow volume"])


def show_vp_DEPRECATED(
    df_vp=[], workdir=[], project_name=[], index="time", x="time", y="SW", **kwargs
):
    """
    plot vp
    DEPRECATED use psi and sw reader instead and plot using pandas after find_nearest_node search.
    """
    # read vp file if df_atmbc not existing
    # ------------------------------------------------------------------------
    if len(df_vp) == 0:
        df_vp = out_CT.read_vp(filename="vp")
    node_uni = df_vp["node"].unique()
    fig, ax = plt.subplots(1, len(node_uni))
    if len(node_uni) < 2:
        ax = [ax]
    colors = cm.Reds(np.linspace(0.2, 0.8, len(df_vp["str_nb"].unique())))
    for i, n in enumerate(node_uni):
        df_vp_pivot = pd.pivot_table(df_vp, values=y, index=["time", "node", "str_nb"])
        df_vp_pivot_nodei = df_vp_pivot.xs(n, level="node")
        df_vp_pivot_nodei.unstack("str_nb").plot(
            ax=ax[i], title="node: " + str(n), color=colors
        )
        ax[i].legend([])
        label = label_units(y)
        if i == 0:
            ax[i].set_ylabel(label)
    return fig, ax


def show_vtk(
    filename=None,
    unit="pressure",
    timeStep=0,
    notebook=False,
    path=None,
    savefig=False,
    ax=None,
    **kwargs,
):
    """
    Plot vtk file using pyvista
    Parameters
    ----------
    filename : str, optional
        Name of the file. The default is None.
    unit : str, optional
        ['pressure', 'saturation', 'ER', 'permeability', 'velocity'] . The default is pressure.
    timeStep : int, optional
        Time step to plot. The default is 0.
    notebook : bool, optional
        Option to plot in a notebook. The default is False.
    path : str, optional
        Path of the vtk file. The default is None.
    savefig : bool, optional
        Save figure. The default is False.
    **kwargs :
        mainly plotting adjustements to pass into Pyvista.
    """
    my_colormap = "viridis"
    if path is None:
        path = os.getcwd()
    # Parse physical attribute + cmap from unit
    # -------------------------------------------------------------------------
    if filename is None:
        # for surface/subsurface hydrology
        # --------------------------------------------------------------------
        if unit == "pressure":
            my_colormap = "autumn"
        elif unit == "saturation":
            my_colormap = "Blues"

        if timeStep < 10:
            filename = "10" + str(timeStep) + ".vtk"
        elif timeStep < 100:
            filename = "1" + str(timeStep) + ".vtk"
        elif timeStep < 200:
            newnb = [int(x) for x in str(timeStep)]
            filename = "2" + str(newnb[1]) + str(newnb[2]) + ".vtk"
        elif timeStep < 300:
            newnb = [int(x) for x in str(timeStep)]
            filename = "3" + str(newnb[1]) + str(newnb[2]) + ".vtk"
        # for transport
        # --------------------------------------------------------------------
        elif unit == "celerity":
            raise NotImplementedError("Transport vtk file output not yet implemented")
        # for ERT
        # --------------------------------------------------------------------
        elif "ER" in unit:
            filename = "ER_converted" + str(timeStep) + ".vtk"
            my_colormap = "viridis"
            unit = "ER_converted" + str(timeStep)
        elif "ER_int" in unit:
            filename = "ER_converted" + str(timeStep) + "_nearIntrp2_pg_msh.vtk"
            my_colormap = "viridis"
            unit = "ER_converted" + str(timeStep) + "_nearIntrp2_pg_msh"
            
    if unit == 'PERMX':
        my_colormap = None
        print('No colormap')
        print(my_colormap)

            
    

    show_edges = True
    if "show_edges" in kwargs:
        show_edges = kwargs['show_edges']
        
    
    mesh = pv.read(os.path.join(path, filename))
    if unit in list(mesh.array_names):
        print("plot " + str(unit))
    else:
        print("physcial property not existing")

    # notebook = activate widgets
    # -------------------------------------------------------------------------
    if notebook:

        if ax is None:
            ax = pv.Plotter(notebook=notebook)
        # pn.extension('vtk')  # this needs to be at the top of each cell for some reason
        out = widgets.Output()

        def on_value_change(change):
            with out:

                PhysScalars = "pressure"
                time_step = timeStep
                # print(change['new'])
                if hasattr(change.owner, "options"):  # =='Phys. prop:':
                    PhysScalars = change.owner.options[change["new"] - 1]
                else:
                    time_step = change["new"]

                out.clear_output()
                mesh = pv.read("./my_cathy_prj/vtk/10" + str(time_step) + ".vtk")
                _ = ax.add_mesh(
                    mesh, scalars=PhysScalars[0], cmap=my_colormap, **kwargs
                )

                if unit == "saturation":
                    ax.update_scalar_bar_range([0, 1])

                if "clim" in kwargs:
                    ax.update_scalar_bar_range([kwargs["clim"][0], 1])

                legend_entries = []
                legend_entries.append(["Time=" + str(mesh["time"]), "w"])
                _ = ax.add_legend(legend_entries)
                ax.show_grid()
                cpos = ax.show(True)

        slider = widgets.IntSlider(
            min=0,
            max=10,
            step=1,
            continuous_update=True,
            description="Time step #:",
        )
        # play = widgets.Play(min=1, interval=2000)
        choice = widgets.Dropdown(
            options=[("pressure", 1), ("saturation", 2)],
            value=1,
            description="Phys. prop:",
        )
        slider.observe(on_value_change, "value")
        choice.observe(on_value_change, "value")

        plotvtk = widgets.VBox([choice, slider, out])
        plotvtk

    # No notebook interaction
    # -------------------------------------------------------------------------
    else:

        if ax is None:
            ax = pv.Plotter(notebook=False)

        _ = ax.add_mesh(mesh, scalars=unit, cmap=my_colormap, **kwargs)

        if unit == "saturation":
            ax.update_scalar_bar_range([0, 1])
        if "clim" in kwargs:
            ax.update_scalar_bar_range([kwargs["clim"][0], kwargs["clim"][1]])
        # add time stamp as legend
        legend_entries = []
        time_delta = transform2_time_delta(mesh["TIME"], "s")
        legend_entries.append(["Time=" + str(time_delta[0]), "w"])
        _ = ax.add_legend(legend_entries)
        _ = ax.show_bounds(minor_ticks=True, font_size=1)

        # add scatter points to the plot
        # ---------------------------------------------------------------------
        for key, value in kwargs.items():
            # add electrodes positions
            # -----------------------------------------------------------------
            if key == "elecs":
                poly_elecs = pv.PolyData(value)
                poly_elecs["My Labels"] = [
                    f"Label {i}" for i in range(poly_elecs.n_points)
                ]
                ax.add_point_labels(
                    poly_elecs, "My Labels", point_size=20, font_size=36
                )
            # add tensiometers positions
            # -----------------------------------------------------------------
            # add TDR probe positions
            # -----------------------------------------------------------------
    if savefig is True:
        ax.view_xz()
        # ax.save_graphic(
        #     os.path.join(path, filename + unit + ".svg"),
        #     title="",
        #     raster=True,
        #     painter=True,
        # )

        # print("figure saved" + os.path.join(path, filename + ".svg"))
        cpos = ax.show(screenshot= os.path.join(path, filename + unit + ".png"))
        print("figure saved" + os.path.join(path, filename + unit + ".png"))
        ax.close()
    else:
        ax.show_axes()
        ax.show()

    pass


def show_vtk_TL(
    filename=None,
    unit="pressure",
    timeStep="all",
    notebook=False,
    path=None,
    savefig=True,
    show=True,
    **kwargs,
):
    """
    Time lapse animation of selected time steps

    Parameters
    ----------
    filename : str, optional
        DESCRIPTION. The default is None.
    unit : TYPE, optional
        DESCRIPTION. The default is None.
    timeStep : TYPE, optional
        DESCRIPTION. The default is "all".
    notebook : bool, optional
        DESCRIPTION. The default is False.
    path : TYPE, optional
        DESCRIPTION. The default is None.
    savefig : TYPE, optional
        DESCRIPTION. The default is False.
    show : TYPE, optional
        DESCRIPTION. The default is True.

    """

    x_units = None
    xlabel = "s"
    for key, value in kwargs.items():
        if key == "x_units":
            x_units = value
            print(x_units)

    if path is None:
        path = os.getcwd()

    if filename is None:
        if unit == "pressure":
            filename = "1*.vtk"
            filename0 = "100.vtk"
            my_colormap = "autumn"
        elif unit == "saturation":
            my_colormap = "Blues"
            filename = "1*.vtk"
            filename0 = "100.vtk"
        elif "ER" in unit:
            filename = "ER" + str(timeStep) + ".vtk"
            my_colormap = "viridis"

    mesh = pv.read(os.path.join(path, filename0))

    if unit in list(mesh.array_names):
        print("plot " + str(unit))
    else:
        print("physcial property not existing")

    offscreen = False
    if show == False:
        offscreen = True
    plotter = pv.Plotter(
        notebook=notebook,
        off_screen=offscreen,
    )
    plotter.add_mesh(mesh, show_edges=True, cmap=my_colormap)

    if savefig:
        plotter.open_gif(os.path.join(path + unit + ".gif"))

    # options to colorbar
    # ---------------------------------------------------------------------
    if "clim" in kwargs:
        plotter.update_scalar_bar_range([kwargs["clim"][0], kwargs["clim"][1]])

    legend_entry = "Time= " + str(mesh["TIME"])
    if x_units is not None:
        xlabel, t_lgd = convert_time_units(mesh["TIME"], x_units)
        legend_entry = "Time=" + str(t_lgd) + xlabel

    plotter.show_grid()
    cpos = plotter.show(auto_close=False)
    plotter.add_text(legend_entry, name="time-label")

    files = []
    for file in glob.glob(os.path.join(path, filename)):
        files.append(file)

    for ff in natsort.natsorted(files, reverse=False):
        print(ff)
        mesh = pv.read(ff)
        array_new = mesh.get_array(unit)
        print(mesh["TIME"])

        if x_units is not None:
            xlabel, t_lgd = convert_time_units(mesh["TIME"], x_units)
            legend_entry = "Time=" + str(t_lgd) + xlabel
        plotter.update_scalars(array_new, render=True)
        plotter.add_text(legend_entry, name="time-label")

        plotter.render()
        plotter.write_frame()
        if unit == "saturation":
            plotter.update_scalar_bar_range([0, 1])

            if "clim" in kwargs:
                plotter.update_scalar_bar_range([kwargs["clim"][0], kwargs["clim"][1]])
    plotter.close()

    if savefig:
        gif_original = os.path.join(path + unit + ".gif")
        gif_speed_down = os.path.join(path + unit + "_slow.gif")
        gif = imageio.mimread(gif_original)
        imageio.mimsave(gif_speed_down, gif, fps=0.8)
        print("gif saved" + os.path.join(path, gif_original))

    return


#%% ---------------------------------------------------------------------------
# -----------------Plot INPUTS CATHY ------------------------------------------
# -----------------------------------------------------------------------------


def show_atmbc(t_atmbc, v_atmbc, ax=None, **kwargs):
    """
    Plot atmbc=f(time)
    Parameters
    ----------
    t_atmbc : np.array
        time where atmbc change.
    v_atmbc : list of 1 or 2 arrays (when available)
        v_atmbc[0] is the array of Rain/Irrigation change over the time;
        v_atmbc[1] is the array of ET demand over the time;
    """

    # NOT YET IMPLEMETED
    # read atmbc file if df_atmbc not existing
    # ------------------------------------------------------------------------
    # df_atmbc = []
    # if len(df_atmbc)==0:
    #     df_atmbc = out_CT.read_atmbc(filename='vp')
    xlabel = "time (s)"
    for key, value in kwargs.items():
        if key == "x_units":
            x_units = value
            if x_units == "days":
                xlabel = "time (days)"
                t_atmbc = [x / (24 * 60 * 60) for x in t_atmbc]
            if x_units == "hours":
                xlabel = "time (h)"
                t_atmbc = [x / (60 * 60) for x in t_atmbc]

    if "datetime" in kwargs:
        t_atmbc = kwargs["datetime"]
        xlabel = "date"
    # https://matplotlib.org/stable/gallery/lines_bars_and_markers/stairs_demo.html#sphx-glr-gallery-lines-bars-and-markers-stairs-demo-py

    v_atmbc_n = []
    if isinstance(v_atmbc, list):
        try:
            np.shape(v_atmbc)[1]
            v_atmbc_p = v_atmbc[1]  # positif
            v_atmbc_n = v_atmbc[0]  # negatif
            v_atmbc = v_atmbc[0] - v_atmbc[1]
        except:
            pass

    # if np.shape(t_atmbc) != np.shape(v_atmbc):
    if len(v_atmbc_n) > 0:
        if ax is None:
            fig, ax = plt.subplots(2, 1, sharex=True)
            (ax1, ax2) = (ax[0], ax[1])

        color = "tab:blue"
        ax1.set_xlabel("time (h)")
        ax1.set_ylabel("Rain/Irr", color=color)
        ax1.step(t_atmbc, v_atmbc_p, color="blue", where="post", label="Rain/Irr")
        color = "tab:red"
        ax2.set_ylabel("ET", color=color)  # we already handled the x-label with ax1
        ax2.step(t_atmbc, -v_atmbc_n, color=color, where="post", label="ET")
        ax2.tick_params(axis="y", labelcolor=color)
        fig.tight_layout()  # otherwise the right y-label is slightly clipped
        # plt.show(block=False)
    else:
        if ax is None:
            fig, ax = plt.subplots(figsize=(6, 3))

        ax.plot(t_atmbc, v_atmbc, "k.")
        ax.set(xlabel=xlabel, ylabel="net Q (m/s)", title="atmbc inputs")
        ax.grid()
        # plt.show(block=False)
        if "IETO" in kwargs:
            if kwargs["IETO"] != 0:
                plt.step(t_atmbc, v_atmbc, color="k", where="post")
            elif kwargs["IETO"] == 0:  # case of linear interpolation between points
                ax.plot(t_atmbc, v_atmbc, "k.")
    pass


def show_atmbc_3d(df_atmbc):
    """
    Temporary (must exist throught show_vtk only)
    """
    # df_atmbc.set_index('time',inplace=True)
    # df_atmbc.loc[0]
    # filename = './vtk/100.vtk'
    # mesh = pv.read(filename)
    # mesh.add_field_data(df_atmbc.loc[0]['value'], 'atmbc')
    # plotter = pv.Plotter(notebook=True)
    # _ = plotter.add_mesh(mesh, show_edges=True, scalars='atmbc')
    # # _ = plotter.add_legend(legend_entries)
    # plotter.show_grid()
    # cpos = plotter.show()
    show_vtk(new_field="atmbc")

    pass


def show_soil(soil_map, ax=None, **kwargs):
    """
    View from top of the soil prop
    Parameters
    ----------
    soil_map : DataFrame()
        Dataframe containing soil properties for the DEM
    """

    yprop = "PERMX"
    if "yprop" in kwargs:
        yprop = kwargs.pop("yprop")

    layer_nb = "1"
    if "layer_nb" in kwargs:
        layer_nb = kwargs.pop("layer_nb")

    cmap = "tab10"
    nb_of_zones = len(np.unique(soil_map))
    cmap = mpl.colors.ListedColormap(plt.cm.tab10.colors[:nb_of_zones])
    if "cmap" in kwargs:
        cmap = kwargs["cmap"]

    if ax is None:
        fig, ax = plt.subplots()

    # linewidth = 1
    # if 'linewidth' in kwargs:
    #     linewidth = kwargs['linewidth']
        
    cf = ax.pcolormesh(
        soil_map,
        edgecolors="black",
        cmap=cmap,
        **kwargs,
    )
    cf.set_clim(min(soil_map.flatten()), max(soil_map.flatten()))

    cax = plt.colorbar(
        cf,
        ticks=np.linspace(
            min(soil_map.flatten()), max(soil_map.flatten()), nb_of_zones
        ),
        ax=ax,
        label=yprop,
    )

    # try:
        # cax.set_ticklabels(range(int(min(soil_map.flatten())), nb_of_zones))
        
    cax.ax.set_yticklabels(
        [
            "{:.2e}".format(x)
            for x in np.linspace(
                min(soil_map.flatten()), max(soil_map.flatten()), nb_of_zones
            )
        ]
    )
    # ,
    # fontsize=16,
    # )
    ax.set_xlabel("x")
    ax.set_ylabel("y")

    ax.set_title("view from top (before extruding), layer nb" + str(layer_nb))
    # plt.show(block=False)
    # plt.close()

    return cf


def show_raster(
    raster_map,
    str_hd_raster={},
    prop="",
    hapin={},
    ax=None,
    cmap="gist_earth",
    **kwargs,
):

    x = np.zeros(raster_map.shape[0])  # + hapin['xllcorner']
    y = np.zeros(raster_map.shape[1])  # + hapin['yllcorner']

    if len(str_hd_raster) < 1:
        str_hd_raster = {}
        str_hd_raster["west"] = 0
        str_hd_raster["south"] = 0

    if len(hapin) < 1:
        hapin = {}
        hapin["delta_x"] = 1
        hapin["delta_y"] = 1

    for a in range(raster_map.shape[0]):
        x[a] = float(str_hd_raster["west"]) + hapin["delta_x"] * a

    for a in range(raster_map.shape[1]):
        y[a] = float(str_hd_raster["south"]) + hapin["delta_y"] * a

    if ax is None:
        # fig = plt.figure()
        # ax = plt.axes(projection="3d")
        fig, ax = plt.subplots()

    # X, Y = np.meshgrid(x, y)
    # surf = ax.plot_surface(X, Y, raster_map.T, cmap="viridis")

    pmesh = ax.pcolormesh(x, y, raster_map.T, **kwargs)  # , cmap=cmap)

    # cbar = plt.colorbar(pmesh, shrink=0.25, orientation='horizontal',
    #                     label='Elevation (m)')

    # ax.set(xlabel="Easting (m)", ylabel="Northing (m)", zlabel="Elevation (m)")
    ax.set(xlabel="Easting (m)", ylabel="Northing (m)")

    # plt.show(block=False)
    # plt.close()
    ax.set_title(prop)

    return pmesh


def show_zone(zone_map, **kwargs):
    """
    View from top of the vegetation type (equivalent somehow to root map)
    Parameters
    ----------
    veg_map : np.array([])
        Indice of vegetation. The dimension of the vegetation map must match
        the dimension of the DEM.
    """
    # cmap='tab10'
    nb_of_zones = len(np.unique(zone_map))
    cmap = mpl.colors.ListedColormap(plt.cm.tab10.colors[:nb_of_zones])
    if "cmap" in kwargs:
        cmap = kwargs["cmap"]

    fig, ax = plt.subplots()
    cf = ax.pcolormesh(zone_map, edgecolors="black", cmap=cmap)
    # cbar = fig.colorbar(cf, ax=ax, label='indice of zones')

    cax = plt.colorbar(
        cf,
        ticks=np.linspace(
            int(min(zone_map.flatten())), int(max(zone_map.flatten())), nb_of_zones + 1
        ),
        ax=ax,
        label="indice of zones",
    )
    cax.set_ticklabels(range(int(min(zone_map.flatten())), nb_of_zones + 2))

    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title("view from top (before extruding)")
    plt.show(block=False)
    plt.close()
    return fig, ax


def show_indice_veg(veg_map, ax=None, **kwargs):
    """
    View from top of the vegetation type (equivalent somehow to root map)
    Parameters
    ----------
    veg_map : np.array([])
        Indice of vegetation. The dimension of the vegetation map must match
        the dimension of the DEM.
    """
    # cmap='tab10'
    nb_of_zones = len(np.unique(veg_map))
    cmap = mpl.colors.ListedColormap(plt.cm.tab10.colors[:nb_of_zones])
    if "cmap" in kwargs:
        cmap = kwargs.pop("cmap")

    if ax is None:  
        fig, ax = plt.subplots()
    cf = ax.pcolormesh(veg_map, edgecolors="black", cmap=cmap,
                       **kwargs)
    # fig.colorbar(cf, ax=ax, label='indice of vegetation')

    cax = plt.colorbar(
        cf,
        ticks=np.arange(
            int(min(veg_map.flatten())), int(max(veg_map.flatten()))+1
        ),
        ax=ax,
        label="indice of vegetation",
    )
    
    # cax.set_ticklabels(range(int(min(veg_map.flatten())), nb_of_zones + 2))
    cax.set_ticklabels(np.arange(
                                    int(min(veg_map.flatten())), 
                                    int(max(veg_map.flatten())) +1
                                    # nb_of_zones + 1
                                    )
                        )

    cax.ax.set_yticklabels(
        [
            "{:d}".format(int(x))
            for x in np.arange(
                min(veg_map.flatten())-1, max(veg_map.flatten())
            )
        ]
    )


    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title("view from top (before extruding)")
    # plt.show(block=False)
    # plt.close()
    return ax


def dem_plot_2d_top(parameter, label="", **kwargs):
    """
    View of the DEM from top of the a given parameter

    (Not yet implemented)
    Possible parameters are:
        - vegetation
        - altitude

    """
    if label == "all":
        fig, axs = plt.subplots(
            int(len(parameter.keys()) / 2),
            int(len(parameter.keys()) / 3),
            sharex=True,
            sharey=True,
        )
        for ax, p in zip(axs.reshape(-1), parameter.keys()):
            cf = ax.pcolormesh(parameter[p])  # edgecolors="black"
            fig.colorbar(cf, ax=ax, label=p, fraction=0.046, pad=0.04, shrink=0.8)
            ax.set_xlabel("x")
            ax.set_ylabel("y")
            ax.set_aspect("auto", "box")
        plt.tight_layout()
        plt.show(block=False)

    else:
        fig, ax = plt.subplots()
        cf = ax.pcolormesh(parameter, edgecolors="black")
        fig.colorbar(cf, ax=ax, label=label)
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_title("view from top (before extruding)")
        plt.show(block=False)
    return fig, ax


def get_dem_coords(
    dem_mat=[], str_hd_dem="", hapin={}, workdir=None, project_name=None, **kwargs
):

    if len(dem_mat) == 0:
        # Read the Header
        dem_mat, str_hd_dem = in_CT.read_dem(
            os.path.join(workdir, project_name, "prepro/dem"),
            os.path.join(workdir, project_name, "prepro/dtm_13.val"),
        )

    # transpose because values in dtm_13 files from where the DEM raster is extracted are transposed ...
    dem_mat = dem_mat.T

    x = np.zeros(dem_mat.shape[0]) + hapin["xllcorner"]
    y = np.zeros(dem_mat.shape[1]) + hapin["yllcorner"]

    for a in range(0, dem_mat.shape[0]):
        x[a] = float(str_hd_dem["west"]) + hapin["delta_x"] * (a + 1)

    for a in range(0, dem_mat.shape[1]):
        y[a] = float(str_hd_dem["south"]) + hapin["delta_y"] * (a + 1)

    return x, y, np.flipud(dem_mat)


def show_dem(
    dem_mat=[],
    str_hd_dem="",
    hapin={},
    ax=None,
    workdir=None,
    project_name=None,
    **kwargs,
):
    """
    Creates a 3D representation from a Grass DEM file
    """
    # np.shape(dem_mat)
    x, y, dem_mat = get_dem_coords(
        dem_mat, str_hd_dem, hapin, workdir, project_name, **kwargs
    )

    if ax is None:
        fig = plt.figure()
        ax = fig.add_subplot(projection="3d")

    X, Y = np.meshgrid(y, x)
    surf = ax.plot_surface(X, Y, dem_mat, cmap="viridis", **kwargs)
    # surf = ax.plot_surface(Y,X, dem_mat, cmap="viridis",**kwargs)
    cbar = plt.colorbar(
        surf, shrink=0.25, orientation="horizontal", label="Elevation (m)"
    )
    ax.set(xlabel="Easting (m)", ylabel="Northing (m)", zlabel="Elevation (m)")
    # plt.show(block=False)
    # plt.close()

    ax.yaxis.set_major_formatter(FormatStrFormatter("%3.4e"))
    ax.xaxis.set_major_formatter(FormatStrFormatter("%3.4e"))

    pass


def plot_mesh_bounds(BCtypName, mesh_bound_cond_df, time, ax=None):
    
    m = np.array(["o", "+"])
    mvalue = []
    alpha = []
    
    
    mesh_bound_cond_df_selec = mesh_bound_cond_df[mesh_bound_cond_df['time']==time]
    
    
    for bound_val in mesh_bound_cond_df_selec[BCtypName]:
        if bound_val == 0:
            mvalue.append(1)
            alpha.append(1)
        else:
            mvalue.append(0)
            alpha.append(0.1)

    if ax is None:
        fig = plt.figure()
        ax = fig.add_subplot(projection="3d")

    ax.scatter(
        mesh_bound_cond_df_selec["x"],
        mesh_bound_cond_df_selec["y"],
        mesh_bound_cond_df_selec["z"],
        c=mvalue,
    )
    ax.set_xlabel("X Label")
    ax.set_ylabel("Y Label")
    ax.set_zlabel("Z Label")
    ax.set_title(BCtypName + " Time " + str(time))
    # ax.set_title(BCtypName)
    # plt.show(block=False)
    # return fig, ax
    pass


#%% ---------------------------------------------------------------------------
# -----------------Plot PETRO-PEDOPHYSICS relationships -----------------------
# -----------------------------------------------------------------------------


def plot_VGP(df_VGP, savefig=False, **kwargs):
    if "ax" in kwargs:
        ax = kwargs["ax"]
    else:
        fig = plt.figure(figsize=(6, 3), dpi=350)
        ax = fig.add_subplot()

    label = []
    if "label" in kwargs:
        label = kwargs["label"]

    ax.plot(df_VGP["psi"], df_VGP["theta"], label=label, marker=".")
    ax.set_xlabel("Soil Water Potential (cm)")
    ax.set_ylabel(r"Water content ($m^3/m^3$)")
    return ax


def DA_plot_Archie(df_Archie, savefig=False, **kwargs):
    if "ax" in kwargs:
        ax = kwargs["ax"]
    else:
        fig = plt.figure(figsize=(6, 3), dpi=350)
        ax = fig.add_subplot()

    ax.scatter(df_Archie["sw"], df_Archie["ER_converted"])
    ax.set_xlabel("Saturation (-)")
    ax.set_ylabel("ER converted")
    ax.set_title("[All ensemble]")

    if "porosity" in kwargs:
        ax.scatter(df_Archie["sw"] * kwargs["porosity"], df_Archie["ER_converted"])
        ax.set_xlabel("swc")
        ax.set_ylabel("ER_converted")
    if savefig == True:
        plt.savefig("Archie.png", dpi=300)
    return ax


#%% ----------------------------------------------------------------------------
# -----------------Plot results DATA ASSIMILATION------------------------------
# -----------------------------------------------------------------------------


def plot_hist_perturbated_parm(parm, var_per, type_parm, parm_per_array, **kwargs):
    fig = plt.figure(figsize=(6, 3), dpi=150)

    if var_per[type_parm]["transf_type"] is not None:
        if "log".casefold() in var_per[type_parm]["transf_type"].casefold():
            w = 0.2
            nbins = math.ceil((parm_per_array.max() - parm_per_array.min()) / w)
            # plt.hist(np.log10(parm_sampling), ensemble_size, alpha=0.5, label='sampling')
            plt.hist(
                np.log10(parm_per_array), nbins, alpha=0.5, label="ini_perturbation"
            )
            plt.axvline(
                x=np.log10(parm[type_parm + "_nominal"]), linestyle="--", color="red"
            )
    else:
        # plt.hist(parm_sampling, ensemble_size/2, alpha=0.5, label='sampling')
        plt.hist(parm_per_array, alpha=0.5, label="ini_perturbation")
        plt.axvline(x=parm["nominal"], linestyle="--", color="red")
    plt.legend(loc="upper right")
    plt.xlabel(parm["units"])
    plt.ylabel("Probability")
    plt.title("Histogram of " + type_parm)
    plt.tight_layout()
    fig.savefig(os.path.join(os.getcwd(), kwargs["savefig"]), dpi=350)


def show_DA_process_ens(
    EnsembleX, Data, DataCov, dD, dAS, B, Analysis, savefig=False, **kwargs
):
    """Plot result of Data Assimilation Analysis"""
    label_sensor = "raw data"
    if "label_sensor" in kwargs:
        label_sensor = kwargs["label_sensor"]

    fig = plt.figure(figsize=(12, 6), dpi=300)
    ax1 = fig.add_subplot(2, 5, 1)
    cax = ax1.matshow(EnsembleX, aspect="auto")  # ,
    # cmap=cm.rainbow, norm=colors.LogNorm())
    ax1.set_title("Prior")
    ax1.set_ylabel("$\psi$ params #")
    ax1.set_xlabel("Members #")
    cbar = fig.colorbar(cax, location="bottom")

    ax = fig.add_subplot(2, 5, 6)
    cax = ax.matshow(np.cov(EnsembleX), aspect="auto", cmap="gray", norm=LogNorm())
    ax.set_title("cov(Prior)")
    ax.set_xlabel("$\psi$ params #")
    ax.set_ylabel("$\psi$ params #")
    # cbar = fig.colorbar(cax, location='bottom')
    cbar = fig.colorbar(cax, format="$%.1f$", location="bottom")

    ax.set_yticks([])

    ax = fig.add_subplot(2, 5, 2)
    cax = ax.matshow(np.tile(Data, (np.shape(EnsembleX)[1], 1)).T, aspect="auto")
    ax.set_title(label_sensor)
    ax.set_ylabel("Meas")
    ax.set_xlabel("Members #")
    cbar = fig.colorbar(cax, location="bottom")
    ax.set_yticks([])

    ax = fig.add_subplot(2, 5, 7)
    cax = ax.matshow(DataCov, aspect="auto", cmap="gray_r")
    # cmap=cm.rainbow, norm=colors.LogNorm())
    # vmin=0, vmax=1e-29)
    ax.set_title("cov(meas)")
    ax.set_ylabel("Meas")
    ax.set_xlabel("Meas")
    cbar = fig.colorbar(cax, location="bottom")
    ax.set_yticks([])

    ax = fig.add_subplot(2, 5, 3)
    cax = ax.matshow(dD, aspect="auto", cmap="jet")
    ax.set_title("Meas - Sim")
    ax.set_ylabel("Meas")
    ax.set_xlabel("Members #")
    cbar = fig.colorbar(cax, location="bottom")
    ax.set_yticks([])

    ax = fig.add_subplot(2, 5, 4, sharey=ax1)
    cax = ax.matshow(np.dot(dAS, B), aspect="auto", cmap="jet")
    ax.set_title("Correction")
    ax.set_ylabel("$\psi$ params #")
    ax.set_xlabel("Members #")
    cbar = fig.colorbar(cax, location="bottom")
    ax.set_yticks([])

    ax = fig.add_subplot(2, 5, 5, sharey=ax1)
    cax = ax.matshow(Analysis, aspect="auto")
    ax.set_title("Posterior")
    ax.set_ylabel("$\psi$ params #")
    ax.set_xlabel("Members #")
    cbar = fig.colorbar(cax, location="bottom")
    ax.set_yticks([])

    plt.tight_layout()
    savename = "showDA_process_ens"
    if "savename" in kwargs:
        savename = kwargs["savename"]

    if savefig == True:
        fig.savefig(savename + ".png", dpi=300)
    plt.close()

    return fig, ax


def DA_RMS(df_performance, sensorName, **kwargs):
    """Plot result of Data Assimilation: RMS evolution over the time"""
    
    if "ax" in kwargs:
        ax = kwargs["ax"]
    # else:
    #     if "start_date" in kwargs:
    #         fig, ax = plt.subplots(3, 1, sharex=True)
    #     else:
    #         fig, ax = plt.subplots(2, 1)
    keytime = "time"
    xlabel = "assimilation #"
    start_date = None
    if "start_date" in kwargs:
        start_date = kwargs["start_date"]
        keytime = "time_date"
        xlabel = "date"
        
    

    atmbc_times = None
    if "atmbc_times" in kwargs:
        atmbc_times = kwargs["atmbc_times"]

    header = ["time", "ObsType", "RMSE" + sensorName, "NMRMSE" + sensorName, "OL"]
    df_perf_plot = df_performance[header]
    df_perf_plot["RMSE" + sensorName] = df_perf_plot["RMSE" + sensorName].astype(
        "float64"
    )
    df_perf_plot["NMRMSE" + sensorName] = df_perf_plot["NMRMSE" + sensorName].astype(
        "float64"
    )
    df_perf_plot.OL = df_perf_plot.OL.astype("str")
    df_perf_plot.dropna(inplace=True)

    # len(dates)
    # len(df_perf_plot["time"])
    # len(atmbc_times)
    
    if start_date is not None:
        dates = change_x2date(atmbc_times, start_date)
        df_perf_plot["time_date"] = df_perf_plot["time"].replace(
            list(df_perf_plot["time"].unique()), dates)
    p0 = df_perf_plot.pivot(index=keytime, columns="OL", values="RMSE" + sensorName)
    p1 = df_perf_plot.pivot(index=keytime, columns="OL", values="NMRMSE" + sensorName)

    if "start_date" in kwargs:
        p0.plot(xlabel=xlabel, ylabel="RMSE" + sensorName, ax=ax[1], style=[".-"])
        p1.plot(xlabel=xlabel, ylabel="NMRMSE" + sensorName, ax=ax[2], style=[".-"])
    else:
        p0.plot(xlabel=xlabel, ylabel="RMSE" + sensorName, ax=ax[0], style=[".-"])
        p1.plot(xlabel=xlabel, ylabel="NMRMSE" + sensorName, ax=ax[1], style=[".-"])

    return ax, plt


def DA_plot_parm_dynamic(
    parm="ks", dict_parm_pert={}, list_assimilation_times=[], savefig=False, **kwargs
):
    """Plot result of Data Assimilation: parameter estimation evolution over the time"""
    ensemble_size = len(dict_parm_pert[parm]["ini_perturbation"])
    # nb_times = len(df_DA['time'].unique())

    # fig = plt.figure(figsize=(6, 3), dpi=150)
    
    if 'ax' in kwargs:
        ax = kwargs['ax']
    else:
        fig, ax = plt.subplots()
        
    ax.hist(
        dict_parm_pert[parm]["ini_perturbation"],
        ensemble_size,
        alpha=0.5,
        label="ini_perturbation",
    )
    ax.legend(loc="upper right")
    ax.set_ylabel("Probability")
    for nt in list_assimilation_times:
        try:
            ax.hist(
                dict_parm_pert[parm]["update_nb" + str(int(nt + 1))],
                ensemble_size,
                alpha=0.5,
                label="update nb" + str(int(nt + 1)),
            )
        except:
            pass
        ax.legend(loc="upper right")
        ax.set_ylabel("Probability")
    if "log" in kwargs:
        if kwargs["log"]:
            ax.set_xscale("log")
    # plt.show()
    return ax


def DA_plot_parm_dynamic_scatter(
    parm="ks", dict_parm_pert={}, list_assimilation_times=[], savefig=False, **kwargs
):
    """Plot result of Data Assimilation: parameter estimation evolution over the time"""
    
    if "ax" in kwargs:
        ax = kwargs["ax"]
    else:
        fig = plt.figure(figsize=(6, 3), dpi=350)
        ax = fig.add_subplot()
        
        
    ensemble_size = len(dict_parm_pert[parm]["ini_perturbation"])
    mean_t = [np.mean(dict_parm_pert[parm]["ini_perturbation"])]
    mean_t_yaxis = np.mean(dict_parm_pert[parm]["ini_perturbation"])
    cloud_t = np.zeros([ensemble_size, len(list_assimilation_times)])
    cloud_t[:, 0] = np.array(dict_parm_pert[parm]["ini_perturbation"])
    np.shape(cloud_t)
    try:
        for nt in list_assimilation_times[1:]:
            cloud_t[:, int(nt + 1)] = np.hstack(
                dict_parm_pert[parm]["update_nb" + str(int(nt))]
            )
    except:
        pass

    dict_parm_new = {}
    name = []
    i = 0
    for k in dict_parm_pert[parm].keys():
        if "upd" in k:
            dict_parm_new[parm + "_" + k] = np.hstack(dict_parm_pert[parm][k])
            name.append(str(i + 1))
            i = i + 1
    df = pd.DataFrame()
    df = pd.DataFrame(data=dict_parm_new)
    df.index.name = "Ensemble_nb"
    
    
    color = 'k'
    if "color" in kwargs:
        color = kwargs["color"]
    
    boxplot = df.boxplot(color='grey',ax=ax)
    boxplot.set_xticklabels(name, rotation=90)
    
    ax.set_ylabel(parm)
    ax.set_xlabel("assimilation #")
    if "log" in kwargs:
        if kwargs["log"]:
            boxplot.set_yscale("log")
    return ax


def prepare_DA_plot_time_dynamic(DA, state="psi", nodes_of_interest=[], **kwargs):
    """Select data from DA_df dataframe"""
    keytime = "time"
    start_date = None
    if "start_date" in kwargs:
        start_date = kwargs["start_date"]
        keytime = "time_date"

    atmbc_times = None
    if "atmbc_times" in kwargs:
        atmbc_times = kwargs["atmbc_times"]

    if start_date is not None:
        dates = change_x2date(atmbc_times, start_date)

        if len(dates) < len(list(DA["time"].unique())):
            DA = DA.drop(DA[DA.time + 1 >= len(list(DA["time"].unique()))].index)
        if len(dates) > len(list(DA["time"].unique())):
            # check if contains difference in time otherwise add articifially 1s to keep
            # the formatting. (Else plot crashes)
            if all(dates[: len(list(DA["time"].unique()))].hour == 0):
                time_delta_change = datetime.timedelta(seconds=1)
                dates.values[0] = dates[0] + time_delta_change
            dates = dates[: len(list(DA["time"].unique()))]
        # DA["time_date"] = DA["time"].replace(list(DA["time"].unique()), dates)
        # DA['time_date'].dt.strftime('%Y-%m-%d %H:%M:%S')
        unique_times = DA["time"].unique()
        DA["time_date"] = DA["time"].map(dict(zip(unique_times, dates)))

    isOL = DA.loc[DA["OL"] == True]
    isENS = DA.loc[DA["OL"] == False]

    isENS_time_Ens = isENS.set_index(["time", "Ensemble_nb"])
    isOL_time_Ens = isOL.set_index(["time", "Ensemble_nb"])

    if type(nodes_of_interest) != list:
        nodes_of_interest = [nodes_of_interest]

    NENS = int(max(DA["Ensemble_nb"].unique()))

    key2plot = "psi_bef_update"
    if "sw" in state:
        key2plot = "sw_bef_update_"

    if "key2plot" in kwargs:
        key2plot = kwargs["key2plot"]

    prep_DA = {
        "isENS": isENS,
        "isOL": isOL,
    }
    # isENS_time_Ens.xs((1, 1), level=('time', 'Ensemble_nb'), axis=0)
    # -----------------------------#
    if len(nodes_of_interest) > 0:

        if len(isOL) > 0:

            # nb_of_nodes = len(np.arange(int(len(isOL)/((max(isOL['time'])-1)*NENS))))
            # test = len(isOL)/nb_of_nodes

            nb_of_times = len(np.unique(isOL["time"]))
            nb_of_ens = len(np.unique(isOL["Ensemble_nb"]))
            nb_of_nodes = len(isOL[isOL["time"] == 0]) / nb_of_ens
            test = len(isOL) / nb_of_nodes

            try:
                int(test)
            except:
                ValueError("inconsistent nb of OL data - no plot")
                pass
            else:

                isOL.insert(
                    2,
                    "idnode",
                    np.tile(np.arange(nb_of_nodes), nb_of_times * nb_of_ens),
                    True,
                )

                # isOL.insert(2, "idnode", np.tile(np.arange(int(len(isOL)/(max(isOL['time']+1)*NENS))),
                #                                   int(max(isOL['time']+1)*NENS)), True)
                # len(isOL)/test
                # len(isOL)/((len(isOL['time'].unique())1)*NENS)
                # isOL.insert(2, "idnode", np.tile(np.arange(nb_of_nodes),
                #                                   int((max(isOL['time'])-1)*NENS)), True)
                select_isOL = isOL[isOL["idnode"].isin(nodes_of_interest)]
                select_isOL = select_isOL.set_index([keytime, "idnode"])
                select_isOL = select_isOL.reset_index()

                # mean, min and max of Open Loop
                # --------------------------------------------------------------------------
                ens_mean_isOL_time = (
                    select_isOL.set_index([keytime, "Ensemble_nb", "idnode"])
                    .groupby(level=[keytime, "idnode"])[key2plot]
                    .mean()
                )
                ens_mean_isOL_time = ens_mean_isOL_time.reset_index(name="mean(ENS)_OL")

                ens_min_isOL_time = (
                    select_isOL.set_index([keytime, "Ensemble_nb", "idnode"])
                    .groupby(level=[keytime, "idnode"])[key2plot]
                    .min()
                )
                ens_min_isOL_time = ens_min_isOL_time.reset_index(name="min(ENS)_OL")

                ens_max_isOL_time = (
                    select_isOL.set_index([keytime, "Ensemble_nb", "idnode"])
                    .groupby(level=[keytime, "idnode"])[key2plot]
                    .max()
                )
                ens_max_isOL_time = ens_max_isOL_time.reset_index(name="max(ENS)_OL")

                prep_DA.update(
                    {
                        "ens_mean_isOL_time": ens_mean_isOL_time,
                        "ens_max_isOL_time": ens_max_isOL_time,
                        "ens_min_isOL_time": ens_min_isOL_time,
                    }
                )
                # ens_mean_isOL_time['time_date']

        if len(isENS) > 0:

            if len(isOL) > 0:

                isENS.insert(
                    2,
                    "idnode",
                    np.tile(
                        np.arange(int(len(isENS) / (max(isENS["time"]) * (NENS)))),
                        int(max(isENS["time"])) * (NENS),
                    ),
                    True,
                )
            else:
                # number of nodes = np.sum(isENS['time']==1)/24
                
                # np.sum((isENS['time']==1) & (isENS['Ensemble_nb']==0))
                # np.sum(isENS['Ensemble_nb']==0)
               
                
                # nnode = np.sum((isENS['time']==1) & (isENS['Ensemble_nb']==0))
                # isENS.insert(
                #     2,
                #     "idnode",
                #     np.tile(np.arange(nnode),
                #         int(max(isENS["time"])),
                #     ),
                #     True,
                # )
                
                isENS.insert(
                    2,
                    "idnode",
                    np.tile(
                        np.arange(int(len(isENS) / (max(isENS["time"]) * (NENS + 1)))),
                        int(max(isENS["time"])) * (NENS + 1),
                    ),
                    True,
                )

            select_isENS = isENS[isENS["idnode"].isin(nodes_of_interest)]
            select_isENS = select_isENS.set_index([keytime, "idnode"])
            select_isENS = select_isENS.reset_index()

            # mean, min and max of Open Loop
            # --------------------------------------------------------------------------
            ens_mean_isENS_time = (
                select_isENS.set_index([keytime, "Ensemble_nb", "idnode"])
                .groupby(level=[keytime, "idnode"])[key2plot]
                .mean()
            )
            ens_mean_isENS_time = ens_mean_isENS_time.reset_index(name="mean(ENS)")

            ens_min_isENS_time = (
                select_isENS.set_index([keytime, "Ensemble_nb", "idnode"])
                .groupby(level=[keytime, "idnode"])[key2plot]
                .min()
            )
            ens_min_isENS_time = ens_min_isENS_time.reset_index(name="min(ENS)")

            ens_max_isENS_time = (
                select_isENS.set_index([keytime, "Ensemble_nb", "idnode"])
                .groupby(level=[keytime, "idnode"])[key2plot]
                .max()
            )
            ens_max_isENS_time = ens_max_isENS_time.reset_index(name="max(ENS)")

            prep_DA.update(
                {
                    "ens_mean_isENS_time": ens_mean_isENS_time,
                    "ens_max_isENS_time": ens_max_isENS_time,
                    "ens_min_isENS_time": ens_min_isENS_time,
                }
            )

    else:
        # take the spatial average mean
        # -----------------------------#

        spatial_mean_isOL_time_ens = isOL_time_Ens.groupby(
            level=[keytime, "Ensemble_nb"]
        )["analysis"].mean()
        spatial_mean_isOL_time_ens = spatial_mean_isOL_time_ens.reset_index()

        spatial_mean_isENS_time_ens = isENS_time_Ens.groupby(
            level=[keytime, "Ensemble_nb"]
        )["analysis"].mean()
        spatial_mean_isENS_time_ens = spatial_mean_isENS_time_ens.reset_index()

        select_isOL = spatial_mean_isOL_time_ens
        select_isENS = spatial_mean_isENS_time_ens

    return prep_DA


def DA_plot_time_dynamic(
    DA, state="psi", nodes_of_interest=[], savefig=False, **kwargs
):
    """Plot result of Data Assimilation: state estimation evolution over the time"""
    prep_DA = prepare_DA_plot_time_dynamic(
        DA, state=state, nodes_of_interest=nodes_of_interest, **kwargs
    )
    if "ax" in kwargs:
        ax = kwargs["ax"]
    else:
        fig = plt.figure(figsize=(6, 3), dpi=350)
        ax = fig.add_subplot()

    alpha = 0.5
    colors_minmax = 'blue'
    if "colors_minmax" in kwargs:
        colors_minmax = kwargs["colors_minmax"]
        
        
    keytime = "time"
    xlabel = "time (h)"
    if "start_date" in kwargs:
        keytime = "time_date"
        xlabel = "date"

    ylabel = r"pressure head $\psi$ (m)"
    if "sw" in state:
        ylabel = "water saturation (-)"

    # Plot
    # --------------------------------------------------------------------------

    if len(prep_DA["isENS"]) > 0:
        prep_DA["ens_mean_isENS_time"].pivot(
            index=keytime,
            columns=["idnode"],
            # columns=['idnode'],
            values=["mean(ENS)"],
        ).plot(ax=ax, style=[".-"], color=colors_minmax,
               )

        prep_DA["ens_max_isENS_time"].pivot(
            index=keytime,
            columns=["idnode"],
            # columns=['idnode'],
            values=["max(ENS)"],
        ).plot(ax=ax, style=[".-"], color=colors_minmax,
               )

        prep_DA["ens_min_isENS_time"].pivot(
            index=keytime,
            columns=["idnode"],
            # columns=['idnode'],
            values=["min(ENS)"],
        ).plot(
            ax=ax,
            style=[".-"],
            color=colors_minmax,
            xlabel="(assimilation) time - (h)",
            ylabel="pressure head $\psi$ (m)",
        )

        lgd = ax.fill_between(
            prep_DA["ens_max_isENS_time"][keytime],
            prep_DA["ens_min_isENS_time"]["min(ENS)"],
            prep_DA["ens_max_isENS_time"]["max(ENS)"],
            alpha=0.2,
            color=colors_minmax,
            label="minmax DA",
        )
        # lgd= ax.fill_between(prep_DA['ens_max_isENS_time'][keytime],
        #                 prep_DA['ens_min_isENS_time'][[keytime,'min(ENS)']],
        #                 prep_DA['ens_max_isENS_time'][[keytime,'max(ENS)']],
        #                 alpha=0.2,
        #                 color='blue',
        #                 label='minmax DA')

    # if len(prep_DA['isOL'])>0:
    if "ens_mean_isOL_time" in prep_DA.keys():
        prep_DA["ens_mean_isOL_time"].pivot(
            index=keytime,
            # columns=["Ensemble_nb",'idnode'],
            columns=["idnode"],
            values=["mean(ENS)_OL"],
        ).plot(
            ax=ax,
            style=["-"],
            color="grey",
            label=False,
            ylabel="pressure head $\psi$ (m)",
        )  # water saturation (-)
        prep_DA["ens_min_isOL_time"].pivot(
            index=keytime,
            columns=["idnode"],
            # columns=['idnode'],
            values=["min(ENS)_OL"],
        ).plot(ax=ax, style=["--"], color="grey", label=False)

        prep_DA["ens_max_isOL_time"].pivot(
            index=keytime,
            columns=["idnode"],
            # columns=['idnode'],
            values=["max(ENS)_OL"],
        ).plot(ax=ax, style=["--"], color="grey", label=False)

        ax.fill_between(
            prep_DA["ens_mean_isOL_time"][keytime],
            prep_DA["ens_min_isOL_time"]["min(ENS)_OL"],
            prep_DA["ens_max_isOL_time"]["max(ENS)_OL"],
            alpha=0.2,
            color="grey",
            label="minmax OL",
        )

    ax.set_xlabel(xlabel)
    # ax.set_ylabel('pressure head (m)')
    ax.set_ylabel(ylabel)

    savename = "showDA_dynamic"
    if "savename" in kwargs:
        savename = kwargs["savename"]

    if savefig == True:
        plt.savefig(savename + ".png", dpi=300)
    pass
