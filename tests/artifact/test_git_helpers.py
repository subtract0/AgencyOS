import subprocess
from unittest import mock
from night_shift.artifact.git import get_recent_commits

def test_get_recent_commits_parses_output():
    fake_output = "abc123|John Doe|Initial commit\ndef456|Jane Smith|Add feature"
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(stdout=fake_output, returncode=0)
        res = get_recent_commits(limit=2)
        assert res.is_ok()
        commits = res.unwrap()
        assert len(commits) == 2
        assert commits[0].sha == "abc123"
        assert commits[0].author == "John Doe"
        assert commits[0].message == "Initial commit"
        assert commits[1].sha == "def456"
