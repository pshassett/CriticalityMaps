# -*- coding: utf-8 -*-
"""
Created on Wed Aug  7 18:41:45 2019

@author: PHassett
"""
import os
import json
import time
import jinja2
from criticalityMaps.mapping.geojson_handler import _criticality_yml_to_geojson, inp_to_geojson


def make_criticality_map(wn, results_file, output_file=None, pop=None):
    '''
    Make a criticality map from a criticality results file.


    Parameters
    ----------
    wn: wntr waternetwork model
        the wntr waternetwork model of interest

    results_file: str/path-like object
        path to the .yml results file from a criticality analysis

    output_file: str/path-like
            path and .html file name for map output.
            Defaults to the path of the results file with '.yml' replaced with
            '_map.html'

    pop: dict/Pandas Series, optional
        population estimate at each node. If None, will use
        wntr.metrics.population(wn).

        Defaults to None

    '''
    if output_file is None:
        output_file = results_file.split('.yml')[0] + "_map.html"
    # Produce a geojson layer for the wn
    wn_layer = inp_to_geojson(wn, to_file=False)
    # Produce a geojson layer for the criticality results
    criticality_layer = _criticality_yml_to_geojson(wn, results_file, pop)
    # Determine which template to use
    if 'fire' in results_file:
        html_template = './templates/fire_criticality_template.html'
        data_layer = {'Fire Criticality': criticality_layer}
    elif 'pipe' in results_file:
        html_template = './templates/pipe_criticality_template.html'
        data_layer = {'Pipe Criticality': criticality_layer}
    # Pass geojson layers to fill the template file
    _fill_criticality_template(html_template, wn_layer,
                               data_layer,
                               output=output_file)


def _fill_criticality_template(template_file, wn_geojson,
                               network_data_layers, output='./wn_map.html'):
    '''
    Create a leaflet map of the water network from a geojson representation.

    jinja2 interaction based on example at:
    https://gist.github.com/wrunk/1317933/d204be62e6001ea21e99ca0a90594200ade2511e

    Parameters
    ----------

    template_file: string/path-like object
            jinja2 html template file path

    wn_geojson: dict in geojson format
        geojson spatial representation of the water network

    network_data_layers: dict
            A dictionary of the form, {'Title for Layer1': layer1data},
            where 'layer1data' is a dictionary of the form {id, value},
            where id is a string and value is a float representing the value of
            a Water Network component for Layer1

    output: str/path-like object
            output path for the .html file

    '''
    # Capture our current directory.
    THIS_DIR = os.path.dirname(os.path.abspath(__file__))
    # Create the jinja2 environment.
    # Notice the use of trim_blocks, which greatly helps control whitespace.
    j2_env = jinja2.Environment(loader=jinja2.FileSystemLoader(THIS_DIR),
                                trim_blocks=True)
    # Load the wn geojson data.
    if type(wn_geojson) != dict:
        try:
            # Load the water network geojson file.
            with open(os.path.abspath(wn_geojson), 'r') as fp:
                wn_geojson = json.load(fp)
        except Exception as e:
            print("wn_geojson must either be a geojson FeatureCollection dict \
                  or a file path to a valid .json representatiom of the \
                  FeatureCollection.")
            raise e
    # Load additional data layer.
    data_layers = {}
    for name, data_layer in network_data_layers.items():
        if type(data_layer) != dict:
            try:
                # Load the water network geojson file.
                with open(os.path.abspath(data_layer), 'r') as fp:
                    data_layer = json.load(fp)
            except Exception as e:
                print("wn_geojson must either be a geojson FeatureCollection dict \
                      or a file path to a valid .json representation of the \
                      FeatureCollection.")
                raise e
        data_layers[name] = data_layer
    # Fill the jinja2 html template and save the file
    with open(output, 'w') as fp:
        fp.write(j2_env.get_template(template_file).render(
                wn_geojson=wn_geojson,
                data_layers_geojson=data_layers)
        )
