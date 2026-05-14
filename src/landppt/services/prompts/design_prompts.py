"""
PPT设计基因和视觉指导相关提示词
包含所有用于设计分析和视觉指导的提示词模板

"""

from typing import Dict, Any
import logging

from .system_prompts import SystemPrompts

logger = logging.getLogger(__name__)


def _is_image_service_enabled() -> bool:
    """检查图片服务是否启用和可用"""
    try:
        from ..service_instances import get_ppt_service
        ppt_service = get_ppt_service()

        if not ppt_service.image_service or not ppt_service.image_service.initialized:
            return False

        from ..image.providers.base import provider_registry

        generation_providers = provider_registry.get_generation_providers(enabled_only=True)
        search_providers = provider_registry.get_search_providers(enabled_only=True)
        storage_providers = provider_registry.get_storage_providers(enabled_only=True)

        has_providers = (
            len(generation_providers) > 0
            or len(search_providers) > 0
            or len(storage_providers) > 0
        )

        logger.debug(
            f"Image service status: initialized={ppt_service.image_service.initialized}, "
            f"generation={len(generation_providers)}, search={len(search_providers)}, "
            f"storage={len(storage_providers)}"
        )
        return has_providers

    except Exception as e:
        logger.debug(f"Failed to check image service status: {e}")
        return False


class DesignPrompts:
    """PPT 设计提示词构建器。

    所有 _build_* 方法返回可嵌入的上下文片段；
    所有 get_* 方法返回完整的、可直接发送给 LLM 的提示词。
    """

    # ================================================================
    # 一、基础上下文构建块（Context Building Blocks）
    # ================================================================

    @staticmethod
    def _build_resource_performance_context() -> str:
        """资源与性能约束。"""
        return SystemPrompts.get_resource_performance_prompt()

    @staticmethod
    def _build_template_guidance_context() -> str:
        """模板使用方向：合并模板继承、变化、锚点和推导提示。"""
        return """
**模板理解与使用方向**
把模板 HTML 原文当作视觉母语和边界参考，优先继承其中更稳定的配色、字体、材质、组件气质与锚点关系。
普通内容页更适合把变化放在主内容区，让标题区、页码区和其他稳定区域继续沿着模板里的结构与位置关系展开。
分析模板时，先看它如何组织阅读顺序、重心和层级，再决定这一页怎样做同源变化，而不是先套版式名称。
如果需要新的间距、体量、图文比例或强调方式，尽量从模板原文和内容逻辑中推导，让结果既有变化，也仍然像同一套设计系统。
""".strip()

    @staticmethod
    def _build_creative_intent_context() -> str:
        """创意决策：引导思考顺序而非指定步骤。"""
        return """
**创意思考顺序**
先问这页要做什么（聚焦？展开？对比？总结？转场？），再问观众第一眼该看哪里、阅读路径怎么走。
然后才决定空间怎么切、元素怎么放。装饰和点缀最后考虑——它们放大构图，但不能替代构图。
""".strip()

    @staticmethod
    def _build_html_output_context() -> str:
        """HTML 输出格式要求。"""
        return """
**输出格式**
只返回 ```html ... ``` 代码块，以 `<!DOCTYPE html>` 开始、`</html>` 结束，不附加解释。
""".strip()

    @staticmethod
    def _build_image_usage_context() -> str:
        """图片使用原则。"""
        return """
**图片使用**
图片服务于内容重点，不喧宾夺主。根据实际用途决定位置、裁切与样式，按需使用蒙版或边框。
""".strip()

    @staticmethod
    def _build_content_quality_context() -> str:
        """内容充实度与设计丰富度（合并原来两个方法）。"""
        return """
**内容与设计质量**
- 信息密度与主题复杂度相称，先补足事实和层次，再加装饰。
- 留白服务于分组和节奏，不替代内容；背景、数据、结论形成有区分度的前后层次。
- 避免四宫格等均质化布局；即使内容天然对等，也要通过主次、轻重、节奏建立层次差异。
""".strip()

    @staticmethod
    def _build_slide_generation_principles_context() -> str:
        """单页生成核心原则（用原则替代禁令清单）。"""
        return """
**生成方向**
- 先为页面建立清晰的第一视觉落点，再展开阅读动线。
- 通过分组、对比、层叠、方向变化或留白张力，让主次关系自然显现。
- 当内容容易变得平均时，优先调整空间关系，而不是把元素铺平摆齐。
- 避免默认落回四宫格、等宽等高卡片阵列这类均质化布局；即使四项内容完全对等，也不要做成均质排布，仍要主动制造视觉层次。
- 当内容偏多时，优先换一种更合适的组织方式，再考虑压缩细节。
- 让创意始终服务可读性、信息表达和实现稳定性。
""".strip()

    @staticmethod
    def _build_generation_self_check_context() -> str:
        """生成前自检（用问题替代规则）。"""
        return """
**输出前问自己**
- 主内容区是否真的围绕当前页任务重新组织，而不是直接沿用模板中段骨架？
- 标题区、页码区和稳定锚点是否仍然来自模板原文，而不是我临时发明的新规则？
- 当我调整间距、比例或强调方式时，能否在模板原文或内容逻辑里说清依据？
""".strip()

    # ================================================================
    # 二、固定画布相关（Canvas Constraints）
    # ================================================================

    @staticmethod
    def _build_fixed_canvas_strategy_context() -> str:
        """固定画布高层策略。"""
        return """
**固定画布策略**
- 1280×720 外框先约束，内容再适配；三段式结构（页眉/主体/页脚），页眉页脚不可压缩，主体区吸收剩余空间。
- 先做高度预算再做视觉设计；间距用 `gap`/百分比/`clamp()`，不要用大号固定 `padding`/`margin` 硬顶。
- 图表、卡片组、长列表等易增高模块，优先限高、减列、收紧装饰，再考虑缩字号。
""".strip()

    @staticmethod
    def _build_fixed_canvas_html_guardrails() -> str:
        """固定画布 HTML 实现提醒。"""
        return """
**固定画布实现**
- 根容器 `1280×720` + `overflow:hidden`；主内容区是重构区，锚点区沿用模板位置。首尾页弱化页码。
- flex 骨架：锚点区稳定，主区可收缩；grid 骨架：主轨道可压缩，flex/grid item 设置最小尺寸。
- 溢出时优先删减/分组/限高，不挤压锚点区；避免滚动条和硬裁切。
""".strip()

    @staticmethod
    def _build_layout_priority_context() -> str:
        """版面优先级。"""
        return """
**版面取舍顺序**
优先守住 1280×720 内的完整容纳和锚点稳定，再决定装饰强度与版式复杂度。
内容偏多时，可以先从装饰、特效、间距和次要说明中回收空间，再考虑字号微调。
当布局被推到极限时，选择更简单的组织方式，通常比硬撑当前构图更稳。
""".strip()

    # ================================================================
    # 三、版式知识库（Layout Knowledge）
    # ================================================================

    @staticmethod
    def _build_layout_mastery_context() -> str:
        """高级版式方法库：显式提供布局推理工具箱。"""
        return """
**版式工具箱（内化后使用，输出时转化为可执行的排版判断）**
可混合使用，但要明确主导/辅助策略；高张力做法须确保版心、安全区和可读性稳定。

**栅格与空间**：版心、天头/地脚、水槽、模块化栅格、分栏网格（12/24栏）、基线网格、出血位、微观/宏观留白、安全边界。
**视觉动线**：古腾堡图表、F型、Z型、第一落幅/视觉锚点、引导线、中心辐射、格式塔分组。
**版式结构**：三分法、非对称平衡、砌体/瀑布流、满版全画幅、悬浮顶对齐、对角线构图、黄金比例、仪表盘、时间线、沉浸场景。
**对齐与微排版**：悬挂缩进、孤寡行控制、视觉边界补偿、纵向节律、字偶间距、层级跃升。
**破局与张力**：破格、叠层、截断感、跨栏延展、留白张力、色彩重量倾斜、沉底排版。
""".strip()

    # ================================================================
    # 四、模板解析工具（Template Analysis）
    # ================================================================

    @staticmethod
    def _build_project_brief(confirmed_requirements: Dict[str, Any]) -> str:
        """从需求中构建紧凑的项目简报。"""
        confirmed_requirements = confirmed_requirements or {}

        field_map = {
            '主题': confirmed_requirements.get('topic') or confirmed_requirements.get('title'),
            '项目类型': confirmed_requirements.get('type') or confirmed_requirements.get('scenario'),
            '使用场景': confirmed_requirements.get('scenario'),
            '目标受众': (
                confirmed_requirements.get('target_audience')
                or confirmed_requirements.get('custom_audience')
            ),
            '风格偏好': confirmed_requirements.get('ppt_style'),
            '自定义风格补充': confirmed_requirements.get('custom_style_prompt'),
        }

        lines = [f"- {k}：{v}" for k, v in field_map.items() if v]
        return "\n".join(lines) if lines else "- 未提供项目背景，请根据内容自行建立设计主张。"

    @staticmethod
    def _build_slide_images_context(slide_data: Dict[str, Any]) -> str:
        """仅当有图片输入时构建图片上下文。"""
        if not (_is_image_service_enabled() and 'images_summary' in slide_data):
            return ""
        return f"\n\n{DesignPrompts._build_image_usage_context()}"

    def _build_template_html_context(template_html: str) -> str:
        """模板 HTML 原样透传，不做截断、提取或兜底。"""
        return template_html or ""

    @staticmethod
    def _build_locked_zones_context(template_html: str, page_number: int,
                                     total_pages: int, slide_type: str,
                                      slide_title: str = "") -> str:
        """普通内容页给出稳定区域的理解方向，不解析模板 HTML。"""
        is_first = page_number == 1
        is_last = page_number == total_pages
        is_catalog = slide_type in ("outline", "catalog", "directory", "agenda")
        if not is_catalog and slide_title:
            is_catalog = any(kw in slide_title for kw in ["目录", "大纲"])

        if is_first or is_last or is_catalog or not template_html:
            return ""

        return """
**稳定区域理解方向**
结合上方模板 HTML 原文，自行识别标题区、页码区和其他稳定锚点。
普通内容页更适合沿用这些区域的层级、位置关系和语气，只在主内容区重新组织信息。
""".strip()

    @staticmethod
    def _normalize_page_guidance_type(slide_data: Dict[str, Any], page_number: int, total_pages: int) -> str:
        """将页面归一到可复用的页面类型，用于类型级指导。"""
        slide_data = slide_data or {}
        title = str(slide_data.get("title") or "").strip()
        slide_type = str(slide_data.get("slide_type") or slide_data.get("type") or "").strip().lower()

        if page_number == 1:
            return "cover"
        if page_number == total_pages:
            return "ending"
        if slide_type in ("outline", "catalog", "directory", "agenda") or any(
            kw in title for kw in ["目录", "大纲"]
        ):
            return "catalog"
        if not slide_type or slide_type == "unknown":
            return "content"
        return slide_type

    @staticmethod
    def _get_page_guidance_type_label(guidance_type: str) -> str:
        """将页面类型键映射为可读标签。"""
        label_map = {
            "cover": "首页/封面",
            "catalog": "目录/大纲",
            "transition": "章节过渡页",
            "ending": "结尾/感谢",
            "content": "普通内容页",
        }
        return label_map.get(guidance_type, f"{guidance_type} 类型页")

    @staticmethod
    def _build_page_type_guidance_overview(all_slides: list, total_pages: int) -> str:
        """构建页面类型概览，提示模型按类型输出指导。"""
        groups: Dict[str, Dict[str, Any]] = {}

        for idx in range(total_pages):
            page_number = idx + 1
            slide = (all_slides[idx] if all_slides and idx < len(all_slides) else {}) or {}
            guidance_type = DesignPrompts._normalize_page_guidance_type(slide, page_number, total_pages)
            title = str(slide.get("title") or f"第{page_number}页").strip()

            entry = groups.setdefault(
                guidance_type,
                {
                    "label": DesignPrompts._get_page_guidance_type_label(guidance_type),
                    "pages": [],
                },
            )
            entry["pages"].append(f"第{page_number}页《{title}》")

        lines = []
        for guidance_type, entry in groups.items():
            pages = entry["pages"]
            pages_text = "、".join(pages[:6])
            if len(pages) > 6:
                pages_text += f" 等 {len(pages)} 页"
            lines.append(f"- TYPE: {guidance_type}（{entry['label']}）：{pages_text}")

        return "\n".join(lines) if lines else "- TYPE: content（普通内容页）：请结合完整大纲自行归纳。"

    # ================================================================
    # 五、三层架构提示词（Layer 1/2/3）
    # ================================================================

    @staticmethod
    def get_global_visual_constitution_prompt(confirmed_requirements: Dict[str, Any],
                                              template_html: str, total_pages: int,
                                              first_slide_data: Dict[str, Any] = None) -> str:
        """Layer 1: 全局视觉宪法——只定规则，不涉及具体页面。"""
        project_brief = DesignPrompts._build_project_brief(confirmed_requirements)
        template_context = DesignPrompts._build_template_html_context(template_html)
        resource_perf = DesignPrompts._build_resource_performance_context()

        return f"""请为一套 {total_pages} 页的 PPT 输出"全局视觉宪法"——只定规则，不涉及任何具体页面的布局。

**项目简报**
{project_brief}

**参考模板 HTML 原文**
{template_context}

{DesignPrompts._build_template_guidance_context()}

{DesignPrompts._build_fixed_canvas_strategy_context()}

请按以下结构输出：

1. **整册视觉气质**
   - 核心风格方向、色彩策略、装饰语言
   - 首页与普通内容页的气质差异

2. **固定画布规则**
   - 1280×720 画布下的锚点预算策略
   - 首页和尾页不显示页码
   - 其他页面的页码锚点规则

3. **给单页生成器的执行原则**
   - 涵盖：布局选择、层级建立、配色使用、内容版式组织、模板边界

{resource_perf}

要求：
- 只输出全局规则，不要涉及具体某一页
- 规则要可执行，不要空泛形容
- 不要给出具体像素值或固定比例数字，让单页生成器根据内容自行推导"""

    @staticmethod
    def get_page_creative_briefs_prompt(confirmed_requirements: Dict[str, Any],
                                        all_slides: list, total_pages: int,
                                        global_constitution: str) -> str:
        """Layer 2: 按页面类型输出页面指导——给方向感但不锁死版式。"""
        project_brief = DesignPrompts._build_project_brief(confirmed_requirements)
        page_type_overview = DesignPrompts._build_page_type_guidance_overview(all_slides, total_pages)

        slides_lines = []
        for idx, slide in enumerate(all_slides or [], start=1):
            if not isinstance(slide, dict):
                continue
            title = str(slide.get("title") or f"第{idx}页").strip()
            slide_type = str(slide.get("slide_type") or slide.get("type") or "content").strip()
            points = slide.get("content_points") or slide.get("content") or []
            if isinstance(points, list):
                pts = "；".join(str(p).strip()[:50] for p in points[:5] if str(p).strip())
            else:
                pts = str(points).strip()[:100]
            line = f"{idx}. {title}（{slide_type}"
            if pts:
                line += f"；{pts}"
            line += "）"
            slides_lines.append(line)
        slides_detail = "\n".join(slides_lines) if slides_lines else "(无大纲数据)"

        return f"""请为这套 {total_pages} 页 PPT 生成整套"页面类型指导"。

**项目简报**
{project_brief}

**全局视觉方向（已确定，优先对齐）**
{global_constitution}

**完整大纲**
{slides_detail}

**页面类型概览**
{page_type_overview}

{DesignPrompts._build_layout_mastery_context()}

**你的任务**
按页面类型归纳指导，同类型只输出一次，共享方向、节奏和边界。
变化空间写进"节奏与变化"或"弹性调节"；用弹性表达给单页生成器留空间。
不要输出 JSON、固定尺寸参数或查表式枚举。

请严格按以下结构输出，每种类型只输出一次，并沿用上方概览里的 `TYPE` 键名：

## TYPE: cover
- **适用页面**：这一类型覆盖哪些页面
- **页面角色**：这一类型页面在整套 PPT 里的作用
- **设计概念**：适合这一类型页面的高级排版/信息设计概念
- **视觉焦点**：观众第一眼应该看到什么
- **构图倾向**：适合怎样的空间关系和主次节奏
- **节奏与变化**：同类型页面之间可以如何避免雷同
- **创意边界**：哪些克制，哪些可以大胆
- **弹性调节**：内容过多或过少时优先如何调整

补充：
- 首页、目录页、尾页属于特殊页面，可相对自由地处理锚点关系。
- 更适合给出相对关系，而不是具体像素值或比例范围。
- 只输出页面类型指导，不附加解释。"""

    @staticmethod
    def get_page_plan_prompt(confirmed_requirements: Dict[str, Any],
                             all_slides: list, total_pages: int,
                             global_constitution: str) -> str:
        """向后兼容：旧接口转发到按页面类型输出的指导提示词。"""
        return DesignPrompts.get_page_creative_briefs_prompt(
            confirmed_requirements=confirmed_requirements,
            all_slides=all_slides,
            total_pages=total_pages,
            global_constitution=global_constitution,
        )

    # ================================================================
    # 六、项目级与页面级设计指导（Design Guides）
    # ================================================================

    @staticmethod
    def get_project_design_guide_prompt(confirmed_requirements: Dict[str, Any],
                                        slides_summary: str, total_pages: int,
                                        first_slide_data: Dict[str, Any] = None,
                                        template_html: str = "") -> str:
        """项目级创意设计指导。"""
        project_brief = DesignPrompts._build_project_brief(confirmed_requirements)
        slides_summary = slides_summary or "(未提供大纲摘要)"
        template_context = DesignPrompts._build_template_html_context(template_html)
        resource_perf = DesignPrompts._build_resource_performance_context()

        return f"""请为整套 PPT 生成一份"项目级创意设计指导"。

输出全局可迁移的设计策略，而非某一页的局部答案。
先阅读模板 HTML 原文判断可继承的视觉边界，再定义整体气质，最后扩展为页面家族系统和跨页节奏。

**项目简报**
{project_brief}

**整套结构摘要**
{slides_summary}

**总页数**：{total_pages} 页

**模板 HTML 原文**
{template_context}

{DesignPrompts._build_template_guidance_context()}

{DesignPrompts._build_content_quality_context()}

{DesignPrompts._build_fixed_canvas_strategy_context()}

{DesignPrompts._build_layout_priority_context()}

{DesignPrompts._build_layout_mastery_context()}

请按以下结构输出：

**A. 整体叙事与视觉主张**
**B. 模板继承边界与全局风格系统**
**C. 首页/封面首屏锚点策略**（明确哪些只属于首页）
**D. 跨页节奏与空间原则**（如何避免连续雷同）
**E. 普通内容页与特殊页面的分工**
**F. 图像、图标与数据可视化原则**
**G. 风险与禁区**
**H. 给单页生成器的执行原则**

要求：
- 具体、专业、可操作，避免空泛形容词
- 更适合给出相对关系，而不是具体像素值或固定版式方案
- 如果模板与项目语义冲突，说明如何受控修正
- 不要直接代写任何页面的 HTML

{resource_perf}"""

    @staticmethod
    def get_slide_design_guide_prompt(slide_data: Dict[str, Any], confirmed_requirements: Dict[str, Any],
                                      slides_summary: str, page_number: int, total_pages: int,
                                      template_html: str = "") -> str:
        """单页级创意设计指导。"""
        project_brief = DesignPrompts._build_project_brief(confirmed_requirements)
        slides_summary = slides_summary or "(未提供大纲摘要)"
        images_context = DesignPrompts._build_slide_images_context(slide_data)
        template_context = DesignPrompts._build_template_html_context(template_html)
        resource_perf = DesignPrompts._build_resource_performance_context()

        return f"""请为第 {page_number} 页生成"单页创意设计指导"。

延续整套风格，让当前页拥有明确角色和合适变化。聚焦当前页，不要写泛泛原则。

**项目简报**
{project_brief}

**整套结构摘要**
{slides_summary}

**当前页数据**
{slide_data}

**页面位置**：第 {page_number} 页 / 共 {total_pages} 页

**模板 HTML 原文**
{template_context}

{DesignPrompts._build_template_guidance_context()}

{DesignPrompts._build_content_quality_context()}

{DesignPrompts._build_fixed_canvas_strategy_context()}

{DesignPrompts._build_layout_priority_context()}

{DesignPrompts._build_layout_mastery_context()}

{images_context}

**额外要求**
- 根据标题长度、要点数量、是否含图表/表格/时间线等，判断适合放大焦点、保持均衡还是压缩收敛
- 从版式工具箱中选择最合适的方法，转化为可执行建议
- 明确避免推荐四宫格等均质化布局；即使当前页内容天然四等分且主次关系一致，也必须主动建立视觉层次，不能做成均质排布
- 更适合给出相对关系，让生成器根据内容自行推导

请按以下结构输出：

**A. 当前页角色判断**
**B. 视觉焦点与布局方向**（标题区、主体区、页码区的空间预算）
**C. 内容呈现策略**（内容偏少/适中/偏多时如何调节）
**D. 色彩、组件与图像处理**
**E. 与前后页面的呼应和差异化**
**F. 风险与避坑**

{resource_perf}"""

    # ================================================================
    # 七、HTML 生成提示词（Slide Generation）
    # ================================================================

    @staticmethod
    def get_creative_template_context_prompt(slide_data: Dict[str, Any], template_html: str,
                                           slide_title: str, slide_type: str, page_number: int,
                                           total_pages: int, context_info: str, style_genes: str,
                                           project_topic: str = "",
                                           project_type: str = "", project_audience: str = "",
                                           project_style: str = "",
                                           global_constitution: str = "",
                                           current_page_brief: str = "") -> str:
        """创意模板上下文 HTML 生成提示词。"""
        template_context = DesignPrompts._build_template_html_context(template_html)
        locked_zones = DesignPrompts._build_locked_zones_context(
            template_html, page_number, total_pages, slide_type, slide_title)
        images_info = ""
        if _is_image_service_enabled() and 'images_summary' in slide_data:
            images_info = "\n\n" + DesignPrompts._build_image_usage_context()
        resource_perf = DesignPrompts._build_resource_performance_context()

        # 条件性地加入指导上下文
        constitution_block = f"**全局设计规则**\n{global_constitution}" if global_constitution else ""
        brief_block = f"**当前页面指导**\n{current_page_brief}" if current_page_brief else ""

        return f"""为第{page_number}页生成完整 PPT HTML。

**核心目标**
把模板当作视觉语言系统来创作，而不是换字。主内容区更适合围绕当前页使命重新建立空间秩序。
如果结果看起来接近"模板换字"，回到主内容区重新组织。

**页面信息**
- 标题：{slide_title}
- 类型：{slide_type}
- 第 {page_number} 页 / 共 {total_pages} 页

**页面数据**
{slide_data}
{images_info}

**模板 HTML 原文**
{template_context}

{DesignPrompts._build_template_guidance_context()}

{locked_zones}

{DesignPrompts._build_content_quality_context()}

{DesignPrompts._build_creative_intent_context()}

**项目背景**
- 主题：{project_topic}
- 类型：{project_type}
- 受众：{project_audience}
- 风格：{project_style}

**设计基因**
{style_genes}

{constitution_block}

{brief_block}

{DesignPrompts._build_fixed_canvas_html_guardrails()}

{DesignPrompts._build_layout_priority_context()}

{context_info}

{DesignPrompts._build_slide_generation_principles_context()}

{DesignPrompts._build_generation_self_check_context()}

**富文本**
可按需使用 MathJax、Prism.js、Chart.js、ECharts.js、D3.js。

{resource_perf}

{DesignPrompts._build_html_output_context()}
"""

    @staticmethod
    def get_single_slide_html_prompt(slide_data: Dict[str, Any], confirmed_requirements: Dict[str, Any],
                                   page_number: int, total_pages: int, context_info: str,
                                   style_genes: str,
                                   template_html: str = "",
                                   global_constitution: str = "",
                                   current_page_brief: str = "") -> str:
        """单页 HTML 生成提示词。"""
        slide_type = slide_data.get("slide_type", "content") if isinstance(slide_data, dict) else "content"
        slide_title = slide_data.get("title", "") if isinstance(slide_data, dict) else ""
        template_context = DesignPrompts._build_template_html_context(template_html)
        locked_zones = DesignPrompts._build_locked_zones_context(
            template_html, page_number, total_pages, slide_type, slide_title)
        images_info = ""
        if _is_image_service_enabled() and 'images_summary' in slide_data:
            images_info = "\n\n" + DesignPrompts._build_image_usage_context()
        resource_perf = DesignPrompts._build_resource_performance_context()

        constitution_block = f"**全局设计规则**\n{global_constitution}" if global_constitution else ""
        brief_block = f"**当前页面指导**\n{current_page_brief}" if current_page_brief else ""

        return f"""为第{page_number}页生成完整 HTML。

**核心目标**
把内容、模板语言和创意蓝图转译成一个成立的空间体验。
如果结果看起来接近"模板换字"，回到主内容区重新组织。

**项目信息**
- 主题：{confirmed_requirements.get('topic', '')}
- 受众：{confirmed_requirements.get('target_audience', '')}
- 补充：{confirmed_requirements.get('description', '无')}

**当前页面**
{slide_data}
{images_info}

**模板 HTML 原文**
{template_context}

{DesignPrompts._build_template_guidance_context()}

{locked_zones}

{DesignPrompts._build_content_quality_context()}

{DesignPrompts._build_creative_intent_context()}

**设计基因**
{style_genes}

{constitution_block}

{brief_block}

{DesignPrompts._build_fixed_canvas_html_guardrails()}

{DesignPrompts._build_layout_priority_context()}

{context_info}

{DesignPrompts._build_slide_generation_principles_context()}

{DesignPrompts._build_generation_self_check_context()}

**富文本**
可按需使用 MathJax、Prism.js、Chart.js、ECharts.js、D3.js。

{resource_perf}

{DesignPrompts._build_html_output_context()}
"""

    # ================================================================
    # 八、辅助提示词（Utility Prompts）
    # ================================================================

    @staticmethod
    def get_style_gene_extraction_prompt(template_code: str) -> str:
        """设计基因提取提示词。"""
        template_context = DesignPrompts._build_template_html_context(template_code)
        resource_perf = DesignPrompts._build_resource_performance_context()

        return f"""请直接阅读以下模板 HTML 原文，提炼"可复用设计基因"。

{template_context}

请输出：
1. 色彩系统
2. 字体系统
3. 布局与间距特征
4. 组件与材质语言
5. 可复用倾向与边界

要求：尽量具体（可写 CSS 值、比例或关键词），聚焦稳定特征，不必复述源码。

{resource_perf}"""

    @staticmethod
    def get_style_genes_extraction_prompt(template_code: str) -> str:
        """向后兼容别名。"""
        return DesignPrompts.get_style_gene_extraction_prompt(template_code)

    @staticmethod
    def get_creative_variation_prompt(slide_data: Dict[str, Any], page_number: int, total_pages: int) -> str:
        """创意变化指导提示词。"""
        return f"""请为当前页提供创意变化建议。

**页面数据**
{slide_data}

**页面位置**：第{page_number}页 / 共{total_pages}页

请输出：
1. 适合的变化方向
2. 可变化的元素（布局、焦点、背景等）
3. 需要保持不变的全局特征
4. 需要避免的雷同和过度设计

要求：变化服务内容，不要为变化而变化。不要推荐海外外链资源。"""

    @staticmethod
    def get_content_driven_design_prompt(slide_data: Dict[str, Any], page_number: int, total_pages: int) -> str:
        """内容驱动设计建议提示词。"""
        return f"""请根据当前页内容给出版式建议。

**页面数据**
{slide_data}

**页面位置**：第{page_number}页 / 共{total_pages}页

请输出：
1. 信息层级
2. 最合适的表达方式
3. 布局建议
4. 风险与取舍

要求：优先服务信息清晰度和阅读效率。不要推荐海外外链资源。"""

    @staticmethod
    def get_slide_context_prompt(slide_data: Dict[str, Any], page_number: int, total_pages: int) -> str:
        """幻灯片上下文提示词（特殊页面 vs 普通页面）。"""
        slide_type = slide_data.get("slide_type", "")
        title = slide_data.get("title", "")

        is_catalog = (
            slide_type in ("outline", "catalog", "directory", "agenda")
            or any(kw in title for kw in ["目录", "大纲"])
        )

        # --- 特殊页面 ---
        if page_number == 1:
            return """**特殊页面：首页/封面**
- 更适合做出区别于普通内容页的开篇设计。
- 通常不显示页码，标题区和编号区可以更自由地处理。
- 建立强主焦点和开篇气场，标题是绝对焦点。
- 应与后续内容页有明显视觉区别，作为整套 PPT 的开篇定调。
"""

        if is_catalog:
            return """**特殊页面：目录/大纲**
- 属于特殊页面，需要与普通内容页明显不同。
- 不显示页码，锚点可以自由设计。
- 核心是结构导航：章节关系、主次层级一眼可辨。
- 与首页风格衔接，作为从开篇到正文的过渡。
"""

        if str(slide_type).lower() == "transition":
            return """**特殊页面：章节过渡页**
- 用于章节分隔和演示节奏控制，需要与普通内容页明显不同。
- 优先突出章节标题、短转场语和下一部分方向，不展开正文。
- 可以弱化页码和细节元素，让页面更像阶段切换。
"""

        if page_number == total_pages:
            return """**特殊页面：结尾/感谢**
- 更适合做出有收束感和仪式感的设计，与首页形成呼应。
- 通常不显示页码，锚点可以更自由地处理。
- 优先单一焦点和情绪收尾，与首页在气质上形成闭环。
"""

        # --- 普通内容页 ---
        return """**普通内容页**
        - 标题区和页码区为母板锚定区，创意主要发生在主内容区。
        - 页码锚点优先跟随模板原有位置。
        - 吸收页面指导的方向建议，但可根据内容自由选择实现方式。
        - 每个要点展开为完整信息单元，组合多种视觉手法，避免纯文本。
"""

    @staticmethod
    def get_combined_style_genes_and_guide_prompt(template_code: str, slide_data: Dict[str, Any],
                                                  page_number: int, total_pages: int) -> str:
        """合并的设计基因 + 统一设计指导（单次 LLM 调用）。

        输出用分隔标记分开：
        - ===STYLE_GENES=== / ===END_STYLE_GENES===
        - ===DESIGN_GUIDE=== / ===END_DESIGN_GUIDE===
        """
        images_context = ""
        if _is_image_service_enabled() and 'images_summary' in slide_data:
            images_context = f"\n\n{DesignPrompts._build_image_usage_context()}"
        template_context = DesignPrompts._build_template_html_context(template_code)
        resource_perf = DesignPrompts._build_resource_performance_context()

        return f"""请一次完成两件事，严格按标记输出。

**输入**
- 首页数据：{slide_data}
- 总页数：{total_pages}页
{images_context}

**模板 HTML 原文**
{template_context}

{DesignPrompts._build_template_guidance_context()}

{DesignPrompts._build_content_quality_context()}

{DesignPrompts._build_fixed_canvas_strategy_context()}

{DesignPrompts._build_layout_priority_context()}

{DesignPrompts._build_layout_mastery_context()}

**任务一：提炼设计基因**
只总结可跨页复用的稳定规则：色彩、字体、布局、组件/材质、约束。

**任务二：生成通用设计指导**
基于设计基因和首页信息，写出整套 PPT 的方向：
气质、页面家族、内容密度、图片/图表语气、固定画布限制。

**输出格式**

===STYLE_GENES===
任务一结果
===END_STYLE_GENES===

===DESIGN_GUIDE===
任务二结果
===END_DESIGN_GUIDE===

不要输出其他说明。

{resource_perf}"""
