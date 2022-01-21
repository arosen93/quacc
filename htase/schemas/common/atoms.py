from atomate2.common.schemas.structure import StructureMetadata
from atomate2.common.schemas.molecule import MoleculeMetadata
from pymatgen.io.ase import AseAtomsAdaptor
from ase.io.jsonio import encode
from monty.json import jsanitize
import numpy as np
from copy import deepcopy
import hashlib


def atoms_to_db(atoms, get_metadata=True, strip_info=False):

    """
    Convert an ASE Atoms object to a dict suitable for storage in MongoDB.

    Args:
        atoms (ase.Atoms): ASE Atoms object to store in {"atoms": atoms}.
        get_metadata (bool): Whether to store atoms metadata in the returned dict.
            Defaults to True.
        strip_info (bool): Whether to strip the data from atoms.info in the returned {"atoms":atoms}.
        Note that this data will be stored in {"atoms_info":atoms.info} regardless.
            Defaults to False.

    Returns:
        Dict: dictionary of tabulated atoms object data

    """

    atoms = deepcopy(atoms)
    atoms_no_info = deepcopy(atoms)
    atoms_no_info.info = {}
    results = {}

    # Get Atoms metadata, if requested. Atomate2 already has built-in tools for
    # generating pymatgen Structure/Molecule metadata, so we'll just use that.
    if get_metadata:
        if np.all(atoms.pbc == False):
            mol = AseAtomsAdaptor().get_molecule(atoms)
            metadata = MoleculeMetadata().from_molecule(mol).dict()
        else:
            struct = AseAtomsAdaptor().get_structure(atoms)
            metadata = StructureMetadata().from_structure(struct).dict()
    else:
        metadata = {}

    # Give the Atoms object a unique ID. This will be helpful for querying later.
    # Also store any old IDs somewhere else for future reference.
    if atoms.info.get("_id", None) is not None:
        if atoms.info.get("_old_ids") is None:
            atoms.info["_old_ids"] = []
        atoms.info["_old_ids"].append(atoms.info["_id"])
    atoms.info["_id"] = hashlib.md5(encode(atoms_no_info).encode("utf-8")).hexdigest()

    # Copy the info flags as a separate entry in the DB for easy querying
    results["atoms_info"] = {}
    for key, val in atoms.info.items():
        # We use jsanitize to make sure all data is stored in
        # a JSON-friendly formaat (or converted to a string if not).
        results["atoms_info"][key] = jsanitize(val)

    # Store the encoded Atoms object
    if strip_info:
        results["atoms"] = encode(atoms_no_info)
    else:
        results["atoms"] = encode(atoms)

    # Combine the metadata and results dictionaries
    results_full = {**metadata, **results}

    return results_full
