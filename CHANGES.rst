Changelog of lizard-riool
===================================================


0.9.2 (unreleased)
------------------

- Remove unused models, old code for computing lost capacity.

- Generate RIB files. Add a link to the Archive page.


0.9.1 (2013-06-21)
------------------

- Added an "archive page" at riolering/archief/

- Non computed water levels (because part of the system is not
  connected to the rest) are now stored as NULL values, and therefore
  drawing them in black now works.

- Increased max length of file path fields, we sometimes ran into them.

- Make sure no error messages occur in the upload window, it sometimes
  gets confused

- Increase chunk size, uploading files > 50mb went wrong

- Improved error messages.


0.9 (2013-06-20)
----------------

- New upload screen (UploadsView); divides uploads in four categories
  (not processed yet, being processed, errors, successful) and does all
  processing in the background. Overview on the page uses Ajax and changes
  as files are being processed. Has links to an error screen and uploads
  can be removed.

- An uploaded file can have a list of errors now that are all saved in
  the database, to be shown on an error screen.

- Parsing and initial processing of .RIB and .RMB files is moved into a new
  library, sufriblib.

- Reimplement lost capacity algorithm. It doesn't seem to work correctly yet.

- Add "virtual sewers" if a sewer is present in the RIB file, but not
  in the RMB file.

- Add virtual measurements at the locations of the manholes, height
  equal to the sewer's BOBs

- Save a Sewerage's files once it has been imported successfully, to a
  directory that is independent of the Upload.

- Implemented quality criteria; missing measurements result in
  "quality unknown", sufficient measurements in "quality reliable" and
  too few measurements in "quality unreliable".

- Tweak the error screen: show only errors, show only part of the
  line.

- Try to reconstruct a manhole's surface level using a sewer's bob and
  distance from bob to cover

- Improve check if some RMB name already exists; error out if a file of the
  same name is already being processed.


0.5.13 (2013-05-22)
-------------------

- Improve visibility of lost capacity by using a 2x2 pixel.


0.5.12 (2013-01-18)
-------------------

- Correction of z-values has been made more robust.


0.5.11 (2012-12-17)
-------------------

- Fix icons being drawn under the file-management item.

- Moved css and script tags to their proper location (in the beheer.html)

- Modified plupload to use $.jqbutton instead of $.button.


0.5.10 (2012-11-30)
-------------------

- Fix the spinner when a "langsprofiel" is loading.


0.5.9 (2012-11-27)
------------------

- Add support for Lizard 4.0 by fixing some styling issues.

- Properly set dependency versions.


0.5.8 (2012-06-08)
------------------

- Improved performance by using bulk_create (Django 1.4).


0.5.7 (2012-06-04)
------------------

- Fixed bug in the correction of z-values of reversed MRIO
  measurements (i.e. ZYB == "2").


0.5.6 (2012-05-29)
------------------

- MRIO measurements are corrected to prevent sawtooth-like graphs.


0.5.5 (2012-05-25)
------------------

- Made syntax compatible with Python 2.6 (no dict comprehension).


0.5.4 (2012-05-07)
------------------

- Skipping graph nodes without computed results for download.


0.5.3 (2012-05-07)
------------------

- Computed results (lost capacity aka "verloren berging") can now be downloaded.


0.5.2 (2012-05-03)
------------------

- Previously uploaded files can now be deleted.

- Fixed another missing adapter issue.


0.5.1 (2012-04-26)
------------------

- Fix for internal server error (missing adapter).


0.5 (2012-04-26)
----------------

- Created a datamodel.py to hold some of the more generic things that
  were in parsers.py and views.py

- As a result, a bug with puts that didn't show up on the graph
  (e.g. trac #3594) was solved.

- We now use the minimum z value of the actual Put objects, not of the
  Put's neighbours. This gives more accurate results.

- Added a model that remembers the sink of each RMB file

- Added a model that stores the lost capacity percentages of each
  measurement point

- Made a Celery task that computes lost capacity and implements good
  locking so that the task only ever runs once at any given
  moment. Task is called after uploading files and whenever the side
  profile page is viewed and there are RMB files without computed lost
  capacity.

- Show an icon after files that aren't computed yet. They can't be
  clicked.

- Coloured the lines that represent sewers on the map according to
  lost capacity. This had to be implemented by drawing thousands of
  1-pixel "icons". First in its own adapter on its own page, later
  merged into the existing adapter for side profile graphs.

- Improved classes and colours of the lost capacity visualization.

- Corrected calculation of the lost capacity based on the height
  percentage of flooding in a circular pipe.

- Slightly improved README

- Added a legend to the workspace items

- Added a mouseover function that shows lost capacity percentage

- Fixed a nasty bug in which cached graphs would fail to draw
  correctly

0.4.5 (2012-04-17)
------------------

- We now give Put objects in the graph a z-value that is the minimum
  of the z-values of the connecting strengs. This solves bugs where
  the put had a higher z-value and therefore seemed to be a high
  barrier that prevented water from draining away.

  This solves several tickets, at least #3603 and #3626.

  Puts in the side profile graph can now look like "spikes" because
  their bottom and top depend on all the connecting strengs, not just
  the ones shown in the graph. For now this is OK.

0.4.4 (2012-04-06)
------------------

- FLooded side profiles (with a known issue: #3603).


0.4.3 (2012-03-16)
------------------

- Fixed dialog resize problem with Firefox.

- Fixed missing ACR/ACS values in SUFRMB.


0.4.2 (2012-03-15)
------------------

- Side profile ("langsprofiel") popup is now correctly centered on the screen.

- Side profile ("langsprofiel") popup shows an ajax loader while waiting.

- Side profile ("langsprofiel") popup displays a new graph upon resize.


0.4.1 (2012-03-12)
------------------

- Filesystem caching of network graphs.


0.4 (2012-03-09)
----------------

- Initial version of side profile ("langsprofiel") functionality.


0.3 (2012-03-01)
----------------

- Initial version of path selection in network.


0.2.1 (2012-02-28)
------------------

- The parser now displays the line number of an erroneous line.


0.2 (2012-02-15)
----------------

- Implemented workspace item adapters for sufrib and sufrmb.


0.1 (2012-02-10)
----------------

- Initial release having file upload functionality for sufrib and sufrmb.
