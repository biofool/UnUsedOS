# Technical Marketing Summary — UnUsedOS

> **One-line positioning:** A Linux system analysis toolkit that identifies
> unused files and packages on SCS appliances using filesystem access
> timestamps and package usage data, then produces security patches to
> safely remove bloat.

## Target Users / Personas

| Persona | Description | Primary Need |
|---------|-------------|--------------|
| **System engineer** | Maintains SCS (Supercomputing System) appliance OS images | Identify and remove unused files/packages to reduce image size |
| **Security engineer** | Hardens OS images by removing attack surface | Generate security patches that strip unused components |
| **DevOps / platform owner** | Manages VM templates and appliance builds | Data-driven analysis of what's actually used vs installed |

## Key Features & Capabilities

*(Grounded in the Python scripts, shell scripts, notebooks, and data files.)*

- **File usage analysis** — `FileUsageReport.sh` and `access_times.py`
  collect filesystem access timestamps (`atime`) to identify files that are
  never accessed.
- **Package usage reports** — `PackageUsageReport.py`,
  `ModifiedPackageUsageReport.py`, and
  `ModifiedPackageUsageReportWithValidation.py` cross-reference installed
  packages with file access data to find packages whose files are never used.
- **Interactive notebooks** — `UnusedFilesAndPackages.ipynb` (v1 + v2),
  `UnusedPackageReport.ipynb`, and `WhatsUnused.ipynb` provide pandas-based
  interactive exploration of usage data.
- **Security patch creation** — `CreateSecurityPatch/` bundles unused
  components into a removable patch with an installer script.
- **Stats collection** — `StatsCollector/` installs VM collectors and
  gathers bloated-file usage statistics over time.
- **SCS version coverage** — `bloated-scs-full_*.txt` files cover SCS
  appliance versions from 4.2.0 through 7.11.6 (Lucid, Precise, Xenial).
- **DataFrame inspection** — `DescribeDataFrames.py` prints the structure
  of pandas DataFrames as JSON for debugging.

## Technical Differentiators

| Differentiator | Detail |
|----------------|--------|
| **Access-time-based detection** | Uses filesystem `atime` to determine actual usage — more accurate than package metadata alone. |
| **Validation layer** | `ModifiedPackageUsageReportWithValidation.py` adds validation to reduce false positives. |
| **Security patch pipeline** | Not just analysis — produces installable patches (`CreateSecurityPatchBundle.sh` + `SecurityPatchInstaller.sh`). |
| **Multi-version SCS support** | Package file lists span dozens of SCS versions (4.x through 7.x) across Ubuntu Lucid/Precise/Xenial. |
| **Mixed tooling** | Combines shell scripts (fast collection), Python (analysis), and Jupyter (exploration) — right tool for each stage. |

## Technology Stack

- **Language**: Python 3, Bash shell
- **Data analysis**: pandas, Jupyter Notebook
- **System tools**: `find`, `stat`, `dpkg`, `shar`
- **Data format**: CSV, PSV (pipe-separated)
- **Target OS**: Ubuntu (Lucid, Precise, Xenial) on SCS appliances

## Use Cases / Scenarios

1. **Image size reduction** — Analyze an SCS appliance image, identify
   packages whose files have never been accessed, and generate a patch to
   remove them, reducing image size and attack surface.
2. **Security hardening** — Before shipping an appliance, run the analysis
   to find unused packages that could contain vulnerabilities, then strip
   them via the security patch pipeline.
3. **Longitudinal usage tracking** — Deploy `StatsCollector` on VMs to
   gather file access data over time, then analyze trends to identify
   candidates for removal.
4. **Interactive exploration** — Open the Jupyter notebooks to interactively
   explore which packages are used vs unused, filtering and visualizing with
   pandas.

## Benefits / Value Proposition

- **Smaller images** — Removing unused packages reduces OS image size,
  speeding up deployment and reducing storage costs.
- **Reduced attack surface** — Unused packages often contain vulnerabilities;
  removing them hardens the system.
- **Data-driven decisions** — Access-time analysis provides evidence of what
  is actually used, not just what is installed.
- **Actionable output** — Produces installable security patches, not just
  reports.
- **Multi-version support** — Covers a wide range of SCS appliance versions.

## Known Limitations (evidenced in the repo)

- Requires `atime` to be enabled on the filesystem (often disabled by default
  with `noatime` mount option for performance).
- SCS-specific — the package file lists are for Supercomputing System
  appliances, not general-purpose Linux.
- Large number of `bloated-scs-full_*.txt` data files for many versions
  increases repo size.
- No automated CI — analysis is run manually or via notebooks.
