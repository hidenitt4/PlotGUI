# helper.py
# Name: Hidetomi Nitta

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib, scipy, subprocess, os
matplotlib.use('TkAgg')
from matplotlib.backends.backend_pdf import PdfPages
from pathlib import Path
from fit import Fit

plt.rcParams.update({
    'figure.facecolor': '#eceff4',
    'axes.facecolor': '#d8dee9',
    'axes.edgecolor': '#eceff4',
    'grid.color': '#d9e2ec',
    'xtick.color': '#627d98',
    'ytick.color': '#627d98',
    'text.color': '#455669',
})

def plot(df: pd.DataFrame, axs: matplotlib.axes.Axes | np.ndarray, drug: str,
         strains: list | np.ndarray, timepoints: list | np.ndarray, row_indices=None, subplot: int = 0, save_type=None,
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

    # Set1 has a max of 9 colors
    colors = plt.cm.Set1.colors
    strain_palette = dict(zip(sorted(strains),colors[:len(strains)]))
    timepoint_palette = dict(zip(sorted(timepoints),colors[:len(timepoints)]))

    f = Fit()
    seen_strains = seen_timepoints = set()
    rep_locs = list()

    if isinstance(axs, np.ndarray):  # checks for existence of subplot else it's a specific axs obj
        axs = axs.flatten()[subplot]

    # Row indices for all (three) replicates matching the specified strain(s), drug, and timepoint(s) criteria
    if row_indices is None:
        row_indices = df[(df['Drug'] == drug) & (df['Strain'].isin(strains)) & (df['Timepoint'].isin(timepoints))].index

    for i, row_idx in enumerate(row_indices): # for each replicate, for each strain, for each timepoint
        row = df.loc[row_idx]
        strain = row['Strain']
        timepoint = row['Timepoint']
        algo = row['Best Algo']

        ## Adjusting color and legend depending on len() of strains and timepoints
        # Single strain and timepoint (assumes max of 3 replicates)
        if len(strains) == 1 and len(timepoints) == 1:
            color = ['red','blue','green'][i]
            rep_locs.append(row_idx if algo else algo) # only returns non-empty list for single strain and timepoint
            legend_label = f'R{i+1}'

        # Multiple strains and single timepoint
        elif len(strains) > 1 and len(timepoints) == 1:
            color = strain_palette[strain]
            legend_label = strain if strain not in seen_strains else ""

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

        # x,y for scatter plot
        x = row['Volume']
        y = row['Growth Inhibitions'] if not gr else row['gr']['norm_gr']

        # Allows/ensures indexing of axs obj
        # if isinstance(axs, np.ndarray): # checks for existence of subplot
        #     if axs.ndim == 2: # if more than one row to display plots
        #         axs = axs.flatten()[subplot]
        #     else:
        #         axs = axs[subplot]

        # Conditionals for whether a curve fit exists for dose response or growth rate
        if gr and (grinf := row['gr']['Einf']):
            ec50 = row['gr']['EC50']
            hill_slope = row['gr']['Hill Slope']
            r2 = np.round(row['gr']['R_squared'],3)

            y_pred = f.GR_Hill(x, grinf, ec50, hill_slope)
            axs.set_ylim(-1,1)
            axs.plot(np.log10(x), y_pred, color=color, ls='--', label=r2 if len(row_indices) == 1 else legend_label,
                     alpha=0.5)  # curve fit only if algo

        else:
            if algo:
                einf = row[algo]['Einf']
                ec50 = row[algo]['EC50']
                hill_slope = row[algo]['Hill Slope']
                r2 = np.round(row[algo]['R_squared'],3)

                y_pred = f.Hill(np.array(x), einf, ec50, hill_slope)
                axs.set_ylim(0, 1)
                axs.plot(np.log10(x), y_pred, color=color, ls='--', label=r2 if len(row_indices) == 1 else legend_label,
                         alpha=0.5) # curve fit only if algo

        axs.scatter(np.log10(x), y, marker='o', color=color, antialiased=False, alpha=0.6)
        axs.grid(color='white', linestyle='-.', linewidth=0.9, alpha=0.9)

        # When plots are separated by strain, timepoint, and replicate
        if len(strains) == 1 and len(timepoints) == 1 and len(row_indices) == 1:
            axs.plot(np.log10(x), y, color='black', antialiased=False, alpha=0.35)

    if save_type == 'pdf':
        axs.set_title(f"{drug}")
        if len(strains) == 1 and len(timepoints) == 1 and len(row_indices) == 1:
            axs.set_title(f"{drug} \u2022 {strain} \u2022 {timepoint}")
    else:
        axs.set_title(f"{drug} {'Dose response' if not gr else 'Growth rate'} curves for {', '.join(strains)}")

    axs.set(xlabel='Volume (log10) (nL)', ylabel=f'{'Growth inhibitions' if not gr else 'Normalized growth rate'}')
    axs.legend(frameon=False)

    return rep_locs

def generate_plot_images(df, drugs, strains, timepoints, save_path, save_type=None, gr=False, partition=False):
    """"Generates individual dose response plot as png or as a batch of 3 plots per page in a pdf file

        Keyword arguments:
        :param df: pd.DataFrame of MK DiaMOND pipeline
        :param drugs: np.ndarray or list() of drugs for which a plot will be made
        :param strains: list() of strains to superimpose on each plot
        :param save_path: file path to save png images (pathlib obj)
    """
    save_path = Path(save_path)
    row_indices = df.sort_values(['Strain', 'Timepoint',
                                  'Drug']).index  # where each index is a row (and individual plot) for all data to be plotted

    if save_type == 'pdf':
        batch_size = 3

        if partition:
            batches = [row_indices[i:i + batch_size] for i in range(0, len(row_indices), batch_size)]
        else:
            batches = [drugs[i:i + batch_size] for i in range(0, len(drugs), batch_size)]

        with PdfPages(unique_filename(save_path / 'hillcurves.pdf')) as pdf:
            for b in batches:  # each batch is a page on the pdf
                fig, axs = plt.subplots(nrows=1, ncols=3, facecolor='white', figsize=(15, 4))
                axs = axs.flatten() if isinstance(axs, np.ndarray) else axs
                plt.suptitle(f'Dose Response Curves for {", ".join(strains)}')

                for i_element, element in enumerate(b): # an element is either a drug:str or a pandas.Index for a the .loc of a row
                    if partition:
                        row = df.loc[element]
                        d = row['Drug']
                        s= row['Strain']
                        t = row['Timepoint']

                        plot(df, axs, drug=d, strains=[s], timepoints=[t],
                                        row_indices=[element],
                                        subplot=i_element, save_type='pdf', gr=gr)

                    else:
                        plot(df, axs, strains=strains, drug=element,
                                        timepoints=timepoints,
                                        subplot=i_element, save_type='pdf', gr=gr)

                    axs[i_element].set_facecolor('#EAEAF2')

                pdf.savefig(fig)
                plt.close(fig)

    elif save_type == 'png':
        iterable = row_indices if partition else drugs

        for i_element, element in enumerate(iterable):
            fig, axs = plt.subplots(1, 1, facecolor='white')

            if partition:
                row = df.loc[element]
                d = row['Drug']
                s = row['Strain']
                t = row['Timepoint']

                plot(df, axs, drug=d, strains=[s], timepoints=[t], row_indices=[element],
                     subplot=0, save_type='pdf', gr=gr)

            else:
                plot(df, axs, drug=element, strains=strains, timepoints=timepoints, row_indices=None,
                     subplot=0, gr=gr)

            axs.set_facecolor('#EAEAF2')
            fig.savefig(unique_filename(save_path / f"{", ".join(strains)}_{d if partition else element}.png"))
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


if __name__ == "__main__":
    hp_path = '/Users/hidetominitta/Downloads/2025-05-09_result.pkl'
    hp_path = '/Users/hidetominitta/Desktop/DiaMOND/Experiments/BDQ-R/Aux_Validation/results/results_05052025.pkl'
    df = pd.read_pickle(hp_path)
    drugs = df['Drug'].unique()
    strains = df['Strain'].unique()
    timepoints = df['Timepoint'].unique()


    fig, axs = plt.subplots(4,6)
    print(len(timepoints))

    idx = 0
    for strain in strains[:2]:
        for drug in drugs[-2:]:
            for timepoint in timepoints[:2]:
                row_indices = df[(df['Drug'] == drug) & (df['Strain'] == strain) & (df['Timepoint'] == timepoint)].index
                for row_index in row_indices:
                    plot(df, axs, drug,strains=[strain],timepoints=[timepoint], row_indices=[row_index], subplot=idx, save_type='pdf',
                         gr = True)
                    idx+=1

    plt.show()


    print('helper.py was run')





