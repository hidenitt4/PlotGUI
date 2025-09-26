# PlotGUI (beta-version)
Visualization GUI that takes MK DiaMOND pickle (.pkl) file output. <br>
Internal name: "Margarine", sister product of "Butter" <br>
Last updated: 9/25/25

----------------

### Features:
* View dose response or growth rate inhibition curves
  * Overlay multiple strains or timepoints on a single plot
  * Segmented button to to see 4, 9, or 16 plots at a time
  * Annotations on click
  * Partition elements of curves to single plot view 

* Selection to PDF or PNG(s) feature
  * Edit grouping preferences, view GR, partition plots, and control batch size of PDF file

* Manual selection feature on double-click (to exclude certain replicates from DiaMOND analysis)

----------------

### Keybinds and additional notes:
* L/R arrow to navigate between display frames
* D arrow to clear any visible plots and return to default state of GUI
* Spacebar to lift parameter frame into view (or click on thin gray button on the bottom of the page)
* Multiple strains OR multiple timepoints can be selected (not multiple of both)
* For manual selection, in the case of Algo is None, that rep will not be added to MS_Flag. 

### Known bugs (to be fixed):
* Clearing memory may still not be perfectly handled
* If file is already selected and one clicks the file button again without selecting a file, may cause error.
* Use of plt.subplots when selecting individual drug instead of plt.figure
* Possible r/f-strings string delimiter conflict

  
----------------

### Reference 1<br>

- 9 plot view 
- Multiple strains are superimposed for easy comparison 
- Annotation on click
- Parameter frame is currently visible (and can be hidden)

<img width="750" height="675" alt="Screenshot 2025-09-25 at 9 15 54 PM" src="https://github.com/user-attachments/assets/640331d0-aa31-4d58-af05-9abdd95016ad" />

<br>

### Reference 2<br>

- 16 plot view
- Partitioned
- Manual selection toplevel and replicate is highlighted red on removal
- Parameter frame is currently hidden (can be made visible)
  

<img width="750" height="675" alt="Screenshot 2025-09-25 at 9 38 32 PM" src="https://github.com/user-attachments/assets/c2d64ff2-5221-4818-b197-7b5c45b2822c" />


<br>

### Reference 3<br>

- 4 plot view
- Save to PDF toplevel with options to control output file format 


<img width="750" height="675" alt="Screenshot 2025-09-25 at 9 19 27 PM" src="https://github.com/user-attachments/assets/f1e801fc-3f44-4ee8-af1d-663d86f39e2a" />


<br>
