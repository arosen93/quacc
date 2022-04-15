import os

import pytest
from ase.build import bulk, molecule
from jobflow.managers.local import run_locally

try:
    from tblite.ase import TBLite
except (ModuleNotFoundError, ImportError):
    tblite = None
from quacc.recipes.xtb.core import RelaxJob, StaticJob


def teardown_module():
    for f in os.listdir("."):
        if f.endswith(".log") or f.endswith(".pckl") or f.endswith(".traj"):
            os.remove(f)


@pytest.mark.skipif(
    tblite is None,
    reason="tblite must be installed. Try conda install -c conda-forge tblite",
)
def test_static_Job():

    atoms = molecule("H2O")
    job = StaticJob().make(atoms)
    responses = run_locally(job, ensure_success=True)
    output = responses[job.uuid][1].output
    assert output["spin_multiplicity"] == 1
    assert output["nsites"] == len(atoms)
    assert output["parameters"]["method"] == "GFN2-xTB"
    assert output["name"] == "xTB-Static"
    assert output["results"]["energy"] == pytest.approx(-137.96777587302995)

    job = StaticJob(method="GFN1-xTB").make(atoms)
    responses = run_locally(job, ensure_success=True)
    output = responses[job.uuid][1].output
    assert output["parameters"]["method"] == "GFN1-xTB"
    assert output["results"]["energy"] == pytest.approx(-156.96750578831137)

    atoms = bulk("Cu")
    job = StaticJob(method="GFN1-xTB").make(atoms)
    responses = run_locally(job, ensure_success=True)
    output = responses[job.uuid][1].output
    assert output["results"]["energy"] == pytest.approx(-119.77643232313169)


@pytest.mark.skipif(
    tblite is None,
    reason="tblite must be installed. Try conda install -c conda-forge tblite",
)
def test_relax_Job():
    atoms = molecule("H2O")
    job = RelaxJob().make(atoms)
    responses = run_locally(job, ensure_success=True)
    output = responses[job.uuid][1].output
    assert output["spin_multiplicity"] == 1
    assert output["nsites"] == len(atoms)
    assert output["parameters"]["method"] == "GFN2-xTB"
    assert output["name"] == "xTB-Relax"
    assert output["results"]["energy"] == pytest.approx(-137.9764670127011)

    job = RelaxJob(method="GFN1-xTB").make(atoms)
    responses = run_locally(job, ensure_success=True)
    output = responses[job.uuid][1].output
    assert output["parameters"]["method"] == "GFN1-xTB"
    assert output["results"]["energy"] == pytest.approx(-156.9763496338962)

    atoms = bulk("Cu")
    job = RelaxJob(method="GFN1-xTB").make(atoms)
    responses = run_locally(job, ensure_success=True)
    output = responses[job.uuid][1].output
    assert output["results"]["energy"] == pytest.approx(-119.77643232313169)