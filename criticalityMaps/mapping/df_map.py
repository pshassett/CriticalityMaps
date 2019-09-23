# -*- coding: utf-8 -*-
"""
Created on Mon Sep  9 13:12:07 2019

@author: PHassett
"""
import os
import copy
import jinja2
import pandas as pd
import wntr


class wn_dataframe(object):
    '''
    A WaterNetwork Dataframe class specifically designed for mapping network
    components and their attributes

    wn: wntr WaterNetworkModel

        WaterNetworkModel of interest

    node_data: pandas DataFrame or other object than can be converted to a
        DataFrame by pd.DataFrame(node_data).

        data indexed by node id

    link_data: pandas DataFrame

        data indexed by link id

    '''
    def __init__(self, wn, node_data=None, link_data=None):
        self._wn = copy.deepcopy(wn)
        # Fill the dataframes with network  coordinates to start with.
        node_coordinates = {}
        for name, node in self._wn.nodes():
            node_coordinates[name] = list(node.coordinates)
        node_coordinates = pd.DataFrame({'coordinates': node_coordinates})

        link_coordinates = {}
        for name, link in self._wn.links():
            start = list(link.start_node.coordinates)
            end = list(link.end_node.coordinates)
            link_coordinates[name] = [start, end]
        link_coordinates = pd.DataFrame({'coordinates': link_coordinates})

        # Add any other data that was specified in initialization
        self.node_data = node_coordinates.join(pd.DataFrame(node_data))
        self.link_data = link_coordinates.join(pd.DataFrame(link_data))

    def make_map(self, output_file=None, map_columns=[],
                 tooltip_columns=[], geojson_layers={}):
        """
        Make a .html web map of the wn and any data contained in the wn_dataframe

        Parameters
        ----------

        center: list of floats
            [lat, long] for the center point of the map.

        output_file: str/path-like
            path and .html file name for map output.
            Defaults to the name of the wn .inp file in the working directory.

        map_columns: list, optional
            list of column names in the wn_dataframe to be added as map layers

            Defaults to an empty list: [].

        tooltip_columns: list, optional
            list of column names in the wn_dataframe to be added to the
            informational tooltip that appears when hovering over network
            components with mouse.

            Defaults to an empty list: [].

        geojson_layers: dict, optional
            dict with layer names as keys and geojson objects or paths to
            geojson files as values.

            To custom style the layer, specify add a 'style' attribute as a
            Leaflet path-option (https://leafletjs.com/reference-1.5.0.html#path-option)
            to the 'properties' of each feature of the geojson object.

            For example:

                {"geometry": [0.00, 1.00],"id": "a point","properties":{"style": {"fillColor": "#fe943f", "fillOpacity": 0.5, "weight": 0}},'type': 'Point'}

            Defaults to None.

        """
        # Define the output file.
        if output_file is None:
            output_file = './' + os.path.basename(self._wn.name).split('.inp')[0] + '_map.html'
        # Sort map_columns into seperate node and link dicts with quartiles
        node_map_fields = {}
        link_map_fields = {}
        for col in map_columns:
            quartiles = {}
            if col in self.node_data.columns:
                quartiles[1] = self.node_data[col].max()
                quartiles[0] = self.node_data[col].min()
                col_range = quartiles[1] - quartiles[0]
                quartiles[0.75] = quartiles[0] + col_range * 0.75
                quartiles[0.5] = quartiles[0] + col_range * 0.5
                quartiles[0.25] = quartiles[0] + col_range * 0.25
                node_map_fields[col] = quartiles
            elif col in self.link_data.columns:
                quartiles[1] = self.link_data[col].max()
                quartiles[0] = self.link_data[col].min()
                col_range = quartiles[1] - quartiles[0]
                quartiles[0.75] = quartiles[0] + col_range * 0.75
                quartiles[0.5] = quartiles[0] + col_range * 0.5
                quartiles[0.25] = quartiles[0] + col_range * 0.25
                link_map_fields[col] = quartiles
            else:
                raise KeyError('map_columns must be columns of data that \
already exist in the wn_dataframe.')
        # Sort tooltip_columns into seperate node and link lists
        node_tooltip_fields = []
        link_tooltip_fields = []
        for col in tooltip_columns:
            if col in self.node_data.columns:
                node_tooltip_fields.append(col)
            elif col in self.link_data.columns:
                link_tooltip_fields.append(col)
            else:
                raise KeyError('tooltip_columns must be columns of data that \
already exist in the wn_dataframe.')
        # Get the set of all node fields and all link fields
        node_field_set = list(set(node_tooltip_fields).union(
                              set(node_map_fields.keys())))
        link_field_set = list(set(link_tooltip_fields).union(
                              set(link_map_fields.keys())))
        # Capture our current directory.
        THIS_DIR = os.path.dirname(os.path.abspath(__file__))
        # Create the jinja2 environment.
        # Notice the use of trim_blocks, which greatly helps control whitespace.
        j2_env = jinja2.Environment(loader=jinja2.FileSystemLoader(THIS_DIR),
                                    trim_blocks=True)
        with open(output_file, 'w') as fp:
            fp.write(j2_env.get_template(
                    './templates/dataframe_map_template.html').render(
                    node_data=self.node_data,
                    node_map_fields=node_map_fields,
                    node_tooltip_fields=node_tooltip_fields,
                    node_field_set=node_field_set,
                    link_data=self.link_data,
                    link_map_fields=link_map_fields,
                    link_tooltip_fields=link_tooltip_fields,
                    link_field_set=link_field_set,
                    geojson_layers=geojson_layers
                    )
            )
