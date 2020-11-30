# -*- coding: utf-8 -*-
"""
Created on Tue Jun  4 11:33:38 2019

@author: PHassett
"""
import json
import pickle
import pandas as pd
import wntr


def _fire_criticality(wn_pickle, start, fire_duration, p_min, p_nom, fire_node,
                      fire_dmnd, nzd_nodes, nodes_below_pmin, results_dir):
    # print('~'*20 + 'running fire analysis for node' + fire_node + '~'*20)
    # Reset the wn to original status. Pickle beforehand as needed.
    with open(wn_pickle, 'rb') as fp:
        _wn = pickle.load(fp)
    # Set the simulation characteristics.
    for name, node in _wn.nodes():
        node.required_pressure = p_nom
    _wn.options.time.duration = (start + fire_duration)
    # Add the fire flow pattern and demand to the fire node
    fire_flow_pattern = wntr.network.elements.Pattern.binary_pattern(
            'fire_flow',
            start_time=start,
            end_time=start + fire_duration,
            step_size=_wn.options.time.pattern_timestep,
            duration=_wn.options.time.duration
            )
    _wn.add_pattern('fire_flow', fire_flow_pattern)
    node = _wn.get_node(fire_node)
    node.demand_timeseries_list.append((fire_dmnd,
                                        fire_flow_pattern,
                                        'Fire flow'))
    unique_results = {}
    try:
        # Run fire simulation.
        _wn.options.hydraulic.demand_model = 'PDD'
        fire_sim = wntr.sim.WNTRSimulator(_wn)
        results = fire_sim.run_sim(solver_options={'MAXITER': 500})
        # Get pressure at nzd nodes that fall below p_min.
        temp = results.node['pressure'].loc[_wn.options.time.duration - 3600,
                                            nzd_nodes]
        temp = temp[temp < p_min]
        # Round off extra decimals
        temp = temp.round(decimals=5)
        # Remove nodes that are below pressure threshold in base case.
        unique_results = temp[set(temp.index)
                              - set(nodes_below_pmin[_wn.sim_time - 3600])]
        unique_results = unique_results.to_dict()

    except Exception as e:
        unique_results = 'failed: ' + str(e)
        print(fire_node, ' Failed:', e)

    else:
        if len(unique_results.keys()) == 0:
            unique_results = 'NO AFFECTED NODES'
    finally:
        with open(results_dir + fire_node + '.json', 'w') as fp:
            json.dump(unique_results, fp)
        return (fire_node, unique_results)


def _pipe_criticality(wn_pickle, start, break_duration, p_min, p_nom,
                      pipe_name, nzd_nodes, nodes_below_pmin, results_dir):
    # print('~'*20 + ' running pipe criticality for pipe' + pipe_name + '~'*20)
    # Reset the _wn to original status. Pickle beforehand as needed.
    with open(wn_pickle, 'rb') as fp:
        _wn = pickle.load(fp)
    # Set the simulation characteristics.
    for name, node in _wn.nodes():
        node.required_pressure = p_nom
    _wn.options.time.duration = (start + break_duration)

    try:
        # Apply pipe break conditions.
        pipe = _wn.get_link(pipe_name)
        act = wntr.network.controls.ControlAction(pipe,
                                                  'status',
                                                  wntr.network.LinkStatus.Closed)
        cond = wntr.network.controls.SimTimeCondition(_wn, '=', start)
        ctrl = wntr.network.controls.Control(cond, act)
        _wn.add_control('close pipe ' + pipe_name, ctrl)
        _wn.options.hydraulic.demand_model = 'PDD'
        pipe_sim = wntr.sim.WNTRSimulator(_wn)
        results = pipe_sim.run_sim(solver_options={'MAXITER': 500})

        # Get pressure at nzd nodes that fall below p_min.
        temp = results.node['pressure'].loc[start:
                                            _wn.options.time.duration,
                                            nzd_nodes]
        temp = temp[temp < p_min]
        # Round off extra decimals
        temp = temp.round(decimals=5)
        # Remove nodes that are below pressure threshold in base case.
        for val in list(temp.index):
            for node in nodes_below_pmin[val]:
                temp.loc[val, node] = None

        temp_min = temp.min()
        for ind in list(temp_min.index):
            if str(temp_min[ind]) == 'nan':
                temp_min.pop(ind)

        unique_results = temp_min.to_dict()

    except Exception as e:
        unique_results = 'failed: ' + str(e)
        print(pipe_name, ' Failed:', e)

    else:
        if len(unique_results.keys()) == 0:
            unique_results = 'NO AFFECTED NODES'
    finally:
        with open(results_dir + pipe_name + '.json', 'w') as fp:
            json.dump(unique_results, fp)
        return (pipe_name, unique_results)


def _segment_criticality(wn_pickle, segment, link_segments, node_segments,
                         nodes_below_pmin, nzd_nodes, results_dir, start=86400, 
                         break_duration=172800, p_min=14.06, p_nom=17.58):
    # print('~'*20 + ' running segment criticality for segment' + segment + '~'*20)
    # Reset the _wn to original status. Pickle beforehand as needed.
    
    
    with open(wn_pickle, 'rb') as fp:
        _wn = pickle.load(fp)
      
    # Set the simulation characteristics.
    for name, node in _wn.nodes():
        node.required_pressure = p_nom
    
    _wn.options.time.duration = start + break_duration
    
    # Gather start and end nodes for all pipes
    start_nodes = _wn.query_link_attribute('start_node_name')
    end_nodes = _wn.query_link_attribute('end_node_name')
    links_connected_to_nodes = pd.concat([start_nodes,end_nodes])
    
    try:
        # Apply pipe break conditions
        pipes_in_seg = link_segments[link_segments == segment].index
        nodes_in_seg = node_segments[node_segments == segment].index
        pipes_list = []
        
        # Break each pipe in the segment
        for pipe in pipes_in_seg:
            pipe_name = _wn.get_link(pipe)
            act = wntr.network.controls.ControlAction(pipe_name,
                                                  'status',
                                                  wntr.network.LinkStatus.Closed)
            pipes_list.append(pipe)
            cond = wntr.network.controls.SimTimeCondition(_wn, '=', start)
            ctrl = wntr.network.controls.Control(cond, act)
            _wn.add_control('close pipe ' + pipe, ctrl)
            # ADDED CHECK
#            print(_wn.get_control('close pipe ' + pipe))
        
        # Break pipes connected to each node in the segment
        for node in nodes_in_seg:
            node_pipes = links_connected_to_nodes[links_connected_to_nodes==node].index
            for node_pipe in node_pipes:
                if not(node_pipe in pipes_list):
                    pipe_name = _wn.get_link(node_pipe)
                    act = wntr.network.controls.ControlAction(pipe_name,
                                                              'status',
                                                              wntr.network.LinkStatus.Closed)
                    pipes_list.append(node_pipe)
                    cond = wntr.network.controls.SimTimeCondition(_wn, '=', start)
                    ctrl = wntr.network.controls.Control(cond, act)
                    _wn.add_control('close pipe ' + node_pipe, ctrl)
                    # ADDED CHECK
#                    print(_wn.get_control('close pipe ' + node_pipe))

        _wn.options.hydraulic.demand_model = 'PDD'
        pipe_sim = wntr.sim.WNTRSimulator(_wn)
        results = pipe_sim.run_sim(solver_options={'MAXITER': 500})
    
        # Get pressure at nzd nodes that fall below p_min.
        temp = results.node['pressure'].loc[start:
                                            _wn.options.time.duration,
                                            nzd_nodes]
        
        temp = temp[temp < p_min]
        # Round off extra decimals
        temp = temp.round(decimals=5)
        
        # Remove nodes that are below pressure threshold in base case.
        for val in list(temp.index):
            for node in nodes_below_pmin[val]:
                temp.loc[val, node] = None
    
        temp_min = temp.min()
        for ind in list(temp_min.index):
            if str(temp_min[ind]) == 'nan':
                temp_min.pop(ind)
    
        unique_results = temp_min.to_dict()
        
    except Exception as e:
        unique_results = 'failed: ' + str(e)
        print('Segment ', segment, ' Failed:', e)

    else:
        if len(unique_results.keys()) == 0:
            unique_results = 'NO AFFECTED NODES'
    finally:
        with open(results_dir + str(segment) + '.json', 'w') as fp:
            json.dump(unique_results, fp)
        return (segment, unique_results)
