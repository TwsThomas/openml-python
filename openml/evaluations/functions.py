import json
import xmltodict
import pandas as pd
import numpy as np
from typing import Union, List, Optional, Dict
import collections

import openml.utils
import openml._api_calls
from ..evaluations import OpenMLEvaluation
import openml


def list_evaluations(
    function: str,
    offset: Optional[int] = None,
    size: Optional[int] = None,
    id: Optional[List] = None,
    task: Optional[List] = None,
    setup: Optional[List] = None,
    flow: Optional[List] = None,
    uploader: Optional[List] = None,
    tag: Optional[str] = None,
    per_fold: Optional[bool] = None,
    sort_order: Optional[str] = None,
    output_format: str = 'object'
) -> Union[Dict, pd.DataFrame]:
    """
    List all run-evaluation pairs matching all of the given filters.
    (Supports large amount of results)

    Parameters
    ----------
    function : str
        the evaluation function. e.g., predictive_accuracy
    offset : int, optional
        the number of runs to skip, starting from the first
    size : int, optional
        the maximum number of runs to show

    id : list, optional

    task : list, optional

    setup: list, optional

    flow : list, optional

    uploader : list, optional

    tag : str, optional

    per_fold : bool, optional

    sort_order : str, optional
       order of sorting evaluations, ascending ("asc") or descending ("desc")

    output_format: str, optional (default='object')
        The parameter decides the format of the output.
        - If 'object' the output is a dict of OpenMLEvaluation objects
        - If 'dict' the output is a dict of dict
        - If 'dataframe' the output is a pandas DataFrame

    Returns
    -------
    dict or dataframe
    """
    if output_format not in ['dataframe', 'dict', 'object']:
        raise ValueError("Invalid output format selected. "
                         "Only 'object', 'dataframe', or 'dict' applicable.")

    per_fold_str = None
    if per_fold is not None:
        per_fold_str = str(per_fold).lower()

    return openml.utils._list_all(output_format=output_format,
                                  listing_call=_list_evaluations,
                                  function=function,
                                  offset=offset,
                                  size=size,
                                  id=id,
                                  task=task,
                                  setup=setup,
                                  flow=flow,
                                  uploader=uploader,
                                  tag=tag,
                                  sort_order=sort_order,
                                  per_fold=per_fold_str)


def _list_evaluations(
    function: str,
    id: Optional[List] = None,
    task: Optional[List] = None,
    setup: Optional[List] = None,
    flow: Optional[List] = None,
    uploader: Optional[List] = None,
    sort_order: Optional[str] = None,
    output_format: str = 'object',
    **kwargs
) -> Union[Dict, pd.DataFrame]:
    """
    Perform API call ``/evaluation/function{function}/{filters}``

    Parameters
    ----------
    The arguments that are lists are separated from the single value
    ones which are put into the kwargs.

    function : str
        the evaluation function. e.g., predictive_accuracy

    id : list, optional

    task : list, optional

    setup: list, optional

    flow : list, optional

    uploader : list, optional

    kwargs: dict, optional
        Legal filter operators: tag, limit, offset.

    sort_order : str, optional
        order of sorting evaluations, ascending ("asc") or descending ("desc")

    output_format: str, optional (default='dict')
        The parameter decides the format of the output.
        - If 'dict' the output is a dict of dict
        The parameter decides the format of the output.
        - If 'dict' the output is a dict of dict
        - If 'dataframe' the output is a pandas DataFrame
        - If 'dataframe' the output is a pandas DataFrame

    Returns
    -------
    dict of objects, or dataframe
    """

    api_call = "evaluation/list/function/%s" % function
    if kwargs is not None:
        for operator, value in kwargs.items():
            api_call += "/%s/%s" % (operator, value)
    if id is not None:
        api_call += "/run/%s" % ','.join([str(int(i)) for i in id])
    if task is not None:
        api_call += "/task/%s" % ','.join([str(int(i)) for i in task])
    if setup is not None:
        api_call += "/setup/%s" % ','.join([str(int(i)) for i in setup])
    if flow is not None:
        api_call += "/flow/%s" % ','.join([str(int(i)) for i in flow])
    if uploader is not None:
        api_call += "/uploader/%s" % ','.join([str(int(i)) for i in uploader])
    if sort_order is not None:
        api_call += "/sort_order/%s" % sort_order

    return __list_evaluations(api_call, output_format=output_format)


def __list_evaluations(api_call, output_format='object'):
    """Helper function to parse API calls which are lists of runs"""
    xml_string = openml._api_calls._perform_api_call(api_call, 'get')
    evals_dict = xmltodict.parse(xml_string, force_list=('oml:evaluation',))
    # Minimalistic check if the XML is useful
    if 'oml:evaluations' not in evals_dict:
        raise ValueError('Error in return XML, does not contain '
                         '"oml:evaluations": %s' % str(evals_dict))

    assert type(evals_dict['oml:evaluations']['oml:evaluation']) == list, \
        type(evals_dict['oml:evaluations'])

    evals = collections.OrderedDict()
    for eval_ in evals_dict['oml:evaluations']['oml:evaluation']:
        run_id = int(eval_['oml:run_id'])
        value = None
        values = None
        array_data = None
        if 'oml:value' in eval_:
            value = float(eval_['oml:value'])
        if 'oml:values' in eval_:
            values = json.loads(eval_['oml:values'])
        if 'oml:array_data' in eval_:
            array_data = eval_['oml:array_data']

        if output_format == 'object':
            evals[run_id] = OpenMLEvaluation(int(eval_['oml:run_id']),
                                             int(eval_['oml:task_id']),
                                             int(eval_['oml:setup_id']),
                                             int(eval_['oml:flow_id']),
                                             eval_['oml:flow_name'],
                                             eval_['oml:data_id'],
                                             eval_['oml:data_name'],
                                             eval_['oml:function'],
                                             eval_['oml:upload_time'],
                                             value, values, array_data)
        else:
            # for output_format in ['dict', 'dataframe']
            evals[run_id] = {'run_id': int(eval_['oml:run_id']),
                             'task_id': int(eval_['oml:task_id']),
                             'setup_id': int(eval_['oml:setup_id']),
                             'flow_id': int(eval_['oml:flow_id']),
                             'flow_name': eval_['oml:flow_name'],
                             'data_id': eval_['oml:data_id'],
                             'data_name': eval_['oml:data_name'],
                             'function': eval_['oml:function'],
                             'upload_time': eval_['oml:upload_time'],
                             'value': value,
                             'values': values,
                             'array_data': array_data}

    if output_format == 'dataframe':
        rows = [value for key, value in evals.items()]
        evals = pd.DataFrame.from_records(rows, columns=rows[0].keys())
    return evals


def list_evaluation_measures() -> List[str]:
    """ Return list of evaluation measures available.

    The function performs an API call to retrieve the entire list of
    evaluation measures that are available.

    Returns
    -------
    list

    """
    api_call = "evaluationmeasure/list"
    xml_string = openml._api_calls._perform_api_call(api_call, 'get')
    qualities = xmltodict.parse(xml_string, force_list=('oml:measures'))
    # Minimalistic check if the XML is useful
    if 'oml:evaluation_measures' not in qualities:
        raise ValueError('Error in return XML, does not contain '
                         '"oml:evaluation_measures"')
    if not isinstance(qualities['oml:evaluation_measures']['oml:measures'][0]['oml:measure'],
                      list):
        raise TypeError('Error in return XML, does not contain '
                        '"oml:measure" as a list')
    qualities = qualities['oml:evaluation_measures']['oml:measures'][0]['oml:measure']
    return qualities


def list_evaluations_setups(
        function: str,
        offset: Optional[int] = None,
        size: Optional[int] = None,
        id: Optional[List] = None,
        task: Optional[List] = None,
        setup: Optional[List] = None,
        flow: Optional[List] = None,
        uploader: Optional[List] = None,
        tag: Optional[str] = None,
        per_fold: Optional[bool] = None,
        sort_order: Optional[str] = None,
        output_format: str = 'dataframe'
) -> Union[Dict, pd.DataFrame]:
    """
    List all run-evaluation pairs matching all of the given filters
    and their hyperparameter settings.

    Parameters
    ----------
    function : str
        the evaluation function. e.g., predictive_accuracy
    offset : int, optional
        the number of runs to skip, starting from the first
    size : int, optional
        the maximum number of runs to show
    id : list[int], optional
        the list of evaluation ID's
    task : list[int], optional
        the list of task ID's
    setup: list[int], optional
        the list of setup ID's
    flow : list[int], optional
        the list of flow ID's
    uploader : list[int], optional
        the list of uploader ID's
    tag : str, optional
        filter evaluation based on given tag
    per_fold : bool, optional
    sort_order : str, optional
       order of sorting evaluations, ascending ("asc") or descending ("desc")
    output_format: str, optional (default='dataframe')
        The parameter decides the format of the output.
        - If 'dict' the output is a dict of dict
        - If 'dataframe' the output is a pandas DataFrame


    Returns
    -------
    dict or dataframe with hyperparameter settings as a list of tuples.
    """
    # List evaluations
    evals = list_evaluations(function=function, offset=offset, size=size, id=id, task=task,
                             setup=setup, flow=flow, uploader=uploader, tag=tag,
                             per_fold=per_fold, sort_order=sort_order, output_format='dataframe')

    # List setups
    # Split setups in evals into chunks of N setups as list_setups does not support large size
    df = pd.DataFrame()
    if len(evals) != 0:
        N = 100
        setup_chunks = np.split(evals['setup_id'].unique(),
                                ((len(evals['setup_id'].unique()) - 1) // N) + 1)
        setups = pd.DataFrame()
        for setup in setup_chunks:
            result = pd.DataFrame(openml.setups.list_setups(setup=setup, output_format='dataframe'))
            result.drop('flow_id', axis=1, inplace=True)
            # concat resulting setup chunks into single datframe
            setups = pd.concat([setups, result], ignore_index=True)
        parameters = []
        # Convert parameters of setup into list of tuples of (hyperparameter, value)
        for parameter_dict in setups['parameters']:
            if parameter_dict is not None:
                parameters.append([tuple([param['parameter_name'], param['value']])
                                   for param in parameter_dict.values()])
            else:
                parameters.append([])
        setups['parameters'] = parameters
        # Merge setups with evaluations
        df = pd.merge(evals, setups, on='setup_id', how='left')

    if output_format == 'dataframe':
        return df
    else:
        return df.to_dict(orient='index')
