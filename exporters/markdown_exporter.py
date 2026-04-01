"""
Markdown Exporter — writes blog drafts and video script to the output directory.

Blog files:   content/blog_<brief_id>.md
Video script: content/video_script.md
"""

from pathlib import Path

from schemas.content_schemas import BlogPerspective, ContentBundle, VideoScript


class MarkdownExporter:
    def export(self, bundle: ContentBundle, content_dir: Path) -> dict[str, str]:
        """
        Write all content files to disk.
        Returns a dict of {description: file_path} for summary display.
        """
        content_dir.mkdir(parents=True, exist_ok=True)
        output_paths: dict[str, str] = {}

        for blog in bundle.blog_perspectives:
            path = content_dir / f"blog_{blog.perspective_id}.md"
            path.write_text(_render_blog(blog), encoding="utf-8")
            output_paths[f"Blog: {blog.perspective_id}"] = str(path)

        video_path = content_dir / "video_script.md"
        video_path.write_text(_render_video(bundle.video_script), encoding="utf-8")
        output_paths["Video Script"] = str(video_path)

        return output_paths


def _render_blog(blog: BlogPerspective) -> str:
    lines: list[str] = []

    lines.append(f"# {blog.title}")
    lines.append(f"*{blog.subtitle}*")
    lines.append("")
    lines.append(f"**Target Audience:** {blog.target_audience}")
    lines.append(f"**Angle:** {blog.angle}")
    lines.append(f"**Word Count:** ~{blog.word_count}")
    lines.append(f"**Batch:** {blog.batch_id}")
    lines.append(f"**Generated:** {blog.generated_at.strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("")
    lines.append("---")
    lines.append("")

    for section in blog.sections:
        lines.append(f"## {section.heading}")
        lines.append("")
        lines.append(section.body)
        lines.append("")
        if section.grounded_in:
            lines.append(f"*Grounded in: {'; '.join(section.grounded_in)}*")
            lines.append("")

    return "\n".join(lines)


def _render_video(script: VideoScript) -> str:
    lines: list[str] = []

    lines.append("# Video Script")
    lines.append("")
    lines.append(f"**Storytelling Style:** {script.storytelling_style}")
    lines.append(f"**Estimated Duration:** {script.estimated_duration}")
    lines.append(f"**Batch:** {script.batch_id}")
    lines.append(f"**Generated:** {script.generated_at.strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Hook")
    lines.append("")
    lines.append(f"> {script.hook}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Core Message")
    lines.append("")
    lines.append(script.core_message)
    lines.append("")
    lines.append("---")
    lines.append("")

    for scene in script.scenes:
        lines.append(f"## Scene {scene.scene_number}")
        lines.append("")
        lines.append(f"**Narration:**")
        lines.append(scene.narration)
        lines.append("")
        lines.append(f"**Visual:** {scene.visual_suggestion}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Call to Action")
    lines.append("")
    lines.append(script.call_to_action)

    return "\n".join(lines)
