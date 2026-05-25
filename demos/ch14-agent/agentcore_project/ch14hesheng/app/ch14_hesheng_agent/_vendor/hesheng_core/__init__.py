"""hesheng_core — shared substrate for FDE book chapter demos.

Public surface used by chapter demos:

    from hesheng_core import config, athena, ontology

    cfg = config.load()                    # bucket names, db, region
    rows = athena.query(cfg, "SELECT ...")
    ontology.RESOLUTION_VIEW               # the SQL view name to query
"""

from . import athena, config, ontology

__all__ = ["athena", "config", "ontology"]
