# PlotGUI (beta-version)
Visualization GUI that takes MK DiaMOND pickle (.pkl) file output. <br>
Internal name: "Margarine", sister product of "Butter" <br>
Last updated: 7/3/25

----------------

### Features:
* View dose response or growth rate curves
  * Overlay multiple strains or timepoints on a single plot
  * Segmented button to to see 4, 6, or 12 plots at a time (with varying functionalities)
  * Annotations on click 

* Selection to PDF feature

* Manual selection feature on double-click (for DiaMOND)

----------------

### Keybinds and additional notes:
* L/R arrow to navigate between display frames
* D arrow to clear any visible plots and return to default state of GUI
* Thin gray button at the bottom of page can be used in order to slide parameter frame into view
* Multiple strains OR multiple timepoints can be selected but not both
* For Manual selection, in the case of Algo is None, that rep will not be added to MS_Flag. 

### Known bugs:
* Clearing memory may still not be perfectly handled
* If file is already selected and one clicks the file button again without selecting a file, may cause error.
* Use of plt.subplots when selecting individual drug instead of plt.figure
* r/f-strings incompatibility with some computers
  
  
----------------

### Reference 1<br>

- Previous, but still relevant version of GUI (QuickView is replaced by segmented button to select either 4, 6, or 12 plot views)
- QuickView is off. Default: 4 plot view 
- Manual selection Toplevel and facecolor change on selection 
- Annotation on click
- Parameter frame is currently hidden (can be made visible using thin gray button)

![Screenshot 2025-06-30 at 6 45 21 PM](https://github.com/user-attachments/assets/a8c19272-3f8e-468a-8900-0c32c94fcceb)

<br>

### Reference 2<br>

- Most up-to-date version of GUI
- Segmented button. Current: 12 plot view 
- Multiple strains selected
- Parameter frame is currently visible (can be hidden from view using thin gray button)

<img width="893" height="849" alt="Screenshot 2025-07-30 at 4 38 59 PM" src="https://github.com/user-attachments/assets/b116c8d6-6255-401d-9478-639a1bd8ba4b" />

<br>

