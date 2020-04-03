Criticality Analysis
====================
The criticality analysis options currently supported in criticalityMaps
are fire and pipe criticality analysis.

Fire Criticality
^^^^^^^^^^^^^^^^
Fire criticality analysis is an assessment of the expected impact of
firefighting demands at a given location.  The analysis process consists of 
applying a fire fighting demand and measuring the impact on surrounding 
customers for all possible firefighting points in the system. Key parameters
to customize this analysis are:

* firefighting demand (defaults to 1500 gpm)
* duration of the fire demand (defaults to 2 hr)
* diameter tresholds of pipes that will have fire demands applied (defaults to all pipes between 6 and 8in in diameter)
 
See :func:`.fire_criticality_analysis` in the api documentation for more details on
the customization options.

Pipe Criticality
^^^^^^^^^^^^^^^^
Pipe criticality analysis provides insight on where the most critical 
pipes of the system are. To determine the criticality of a single pipe, the 
pipe is closed during a simulation and the impact on surrounding customers 
is measured. This process is then repeated for all pipes of interest 
in the system. Key parameters to customize this analysis are:

* duration of the pipe closure (defaults to 48 hr)
* diameter thresholds of pipes that will have pipe closures applied (defaults to all pipes greater than 12in in diameter)

See :func:`.pipe_criticality_analysis` in the api documentation for more details on
the customization options.

Segment Criticality
^^^^^^^^^^^^^^^^
Segment criticality analysis provides insight on where the most critical 
segments of the system are. Segments are defined as groups of pipes that are
connected within the same set of valves. In order to close one pipe in a 
segment, all the pipes in the segment must be closed. To determine the 
criticality of a single segment, all of the pipes in a segment are closed 
during a simulation and the impact on surrounding customers is measured. 
This process is then repeated for all segments of interest in the system. 
Key parameters to customize this analysis are:

* duration of the segment closure (defaults to 48 hr)
* diameter thresholds of pipes that will have pipe closures applied (defaults to all pipes greater than 12in in diameter)

See :func:`.segment_criticality_analysis` in the api documentation for more details on
the customization options.

Output and Post-processing
^^^^^^^^^^^^^^^^^^^^^^^^^^
The core output of the criticality analyses is a [key:value] .yml file log where each key is the
ID of a node/link tested and each value is the result of that test. Any nodes that fall below the 
minimum pressure threshold (a settable parameter ``p_min``) of a pressure driven demand
simulation recieved **none** of their requested demand during that period and are thus deemed 
impacted.

* If there were nodes impacted at a given test node/link, the value for that node/link will beanother set of [key:value] entries with the impacted node's ID as the key and its lowest observed pressure as the value.
* If there was no impact at a given test node/link, the value will be "NO AFFECTED NODES".
* Otherwise, if the simulation failed at a given test node/link, the value will be "failed:", followed by the exception message associated with the failure.

Below is an example of the .yml output demonstrating these three possible cases.
::
    # a node/link with multiple impacted nodes
    '123':
        '23': 11.33654
        '34': 5.345237
        '56': 10.21345
        '67': 9.234789
    # a node/link with no impacted nodes
    '35': NO AFFECTED NODES
    # a node/link with failed simulation
    '773': "failed: Simulation did not converge. Reached maximum number of iterations: 499"

By default, the criticality analysis methods will additionally create the following outputs:

* a .csv file log of the population and nodes impacted at each node/link tested
* .pdf maps of the population and nodes impacted at each node/link tested

This behavior can be overridden by setting the post_process argument to False. The results
summary .yml file will still be produced and can be then custom-processed with the :func:`.process_criticality`
function. See the api documentation on :func:`.process_criticality` for more details.

The results of criticality analyses can also be displayed on an interactive map as demonstrated in 
the :ref:`criticality-maps` section.

Multiprocessing
^^^^^^^^^^^^^^^
CriticalityMaps has the built-in ability to execute criticality 
analysis with mulitiprocessing, enabling multiple processors to work
on a set of simulations at once.  This offers a significant speedup in 
execution time, especially in cases with a large number of simulations and extra computing capacity available.

To enable multiprocessing on your criticlaity analysis, in addition to setting
the multiprocess keyword argument to True, the code the criticality analysis
must be wrapped in a ``if __name__ == "__main__":`` block as shown below.
::    
    if __name__ == "__main__":
        cm.fire_criticality_analysis(wn, multiprocess=True)
        cm.pipe_criticality_analysis(wn, multiprocess=True)

By default criticalityMaps will use about 66.7% of the machine's cpu. The numbers of cpu's
used can be increased or decreased used by assigning a value for ``num_processors``. See 
the api documentation on :func:`.fire_criticality_analysis` and :func:`.pipe_criticality_analysis`
for more details on the multiprocessing options.

