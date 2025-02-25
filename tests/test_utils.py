import platform
import sys

import pytest
from freezegun import freeze_time

from aocd.exceptions import DeadTokenError
from aocd.utils import atomic_write_file
from aocd.utils import blocker
from aocd.utils import different_rate
from aocd.utils import get_owner


cpython = platform.python_implementation() == "CPython"
winblows = sys.platform == "win32"
py27 = sys.version_info[:2] == (2, 7)
py27_on_windows = py27 and winblows
# see https://github.com/spulec/freezegun/issues/253


@pytest.mark.xfail(py27_on_windows, reason="freezegun tick is not working on py2.7 windows")
@pytest.mark.xfail(not cpython, reason="freezegun tick is not working on pypy")
def test_blocker(capsys):
    with freeze_time("2020-11-30 23:59:59.8-05:00", tick=True):
        # 0.2 second before unlock day 1
        blocker(dt=0.2)
    out, err = capsys.readouterr()
    assert " Unlock day 1 at " in out


def test_blocker_quiet(capsys):
    with freeze_time("2020-11-30 23:59:59.8-05:00", auto_tick_seconds=1):
        blocker(dt=0.2, quiet=True)
    out, err = capsys.readouterr()
    assert not out


def test_get_owner_not_logged_in(requests_mock):
    requests_mock.get("https://adventofcode.com/settings", status_code=302)
    with pytest.raises(DeadTokenError):
        get_owner("not_logged_in")


def test_get_owner_user_id(requests_mock):
    requests_mock.get(
        "https://adventofcode.com/settings",
        text="<span>Link to wtf</span><code>ownerproof-123-456-9c3a0172</code>",
    )
    owner = get_owner("...")
    assert owner == "unknown.unknown.123"


def test_get_owner_and_username(requests_mock):
    requests_mock.get(
        "https://adventofcode.com/settings",
        text="<span>Link to https://www.reddit.com/u/wim</span><code>ownerproof-123-456-9c3a0172</code>",
    )
    owner = get_owner("...")
    assert owner == "reddit.wim.123"


def test_get_owner_google(requests_mock):
    requests_mock.get(
        "https://adventofcode.com/settings",
        text='<span><img src="https://lh3.googleusercontent.com/...">wim</span><code>ownerproof-1-2</code>',
    )
    owner = get_owner("...")
    assert owner == "google.wim.1"


def test_atomic_write_file(aocd_data_dir):
    target = aocd_data_dir / "foo/bar/baz.txt"
    # Python 2.7 requires inputs to os.path.expanduser to be strings, not PosixPath (which is missing startswith)
    atomic_write_file(str(target), "123")  # no clobber
    assert target.read_text() == "123"
    atomic_write_file(str(target), "456")  # clobber existing
    assert target.read_text() == "456"


def test_mutual_rate():
    assert different_rate("111", "222") == 0
    assert different_rate("111", "111") == 0
    assert different_rate("111a", "a") == 0.5
    assert different_rate("1+1", "1") == 0.5
    assert different_rate("111", "a") == 1
    assert different_rate("111a", "") == 1
