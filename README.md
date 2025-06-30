# PlotGUI (beta-version)
Visualization GUI that takes MK DiaMOND pickle file output 

Features: 
* View dose response or growth rate curves
  * Overlay multiple strains or timepoints on a single plot
  * 'QuickView' to see 12 plots at a time (instead of the default 4)
  * Annotations on click 

* Selection to PDF feature

* Manual selection feature on double-click (for DiaMOND)
\n
Keybinds and additional notes: 
* L/R arrow to navigate between display frames
* D arrow to clear any visible plots and return to default state of GUI
  
* Button at the bottom of page upon initialization can be used in order to slide parameter frame into view
* Multiple strains OR multiple timepoints can be selected but not both
* GR curves may error since case where GRinf is None was not handled yet.
* For Manual selection, in the case of Algo is None, that rep will not be added to MS_Flag. 





Last updated: 6/30/25
