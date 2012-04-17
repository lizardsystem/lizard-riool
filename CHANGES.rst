Changelog of lizard-riool
===================================================


0.4.6 (unreleased)
------------------

- Nothing changed yet.


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
