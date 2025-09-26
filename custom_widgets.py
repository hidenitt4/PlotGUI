# custom_widgets.py
# Name: Hidetomi Nitta
# Purpose: Custom widgets for use in PlotGUI class

import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mplcursors import cursor

# make sure to destroy textbox once created...

class PlotFrame(ctk.CTkFrame):
    """Frame that contains the id/location for the respective data that is displayed on subplots (or a plot in the case
    of a single drug selection). Also serves as master for MSToplevel object through which receives replicates selected
    for removal (manual selection)."""

    def __init__(self, master, fig, subplot_rep_locs):
        super().__init__(master, height=650)
        self.fig = fig
        self.num_axes = len(self.fig.get_axes())

        self.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.lower() # control visibility

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky='nsew')

        # Event-related connections
        self.mst_cid = None
        self.cur_enter_cid = None
        self.cur_leave_cid = None
        self.active_cursor = None

        # Manual selection variables
        self.subplot_rep_locs = subplot_rep_locs
        self.mapped_selections = dict()
        self.mst = list() # store MSToplevel
        self.ms_condition = any(self.subplot_rep_locs.values()) # whether to allow MS on a frame

        self.canvas.draw()
        plt.close(self.fig)

    def __del__(self):
        print (f'PlotFrame was deleted')

    def toggle_event_listeners(self, state: bool):
        """Allows for the toggling of mplcursors obj/connections and connection responsible for manual selection feature.
         Also removes any lingering references for prophylactic garbage collection."""

        if state:
            if not all([self.mst_cid, self.cur_enter_cid, self.cur_leave_cid]):
                if self.ms_condition:
                    self.mst_cid = self.fig.canvas.mpl_connect('button_press_event', self.on_click)
                else:
                    self.mst_cid = True

                self.cur_enter_cid = self.fig.canvas.mpl_connect('axes_enter_event',
                                                                 lambda event: self.toggle_cursor(event, state=True))
                self.cur_leave_cid = self.fig.canvas.mpl_connect('axes_leave_event',
                                                                 lambda event: self.toggle_cursor(event, state=False))

        else:
            if self.mst_cid and self.cur_enter_cid and self.cur_leave_cid:
                if self.ms_condition:
                    self.fig.canvas.mpl_disconnect(self.mst_cid)

                self.mst_cid = None

                if self.active_cursor:
                    self.active_cursor.remove()
                    self.active_cursor = None

                self.fig.canvas.mpl_disconnect(self.cur_enter_cid)
                self.fig.canvas.mpl_disconnect(self.cur_leave_cid)
                self.cur_enter_cid = None
                self.cur_leave_cid = None

        return

    def toggle_cursor(self, event, state:bool):
        """Handles cursor creation/destruction logic using axes_enter_event (state=True) and axes_leave_event
         (state=False), respectively. Artists that cursor uses is dependent on the number of plots visible per frame
         for smoother performance (line2D at the very least). """

        event_axs = event.inaxes

        if state: # for entering axs obj
            if event_axs:
                if self.active_cursor: # vestigial cursor
                    self.active_cursor.remove()
                    self.active_cursor = None

                if not self.active_cursor:
                    # Dynamic cursor artists dependent on number of subplots per frame for best performance
                    artists = (list(event_axs.lines) if self.num_axes <=9 else list()) + (list(event_axs.collections)
                                                                              if self.num_axes <=4 else list())
                    if artists:
                        c = cursor(artists, hover=None)
                        self.active_cursor = c

                        @c.connect("add") # Adjust mplcursors annotation style
                        def on_add(sel):
                            sel.annotation.set_text(f"{sel.target[0]:.2f}, {sel.target[1]:.2f}")
                            sel.annotation.get_bbox_patch().set(fc="white", alpha=0.8, edgecolor="none")

        else: # for leaving axs obj
            if event_axs: # refers to axs obj that is being left
                if self.active_cursor:
                    self.active_cursor.remove()
                    self.active_cursor = None

        return

    def on_click(self, event):
        """Method that is bound to the double-click event and opens MSToplevel widget for that specific subplot."""

        event_axs = event.inaxes

        if event_axs and event.dblclick:
            title = event_axs.get_title()
            rep_locs = self.subplot_rep_locs[event_axs]

            if event_axs in self.mapped_selections.keys(): # if subplot has been clicked on before
                prior_selections = self.mapped_selections[event_axs]
            elif not all(rep_locs):
                prior_selections = tuple(False if loc else True for loc in rep_locs)  # Algo is None (no curve fit for rep)
            else:
                prior_selections = None

            if not any(isinstance(child, ctk.CTkToplevel) for child in self.winfo_children()):
                mst = MSToplevel(master=self, title=title, canvas=self.canvas, event=event, rep_locs=rep_locs,
                           on_close_callback=self.receive_on_close, prior_selections=prior_selections)
                self.mst.append(mst)

            self.canvas.draw_idle()

        return

    def receive_on_close(self, fromToplevel):
        """Method to receive replicates that were selected for removal from MSToplevel widget."""

        axs, selections = fromToplevel
        self.mapped_selections.update({axs: selections})
        self.filter_replicates_for_removal()

        return

    def filter_replicates_for_removal(self):
        """Contains a set of the integer label (using .loc) of selected replicates or string of single in which >1
        replicate(s) was selected for removal."""

        self.reps_to_remove = set()

        for axs, selections in self.mapped_selections.items():
            rep_locs = self.subplot_rep_locs[axs]
            title = axs.get_title()

            if selections.count(True) >= 2:
                self.reps_to_remove.add(title)

            else:
                for r, s in zip(rep_locs, selections):
                    if s and r != None:
                        self.reps_to_remove.add(r)

        print(f'Reps for removal: {self.reps_to_remove}')

        return

    def destroy(self):
        """Makes sure to do a deep-destroy, including any references or objects that might be preventing garbage
        collection from occurring."""

        # Hover feature
        if self.active_cursor:
            self.active_cursor.remove()
            self.active_cursor = None

            # Double-click event
        if self.mst_cid:
            self.fig.canvas.mpl_disconnect(self.mst_cid)
            self.mst_cid = None

        # Canvas for subplots or plot
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None

        # Matplotlib
        if self.fig:
            plt.close(self.fig)
            self.fig = None

        # MSToplevel
        if self.mst:
            if len(self.mst) > 1:
                # raise RuntimeError('MSToplevel reference still exists and was not properly destroyed')
                for mst in self.mst:
                    mst.destroy()
                    self.mst.clear()

            else:
                mst = self.mst[0]
                mst.destroy()
                self.mst.clear()

        # References holding axs references
        self.subplot_rep_locs.clear()
        self.mapped_selections.clear()

        super().destroy()

        return


class ParameterCheckbox(ctk.CTkCheckBox):
    """Checkbox object that is generated in drugs, strains, and timepoint scrollable frames OR MSToplevel.
    Stored in self.checkboxes."""

    def __init__(self, master, row, text, **kwargs):
        self.var = ctk.BooleanVar()
        super().__init__(master, text=text, variable=self.var, text_color='#455669',**kwargs)
        self.grid(row=row, column=0, padx=5, pady=5, sticky='w')

    def get(self):
        return self.var.get()

    def set(self, value: bool):
        self.var.set(value)
        return


class MSToplevel(ctk.CTkToplevel):
    """Toplevel window that appears upon double-clicking a subplot on the current frame. Allows selection of replicates
    in order to ultimately filter data for removal (manual selection)."""

    def __init__(self, master, title, canvas, event, rep_locs, on_close_callback, prior_selections):
        super().__init__(master)
        self.title(title)
        self.canvas = canvas
        self.event = event
        self.axs = event.inaxes
        self.rep_locs = rep_locs
        self.on_close_callback = on_close_callback
        self.prior_selections = prior_selections
        self.checkboxes = list()

        self.geometry(f"+{self.event.guiEvent.x_root}+{self.event.guiEvent.y_root}")
        self.bind('<FocusOut>', self.destroy)

        self.dynamic_setup()

    def dynamic_setup(self):
        """Depending on the number of replicates per drug, creates a Toplevel widget with checkboxes."""

        self.checkboxes = list()
        num_of_reps = len(self.rep_locs)

        for i in range(num_of_reps+1):
            if i == num_of_reps:
                self.close_button = ctk.CTkButton(master=self, text='Select for removal', width=20, command=lambda: self.destroy())
                self.close_button.grid(row=i, column=0, padx=5, pady=5)

            elif num_of_reps <=3:
                color = ['red', 'blue', 'green'][i]
                checkbox = ParameterCheckbox(master=self, row=i, text=f'R{i+1}', fg_color=color)
                checkbox.grid(sticky='e')

                if self.prior_selections:
                    checkbox.set(self.prior_selections[i])

                    if self.rep_locs[i] is None:
                        checkbox.configure(state=ctk.DISABLED)

                self.checkboxes.append(checkbox)

        if num_of_reps == 1:
            textbox = ctk.CTkEntry(master=self) # for entries
            textbox.grid(row=1, column=0, padx=5, pady=5)
            self.close_button.grid(row=2, column=0, padx=5, pady=5) # re-order close button to last row

            self.grid_rowconfigure((0,1,2), weight=1)
        else:
            self.grid_rowconfigure(tuple(x for x in range(num_of_reps+1)), weight=1)

        self.grid_columnconfigure(0, weight=1)

        return

    def get_selections(self):
        return tuple(checkbox.get() for checkbox in self.checkboxes)

    def destroy(self, event=None):
        """Destroys MSToplevel object, collects IntVars for use in manual selection feature (goes to PlotFrame), and
        changes canvas color to indicate any selection that was made. For the case of PlotFrame destruction,
         any references that might prevent garbage collection are also removed."""

        if self.winfo_exists(): # does the toplevel still exist
            self.unbind('<FocusOut>')

        # Tuple format where 0 indicates no selection and 1 indicates a selection.
        if self.axs:
            if any(self.get_selections()):
                self.axs.set_facecolor('#FFB3B3')
            else:
                self.axs.set_facecolor('#d8dee9')

            self.canvas.draw_idle()
            self.on_close_callback([self.axs, self.get_selections()])
            self.update()

        # References
        self.canvas = None
        self.event = None
        self.axs = None
        self.on_close_callback = None

        super().destroy()

        return

class PDFToplevel(ctk.CTkToplevel):
    """PDF specifications"""

    def __init__(self, master, title, callback, restrictions):
        super().__init__(master)
        master.update_idletasks()
        self.update_idletasks()
        center_x = (master.winfo_x() + master.winfo_width() // 2 - self.winfo_width() // 2)
        center_y = (master.winfo_y() + master.winfo_height() // 2 - self.winfo_height() // 2)

        self.geometry(f"+{center_x}+{center_y}")
        self.title(title)
        self.callback = callback
        self.can_superimpose = restrictions
        self.grid_rowconfigure(index=(0,1,2,3,4,5,6,7), weight=1)
        self.grid_columnconfigure(index=(0,1), weight=1)

        # Choose grouping of strain, drug, and timepoint
        self.grouping_label = ctk.CTkLabel(self, text=f'Grouping',font=("Arial", 14, "bold"))
        self.grouping_label.grid(row=0, column=0, columnspan=2, padx=5, pady=7, sticky='ew')

        grouping_options = ['Strain','Drug','Timepoint','None']

        self.grouping_1_var =  ctk.StringVar(value='None')
        self.grouping_1 = ctk.CTkOptionMenu(master=self,values=grouping_options,
                                            command=lambda event: self.check_grouping_selections(),
                                            variable=self.grouping_1_var)
        self.grouping_1.grid(row=1, column=0, columnspan=2, padx=5, pady=5)

        self.grouping_2_var = ctk.StringVar(value='None')
        self.grouping_2 = ctk.CTkOptionMenu(master=self, values=grouping_options,
                                            command=lambda event: self.check_grouping_selections(),
                                            variable=self.grouping_2_var)
        self.grouping_2.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

        self.grouping_3_var = ctk.StringVar(value='None')
        self.grouping_3 = ctk.CTkOptionMenu(master=self, values=grouping_options,
                                            command=lambda event: self.check_grouping_selections(),
                                            variable=self.grouping_3_var)
        self.grouping_3.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

        # Other options for PDF (batch_size, gr, and partition)
        self.others_label = ctk.CTkLabel(self, text=f'Other options', font=("Arial", 14, "bold"))
        self.others_label.grid(row=4, column=0, columnspan=2, padx=5, pady=7, sticky='ew')

        self.gr_var = ctk.BooleanVar()
        self.gr_checkbox = ctk.CTkCheckBox(master=self, variable=self.gr_var, text='GR', text_color='#455669')
        self.gr_checkbox.grid(row=5, column=0, padx=15, pady=5)

        self.partition_var = ctk.BooleanVar()
        self.partition_checkbox = ctk.CTkCheckBox(master=self, variable=self.partition_var, text='Partition',
                                                  command=self.check_grouping_selections,
                                                  text_color='#455669')
        self.partition_checkbox.grid(row=5, column=1, padx=15, pady=5)

        self.slider_var = ctk.IntVar(value=2)
        self.batch_slider = ctk.CTkSlider(master=self, from_=2, to=20, number_of_steps=18, variable=self.slider_var)
        self.batch_slider.grid(row=6, column=0, columnspan=2, padx=10, pady=20)

        self.update_idletasks()
        slider_x = (self.batch_slider.winfo_x())
        slider_y = (self.batch_slider.winfo_y())

        self.slider_label = ctk.CTkLabel(self, textvariable=self.slider_var, font=("Arial", 10))
        self.slider_label.place(x=(self.winfo_width() // 2)-6, y=(slider_y-29))

        # Generate PDF
        self.generate_button = ctk.CTkButton(master=self, text='Generate PDF', command=self.generate_pdf, fg_color='gray', hover_color='gray30')
        self.generate_button.grid(row=7, column=0, columnspan=2, padx=5, pady=5)

        self.bind('<FocusOut>', lambda event: self.destroy())
        self.check_grouping_selections()

    def generate_pdf(self):
        """"""

        g1, g2, g3 = self.grouping_1_var.get(), self.grouping_2_var.get(), self.grouping_3_var.get()
        gr, partition, batch_size = self.gr_var.get(), self.partition_var.get(), self.slider_var.get()
        callback_dict = {'groupings':[g1, g2, g3], 'gr': gr, 'partition': partition, 'batch_size': batch_size}

        self.callback(callback_dict)
        self.destroy()

    def check_grouping_selections(self):
        """"""

        g1, g2, g3 = self.grouping_1_var.get(), self.grouping_2_var.get(), self.grouping_3_var.get()
        f_groupings = [g for g in [g1, g2, g3] if g!='None']
        no_duplicates = len(f_groupings) == len(set(f_groupings))

        if not no_duplicates:
            self.generate_button.configure(state=ctk.DISABLED)
            return False

        # Disable if partition is off and it can't be superimposed
        if not self.can_superimpose and not self.partition_var.get():
            self.generate_button.configure(state=ctk.DISABLED)
            return False

        self.generate_button.configure(state=ctk.NORMAL)
        return True

class LabelToplevel(ctk.CTkToplevel):
    """Basic toplevel widget to display a specified message upon creation."""

    def __init__(self, master, title, text):
        super().__init__(master)
        self.title(title)
        master.update_idletasks()
        self.update_idletasks()
        center_x = (master.winfo_x() + master.winfo_width() // 2 - self.winfo_width() // 2)
        center_y = (master.winfo_y() + master.winfo_height() // 2 - self.winfo_height() // 2)

        self.geometry(f"+{center_x}+{center_y}")
        self.bind('<FocusOut>', self.destroy)

        self.grid_rowconfigure((0, 1), weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.label = ctk.CTkLabel(self,text=text)
        self.label.grid(row=0, column=0, padx=10, pady=5)

        self.close_button = ctk.CTkButton(master=self, text='Close window',width=20, command=self.destroy)
        self.close_button.grid(row=1, column=0, padx=5, pady=5)

    def destroy(self,event=None):
        if self.winfo_exists():
            self.unbind('<FocusOut>')

        super().destroy()

        return


class SlidingBase:
    """Base class that is meant to be inherited by widgets that slide."""

    def slide(self, ytarget:int, increment:int, direction:str):
        """A recursive function that creates the illusion of sliding, up or down, via multiple .place() calls.

        :param ytarget: the pixel y-value that the slide should end at
        :param increment: the pixel step-size (one can also think of this as speed)
        :param direction: either UP or DOWN
        """

        if direction == 'UP':
            if self.y <= ytarget:
                self.place(x=self.x, y=self.y)
                return

            if self.y > ytarget:
                self.place(x=self.x, y=self.y)
                self.y -= increment

                self.after(15, lambda: self.slide(ytarget, increment, direction='UP'))

        elif direction == 'DOWN':
            if self.y >= ytarget:
                self.place(x=self.x, y=self.y)
                if isinstance(self, SlidingFrame):
                    self.lower()
                return

            if self.y < ytarget:
                self.place(x=self.x, y=self.y)
                self.y += increment

                self.after(15, lambda: self.slide(ytarget=ytarget, increment=increment, direction='DOWN'))


class SlidingButton(ctk.CTkButton, SlidingBase):
    def __init__(self, master, x, y, **kwargs):
        super().__init__(master, font=('',1), text='', fg_color= 'gray',
                         hover_color='gray20', corner_radius=3.5, **kwargs)
        self.x = x
        self.y = y

        self.place(x=self.x, y=self.y, anchor='s')


class SlidingFrame(ctk.CTkFrame, SlidingBase):
    def __init__(self, master, x, y, **kwargs):
        super().__init__(master, **kwargs)
        self.x = x
        self.y = y

        self.place(x=self.x, y=self.y, anchor='n')


if __name__ == '__main__':
    print('custom_widgets.py was run')

