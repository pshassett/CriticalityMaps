# -*- coding: utf-8 -*-
"""
Created on Tue Jun  4 11:09:02 2019

@author: PHassett
"""
import os
import shutil
import multiprocessing as mp
import time
import pickle
import copy
import matplotlib.pyplot as plt
import pandas as pd
import yaml
import numpy as np
import wntr
from .mp_queue_tools import runner
from .criticality_functions import _fire_criticality, _pipe_criticality


def fire_criticality_analysis(wn, output_dir="./", fire_demand=0.946,
                              fire_start=86400, fire_duration=7200,
                              min_pipe_diam=0.1524, max_pipe_diam=0.2032,
                              p_nom=17.58, p_min=14.06, save_log=False,
                              post_process=True, pop=None, multiprocess=False,
                              num_processors=None):
    """
    A plug-and-play ready function for executing fire criticality analysis.

    Parameters
    ----------
    _wn: wntr WaterNetworkModel object
        wntr _wn for the water network of interest

    output_dir: str/path-like object, optional
        path to the directory to save the results of the analysis.

        Defaults to the working directory ("./").

    fire_demand: float, optional
        fire fighting demand(m^3/s).

        Defaults to 0.946 m^3/s (1500gpm).

    fire_start: integer, optional
        start time of the fire in seconds.

        Defaults to 86400 sec (24hr).

    fire_duration: integer, optional
        total duration of the fire demand in seconds.

        Defaults to 7200 sec (2hr).

    min_pipe_diam: float, optional
        minimum diameter pipe to perform fire criticality analysis on(meters).

        Defaults to 0.1524 m (6in).

    max_pipe_diam: float, optional
        maximum diameter pipe to perform fire criticality analysis on(meters).

        Defaults to 0.2032 m (8in).

    p_nom: float, optional
        nominal pressure for PDD (kPa). The minimun pressure to still recieve
        full expected demand.

        Defaults to 17.58 kPa (25psi).

    p_min: float, optional
        minimum pressure for PDD (kPa). The minimun pressure to still recieve
        any demand.

        Defaults to 14.06 kPa (20psi).

    save_log: boolean, optional
        option to save .json log files for each fire simulation. Otherwise,
        log files are still created but deleted after successful completion of
        all simulations. Serves as an effective back-up of the analysis
        results.

        Defaults to False.

    post_process: boolean, optional
        option to post process the analysis results with process_criticality.
        Saves pdf maps of the nodes and population impacted at each fire node,
        and corresponding csv files. To customize the post-processing output,
        set post_process to False and then run process_criticality() with the
        summary .yml file and any additional args as input.

        Defaults to True.

    pop: dict or pandas DataFrame, optional
        population estimate at each node. Used for post processing. If
        undefined, defaults to the result of wntr.metrics.population(_wn).

        Defaults to None.

    multiprocess: boolean, optional
        option to run criticality across multiple processors.

        Defaults to False.

    num_processors: int, optional
        the number of processors to use if mp is True.

        Defaults to None if mp is False.
        Otherwise, defaults to int(mp.cpu_count() * 0.666), or 2/3 of the
        available processors.
    """
    # Make copy of the wn, preserving the original.
    _wn = copy.deepcopy(wn)
    # Start the timer.
    start = time.time()
    # Set the PDD simulation characteristics.
    _set_PDD_params(_wn, p_nom, p_min)
    # Duration can be set in _fire_criticality instead of here
    # _wn.options.time.duration = fire_start + fire_duration
    # Pickle-serialize the _wn for reuse.
    with open('./_wn.pickle', 'wb') as fp:
        pickle.dump(_wn, fp)
    # Check if any nzd junctions fall below pmin during sim period.
    nzd_nodes = _get_nzd_nodes(_wn)
    nodes_below_pmin = _get_lowP_nodes(_wn, p_min, nzd_nodes)

    # Define eligible pipes for fire criticality.
    fire_pipes_hi = _wn.query_link_attribute('diameter', np.less_equal,
                                             max_pipe_diam,
                                             link_type=wntr.network.model.Pipe)
    fire_pipes_lo = _wn.query_link_attribute('diameter', np.greater_equal,
                                             min_pipe_diam,
                                             link_type=wntr.network.model.Pipe)
    fire_pipes = list(set(fire_pipes_hi.index) & set(fire_pipes_lo.index))

    # Get the nodes for each pipe.
    fire_nodes = set()
    for pipe_name in fire_pipes:
        pipe = _wn.get_link(pipe_name)
        fire_nodes.add(pipe.start_node_name)
        fire_nodes.add(pipe.end_node_name)
    # Define output files.
    log_dir = os.path.join(output_dir, 'log', '')
    os.makedirs(log_dir, exist_ok=True)
    summary_file = os.path.join(output_dir, 'fire_criticality_summary.yml')
    if multiprocess:
        # Define arguments for fire analysis.
        args = [(_fire_criticality, ('./_wn.pickle', fire_start, fire_duration,
                                     p_min, p_nom, node, fire_demand,
                                     nzd_nodes, nodes_below_pmin, log_dir))
                for node in fire_nodes]
        # Execute in a mp fashion.
        mp.freeze_support()
        results = runner(args, num_processors)
        with open(summary_file, 'w') as fp:
            yaml.dump(dict(results), fp, default_flow_style=False)
        print('fire criticality runtime =', time.time() - start)
    else:
        # Define arguments for fire analysis.
        result = []
        for node in fire_nodes:
            result.append(_fire_criticality('./_wn.pickle', fire_start,
                                            fire_duration, p_min, p_nom, node,
                                            fire_demand, nzd_nodes,
                                            nodes_below_pmin, log_dir)
                          )
        with open(summary_file, 'w') as fp:
            yaml.dump(dict(result), fp, default_flow_style=False)
        print('fire criticality runtime =', time.time() - start)
    # Clean up temp files
    os.remove('./_wn.pickle')
    if not save_log:
        shutil.rmtree(log_dir)
    # Process the results and save some data and figures.
    if post_process:
        process_criticality(_wn, summary_file, output_dir, pop)


def pipe_criticality_analysis(wn, output_dir="./", break_start=86400,
                              break_duration=172800, min_pipe_diam=0.3048,
                              max_pipe_diam=None, p_nom=17.58, p_min=14.06,
                              save_log=False, post_process=True, pop=None,
                              multiprocess=False, num_processors=None):
    """
    A plug-and-play ready function for executing fire criticality analysis.

    Parameters
    ----------
    _wn: wntr WaterNetworkModel object
        wntr _wn for the water network of interest

    output_dir: str/path-like object, optional
        path to the directory to save the results of the analysis.

        Defaults to the working directory ("./").

    break_start: integer, optional
        start time of the pipe break in seconds.

        Defaults to 86400 sec (24hr).

    break_duration: integer, optional
        total duration of the fire demand in seconds.

        Defaults to 172800 sec (48hr).

    min_pipe_diam: float, optional
        minimum diameter pipe to perform fire criticality analysis on(meters).

        Defaults to 0.3048 m (12in).

    max_pipe_diam: float, optional
        maximum diameter pipe to perform fire criticality analysis on(meters).

        Defaults to None.

    p_nom: float, optional
        nominal pressure for PDD (kPa). The minimun pressure to still recieve
        full expected demand.

        Defaults to 17.58 kPa (25psi).

    p_min: float, optional
        minimum pressure for PDD (kPa). The minimun pressure to still recieve
        any demand.

        Defaults to 14.06 kPa (20psi).

    save_log: boolean, optional
        option to save .json log files for each fire simulation. Otherwise,
        log files are still created but deleted after successful completion of
        all simulations. Serves as an effective back-up of the analysis
        results.

        Defaults to False.

    post_process: boolean, optional
        option to post process the analysis results with process_criticality.
        Saves pdf maps of the nodes and population impacted at each fire node,
        and corresponding csv files. To customize the post-processing output,
        set post_process to False and then run process_criticality() with the
        summary .yml file and any additional args as input.

        Defaults to True.

    pop: dict or pandas DataFrame, optional
        population estimate at each node. Used for post processing. If
        undefined, defaults to the result of wntr.metrics.population(_wn).

        Defaults to None.

    multiprocess: boolean, optional
        option to run criticality across multiple processors.

        Defaults to False.

    num_processors: int, optional
        the number of processors to use if mp is True.

        Defaults to None if mp is False.
        Otherwise, defaults to int(mp.cpu_count() * 0.666), or 2/3 of the
        available processors.
    """
    # Make copy of the wn, preserving the original.
    _wn = copy.deepcopy(wn)
    # Start the timer.
    start = time.time()
    # Set the PDD simulation characteristics.
    _set_PDD_params(_wn, p_nom, p_min)
    _wn.options.time.duration = break_start + break_duration
    # Pickle-serialize the _wn for reuse.
    with open('./_wn.pickle', 'wb') as fp:
        pickle.dump(_wn, fp)
    # Check if any nzd junctions fall below pmin during sim period.
    nzd_nodes = _get_nzd_nodes(_wn)
    nodes_below_pmin = _get_lowP_nodes(_wn, p_min, nzd_nodes)

    # Define eligible pipes for pipe criticality.
    critical_pipes_lo = _wn.query_link_attribute('diameter', np.greater_equal,
                                                 min_pipe_diam,
                                                 link_type=wntr.network.model.Pipe)
    if max_pipe_diam is not None:
        critical_pipes_hi = _wn.query_link_attribute('diameter', np.less_equal,
                                                     max_pipe_diam,
                                                     link_type=wntr.network.model.Pipe)
        critical_pipes = list(set(critical_pipes_lo.index)
                              & set(critical_pipes_hi.index))
    else:
        critical_pipes = list(set(critical_pipes_lo.index))
    # Define output files.
    log_dir = os.path.join(output_dir, 'log', '')
    os.makedirs(log_dir, exist_ok=True)
    summary_file = os.path.join(output_dir, 'pipe_criticality_summary.yml')
    # run the simulations
    if multiprocess:
        # Define arguments for fire analysis.
        args = [(_pipe_criticality, ('./_wn.pickle', break_start,
                                     break_duration, p_min, p_nom, pipe,
                                     nzd_nodes, nodes_below_pmin, log_dir))
                for pipe in critical_pipes]
        # Execute in a mp fashion.
        mp.freeze_support()
        results = runner(args, num_processors)
        with open(summary_file, 'w') as fp:
            yaml.dump(dict(results), fp, default_flow_style=False)
        print('pipe criticality runtime =', time.time() - start)
    else:
        # Define arguments for fire analysis.
        result = []
        for pipe in critical_pipes:
            result.append(_pipe_criticality('./_wn.pickle', break_start,
                                            break_duration, p_min, p_nom, pipe,
                                            nzd_nodes, nodes_below_pmin,
                                            log_dir)
                          )
        with open(summary_file, 'w') as fp:
            yaml.dump(dict(result), fp, default_flow_style=False)
        print('pipe criticality runtime =', time.time() - start)
    # Clean up temp files.
    os.remove('./_wn.pickle')
    if not save_log:
        shutil.rmtree(log_dir)
    # Process the results and save some data and figures.
    if post_process:
        process_criticality(_wn, summary_file, output_dir, pop)


def process_criticality(_wn, summary_file, output_dir, pop=None,
                        save_maps=True, save_csvs=True):
    """
    Process the results of a criticality analysis and produce some figures

    Parameters
    ----------
    _wn: wntr WaterNetworkModel object
        the _wn that the analysis was performed on

    summary_file: str/path-like object
        path to the .yml summary file produced from a criticality analysis

    pop: dict or pandas Series
        population estimate at each junction of the _wn. Output from
        `wntr.metrics.population` is suitable input format.

    """
    # Set some local parameters.
    cmap = wntr.graphics.color.custom_colormap(numcolors=2,
                                               colors=['gray', 'gray'],
                                               name='custom')
    fig_x = 6
    fig_y = 6
    # Close any existing figures.
    plt.close('all')
    # Calculate population as necessary
    if pop is None:
        pop = wntr.metrics.population(_wn)
    # Parse the results file into nodes and population impacted.
    with open(summary_file, 'r') as fp:
        summary = yaml.load(fp, Loader=yaml.BaseLoader)
    summary_len = pd.Series()
    summary_pop = pd.Series()
    failed_sim = {}
    for key, val in summary.items():
        if type(val) is dict:
            summary_len[key] = len(val.keys())
            summary_pop[key] = 0
            for node in val.keys():
                summary_pop[key] += pop[node]
        elif val == 'NO EFFECTED NODES':
            pass
        elif 'failed:' in val:
            failed_sim[key] = val
    # Produce output and save in output dir
    if save_csvs:
        summary_len.to_csv(os.path.join(output_dir, 'nodes_impacted.csv'),
                           header=False)
        summary_pop.to_csv(os.path.join(output_dir, 'pop_impacted.csv'),
                           header=False)
    if save_maps:
        if 'fire' in summary_file:
            fig, ax = plt.subplots(1, 1, figsize=(fig_x, fig_y))
            wntr.graphics.plot_network(_wn, link_attribute='length',
                                       node_size=0, link_cmap=cmap,
                                       add_colorbar=False, ax=ax)
            wntr.graphics.plot_network(_wn, node_attribute=summary_len,
                                       node_size=20, link_width=0,
                                       title='Number of nodes impacted by low \
pressure conditions\nfor each fire demand', ax=ax)
            plt.savefig(os.path.join(output_dir, 'nodes_impacted_map.pdf'))

            fig, ax = plt.subplots(1, 1, figsize=(fig_x, fig_y))
            wntr.graphics.plot_network(_wn, link_attribute='length',
                                       node_size=0, link_cmap=cmap,
                                       add_colorbar=False, ax=ax)
            wntr.graphics.plot_network(_wn, node_attribute=summary_pop,
                                       node_size=20, link_width=0,
                                       title='Number of people impacted by low\
 pressure conditions\nfor each fire demand', ax=ax)
            plt.savefig(os.path.join(output_dir, 'pop_impacted_map.pdf'))
        else:
            fig, ax = plt.subplots(1, 1, figsize=(fig_x, fig_y))
            wntr.graphics.plot_network(_wn, link_attribute='length',
                                       node_size=0, link_cmap=cmap,
                                       add_colorbar=False, ax=ax)
            wntr.graphics.plot_network(_wn, link_attribute=summary_len,
                                       node_size=0, link_width=2,
                                       title='Number of nodes impacted by low \
pressure conditions\nfor each pipe closure', ax=ax)
            plt.savefig(os.path.join(output_dir, 'nodes_impacted_map.pdf'))

            fig, ax = plt.subplots(1, 1, figsize=(fig_x, fig_y))
            wntr.graphics.plot_network(_wn, link_attribute='length',
                                       node_size=0, link_cmap=cmap,
                                       add_colorbar=False, ax=ax)
            wntr.graphics.plot_network(_wn, link_attribute=summary_pop,
                                       node_size=0, link_width=2,
                                       title='Number of people impacted by low\
 pressure conditions\nfor each pipe closure', ax=ax)
            plt.savefig(os.path.join(output_dir, 'pop_impacted_map.pdf'))


def _set_PDD_params(_wn, pnom, pmin):
    for name, node in _wn.nodes():
        node.nominal_pressure = pnom
        node.minimum_pressure = pmin


def _get_nzd_nodes(_wn):
    nzd_nodes = []
    for name, node in _wn.junctions():
        for dmnd in node.demand_timeseries_list:
            if dmnd.base_value > 0:
                nzd_nodes.append(name)
                break
    return nzd_nodes


def _get_lowP_nodes(_wn, pmin, nzd_nodes):
    nodes_below_pmin = {}
    # Original simulation
    sim = wntr.sim.WNTRSimulator(_wn, mode='PDD')
    results = sim.run_sim()
    nzd_pressure = results.node['pressure'].loc[:, nzd_nodes]
    below_pmin = nzd_pressure[nzd_pressure < pmin].notna()
    for hr in below_pmin.index:
        nodes_below_pmin[hr] = []
        for node in below_pmin.columns:
            if below_pmin.loc[hr, node]:
                nodes_below_pmin[hr].append(node)
    return nodes_below_pmin
