# helper.py
# Name: Hidetomi Nitta

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import cm
from scipy.stats import shapiro, mannwhitneyu,levene
import matplotlib, scipy, subprocess, os
from matplotlib.backends.backend_pdf import PdfPages
from fit import Fit

matplotlib.use('Agg')


def plot(df: pd.DataFrame, axs: matplotlib.axes.Axes | np.ndarray, drug: str,
         strains: list | np.ndarray, timepoints: list | np.ndarray, subplot: int = 0, save_type=None,
         gr: bool = False) -> None:
    """"Plots all replicates for a given drug. Allows for the overlay of different strains or timepoints.

    Keyword arguments:
    :param df: pd.DataFrame of MK DiaMOND pipeline
    :param drug: singular drug or drug combination
    :param strains: list of strains where each strain is a str
    :param axs: matplotlib.axes.Axes from plt.subplots
    :param subplot: index of axs object to draw on
    """

    # Plot appearance for better performance
    plt.rcParams['font.family'] = 'Arial'
    plt.rcParams['path.simplify'] = True
    plt.rcParams['path.simplify_threshold'] = 0.75

    colors = plt.cm.Set1.colors
    strain_palette = dict(zip(sorted(strains),colors[:len(strains)]))
    timepoint_palette = dict(zip(sorted(timepoints),colors[:len(timepoints)]))

    # strain_colors = {'EL': 'magenta', 'H37Rv': 'blue', 'bioA': 'red', 'bioBop': 'mediumseagreen'}
    f = Fit()
    seen_strains = seen_timepoints = set()
    rep_locs = list()

    # Row indices for all (three) replicates matching the specified strain(s), drug, and timepoint(s) criteria
    row_indices = df[(df['Drug'] == drug) & (df['Strain'].isin(strains)) & (df['Timepoint'].isin(timepoints))].index

    for i, row_idx in enumerate(row_indices): # for each replicate, for each strain
        row = df.loc[row_idx]
        strain = row['Strain']
        timepoint = row['Timepoint']
        algo = row['Best Algo']

        ## Adjusting color and legend depending on len() of strains and timepoints
        # Single strain and timepoint
        if len(strains) == 1 and len(timepoints) == 1:
            color = ['red','blue','green'][i]
            rep_locs.append(row_idx if algo else algo) # only returns non-empty list for single strain and timepoint
            legend_label = f'R{i+1}'

        # Multiple strains and single timepoint
        elif len(strains) > 1 and len(timepoints) == 1:
            color = strain_palette[strain]
            legend_label = strain if strain not in seen_strains else ""
            # color = strain_colors[strain]
            if strain not in seen_strains:  # ensure non-redundant legend labels for multiple strains
                seen_strains.add(strain)

        # Single strain and multiple timepoints
        elif len(strains) == 1 and len(timepoints) > 1:
            color = timepoint_palette[timepoint]
            legend_label = timepoint if timepoint not in seen_timepoints else ""

            if timepoint not in seen_timepoints:  # ensure non-redundant legend labels for multiple timepoints
                seen_timepoints.add(timepoint)

        else:
            return "Can't have multiple strains AND timepoints!"

        x = row['Volume']
        y = row['Growth Inhibitions'] if not gr else row['gr']['norm_gr']

        if isinstance(axs, np.ndarray): # checks for existence of subplot
            if axs.ndim == 2: # if more than one row to display plots
                axs = axs.flatten()[subplot]
            else:
                axs = axs[subplot]

        if algo is not None:
            if gr:
                grinf = row['gr']['Einf']
                ec50 = row['gr']['EC50']
                hill_slope = row['gr']['Hill Slope']

                y_pred = f.GR_Hill(x, grinf, ec50, hill_slope)
            else:
                einf = row[algo]['Einf']
                ec50 = row[algo]['EC50']
                hill_slope = row[algo]['Hill Slope']

                y_pred = f.Hill(np.array(x), einf, ec50, hill_slope)

            axs.plot(np.log10(x), y_pred, color=color, ls='--', label=legend_label, alpha=0.5)

        axs.scatter(np.log10(x), y, marker='o', color=color, antialiased=False, alpha=0.6)
        axs.grid(color='white', linestyle='-.', linewidth=0.9, alpha=0.9)


    if save_type == 'pdf':
        axs.set_title(f"{drug}")
    else:
        axs.set_title(f"{drug} {'Dose response' if not gr else 'Growth rate'} curves for {', '.join(strains)}")

    axs.set(xlabel='Volume (log10) (nL)', ylabel=f'{'Growth inhibitions' if not gr else 'Normalized growth rate'}')
    axs.legend(frameon=False)

    return rep_locs

def generate_plot_images(df, drugs, strains, timepoints, save_path, save_type=None):
    """"Generates individual dose response plot as png or as a batch of 3 plots per page in a pdf file

        Keyword arguments:
        :param df: pd.DataFrame of MK DiaMOND pipeline
        :param drugs: np.ndarray or list() of drugs for which a plot will be made
        :param strains: list() of strains to superimpose on each plot
        :param save_path: file path to save png images (pathlib obj)
    """

    if save_type == 'pdf':
        with PdfPages(unique_filename(save_path / 'hillcurves.pdf')) as pdf:
            batch_size = 3
            batches = [drugs[i:i + batch_size] for i in range(0, len(drugs), batch_size)]

            for b in batches:  # each batch is a subplot
                fig, axs = plt.subplots(nrows=1, ncols=3, facecolor='white', figsize=(15, 4))
                plt.suptitle(f'Dose Response Curves for {", ".join(strains)}')

                for idx, drug in enumerate(b):
                    plot(df, axs, strains=strains, drug=drug, timepoints=timepoints,
                         subplot=idx, save_type='pdf', gr=False)
                pdf.savefig(fig)
                plt.close(fig)

    else:

        for idx, d in enumerate(drugs):
            fig, axs = plt.subplots(1, 1, facecolor='white')
            plot(df, axs, drug = d, strains = strains, subplot=0)
            fig.savefig(save_path + f"{", ".join(strains)}_{d}.png")
            plt.close(fig)

    # subprocess.run(["open", save_path])

    return

def unique_filename(base_filename):
    file_name, ext = os.path.splitext(base_filename)
    counter = 1
    new_file_name = f"{file_name}_{counter}{ext}"

    while os.path.exists(new_file_name):
        counter += 1
        new_file_name = f"{file_name}_{counter}{ext}"

    return new_file_name

def twogroup_stat(df1,df2): # certain column, with certain metric
    """Run statistics on phase 1 of biotin-auxotroph H37Rv experiments

    Keyword arguments:
    :param df1: expects pd.DataFrame column e.g. df['Einf']. Does not factor in NaN.
    :param df2: same as above, but different group for comparison (but same metric)
    """

    sample_size = (len(df1), len(df2))

    # normality
    s1_stat, s1_p = shapiro(df1)
    s2_stat, s2_p = shapiro(df2)

    # variance
    l_stat, l_p = levene(df1,df2)


    if s1_p > 0.05 and s2_p > 0.05:

        if l_p > 0.05 and sample_size[0] == sample_size[1]:
            t_stat, t_p = scipy.stats.ttest_ind(df1,df2)

            return {'t':t_p}, sample_size

        else:
            w_stat, w_p = scipy.stats.ttest_ind(df1,df2,equal_var=False)

            return {'w':w_p}, sample_size

    else:

        if l_p > 0.05:
            mw_stat, mw_p = mannwhitneyu(df1,df2)

            return {'mw':mw_p}, sample_size

        else:
            print('???')

    return '???'


def intersection_filter(df1, df2):
    """Find intersection of two dataframes. Typically used in conjunction with twogroup_stat()

    Keyword arugments:
    :param df1: column view of a pd.DataFrame
    :param df2: column view of a pd.DataFrame
    """

    intersection = set(df1['Drug']).intersection(set(df2['Drug']))

    return df1[df1['Drug'].isin(intersection)], df2[df2['Drug'].isin(intersection)]



if __name__ == "__main__":
    print('helper.py was run')

