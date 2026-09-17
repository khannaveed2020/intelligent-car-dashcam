"""Render a short RoadLens hackathon demo video from the deck story and sample footage."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from app.detector import YoloObjectDetector
from app.video_processor import VideoProcessor

WIDTH = 1280
HEIGHT = 720
FPS = 24
INK = (24, 34, 28)
MUTED = (104, 113, 107)
SIGNAL = (228, 87, 46)
PALE = (247, 249, 247)
LINE = (220, 226, 221)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = (
        r"C:\Windows\Fonts\bahnschrift.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
        r"/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    )
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def text_block(
    draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, size: int, fill=INK, bold=False
) -> int:
    current_y = xy[1]
    line_height = size + 11
    for line in text.splitlines():
        draw.text((xy[0], current_y), line, font=font(size, bold), fill=fill)
        current_y += line_height
    return current_y


def card(title: str, eyebrow: str, body: str, footer: str = "") -> np.ndarray:
    image = Image.new("RGB", (WIDTH, HEIGHT), (252, 253, 251))
    draw = ImageDraw.Draw(image)
    for x in range(0, WIDTH, 28):
        draw.line((x, 0, x, HEIGHT), fill=(239, 243, 239), width=1)
    for y in range(0, HEIGHT, 28):
        draw.line((0, y, WIDTH, y), fill=(239, 243, 239), width=1)
    draw.rectangle((0, 0, 16, HEIGHT), fill=SIGNAL)
    draw.text((76, 66), eyebrow.upper(), font=font(18, bold=True), fill=SIGNAL)
    draw.text((76, 122), title, font=font(50, bold=True), fill=INK)
    draw.line((76, 210, WIDTH - 76, 210), fill=LINE, width=2)
    text_block(draw, (76, 255), body, 28, fill=INK)
    if footer:
        draw.text((76, 635), footer, font=font(19), fill=MUTED)
    draw.text((WIDTH - 280, 66), "ROAD", font=font(21, bold=True), fill=INK)
    draw.text((WIDTH - 211, 66), "LENS", font=font(21, bold=True), fill=SIGNAL)
    return cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)


def demo_intro() -> np.ndarray:
    image = card(
        "From footage to finding",
        "Live product demonstration",
        "Upload a dashcam clip.\nAnalyze sampled frames locally.\nSearch the moments that matter.",
        "Real RoadLens workflow using approved dashcam footage",
    )
    return image


def demo_frame(
    frame: np.ndarray, elapsed: float, counts: dict[str, int], search_results: int
) -> np.ndarray:
    canvas = np.full((HEIGHT, WIDTH, 3), 245, dtype=np.uint8)
    canvas[:, :860] = cv2.resize(frame, (860, HEIGHT), interpolation=cv2.INTER_AREA)
    cv2.rectangle(canvas, (860, 0), (WIDTH, HEIGHT), (252, 253, 251), -1)
    cv2.line(canvas, (860, 0), (860, HEIGHT), LINE, 2)
    cv2.putText(canvas, "ROAD", (905, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.72, INK, 2, cv2.LINE_AA)
    cv2.putText(canvas, "LENS", (984, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.72, SIGNAL, 2, cv2.LINE_AA)
    cv2.putText(
        canvas, "LIVE ANALYSIS", (905, 117), cv2.FONT_HERSHEY_SIMPLEX, 0.52, SIGNAL, 1, cv2.LINE_AA
    )
    cv2.putText(
        canvas,
        f"Timestamp  {int(elapsed // 60):02d}:{int(elapsed % 60):02d}",
        (905, 164),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.58,
        INK,
        1,
        cv2.LINE_AA,
    )
    cv2.line(canvas, (905, 188), (1230, 188), LINE, 2)
    cv2.putText(
        canvas,
        "DETECTED OBJECTS",
        (905, 228),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.48,
        MUTED,
        1,
        cv2.LINE_AA,
    )
    row_y = 270
    for label, count in sorted(counts.items()):
        cv2.putText(
            canvas, label.title(), (905, row_y), cv2.FONT_HERSHEY_SIMPLEX, 0.66, INK, 1, cv2.LINE_AA
        )
        cv2.putText(
            canvas,
            str(count),
            (1170, row_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.66,
            SIGNAL,
            2,
            cv2.LINE_AA,
        )
        row_y += 42
    cv2.rectangle(canvas, (905, 470), (1230, 540), (228, 87, 46), -1)
    cv2.putText(
        canvas,
        "SEARCH:  all vehicles",
        (925, 514),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.52,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )
    cv2.putText(
        canvas,
        f"{search_results} matching moments",
        (905, 585),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.52,
        MUTED,
        1,
        cv2.LINE_AA,
    )
    cv2.putText(
        canvas,
        "Local processing  |  No upload",
        (905, 640),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.48,
        MUTED,
        1,
        cv2.LINE_AA,
    )
    return canvas


def write_clip(writer: cv2.VideoWriter, frame: np.ndarray, seconds: float) -> None:
    for _ in range(round(seconds * FPS)):
        writer.write(frame)


def render_demo(input_path: Path, output_path: Path, work_dir: Path) -> None:
    work_dir.mkdir(parents=True, exist_ok=True)
    detector = YoloObjectDetector(model_name=str(Path("yolo11n.pt")))
    events = VideoProcessor(detector).process(input_path, work_dir / "thumbnails")
    counts: dict[str, int] = {}
    for event in events:
        counts[event.label] = counts.get(event.label, 0) + 1
    vehicle_labels = {"car", "truck", "bus", "motorcycle", "bicycle"}
    vehicle_results = sum(event.label in vehicle_labels for event in events)

    writer = cv2.VideoWriter(
        str(output_path), cv2.VideoWriter_fourcc(*"mp4v"), FPS, (WIDTH, HEIGHT)
    )
    if not writer.isOpened():
        raise RuntimeError("OpenCV could not open the MP4 writer.")
    try:
        opening = card(
            "RoadLens",
            "Intelligent car dashcam",
            "Find the moments that matter\nin dashcam footage.",
            "A privacy-conscious local AI application",
        )
        write_clip(writer, opening, 4)
        write_clip(
            writer,
            card(
                "Hours of footage hide the moment that matters",
                "The problem",
                "Manual review does not scale.\n"
                "RoadLens turns long recordings into searchable, timestamped events.",
            ),
            4,
        )
        write_clip(
            writer,
            card(
                "Upload. Detect. Search. Review.",
                "The workflow",
                "01  Upload an MP4\n02  Sample frames\n"
                "03  Detect people and vehicles\n04  Search in plain language\n"
                "05  Open the matching timestamp",
            ),
            5,
        )
        write_clip(writer, demo_intro(), 3)

        capture = cv2.VideoCapture(str(input_path))
        if not capture.isOpened():
            raise RuntimeError(f"Could not open {input_path}")
        frame_index = 0
        max_frames = int(FPS * 16)
        while frame_index < max_frames:
            ok, frame = capture.read()
            if not ok:
                break
            elapsed = capture.get(cv2.CAP_PROP_POS_MSEC) / 1000
            writer.write(demo_frame(frame, elapsed, counts, vehicle_results))
            frame_index += 1
        capture.release()

        write_clip(
            writer,
            card(
                "The MVP already delivers",
                "Built for the hackathon",
                "Browser-based experience\nLocal YOLO analysis\n"
                "Timestamped thumbnails and confidence\nSearchable results\n"
                "Windows, macOS, Linux and Docker",
            ),
            5,
        )
        write_clip(
            writer,
            card(
                "Start focused, then expand",
                "What is next",
                "Today: reliable people and vehicle retrieval\n"
                "Next: grouped events, movement analysis, redaction\n"
                "Always: keep human judgement in the loop",
            ),
            4,
        )
        write_clip(
            writer,
            card(
                "Find the moment that matters",
                "Thank you",
                "RoadLens turns dashcam footage into\n"
                "searchable, timestamped evidence.\n\n"
                "Private. Searchable. Ready to trial.",
                "Sriram Iyer  •  Naveed Khan  •  Sai Krishna Bellala",
            ),
            5,
        )
    finally:
        writer.release()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", type=Path, default=Path("sample_data/855978-hd_1920_1080_30fps.mp4")
    )
    parser.add_argument("--output", type=Path, default=Path("demo/RoadLens_demo.mp4"))
    parser.add_argument("--work-dir", type=Path, default=Path("data/demo-video"))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.work_dir.exists():
        shutil.rmtree(args.work_dir)
    render_demo(args.input, args.output, args.work_dir)
    print(f"Created {args.output} ({args.output.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
