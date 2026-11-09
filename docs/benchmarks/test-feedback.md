# Test feedback benchmarks

Measurements behind the test feedback budget in TASK-1. The budget is a warm
median of 2 seconds or less for a complete run in the default generated project.

## Why the budget is a median, not a CI assertion

The budget exists to keep feedback inside an agent's edit loop. It is a local
property of one project on one machine, so it is measured here and recorded, not
enforced in CI. A CI wall-clock assertion would fail on slower runners and teach
people to loosen the threshold instead of noticing a regression.

Cold starts and dependency installation are measured separately. They happen
once per environment, and mixing them into the edit loop number would hide the
cost that matters.

## Reference machine

| Property | Value |
| --- | --- |
| CPU | AMD Ryzen 9 5950X 16-Core |
| Logical CPUs | 32 |
| Kernel | 7.1.1-76070101-generic |
| Python | 3.12.10 (mise) |
| uv | 0.13.1 |
| prek | 0.5.7 |
| Poetry | 2.5.1 |
| Copier | 9.18.2 |

## Method

1. Render a project from the template with `installer=uv` and the default
   answers.
2. `git init`, then `mise run lock` and `mise run sync`, so the environment is
   warm and the lock and sync digests are recorded.
3. Run `mise run test` once and discard it, to load the interpreter and page
   cache.
4. Time 20 further runs of `mise run test`. Report the median, the 95th
   percentile, and the maximum.

Each sample covers the whole public path: `mise` task dispatch, `prek exec`, the
Python runner, the environment readiness check, and one pytest process that runs
the complete suite.

## Results

Current code, host, uv (20 runs):

| Statistic | Value |
| --- | --- |
| Median | 0.408 s |
| p95 | 0.431 s |
| Max | 0.432 s |
| Min | 0.399 s |

Earlier series, recorded during development:

| Environment | Runs | Median | p95 | Max |
| --- | --- | --- | --- | --- |
| Host (uv), before review fixes | 20 | 0.432 s | 0.504 s | 1.316 s |
| Debian 13 VM (uv) | 10 | 0.269 s | — | 0.294 s |

The first sample of the pre-review series was a cold outlier at 1.316 s;
samples 2 to 20 fell between 0.422 s and 0.504 s. The current series is tighter
because the environment was fully warm before timing began.

The virtual machine was Debian 13 (trixie), kernel 6.12, 4 vCPUs, with the
system Python 3.12.16, uv 0.13.7, prek 0.5.10, and mise 2026.11.3.

## Suite size

The generated project ships 3 tests. That is deliberate: the template is a
starting point, and the feedback path is what is being measured. A real project
with thousands of tests will exceed this budget, which is why the budget is
recorded rather than enforced.

## What is not covered

- Focused selection. It is not implemented; the complete suite already fits the
  budget for the generated project, so a selector would add risk without
  measurable benefit.
- Watch mode. It is a human terminal feature and is not part of the agent loop.
- Network-bound test suites. Their duration is not a property of this harness.
