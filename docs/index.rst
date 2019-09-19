CriticalityMaps
===============================================

CriticalityMaps is a `WNTR <https://wntr.readthedocs.io/en/latest/index.html>`_-based 
utility for running large sets of fire and pipe criticality simulations and visualizing
the results on interactive leaflet.js html maps. 

Additionally, CriticalityMaps has mapping utilities that can be used to visualize 
any other attributes of the network on an interactive .html map.

Example Fire Criticality interactive map. Click on a highlited pipe to see the impact of its closure.

.. raw:: html    

    <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; height: auto;">
        <iframe src="_static/pipe_criticality_summary_map.html" frameborder="0" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe>
    </div>

**A word on units**
"""""""""""""""""""
All values in CriticalityMaps are in SI for conformity with the 
`WNTR units conventions <https://wntr.readthedocs.io/en/latest/units.html>`_.
All unit conversions are left to the user.

Overview
========
CriticalityMaps is composed of the following main components:

.. toctree::
   :maxdepth: 2

   criticality
   mapping
   apidoc/modules


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Funding Disclaimer
==================
The U.S. Environmental Protection Agency (EPA) through its Office of Research and Development funded and collaborated in the research described herein under Interagency Agreement (IA #92432901) with the Department of Energy's Oak Ridge Associated Universities (ORAU).
