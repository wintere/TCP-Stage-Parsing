# An EEBO-TCP Metadata Parser
This pipeline processes headers from the EEBO-TCP in order to extract key identifiers like ESTC, STC, and Wing and indicators that work is a play or collection of plays. This is not meant to replace the official TCP metdata, official EEBO metadata, or the more thorough information in catalogues like the ESTC.

## First Run: Create the **xml-processing** Conda Environment 

The first time you run this script, you will need to create a [conda](https://docs.conda.io/projects/conda/en/stable/user-guide/tasks/manage-environments.html) environment.

This stage requires a miniconda/Anaconda installation. 

```bash
conda env create -f environment.yml
```

If this statement fails, then Python3 and conda are *not* on your path. 

Here is a set of instructions for [installing Python3 through Anaconda](https://researchguides.uoregon.edu/library_workshops/install_anaconda).

## Usage: 

Activate the conda environment with the project dependencies.

```python
conda activate xml-processing
```

As a reasonable default configuration, I recommend the following.
* Use the `-o` argument to indicate an output filepath. Use the `.csv` extension. This will output in a `utf-8` encoding. 
* Use the `-f` argument *last* followed by a list of paths to folders containing TCP XML files.

```python
python batch-process.py -o outfile.csv -f EEBO-TCP/EEBO1/P4_XML_TCP/ 
```

### Notes
* EEBO, ECCO, and Evans each encode identifier information in a slightly different way.
* As Evans does not have XML files of interest, this parser doesn't perform well on Evans.
* `xpath` is suboptimal in performance to compared to lxml's `find`. 