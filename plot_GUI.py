# main.py
# Name: Hidetomi Nitta
# Purpose: Visualize plots for DiaMOND experiments using MK DiaMOND pipeline

# PlotGUI
# TODO: combos with certain drugs (e.g. all BDQ drugs)
# TODO: getting rid if vestigials after hitting "run"
# TODO: blitting for 12 subplots
# TODO: recursive self.after() calls for plot() function

# GUI hub
# TODO: Make central GUI portal (dropdown) in order to select between multiple different DiaMOND tools.

# DiaMOND
# TODO: simple GUI to run initial DiaMOND on data

import matplotlib
matplotlib.use('TkAgg')
import customtkinter as ctk
from customtkinter import filedialog
from pathlib import Path
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import gc, os, subprocess
from helper import plot, generate_plot_images
from custom_widgets import PlotFrame, ParameterCheckbox, MSToplevel, LabelToplevel, SlidingButton, SlidingFrame

ctk.set_appearance_mode('light')
ctk.set_default_color_theme('green')

# Matplotlib global appearance
plt.rcParams.update({
    'figure.facecolor': '#eceff4',
    'axes.facecolor': '#d8dee9',
    'axes.edgecolor': '#eceff4',
    'grid.color': '#d9e2ec',
    'xtick.color': '#627d98',
    'ytick.color': '#627d98',
    'text.color': '#455669',
})

# Customtkinter global appearance
root_color = '#eceff4'
frame_color = '#d8dee9'
widget_color = '#eceff4'


class PlotGUI(ctk.CTk):
    def __init__(self):
        super().__init__(fg_color=root_color)
        # Base frame
        usable_height = self.winfo_screenheight() - 135 # account for taskbar
        self.geometry(f"{int(usable_height*1.14)}x{usable_height}") # geometry expects an int, not float
        # self.geometry('975x855')
        self.title('Plot data')
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        ## plot frame
        self.setup_default_state()
        ## parameter frame
        self.setup_parameter_frame()
        self.bind('<space>', lambda event: self.slide_parameter_frame())
        ### action frame
        self.setup_action_frame()

        # self.resizable can limit geometry size if called before widgets are placed.
        self.update_idletasks()
        self.resizable(False, False)

    def setup_default_state(self):
        """GUI state that is initialized upon start of the GUI and when the plots are cleared.

        Frame info:
        master = self, row = 0
        """

        self.destroy_display_frames()

        # Clearing 1-way, 2-way checkboxes
        if hasattr(self, 'checkboxes'):
            self.checkboxes['all_singles'].set(False)
            self.checkboxes['all_combos'].set(False)

            # Clearing any other selections by accessing tuple in (idx, ParameterCheckbox) form
            for key, parameter in self.checkboxes.items():
                if key in ['drugs', 'strains', 'timepoints']:
                    for checkbox_info in parameter:
                        checkbox = checkbox_info[1]
                        if checkbox.get():
                            checkbox.set(False)

        if hasattr(self, 'temp_frame'):
            self.temp_frame.tkraise()
            self.subplot_count_sbutton.tkraise()
            self.partition_plot_switch.tkraise()
            self.pf_button.tkraise()

            if self.slide_visible:
                self.parameter_frame.tkraise()

            self.progress_bar.set(0)

        else: # initial launch of GUI
            # Frame to display blank plot
            self.temp_frame = ctk.CTkFrame(master=self)
            self.temp_frame.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')
            self.temp_frame.grid_rowconfigure(0, weight=1)
            self.temp_frame.grid_columnconfigure(0, weight=1)

            # Layout buttons (to see either 4, 6, or 12 plots per frame)
            values = [4, 9, 16]
            self.subplot_count_sbutton = ctk.CTkSegmentedButton(master=self, values=values)
            self.subplot_count_sbutton.set(4)
            self.subplot_count_sbutton.place(relx=1.0, y=5, anchor='ne', x=-10)

            # Toggle between superimposition or partitioning of plots
            self.partition_plot_var = ctk.BooleanVar()
            self.partition_plot_switch = ctk.CTkSwitch(master=self, text='Partition', variable=self.partition_plot_var)
            self.partition_plot_switch.place(relx=0, y=5, anchor='nw', x=10)

            # Accessory plot
            fig, axs = plt.subplots(1, 1)

            canvas = FigureCanvasTkAgg(fig, self.temp_frame)
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.grid(row=0, column=0, sticky='nsew')

            canvas.draw()
            plt.close(fig)

            # Initializing progress bar for when rendering large dataframe selections
            self.progress_bar = ctk.CTkProgressBar(master=self.temp_frame, orientation='horizontal', width=450,
                                                   height=22,
                                                   corner_radius=20, border_width=2, border_color='#d8dee9',
                                                   fg_color='#eceff4',
                                                   bg_color='#d8dee9', mode='determinate', determinate_speed=5,
                                                   indeterminate_speed=0.5)

            self.progress_bar.place(x=260, y=525)
            self.progress_bar.set(0)

        return

    def setup_parameter_frame(self):
        """Frame that holds scrollable frames to allow user to select from drugs, strains, or timepoints
        as well as the initial file selection and generate plot button.

        Frame info:
        master = self, row = 1
        """

        self.after(10)
        self.width = self.winfo_width()
        self.height = self.winfo_height()
        self.slide_visible = False

        self.pf_button = SlidingButton(master=self, x=self.width // 2, y=self.height - 5, width=250, height=10,
                                       command=self.slide_parameter_frame)
        # self.parameter_frame = ctk.CTkFrame(master=self, height=175,fg_color=frame_color, corner_radius=15)
        self.parameter_frame = SlidingFrame(master=self, x=self.width // 2, y=self.height, fg_color=frame_color,
                                            border_color='gray70', border_width=1, width=self.width - 10, height=175,
                                            corner_radius=15)
        self.parameter_frame.grid_rowconfigure(0, weight=1)
        self.parameter_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        self.parameter_frame.grid_propagate(False)

        # drug scrollable
        self.drugs_scrollable = ctk.CTkScrollableFrame(master=self.parameter_frame, height=160, fg_color=widget_color,
                                                       corner_radius=15)
        self.drugs_scrollable.grid(row=0, column=0, padx=7, pady=7, sticky='e')

        # strain scrollable
        self.strains_scrollable = ctk.CTkScrollableFrame(master=self.parameter_frame, height=160, fg_color=widget_color,
                                                         corner_radius=15)
        self.strains_scrollable.grid(row=0, column=1, padx=7, pady=7)

        # timepoint scrollable
        self.timepoints_scrollable = ctk.CTkScrollableFrame(master=self.parameter_frame, height=160,
                                                            fg_color=widget_color, corner_radius=15)
        self.timepoints_scrollable.grid(row=0, column=2, padx=7, pady=7, sticky='w')

        return

    def setup_action_frame(self):
        """Frame that holds widgets that either execute or help in the execution of a command

        Frame info:
        master = self.parameter_frame
        """

        # action frame
        self.action_frame = ctk.CTkFrame(master=self.parameter_frame, fg_color=widget_color)
        self.action_frame.grid(row=0, column=3, padx=5, pady=5, sticky='w')
        self.action_frame.grid_rowconfigure((0, 1), weight=1)
        self.action_frame.grid_columnconfigure(0, weight=1)

        # File button
        self.file_button = ctk.CTkButton(master=self.action_frame, text='Select file',
                                         command=lambda: self.load_file(),
                                         fg_color='gray', width=25,
                                         hover_color='gray20')
        self.file_button.grid(row=0, column=0, padx=10, pady=10, sticky='ew')

        # Generation frame (contains dropdown menu and create plot button)
        self.generation_frame = ctk.CTkFrame(master=self.action_frame, fg_color=widget_color)
        self.generation_frame.grid(row=1, column=0, padx=0, pady=2, sticky='w')
        self.generation_frame.grid_rowconfigure(0, weight=1)
        self.generation_frame.grid_columnconfigure((0, 1), weight=2)
        self.generation_frame.grid_columnconfigure(2, weight=0)

        # Options for creating specifying type of plot, etc.
        self.dropdown_var = ctk.StringVar(value="Dose response")

        dropdown_options = ['Dose response', 'Growth rate', 'Save to PDF', 'Save to PNGs', 'Manual selection']
        self.dropdowns = ctk.CTkOptionMenu(master=self.generation_frame,
                                           values=dropdown_options,
                                           variable=self.dropdown_var)
        self.dropdowns.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky='ew')

        # Create plot button
        self.create_plot_button = ctk.CTkButton(master=self.generation_frame, text='Run',
                                                width=20, command=self.execute_dropdown_action)
        self.create_plot_button.grid(row=0, column=2, padx=5, pady=5)

        return

    def update_progress(self, total_batches):
        """Updates progress bar as each frame is constructed"""

        step_size = (100 / total_batches) / 100
        current = self.progress_bar.get()

        if current < 1:
            current += step_size
            self.progress_bar.set(current)
            self.after(5)
            self.update_idletasks()

        return

    def slide_parameter_frame(self):
        """Responsible for sliding animation for self.pf_button and self.parameter_frame. Controls speed and heights of
        different states."""

        increment = 30
        up_state = self.height - 175
        down_state = self.height

        if self.slide_visible:
            self.pf_button.slide(ytarget=down_state - 5, increment=increment, direction='DOWN')
            self.parameter_frame.slide(ytarget=down_state, increment=increment, direction='DOWN')

            self.slide_visible = False

        else:
            self.pf_button.slide(ytarget=up_state - 5, increment=increment, direction='UP')
            self.parameter_frame.tkraise()
            self.parameter_frame.slide(ytarget=up_state, increment=increment, direction='UP')

            self.slide_visible = True

        return

    def load_file(self):
        """Requests pickle file which is then used in order to generate checkbox button(s)
        (using self.generate_checkbox_scrollables) within each scrollable frame (for drugs, strains, and timepoints)."""

        self.setup_default_state()
        initial_path = Path.home() / 'Downloads'
        self.file_path = filedialog.askopenfilename(title='Select file',
                                                    filetypes=[("Pickle files", "*.pkl")],
                                                    initialdir=f'{initial_path}')

        self.destroy_checkboxes()

        if self.slide_visible:  # should be True
            self.parameter_frame.tkraise()

        if self.file_path:
            self.file_button.configure(text='File selected', fg_color='gray26')

            self.df = pd.read_pickle(self.file_path)
            self.df_drugs = self.df['Drug'].unique()
            self.df_singles = [d for d in self.df_drugs if '+' not in d]
            self.df_combos = [d for d in self.df_drugs if '+' in d]
            self.df_strains = self.df['Strain'].unique()
            self.df_timepoints = self.df['Timepoint'].unique()

            self.generate_checkbox_scrollables()

        else:
            pass

        return

    def generate_checkbox_scrollables(self):
        """Initializes parameters, as checkboxes, inside the scrollable frames for drugs, strains, and timepoints
         in order to allow the user to display and filter specific data. The current state of these checkboxes is
         stored as boolean variables within the self.checkboxes dict().

        Format of self.checkboxes.items():
        key, (index, ParameterCheckbox)
        """

        frames = [self.drugs_scrollable, self.strains_scrollable, self.timepoints_scrollable]
        self.checkboxes = dict()
        self.idx1_map = {0: 'drugs', 1: 'strains', 2: 'timepoints'}

        self.checkboxes['all_singles'] = ParameterCheckbox(master=frames[0], row=0, text='1-way')
        self.checkboxes['all_combos'] = ParameterCheckbox(master=frames[0], row=1, text='2-way')

        # Checkboxes for all drugs (singles and combinations), strains, and timepoints
        for idx1, parameter in enumerate([self.df_drugs, self.df_strains, self.df_timepoints]):
            key = self.idx1_map[idx1]
            offset = 2 if idx1 == 0 else 0

            self.checkboxes.update({key: []})

            for idx2, p in enumerate(parameter, start=offset):
                checkbox = ParameterCheckbox(master=frames[idx1], row=idx2, text=str(p))

                self.checkboxes[key].append(((idx2 - offset), checkbox))

        return

    def get_user_inputs(self):
        """Retrieves selected user inputs for drugs, strains, and timepoints and uses them to filter data.
        These selections are boolean variables contained within the self.checkboxes dict(). Initiates/updates class
        attributes self.f_drugs, self.f_strains, and self.f_timepoints.
        """

        self.f_drugs = self.f_strains = self.f_timepoints = None

        if hasattr(self, 'checkboxes'):
            singles_clicked = self.checkboxes['all_singles'].get()
            combos_clicked = self.checkboxes['all_combos'].get()
            filter_list = lambda a, b: list(np.array(a)[b])  # returns list of a which satisfies b

            # If both, 1-way, or 2-way selected
            if singles_clicked and combos_clicked:
                f_drugs = list(self.df_drugs)
            elif singles_clicked:
                f_drugs = self.df_singles
            elif combos_clicked:
                f_drugs = self.df_combos

            # Individual drug selections
            else:
                drug_indices = [x[0] for x in self.checkboxes['drugs'] if x[1].get() is True]
                f_drugs = filter_list(self.df_drugs, drug_indices)

            strain_indices = [y[0] for y in self.checkboxes['strains'] if y[1].get() is True]
            timepoint_indices = [z[0] for z in self.checkboxes['timepoints'] if z[1].get() is True]

            f_strains = filter_list(self.df_strains, strain_indices)
            f_timepoints = filter_list(self.df_timepoints, timepoint_indices)

            if all([f_drugs, f_strains, f_timepoints]):
                self.f_drugs = f_drugs
                self.f_strains = f_strains
                self.f_timepoints = f_timepoints

        return

    def execute_dropdown_action(self):
        """Executes plotting methods, saves selection to PDF, or manual selection using self.dropdown_var. Also
        specifies to the user of certain, illegitimate selection of parameters."""

        command = self.dropdown_var.get()
        self.get_user_inputs()

        if all([self.f_drugs, self.f_strains, self.f_timepoints]):
            match command:
                case 'Dose response' | 'Growth rate':
                    self.destroy_display_frames()
                    self.get_user_inputs()

                    # Initialize or re-bind controls (disconnected for proper destruction)
                    self.bind('<Left>', lambda event: self.next_frame('L'))
                    self.bind('<Right>', lambda event: self.next_frame('R'))
                    self.bind('<Down>', lambda event: self.setup_default_state())

                    self.initialize_display_frames()

                case 'Save to PDF' | 'Save to PNGs':
                    self.save_selections()

                case 'Manual select.':
                    self.get_user_inputs()

                    if any(True if '+' in d else False for d in self.f_drugs):
                        LabelToplevel(master=self, title='Error',
                                      text='Please select 1-way combinations\n for manual selection')
                    elif len(self.f_strains) > 1 or len(self.f_timepoints) > 1:
                        LabelToplevel(master=self, title='Error',
                                      text='Please only use a singular timepoint\n and strain for manual selection')
                    else:
                        self.manual_selection()
                        print('Manual selection was executed')
        else:
            LabelToplevel(master=self, title='Error',
                          text='Please select at least\n one of each parameter')

    def initialize_display_frames(self):
        """Uses custom plot function (from helper.py) where each plot for a drug is batched into 4 per frame or 12
         per frame if QuickView switch is selected. User inputs for drugs, strains, and timepoints are used in order to
         filter data that is displayed on the canvas. Method that is called after self.get_user_inputs()."""

        # Reset and initialize objects/variables
        self.progress_bar.set(0)
        self.progress_bar.update_idletasks()
        self.current_frame_idx = 0
        self.display_frames = dict()

        # One drug, one plot
        if len(self.f_drugs) == 1:
            nrows = ncols = 1
            batch_size = 1

        num_plots = self.subplot_count_sbutton.get()

        # Plot shaped based on user specifications (segmented button)
        match num_plots:
            case 4:
                batch_size = 4
                nrows = ncols = 2
            case 9:
                batch_size = 9
                nrows, ncols = 3, 3
            case 16:
                batch_size = 16
                nrows, ncols = 4, 4

        # Each subplot is a unique drug. Strains, timepoints, and replicates are all superimposed.
        self.construct_frames(batch_size, num_plots, nrows, ncols)

        initial_display = self.display_frames[self.current_frame_idx]
        initial_display.toggle_event_listeners(state=True)
        initial_display.tkraise()
        self.subplot_count_sbutton.tkraise()
        self.partition_plot_switch.tkraise()
        self.pf_button.tkraise()

        if self.slide_visible:
            self.parameter_frame.tkraise()

        self.after(50)

        return

    def construct_frames(self, batch_size, num_plots, nrows, ncols):
        """Superimposed (default) or partitioned plots are batched to frames."""

        # Improve indexing efficiency by subsetting self.df (even though plot() method handles this)
        df = self.df[self.df['Timepoint'].isin(self.f_timepoints) & (self.df['Strain'].isin(self.f_strains)) &
                     (self.df['Drug'].isin(self.f_drugs))]
        gr = True if self.dropdown_var.get() == 'Growth rate' else False
        partition = self.partition_plot_switch.get()

        if partition:
            row_indices = df.sort_values(['Strain','Timepoint','Drug']).index  # where each index is a row (and individual plot) for all data to be plotted
            batches = [row_indices[i:i + batch_size] for i in range(0, len(row_indices), batch_size)]
        else:
            batches = [self.f_drugs[i:i + batch_size] for i in range(0, len(self.f_drugs), batch_size)]

        # Construction of self.display_frames according to user specifications
        for i_frame, batch in enumerate(batches):  # each batch is a subplot and a frame
            fig, axs = plt.subplots(nrows=nrows, ncols=ncols, dpi=95)

            subplot_rep_locs = {}
            main_text = r"$\bf{Growth\ rate\ inhibitions}$" if gr else r"$\bf{Dose\ response}$"

            plt.suptitle(
                f'{main_text}\n{" \u2022 ".join(self.f_strains) if self.f_strains != ["EL"] else "Erdman-Lux"}'
                f', {" \u2022 ".join(self.f_timepoints)}',
                fontname='Arial', fontsize=14, fontstyle='oblique')

            if isinstance(axs, np.ndarray):  # checks for existence of subplot
                flattened_axs = axs.flatten()
            else:
                flattened_axs = axs
            flattened_axs = axs.flatten() if isinstance(axs, np.ndarray) else axs

            for i_element, element in enumerate(batch): # an element is either a drug:str or a pandas.Index for a the .loc of a row
                subplot_axs = flattened_axs[i_element]

                # Plot and retrieve integer-label (.loc) of replicates
                if partition:
                    row = df.loc[element]
                    drug = row['Drug']
                    strain = row['Strain']
                    timepoint = row['Timepoint']

                    rep_locs = plot(df, subplot_axs, drug, strains=[strain], timepoints=[timepoint], row_indices=[element],
                                    subplot=i_element, save_type='pdf', gr=gr)

                else:
                    rep_locs = plot(df, subplot_axs, strains=self.f_strains, drug=element, timepoints=self.f_timepoints,
                                    subplot=i_element, save_type='pdf', gr=gr)

                # Subplot specifications depending on plots per frame
                self.plot_specifications(subplot_axs, num_plots)

                # Store in a dictionary that maps it to the respective axs obj
                subplot_rep_locs.update({subplot_axs: rep_locs})

            self.update_progress(len(batches))

            plt.subplots_adjust(hspace=0.4, wspace=0.3)
            frame = PlotFrame(master=self, fig=fig, subplot_rep_locs=subplot_rep_locs)

            if (has_combo := any('+' in d for d in self.f_drugs)):  # manual selection is only used for singles
                frame.ms_condition = False

            plt.close(fig)
            self.display_frames.update({i_frame: frame})

        return

    def plot_specifications(self, axs, num_plots):
        match num_plots:
            case 4:
                axs.title.set_fontsize(14)
                axs.xaxis.label.set_fontsize(9)
                axs.yaxis.label.set_fontsize(9)
            case 9:
                axs.title.set_fontsize(11)
                axs.xaxis.label.set_fontsize(8)
                axs.yaxis.label.set_fontsize(8)

                for label in (axs.get_xticklabels() + axs.get_yticklabels()):
                    label.set_fontsize(8)
            case 16:
                axs.title.set_fontsize(9)
                axs.xaxis.label.set_visible(False)
                axs.yaxis.label.set_visible(False)
                axs.legend(frameon=False, fontsize=10)

                for label in (axs.get_xticklabels() + axs.get_yticklabels()):
                    label.set_fontsize(6)

        return

    def save_selections(self):
        """Currently selected checkboxes are used in order to generate a PDF in which each page is a 1x3 subplot
        """
        save_path = Path.home() / 'Downloads'
        df = self.df[(self.df['Drug'].isin(self.f_drugs)) & (self.df['Strain'].isin(self.f_strains))
                     & (self.df['Timepoint'].isin(self.f_timepoints))]
        partition = self.partition_plot_switch.get()
        save_map = {'Save to PDF': 'pdf', 'Save to PNGs': 'png'}

        generate_plot_images(df, drugs=self.f_drugs, strains=self.f_strains, timepoints=self.f_timepoints,
                             save_path=save_path, save_type=save_map[self.dropdown_var.get()],
                             partition=True if partition else False)

        LabelToplevel(master=self, title='Success', text='Selected plots saved in Downloads')
        self.after(50)

        return

    def manual_selection(self):
        """Method that contains Manual Selection logic e.g. if 2/3 reps selected for a single -> remove all associated combos.
        Uses selected replicates and then creates an MS_Flag column."""

        # if 2/3 reps selected for a single -> remove all associated combos
        all_reps_to_remove = set()
        row_integer_labels, drugs = set(), set()

        for frame in self.display_frames.values():
            if hasattr(frame, 'reps_to_remove'):
                all_reps_to_remove = all_reps_to_remove | frame.reps_to_remove  # union of sets

        if all_reps_to_remove:
            for arg in all_reps_to_remove:
                (row_integer_labels if type(arg) == int else drugs).add(arg)

            # Single strain, single timepoint for MS
            condition1 = self.df['Strain'].isin(self.f_strains)
            condition2 = self.df['Timepoint'].isin(self.f_timepoints)

            # Handles filtering replicates or all combinations containing a certain drug
            empty = pd.Series(False, index=self.df.index)
            condition3 = self.df.index.isin(row_integer_labels) if row_integer_labels else empty # replicates
            condition4 = self.df['Drug'].str.contains('|'.join(drugs)) if drugs else empty # single and combos containing drug(s)

            self.df['MS_Flag'] = np.nan
            mask = (condition1 & condition2) & condition3 | condition4  # condition3 or condition4 for single strain and timepoint
            self.df.loc[mask, 'MS_Flag'] = int(1)
            self.df.to_pickle(self.file_path)

            LabelToplevel(master=self, title='Success', text='Manual selection was done\n on the selected replicates')
            print(all_reps_to_remove)
            print(self.df['MS_Flag'].value_counts()[1])

        else:
            LabelToplevel(master=self, title='Error', text='Please select replicate(s)\n for removal')

        return

    def next_frame(self, direction: str = 'R'):
        """After self.generate_plot(), lifts leftward or rightward frame in self.display_frames while handling
         event_listeners.
        """

        dir_var = 1 if direction == 'R' else -1

        if hasattr(self, 'display_frames'):
            # Prepare for background
            current_frame = self.display_frames[self.current_frame_idx]
            current_frame.toggle_event_listeners(state=False)

            # Adjust variables and bring new frame into foreground
            self.current_frame_idx = (self.current_frame_idx + dir_var) % len(
                self.display_frames)  # update to next frame
            next_frame = self.display_frames[self.current_frame_idx]
            next_frame.toggle_event_listeners(state=True)

            next_frame.tkraise()
            self.subplot_count_sbutton.tkraise()
            self.partition_plot_switch.tkraise()
            self.pf_button.tkraise()

            if self.slide_visible:
                self.parameter_frame.tkraise()

        return

    def destroy_display_frames(self):
        """Full destroy of PlotFrame objects (and any references) within self.display_frames dict() as well as
        MSTopLevel which is mastered by PlotFrame."""

        # Help release PlotFrame objects by unbinding events
        self.unbind('<Left>')
        self.unbind('<Right>')
        self.unbind('<Down>')

        if hasattr(self, 'display_frames'):
            for frame in self.display_frames.values():
                frame.destroy()
            self.display_frames.clear()
            gc.collect()  # Force garbage collection on lingering objects

        return

    def destroy_checkboxes(self):
        """Destroys checkboxes and gets rid of any references."""

        if hasattr(self, 'checkboxes'):  # destroy checkboxes
            for val in self.checkboxes.values():
                if isinstance(val, list):
                    for tupl in val:
                        cb = tupl[1]
                        cb.destroy()

                        for attr in list(cb.__dict__.keys()):
                            setattr(cb, attr, None)

            self.checkboxes.clear()

        return


if __name__ == '__main__':
    print('plot_GUI.py was run')
    app = PlotGUI()
    app.mainloop()

