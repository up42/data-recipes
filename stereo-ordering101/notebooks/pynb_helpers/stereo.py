# Module to filter stereo pairs/tristereo triples from a list of
# search result using an acquisition date and incidence angle
# heuristic.

from datetime import datetime as dt

import re

# Get the modules required for reducing the acquisition dates.
from functools import reduce
from operator import sub as minus_op

# Create multiple paralllel iterators and flatten a list.
from itertools import tee, chain

# Trigonometric calculations functions.
from math import sin, radians

from typing import Union, Final

# The maximum acquisition date delta in seconds in a stereo/tri-stereo capture.
MAX_ACQ_TIME_DELTA: Final[float]= 90

# B/H range for Pléiades, SPOT and Pléiades NEO.
B_H_RANGE_SENSORS: Final[dict]={"phr": {"stereo": {"upper": 0.6,
                                                   "lower": 0.15
                                                   },
                                        "tri-stereo": {"upper": 0.7,
                                                       "lower": 0.3
                                                       }
                                        },
                                "spot": {"stereo": {"upper": 0.6,
                                                    "lower": 0.15
                                                    },
                                         "tri-stereo": {"upper": 0.7,
                                                        "lower": 0.3
                                                        }
                                         },
                                "pneo": {"stereo": {"upper": 0.5,
                                                    "lower": 0.15
                                                    },
                                         "tri-stereo": {"upper": 0.7,
                                                        "lower": 0.3
                                                        }
                                         }
                                }


def is_stereo_dates(*acquisition_dates: str) -> bool:
    """Checks to see if the acquisition dates are within the range allowed for a stereo/tri-stereo capture.

    Parameters
    ----------
    *acquisition_dates : str
        pair/triple of acquisition dates

    Returns
    -------
    bool
        True if the dates are within a stereo/tri-stereo range, False
        if not.

    Examples
    --------
    is_stereo_dates(("2021-10-13T10:59:01.624Z", "2021-10-13T10:58:42.874Z"))
    is_stereo_dates(("2021-10-07T11:21:34.555Z", "2021-10-07T11:21:20.305Z", "2021-10-07T11:21:06.180Z"))

    """

    # Convert the milliseconds to microseconds. Python doesn't have a
    # milliseconds date format descriptor. See:
    # https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes. Also
    # create a UNIX timestamp from the given acquisition dates.
    return reduce(minus_op, map(lambda d: dt.timestamp(
        re.sub(r"(?P<ms>\.\d{3})Z$", r"\g<ms>000Z", d),
        "%Y-%m-%dT%H:%M:%S.%fZ"), acquisition_dates)) < MAX_ACQ_TIME_DELTA


def is_stereo_angles(*incidence_angles: float, sensor: str, tristereo: bool=False) -> bool:
    """Checks is the incidence angles along the track is within the B/H bounds defined for a given satellite when doing stereo/tri-stereo captures.

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
    is_stereo_angles((12.458, -1.567))
    is_stereo_angles((12.458, -1.567, 4.674))

    """

    # Compute the sin of each incidence angle along track. Assuming
    # the curvature of the Earth is negligible for the maximum length
    # of stereo/tri-stereo captures. Up to 100 km. The curvature of the
    # Earth will make it so that the "drop" between, the beginning and
    # the end of the capture is roughly 800 m for a 100 km length.
    b_over_h = reduce(lambda x, y: sin(radians(x)) + sin(radians(y)),
                      incidence_angles)
    # Get the acquisition mode.
    mode = "tristereo" if tristereo else "stereo"
    # Check if B/H is within the respective sensor bounds.
    return B_H_RANGE_SENSORS[sensor][mode]["lower"] <= b_over_h <= B_H_RANGE_SENSORS[sensor][mode]["upper"]


def select_stereo(feature_list: list[dict])-> Union[None, list[dict]]:
    """Given a list of GeoJSON simple features it returns the ones that are possibly stereo pairs.

    Parameters
    ----------
    feature_list : list[dict]
        A list of GeoJSON simple features.

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
    # that list for stereo pairs.  This works due to the ordering of
    # the search results.
    return list(filter(lambda e:
                       is_stereo_dates(
                           e[0]["properties"]["acquisitionDate"],
                           e[1]["properties"]["acquisitionDate"],
                       )
                       and
                       is_stereo_angles(
                           e[0]["properties"]["providerProperties"]["incidenceAngleAlongTrack"],
                           e[1]["properties"]["providerProperties"]["incidenceAngleAlongTrack"],
                           e[0]["properties"]["collection"],
                       ),
                       list(zip(a, b))
                       )
                )

def select_tristereo(feature_list: list[dict])-> Union[None, list[dict]]:
    """Given a list of GeoJSON simple features it returns the ones that are possibly tri-stereo triples.

    Parameters
    ----------
    feature_list : list[dict]
        A list of GeoJSON simple features.

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
    # of the triple for the dates. For the angle we look at the first
    # two, since the B/H value is adjusted for tri-stereo, This works
    # due to the ordering of the search results.
    return list(filter(lambda e:
                       is_stereo_dates(
                           e[0]["properties"]["acquisitionDate"],
                           e[2]["properties"]["acquisitionDate"],
                       )
                       and
                       is_stereo_angles(
                           e[0]["properties"]["providerProperties"]["incidenceAngleAlongTrack"],
                           e[2]["properties"]["providerProperties"]["incidenceAngleAlongTrack"],
                           e[0]["properties"]["collection"],
                           True, # is tri-stereo
                       ),
                       list(zip(a, b, c))
                       )
                )


def get_stereo_image_ids(results_list: list[tuple])-> list[str]:
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

    # Build and flatten the list using chain.from_iterable.
    return list(chain.from_iterable(map(lambda e: [e[0]["properties"]["id"],
                                                   e[1]["properties"]["id"]],
                                        results_list)))


def get_tristereo_image_ids(results_list: list[tuple])-> list[str]:
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
