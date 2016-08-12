# ABE in Health Care

Master: [![Build Status](https://travis-ci.com/denniss17/abe-healthcare.svg?token=yNBTTxeeyDjVthn2bzgm&branch=master)](https://travis-ci.com/denniss17/abe-healthcare)
Develop: [![Build Status](https://travis-ci.com/denniss17/abe-healthcare.svg?token=yNBTTxeeyDjVthn2bzgm&branch=develop)](https://travis-ci.com/denniss17/abe-healthcare)

![Overview](detailed-use-case.png)

## Requirements

- Charm ([link](http://charm-crypto.com/))

Download charm from [here](https://github.com/denniss17/charm). Charm has its own requirements, see their website
for more info.

## Installation and tests

- See `.travis.yml` for up to date details of how to install and execute tests.

## Experiments

The different experiments can be found in `experiments`. All experiments should extend the `BaseExperiment`, and 
should define one or more cases of type `ExperimentCase`. 

The `ExperimentRunner` in `experiments.py` runs all experiments for all implementations for each case.

### Execution

Run `experiments.py` to run all experiments

### Output

The output of the experiments can be found in `data/experiments/output/{experiment_name}/{implementation}`.
For each case, several files are created.

#### CPU
Percentage of CPU during entire experiment

#### Timings
The `.txt` file is the result of a dump of [pstats.Stats](https://docs.python.org/3.5/library/profile.html#pstats.Stats). 
The `.csv` file is this result converted to CSV.

#### Memory

res is what is used, in total
data is what is available for data only

See [psutil.Process.memory_info](https://pythonhosted.org/psutil/#psutil.Process.memory_info).

- rss: aka “Resident Set Size”, this is the non-swapped physical memory a process has used. 
  On UNIX it matches “top“‘s RES column (see doc). On Windows this is an alias for wset field and it 
  matches “Mem Usage” column of taskmgr.exe.
- vms: aka “Virtual Memory Size”, this is the total amount of virtual memory used by the process. 
  On UNIX it matches “top“‘s VIRT column (see doc). On Windows this is an alias for pagefile field and it matches
  “Mem Usage” “VM Size” column of taskmgr.exe.
- shared: (Linux) memory that could be potentially shared with other processes. This matches “top“‘s SHR column (see doc).
- text (Linux, BSD): aka TRS (text resident set) the amount of memory devoted to executable code. 
  This matches “top“‘s CODE column (see doc).
- data (Linux, BSD): aka DRS (data resident set) the amount of physical memory devoted to other than executable code. 
  It matches “top“‘s DATA column (see doc).
- lib (Linux): the memory used by shared libraries.
- dirty (Linux): the number of dirty pages.

Relevant link: [What is the simplest and most accurate way to measure the memory used by a program in a programming contest environment?](https://www.quora.com/What-is-the-simplest-and-most-accurate-way-to-measure-the-memory-used-by-a-program-in-a-programming-contest-environment)

[source](http://mugurel.sumanariu.ro/linux/the-difference-among-virt-res-and-shr-in-top-output/):

VIRT stands for the virtual size of a process, which is the sum of memory it is actually using, 
memory it has mapped into itself (for instance the video card’s RAM for the X server), 
files on disk that have been mapped into it (most notably shared libraries), 
and memory shared with other processes. VIRT represents 
how much memory the program is able to access at the present moment.

RES stands for the resident size, which is an accurate representation of how much actual physical memory 
a process is consuming. (This also corresponds directly to the %MEM column.) This will virtually always be less than 
the VIRT size, since most programs depend on the C library.

SHR indicates how much of the VIRT size is actually sharable (memory or libraries). In the case of libraries, it does 
not necessarily mean that the entire library is resident. For example, if a program only uses a few functions in a 
library, the whole library is mapped and will be counted in VIRT and SHR, but only the parts of the library file 
containing the functions being used will actually be loaded in and be counted under RES.

