import os
from copy import deepcopy
from shutil import copy, rmtree
from tempfile import mkdtemp

from ase.atoms import Atoms
from monty.shutil import copy_r, gzip_dir


def run_calc(
    atoms: Atoms,
    store_dir: str = None,
    scratch_dir: str = None,
    gzip: bool = True,
    copy_from_store_dir: bool = False,
) -> float:
    """
    Run a calculation in a scratch directory and copy the results back to the
    original directory. This can be useful if file I/O is slow in the working
    directory, so long as file transfer speeds are reasonable.

    This is a wrapper around atoms.get_potential_energy().

    Parameters
    ----------
    atoms : .Atoms
        The Atoms object to run the calculation on.
    store_dir : str
        Path where calculation results should be stored.
        If None, the current working directory will be used.
    scratch_dir : str
        Path to the base directory where a tmp directory will be made for
        scratch files. If None, a temporary directory in $SCRATCH will be used.
        If $SCRATCH is not present, a tmp directory will be made in store_dir.
    gzip : bool
        Whether to gzip the output files.
    copy_from_store_dir : bool
        Whether to copy any pre-existing files from the store_dir to the scratch_dir
        before running the calculation.

    Returns
    -------
    .Atoms
        The updated .Atoms object,
    """

    atoms = deepcopy(atoms)
    if atoms.calc is None:
        raise ValueError("Atoms object must have attached calculator.")

    # Find the relevant paths
    if not store_dir:
        store_dir = os.getcwd()
    if not scratch_dir:
        if "SCRATCH" in os.environ:
            scratch_dir = os.path.expandvars("$SCRATCH")
        else:
            scratch_dir = store_dir
    if not os.path.exists(scratch_dir):
        raise OSError(f"Cannot find {scratch_dir}")

    tmp_path = mkdtemp(dir=scratch_dir, prefix="quacc-")

    # Copy files to scratch
    if copy_from_store_dir:
        for f in os.listdir(store_dir):
            if os.path.isfile(os.path.join(store_dir, f)):
                copy(os.path.join(store_dir, f), os.path.join(tmp_path, f))

    # Make a symlink to the scratch dir
    sym_path = os.path.join(store_dir, "scratch_symlink")
    if os.name != "nt":
        os.symlink(tmp_path, sym_path)

    # Run calculation via get_potential_energy()
    atoms.calc.directory = tmp_path
    atoms.get_potential_energy()

    # gzip files and recursively copy files back to store_dir
    if gzip:
        gzip_dir(tmp_path)
    copy_r(tmp_path, store_dir)

    # Remove the tmp dir and symlink
    if os.path.exists(sym_path):
        os.remove(sym_path)
    if os.path.exists(tmp_path):
        rmtree(tmp_path)

    return atoms
