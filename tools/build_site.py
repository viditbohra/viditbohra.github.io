"""Generate the site: index.html plus one page per project.

All the words live in this file. Edit the content below and re-run:

    python tools/build_site.py

Six project pages share the same shell, so generating them keeps the header,
navigation and gallery markup identical across all of them instead of drifting
apart the way six hand edited copies would.

Gallery tiles are sized from each image's real shape, read from
assets/dimensions.json, which build_media.py writes. That is what lets a row of
mixed portrait and landscape media sit flush instead of leaving holes.
"""

import hashlib
import html
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EMAIL = "bohravidit@gmail.com"
GITHUB = "https://github.com/viditbohra"

DIMS = json.loads((ROOT / "assets" / "dimensions.json").read_text())

# ── Content ──────────────────────────────────────────────────────────────

TAGLINE = [
    "Mechanical engineering undergraduate at IIT Bombay, minoring in Artificial "
    "Intelligence and Data Science, and in Systems and Control.",
    "I build robots: the mechanisms, the control and estimation that run them, and "
    "the parts themselves.",
]

EDUCATION = [
    {
        "title": "B.Tech, Mechanical Engineering",
        "org": "Indian Institute of Technology Bombay",
        "when": "2024 to 2028",
        "points": [
            "CPI 8.58",
            "Minor in Artificial Intelligence and Data Science",
            "Minor in Systems and Control",
        ],
    },
    {"title": "HSC", "org": "Pace Junior Science College, Dadar", "when": "2024",
     "points": ["86.67%"]},
    {"title": "ICSE", "org": "Campion School", "when": "2022",
     "points": ["96.20%"]},
]

EXPERIENCE = [
    {
        "title": "Subsystem Lead, Robotic Arm and LDT",
        "org": "Mars Rover Team, IIT Bombay",
        "when": "Apr 2026 to present",
        "points": [
            "Leading 15 undergraduates on a multi functional robotic arm",
            "Built around belt drives, BLDC motors and a two stage planetary and cycloidal gearbox",
            "Mentoring the quadruped and hexapod builds from concept to working prototype",
        ],
    },
    {
        "title": "Research Intern",
        "org": "GV Lab, University of Tokyo",
        "when": "Jun 2026 to Jul 2026",
        "points": [
            "Built a human to robot motion retargeting pipeline under Prof. Gentiane Venture",
            "Deployed it on a Pepper humanoid and a UR5 arm",
        ],
    },
    {
        "title": "Senior Design Engineer, Robotic Arm Subsystem",
        "org": "Mars Rover Team, IIT Bombay",
        "when": "Apr 2025 to Apr 2026",
        "points": [
            "Designed the 5-DOF arm and its full drivetrain",
            "Custom two stage 81:1 cycloidal drive, and a 2-DOF differential wrist 35% lighter than the version it replaced",
            "Worm drive in the explicit steering so joints hold position with no power applied",
        ],
    },
    {
        "title": "Convener",
        "org": "Krittika, Astronomy Club, IIT Bombay",
        "when": "May 2025 to Mar 2026",
        "points": [
            "Designed a custom 2-DOF stand for the EdgeHD11 telescope in the institute observatory",
            "Led a learners' space session on coordinate systems and time",
            "Ran outreach reaching over 10,000 people on National Space Day",
        ],
    },
]

SKILLS = [
    ("Design and simulation",
     "SolidWorks, ANSYS, ANSYS Fluent, COMSOL, Fusion 360, MSC Adams, MATLAB, Simulink, Simscape Multibody"),
    ("Robotics", "ROS2, Isaac Lab, Holosoma, Gazebo, MuJoCo"),
    ("Programming", "C, C++, Python, SQL, LaTeX"),
]

PROJECTS = [
    {
        "slug": "retargeting",
        "title": "Human to Robot Motion Retargeting",
        "org": "GV Lab, University of Tokyo",
        "when": "Jun 2026 to Jul 2026",
        "summary": "Turning a phone video of a person handling an object into motion a robot can reproduce.",
        "tags": ["HMR2 / 4D-Humans", "SMPL", "Holosoma", "Inverse kinematics", "Python"],
        "cover": ("video", "pepper-sim", "A Pepper humanoid reproducing a captured human motion in simulation"),
        "body": [
            "An end to end pipeline that takes an ordinary monocular RGB video of someone "
            "handling an object and produces motion a robot can actually execute. Human pose "
            "comes from HMR2 (4D-Humans), joint positions are extracted through SMPL, and the "
            "motion is retargeted onto the robot using inverse kinematics in Holosoma. It runs "
            "on both a Pepper humanoid and a UR5 arm.",
            "The hard part is what gets preserved. Copying joint angles between bodies with "
            "different proportions breaks the task, because the hand ends up in the wrong place "
            "relative to the object. This pipeline uses an interaction mesh formulation that "
            "encodes the spatial relationship between the human and the object, so the "
            "retargeted motion keeps the manipulation intact rather than just the pose.",
        ],
        "gallery": [
            ("video", "pepper-arms", "Retargeted arm motion on the Pepper humanoid."),
            ("video", "ur5-arm", "The same pipeline driving a UR5 arm."),
            ("video", "humanoid-sim", "A full humanoid reproducing the captured motion."),
            ("video", "smpl-body", "The SMPL body model recovered from the human motion."),
            ("plot", "point-cloud", "Cleaned point cloud of the object, XZ and XY projections."),
        ],
    },
    {
        "slug": "mars-rover-arm",
        "title": "Mars Rover Robotic Arm",
        "org": "Mars Rover Team, IIT Bombay",
        "when": "Oct 2024 to present",
        "summary": "A 5-DOF manipulator for a competition rover, built around a custom cycloidal drive.",
        "tags": ["SolidWorks", "Cycloidal drive", "ANSYS", "3D printing", "MSC Adams"],
        "cover": ("image", "rover-field", "The completed rover with its robotic arm deployed on a competition course"),
        "body": [
            "The manipulator on a semi autonomous rover built by a 30 person team to cross rough "
            "terrain and perform dexterous tasks at international competitions. I designed the "
            "5-DOF arm and reworked most of its drivetrain, including a custom two stage 81:1 "
            "cycloidal drive for torque density and a 2-DOF differential wrist redesigned as a "
            "3D print that came out 35% lighter and much easier to manufacture.",
            "Each joint uses explicit steering, so a commanded angle maps to one actuator rather "
            "than being shared across a coupled linkage, which keeps the control predictable. I "
            "implemented a worm drive in the explicit steering for better control and "
            "robustness. A worm cannot be back driven, so a joint holds its position under load "
            "and stays where it is if power is lost, instead of collapsing under the weight of "
            "the arm.",
            "The linear base needed its own fix. Scaled up, it kept binding on tolerance stack "
            "up, so the rails were redesigned around the principle used in optical disk drives "
            "to take the over constraint out.",
            "With this rover the team placed 2nd at the European Rover Challenge against 24 "
            "teams from 15 countries, took 1st in the Astrobiology Mission at the International "
            "Rover Challenge, and finished 9th overall in the IRC against more than 35 "
            "institutions worldwide.",
        ],
        "gallery": [
            ("image", "arm-cad", "The full 5-DOF arm in CAD, with the linear base and gripper."),
            ("image", "cycloidal-drive", "The two stage 81:1 cycloidal drive."),
            ("image", "wrist-assembly", "The 2-DOF differential wrist, assembled."),
            ("image", "wrist-build", "The wrist with its lead screw and gripper drive."),
            ("image", "rover-cad", "Full rover chassis in CAD."),
            ("video", "wrist-cad", "The 2-DOF differential wrist in CAD."),
            ("video", "linear-base-cad", "Linear base motion study."),
            ("video", "linear-base-demo", "The linear base running on hardware."),
        ],
    },
    {
        "slug": "bipedal-robot",
        "title": "Robo Sapien, a Bipedal Robot",
        "org": "Institute Technical Summer Project, IIT Bombay",
        "when": "May 2025 to present",
        "summary": "A 6-DOF walking robot with a reinforcement learning policy trained in Isaac Lab.",
        "tags": ["Isaac Lab", "PPO", "Simulink", "LQR", "Arduino", "FDM printing"],
        "cover": ("image", "hardware", "The assembled bipedal robot in red printed parts, standing on a bench"),
        "body": [
            "A 6-DOF biped built from scratch after a literature review of existing walking "
            "robots set the baseline requirements. The frame uses lightweight carbon fibre tubes "
            "to keep mass down, limit sensors for joint homing, and a rack and pinion assembly "
            "that shifts the centre of mass predictably instead of relying on the legs alone to "
            "stay upright.",
            "Control was approached three ways. A PPO policy trained in Isaac Lab, with a multi "
            "term reward covering velocity tracking, feet air time and joint limit penalties, "
            "produced a stable walking gait in simulation. A state space model fitted from "
            "Simscape at 85% fit drove a data driven controller in Simulink. And an LQR "
            "controller on a linear inverted pendulum model produced a stable gait analytically. "
            "On hardware, inverse kinematics and PID loops on an Arduino Mega with an MPU6050 "
            "handle real time balance.",
        ],
        "gallery": [
            ("image", "cad-render", "The biped in CAD, trussed throughout to cut mass."),
            ("video", "rl-policy", "The trained PPO policy walking in Isaac Lab."),
            ("video", "data-driven-control", "The data driven controller running in simulation."),
            ("video", "hardware-test", "Hardware test."),
            ("plot", "simscape-model", "The Simscape multibody model."),
        ],
    },
    {
        "slug": "state-estimation",
        "title": "State Estimation on Lie Groups",
        "org": "SC651, Prof. Ravi Banavar, IIT Bombay",
        "when": "Aug 2025 to present",
        "summary": "Attitude estimation on Lie groups, extended into visual inertial odometry on a rig I built.",
        "tags": ["Lie groups", "Kalman", "Mahony", "Allan deviation", "RP2040", "Python"],
        "cover": ("image", "camera-imu-rig", "A hand holding the custom camera and IMU rig built on a printed plate"),
        "body": [
            "This started as coursework in estimation on Lie groups: implementing the Kalman "
            "filter, TRIAD and QUEST on an IMU to get a stable attitude estimate by fusing "
            "gyroscope, accelerometer and magnetometer data. I then implemented the Mahony "
            "filter and compared it systematically against TRIAD and QUEST, which gave a 40% "
            "lower standard deviation in the output.",
            "It has since grown into a visual inertial setup on hardware I built, an RP2040 Pico "
            "with an IMX335 camera and an MPU6050, characterised with an Allan deviation "
            "analysis to pin down the gyro and accelerometer noise parameters. The filter "
            "estimates the camera trajectory and a landmark map together from the fused visual "
            "and inertial stream.",
        ],
        "gallery": [
            ("image", "rig-detail", "The rig set up for a capture run."),
            ("video", "vio-run", "A live run with tracked features and the state estimate overlaid."),
            ("plot", "trajectory", "Estimated path coloured by time, with the recovered landmarks."),
            ("plot", "landmark-map", "The resulting 3D landmark map."),
            ("plot", "allan-deviation", "Allan deviation for all six IMU axes. This sets the noise model the filter uses."),
        ],
    },
    {
        "slug": "support-free-printing",
        "title": "Support Free 3D Printing",
        "org": "ME230, Prof. Ramesh Singh, IIT Bombay",
        "when": "Jan 2026 to Apr 2026",
        "summary": "Printing 90 degree overhangs with no support material, on an unmodified 3-axis printer.",
        "tags": ["Python", "G-code", "Non planar slicing", "FDM", "SolidWorks"],
        "cover": ("image", "printed-part", "A black 3D printed pipe with a 90 degree overhang, printed without supports"),
        "body": [
            "Printing a 90 degree overhang normally means printing supports, then cutting them "
            "off and cleaning up the scar they leave behind. This project prints them with no "
            "support at all, on an unmodified 3-axis FDM printer with no hardware changes.",
            "All of the work happens in software. The STL is pre warped, sliced with an ordinary "
            "planar slicer, and the resulting G-code is put through a back transformation in "
            "Python so the nozzle traces conical non planar layers that support themselves as "
            "they build. The result is 25% less material, 20% shorter build time, and no post "
            "processing at all.",
        ],
        "gallery": [
            ("image", "cad-model", "The test part, a bent pipe with a true 90 degree overhang."),
            ("image", "nozzle-angle", "Measuring the achieved cone angle mid print."),
            ("video", "nozzle-path", "The nozzle tracing a non planar path."),
        ],
    },
    {
        "slug": "photoelasticity",
        "title": "Stress Concentration by Photoelasticity",
        "org": "ME218 Solid Mechanics Lab, IIT Bombay",
        "when": "Jan 2026 to Apr 2026",
        "summary": "Measuring stress concentration factors optically, with fringe patterns instead of a solver.",
        "tags": ["Photoelasticity", "ANSYS FEA", "Experimental mechanics", "TPU moulding"],
        "cover": ("image", "square-hole", "Coloured isochromatic fringe pattern around a square hole in a loaded specimen"),
        "body": [
            "Measuring stress concentration factors optically rather than numerically. Epoxy "
            "specimens were cast in TPU moulds with three hole geometries, square, filleted "
            "square and elliptical, then loaded in a polariscope where the isochromatic fringe "
            "pattern makes the stress field directly visible. Counting fringe order around the "
            "hole gives the stress concentration factor.",
            "The measured values were validated against ANSYS FEA and agreed closely on where "
            "the concentrations appear. Filleting the sharp corners of the square hole cut the "
            "factor by 21%, and switching to an elliptical hole reduced it a further 33%.",
        ],
        "gallery": [
            ("image", "filleted-hole", "Filleted corners, giving a 21% lower stress concentration factor."),
            ("image", "elliptical-hole", "An elliptical hole, a further 33% reduction."),
            ("image", "square-hole-detail", "Counting fringe order around the square hole."),
            ("image", "elliptical-hole-detail", "The elliptical specimen in the loading frame."),
            ("image", "square-hole-wide", "The full polariscope view, grips and frame included."),
        ],
    },
]

OTHER = [
    {
        "title": "Holo-Battalion",
        "org": "e-Yantra Robotics Competition",
        "when": "Aug 2025 to present",
        "points": [
            "A swarm of three robots, each with an articulated arm and omnidirectional holonomic drive",
            "ROS2 server and client framework with ArUco marker vision and homography for pose estimation",
            "Centralized task allocation by Euclidean proximity, minimising total travel",
        ],
    },
    {
        "title": "Wildlife Detection from Camera Traps",
        "org": "DS203, IIT Bombay",
        "when": "Aug 2025 to Oct 2025",
        "points": [
            "An XGBoost pipeline 60% more accurate than a logistic regression baseline",
            "HOG, LBP, GLCM and ORB descriptors pruned with SelectKBest to the 150 most predictive features",
        ],
    },
    {
        "title": "Drone Remote Controller",
        "org": "Makerspace MS101, IIT Bombay",
        "when": "Jul 2024 to Nov 2024",
        "points": [
            "A joystick remote giving a drone prototype hover capability",
            "Custom ESP32 PCB routed in EasyEDA with ARM switches and an OLED display",
        ],
    },
]


# ── Templating ───────────────────────────────────────────────────────────

def e(text):
    return html.escape(str(text), quote=True)


_digests = {}


def asset(up, rel):
    """URL for a file, tagged with a hash of its contents.

    GitHub Pages serves these with a ten minute cache and the filenames never
    change, so a browser will happily pair newly fetched HTML with a stale
    stylesheet or an old image. Changing the query string whenever the bytes
    change makes that impossible.
    """
    if rel not in _digests:
        _digests[rel] = hashlib.md5((ROOT / rel).read_bytes()).hexdigest()[:8]
    return f"{up}{rel}?v={_digests[rel]}"


def ratio(slug, name):
    """Width over height of the displayed media, used to size gallery tiles."""
    w, h = DIMS[f"{slug}/{name}"]
    return round(w / h, 4)


def shell(title, description, body, depth=0):
    up = "../" * depth
    if depth:
        nav = f'<a class="back" href="{up}index.html">All work</a>'
    else:
        nav = ('<a href="#projects">Projects</a><a href="#experience">Experience</a>'
               '<a href="#contact">Contact</a>')

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:type" content="website">
<link rel="stylesheet" href="{asset(up, "style.css")}">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>&#9881;</text></svg>">
</head>
<body>

<header class="topbar">
  <div class="bar">
    <a class="wordmark" href="{up}index.html">Vidit Bohra</a>
    <nav class="topnav">{nav}</nav>
    <button id="theme-toggle" type="button" aria-label="Switch colour theme" title="Switch colour theme"></button>
  </div>
</header>

{body}

<footer id="contact">
  <div class="wrap">
    <h2>Get in touch</h2>
    <p class="footer-line">Happy to talk about robotics, mechanism design or anything on this site.</p>
    <div class="btns">
      <a class="btn primary" href="mailto:{EMAIL}">{EMAIL}</a>
      <a class="btn" href="{GITHUB}">GitHub</a>
      <a class="btn" href="{up}resume.pdf">Download resume</a>
    </div>
  </div>
</footer>

<div id="lightbox" hidden>
  <button id="lightbox-close" type="button" aria-label="Close">&times;</button>
  <img id="lightbox-img" alt="">
</div>

<script src="{asset(up, "script.js")}"></script>
</body>
</html>
"""


def media_button(kind, slug, name, alt, up):
    base = f"assets/{slug}/{name}"
    alt = e(alt)
    if kind == "video":
        return (f'<button class="media video" data-video="{asset(up, base + ".mp4")}" '
                f'aria-label="Play video: {alt}">'
                f'<img src="{asset(up, base + "-poster.jpg")}" alt="{alt}" '
                f'loading="lazy" decoding="async">'
                f'<span class="play" aria-hidden="true"></span></button>')
    return (f'<button class="media" data-full="{asset(up, base + ".jpg")}" '
            f'aria-label="Enlarge image: {alt}">'
            f'<img src="{asset(up, base + "-thumb.jpg")}" alt="{alt}" '
            f'loading="lazy" decoding="async"></button>')


def tile(kind, slug, name, caption, up):
    cls = "tile plot" if kind == "plot" else "tile"
    return (f'<figure class="{cls}" style="--ar:{ratio(slug, name)}">'
            f'{media_button(kind, slug, name, caption, up)}'
            f"<figcaption>{e(caption)}</figcaption></figure>")


def listing(items):
    """Dates sit in a narrow left gutter, which scans far better than floating
    them out to the right edge away from what they belong to."""
    rows = []
    for it in items:
        points = "".join(f"<li>{e(p)}</li>" for p in it.get("points", []))
        rows.append(
            f'<li class="row">'
            f'<p class="when">{e(it["when"])}</p>'
            f'<div class="row-body">'
            f'<h3>{e(it["title"])}</h3>'
            f'<p class="org">{e(it["org"])}</p>'
            f'<ul class="points">{points}</ul>'
            f"</div></li>"
        )
    return '<ul class="rows">' + "".join(rows) + "</ul>"


def build_index():
    cards = []
    for p in PROJECTS:
        kind, name, alt = p["cover"]
        img = asset("", f'assets/{p["slug"]}/{name}'
                    + ("-poster.jpg" if kind == "video" else "-thumb.jpg"))
        tags = "".join(f"<li>{e(t)}</li>" for t in p["tags"][:3])
        cards.append(
            f'<a class="card" href="projects/{p["slug"]}.html">'
            f'<div class="card-img"><img src="{img}" alt="{e(alt)}" loading="lazy" decoding="async"></div>'
            f'<div class="card-body">'
            f'<h3>{e(p["title"])}</h3>'
            f'<p class="card-sum">{e(p["summary"])}</p>'
            f'<ul class="tags">{tags}</ul>'
            f"</div></a>"
        )

    skills = "".join(f'<div class="skill"><dt>{e(k)}</dt><dd>{e(v)}</dd></div>' for k, v in SKILLS)
    tagline = "".join(f"<p>{e(t)}</p>" for t in TAGLINE)

    body = f"""
<header class="intro">
  <div class="wrap intro-inner">
    <img class="avatar" src="{asset("", "assets/me/portrait-thumb.jpg")}" alt="Vidit Bohra" decoding="async">
    <div class="intro-text">
      <h1>Vidit Bohra</h1>
      <p class="role">Mechanical Engineering, IIT Bombay</p>
      {tagline}
      <div class="btns">
        <a class="btn primary" href="#projects">See my work</a>
        <a class="btn" href="resume.pdf">Resume</a>
        <a class="btn" href="mailto:{EMAIL}">Email</a>
        <a class="btn" href="{GITHUB}">GitHub</a>
      </div>
    </div>
  </div>
</header>

<main>

<section id="education">
  <div class="wrap"><h2>Education</h2>{listing(EDUCATION)}</div>
</section>

<section id="experience">
  <div class="wrap"><h2>Experience</h2>{listing(EXPERIENCE)}</div>
</section>

<section id="skills">
  <div class="wrap"><h2>Skills</h2><dl class="skills">{skills}</dl></div>
</section>

<section id="projects">
  <div class="wrap">
    <h2>Projects</h2>
    <div class="cards">{"".join(cards)}</div>
  </div>
</section>

<section id="other">
  <div class="wrap"><h2>Also worked on</h2>{listing(OTHER)}</div>
</section>

</main>
"""
    return shell(
        "Vidit Bohra",
        "Mechanical engineering at IIT Bombay. Robotics, mechanism design, control and estimation.",
        body,
    )


def build_project(index):
    p = PROJECTS[index]
    up = "../"
    kind, name, alt = p["cover"]

    tags = "".join(f"<li>{e(t)}</li>" for t in p["tags"])
    paras = "".join(f"<p>{e(t)}</p>" for t in p["body"])
    tiles = "".join(tile(k, p["slug"], n, c, up) for k, n, c in p["gallery"])

    prev_p = PROJECTS[index - 1]
    next_p = PROJECTS[(index + 1) % len(PROJECTS)]

    body = f"""
<main class="project-page">

<header class="project-head">
  <div class="wrap">
    <h1>{e(p["title"])}</h1>
    <p class="role">{e(p["org"])} &middot; {e(p["when"])}</p>
    <p class="summary">{e(p["summary"])}</p>
    <ul class="tags">{tags}</ul>
    <figure class="cover" style="--ar:{ratio(p["slug"], name)}">
      {media_button(kind, p["slug"], name, alt, up)}
    </figure>
  </div>
</header>

<section class="writeup">
  <div class="wrap"><div class="prose">{paras}</div></div>
</section>

<section>
  <div class="wrap">
    <h2>Gallery</h2>
    <div class="grid">{tiles}</div>
  </div>
</section>

<nav class="pager">
  <div class="wrap">
    <a class="pager-link" href="{prev_p["slug"]}.html">
      <span class="dir">Previous</span><span class="name">{e(prev_p["title"])}</span></a>
    <a class="pager-link next" href="{next_p["slug"]}.html">
      <span class="dir">Next</span><span class="name">{e(next_p["title"])}</span></a>
  </div>
</nav>

</main>
"""
    return shell(f'{p["title"]} | Vidit Bohra', p["summary"], body, depth=1)


def main():
    # Fail loudly if the content references media that build_media.py did not produce.
    missing = []
    for p in PROJECTS:
        for _, name, _ in [p["cover"]] + [(k, n, c) for k, n, c in p["gallery"]]:
            if f'{p["slug"]}/{name}' not in DIMS:
                missing.append(f'{p["slug"]}/{name}')
    if missing:
        print("Referenced media not built:", *missing, sep="\n  ")
        return 1

    (ROOT / "index.html").write_text(build_index(), encoding="utf-8")
    print("index.html")

    out = ROOT / "projects"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir()

    for i, p in enumerate(PROJECTS):
        (out / f'{p["slug"]}.html').write_text(build_project(i), encoding="utf-8")
        print(f'projects/{p["slug"]}.html')

    # Nothing on this site should contain an en or em dash.
    bad = []
    for page in [ROOT / "index.html", *out.glob("*.html")]:
        text = page.read_text(encoding="utf-8")
        for ch, label in (("–", "en dash"), ("—", "em dash")):
            if ch in text:
                bad.append(f"{page.name}: {label}")
    if bad:
        print("\nDashes found:", *bad, sep="\n  ")
        return 1
    print("\nno en or em dashes present")
    return 0


if __name__ == "__main__":
    sys.exit(main())
