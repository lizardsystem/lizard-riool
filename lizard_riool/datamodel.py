"""Contains classes that implement the datamodel. At the moment those
are spread out over parsers.py, views.py and models.py, but the goal
is to put at least the main sewer pool graph in here.

The ideal situation would be that models.py and parsers.py are
independent (don't import from other lizard-riool modules), this
module datamodel.py imports parsers and models, and views.py only
imports datamodel.py. However as this model is created very late in
the project, there is no time for that."""

import logging
import networkx
import os
import pprint

from django.core.cache import get_cache

from lizard_riool import parsers
from lizard_riool import models

logger = logging.getLogger(__name__)

# Our objects become larger than 1M, so they don't fit in memcached
cache = get_cache('file_based_cache')


class RMB(object):
    """This file models a single RMB file, which is a single sewer
    'streng' pool, for which a single graph is made that contains the
    lost volume data."""

    def __init__(self, uploaded_file_id):
        """Gets the data for the RMB file with this Upload id.  Raises
        ValueError if the id doesn't exist."""

        if isinstance(uploaded_file_id, models.Upload):
            self.uploaded_file_id = uploaded_file_id.pk
            self.rmb_file = uploaded_file_id
        else:
            self.uploaded_file_id = uploaded_file_id
            self.rmb_file = self._init_rmb_file()
        self.rib_file = None
        self.pool = self._init_pool()
        self.graph = self._init_graph()
        self.sink = None
        self.lost_water_depth_computed = False
        self.flooded_percentages_computed = False

    def compute_lost_water_depth(self, put=None):
        """Compute the level of flooding within the graph. To do this, we may
        need to find the RIB file corresponding to this RMB file (to find the
        sink), and for that it helps to have a put."""
        if self.lost_water_depth_computed:
            return

        sink = self._find_sink(put)
        if sink:
            logger.debug("Computing lost water depth.")
            parsers.compute_lost_water_depth(
                self.graph, (sink.CAB.x, sink.CAB.y))
            self.lost_water_depth_computed = True
        else:
            raise ValueError("No sink!")

    def compute_flooded_percentages(self):
        """Compute flooded percentages for the graph. Get them from
        the database if they already exist, otherwise compute lost
        water depth first, then store the computed percentages in the
        database."""
        if self.flooded_percentages_computed:
            return

        if models.StoredGraph.is_stored(self.uploaded_file_id):
            self.flooded_percentages_computed = True
            return

        self.compute_lost_water_depth()
        models.StoredGraph.store_graph(self.uploaded_file_id, self.graph)
        self.flooded_percentages_computed = True

    def get_riool(self, sufid):
        """Get riool from the pool by sufid."""

        # The for loop is probably overkill, since the Riool object is
        # the first element of the list. But perhaps this is more
        # robust.
        for obj in self.pool[sufid]:
            if obj.suf_id == sufid:
                return obj

    def _init_rmb_file(self):
        """Find the RMB file. Raise ValueError if it doesn't exist."""
        try:
            return models.Upload.objects.get(pk=self.uploaded_file_id)
        except models.Upload.DoesNotExist:
            raise ValueError("Upload with id %s does not exist." %
                             (str(self.uploaded_file_id),))

    def _init_pool(self):
        """Parse the file into a pool dict, and cache it."""

        pool_cache_key = "pool_%d" % self.uploaded_file_id
        pool = cache.get(pool_cache_key, {})

        if not pool:
            parsers.parse(self.rmb_file.full_path, pool)
            logger.debug(pprint.pformat(pool))
            cache.set(pool_cache_key, pool)
        return pool

    def _init_graph(self):
        """Init the graph, and cache it."""

        graph_cache_key = "graph_%d" % self.uploaded_file_id
        graph = {}
#        graph = cache.get(graph_cache_key, {})

        if not graph:
            graph = networkx.Graph()
            parsers.convert_to_graph(self.pool, graph)
            cache.set(graph_cache_key, graph)

        return graph

    def _find_sink(self, put=None):
        """Find sink for this RMB file. Get it from the database
        cache, or the corresponding RIB file."""

        logger.debug("Looking for sink using put %s" % str(put))

        if not self.sink:
            self.sink = models.SinkForUpload.get(self.rmb_file)

        if not self.sink:
            rib_file = self._find_rib_file(put)

            if rib_file:
                # We need to know which manhole (i.e. "put")
                # has been designated as the sink.

                try:
                    self.sink = (models.Put.objects.filter(upload=rib_file)
                                 .get(_CAR='Xs'))
                    models.SinkForUpload.set(self.rmb_file, self.sink)
                    logger.debug("Sink = %s" % self.sink)
                except models.Put.DoesNotExist:
                    logger.warn("No sink defined for %s" % \
                                    rib_file.full_path)

        return self.sink

    def _find_rib_file(self, put=None):
        """Find the relevent RIB file. First we look for a file with
        the same name as the current RMB file and a different
        extension, otherwise this function can use a Put object and
        see in which file it was uploaded."""

        if self.rib_file:
            return self.rib_file

        sufrib = os.path.splitext(self.rmb_file.the_file.name)[0] + '.rib'

        try:
            rib_upload = models.Upload.objects.get(the_file__iexact=sufrib)
        except models.Upload.DoesNotExist:
            logger.warn("Could not find SUFRIB for %s by name" % \
                            self.rmb_file.the_file.name)
            rib_upload = None

        if not rib_upload:

            # The corresponding SUFRIB could not be found by name.
            # Find a SUFRIB having 'put' as a last resort.

            try:
                rib_upload = models.Put.objects.filter(
                    _CAA=put)[0:1].get().upload
            except models.Put.DoesNotExist:
                logger.warn("Could not find SUFRIB for %s by put" % \
                                self.rmb_file.the_file.name)
                rib_upload = None

        self.rib_file = rib_upload
        return self.rib_file

def compute_all_flooded_percentages():
    for f in models.Upload.objects.filter(the_file__iendswith='.rmb'):
        if not f.has_computed_percentages:
            rmb = RMB(f.pk)
            rmb.compute_flooded_percentages()
