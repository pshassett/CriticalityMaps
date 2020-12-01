# -*- coding: utf-8 -*-
"""
Created on Tue Mar 10 17:12:22 2020

@author: jhogge
"""
import wntr
import criticalityMaps as cm


''' Gather WNTR network from input file '''
inp_file = 'Net3.inp' 
wn = wntr.network.WaterNetworkModel(inp_file)
G = wn.get_graph()


# Pick criticality type, whether to post-process, whether to use multiprocessing
criticality_type = 'segment' # 'pipe', 'fire', or 'segment'; criticality analysis type
post_process = True # True or False; post-processing capability 
multiprocess = False # True of False; multiprocessing capability

if criticality_type == 'segment':
    # Generate valve layer and run segmentation algorithm
    valve_layer = wntr.network.generate_valve_layer(wn, n=2, seed=123)
    node_segments, link_segments, seg_sizes = wntr.metrics.valve_segments(G, valve_layer)    
    # Run segment criticality analysis
    cm.criticality.segment_criticality_analysis(wn, link_segments, node_segments, 
                                                valve_layer,
                                                output_dir="./segment_criticality",
                                                post_process=post_process, 
                                                multiprocess=multiprocess
                                                )

if criticality_type == 'pipe':
    # Run pipe criticality analysis
    cm.criticality.pipe_criticality_analysis(wn, 
                                             output_dir="./pipe_criticality", 
                                             post_process=post_process, 
                                             multiprocess=multiprocess
                                             )
    
if criticality_type == 'fire':
    # Run fire criticality analysis
    cm.criticality.fire_criticality_analysis(wn, 
                                             output_dir="./fire_criticality",
                                             post_process=post_process, 
                                             multiprocess=multiprocess
                                             )
