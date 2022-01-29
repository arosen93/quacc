from ase.io.jsonio import encode, decode
from quacc.calculators.vasp import SmartVasp
from quacc.schemas.vasp import summarize_run
from quacc.util.slabs import make_max_slabs_from_bulk, make_adsorbate_structures
from jobflow import job, Flow, Response

NCORE = 4
KPAR = 4


@job
def run_relax_job(atoms_json, slab=True):
    atoms = decode(atoms_json)

    if slab:
        updates = {"ncore": NCORE, "kpar": KPAR}
    else:
        updates = {
            "isif": 3,
            "auto_dipole": False,
            "auto_kpts": {"length_density": [50, 50, 50]},
            "ncore": NCORE,
            "kpar": KPAR * 4,
        }
    atoms = SmartVasp(atoms, preset="SlabRelaxSet", **updates)

    atoms.get_potential_energy()
    summary = summarize_run(atoms)

    return summary


@job
def run_static_job(atoms_json, slab=True):
    atoms = decode(atoms_json)

    if slab:
        updates = {"ncore": NCORE, "kpar": KPAR, "lvhar": True}
    else:
        updates = {
            "auto_dipole": False,
            "auto_kpts": {"length_density": [50, 50, 50]},
            "ncore": NCORE,
            "kpar": KPAR * 4,
        }
    atoms = SmartVasp(
        atoms,
        preset="SlabRelaxSet",
        nsw=0,
        ismear=-5,
        isym=2,
        nedos=5000,
        lwave=True,
        lcharg=True,
        laechg=True,
        **updates
    )
    atoms.get_potential_energy()
    summary = summarize_run(atoms)

    return summary


@job
def bulk_to_slab_job(atoms_json, max_slabs=None, **slab_kwargs):
    atoms = decode(atoms_json)

    slabs = make_max_slabs_from_bulk(atoms, max_slabs=max_slabs, **slab_kwargs)
    jobs = []
    outputs = []
    for slab in slabs:
        relax_job = run_relax_job(encode(slab))
        jobs.append(relax_job)
        outputs.append(relax_job.output)

        static_job = run_static_job(relax_job.output["atoms"])
        jobs.append(static_job)
        outputs.append(static_job.output)

    return Response(replace=Flow(jobs))


@job
def slab_to_ads_slab_job(atoms_json, adsorbate_json, **slab_ads_kwargs):
    atoms = decode(atoms_json)
    adsorbate = decode(adsorbate_json)

    slabs = make_adsorbate_structures(atoms, adsorbate, **slab_ads_kwargs)
    if slabs is None:
        return None

    jobs = []
    outputs = []
    for slab in slabs:
        relax_job = run_relax_job(encode(slab))
        jobs.append(relax_job)
        outputs.append(relax_job.output)

        static_job = run_static_job(relax_job.output["atoms"])
        jobs.append(static_job)
        outputs.append(static_job.output)

    return Response(replace=Flow(jobs))