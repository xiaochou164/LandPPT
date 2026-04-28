from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECTS_LIST_TEMPLATE = ROOT / "src/landppt/web/templates/pages/project/projects_list.html"
LIFECYCLE_ROUTES_FILE = ROOT / "src/landppt/web/route_modules/project_lifecycle_routes.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_projects_route_renders_pages_project_projects_list_template():
    routes_text = _read(LIFECYCLE_ROUTES_FILE)
    assert '"pages/project/projects_list.html"' in routes_text


def test_projects_list_buttons_have_explicit_actions_and_do_not_overlap():
    template_text = _read(PROJECTS_LIST_TEMPLATE)

    assert 'data-action="restart-ppt"' in template_text
    assert 'data-action="delete-project"' in template_text
    assert 'class="action-btn js-restart-ppt-btn"' in template_text
    assert 'class="action-btn action-btn--danger js-delete-project-btn"' in template_text

    assert 'button[data-action="restart-ppt"]:not(.js-delete-project-btn)' in template_text
    assert 'button[data-action="delete-project"]:not(.js-restart-ppt-btn)' in template_text


def test_restart_api_uses_current_endpoint_and_fallback_to_legacy_on_404():
    template_text = _read(PROJECTS_LIST_TEMPLATE)

    assert 'const currentEndpoint = `/api/projects/${projectId}/restart-ppt-generation`;' in template_text
    assert 'const legacyEndpoint = `/api/projects/${projectId}/restart-ppt-generation-entry`;' in template_text
    assert 'if (response.status === 404)' in template_text
    assert '({ response, payload } = await tryPostJson(legacyEndpoint));' in template_text


def test_reset_progress_actions_are_present_on_project_management_surfaces():
    template_text = _read(PROJECTS_LIST_TEMPLATE)
    project_detail_text = _read(ROOT / "src/landppt/web/templates/components/project/detail/content_1.html")
    project_detail_js = _read(ROOT / "src/landppt/web/templates/components/project/detail/extra_js_1.html")

    assert 'data-action="reset-requirements"' in template_text
    assert 'data-action="reset-outline"' in template_text
    assert '/api/projects/${projectId}/reset-progress' in template_text
    assert 'target_stage: targetStage' in template_text

    assert 'resetProjectProgress(' in project_detail_js
    assert '重置到需求确认' in project_detail_text
    assert '重置到大纲生成' in project_detail_text


def test_todo_board_templates_expose_reset_progress_controls_and_handlers():
    todo_board_content = _read(ROOT / "src/landppt/web/templates/components/project/todo_board/content_1.html")
    todo_board_js = _read(ROOT / "src/landppt/web/templates/components/project/todo_board/extra_js_1.html")
    todo_board_editor_body = _read(ROOT / "src/landppt/web/templates/components/project/todo_board_with_editor/body_1.html")
    todo_board_editor_js = _read(ROOT / "src/landppt/web/templates/components/project/todo_board_with_editor/script_1.html")

    for template_text in (todo_board_content, todo_board_editor_body):
        assert 'data-action="reset-requirements"' in template_text
        assert 'data-action="reset-outline"' in template_text
        assert '重置到需求确认' in template_text
        assert '重置到大纲生成' in template_text

    for script_text in (todo_board_js, todo_board_editor_js):
        assert '/api/projects/${projectId}/reset-progress' in script_text
        assert 'target_stage: targetStage' in script_text
        assert 'payload.next_url || `/projects/${projectId}/todo`' in script_text


def test_delete_flow_error_copy_is_not_mixed_with_restart_copy():
    template_text = _read(PROJECTS_LIST_TEMPLATE)

    delete_block = template_text.split('async function executeDeleteProject() {', 1)[1].split(
        'async function tryPostJson(url) {',
        1,
    )[0]

    assert '删除失败：' in delete_block
    assert '重置失败' not in delete_block
    assert '重新生成PPT失败' not in delete_block
    assert '/restart-ppt-generation' not in delete_block
