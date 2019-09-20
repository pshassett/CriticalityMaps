Mapping
=======
.. highlight:: python

.. _criticality-maps:

Criticality Maps
----------------
There are built in methods to create interactive maps from the results of completed 
criticality analyses. To create a criticality map, enter the wn, the criticality results file,
and the map center into the :func:`.make_criticality_map` function:
::
  center = [40, -100]
  # Fire criticality example
  cm.make_criticality_map(wn, fire_criticality_summary.yml, center)
  # Pipe criticality example
  cm.make_criticality_map(wn, pipe_criticality_summary.yml, center)

.. raw:: html
    
    <div style="position: relative; padding-bottom: 56.25%; height: 600; overflow: hidden; max-width: 100%; height: auto;">
        <iframe src="_static/fire_criticality_summary_map.html" frameborder="1" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe>
    </div>
    <br>
    <br>
    <div style="position: relative; padding-bottom: 56.25%; height: 600; overflow: hidden; max-width: 100%; height: auto;">
        <iframe src="_static/pipe_criticality_summary_map.html" frameborder="1" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe>
    </div>



See the api documentation on :func:`.make_criticality_map` for all available function options.

Dataframe-based Maps
--------------------
CriticalityMaps also has the ability to create more general network maps based on the
:class:`.wn_dataframe` class. A :class:`.wn_dataframe` object is composed of the a wn 
object, a node_data 
`pandas DataFrame <https://pandas.pydata.org/pandas-docs/stable/getting_started/dsintro.html#dataframe>`_ indexed by the water network's node ID's, and a 
link_data `pandas DataFrame <https://pandas.pydata.org/pandas-docs/stable/getting_started/dsintro.html#dataframe>`_ indexed by the water network's link ID's.

Initializing a wn_dataframe object
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The initialization of a wn_dataframe object
requires a `WNTR WaterNetworkModel (wn) <https://wntr.readthedocs.io/en/latest/waternetworkmodel.html>`_ object as input. The node_data and link_data DataFrames
are automatically created and populated with a 'coordinates' column, containing the coordinates
of those network components.::
    # The most basic initialization of a wn_dataframe object
    my_wn_dataframe = cm.wn_dataframe(wn)
    
Adding data to the wn_dataframe
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
To add data to the wn_dataframe, standard methods for adding columns to an existing 
`pandas DataFrame <https://pandas.pydata.org/pandas-docs/stable/getting_started/dsintro.html#dataframe>`_ can be used:
::
    # collect some data indexed by node ID
    elevations = {}
    for name, node in wn.nodes:
        elevations[name] = node.elevations
    # add the node data as a new column labeled "elevation"
    my_wn_dataframe.node_data["elevation"] = elevations
    
    # wn querys are another great way to collect data on the water network model
    base_demands = wn.query_node_attribute("base_demand")   
    # add the node data as a new column labeled "base demand"
    my_wn_dataframe.node_data["base demand"] = base_demands
   
    # collect some other data indexed by link ID
    diameters = wn.query_link_attribute("diameter")
    # add the data as a new column labeled "diameter"
    my_wn_dataframe.link_data["diameter"] = diameters
    

Optionally, initial node and link data indexed by component ID can also be added to the object at 
initialization:
::
    my_wn_dataframe = cm.wn_dataframe(wn, 
                                      node_data={"elevation": elevations,"base demand": base_demands},
                                      link_data={"diameter": diameters})
    
The data entered at initialization can be a DataFrame, a dict of dicts/Series,
or any other object that can be converted to a dataframe by `pandas.DataFrame() <https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html>`_,
so long as it is indexed by node/link ID.

Mapping the wn_dataframe
^^^^^^^^^^^^^^^^^^^^^^^^
To map the data stored in the :class:`.wn_dataframe` on the water network, simply call the :meth:`.make_map` function 
of the wn_dataframe. Specify which fields will appear in tooltips and which fields are added as 
map overlays on the water network (Note: any fields added to map_columns will automatically be 
added to the tooltip when that layer is activated on the map).
::
    my_wn_dataframe.make_map(center,
                             map_columns=["base demand", "diameter"],
                             tooltip_columns=["elevation"])

.. raw:: html
    
    <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; height: auto;">
        <iframe src="_static/Net3_map.html" frameborder="0" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe>
    </div>

See the :class:`.wn_dataframe` class and its :meth:`.make_map` method in the api documentation 
for more details on implementation options.
