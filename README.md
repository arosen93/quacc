![example workflow](https://github.com/arosen93/quacc/actions/workflows/workflow.yaml/badge.svg)
[![codecov](https://codecov.io/gh/arosen93/quacc/branch/main/graph/badge.svg?token=BCKGTD89H0)](https://codecov.io/gh/arosen93/quacc)
[![CodeFactor](https://www.codefactor.io/repository/github/arosen93/quacc/badge)](https://www.codefactor.io/repository/github/arosen93/quacc)

# QuAcc (🚧 Under Construction 🚧)
The Quantum Accelerator (QuAcc) supercharges your code to support high-throughput, database-driven density functional theory (DFT). QuAcc is built with the following goals in mind:
1. Rapid workflow development and prototyping, no matter your favorite DFT package.
2. A database-oriented approach that is as easy to use for 1 calculation as it is for 10,000.
3. On-the-fly error handling and "smart" calculators.
4. All within the existing framework of the [Atomic Simulation Environment](https://wiki.fysik.dtu.dk/ase/index.html) and the corresponding `Atoms` object.
 
In practice, the goal here is to enable the development of high-throughput workflows centered around ASE with a focus on rapid workflow construction and prototyping. If your goal is to use a package that provides pre-defined recipes, [Atomate2](https://github.com/materialsproject/atomate2) is what you're looking for!
<p align="center">
<img src="https://imgs.xkcd.com/comics/standards_2x.png" alt="xkcd Comic" width="528" height="300">
<p align="center">
Credit: xkcd
</p>

## Representative Examples
### SmartVasp Calculator
For VASP, QuAcc comes pre-packaged with a `SmartVasp` calculator that can run calculations via [Custodian](https://github.com/materialsproject/custodian) for on-the-fly error handling, an optional "co-pilot" mode to ensure your input arguments don't go against what is in the [VASP manual](https://www.vasp.at/wiki/index.php/Main_page), and more.

The example below runs a Custodian-powered VASP relaxation of bulk Cu using the RPBE functional with the remaining settings taken from a [pre-defined](https://github.com/arosen93/quacc/tree/main/quacc/defaults/user_calcs/vasp) set ("preset") of ASE-style calculator input arguments.

```python
from quacc.calculators.vasp import SmartVasp
from ase.build import bulk

atoms = bulk("Cu") # example Atoms object
atoms = SmartVasp(atoms, xc='rpbe', preset="BulkRelaxSet") # set calculator
atoms.get_potential_energy() # run VASP w/ Custodian
```

### Jobflow Integration
QuAcc makes it easy to interface ASE with [Jobflow](https://github.com/materialsproject/jobflow) for the rapid construction of workflows, from simple to highly complex. All the calculation results and metadaata can be stored in a database of your choosing as well.

The above example can be made compatible with Jobflow simply by defining it in a function with a `@job` wrapper immediately preceeding it. One nuance of Jobflow is that the inputs and outputs must be JSON serializable (so that it can be easily stored in a database), but otherwise it works the same.

```python
from quacc.calculators.vasp import SmartVasp
from quacc.schemas.vasp import summarize_run
from ase.io.jsonio import decode
from jobflow import job

#-----Jobflow Function-----
@job
def run_relax(atoms_json):

    # Run VASP
    atoms = SmartVasp(decode(atoms_json), xc='rpbe', preset="BulkRelaxSet")
    atoms.get_potential_energy()
    
    # Return serialized results
    summary = summarize_run(atoms)
    return summary
```
```python
from ase.build import bulk
from ase.io.jsonio import encode
from jobflow import Flow
from jobflow.managers.local import run_locally

#-----Make and Run a Flow-----
# Constrct an Atoms object
atoms = bulk("Cu")

# Define the job
job1 = run_relax(encode(atoms))
flow = Job([job1])

# Run the flow locally
run_locally(flow, create_folders=True)
```
### Fireworks Integration
Jobflow provides an easy interface to [Fireworks](https://github.com/materialsproject/fireworks) for high-throughput job management. For additional details on how to convert a Jobflow job or flow to a Fireworks firework or workflow, refer to the [Jobflow documentation](https://materialsproject.github.io/jobflow/jobflow.managers.html#module-jobflow.managers.fireworks). 

### Coupling of Multiple Codes
QuAcc is built on top of [ASE](https://wiki.fysik.dtu.dk/ase/index.html) for calculation setup and execution, providing native support for dozens of DFT packages through a common interface. Through the use of [cclib](https://github.com/cclib/cclib) and [pymatgen](https://pymatgen.org/), there's a consistent interface in QuAcc for output parsing too.

The example below highlights how one could construct a Fireworks workflow to carry out a structure relaxation of O2 using Gaussian and then a refinement using Q-Chem. The metadata and tabulated calculation results of this workflow would be deposited in your database.
```python
from ase.calculators.gaussian import Gaussian
from ase.calculators.qchem import QChem
from quacc.schemas.cclib import summarize_run
from ase.io.jsonio import decode
from jobflow import job

# -----Jobflow Function-----
@job
def run_relax_gaussian(atoms_json):
    # Run Gaussian
    atoms = decode(atoms_json)
    atoms.calc = Gaussian(method="wB97X-D", basis="def2-TZVP", extra="opt")
    atoms.get_potential_energy()

    # Return serialized results
    summary = summarize_run(atoms)
    return summary


# -----Jobflow Function-----
@job
def run_relax_qchem(atoms_json):

    # Run Q-Chem
    atoms = decode(atoms_json)
    atoms.calc = QChem(method="wB97M-V", basis="def2-TZVPD", jobtype="opt")
    atoms.get_potential_energy()

    # Return serialized results
    summary = summarize_run(atoms)
    return summary
```
```python
from ase.build import molecule
from ase.io.jsonio import encode
from fireworks import LaunchPad
from jobflow import Flow
from jobflow.managers.local import flow_to_workflow

# -----Create a Fireworks workflow-----
# Constrct an Atoms object
atoms = molecule("O2")

# Define the flow
job1 = run_relax_gaussian(encode(atoms))
job2 = run_relax_qchem(encode(job1.output["atoms"]))
flow = Flow([job1, job2])

# Add a Firework to the launchpad
wf = flow_to_workflow(flow)
lpad = LaunchPad.auto_load()
lpad.add_wf(wf)
```
## Installation
1. Run the following command in a convenient place to install QuAcc:
```bash
git clone https://github.com/arosen93/quacc.git
cd quacc && pip install -r requirements.txt && pip install -e .
```

2. Follow the instructions in ASE's [documentation](https://wiki.fysik.dtu.dk/ase/ase/calculators/calculators.html#supported-calculators) for how to set up the ASE calculator(s) you plan to use.

3. Define the following environment variables (e.g. in your `~/.bashrc`) if you wish to use Jobflow and/or Fireworks, in addition to any that you have set in Step 2. Example `.yaml` files are provided [here](https://github.com/arosen93/quacc/tree/main/quacc/setup).

```bash
# Jobflow requirements
# (details: https://materialsproject.github.io/jobflow/jobflow.settings.html)
export JOBFLOW_CONFIG_FILE="/path/to/config/jobflow_config/jobflow.yaml"

# FireWorks requirements
# (details: https://materialsproject.github.io/fireworks)
export FW_CONFIG_FILE='/path/to/config/fw_config/FW_config.yaml'

```
## License
QuAcc is released under a [modified BSD license](https://github.com/arosen93/quacc/blob/main/LICENSE.md).
