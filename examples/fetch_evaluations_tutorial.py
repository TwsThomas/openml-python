"""
=================
Fetch Evaluations
=================

A tutorial on how to fetch evalutions of a task.

Evalutions contain a concise summary of the results of all runs made. Each evaluation
provides information on the dataset used, the flow applied, the setup used, the metric
evaluated, and the result obtained on the metric, for each such run made. These collection
of results can be used for efficient benchmarking of an algorithm and also allow transparent
reuse of results from previous experiments on similar parameters.
"""

############################################################################
import openml
from pprint import pprint

############################################################################
# Listing evaluations
# *******************
# Evaluations can be retrieved from the database in the chosen output format
# Required filters can be applied to retrieve results from runs as required

# We shall retrieve a small set (only 10 entries) to test the listing function for evaluations
openml.evaluations.list_evaluations(function='predictive_accuracy', size=10,
                                    output_format='dataframe')

# Using other evaluation metrics, 'precision; in this case
evals = openml.evaluations.list_evaluations(function='precision', size=10,
                                            output_format='dataframe')

# Querying the returned results for precision above 0.98
pprint(evals[evals.value > 0.98])

#############################################################################
# View a sample task
# ==================
# Over here we shall briefly take a look at the details of the task we'll use in this example

# We will start by displaying a simple *supervised classification* task:
task_id = 167140        # https://www.openml.org/t/167140
task = openml.tasks.get_task(task_id)
pprint(vars(task))

#############################################################################
# Obtaining all the evaluations for the task
# ==========================================
# We'll now obtain all the runs that were made for the task we displayed previously
# Note that we now filter the evaluations based on another parameter 'task'

metric = 'predictive_accuracy'
evals = openml.evaluations.list_evaluations(function=metric, task=[task_id],
                                            output_format='dataframe')
# Displaying the first 10 rows
pprint(evals.head(n=10))
# Sorting the evaluations in decreasing order of the metric chosen
evals = evals.sort_values(by='value', ascending=False)
print("\nDisplaying head of sorted dataframe: ")
pprint(evals.head())

#############################################################################
# Obtain CDF of metric for chosen task
# ************************************
# We shall now analyse how the performance of various flows have been to address
# this chosen task, by seeing the likelihood of the accuracy obtained across all runs.
# We shall now plot a cumulative distributive function (CDF) for the accuracy obtained.

from matplotlib import pyplot as plt


def plot_cdf(values, metric='predictive_accuracy'):
    max_val = max(values)
    n, bins, patches = plt.hist(values, density=True, histtype='step',
                                cumulative=True, linewidth=3)
    patches[0].set_xy(patches[0].get_xy()[:-1])
    plt.xlim(max(0, min(values) - 0.1), 1)
    plt.title('CDF')
    plt.xlabel(metric)
    plt.ylabel('Likelihood')
    plt.grid(b=True, which='major', linestyle='-')
    plt.minorticks_on()
    plt.grid(b=True, which='minor', linestyle='--')
    plt.axvline(max_val, linestyle='--', color='gray')
    plt.text(max_val, 0, "%.3f" % max_val, fontsize=9)
    plt.show()


plot_cdf(evals.value, metric)
# This CDF plot shows that for the given task, based on the results of the
# runs uploaded, it is almost certain to achieve an accuracy above 52%, i.e.,
# with non-zero probability. While the maximum accuracy seen till now is 96.5%.

#############################################################################
# Compare top 10 performing flows
# *******************************
# Let us now try to see which flows generally performed the best for this task.
# To this effect, we shall compare the top performing flows.

import numpy as np
import pandas as pd


def plot_flow_compare(evaluations, top_n=10, metric='predictive_accuracy'):
    # Collecting the top 10 performing unique flow_id
    flow_list = evaluations.flow_id.unique()[:top_n]

    df = pd.DataFrame()
    # Creating a data frame containing only the metric values of the selected flows
    #   assuming evaluations is sorted in decreasing order of metric
    for i in range(len(flow_list)):
        df = pd.concat([df, pd.DataFrame(evaluations[evaluations.flow_id == flow_list[i]].value)],
                       ignore_index=True, axis=1)
    fig, axs = plt.subplots()
    df.boxplot()
    axs.set_title('Boxplot comparing ' + metric + ' for different flows')
    axs.set_ylabel(metric)
    axs.set_xlabel('Flow ID')
    axs.set_xticklabels(flow_list)
    axs.grid(which='majpr', linestyle='-', linewidth='0.5', color='gray')
    axs.minorticks_on()
    axs.grid(which='minor', linestyle='--', linewidth='0.5', color='gray')
    # Counting the number of entries for each flow in the data frame
    #   which gives the number of runs for each flow
    flow_freq = list(df.count(axis=0, numeric_only=True))
    for i in range(len(flow_list)):
        axs.text(i + 1.05, np.nanmin(df.values), str(flow_freq[i]) + '\nrun(s)', fontsize=7)
    plt.show()


plot_flow_compare(evals, metric=metric, top_n=10)
# The boxplots below show how the flows perform across multiple runs on the chosen
# task. The green horizontal lines represent the median accuracy of all the runs for
# that flow (number of runs denoted at the bottom of the boxplots). The higher the
# green line, the better the flow is for the task at hand. The ordering of the flows
# are in the descending order of the higest accuracy value seen under that flow.
