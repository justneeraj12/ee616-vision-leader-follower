from __future__ import annotations

from pathlib import Path
import shutil
import textwrap

from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = Path('/home/justneeraj/.codex/plugins/cache/openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-system-design/assets/reference.docx')
OUTPUT = ROOT / 'deliverables' / 'Neeraj_Kanchani_EE616_Project_Update_Package.docx'
WORK = ROOT / 'work' / 'professor_package'
DIAGRAM = WORK / 'architecture.png'

NAVY = '0B3153'
BLUE = '2F6F9F'
LIGHT_BLUE = 'E5F0F8'
PALE = 'F4F7FA'
MID = '60758A'
BLACK = '000000'
WHITE = 'FFFFFF'
GRID = 'D9D9D9'


def set_cell_shading(cell, fill: str):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn('w:shd'))
    if shd is None:
        shd = OxmlElement('w:shd')
        tc_pr.append(shd)
    shd.set(qn('w:fill'), fill)


def set_cell_margins(cell, top=105, start=120, bottom=105, end=120):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in('w:tcMar')
    if tc_mar is None:
        tc_mar = OxmlElement('w:tcMar')
        tc_pr.append(tc_mar)
    for tag, value in [('top', top), ('start', start), ('bottom', bottom), ('end', end)]:
        node = tc_mar.find(qn(f'w:{tag}'))
        if node is None:
            node = OxmlElement(f'w:{tag}')
            tc_mar.append(node)
        node.set(qn('w:w'), str(value))
        node.set(qn('w:type'), 'dxa')


def set_table_borders(table):
    tbl_pr = table._tbl.tblPr
    borders = tbl_pr.first_child_found_in('w:tblBorders')
    if borders is None:
        borders = OxmlElement('w:tblBorders')
        tbl_pr.append(borders)
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        tag = borders.find(qn(f'w:{edge}'))
        if tag is None:
            tag = OxmlElement(f'w:{edge}')
            borders.append(tag)
        tag.set(qn('w:val'), 'single')
        tag.set(qn('w:sz'), '6')
        tag.set(qn('w:color'), GRID)


def set_repeat_table_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement('w:tblHeader')
    tbl_header.set(qn('w:val'), 'true')
    tr_pr.append(tbl_header)


def set_run_font(run, name='Helvetica Neue', size=10.5, bold=None, color=BLACK, italic=None):
    run.font.name = name
    run._element.get_or_add_rPr().rFonts.set(qn('w:ascii'), name)
    run._element.get_or_add_rPr().rFonts.set(qn('w:hAnsi'), name)
    run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic
    run.font.color.rgb = RGBColor.from_string(color)


def add_hyperlink(paragraph, text, url):
    part = paragraph.part
    rid = part.relate_to(url, 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink', is_external=True)
    hyperlink = OxmlElement('w:hyperlink')
    hyperlink.set(qn('r:id'), rid)
    run = OxmlElement('w:r')
    r_pr = OxmlElement('w:rPr')
    color = OxmlElement('w:color')
    color.set(qn('w:val'), BLUE)
    underline = OxmlElement('w:u')
    underline.set(qn('w:val'), 'single')
    r_fonts = OxmlElement('w:rFonts')
    r_fonts.set(qn('w:ascii'), 'Helvetica Neue')
    r_fonts.set(qn('w:hAnsi'), 'Helvetica Neue')
    r_pr.extend([r_fonts, color, underline])
    run.append(r_pr)
    text_el = OxmlElement('w:t')
    text_el.text = text
    run.append(text_el)
    hyperlink.append(run)
    paragraph._p.append(hyperlink)


def clear_document_body(doc):
    body = doc._element.body
    sect_pr = body.sectPr
    for child in list(body):
        if child is not sect_pr:
            body.remove(child)


def configure_styles(doc):
    normal = doc.styles['Normal']
    normal.font.name = 'Helvetica Neue'
    normal._element.rPr.rFonts.set(qn('w:ascii'), 'Helvetica Neue')
    normal._element.rPr.rFonts.set(qn('w:hAnsi'), 'Helvetica Neue')
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = RGBColor.from_string('24384D')
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.08

    title = doc.styles['Title']
    title.font.name = 'Helvetica Neue'
    title._element.rPr.rFonts.set(qn('w:ascii'), 'Helvetica Neue')
    title._element.rPr.rFonts.set(qn('w:hAnsi'), 'Helvetica Neue')
    title.font.size = Pt(31)
    title.font.bold = True
    title.font.color.rgb = RGBColor.from_string(BLACK)
    title.paragraph_format.space_after = Pt(12)

    for style_name, size, color in [('Heading 1', 17, NAVY), ('Heading 2', 13, NAVY), ('Heading 3', 11.5, MID)]:
        style = doc.styles[style_name]
        style.font.name = 'Helvetica Neue'
        style._element.rPr.rFonts.set(qn('w:ascii'), 'Helvetica Neue')
        style._element.rPr.rFonts.set(qn('w:hAnsi'), 'Helvetica Neue')
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor.from_string(color)
        style.paragraph_format.space_before = Pt(12 if style_name == 'Heading 1' else 8)
        style.paragraph_format.space_after = Pt(5)
        style.paragraph_format.keep_with_next = True


def add_para(doc, text='', *, bold_lead=None, style=None, space_after=6, keep=False):
    p = doc.add_paragraph(style=style)
    if bold_lead and text.startswith(bold_lead):
        r1 = p.add_run(bold_lead)
        set_run_font(r1, bold=True)
        r2 = p.add_run(text[len(bold_lead):])
        set_run_font(r2)
    else:
        r = p.add_run(text)
        set_run_font(r)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.keep_with_next = keep
    return p


def add_bullet(doc, text, level=0):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.28 + 0.20 * level)
    p.paragraph_format.first_line_indent = Inches(-0.18)
    r = p.add_run('• ' + text)
    set_run_font(r)
    p.paragraph_format.space_after = Pt(3)
    return p


_NUMBER_COUNTER = 0


def reset_numbering():
    global _NUMBER_COUNTER
    _NUMBER_COUNTER = 0


def add_number(doc, text):
    global _NUMBER_COUNTER
    _NUMBER_COUNTER += 1
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.32)
    p.paragraph_format.first_line_indent = Inches(-0.22)
    r = p.add_run(f'{_NUMBER_COUNTER}.  {text}')
    set_run_font(r)
    p.paragraph_format.space_after = Pt(3)
    return p


def add_heading(doc, text, level=1):
    p = doc.add_heading(text, level=level)
    for run in p.runs:
        set_run_font(run, size={1:17, 2:13, 3:11.5}.get(level, 11), bold=True, color=NAVY if level < 3 else MID)
    p.paragraph_format.keep_with_next = True
    return p


def add_table(doc, headers, rows, widths=None, font_size=9.0):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    set_table_borders(table)
    header = table.rows[0]
    set_repeat_table_header(header)
    for idx, label in enumerate(headers):
        cell = header.cells[idx]
        set_cell_shading(cell, NAVY)
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        set_cell_margins(cell, 125, 125, 125, 125)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(label)
        set_run_font(r, size=9.3, bold=True, color=WHITE)
        if widths:
            cell.width = Inches(widths[idx])
    for row_idx, values in enumerate(rows):
        cells = table.add_row().cells
        fill = LIGHT_BLUE if row_idx % 2 == 0 else PALE
        for idx, value in enumerate(values):
            cell = cells[idx]
            set_cell_shading(cell, fill)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_margins(cell)
            if widths:
                cell.width = Inches(widths[idx])
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(str(value))
            set_run_font(r, size=font_size, color='24384D')
    doc.add_paragraph().paragraph_format.space_after = Pt(1)
    return table


def make_architecture_diagram():
    width, height = 2948, 1375
    img = Image.new('RGB', (width, height), '#F5F9FC')
    draw = ImageDraw.Draw(img)
    regular_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    bold_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    title_font = ImageFont.truetype(bold_path, 49)
    box_title_font = ImageFont.truetype(bold_path, 29)
    body_font = ImageFont.truetype(regular_path, 23)
    note_font = ImageFont.truetype(regular_path, 23)

    def box(x, y, w, h, title, subtitle, fill='#FFFFFF', edge='#0B3153'):
        draw.rounded_rectangle((x, y, x + w, y + h), radius=18, fill=fill, outline=edge, width=4)
        draw.text((x + 28, y + 22), title, font=box_title_font, fill='#0B3153')
        lines = []
        for logical_line in subtitle.split('\n'):
            lines.extend(textwrap.wrap(logical_line, width=max(14, int(w / 21))))
        draw.multiline_text((x + 28, y + 72), '\n'.join(lines), font=body_font, fill='#34495E', spacing=7)

    def arrow(x1, y1, x2, y2, color='#2F6F9F'):
        draw.line((x1, y1, x2, y2), fill=color, width=6)
        import math
        angle = math.atan2(y2 - y1, x2 - x1)
        length = 24
        spread = 0.55
        pts = [
            (x2, y2),
            (x2 - length * math.cos(angle - spread), y2 - length * math.sin(angle - spread)),
            (x2 - length * math.cos(angle + spread), y2 - length * math.sin(angle + spread)),
        ]
        draw.polygon(pts, fill=color)

    draw.rounded_rectangle((32, 28, width - 32, 156), radius=14, fill='#0B3153')
    draw.text((92, 67), 'Vision Only Leader Follower Control Architecture', font=title_font, fill='white')

    top_y, top_h = 300, 255
    top = [
        (55, 400, 'Follower RGB Camera', '640 x 480 image stream\n30 frames per second'),
        (500, 400, 'Leader Detector', 'YOLOv8 Nano\nDetection2DArray'),
        (945, 435, 'Relative Measurement', 'Bearing from image center\nRange from calibrated scale'),
        (1425, 400, 'State Estimator', 'EKF prediction and update\nRelative pose and velocity'),
        (1870, 500, 'Controller and Safety', 'PID visual servo\nTrack search and safe stop'),
        (2415, 370, 'cmd vel', 'Follower wheel\ncommands'),
    ]
    for x, w, title, subtitle in top:
        box(x, top_y, w, top_h, title, subtitle)
    for i in range(len(top) - 1):
        x1 = top[i][0] + top[i][1]
        x2 = top[i + 1][0]
        arrow(x1, top_y + top_h // 2, x2, top_y + top_h // 2)

    bottom_y, bottom_h = 800, 230
    bottom = [
        (55, 500, 'Gazebo Harmonic', 'Leader trajectory\nFollower dynamics and camera', '#E5F0F8', '#0B3153'),
        (1130, 435, 'Experiment Logger', 'Errors latency timing\nVRAM and recovery events', '#E5F0F8', '#0B3153'),
        (1665, 435, 'Follower Odometry', 'Wheel motion estimate\nTimestamped ROS 2 message', '#E5F0F8', '#0B3153'),
        (2200, 510, 'Gazebo Ground Truth', 'Evaluation only\nNever enters controller', '#FFF6E8', '#A76D10'),
    ]
    for x, w, title, subtitle, fill, edge in bottom:
        box(x, bottom_y, w, bottom_h, title, subtitle, fill, edge)

    # Simulator supplies the camera; odometry supplies only the estimator.
    arrow(250, bottom_y, 250, top_y + top_h)
    arrow(1882, bottom_y, 1625, top_y + top_h)
    # Commands close the physical simulation loop without entering evaluation.
    arrow(2600, top_y + top_h, 2600, 690)
    draw.line((2600, 690, 300, 690), fill='#2F6F9F', width=6)
    arrow(300, 690, 300, bottom_y)
    # Evaluation data flows only into the experiment logger.
    arrow(2200, bottom_y + bottom_h // 2, 1565, bottom_y + bottom_h // 2, '#A76D10')
    arrow(1162, top_y + top_h, 1320, bottom_y)
    arrow(1625, top_y + top_h, 1450, bottom_y)

    draw.text((86, 1160),
              'Experimental boundary  Each follower uses only its namespaced camera and odometry. Ground truth is recorded only for evaluation.',
              font=note_font, fill='#34495E')
    img.save(DIAGRAM, quality=95)


def add_reference(doc, number, citation, url):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.18)
    p.paragraph_format.first_line_indent = Inches(-0.18)
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(f'[{number}] {citation} ')
    set_run_font(r, size=9.2)
    add_hyperlink(p, url, url)


def build():
    WORK.mkdir(parents=True, exist_ok=True)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    make_architecture_diagram()
    shutil.copy2(REFERENCE, OUTPUT)
    doc = Document(OUTPUT)
    clear_document_body(doc)
    configure_styles(doc)

    section = doc.sections[0]
    section.top_margin = Inches(0.70)
    section.bottom_margin = Inches(0.62)
    section.left_margin = Inches(0.70)
    section.right_margin = Inches(0.70)

    # Cover
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(98)
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run('EE 616 Project Update')
    set_run_font(r, size=22, color=MID)

    title = doc.add_paragraph(style='Title')
    title.add_run('Vision Only Leader Follower Coordination on Constrained Edge Hardware')
    title.alignment = WD_ALIGN_PARAGRAPH.LEFT
    title.paragraph_format.space_after = Pt(12)
    for run in title.runs:
        set_run_font(run, size=31, bold=True, color=BLACK)

    subtitle = doc.add_paragraph()
    sr = subtitle.add_run('Revised scope and preliminary results plan for faculty review')
    set_run_font(sr, size=14, color='34495E')
    subtitle.paragraph_format.space_after = Pt(80)

    meta = doc.add_table(rows=1, cols=3)
    # The metadata strip is visually a set of labeled columns. Mark its first
    # row as a repeating header so screen readers receive equivalent structure.
    set_repeat_table_header(meta.rows[0])
    meta.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta.autofit = False
    labels = [('STATUS', 'Proposed for review'), ('OWNER', 'Neeraj Kumar Kanchani'), ('LAST UPDATED', 'September 15, 2026')]
    for i, (label, value) in enumerate(labels):
        cell = meta.rows[0].cells[i]
        set_cell_margins(cell, 80, 40, 80, 40)
        cell.width = Inches(2.35)
        p1 = cell.paragraphs[0]
        p1.paragraph_format.space_after = Pt(4)
        a = p1.add_run(label)
        set_run_font(a, size=8.5, bold=True, color=MID)
        p2 = cell.add_paragraph()
        p2.paragraph_format.space_after = Pt(0)
        b = p2.add_run(value)
        set_run_font(b, size=10.2, color='24384D')

    doc.add_paragraph().paragraph_format.space_after = Pt(6)
    add_table(doc, ['Field', 'Details'], [
        ('Candidate', 'Neeraj Kumar Kanchani'),
        ('Faculty reviewer', 'Professor Masudul Imtiaz'),
        ('Course', 'EE 616-57, section 9189, four credits'),
        ('Target completion', 'First week of December 2026'),
        ('Scope', 'Simulation-only decentralized leader-follower perception and control using ROS 2 Jazzy and Gazebo Harmonic'),
    ], widths=[1.45, 5.55], font_size=9.2)

    doc.add_page_break()

    add_heading(doc, '1 Executive Summary and Review Request')
    add_para(doc,
        'I propose a simulation-only study of decentralized leader-follower coordination on constrained edge hardware. '
        'A follower autonomous mobile robot will use a forward-facing RGB camera and its own wheel odometry to estimate the relative state of a leader, maintain a commanded formation, and recover after short visual occlusions. ROS 2 namespaces will isolate each robot. Gazebo ground truth will be recorded for evaluation and will never enter the control path.')
    add_para(doc,
        'This revision narrows my earlier warehouse intersection-negotiation idea, which included LiDAR and stereo fusion. The narrower scope makes the research question measurable within the available semester while preserving the main themes of decentralized perception, edge inference, state estimation, and autonomous control.')
    add_para(doc,
        'Review requested. ', bold_lead='Review requested. ')
    add_para(doc,
        'I am asking for confirmation that this revised scope is suitable for EE 616 before I proceed beyond the preliminary baseline. The first evidence package will compare monocular range and bearing estimates with simulator ground truth and report latency, tracking error, and GPU memory use.')

    add_heading(doc, '2 Academic Context and Scope')
    add_para(doc,
        'Professor Imtiaz advised me to begin reading and prepare preliminary results or figures before scheduling a meeting. This package responds with a narrowed technical scope, a first experiment that can produce reviewable figures, and explicit decision gates before implementation expands.')
    add_table(doc, ['Included in the proposed study', 'Excluded from the proposed study'], [
        ('One leader and one follower as the minimum validated system', 'Physical robot deployment during this course'),
        ('Namespace-safe design that can launch additional followers', 'Global mapping, SLAM, GPS, or centralized fleet control'),
        ('RGB detection, relative state estimation, EKF, PID, and recovery logic', 'LiDAR and stereo fusion from the earlier concept'),
        ('Gazebo experiments, repeatable datasets, plots, and resource benchmarks', 'Claims of real-world safety or production certification'),
    ], widths=[3.5, 3.5], font_size=9.1)

    doc.add_page_break()

    add_heading(doc, '3 Research Questions and Hypotheses')
    add_para(doc, 'Primary research question. ', bold_lead='Primary research question. ')
    add_para(doc,
        'How accurately and reliably can a resource-constrained follower robot maintain a leader-relative formation using only monocular RGB detections and local odometry under changes in range, heading, velocity, and short visual occlusion?')
    add_table(doc, ['Hypothesis', 'Testable claim', 'Evidence'], [
        ('H1 Relative perception', 'A calibrated monocular model will estimate leader range and bearing with bounded error over the declared operating envelope.', 'Range RMSE, bearing MAE, bias, and 95th-percentile error against Gazebo ground truth'),
        ('H2 State estimation', 'An EKF will reduce tracking error and bridge short detection gaps more effectively than raw measurements.', 'Paired trials comparing raw, filtered, and prediction-only intervals'),
        ('H3 Edge optimization', 'Reduced-precision inference will lower latency and memory use without materially degrading closed-loop tracking.', 'FP32, FP16, and INT8 detector and closed-loop benchmarks'),
    ], widths=[1.35, 3.5, 2.25], font_size=8.8)

    doc.add_page_break()

    add_heading(doc, '4 Proposed Architecture')
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.add_picture(str(DIAGRAM), width=Inches(7.05))
    doc_pr = run._element.xpath('.//wp:docPr')
    if doc_pr:
        doc_pr[0].set('descr', 'ROS 2 leader-follower architecture showing perception, estimation, control, simulator, and evaluation-only ground truth flows')
    p.paragraph_format.space_after = Pt(3)
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cr = cap.add_run('Figure 1  Proposed ROS 2 computational architecture and experimental boundary')
    set_run_font(cr, size=9.2, italic=True, color=MID)
    cap.paragraph_format.space_after = Pt(8)

    add_heading(doc, 'Component Responsibilities', level=2)
    add_table(doc, ['Component', 'Input and responsibility', 'Output', 'Failure behavior'], [
        ('Camera bridge', 'Gazebo RGB frames with timestamps', 'sensor_msgs Image', 'Marks stale frames and exposes drop counts'),
        ('Leader detector', 'Image stream; detect the leader rear profile', 'vision_msgs Detection2DArray', 'Publishes empty detection with timestamp'),
        ('Relative measurement', 'Bounding box and camera calibration', 'Range, bearing, covariance', 'Rejects invalid geometry and low confidence'),
        ('EKF estimator', 'Visual measurement and follower odometry', 'Relative pose, velocity, covariance', 'Prediction-only mode for bounded gaps'),
        ('Supervisor', 'Detection health, covariance, and timeouts', 'TRACK, SEARCH, or SAFE STOP state', 'Commands safe stop when uncertainty exceeds limit'),
        ('PID controller', 'Filtered range and bearing errors', 'geometry_msgs Twist', 'Velocity and acceleration limits remain active'),
        ('Experiment logger', 'Ground truth and all pipeline telemetry', 'Versioned CSV and rosbag', 'Fails the trial if required evidence is missing'),
    ], widths=[1.15, 2.55, 1.5, 1.9], font_size=8.1)

    doc.add_page_break()

    add_heading(doc, 'Timing and Isolation', level=2)
    add_para(doc,
        'Camera measurements are expected at up to 30 Hz, while the estimator and controller will run at a nominal 50 Hz using predictions between images. Separate callback groups and measured deadline statistics will isolate control work from variable detector latency. A MultiThreadedExecutor enables concurrency but does not by itself guarantee real-time scheduling. Each follower will consume only topics within its namespace; an automated graph audit will flag cross-namespace dependencies.')

    add_heading(doc, '5 Preliminary Experiment for the First Faculty Meeting')
    add_para(doc,
        'The first experiment will validate the measurement model before the detector, EKF, and controller are integrated. A Gazebo leader model with known dimensions will be placed at controlled ranges and headings. The follower camera will record image geometry while Gazebo publishes ground truth to the evaluation logger only.')
    add_table(doc, ['Element', 'Definition'], [
        ('Independent variables', 'Range 0.75 to 3.00 m; relative heading -30 to +30 degrees; three lighting levels; centered and off-axis placement'),
        ('Measurements', 'Bounding-box center, width, height, area, timestamp, camera intrinsics, and Gazebo relative pose'),
        ('Baselines', 'Analytic pinhole-inspired scale model and a fitted regression using held-out calibration poses'),
        ('Controls', 'Fixed target model, camera resolution, focal parameters, random seed, and simulation step size'),
        ('Repetitions', 'At least five seeded trials per condition after a short deterministic smoke-test grid'),
        ('Outputs', 'Tidy CSV, configuration manifest, plots, summary statistics, and a reproducible launch command'),
    ], widths=[1.55, 5.45], font_size=9.0)

    add_heading(doc, 'Planned Preliminary Figures', level=2)
    reset_numbering()
    add_number(doc, 'Estimated range versus Gazebo ground-truth range with an identity line and 95 percent confidence intervals.')
    add_number(doc, 'Range residuals by distance and heading to reveal calibration bias and field-of-view effects.')
    add_number(doc, 'End-to-end measurement latency and peak memory use for the baseline pipeline.')
    add_number(doc, 'Example camera frames showing valid, marginal, and rejected bounding-box geometry.')

    add_heading(doc, 'Decision Rule', level=2)
    add_para(doc,
        'The project proceeds to learned detection only if the calibrated geometry is identifiable and repeatable over the operating envelope. If range error grows beyond the proposed bound at oblique views, the scope will either narrow the allowable heading or replace box area with a target-specific apparent-width model. This decision will be documented before controller development.')

    doc.add_page_break()

    add_heading(doc, '6 Evaluation Plan and Proposed Targets')
    add_para(doc,
        'The values below are proposed engineering targets for discussion. They are not measured results and may be revised after the preliminary baseline.')
    add_table(doc, ['Measure', 'Proposed target', 'Evaluation window'], [
        ('Relative range error', 'RMSE at or below 0.20 m', '0.75 to 3.00 m operating range'),
        ('Relative bearing error', 'Mean absolute error at or below 5 degrees', '-30 to +30 degrees'),
        ('Nominal formation error', 'Distance RMSE at or below 0.25 m and yaw MAE at or below 7 degrees', 'Straight and S-curve trajectories'),
        ('Perception timing', 'At least 15 Hz and p95 latency at or below 67 ms', 'Gazebo and detector running concurrently'),
        ('Control timing', '50 Hz nominal with fewer than 1 percent missed periods', 'Each complete trajectory trial'),
        ('Occlusion recovery', 'Median reacquisition at or below 3 s', '0.5 to 1.5 s partial occlusions'),
        ('Safety', 'Zero collisions in the declared test matrix', 'Minimum 30 seeded closed-loop trials'),
        ('Resource use', 'No OOM; peak GPU memory at or below 3.6 GiB', '15-minute integrated stress run'),
    ], widths=[1.45, 2.75, 2.8], font_size=8.5)

    add_heading(doc, 'Experimental Comparisons', level=2)
    add_table(doc, ['Factor', 'Levels'], [
        ('Estimator', 'Raw measurement; EKF; EKF with prediction during dropout'),
        ('Inference precision', 'Reference FP32; TensorRT FP16; TensorRT INT8 if supported and accurate'),
        ('Trajectory', 'Static; linear acceleration; sharp turn; S-curve; partial occlusion'),
        ('Perception disturbance', 'Nominal; motion blur; reduced light; dropped frames'),
    ], widths=[1.65, 5.35], font_size=9.0)

    doc.add_page_break()

    add_heading(doc, '7 Evidence and Data Contracts')
    add_para(doc,
        'Every trial will be reproducible from a configuration file and seed. The evaluator will record synchronized perception, estimation, command, ground-truth, and resource data. Ground truth remains outside the controller so evaluation cannot leak privileged information into the autonomy stack.')
    add_table(doc, ['Field group', 'Required contents', 'Purpose'], [
        ('Trial identity', 'run_id, git_commit, configuration_hash, seed, start_time', 'Reproduce and audit each result'),
        ('Perception', 'frame_stamp, confidence, box center, width, height, inference_ms', 'Evaluate detection and timing'),
        ('Estimation', 'range, bearing, velocities, covariance, estimator_mode', 'Compare estimates with ground truth'),
        ('Control', 'state, distance_error, yaw_error, linear_cmd, angular_cmd', 'Explain closed-loop behavior'),
        ('Ground truth', 'relative pose and relative velocity', 'Compute accuracy metrics only'),
        ('Resources', 'CPU, RAM, GPU memory, dropped frames, missed periods', 'Verify edge constraints'),
    ], widths=[1.35, 3.8, 1.85], font_size=8.7)

    add_heading(doc, '8 Hardware and Implementation Constraints')
    add_table(doc, ['Constraint', 'Observed baseline', 'Design response'], [
        ('Host', 'MSI Katana GF66 12UD; Intel Core i5-12450H; 16 GB RAM', 'Keep simulation-only scope and profile CPU callback timing'),
        ('GPU', 'RTX 3050 Ti Laptop GPU with 4 GB VRAM', 'Small detector, reduced precision, bounded image size, headless benchmark mode'),
        ('Storage', 'Approximately 294 GB free on NVMe', 'Retain selected rosbags; store derived CSVs and manifests in Git'),
        ('Software', 'Ubuntu 24.04; partial ROS 2 Jazzy installation; CUDA 12.0', 'Create a pinned setup script and validate GPU access before ML integration'),
        ('Current gap', 'ROS 2 CLI, Gazebo Harmonic, and inference runtimes are not yet available in the checked environment', 'Complete an environment smoke test as the first approved implementation milestone'),
    ], widths=[1.2, 2.55, 3.25], font_size=8.7)
    add_para(doc,
        'The implementation will maintain a CPU-compatible evaluation path where practical. This prevents a GPU driver or TensorRT installation problem from blocking data analysis and lets the optimized backend be compared with a reference backend.')

    add_heading(doc, '9 Milestones and Approval Gates')
    add_para(doc,
        'Each implementation milestone begins only after Neeraj approves its scope, acceptance criteria, tests, and documentation changes. Professor confirmation is required before the project moves from preliminary evidence to the full integrated research plan.')
    add_table(doc, ['Dates', 'Milestone and deliverable', 'Exit evidence'], [
        ('Sep 14 to Sep 20', 'M0 Scope, architecture, environment, and reproducibility baseline', 'Professor package; clean ROS and Gazebo smoke test; system diagnostic report'),
        ('Sep 21 to Oct 4', 'M1 Simulation world and calibrated relative-measurement experiment', 'Ground-truth comparison CSV and first four figures'),
        ('Oct 5 to Oct 18', 'M2 Learned detector and EKF estimator', 'Held-out detector metrics; raw versus filtered ablation'),
        ('Oct 19 to Oct 31', 'M3 Integrated controller, recovery states, and beta demonstration', 'Repeatable nominal and occlusion trials; October 31 integration review'),
        ('Nov 1 to Nov 15', 'M4 FP16 and INT8 optimization and adversarial evaluation', 'Latency, accuracy, memory, and closed-loop comparison'),
        ('Nov 16 to Nov 29', 'M5 Repeat experiments, thesis draft, and demonstration video', 'Frozen dataset; reproducible plots; complete draft and recorded demo'),
        ('Nov 30 to Dec 4', 'M6 Final corrections and submission', 'Faculty-requested revisions incorporated; archived release'),
    ], widths=[1.3, 3.7, 2.0], font_size=8.4)

    doc.add_page_break()

    add_heading(doc, '10 Risks and Mitigations')
    add_table(doc, ['Risk', 'Why it matters', 'Mitigation and decision point'], [
        ('Scope ambiguity', 'The earlier LiDAR and stereo negotiation idea differs from the vision-only document.', 'Ask Professor Imtiaz to confirm the revised research question before full implementation.'),
        ('The word swarm overstates validation', 'A single leader-follower pair does not demonstrate swarm behavior.', 'Use coordination in the title; make multi-follower support an extension after the pair is validated.'),
        ('Monocular range bias', 'Bounding-box scale varies with heading, detection jitter, and partial visibility.', 'Calibrate first; quantify residuals; narrow the envelope or change the measurement model if needed.'),
        ('Field-of-view loss', 'Sharp turns can break the feedback loop.', 'Use confidence and covariance gates, bounded prediction, SEARCH, and SAFE STOP states.'),
        ('GPU memory exhaustion', 'Gazebo rendering and inference share 4 GB VRAM.', 'Start with FP16, record peak memory, use headless trials, then evaluate INT8.'),
        ('Timing claims', 'A multi-threaded executor does not guarantee a strict 50 Hz loop.', 'Measure callback periods and missed deadlines; avoid unverified real-time claims.'),
        ('Synthetic-only evidence', 'Simulator accuracy may not transfer to physical robots.', 'State the limitation; vary lighting, blur, occlusion, and model appearance; exclude deployment claims.'),
        ('Schedule compression', 'Integration failures could consume the thesis-writing period.', 'Freeze the integrated beta on October 31 and protect November for experiments and writing.'),
    ], widths=[1.45, 2.5, 3.05], font_size=8.4)

    doc.add_page_break()

    add_heading(doc, '11 Related Work and Technical Foundations')
    add_table(doc, ['Source', 'Relevant contribution', 'Use in this project'], [
        ('Hutchinson, Hager, and Corke, 1996', 'Foundational visual-servo control framework', 'Frames image-derived error as feedback for robot motion'),
        ('Vaitheeswaran et al., 2015', 'Camera-guided leader-follower ground vehicles', 'Provides a direct historical baseline for vision-only following'),
        ('Bateux et al., 2017', 'Learning-based visual servoing with synthetic perturbations', 'Supports simulator-generated training and occlusion experiments'),
        ('Santjoko et al., 2026', 'Leader-follower control with explicit field-of-view safety', 'Motivates treating visibility as a control and recovery constraint'),
        ('ROS 2 and Gazebo documentation', 'Supported Jazzy and Harmonic integration with bridge interfaces', 'Defines the reproducible simulation and message boundary'),
        ('NVIDIA TensorRT documentation', 'Explicit reduced-precision inference and accuracy tradeoffs', 'Defines the FP16 and INT8 benchmark methodology'),
    ], widths=[1.7, 2.55, 2.75], font_size=8.3)

    add_heading(doc, '12 Decisions Requested from Professor Imtiaz')
    reset_numbering()
    add_number(doc, 'Is the revised vision-only, simulation-only scope appropriate for the four-credit EE 616 project?')
    add_number(doc, 'Should the required validation remain one leader and one follower, or should two followers be required to justify the term swarm?')
    add_number(doc, 'Are the proposed preliminary figures sufficient for the first progress meeting?')
    add_number(doc, 'Are there department-specific thesis, demonstration, or repository requirements that should be added now?')

    add_heading(doc, 'Recommended Decision and Immediate Next Step')
    add_para(doc,
        'Approve the revised scope for a preliminary baseline only. The immediate technical task is the calibrated monocular range-and-bearing experiment in Gazebo. Full detector, EKF, and controller implementation should follow after the first evidence is reviewed and the project scope is confirmed.')

    doc.add_page_break()

    add_heading(doc, 'Appendix A Draft Email to Professor Imtiaz')
    add_para(doc, 'Subject: EE 616 revised project scope and preliminary results plan', keep=True)
    add_para(doc, 'Hello Professor Imtiaz,')
    add_para(doc,
        'Following your recommendation, I have continued reading and refined the project into a simulation-focused study of vision-based leader-follower robot coordination on constrained edge hardware.')
    add_para(doc,
        'The revised scope uses ROS 2 Jazzy and Gazebo Harmonic. A follower robot will estimate the relative distance and heading of a leader using only an RGB camera and its own wheel odometry. An extended Kalman filter will smooth the relative-state estimate, and a visual-servo controller will maintain the desired formation and handle short visual occlusions. Gazebo ground truth will be used only to evaluate the estimates and controller.')
    add_para(doc,
        'This scope is narrower than my earlier LiDAR and stereo intersection-negotiation proposal. The narrower study gives me a clearer research question and makes it possible to produce controlled, repeatable results within the project period.')
    add_para(doc, 'For the preliminary evidence, I plan to prepare:')
    reset_numbering()
    add_number(doc, 'A system architecture and ROS 2 computational-graph figure.')
    add_number(doc, 'A comparison of monocular range and bearing estimates with Gazebo ground truth.')
    add_number(doc, 'Initial perception latency and GPU memory measurements on my laptop.')
    add_number(doc, 'A proposed matrix for tracking, sharp-turn, and occlusion-recovery experiments.')
    add_para(doc,
        'Could you please confirm whether this revised scope is appropriate for EE 616 before I proceed with the full implementation? I have attached the project update package for your review.')
    add_para(doc, 'Regards,\nNeeraj Kumar Kanchani')

    doc.add_page_break()

    add_heading(doc, 'Appendix B References')
    add_reference(doc, 1, 'Open Robotics. Gazebo Harmonic feature comparison and ROS 2 Jazzy integration.', 'https://gazebosim.org/docs/harmonic/comparison/')
    add_reference(doc, 2, 'Open Robotics. Using ROS 2 to interact with Gazebo.', 'https://gazebosim.org/docs/harmonic/ros2_integration/')
    add_reference(doc, 3, 'ROS 2 vision_msgs documentation for standardized detector messages.', 'https://docs.ros.org/en/jazzy/p/vision_msgs/')
    add_reference(doc, 4, 'NVIDIA. TensorRT quantization schemes.', 'https://docs.nvidia.com/deeplearning/tensorrt/latest/inference-library/quantized-types-schemes.html')
    add_reference(doc, 5, 'S. Hutchinson, G. D. Hager, and P. I. Corke. A Tutorial on Visual Servo Control. IEEE Transactions on Robotics and Automation, 12(5), 1996.', 'https://doi.org/10.1109/70.538972')
    add_reference(doc, 6, 'S. M. Vaitheeswaran, Bharath M. K., and Gokul M. Leader Follower Formation Control of Ground Vehicles Using Camshift Based Guidance, 2015.', 'https://arxiv.org/abs/1501.01364')
    add_reference(doc, 7, 'Q. Bateux, E. Marchand, J. Leitner, F. Chaumette, and P. Corke. Visual Servoing from Deep Neural Networks, 2017.', 'https://arxiv.org/abs/1705.08940')
    add_reference(doc, 8, 'I. R. Santjoko, R. R. Suganda, M. Pan, and B. Hu. Distributed 3D Leader-Follower Formation Control with Field-of-View Safety via Control Barrier Functions, 2026.', 'https://arxiv.org/abs/2605.17533')

    # Replace footer text while preserving footer layout where possible.
    for sec in doc.sections:
        for footer in [sec.footer, sec.first_page_footer, sec.even_page_footer]:
            for p in footer.paragraphs:
                if p.text.strip():
                    for run in p.runs:
                        run.text = ''
                    r = p.add_run('EE 616 Project Update | Neeraj Kumar Kanchani')
                    set_run_font(r, size=8.3, color=MID)
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Document metadata
    props = doc.core_properties
    props.title = 'EE 616 Vision Only Leader Follower Coordination Project Update'
    props.subject = 'Revised scope and preliminary results plan for faculty review'
    props.author = 'Neeraj Kumar Kanchani'
    props.keywords = 'ROS 2, Gazebo, leader follower, visual servoing, edge inference, EE 616'
    props.comments = 'Prepared for review by Professor Masudul Imtiaz'

    doc.save(OUTPUT)
    print(OUTPUT)


if __name__ == '__main__':
    build()
