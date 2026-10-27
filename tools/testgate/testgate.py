#!/usr/bin/env python3
"""Run RHH's battle tests and fail only on failures that aren't in the known-failures baseline.

At HnS 2.0.6 about 1,900 of 5,100 tests fail, 90% of them because HnS prints classic battle text
where RHH's tests expect Gen 5+ lines (BACKLOG TS-01). So the tests run with their MESSAGE()
expectations dropped (TEST_SKIP_MESSAGES=1), and what still fails is listed, with its reason, in
baseline.txt. A failure that isn't listed there is a regression: exit 1.

    tools/testgate/testgate.py                    # full run, compare
    tools/testgate/testgate.py --tests "Court Change"
    tools/testgate/testgate.py --update           # after fixing a test, or with a reason in the commit
    tools/testgate/testgate.py --strict           # with MESSAGE() checks, report only

Needs arm-none-eabi on PATH. On macOS, coreutils' stdbuf (brew install coreutils) is found
without putting its gnubin on PATH.
"""
import argparse
import collections
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BASELINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "baseline.txt")
BAD = {"FAIL", "INVALID", "CRASH", "TIMEOUT", "EXPECTED_FAIL_PASSING"}
RESULT = re.compile(r"^\[\d+\] (.*): (PASS|FAIL|INVALID|CRASH|TIMEOUT|ASSUMPTION_FAIL|TO_DO|KNOWN_FAILING"
                    r"|EXPECTED_FAIL|KNOWN_FAILING_PASSING|EXPECTED_FAIL_PASSING)$")
REASON = re.compile(r"^  (test/\S+:\d+: .*)$")
ANSI = re.compile(r"\x1b\[[0-9;]*m")


def run(args, log_path):
    env = dict(os.environ)
    if not shutil.which("stdbuf", path=env.get("PATH")):
        brew = shutil.which("brew")
        if brew:
            prefix = subprocess.run([brew, "--prefix"], capture_output=True, text=True).stdout.strip()
            gnubin = os.path.join(prefix, "opt", "coreutils", "libexec", "gnubin")
            if os.path.exists(os.path.join(gnubin, "stdbuf")):
                env["PATH"] = gnubin + os.pathsep + env["PATH"]
    if not shutil.which("stdbuf", path=env["PATH"]):
        sys.exit("testgate: no stdbuf on PATH; on macOS run `brew install coreutils`")
    if not shutil.which("arm-none-eabi-gcc", path=env["PATH"]):
        sys.exit("testgate: no arm-none-eabi-gcc on PATH (CLAUDE.md section 1)")
    cmd = ["make", "check", "BUILD=hns", f"-j{args.jobs}", f"TEST_SKIP_MESSAGES={0 if args.strict else 1}"]
    if args.tests:
        cmd.append(f"TESTS={args.tests}")
    print("testgate:", " ".join(cmd), file=sys.stderr)
    with open(log_path, "w", errors="replace") as log:
        proc = subprocess.run(cmd, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
    return proc.returncode


def parse(log_path):
    """{(name, result): count} and {name: reason} from a make check log."""
    results, reasons = collections.Counter(), {}
    last = None
    for line in open(log_path, errors="replace"):
        line = ANSI.sub("", line.rstrip("\n"))
        m = RESULT.match(line)
        if m:
            last = m.group(1)
            results[(m.group(1), m.group(2))] += 1
            continue
        m = REASON.match(line)
        if m and last:
            reasons.setdefault(last, m.group(1))
    return results, reasons


def read_baseline():
    known = collections.Counter()
    if os.path.exists(BASELINE):
        for line in open(BASELINE):
            if line.strip() and not line.startswith("#"):
                result, name = line.rstrip("\n").split("\t")[:2]
                known[(name, result)] += 1
    return known


def write_baseline(results, reasons):
    with open(BASELINE, "w") as f:
        f.write("# Known failures of `make check BUILD=hns TEST_SKIP_MESSAGES=1`: RESULT<TAB>test<TAB>reason.\n"
                "# Written by tools/testgate/testgate.py --update. Remove a line when its test passes.\n")
        for (name, result), count in sorted(results.items(), key=lambda kv: (kv[0][0], kv[0][1])):
            if result in BAD:
                for _ in range(count):
                    f.write(f"{result}\t{name}\t{reasons.get(name, '')}\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tests", help="only tests whose name starts with this (make check TESTS=)")
    ap.add_argument("--update", action="store_true", help="rewrite baseline.txt from this run")
    ap.add_argument("--strict", action="store_true", help="keep MESSAGE() checks; report, don't gate")
    ap.add_argument("--log", help="parse this existing log instead of running the tests")
    ap.add_argument("-j", "--jobs", type=int, default=os.cpu_count() or 4)
    args = ap.parse_args()

    log_path = args.log or os.path.join(ROOT, "build", "testgate.log")
    if not args.log:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        run(args, log_path)
    results, reasons = parse(log_path)
    if not results:
        sys.exit(f"testgate: no test results in {log_path}; the build may have failed")

    tally = collections.Counter()
    for (_, result), count in results.items():
        tally[result] += count
    print("testgate:", ", ".join(f"{k} {v}" for k, v in tally.most_common()), f"(log: {log_path})")
    if args.strict:
        return 0
    if args.update:
        if args.tests:
            sys.exit("testgate: --update needs a full run, not --tests")
        write_baseline(results, reasons)
        print(f"testgate: wrote {sum(c for (n, r), c in results.items() if r in BAD)} known failures to {BASELINE}")
        return 0

    known = read_baseline()
    ran = {name for name, _ in results}
    bad_now = collections.Counter({k: c for k, c in results.items() if k[1] in BAD})
    known_ran = collections.Counter({k: c for k, c in known.items() if k[0] in ran})
    new = bad_now - known_ran
    fixed = known_ran - bad_now
    for (name, result), _ in sorted(fixed.items()):
        print(f"  now passing, take it out of the baseline: {name}")
    for (name, result), _ in sorted(new.items()):
        print(f"  NEW {result}: {name}\n      {reasons.get(name, '(no reason printed)')}")
    if new:
        print(f"testgate: {sum(new.values())} new failure(s)")
        return 1
    print("testgate: no new failures")
    return 0


if __name__ == "__main__":
    sys.exit(main())
