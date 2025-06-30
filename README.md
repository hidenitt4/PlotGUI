# PlotGUI (beta-version)
Visualization GUI that takes MK DiaMOND pickle file output 

----------------

### <b>Features:<b>
* View dose response or growth rate curves
  * Overlay multiple strains or timepoints on a single plot
  * 'QuickView' to see 12 plots at a time (instead of the default 4)
  * Annotations on click 

* Selection to PDF feature

* Manual selection feature on double-click (for DiaMOND)

----------------

### <b>Keybinds and additional notes:<b> 
* L/R arrow to navigate between display frames
* D arrow to clear any visible plots and return to default state of GUI
<br>

* Button at the bottom of page upon initialization can be used in order to slide parameter frame into view
* Multiple strains OR multiple timepoints can be selected but not both
* GR curves may error since case where GRinf is None was not handled yet.
* For Manual selection, in the case of Algo is None, that rep will not be added to MS_Flag. 
* Clearing memory may still not be perfectly handled
* If file is already selected and one clicks the file button again without selecting a file, may cause error.
  
<br>
<br>
<br>

----------------

<b>Reference 1<b><br>

- Default 4 plot view
- Manual selection Toplevel and facecolor change on selection 
- Annotation on click

![Screenshot 2025-06-30 at 1 35 40 PM](https://github.com/user-attachments/assets/715cae8c-48d4-4252-b9ce-11b997a70acf)

<br>
<br>

<b>Reference 2<b><br>

- QuickView, 12 plot view
- Multiple timepoint selections
- Parameter frame is currently visible (can be hidden from view using thin gray button)

![Screenshot 2025-06-30 at 1 34 28 PM](https://github.com/user-attachments/assets/afb47129-aaa8-40a9-b1f9-efbe215f5da2)








Last updated: 6/30/25
