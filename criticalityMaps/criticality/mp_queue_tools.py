# -*- coding: utf-8 -*-
"""
Created on Tue Jun  4 07:59:47 2019

@author: PHassett
"""
import multiprocessing as mp
import time


def _execute(function, arguments):
    result = function(*arguments)
    print('At {:24}, {:10} completed process: {:4}'.format(time.ctime(),
          mp.current_process().name, str(mp.current_process().pid)))
    return result


def _worker(input_queue, output_queue):
    for func, args in iter(input_queue.get, 'STOP'):
        result = _execute(func, args)
        output_queue.put(result)


def runner(tasks, num_processors):
    """
    Run the tasks specified across mutiple processors and return the
    results in a list.

    Parameters
    ----------
    tasks - list
        task list of the form [(func,(arg1, arg2,...,argN))]

    num_processors - int
        the number of processors to use

    Returns
    -------
    results - list
        list of func return objects for each task
    """
    # Handle undefined num_processors
    if num_processors is None:
        num_processors = int(mp.cpu_count() * 0.666)
    # Do some error checking for the number of processors
    elif type(num_processors) != int:
        raise ValueError('num_processors must of type int')
    elif num_processors < 1:
        raise Exception('num_processors must be greater than 1.')
    elif num_processors > mp.cpu_count():
        raise Exception('num_processors must be less than the total \
                         number of processors on the machine. Run:\n\
                         import multiprocessing as mp\n\
                         mp.cpu_count()\n\
                         to determine the number of processors.')

    # Create task and return queues.
    task_queue = mp.Queue()
    done_queue = mp.Queue()

    # Submit tasks to the task queue.
    for task in tasks:
        task_queue.put(task)

    # Start worker processes.
    for i in range(num_processors):
        mp.Process(target=_worker,
                   args=(task_queue, done_queue)
                   ).start()

    # Get the results and store them in a yaml-friendly object.
    results = []
    for i in range(len(tasks)):
        results.append(done_queue.get())

    # Stop all child processes.
    for i in range(num_processors):
        task_queue.put('STOP')

    # Return the results.
    return results
