# PlotGUI (beta-version)
Visualization GUI that takes MK DiaMOND pickle file output 

Features: 
* View dose response or growth rate curves
  * Overlay multiple strains or timepoints on a single plot
  * 'QuickView' to see 12 plots at a time (instead of the default 4)
  * Annotations on click 

* Selection to PDF feature

* Manual selection feature on double-click (for DiaMOND)

----------------

Keybinds and additional notes: 
* L/R arrow to navigate between display frames
* D arrow to clear any visible plots and return to default state of GUI
  
* Button at the bottom of page upon initialization can be used in order to slide parameter frame into view
* Multiple strains OR multiple timepoints can be selected but not both
* GR curves may error since case where GRinf is None was not handled yet.
* For Manual selection, in the case of Algo is None, that rep will not be added to MS_Flag. 
* Clearing memory may still not be perfectly handled
* If file is already selected and one clicks the file button again without selecting a file, may cause error. 

![Screenshot 2025-06-30 at 1 34 28 PM](https://github.com/user-attachments/assets/b54d9fb1-cb60-48bf-b8c4-86648f88f0d9)
![Screenshot 2025-06-30 at 1 34 44 PM](https://github.com/user-attachments/assets/5943555c-fa24-43e0-8afd-0801de1d4983)
![Screenshot 2025-06-30 at 1 35 40 PM](https://github.com/user-attachments/assets/61a9a670-de6e-41d0-b704-8fa65c9036cf)








Last updated: 6/30/25
