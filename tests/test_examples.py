from pathlib import Path
import pytest
from flow_learning_system import course, lesson

EX = sorted(p for p in (Path(__file__).parent.parent / "examples").iterdir() if (p / "course.json").exists())


@pytest.mark.parametrize("path", EX, ids=[p.name for p in EX])
def test_example_course_is_clean(path):
    c = course.load(path)
    assets = c.assets()
    total = 0
    for L in c.lessons:
        scenes, _, issues = lesson.analyze(L, c.pron, assets)
        errors = [str(i) for i in issues if i.level == "error"]
        assert not errors, (path.name, L["id"], errors[:3])
        total += len(scenes)
    assert total > 0
