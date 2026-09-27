# C006b feasibility gate (before registration)

C006 failed because nobody counted whether HDFS blocks repeat in the 2k sample. This gate is run first,
from structure only (key recurrence, how guessable each answer is). Output: `output_x86_64.txt`.

Result: **OpenSSH fails** every C006 template. It has only one component (`first component` guess
1.000), and the last event is 0.831 guessable by always naming the most common one. **HPC keyed by
Node** passes `last event` and `first event`; `first component` fails (shuffle keeps it 0.605).
Hadoop, Android and Zookeeper fail.

Structured-CSV SHA-256 at the time of the check: HPC `0787df9cfab7e9495669548315ea8a9a51b02029c0dcfa28944707ad755a8c86`,
OpenSSH `c0996a11545f4b94b435993760afa441a9e373f7bfc9e787afdb8e62f65acb4f`.
The full HDFS log (Zenodo HDFS_v1, about 1.5 GB) was reachable (HTTP 200) and not checked.
