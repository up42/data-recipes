# Module to filter stereo pairs/tristereo triples from a list of
# search result using an acquisition date and incidence angle
# heuristic.

from datetime import datetime as dt

import re

# Get the modules required for reducing the acquisition dates.
from functools import reduce
from operator import sub as minus_op

# Create multiple paralllel iterators and flatten a list.
from itertools import tee, chain, pairwise, filterfalse

# Trigonometric calculations and "rounding" functions.
from math import ceil, radians, sin

from typing import Union, Final

# GeoJSON library.
from geojson import FeatureCollection

# Handling dictionaries more functionally.
from toolz.dicttoolz import get_in

# Geometry handling functions.
from shapely.geometry import shape
from shapely import intersection

# The maximum acquisition date delta in seconds in a stereo/tri-stereo capture.
MAX_ACQ_TIME_DELTA: Final[int] = 90
# The minimum overlao for the footprints.
MIN_OVERLAP_PERCENTAGE: Final[float] = 95.0

# B/H range for Pléiades, SPOT and Pléiades NEO.
B_H_RANGE_SENSORS: Final[dict]={"phr": {"stereo": {"upper": 0.6,
                                                   "lower": 0.15
                                                   },
                                        "tristereo": {"upper": 0.7,
                                                      "lower": 0.3
                                                      }
                                        },
                                "spot": {"stereo": {"upper": 0.6,
                                                    "lower": 0.15
                                                    },
                                         "tristereo": {"upper": 0.7,
                                                       "lower": 0.3
                                                       }
                                         },
                                "pneo": {"stereo": {"upper": 0.5,
                                                    "lower": 0.15
                                                    },
                                         "tristereo": {"upper": 0.7,
                                                       "lower": 0.3
                                                       }
                                         }
                                }

# Dictionary key list (tree) for getting the data collection  key for the search results.
catalog_constellation_key: Final[list] = ["properties", "collection"]
# Dictionary key list (tree) for getting the acquisition dates for the search results (catalog).
catalog_datetime_key: Final[list] = ["properties", "acquisitionDate"]
# Dictionary key list (tree) for getting the incidence angle for search results (catalog).
catalog_angles_key: Final[list] = ["properties",  "providerProperties",
                                   "incidenceAngleAlongTrack"]
# Dictionary key list (tree) for getting the geometry (footprint) for search results (catalog).
catalog_geometry_key: Final[list] = ["geometry"]


def compute_delay(*dates: str) -> int:
    """Computes the delay in seconds between two given dates

    Parameters
    ----------
    *dates : str
        two dates for computing the difference given as "yyyy-mm-dd"

    Returns
    -------
    int
        The difference in seconds between the tow given dates.

    Examples
    --------
    compute_delay("2023-06-26", "2021-04-01")

    """
    return abs(int(reduce(minus_op,
                          map(lambda d: dt.timestamp(
                              dt.strptime(f"{d}T00:00:00",
                                          "%Y-%m-%dT%H:%M:%S",
                                          )),
                              [*dates]))))

def format_date(date: str) -> str:
    """Formats a date in a consistent manner so that we have always a microsecond value.

    Parameters
    ----------
    date : str
        A date string

    Returns
    -------
    str
        A modified (with microseconds) date string

    Examples
    --------
    format_date("2019-12-25T16:12:29Z")
    format_date("2019-12-30T14:33:22.430Z")

    """

    # Normal acquisition date string that has a milliseconds value.
    if re.search(r"(?P<ms>\.\d{3})Z$", date):
        return re.sub(r"(?P<ms>\.\d{3})Z$", r"\g<ms>000Z", date)
    # Sometimes the acquisition date doesn't have a milliseconds
    # value. We need to take care of it.
    return re.sub(r"(?P<ds>.*)Z$", r"\g<ds>.000000Z", date)


def is_stereo_dates(*acquisition_dates: str, delay: int=MAX_ACQ_TIME_DELTA) -> bool:
    """Checks to see if the acquisition dates are within the range
    allowed for a stereo/tri-stereo capture.

    Parameters
    ----------
    *acquisition_dates : str
        pair/triple of acquisition dates
    delay : int
        maximum allowed difference in seconds between acquisition dates

    Returns
    -------
    bool
        True if the dates are within a stereo/tri-stereo range, False
        if not.

    Examples
    --------
    is_stereo_dates("2021-10-13T10:59:01.624Z", "2021-10-13T10:58:42.874Z")
    is_stereo_dates("2021-10-07T11:21:34.555Z", "2021-10-07T11:21:20.305Z",
                    "2021-10-07T11:21:06.180Z")

    """

    # Convert the milliseconds to microseconds. Python doesn't have a
    # milliseconds date format descriptor. See:
    # https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes. Also
    # create a UNIX timestamp from the given acquisition dates.
    return 0 < reduce(minus_op, map(lambda d: dt.timestamp(
        dt.strptime(
            format_date(d),
            "%Y-%m-%dT%H:%M:%S.%fZ")), acquisition_dates)) < delay


def is_stereo_angles(*incidence_angles: float, sensor: str, tristereo: bool=False) -> bool:
    """Checks is the incidence angles along the track are within the
    B/H bounds defined for a given satellite when doing
    stereo/tri-stereo captures.

    Parameters
    ----------
    *incidence_angles : float
        pair/triple of incidence angles along the track
    sensor : str
        the name of the sensor (satellite)
    tristereo : bool
        True if we are looking for tri-stereo, False if looking for
        stereo.

    Returns
    -------
    bool
        True if the angles are such that we are within the B/H range
        for stereo/tri-stereo. False if not.

    Examples
    --------
    is_stereo_angles(12.458, -1.567, sensor="phr")
    is_stereo_angles(12.458, -1.567, 4.674, sensor="phr", tristereo=True)

    """

    # Compute the sin of each incidence angle along track. Assuming
    # the curvature of the Earth is negligible for the maximum length
    # of stereo/tri-stereo captures. Up to 100 km. The curvature of the
    # Earth will make it so that the "drop" between, the beginning and
    # the end of the capture is roughly 800 m for a 100 km length.
    b_over_h = reduce(lambda x, y: abs(sin(radians(x))) + abs(sin(radians(y))),
                      incidence_angles)

    # Since the specific of B/H is given with one decimal only in the
    # manuals we need to be a bit unprecise when computing the B/H
    # value otherwise we will miss stereo and above all tristereo
    # pairs.
    b_over_h = ceil(b_over_h * 10) / 10
    # Get the acquisition mode.
    mode = "tristereo" if tristereo else "stereo"
    # Check if B/H is within the respective sensor bounds.
    return B_H_RANGE_SENSORS[sensor][mode]["lower"] <= b_over_h <= B_H_RANGE_SENSORS[sensor][mode]["upper"]


def is_overlapping(*geometries: dict,
                   min_overlap_percentage: float=95.0) -> bool:
    """Predicate that verifies that a given set of geometries overlap
    to a certain percentage.

    Parameters
    ----------
    *geonetries : dict
        set of geometries
    min_overlap_percentage : float
        the lowest possible value for the overlap percentage

    Returns
    -------
    bool
        True if the geometries overlap up to the set percentage. False
        otherwise.

    Examples
    --------
    FIXME: Add docs.

    """
    print
    # Get the shapes (Shapely geometric objects).
    geom_shapes = list(map(lambda e: shape(e), geometries))
    # Compute the overlaps.
    min_area_size = reduce(min, list(map(lambda s: s.area, geom_shapes)))
    overlaps = list(map(lambda g: intersection(g[0], g[1]).area * 100/min_area_size,
                        pairwise(geom_shapes)))

    # Check the overlap percentage.
    it = filterfalse(lambda e: e >= min_overlap_percentage, overlaps)
    # Return the result based on the overlap percentages. If any is
    # below the overlap_percentage_lower_bound then return False. True
    # otherwise.
    return True if next(it, None) is None else False


def select_stereo(feature_list: list[dict],
                  delay: int=MAX_ACQ_TIME_DELTA,
                  min_overlap_percentage: float=MIN_OVERLAP_PERCENTAGE,
                  ) -> Union[None, list[dict]]:

    """Given a list of GeoJSON simple features it returns the ones
    that are possibly stereo pairs.

    Parameters
    ----------
    feature_list : list[dict]
        A list of GeoJSON simple features.
    delay : int
        Maximum allowed difference in seconds between acquisition dates.
    min_overlap_percentage : float
        The lowest possible value for the overlap percentage.

    Returns
    -------
    Union[None, list[dict]]
        A list of pairs that are probable stereo pairs.

    """

    # Get an iterator from the given list.
    it = iter(feature_list)
    # Create two parallel iterators.
    (a, b) = tee(it)
    # Advance the second iterator.
    next(b, None)
    # Build a list of consecutive pairs from the given list. Filter
    # that list for stereo pairs. This works due to the ordering of
    # the search results.
    return list(filter(lambda e:
                       is_stereo_dates(
                           get_in([0] + catalog_datetime_key, e),
                           get_in([1] + catalog_datetime_key, e),
                           delay=delay,
                       )
                       and
                       is_stereo_angles(
                           get_in([0] + catalog_angles_key, e),
                           get_in([1] + catalog_angles_key, e),
                           sensor=get_in([0] + catalog_constellation_key, e),
                       )
                       and
                       is_overlapping(
                           get_in([0] + catalog_geometry_key, e),
                           get_in([1] + catalog_geometry_key, e),
                           min_overlap_percentage=min_overlap_percentage,
                       ),
                       list(zip(a, b))
                       )
                )


def select_tristereo(feature_list: list[dict],
                     delay: int=MAX_ACQ_TIME_DELTA,
                     min_overlap_percentage: float=MIN_OVERLAP_PERCENTAGE) -> Union[None, list[dict]]:
    """Given a list of GeoJSON simple features it returns the ones
    that are possibly tri-stereo triples.

    Parameters
    ----------
    feature_list : list[dict]
        A list of GeoJSON simple features.
    delay : int
        Maximum allowed difference in seconds between acquisition dates.
    min_overlap_percentage : float
        The lowest possible value for the overlap percentage.

    Returns
    -------
    Union[None, list[dict]]
        A list of triples that are probable tri-stereo triples.

    """

    # Get an iterator from the given list.
    it = iter(feature_list)
    # Create three parallel iterators.
    (a, b, c) = tee(it, 3)
    # Advance the second iterator.
    next(b, None)
    # Advance twice the third iterator.
    next(c, None), next(c, None)
    # Build a list of consecutive triples from the given list. Filter
    # that list for tri-stereo triples. We only analyse the "extreme"
    # positions, hence we only check for the first and third element
    # of the triple for the dates and angles. For overlap we look for
    # all the footprints.
    return list(filter(lambda e:
                       is_stereo_dates(
                           get_in([0] + catalog_datetime_key, e),
                           get_in([2] + catalog_datetime_key, e),
                           delay=delay,
                       )
                       and
                       is_stereo_angles(
                           get_in([0] + catalog_angles_key, e),
                           get_in([2] + catalog_angles_key, e),
                           sensor=get_in([0] + catalog_constellation_key, e),
                           tristereo=True,
                       )
                       and
                       is_overlapping(
                           get_in([0] + catalog_geometry_key, e),
                           get_in([1] + catalog_geometry_key, e),
                           get_in([2] + catalog_geometry_key, e),
                           min_overlap_percentage=min_overlap_percentage,
                       ),
                       list(zip(a, b, c))
                       )
                )


def get_features(results_list: list[tuple]) -> dict:
    """Convenience function to generate a feature collection
    given a list of results.

    Parameters
    ----------
    results_list : list[tuple]
        A list of pairs/triples containing the he given stereo
        pairs/tri-stereotriples.

    Returns
    -------
    dict
        Feature collection with all the results.

    """

    return FeatureCollection(list(chain.from_iterable(results_list)))


## NEEDS WORK
def modify_geometries_intersected():
    pass

def modify_geometries_intersected_aux(items: tuple[dict,dict]) ->  tuple[dict, dict]:
    intersected_geometry = dict(geometry=mapping(
        intersection(shape(get_in([0, "geometry"], items)),
                     shape(get_in([1, "geometry"], items)))))
    return(items[0] | intersected_geometry, items[1] | intersected_geometry)
## NEEDS WORK


def get_stereo_image_ids(results_list: list[tuple]) -> list[str]:
    """Convenience function to extract the image IDs from a list of
    given stereo pairs.

    Parameters
    ----------
    results_list : list[tuple]
        A list of pairs containing the IDs of the given stereo pairs.

    Returns
    -------
    list[str]
        A list of UUIDs that are the IDs of the images for the given
        stereo pairs.

    """


    return list(chain.from_iterable(map(lambda e: [e[0]["properties"]["id"],
                                                   e[1]["properties"]["id"]],
                                        results_list)))


def get_tristereo_image_ids(results_list: list[tuple]) -> list[str]:
    """Convenience function to extract the image IDs from a list of
    given tri-stereo triples.

    Parameters
    ----------
    results_list : list[tuple]
        A list of pairs containing the IDs of the given tri-stereo triples.

    Returns
    -------
    list[str]
        A list of UUIDs that are the IDs of the images for the given
        stereo pairs.

    """
    # Build and flatten the list using chain.from_iterable.
    return list(chain.from_iterable(map(lambda e: [e[0]["properties"]["id"],
                                                   e[1]["properties"]["id"],
                                                   e[2]["properties"]["id"]],
                                        results_list)))
