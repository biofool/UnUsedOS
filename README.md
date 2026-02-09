The Project’s Core Objective
The primary goal was to identify which files and or packages had files that are not needed most of the time.
Ask the file system

Data Collection
The project started with gathering two sets of data:
1.	A comprehensive list of all files on the system, detailing their paths, creation, and access times.
2.	A corresponding list mapping files to the packages they belong to.
Data Processing: GPT Chose pandas
Utilizing Python’s pandas library, the data sets were merged based on file paths. This step was crucial in aligning each file with its package, correlating access times in the process.
Analysis: Identifying Least Accessed Packages
The merged data was then grouped by package names, and for each package, the oldest access time of its files was determined. This provided a clear picture of which packages were least interacted with, indicating potential areas for security review.
Reporting: Focused on Security Implications
The final report listed packages sorted by the oldest access time of their files. This prioritization assists security practitioners in identifying packages that might require updates, patches, or even removal to maintain system integrity.
Why This Matters for Security Practitioners
•	Attack Surface Optimization: Removing or updating rarely used packages can reduce the system’s attack surface.
•	Proactive Maintenance: Regular analysis of file access patterns enables a proactive approach to system security, allowing for timely interventions.
Other approaches evaluated
SELinux, auditd, eBPF and AppArmour:
All of these systems perform real-time reporting and would create performance impacts as well as requiring substantial engineering to be sure to detect “all file utilization”.
![image](https://github.com/vigilent/Security/assets/1031599/06ece6b1-f041-4dbc-92ef-8f9da6833e15)
