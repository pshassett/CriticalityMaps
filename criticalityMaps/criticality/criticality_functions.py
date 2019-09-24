# -*- coding: utf-8 -*-
"""
Created on Tue Jun  4 11:33:38 2019

@author: PHassett
"""
import json
import pickle
import wntr


def _fire_criticality(wn_pickle, start, fire_duration, p_min, p_nom, fire_node,
                      fire_dmnd, nzd_nodes, nodes_below_pmin, results_dir):
    # print('~'*20 + 'running fire analysis for node' + fire_node + '~'*20)
    # Reset the wn to original status. Pickle beforehand as needed.
    with open(wn_pickle, 'rb') as fp:
        _wn = pickle.load(fp)
    # Set the simulation characteristics.
    for name, node in _wn.nodes():
        node.nominal_pressure = p_nom
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
        fire_sim = wntr.sim.WNTRSimulator(_wn, mode='PDD')
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
            unique_results = 'NO EFFECTED NODES'
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
        node.nominal_pressure = p_nom
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
        pipe_sim = wntr.sim.WNTRSimulator(_wn, mode='PDD')
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
            unique_results = 'NO EFFECTED NODES'
    finally:
        with open(results_dir + pipe_name + '.json', 'w') as fp:
            json.dump(unique_results, fp)
        return (pipe_name, unique_results)
