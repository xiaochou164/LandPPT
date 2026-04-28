import json
from types import SimpleNamespace

import pytest
from fastapi import HTTPException


class FakeProjectManager:
    def __init__(self, project, *, raise_on_update: Exception | None = None):
        self.project = project
        self.raise_on_update = raise_on_update
        self.update_calls = []

    async def get_project(self, project_id: str, user_id=None):
        return self.project

    async def update_project_metadata(self, project_id: str, metadata, user_id=None):
        self.update_calls.append(
            {
                "project_id": project_id,
                "metadata": metadata,
                "user_id": user_id,
            }
        )
        if self.raise_on_update:
            raise self.raise_on_update


class FakePPTService:
    def __init__(self, project, *, reset_result=True, raise_on_update: Exception | None = None):
        self.project_manager = FakeProjectManager(project, raise_on_update=raise_on_update)
        self.reset_result = reset_result
        self.reset_calls = []
        self.start_calls = []
        self.cleared_project_ids = []

    async def reset_stages_from(self, project_id: str, stage_id: str, user_id=None):
        self.reset_calls.append(
            {
                "project_id": project_id,
                "stage_id": stage_id,
                "user_id": user_id,
            }
        )
        return self.reset_result

    async def start_workflow_from_stage(self, project_id: str, stage_id: str, user_id=None):
        self.start_calls.append(
            {
                "project_id": project_id,
                "stage_id": stage_id,
                "user_id": user_id,
            }
        )
        return True

    def clear_cached_style_genes(self, project_id: str):
        self.cleared_project_ids.append(project_id)


@pytest.mark.asyncio
async def test_restart_ppt_generation_success(monkeypatch):
    from landppt.api import landppt_api

    project = SimpleNamespace(
        project_metadata={
            "selected_global_template_id": "tpl-1",
            "template_mode": "global",
            "free_template_status": "done",
            "keep_me": "value",
        }
    )
    service = FakePPTService(project, reset_result=True)
    monkeypatch.setattr(landppt_api, "get_ppt_service_for_user", lambda _uid: service)

    result = await landppt_api.restart_project_ppt_generation(
        "proj-123",
        user=SimpleNamespace(id=99),
    )

    assert result["status"] == "success"
    assert result["project_id"] == "proj-123"
    assert result["next_url"] == "/projects/proj-123/template-selection"
    assert service.reset_calls == [
        {"project_id": "proj-123", "stage_id": "ppt_creation", "user_id": 99}
    ]
    assert service.cleared_project_ids == ["proj-123"]
    assert service.project_manager.update_calls[0]["metadata"] == {"keep_me": "value"}


@pytest.mark.asyncio
async def test_restart_ppt_generation_returns_400_when_reset_fails(monkeypatch):
    from landppt.api import landppt_api

    project = SimpleNamespace(project_metadata={})
    service = FakePPTService(project, reset_result=False)
    monkeypatch.setattr(landppt_api, "get_ppt_service_for_user", lambda _uid: service)

    with pytest.raises(HTTPException) as excinfo:
        await landppt_api.restart_project_ppt_generation(
            "proj-400",
            user=SimpleNamespace(id=7),
        )

    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "Failed to reset PPT creation stage"


@pytest.mark.asyncio
async def test_restart_ppt_generation_returns_404_when_project_not_found_or_forbidden(monkeypatch):
    from landppt.api import landppt_api

    # Ownership enforcement in service layer returns None for not-found / no-permission cases.
    service = FakePPTService(project=None, reset_result=True)
    monkeypatch.setattr(landppt_api, "get_ppt_service_for_user", lambda _uid: service)

    with pytest.raises(HTTPException) as excinfo:
        await landppt_api.restart_project_ppt_generation(
            "proj-404",
            user=SimpleNamespace(id=8),
        )

    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Project not found"
    assert service.reset_calls == []


@pytest.mark.asyncio
async def test_restart_ppt_generation_masks_internal_error_detail(monkeypatch):
    from landppt.api import landppt_api

    sensitive_error = RuntimeError("db password leaked")
    project = SimpleNamespace(project_metadata={"keep_me": "value"})
    service = FakePPTService(project, reset_result=True, raise_on_update=sensitive_error)
    monkeypatch.setattr(landppt_api, "get_ppt_service_for_user", lambda _uid: service)

    with pytest.raises(HTTPException) as excinfo:
        await landppt_api.restart_project_ppt_generation(
            "proj-500",
            user=SimpleNamespace(id=11),
        )

    assert excinfo.value.status_code == 500
    assert excinfo.value.detail == "Failed to restart PPT generation"
    assert "password" not in excinfo.value.detail


def test_restart_ppt_generation_legacy_and_current_routes_both_registered():
    from landppt.api import landppt_api

    post_paths = {
        route.path
        for route in landppt_api.router.routes
        if "POST" in getattr(route, "methods", set())
    }

    assert "/projects/{project_id}/restart-ppt-generation" in post_paths
    assert "/projects/{project_id}/restart-ppt-generation-entry" in post_paths
    assert "/projects/{project_id}/reset-progress" in post_paths


@pytest.mark.asyncio
async def test_reset_project_progress_success(monkeypatch):
    from landppt.api import landppt_api

    project = SimpleNamespace(project_metadata={"keep_me": "value"})
    service = FakePPTService(project, reset_result=True)
    monkeypatch.setattr(landppt_api, "get_ppt_service_for_user", lambda _uid: service)

    class _FakeRequest:
        async def json(self):
            return {"target_stage": "outline_generation"}

    result = await landppt_api.reset_project_progress(
        "proj-reset",
        request=_FakeRequest(),
        user=SimpleNamespace(id=21),
    )

    assert result == {
        "status": "success",
        "message": "项目进度已重置到大纲生成",
        "project_id": "proj-reset",
        "target_stage": "outline_generation",
        "next_url": "/projects/proj-reset/todo",
    }
    assert service.reset_calls == [
        {"project_id": "proj-reset", "stage_id": "outline_generation", "user_id": 21}
    ]
    assert service.start_calls == []


@pytest.mark.asyncio
async def test_reset_project_progress_rejects_invalid_target_stage(monkeypatch):
    from landppt.api import landppt_api

    service = FakePPTService(SimpleNamespace(project_metadata={}), reset_result=True)
    monkeypatch.setattr(landppt_api, "get_ppt_service_for_user", lambda _uid: service)

    class _FakeRequest:
        async def json(self):
            return {"target_stage": "ppt_creation"}

    with pytest.raises(HTTPException) as excinfo:
        await landppt_api.reset_project_progress(
            "proj-reset-invalid",
            request=_FakeRequest(),
            user=SimpleNamespace(id=22),
        )

    assert excinfo.value.status_code == 422
    assert excinfo.value.detail == "Unsupported target stage"
    assert service.reset_calls == []


@pytest.mark.asyncio
async def test_reset_project_progress_rejects_malformed_json(monkeypatch):
    from landppt.api import landppt_api

    service = FakePPTService(SimpleNamespace(project_metadata={}), reset_result=True)
    monkeypatch.setattr(landppt_api, "get_ppt_service_for_user", lambda _uid: service)

    class _FakeRequest:
        async def json(self):
            raise json.JSONDecodeError("Expecting value", "{", 0)

    with pytest.raises(HTTPException) as excinfo:
        await landppt_api.reset_project_progress(
            "proj-reset-bad-json",
            request=_FakeRequest(),
            user=SimpleNamespace(id=23),
        )

    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "Malformed JSON body"
    assert service.reset_calls == []


@pytest.mark.asyncio
async def test_reset_project_progress_requires_target_stage(monkeypatch):
    from landppt.api import landppt_api

    service = FakePPTService(SimpleNamespace(project_metadata={}), reset_result=True)
    monkeypatch.setattr(landppt_api, "get_ppt_service_for_user", lambda _uid: service)

    class _FakeRequest:
        async def json(self):
            return {}

    with pytest.raises(HTTPException) as excinfo:
        await landppt_api.reset_project_progress(
            "proj-reset-missing-stage",
            request=_FakeRequest(),
            user=SimpleNamespace(id=24),
        )

    assert excinfo.value.status_code == 422
    assert excinfo.value.detail == "Target stage is required"
    assert service.reset_calls == []
