# -*- coding: utf-8 -*-
"""
Created on Wed Sep  4 08:42:03 2019

@author: PHassett
"""
import os
import json
import yaml
import numpy as np
import wntr
from wntr.epanet import FlowUnits


def inp_to_geojson(wn, to_file=True):
    """
    Write a minimal geojson representation of the Water Network.

    Parameters
    ----------
    wn: wntr WaterNetworkModel object
        The network to be make the geojson from
    to_file: Boolean, default=False
        To save the geojson representation as a file in the directory of the
        inp file
    Returns
    -------
    wn_geojson: dict in geojson format
        geojson spatial representation of the water network
    """
    inp_path = os.path.abspath(wn.name)
    # Translate the nodes to geojson.
    wn_geojson = {"type": "FeatureColllection",
                  "features": []
                  }
    for name, node in wn.nodes():
        feature = {"type": "Feature",
                   "geometry": {"type": "Point",
                                "coordinates": list(node.coordinates)
                                },
                   "id": name,
                   "properties": {"ID": name,
                                  }
                   }
        if node.node_type == 'Junction':
            feature['properties']["Base Demand (gpm)"] = node.base_demand/FlowUnits.GPM.factor
        else:
            feature['properties']["Base Demand (gpm)"] = node.node_type
        wn_geojson["features"].append(feature)
    # Translate the links to geojson.
    for name, link in wn.links():
        link = wn.get_link(link)
        start = list(link.start_node.coordinates)
        end = list(link.end_node.coordinates)
        feature = {"type": "Feature",
                   "geometry": {"type": "LineString",
                                "coordinates": [start, end]
                                },
                   "id": name,
                   "properties": {"ID": name
                                  }
                   }
        link_type = link.link_type
        if link_type == 'Pump':
            feature['properties']["Pipe Diameter (in)"] = "Pump"
        else:
            feature['properties']["Pipe Diameter (in)"] = round(link.diameter * 39.3701)
        wn_geojson["features"].append(feature)
    if to_file:
        # Write out the network to the file.
        output_file = inp_path.split('.inp')[0] + '.json'
        with open(output_file, 'w') as fp:
            json.dump(wn_geojson, fp)
    return wn_geojson


def _criticality_yml_to_geojson(wn, yml_file, pop, to_file=False):
    # Calculate population if it is not defined
    if pop is None:
        pop = wntr.metrics.population(wn)
    # Load each results file and generate a geojson file mapping the results.
    with open(yml_file, 'r') as fp:
        summary = yaml.load(fp, Loader=yaml.BaseLoader)
    # Make the GEOJson FeatureCollection object.
    collection = {"type": "FeatureColllection",
                  "features": []
                  }
    # Add a feature for each critical componenet.
    for key, val in summary.items():
        if key in wn.node_name_list:
            node = wn.get_node(key)
            feature = {"type": "Feature",
                       "geometry": {"type": "Point",
                                    "coordinates": list(node.coordinates)
                                    },
                       "properties": {"ID": key,
                                      "impact": val,
                                      "Base Demand (gpm)": np.round(node.base_demand/FlowUnits.GPM.factor, decimals=2)
                                      }
                       }
        elif key in wn.link_name_list:
            link = wn.get_link(key)
            start = list(link.start_node.coordinates)
            end = list(link.end_node.coordinates)
            feature = {"type": "Feature",
                       "geometry": {"type": "LineString",
                                    "coordinates": [start, end]
                                    },
                       "properties": {"ID": key,
                                      "impact": val,
                                      "Pipe Diameter (in)": np.round(link.diameter * 39.3701)
                                      }
                       }
        if type(val) is dict:
            feature["properties"]["Nodes Impacted"] = len(val.keys())
            pop_impacted = 0
            for node in val.keys():
                pop_impacted += pop[node]
            feature["properties"]["Population Impacted"] = pop_impacted
        elif val == 'NO EFFECTED NODES':
            feature["properties"]["Nodes Impacted"] = "NO EFFECTED NODES"
            feature["properties"]["Population Impacted"] = "NO EFFECTED NODES"
        elif 'failed:' in val:
            feature["properties"]["Nodes Impacted"] = "SIMULATION FAILED"
            feature["properties"]["Population Impacted"] = "SIMULATION FAILED"
        collection["features"].append(feature)
    if to_file:
        with open(yml_file.split('.yml')[0] + ".json", 'w') as fp:
            json.dump(collection, fp)
    return collection
