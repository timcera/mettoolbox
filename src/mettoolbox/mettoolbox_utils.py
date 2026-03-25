from .toolbox_utils.src.toolbox_utils import tsutils

_LOCAL_DOCSTRINGS = tsutils.docstrings
_LOCAL_DOCSTRINGS["latitude"] = """latitude:
        The latitude of the location expressed in decimal degrees.  The
        southern hemisphere is expressed as a negative value."""
_LOCAL_DOCSTRINGS["longitude"] = """longitude:
        The longitude of the location expressed in decimal degrees.  The
        western hemisphere is expressed as a negative value."""
_LOCAL_DOCSTRINGS["vardesc"] = """If int or float use the value.  If
        array_like, then convert to numpy array.  If string, then split
        on commas and use as array_like.

        If None (the default) then `input_ts` and `columns` must be set."""
sunits = _LOCAL_DOCSTRINGS["source_units"]
sunits = sunits.split("\n")
del sunits[1:3]
_LOCAL_DOCSTRINGS["psource_units"] = "\n".join(sunits)
