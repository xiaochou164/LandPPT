from types import SimpleNamespace

import pytest

from landppt.services.project_workflow_stage_service import ProjectWorkflowStageService


class FakeProjectManager:
    def __init__(self, project):
        self.project = project

    async def get_project(self, project_id: str, user_id=None):
        return self.project

    @staticmethod
    def calculate_overall_progress(stages):
        if not stages:
            return 0.0
        return sum(float(getattr(stage, "progress", 0.0)) for stage in stages) / len(stages)


class FakeProjectManagerWithoutCalculate:
    def __init__(self, project):
        self.project = project

    async def get_project(self, project_id: str, user_id=None):
        return self.project


class FakeDbProjectManager:
    def __init__(self):
        self.updated_status = []
        self.updated_stages = []
        self.saved_outlines = []
        self.saved_slides = []

    async def update_project_status(self, project_id: str, status: str):
        self.updated_status.append((project_id, status))
        return True

    async def update_stage_status(self, project_id: str, stage_id: str, status: str, progress: float, result):
        self.updated_stages.append((project_id, stage_id, status, progress, result))
        return True

    async def save_project_outline(self, project_id: str, outline):
        self.saved_outlines.append((project_id, outline))
        return True

    async def save_project_slides(self, project_id: str, slides_html: str, slides_data):
        self.saved_slides.append((project_id, slides_html, slides_data))
        return True


def _make_stage(stage_id: str, status: str = "completed", progress: float = 100.0):
    return SimpleNamespace(
        id=stage_id,
        status=status,
        progress=progress,
        result={"ok": True},
        updated_at=0.0,
    )


@pytest.mark.asyncio
async def test_reset_stages_from_accepts_legacy_anchor_when_ppt_creation_not_present(monkeypatch):
    db_manager = FakeDbProjectManager()

    class _FakeDbManagerFactory:
        def __new__(cls):
            return db_manager

    monkeypatch.setattr("landppt.services.db_project_manager.DatabaseProjectManager", _FakeDbManagerFactory)

    stages = [
        _make_stage("requirements_confirmation"),
        _make_stage("outline_generation"),
        _make_stage("theme_design"),
        _make_stage("content_generation"),
        _make_stage("layout_verification"),
        _make_stage("export_output"),
    ]

    project = SimpleNamespace(
        todo_board=SimpleNamespace(
            stages=stages,
            current_stage_index=5,
            overall_progress=100.0,
            updated_at=0.0,
        ),
        outline={"slides": [{"title": "s1"}]},
        slides_html="<html>slides</html>",
        slides_data=[{"title": "slide"}],
        updated_at=0.0,
    )

    workflow = ProjectWorkflowStageService(
        SimpleNamespace(project_manager=FakeProjectManager(project))
    )

    success = await workflow.reset_stages_from("proj-legacy", "ppt_creation", user_id=1)

    assert success is True
    assert project.todo_board.current_stage_index == 2
    assert [stage.status for stage in project.todo_board.stages] == [
        "completed",
        "completed",
        "pending",
        "pending",
        "pending",
        "pending",
    ]
    assert project.outline == {"slides": [{"title": "s1"}]}
    assert project.slides_html is None
    assert project.slides_data is None

    assert db_manager.updated_status == [("proj-legacy", "in_progress")]
    assert [item[1] for item in db_manager.updated_stages] == [
        "theme_design",
        "content_generation",
        "layout_verification",
        "export_output",
    ]
    assert db_manager.saved_outlines == []
    assert db_manager.saved_slides == [("proj-legacy", "", [])]


@pytest.mark.asyncio
async def test_reset_stages_from_succeeds_without_manager_calculate_overall_progress(monkeypatch):
    db_manager = FakeDbProjectManager()

    class _FakeDbManagerFactory:
        def __new__(cls):
            return db_manager

    monkeypatch.setattr("landppt.services.db_project_manager.DatabaseProjectManager", _FakeDbManagerFactory)

    stages = [
        _make_stage("requirements_confirmation"),
        _make_stage("outline_generation"),
        _make_stage("ppt_creation"),
    ]

    project = SimpleNamespace(
        todo_board=SimpleNamespace(
            stages=stages,
            current_stage_index=2,
            overall_progress=100.0,
            updated_at=0.0,
        ),
        outline={"slides": [{"title": "s1"}]},
        slides_html="<html>slides</html>",
        slides_data=[{"title": "slide"}],
        updated_at=0.0,
    )

    workflow = ProjectWorkflowStageService(
        SimpleNamespace(project_manager=FakeProjectManagerWithoutCalculate(project))
    )

    success = await workflow.reset_stages_from("proj-no-calc", "ppt_creation", user_id=1)

    assert success is True
    assert project.todo_board.current_stage_index == 2
    assert [stage.status for stage in project.todo_board.stages] == [
        "completed",
        "completed",
        "pending",
    ]
    assert project.todo_board.overall_progress == pytest.approx((100.0 + 100.0 + 0.0) / 3)
    assert project.outline == {"slides": [{"title": "s1"}]}
    assert project.slides_html is None
    assert project.slides_data is None

    assert db_manager.updated_status == [("proj-no-calc", "in_progress")]
    assert [item[1] for item in db_manager.updated_stages] == ["ppt_creation"]
    assert db_manager.saved_outlines == []
    assert db_manager.saved_slides == [("proj-no-calc", "", [])]
