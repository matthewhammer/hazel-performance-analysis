### Report 29's kernels, the fast path against the builds it is on (4 jobs)

Passes: calls through the evaluator's stages on the counter build and on the fast path; skipped: the passes the fast path stood in for (exact when the first column equals the other two summed). Times: ms a call, the median over jobs of each side's better round; ratio: fast over best on the same runner, the median over jobs; noise: the timing build's spread over its own two rounds.

| kernel | n | passes | fast path | skipped | exact | best (ms) | fast (ms) | ratio | per job | noise |
|---|---|---|---|---|---|---|---|---|---|---|
| count | 100 | 1409 | 907 | 502 | yes | 3.3075 | 2.9058 | 0.872 | 0.91 0.84 0.85 0.89 | 3% |
| count | 1000 | 14009 | 9007 | 5002 | yes | 39.2123 | 36.1693 | 0.921 | 0.91 0.83 0.93 0.95 | 2% |
| count | 5000 | 70009 | 45007 | 25002 | yes | 202.3481 | 188.5353 | 0.931 | 0.93 0.90 0.94 0.95 | 4% |
| fib | 10 | 2562 | 1857 | 705 | yes | 5.2359 | 4.7065 | 0.874 | 0.89 0.85 0.91 0.86 | 2% |
| fib | 13 | 10914 | 7905 | 3009 | yes | 21.5922 | 19.6967 | 0.910 | 0.91 0.91 0.91 0.89 | 2% |
| fib | 16 | 46294 | 33525 | 12769 | yes | 91.7678 | 83.2716 | 0.899 | 0.91 0.89 0.91 0.89 | 3% |
| sumbuild | 100 | 3122 | 2419 | 703 | yes | 13.7235 | 13.6805 | 1.001 | 0.99 1.00 1.00 1.01 | 2% |
| sumbuild | 1000 | 31022 | 24019 | 7003 | yes | 618.4462 | 599.9348 | 0.971 | 0.96 0.97 0.97 1.05 | 2% |
| sumbuild | 3000 | 93022 | 72019 | 21003 | yes | 5183.7596 | 5093.4259 | 0.985 | 1.00 0.93 0.97 1.05 | 1% |
| mapinc | 100 | 5132 | 4028 | 1104 | yes | 20.7618 | 18.4040 | 0.886 | 0.88 0.85 0.89 0.95 | 4% |
| mapinc | 1000 | 51032 | 40028 | 11004 | yes | 693.8670 | 681.7928 | 1.013 | 0.99 1.04 0.98 1.05 | 2% |
| mapinc | 3000 | 153032 | 120028 | 33004 | yes | 5371.4707 | 5387.9023 | 1.007 | 1.03 0.97 0.98 1.06 | 3% |
| skip | 100 | 5 | 4 | 1 | yes | 0.0912 | 0.0892 | 0.980 | 0.99 0.93 0.97 1.00 | 2% |
| skip | 1000 | 5 | 4 | 1 | yes | 0.4207 | 0.4083 | 0.968 | 0.97 0.94 1.00 0.97 | 3% |
| skip | 3000 | 5 | 4 | 1 | yes | 1.1846 | 1.1591 | 0.979 | 0.99 0.93 1.01 0.97 | 5% |
| h_id | 100 | 5 | 5 | 0 | yes | 0.0243 | 0.0268 | 1.018 | 1.48 1.02 0.97 1.01 | 27% |
| h_id | 1000 | 5 | 5 | 0 | yes | 0.0190 | 0.0192 | 1.019 | 1.01 1.04 1.03 1.00 | 3% |
| h_id | 3000 | 5 | 5 | 0 | yes | 0.0186 | 0.0184 | 1.018 | 1.00 1.05 0.96 1.04 | 17% |
| h_ref | 100 | 108 | 7 | 101 | yes | 0.1997 | 0.0348 | 0.190 | 0.13 0.22 0.16 0.23 | 2% |
| h_ref | 1000 | 1008 | 7 | 1001 | yes | 1.1490 | 0.0398 | 0.037 | 0.03 0.04 0.04 0.05 | 3% |
| h_ref | 3000 | 3008 | 7 | 3001 | yes | 3.9042 | 0.1215 | 0.029 | 0.02 0.02 0.04 0.04 | 4% |
| h_walk | 100 | 1312 | 910 | 402 | yes | 3.2277 | 2.8228 | 0.899 | 0.86 0.95 0.88 0.92 | 4% |
| h_walk | 1000 | 13012 | 9010 | 4002 | yes | 53.2542 | 52.3193 | 0.977 | 0.94 1.05 0.95 1.01 | 4% |
| h_walk | 3000 | 39012 | 27010 | 12002 | yes | 168.9438 | 162.6806 | 0.982 | 0.93 1.02 0.95 1.04 | 7% |

job-r1: r1: Model name: INTEL(R) XEON(R) PLATINUM 8573C v22.23.3

job-r2: r2: Model name: AMD EPYC 9V45 96-Core Processor v22.23.3

job-r3: r3: Model name: AMD EPYC 7763 64-Core Processor v22.23.3

job-r4: r4: Model name: AMD EPYC 7763 64-Core Processor v22.23.3
