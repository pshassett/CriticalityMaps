# -*- coding: utf-8 -*-
"""
Created on Tue Jun  4 11:09:02 2019

@author: PHassett

Modified: jhogge
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
from .criticality_functions import _fire_criticality, _pipe_criticality, _segment_criticality, use_EpanetSimulator


def fire_criticality_analysis(wn, output_dir="./", fire_demand=0.946,
                              fire_start=86400, fire_duration=7200,
                              min_pipe_diam=0.1524, max_pipe_diam=0.2032,
                              p_req=17.58, p_min=14.06, save_log=False,
                              summary_file='fire_criticality_summary.yml',
                              post_process=True, pop=None, multiprocess=False,
                              num_processors=None):
    """
    A plug-and-play ready function for executing fire criticality analysis.

    Parameters
    ----------
    wn: wntr WaterNetworkModel object
        wntr wn for the water network of interest

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

    p_req: float, optional
        required pressure for PDD (kPa). The minimun pressure to still recieve
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

    summary_file: str, optional
        file name for the yml summary file saved in output_dir

        Defaults to 'fire_criticality_summary.yml'.

    post_process: boolean, optional
        option to post process the analysis results with process_criticality.
        Saves pdf maps of the nodes and population impacted at each fire node,
        and corresponding csv files. To customize the post-processing output,
        set post_process to False and then run process_criticality() with the
        summary .yml file and any additional args as input.

        Defaults to True.

    pop: dict or pandas DataFrame, optional
        population estimate at each node. Used for post processing. If
        undefined, defaults to the result of wntr.metrics.population(wn).

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
    _set_PDD_params(_wn, p_req, p_min)
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
    summary_file = os.path.join(output_dir, summary_file)
    if multiprocess:
        # Define arguments for fire analysis.
        args = [(_fire_criticality, ('./_wn.pickle', fire_start, fire_duration,
                                     p_min, p_req, node, fire_demand,
                                     nzd_nodes, nodes_below_pmin, log_dir))
                for node in fire_nodes]
        # Execute in a mp fashion.
        mp.freeze_support()
        results = runner(args, num_processors)
        with open(summary_file, 'w') as fp:
            yaml.dump(dict(results), fp, default_flow_style=False)
        print('fire criticality runtime (sec) =', round(time.time() - start))
    else:
        # Define arguments for fire analysis.
        result = []
        for node in fire_nodes:
            result.append(_fire_criticality('./_wn.pickle', fire_start,
                                            fire_duration, p_min, p_req, node,
                                            fire_demand, nzd_nodes,
                                            nodes_below_pmin, log_dir)
                          )
        with open(summary_file, 'w') as fp:
            yaml.dump(dict(result), fp, default_flow_style=False)
        print('fire criticality runtime (sec) =', round(time.time() - start))
    # Clean up temp files
    os.remove('./_wn.pickle')
    if not save_log:
        shutil.rmtree(log_dir)
    # Process the results and save some data and figures.
    if post_process:
        process_criticality(_wn, summary_file, output_dir, pop)


def pipe_criticality_analysis(wn, output_dir="./", break_start=86400,
                              break_duration=172800, min_pipe_diam=0.3048,
                              max_pipe_diam=None, p_req=17.58, p_min=14.06,
                              save_log=False,
                              summary_file='pipe_criticality_summary.yml',
                              post_process=True, pop=None, multiprocess=False,
                              num_processors=None):
    """
    A plug-and-play ready function for executing fire criticality analysis.

    Parameters
    ----------
    wn: wntr WaterNetworkModel object
        wntr wn for the water network of interest

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

    p_req: float, optional
        required pressure for PDD (kPa). The minimun pressure to still recieve
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

    summary_file: str, optional
        file name for the yml summary file saved in output_dir.

        Defaults to 'pipe_criticality_summary.yml'.

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
    _set_PDD_params(_wn, p_req, p_min)
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
    summary_file = os.path.join(output_dir, summary_file)
    # run the simulations
    if multiprocess:
        # Define arguments for pipe analysis.
        args = [(_pipe_criticality, ('./_wn.pickle', break_start,
                                     break_duration, p_min, p_req, pipe,
                                     nzd_nodes, nodes_below_pmin, log_dir))
                for pipe in critical_pipes]
        # Execute in a mp fashion.
        mp.freeze_support()
        results = runner(args, num_processors)
        with open(summary_file, 'w') as fp:
            yaml.dump(dict(results), fp, default_flow_style=False)
        print('pipe criticality runtime (sec) =', round(time.time() - start))
    else:
        # Define arguments for fire analysis.
        result = []
        for pipe in critical_pipes:
            result.append(_pipe_criticality('./_wn.pickle', break_start,
                                            break_duration, p_min, p_req, pipe,
                                            nzd_nodes, nodes_below_pmin,
                                            log_dir)
                          )
        with open(summary_file, 'w') as fp:
            yaml.dump(dict(result), fp, default_flow_style=False)
        print('pipe criticality runtime (sec) =', round(time.time() - start))
    # Clean up temp files.
    os.remove('./_wn.pickle')
    if not save_log:
        shutil.rmtree(log_dir)
    # Process the results and save some data and figures.
    if post_process:
        process_criticality(_wn, summary_file, output_dir, pop)


def segment_criticality_analysis(wn, link_segments, node_segments, valve_layer, 
                                 output_dir="./", break_start=86400, 
                                 break_duration=172800, min_pipe_diam=0.3048, 
                                 max_pipe_diam=None, p_req=17.58, p_min=14.06, 
                                 save_log=False,
                                 summary_file='segment_criticality_summary.yml',
                                 post_process=True, pop=None, multiprocess=False,
                                 num_processors=None):
    """
    A plug-and-play ready function for executing segment criticality analysis.

    Parameters
    ----------
    wn: wntr WaterNetworkModel object
        wntr wn for the water network of interest
    
    link_segments: Pandas series
        results of valve_segments algorithm, listing links and their segment

    node_segments: Pandas series
        results of valve_segments algorithm, listing nodes and their segment
        
    valve_layer: Pandas dataframe
        list of node/segment combinations for the valves in the network
        
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

    p_req: float, optional
        required pressure for PDD (kPa). The minimun pressure to still recieve
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

    summary_file: str, optional
        file name for the yml summary file saved in output_dir.

        Defaults to 'segment_criticality_summary.txt'.

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
    _set_PDD_params(_wn, p_req, p_min)
    _wn.options.time.duration = break_start + break_duration
    # Pickle-serialize the _wn for reuse.
    with open('./_wn.pickle', 'wb') as fp:
        pickle.dump(_wn, fp)
    # Check if any nzd junctions fall below pmin during sim period.
    nzd_nodes = _get_nzd_nodes(_wn)
    nodes_below_pmin = _get_lowP_nodes(_wn, p_min, nzd_nodes)

    # Define output files.
    log_dir = os.path.join(output_dir, 'log', '')
    os.makedirs(log_dir, exist_ok=True)
    summary_file = os.path.join(output_dir, summary_file)
    n_segments = np.array([node_segments.max(), link_segments.max()]).max()
    # run the simulations
    if multiprocess:
        # Define arguments for pipe analysis.
        args = [(_segment_criticality, ('./_wn.pickle', segment,
                                        link_segments, node_segments,
                                        nodes_below_pmin, nzd_nodes,
                                        log_dir, break_start, break_duration, 
                                        p_min, p_req)
                )
                for segment in np.arange(n_segments)]
        # Execute in a mp fashion.
        mp.freeze_support()
        results = runner(args, num_processors)
        with open(summary_file, 'w') as fp:
            yaml.dump(dict(results), fp, default_flow_style=False)
        print('segment criticality runtime (sec) =', round(time.time() - start))
    else:
        # Define arguments for segment analysis.
        result = []
        for segment in range(1, n_segments+1):
            result.append(_segment_criticality('./_wn.pickle', segment,
                                               link_segments, node_segments,
                                               nodes_below_pmin, nzd_nodes,
                                               log_dir, break_start, 
                                               break_duration, p_min, p_req)
                          )
        with open(summary_file, 'w') as fp:
            yaml.dump(dict(result), fp, default_flow_style=False)
        print('segment criticality runtime (sec) =', round(time.time() - start))
    # Clean up temp files.
    os.remove('./_wn.pickle')
    if not save_log:
        shutil.rmtree(log_dir)
    # Process the results and save some data and figures.
    if post_process:
        process_criticality(_wn, summary_file, output_dir, pop, 
                            link_segments=link_segments, 
                            node_segments=node_segments, 
                            valve_layer=valve_layer)


def process_criticality(wn, summary_file, output_dir, pop=None,
                        save_maps=True, save_csv=True, link_segments=None,
                        node_segments=None, valve_layer=None):
    """
    Process the results of a criticality analysis and produce some figures

    Parameters
    ----------
    wn: wntr WaterNetworkModel object
        the _wn that the analysis was performed on

    summary_file: str/path-like object
        path to the .yml summary file produced from a criticality analysis

    pop: dict or pandas Series, optional
        population estimate at each junction of the _wn. Output from
        `wntr.metrics.population` is suitable input format.

    save_maps: bool, optional
        option to save pdf maps of the population and nodes impacted at each node/link tested.
        Defaults to True.

    save_csv: bool, optional
        option to save a csv log of the population and nodes impacted at each node/link tested.
        Defaults to True.

    """
    # Set some local parameters.
    cmap = wntr.graphics.color.custom_colormap(N=2,
                                               colors=['gray', 'gray'],
                                               name='custom')
    fig_x = 6
    fig_y = 6
    # Close any existing figures.
    plt.close('all')
    # Calculate population as necessary
    if pop is None:
        pop = wntr.metrics.population(wn)
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
        elif val == 'NO AFFECTED NODES':
            pass
        elif 'failed:' in val:
            failed_sim[key] = val     

    # assign results from the segments to the links
    if 'segment' in summary_file:
        link_nodes_affected = {}
        link_pop = {}
        for link in link_segments.index:
            if str(link_segments[link]) in summary_len.index:
                link_nodes_affected[link] = summary_len[summary_len.index == str(link_segments[link])][0]
                link_pop[link] = summary_pop[summary_pop.index == str(link_segments[link])][0]
            else:
                link_nodes_affected[link] = 0
                link_pop[link] = 0
            
    # Produce output and save in output dir
    if save_csv:
        csv_summary = pd.DataFrame({"Nodes Impacted": summary_len,
                                    "Population Impacted": summary_pop})
        csv_summary.index.name = "ID"
        csv_summary.to_csv(os.path.join(output_dir, 'pop_node_impacts.csv'))

    if save_maps:
        if 'fire' in summary_file:
            fig, ax = plt.subplots(1, 1, figsize=(fig_x, fig_y))
            wntr.graphics.plot_network(wn, link_attribute='length',
                                       node_size=0, link_cmap=cmap,
                                       add_colorbar=False, ax=ax)
            wntr.graphics.plot_network(wn, node_attribute=summary_len,
                                       node_size=20, link_width=0,
                                       title='Number of nodes impacted by low \
pressure conditions\nfor each fire demand', ax=ax)
            plt.savefig(os.path.join(output_dir, 'nodes_impacted_map.pdf'))

            fig, ax = plt.subplots(1, 1, figsize=(fig_x, fig_y))
            wntr.graphics.plot_network(wn, link_attribute='length',
                                       node_size=0, link_cmap=cmap,
                                       add_colorbar=False, ax=ax)
            wntr.graphics.plot_network(wn, node_attribute=summary_pop,
                                       node_size=20, link_width=0,
                                       title='Number of people impacted by low\
 pressure conditions\nfor each fire demand', ax=ax)
            plt.savefig(os.path.join(output_dir, 'pop_impacted_map.pdf'))
        elif 'segment' in summary_file:
            fig, ax = plt.subplots(1, 1, figsize=(fig_x, fig_y))
            wntr.graphics.plot_network(wn, link_attribute='length',
                                       node_size=0, link_cmap=cmap,
                                       add_colorbar=False, ax=ax)
            wntr.graphics.plot_network(wn, valve_layer=valve_layer, link_attribute=link_nodes_affected,
                                       node_size=0, link_width=2,
                                       title='Number of nodes impacted by low \
pressure conditions\nfor each segment closure', ax=ax)
            plt.savefig(os.path.join(output_dir, 'nodes_impacted_map.pdf'))   
            fig, ax = plt.subplots(1, 1, figsize=(fig_x, fig_y))
            wntr.graphics.plot_network(wn, link_attribute='length',
                                       node_size=0, link_cmap=cmap,
                                       add_colorbar=False, ax=ax)
            wntr.graphics.plot_network(wn, valve_layer=valve_layer, link_attribute=link_pop,
                                       node_size=0, link_width=2,
                                       title='Number of people impacted by low\
 pressure conditions\nfor each segment closure', ax=ax)
            plt.savefig(os.path.join(output_dir, 'pop_impacted_map.pdf'))
        elif 'pipe' in summary_file:
            fig, ax = plt.subplots(1, 1, figsize=(fig_x, fig_y))
            wntr.graphics.plot_network(wn, link_attribute='length',
                                       node_size=0, link_cmap=cmap,
                                       add_colorbar=False, ax=ax)
            wntr.graphics.plot_network(wn, link_attribute=summary_len,
                                       node_size=0, link_width=2,
                                       title='Number of nodes impacted by low \
pressure conditions\nfor each pipe closure', ax=ax)
            plt.savefig(os.path.join(output_dir, 'nodes_impacted_map.pdf'))

            fig, ax = plt.subplots(1, 1, figsize=(fig_x, fig_y))
            wntr.graphics.plot_network(wn, link_attribute='length',
                                       node_size=0, link_cmap=cmap,
                                       add_colorbar=False, ax=ax)
            wntr.graphics.plot_network(wn, link_attribute=summary_pop,
                                       node_size=0, link_width=2,
                                       title='Number of people impacted by low\
 pressure conditions\nfor each pipe closure', ax=ax)
            plt.savefig(os.path.join(output_dir, 'pop_impacted_map.pdf'))


def _set_PDD_params(_wn, preq, pmin):
    _wn.options.hydraulic.required_pressure = preq
    _wn.options.hydraulic.minimum_pressure = pmin

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
    _wn.options.hydraulic.demand_model = 'PDD'

    if use_EpanetSimulator:
        sim = wntr.sim.EpanetSimulator(_wn)
    else:
        sim = wntr.sim.WNTRSimulator(_wn)
    results = sim.run_sim()
    nzd_pressure = results.node['pressure'].loc[:, nzd_nodes]
    below_pmin = nzd_pressure[nzd_pressure < pmin].notna()
    for hr in below_pmin.index:
        nodes_below_pmin[hr] = []
        for node in below_pmin.columns:
            if below_pmin.loc[hr, node]:
                nodes_below_pmin[hr].append(node)
    return nodes_below_pmin
