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
