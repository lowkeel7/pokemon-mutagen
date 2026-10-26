#include "global.h"
#include "test_runner.h"

__attribute__((weak))
const bool8 gTestRunnerEnabled = FALSE;

// The Makefile patches gTestRunnerHeadless as part of make test.
// This allows us to open the ROM in an mgba with a UI and see the
// animations and messages play, which helps when debugging a test.
#if TESTING
const bool8 gTestRunnerHeadless = FALSE;
#endif
const bool8 gTestRunnerSkipIsFail = FALSE;
#if TESTING
// `make check TEST_SKIP_MESSAGES=1` patches this: MESSAGE() expectations are dropped, because
// HnS prints classic battle text where RHH's tests expect Gen 5+ lines (BACKLOG TS-01).
const bool8 gTestRunnerSkipMessages = FALSE;
#endif
