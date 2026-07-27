# UnUsedOS

A Linux system analysis toolkit for identifying unused files and packages on
Supercomputing System (SCS) appliances, using filesystem access timestamps,
package usage reports, and pandas-based data analysis.

<!-- exec-summary: begin -->
UnUsedOS analyzes Linux systems to find files and packages that are never
accessed, helping reduce OS image bloat on SCS appliances. It combines shell
scripts for file usage collection, Python scripts for package usage analysis,
and Jupyter notebooks for interactive exploration — producing security patches
that remove unused components.
<!-- exec-summary: end -->

## Prerequisites

- Linux system (tested on Ubuntu Lucid/Precise/Xenial)
- Python 3 with pandas
- Standard Unix tools: `find`, `stat`, `dpkg`, `shar`, `csvkit`

## Setup

```bash
git clone https://github.com/biofool/UnUsedOS.git
cd UnUsedOS
pip install pandas
```

## Usage

### File usage report

```bash
# Generate a file access-time report for a directory tree
bash FileUsageReport.sh /path/to/analyze
```

### Package usage analysis

```bash
# Basic package usage report
python PackageUsageReport.py

# Modified report with validation
python ModifiedPackageUsageReportWithValidation.py
```

### Interactive analysis (Jupyter)

```bash
jupyter notebook UnusedFilesAndPackages.ipynb
jupyter notebook UnusedPackageReport.ipynb
jupyter notebook WhatsUnused.ipynb
```

### Security patch creation

```bash
bash CreateSecurityPatch/CreateSecurityPatchBundle.sh
bash CreateSecurityPatch/SecurityPatchInstaller.sh
```

### Stats collection

```bash
bash StatsCollector/installVMCollector.sh
bash StatsCollector/BloatedStatsCollectorInc.sh
```

## Project Structure

```
UnUsedOS/
├── UnusedFilesAndPackages.py          # Main analysis script
├── UnusedFilesAndPackages.ipynb       # Interactive notebook (v1)
├── UnusedFilesAndPackages-V2.ipynb    # Interactive notebook (v2)
├── UnusedPackageReport.py             # Package usage report
├── UnusedPackageReport.ipynb          # Package report notebook
├── WhatsUnused.ipynb                  # Survey notebook
├── WhatsUnusedSurvey.py               # Survey script
├── PackageUsageReport.py              # Basic package report
├── ModifiedPackageUsageReport.py      # Modified package report
├── ModifiedPackageUsageReportWithValidation.py  # With validation
├── access_times.py                    # Access time utilities
├── DescribeDataFrames.py              # DataFrame structure inspector
├── FileUsageReport.sh                 # File usage shell report
├── ConCSV2PSV.sh                      # CSV to PSV converter
├── MakeShar.sh                        # Create shar archive
├── AccessValidate/                    # Access validation tools
├── CreateSecurityPatch/               # Security patch creation
├── Dictionaries/                      # Data dictionaries
├── StatsCollector/                    # VM stats collection
├── bloated-scs-full_*.txt             # SCS package file lists (various versions)
└── allpackages.txt                    # All packages reference
```

## License

See repository metadata for license details.
