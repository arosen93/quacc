from atomate2.common.schemas.structure import StructureMetadata
from pymatgen.io.ase import AseAtomsAdaptor
from ase.io.jsonio import encode
from monty.json import jsanitize


def atoms_to_db(atoms, get_metadata=True, **metadata_kwargs):

    """
    Convert an ASE Atoms object to a dict suitable for storage in MongoDB.

    Args:
        atoms (ase.Atoms): ASE Atoms object to store in {"atoms": atoms}.
        get_metadata (bool): Whether to store atoms metadata in the returned dict.
            Defaults to True.
        metadata_kwargs: Keyword arguments to pass to StructureMetadata().from_structure()

    Returns:
        Dict: dictionary of tabulated atoms object data

    """

    results = {}

    # Get Atoms metadata, if requested
    if get_metadata:
        struct = AseAtomsAdaptor().get_structure(atoms)
        struct_metadata = (
            StructureMetadata().from_structure(struct, **metadata_kwargs).dict()
        )
    else:
        struct_metadata = {}

    # Store the info flags separately for easy querying
    results["atoms_info"] = {}
    for key, val in atoms.info.items():
        # We use jsanitize to make sure all data is stored in
        # a JSON-friendly formaat (or converted to a string if not).
        results["atoms_info"][key] = jsanitize(val)

    # Store the encoded Atoms object
    results["atoms"] = encode(atoms)

    # Combine the metadata and results dictionaries
    results_full = {**struct_metadata, **results}

    return results_full
