# Module to handle JSON Lines https://jsonlines.org/. Code adapted
# from
# https://galea.medium.com/how-to-love-jsonl-using-json-line-format-in-your-workflow-b6884f65175b.
import json

from typing import Union

def dump_jsonl(data: list[Union[list, dict]],
               output_path: str,
               append: bool=False,
               ) -> None:
    """Writes a list of lists to a JSON lines file. One list per line.

    Parameters
    ----------
    data : list[Union[dict, list]]
        the list of lists or dicts
    output_path : str
        the path to the output JSON Lines file.
    append : bool
        Open the file in append (True) or write mode (False).

    Examples
    --------
    dump_jsonl([["123", "foobar", "quux-345"]], "my_outfile.jsonl")
    dump_jsonl([["789", "foo2000", "asd1"],
                ["a", "b", "c"]],
               "my_outfile.jsonl",
               append=True)

    """

    # Choose the file writing mode.
    mode = "a+" if append else "w"
    with open(output_path, mode, encoding="utf-8") as f:
        for line in data:
            # Each list element is a line in the JSON Lines file.
            f.write(json.dumps(line, ensure_ascii=False) + "\n")

    print(f"Wrote {len(data)} records to {output_path}.")


def load_jsonl(input_path: str) -> list[list]:
    """Reads a list of JSON objects presented in a JSON lines file.

    Parameters
    ----------
    input_path : str
        path to JSON lines file

    Returns
    -------
    list[list]
        A deserialized list of JSON arrays, i.e., a list of lists.

    Examples
    --------
    load_jsonl("my_file.jsonl")

    """

    data = []
    with open(input_path, "r", encoding="utf-8") as f:
        # Loop over the lines of the JSON lines file.
        # Each line is a JSON document.
        for line in f:
            # Append to the list of deserialized JSON objects (dict).
            data.append(json.loads(line.rstrip("\n|\r")))
            print(f"Loaded {len(data)} records from {input_path}.")

    # Return the list of dicts (JSON line).
    return data
