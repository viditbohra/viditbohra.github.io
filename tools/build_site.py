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
MODELS = json.loads((ROOT / "assets" / "models.json").read_text())

# ── Content ──────────────────────────────────────────────────────────────

TAGLINE = [
    "Minoring in Artificial Intelligence and Data Science, and in Systems and Control.",
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

# Taken from the ASC transcript, grouped by subject rather than by semester,
# since what a course covers is what a reader cares about. Codes and titles are
# exactly as the transcript records them.
#
# Left out on purpose: the zero credit administrative entries (TASET, NCC/NSS/NSO,
# Gender in the Workplace), which are not courses in any useful sense.
COURSEWORK = [
    ("Systems and control, minor", [
        ("ME 319", "Control Systems"),
        ("SC 602", "Control of Nonlinear Dynamical Systems"),
        ("SC 625", "Systems Theory"),
        ("SC 651", "Estimation on Lie Groups"),
    ]),
    ("AI and data science, minor", [
        ("ME 228", "Applied Data Science and Machine Learning"),
        ("DS 203", "Programming for Data Science"),
        ("CS 101", "Computer Programming and Utilization"),
    ]),
    ("Mechanics and solids", [
        ("ME 601", "Stress Analysis"),
        ("ME 223", "Solid Mechanics and Strength of Materials"),
        ("ME 218", "Solid Mechanics Lab"),
        ("ME 221", "Structural Materials"),
        ("ME 104", "Engineering Mechanics"),
    ]),
    ("Thermal and fluids", [
        ("ME 415", "Computational Fluid Dynamics and Heat Transfer"),
        ("ME 346", "Heat Transfer"),
        ("ME 306", "Applied Thermodynamics"),
        ("ME 209", "Thermodynamics"),
        ("ME 219", "Fluid Mechanics"),
        ("ME 224", "Fluid Mechanics Lab"),
    ]),
    ("Manufacturing and materials", [
        ("ME 323", "Thermal and Chemical Processing of Materials"),
        ("ME 230", "Mechanical Processing of Materials"),
        ("ME 374", "Manufacturing Processes Lab"),
        ("ME 213", "Manufacturing Practice Lab"),
    ]),
    ("Design and making", [
        ("ME 444", "Analysis and Design of Mechanical Systems"),
        ("DE 250", "Design Thinking for Innovation"),
        ("MS 101", "Makerspace"),
        ("ME 103", "Mechanical Engineering Introductory Course"),
    ]),
    ("Mathematics and physics", [
        ("MA 105", "Calculus"),
        ("MA 110", "Linear Algebra and Differential Equations"),
        ("ME 225", "Numerical Analysis"),
        ("PH 401", "Classical Mechanics"),
        ("PH 117", "Physics Lab"),
    ]),
    ("Institute core", [
        ("EC 101", "Economics"),
        ("SOM 101", "Introduction to Management"),
        ("HS 110", "Introduction to Psychology"),
        ("BB 101", "Biology"),
        ("CH 117", "Chemistry Lab"),
        ("ES 250", "Environmental Studies"),
    ]),
]

# Registered for the current semester, so they are marked rather than presented
# as finished.
CURRENT_COURSES = {
    "ME 224", "ME 306", "ME 319", "ME 323", "ME 346", "ME 374", "ME 415",
    "ME 601", "SC 625",
}

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
    ("Mechanical design", "SolidWorks, Fusion 360, MSC Adams"),
    ("Simulation & analysis", "ANSYS, ANSYS Fluent, COMSOL"),
    ("Robotics", "ROS2, Isaac Lab, Holosoma, Gazebo, MuJoCo"),
    ("Control & estimation",
     "MATLAB, Simulink, Simscape Multibody, Kalman/Mahony filtering, Lie groups"),
    ("Fabrication", "3D printing (FDM), sheet metal"),
    ("Programming", "C, C++, Python, SQL, LaTeX"),
]

# Each project's "sections" list is the case-study body: an optional lede
# paragraph, then headed blocks that alternate image/text down the page, each
# with at most one paired piece of media (kind, name, caption) or None for a
# text-only block. "stats" are real numbers already established in the prose,
# used as the page's big-number strip - never invented. "role" overrides the
# annotation row's ROLE field with the matching title from EXPERIENCE, where
# one exists; projects without a clean match just show their "org" there.
PROJECTS = [
    {
        "slug": "retargeting",
        "title": "Human to Robot Motion Retargeting",
        "org": "GV Lab, University of Tokyo",
        "role": "Research Intern",
        "when": "Jun 2026 to Jul 2026",
        "summary": "Turning a phone video of a person handling an object into motion a robot can reproduce.",
        "tags": ["HMR2 / 4D-Humans", "SMPL", "Holosoma", "Inverse kinematics", "Python"],
        "cover": ("video", "pepper-sim", "A Pepper humanoid reproducing a captured human motion in simulation"),
        "stats": [],
        "sections": [
            {
                "heading": "Pipeline",
                "media": ("video", "pepper-arms", "Retargeted arm motion on the Pepper humanoid."),
                "body": [
                    "An end to end pipeline that takes an ordinary monocular RGB video of someone "
                    "handling an object and produces motion a robot can actually execute. Human pose "
                    "comes from HMR2 (4D-Humans), joint positions are extracted through SMPL, and the "
                    "motion is retargeted onto the robot using inverse kinematics in Holosoma. It runs "
                    "on both a Pepper humanoid and a UR5 arm.",
                ],
            },
            {
                "heading": "Preserving the interaction",
                "media": ("plot", "point-cloud", "Cleaned point cloud of the manipulated object, XZ and XY projections."),
                "body": [
                    "The hard part is what gets preserved. Copying joint angles between bodies with "
                    "different proportions breaks the task, because the hand ends up in the wrong place "
                    "relative to the object. This pipeline uses an interaction mesh formulation that "
                    "encodes the spatial relationship between the human and the object, so the "
                    "retargeted motion keeps the manipulation intact rather than just the pose.",
                ],
            },
        ],
        "gallery": [
            ("video", "ur5-arm", "The same pipeline driving a UR5 arm."),
            ("video", "humanoid-sim", "A full humanoid reproducing the captured motion."),
            ("video", "smpl-body", "The SMPL body model recovered from the human motion."),
        ],
    },
    {
        "slug": "mars-rover-arm",
        "title": "Mars Rover Robotic Arm",
        "org": "Mars Rover Team, IIT Bombay",
        "role": "Senior Design Engineer, Robotic Arm Subsystem",
        "when": "Oct 2024 to present",
        "summary": "A 5-DOF manipulator for a competition rover, built around two purpose built cycloidal gearboxes.",
        "tags": ["SolidWorks", "Cycloidal drive", "ANSYS", "3D printing", "MSC Adams"],
        "cover": ("image", "rover-field", "The completed rover with its robotic arm deployed on a competition course"),
        "case_study": True,
        "stats": [
            ("81:1", "Shoulder gearbox ratio"),
            ("160 Nm", "Shoulder gearbox torque"),
            ("5 kg", "Payload at full extension"),
            ("35%", "Lighter redesigned wrist"),
        ],
        "lede": [
            "The manipulator on a semi autonomous rover built by a 30 person team to cross rough "
            "terrain and perform dexterous tasks at international competitions. I designed the "
            "5-DOF arm and reworked most of its drivetrain: two purpose built cycloidal "
            "gearboxes, a 2-DOF differential wrist redesigned as a 3D print that came out 35% "
            "lighter, and the linear base, links and gripper below. Rated to carry 5 kg at full "
            "extension, each joint uses explicit steering, so a commanded angle maps to one "
            "actuator rather than being shared across a coupled linkage, which keeps the control "
            "predictable.",
        ],
        "sections": [
            {
                "heading": "Linear base",
                "media": [
                    ("image", "base-slots-detail", "The carriage's elongated mounting slots, which absorb rail misalignment instead of fighting it."),
                    ("video", "linear-base-cad", "Linear base motion study."),
                    ("video", "linear-base-demo", "The linear base running on hardware."),
                ],
                "body": [
                    "The carriage rides on twin MGN9H linear rails, and no assembly is ever "
                    "perfectly parallel: manufacturing and build tolerance can leave the rails "
                    "converging in a slight V, or sitting high on one side and low on the other. "
                    "Fixing the carriage rigidly to both would fight that misalignment and bind. "
                    "Instead the rail mounting holes are cut as elongated slots, giving about 7 to "
                    "8 mm of adjustment, so the carriage can shift sideways to whatever the rails "
                    "actually are rather than what they were drawn as.",
                    "The carriage is driven by a trapezoidal lead screw rather than a ball screw, "
                    "chosen for its tolerance to dust and grit and because it self locks when "
                    "unpowered. A pulley and belt drive was considered for the same job, since it "
                    "would keep the motor's weight off the moving carriage, but it was dropped: "
                    "the belt widened the mounting plate and enough of its length elongates "
                    "plastically over time that positioning would have drifted. The plate that "
                    "bolts the lead screw nut to the carriage carries its own vertical slot for "
                    "the same underlying reason as the rails: it lets the nut float instead of "
                    "being pinned rigidly, so it only ever pushes the carriage horizontally, the "
                    "direction it is actually meant to drive in, and never picks up a vertical "
                    "load it was never meant to carry.",
                ],
            },
            {
                "heading": "Wrist",
                "media": [
                    ("image", "wrist-shaft-support-cad", "The differential's worm shafts, supported by bearings at both ends rather than hanging off the gearbox."),
                    ("video", "wrist-cad", "The 2-DOF differential wrist in CAD."),
                ],
                "body": [
                    "The wrist gets its 2 DOF from a differential: two stepper motors mounted back "
                    "at the base drive into a bevel gear differential, so driving both in the same "
                    "direction produces one motion and driving them opposite produces the other, "
                    "with anything in between blending the two. That keeps both actuators off the "
                    "moving end of the arm, where their mass would cost the most. It is fully 3D "
                    "printed, which let the housing take on a geometry a machined part could not "
                    "have and cut iteration time considerably.",
                    "Each drive runs through a worm stage before it reaches the differential's "
                    "bevel gears, added for two reasons: a worm gets a large reduction in a single "
                    "small stage, and a worm cannot be back driven, so the wrist holds its "
                    "position under load and stays where it is if power is lost, instead of "
                    "collapsing under the weight of the arm.",
                    "The worm shaft originally hung as an unsupported cantilever off the gearbox. "
                    "That was wrong twice over: the whole bending load went through the gear mesh "
                    "with nothing else carrying it, and under vibration the meshing would work "
                    "loose. Constraining the shaft rigidly with bearings at both ends fixed that, "
                    "giving the load a path into the housing instead of overhanging the gearbox. "
                    "With no way to simulate a 3D printed part's behaviour beforehand, the fix "
                    "came from iterative prototyping and load testing on hardware rather than FEA.",
                ],
            },
            {
                "heading": "Gearbox",
                "media": [
                    ("plot", "gearbox-disc-fea", "Stress analysis on a cycloidal disc, the epitrochoid profile at the centre of both gearboxes."),
                    ("image", "gearbox-cross-section", "A section through the gearbox coupler, showing the bearing and seal stack that keeps the discs running true."),
                ],
                "body": [
                    "The shoulder and elbow each get their own cycloidal gearbox rather than "
                    "sharing one: a two stage drive at the shoulder, 81:1, rated to 160 Nm and "
                    "held by a fail safe electromagnetic brake that engages the moment power is "
                    "cut; a lighter single stage drive at the elbow, 34:1 and 65 Nm, deliberately "
                    "smaller so it does not add dead weight the shoulder has to carry.",
                    "A cycloidal disc spins with its mass offset from the output axis, and the "
                    "standard fix for the out of balance force that creates is a second disc at "
                    "the opposite eccentricity. Working from a published two stage cycloidal "
                    "design, the shoulder gearbox gets both reduction stages out of two discs "
                    "rather than the four a conventional layout would need, keeping it far more "
                    "compact. FEA on the internals under a 5 kg payload at full extension gives "
                    "safety factors of 4 on the output plate and 6 and 4 on the two discs, "
                    "margins comfortable enough to build with confidence.",
                    "It has not been a clean win. Trading four discs for two gives up some of the "
                    "balance that pairing normally provides, and the drive stutters under load, a "
                    "limitation that comes from the geometry itself rather than from how it was "
                    "built. The roller rods inside the gearbox came out as its weakest point in "
                    "the same analysis, which lines up with where the stutter shows up. I reached "
                    "out to the paper's authors to ask about it and never heard back, so this is "
                    "an open problem I am still working through.",
                ],
            },
            {
                "heading": "Links",
                "media": ("image", "link-hemmed-edge", "The shoulder link: laser cut aluminium sheet with a hemmed edge, doubled up with U shaped brackets."),
                "body": [
                    "The shoulder link is laser cut aluminium sheet, not the carbon fibre used the "
                    "year before, chosen for a better balance of cost and stiffness. Its long "
                    "edges are hemmed, folded back on themselves, which raises the section's area "
                    "moment of inertia without adding thickness or bolting on a separate flange, "
                    "so a link cut from thin sheet gets meaningfully stiffer in bending for the "
                    "same weight. Two hemmed sheets are then joined with U shaped brackets across "
                    "the span for extra rigidity. The elbow link is a simpler 38 mm square "
                    "aluminium tube, sized to make mounting the electronics and the wrist "
                    "straightforward.",
                ],
            },
            {
                "heading": "Gripper",
                "media": ("image", "gripper-cad", "The gripper: a fixed, rubber padded finger and a lead screw driven jaw."),
                "body": [
                    "A low speed, high torque N20 motor drives a lead screw against a fixed, "
                    "rubber padded finger for a strong, controlled grip, with the jaw travel "
                    "lined up to the competition's sample handling tasks rather than a generic "
                    "centred pinch. It is wireless: an onboard ESP32 replaced a slip ring at the "
                    "wrist that had proven fragile and difficult to maintain, so the gripper now "
                    "carries its own control and video link instead of routing everything through "
                    "a rotating contact.",
                ],
            },
            {
                "heading": "Results",
                "media": None,
                "body": [
                    "With this rover the team placed 2nd at the European Rover Challenge against "
                    "24 teams from 15 countries, took 1st in the Astrobiology Mission at the "
                    "International Rover Challenge, and finished 9th overall in the IRC against "
                    "more than 35 institutions worldwide.",
                ],
            },
        ],
        "gallery": [
            ("image", "arm-cad", "The full 5-DOF arm in CAD, with the linear base, worm driven wrist and gripper."),
            ("image", "rover-cad", "Full rover chassis in CAD."),
            ("image", "wrist-differential-cad", "The wrist differential in CAD, worm stage and bevel gears visible."),
            ("image", "wrist-assembly", "The bevel gear differential at the centre of the 2-DOF wrist, assembled."),
            ("image", "wrist-build", "The wrist with its worm stage, lead screw and gripper drive."),
            ("image", "cycloidal-drive", "The shoulder gearbox, assembled."),
            ("image", "elbow-gearbox-cad", "The elbow's single stage cycloidal gearbox, deliberately smaller than the shoulder's."),
            ("plot", "gearbox-plate-fea", "FEA on the shoulder's output plate: safety factor of 4 under a 160 Nm moment."),
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
        "stats": [
            ("6-DOF", "Biped"),
            ("85%", "Simscape model fit"),
            ("4-DOF", "Standalone test rig"),
        ],
        "lede": [
            "A 6-DOF biped built from scratch after a literature review of existing walking "
            "robots set the baseline requirements. The frame uses lightweight carbon fibre "
            "tubes for the leg links, joined at each servo with 3D printed brackets, and limit "
            "sensors at every joint for homing.",
        ],
        "sections": [
            {
                "heading": "Weight shift mechanism",
                "media": ("image", "cad-render", "The biped in CAD, trussed throughout to cut mass, with the rack and pinion weight shift mechanism at the hip."),
                "body": [
                    "Standing on two feet means shifting the centre of mass over whichever leg is "
                    "about to bear it, and a rack and pinion assembly at the hip does that "
                    "shifting predictably instead of leaving it to the legs alone. The battery "
                    "mounts directly on the moving carriage of that mechanism rather than on the "
                    "fixed torso, so its mass becomes the shifting counterweight instead of dead "
                    "weight the frame just has to carry. That gives the mechanism more authority "
                    "for the same travel and takes the heaviest single component off the torso's "
                    "own weight budget.",
                ],
            },
            {
                "heading": "Wiring",
                "media": None,
                "body": [
                    "The carriage travels back and forth on every step, and running wiring "
                    "straight across that motion would fatigue and tangle it over time. A drag "
                    "chain carries the cabling across the travel instead, so the wiring bends the "
                    "same way on every cycle rather than wherever it happens to fall.",
                ],
            },
            {
                "heading": "Test rig",
                "media": ("image", "leg-test-rig", "The legs on the standalone 4-DOF test rig, hip rack and pinion and carbon fibre tubes visible."),
                "body": [
                    "Before committing to the full assembly, both legs were built and driven on a "
                    "standalone 4-DOF test rig off the torso, to validate the leg design and tune "
                    "control on hardware without risking the complete robot.",
                ],
            },
            {
                "heading": "Underactuated ankle joints",
                "media": None,
                "body": [
                    "Not every DOF is actuated. Two joints in the ankle are left passive and "
                    "returned by springs instead of motors, which keeps the weight and part count "
                    "down while still giving the robot the compliance it needs to turn, since a "
                    "fully rigid foot cannot pivot against the ground.",
                ],
            },
            {
                "heading": "Control",
                "media": ("plot", "simscape-model", "The Simscape multibody model, fitted to 85% and used to drive the data driven controller."),
                "body": [
                    "Three approaches were tried. A PPO policy trained in Isaac Lab, with a multi "
                    "term reward covering velocity tracking, feet air time and joint limit "
                    "penalties, produced a stable walking gait in simulation. A state space model "
                    "fitted from Simscape at 85% fit drove a data driven controller in Simulink. "
                    "And an LQR controller on a linear inverted pendulum model produced a stable "
                    "gait analytically. On hardware, inverse kinematics and PID loops on an "
                    "Arduino Mega with an MPU6050 handle real time balance.",
                ],
            },
        ],
        "gallery": [
            ("video", "rl-policy", "The trained PPO policy walking in Isaac Lab."),
            ("video", "data-driven-control", "The data driven controller running in simulation."),
            ("video", "hardware-test", "Hardware test."),
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
        "stats": [("40%", "Lower deviation vs. TRIAD/QUEST")],
        "sections": [
            {
                "heading": "Attitude estimation",
                "media": None,
                "body": [
                    "This started as coursework in estimation on Lie groups: implementing the "
                    "Kalman filter, TRIAD and QUEST on an IMU to get a stable attitude estimate "
                    "by fusing gyroscope, accelerometer and magnetometer data. I then implemented "
                    "the Mahony filter and compared it systematically against TRIAD and QUEST, "
                    "which gave a 40% lower standard deviation in the output.",
                ],
            },
            {
                "heading": "Visual inertial hardware",
                "media": ("image", "rig-detail", "The rig set up for a capture run."),
                "body": [
                    "It has since grown into a visual inertial setup on hardware I built, an "
                    "RP2040 Pico with an IMX335 camera and an MPU6050, characterised with an "
                    "Allan deviation analysis to pin down the gyro and accelerometer noise "
                    "parameters. The filter estimates the camera trajectory and a landmark map "
                    "together from the fused visual and inertial stream.",
                ],
            },
        ],
        "gallery": [
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
        "stats": [("25%", "Less material"), ("20%", "Shorter build time")],
        "sections": [
            {
                "heading": "The problem",
                "media": ("image", "cad-model", "The test part, a bent pipe with a true 90 degree overhang."),
                "body": [
                    "Printing a 90 degree overhang normally means printing supports, then cutting "
                    "them off and cleaning up the scar they leave behind. This project prints "
                    "them with no support at all, on an unmodified 3-axis FDM printer with no "
                    "hardware changes.",
                ],
            },
            {
                "heading": "Non planar slicing",
                "media": ("video", "nozzle-path", "The nozzle tracing a non planar path."),
                "body": [
                    "All of the work happens in software. The STL is pre warped, sliced with an "
                    "ordinary planar slicer, and the resulting G-code is put through a back "
                    "transformation in Python so the nozzle traces conical non planar layers that "
                    "support themselves as they build. The result is 25% less material, 20% "
                    "shorter build time, and no post processing at all.",
                ],
            },
        ],
        "gallery": [
            ("image", "nozzle-angle", "Measuring the achieved cone angle mid print."),
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
        "stats": [
            ("21%", "SCF reduction, filleted hole"),
            ("33%", "SCF reduction, elliptical hole"),
        ],
        "sections": [
            {
                "heading": "Measuring stress concentration",
                "media": ("image", "square-hole-wide", "The full polariscope view, grips and frame included."),
                "body": [
                    "Measuring stress concentration factors optically rather than numerically. "
                    "Epoxy specimens were cast in TPU moulds with three hole geometries, square, "
                    "filleted square and elliptical, then loaded in a polariscope where the "
                    "isochromatic fringe pattern makes the stress field directly visible. "
                    "Counting fringe order around the hole gives the stress concentration factor.",
                ],
            },
            {
                "heading": "Results",
                "media": ("image", "filleted-hole", "Filleted corners, giving a 21% lower stress concentration factor."),
                "body": [
                    "The measured values were validated against ANSYS FEA and agreed closely on "
                    "where the concentrations appear. Filleting the sharp corners of the square "
                    "hole cut the factor by 21%, and switching to an elliptical hole reduced it a "
                    "further 33%.",
                ],
            },
        ],
        "gallery": [
            ("image", "elliptical-hole", "An elliptical hole, a further 33% reduction."),
            ("image", "square-hole-detail", "Counting fringe order around the square hole."),
            ("image", "elliptical-hole-detail", "The elliptical specimen in the loading frame."),
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

# ── Mars Rover Arm case study ───────────────────────────────────────────
#
# A one-off page (see build_case_study()): a scroll-driven camera moves over
# a single 3D model as you read, instead of the alternating case-block rows
# the other project pages use. Content still lives here as Python data, not
# hand-typed HTML, matching the rest of this file's house rule.

CASE_STUDY_CHAPTERS = [
    {
        "num": "01", "mech": "Linear base", "title": "Linear<br>base", "model": "linear-base",
        "blocks": [
            ("beat", "Design problem", [
                "Twin MGN9H linear rails never mount perfectly parallel in a real "
                "build. Manufacturing and assembly tolerance leave them converging "
                "or sitting at different heights, tolerances that don't exist in "
                "the CAD model.",
            ]),
            ("beat", "Design decision", [
                "The carriage's mounting holes are cut as slots, not circles, "
                "about 7 to 8 mm of lateral play, so the carriage settles onto the "
                "rails as they actually sit instead of forcing the rails to match "
                "the drawing.",
            ]),
            ("evidence", [
                ("image", "base-slots-detail", "The carriage's elongated mounting slots, which absorb rail misalignment instead of fighting it."),
            ]),
            ("beat", "Drive decision", [
                "A trapezoidal lead screw, not a ball screw. It tolerates dust and "
                "grit and self locks when unpowered, so the base holds position "
                "without a brake.",
            ]),
            ("beat-muted", "Alternative considered", [
                "A belt and pulley drive would have kept the motor's mass off the "
                "moving carriage. Dropped: the belt widened the mounting plate, "
                "and enough of its length stretches plastically over time that "
                "positioning would drift. The lead screw nut plate carries the "
                "same fix as the rails, a vertical slot so the nut floats instead "
                "of being pinned rigidly.",
            ]),
            ("evidence", [
                ("video", "linear-base-demo", "The linear base running on hardware."),
            ]),
        ],
    },
    {
        "num": "02", "mech": "Shoulder", "title": "Shoulder", "model": "shoulder",
        "blocks": [
            ("beat", "Design decision", [
                "A two-stage cycloidal drive, 81:1, rated to 160 Nm and held by a "
                "fail safe electromagnetic brake that engages the moment power is "
                "cut.",
            ]),
            ("evidence", [
                ("image", "shoulder-gearbox-cad", "The shoulder's two-stage cycloidal gearbox in CAD."),
            ]),
            ("beat", "Design decision", [
                "A cycloidal disc spins with its mass offset from the output "
                "axis, and the standard fix for the out of balance force that "
                "creates is a second disc at the opposite eccentricity. Working "
                "from a published two stage cycloidal design, the shoulder "
                "gearbox gets both reduction stages out of two discs rather than "
                "the four a conventional layout would need, keeping it far more "
                "compact.",
            ]),
            ("beat", "Tested", [
                "FEA on the internals under a 5 kg payload at full extension "
                "gives safety factors of 4 on the output plate and 6 and 4 on "
                "the two discs, margins comfortable enough to build with "
                "confidence.",
            ]),
            ("evidence", [
                ("image", "gearbox-disc-fea", "Stress analysis on a cycloidal disc, the epitrochoid profile at the centre of both gearboxes."),
                ("image", "gearbox-plate-fea", "FEA on the shoulder's output plate: safety factor of 4 under a 160 Nm moment."),
            ]),
            ("beat-muted", "Open problem", [
                "It has not been a clean win. Trading four discs for two gives "
                "up some of the balance that pairing normally provides, and the "
                "drive stutters under load, a limitation that comes from the "
                "geometry itself rather than from how it was built. The roller "
                "rods inside the gearbox came out as its weakest point in the "
                "same analysis, which lines up with where the stutter shows up. "
                "I reached out to the paper's authors to ask about it and never "
                "heard back, so this is an open problem I am still working "
                "through.",
            ]),
            ("beat", "Structure", [
                "The shoulder link is laser cut aluminium sheet, not the carbon "
                "fibre used the year before, chosen for a better balance of cost "
                "and stiffness. Its long edges are hemmed, folded back on "
                "themselves, which raises the section's area moment of inertia "
                "without adding thickness or bolting on a separate flange, so a "
                "link cut from thin sheet gets meaningfully stiffer in bending "
                "for the same weight. Two hemmed sheets are then joined with U "
                "shaped brackets across the span for extra rigidity.",
            ]),
            ("evidence", [
                ("image", "link-hemmed-edge", "The shoulder link: laser cut aluminium sheet with a hemmed edge, doubled up with U shaped brackets."),
                ("image", "cycloidal-drive", "The shoulder gearbox, assembled."),
            ]),
        ],
    },
    {
        "num": "03", "mech": "Elbow", "title": "Elbow", "model": "elbow",
        "blocks": [
            ("beat-media", "Design decision", [
                "A lighter single stage cycloidal drive, 34:1 and 65 Nm, "
                "deliberately smaller than the shoulder's so it does not add "
                "dead weight the shoulder has to carry.",
            ], [
                ("image", "elbow-gearbox-cad", "The elbow's single stage cycloidal gearbox, deliberately smaller than the shoulder's."),
            ]),
            ("beat", "Structure", [
                "The elbow link is a simpler 38 mm square aluminium tube, sized "
                "to make mounting the electronics and the wrist straightforward.",
            ]),
        ],
    },
    {
        "num": "04", "mech": "Wrist", "title": "Differential<br>wrist", "model": "wrist",
        "blocks": [
            ("beat", "Design problem", [
                "A 2-DOF wrist usually means a motor riding at the joint for "
                "each axis, mass added exactly where it costs the most "
                "leverage.",
            ]),
            ("beat", "Design decision", [
                "The wrist gets its 2 DOF from a differential: two stepper "
                "motors mounted back at the base drive into a bevel gear "
                "differential, so driving both in the same direction produces "
                "one motion and driving them opposite produces the other, with "
                "anything in between blending the two. That keeps both "
                "actuators off the moving end of the arm, where their mass "
                "would cost the most. It is fully 3D printed, which let the "
                "housing take on a geometry a machined part could not have, and "
                "version two of the housing came out 35% lighter than the "
                "machined aluminium it replaced.",
            ]),
            ("evidence", [
                ("video", "wrist-cad", "The 2-DOF differential wrist in CAD."),
            ]),
            ("beat-media", "Anti-backdrive", [
                "Each drive runs through a worm stage before it reaches the "
                "differential's bevel gears, added for two reasons: a worm gets "
                "a large reduction in a single small stage, and a worm cannot "
                "be back driven, so the wrist holds its position under load and "
                "stays where it is if power is lost, instead of collapsing "
                "under the weight of the arm.",
            ], [
                ("image", "wrist-differential-cad", "The wrist differential in CAD, worm stage and bevel gears visible."),
            ]),
            ("beat-muted", "Fixed after testing", [
                "The worm shaft originally hung as an unsupported cantilever "
                "off the gearbox. That was wrong twice over: the whole bending "
                "load went through the gear mesh with nothing else carrying it, "
                "and under vibration the meshing would work loose. Constraining "
                "the shaft rigidly with bearings at both ends fixed that, "
                "giving the load a path into the housing instead of overhanging "
                "the gearbox. With no way to simulate a 3D printed part's "
                "behaviour beforehand, the fix came from iterative prototyping "
                "and load testing on hardware rather than FEA.",
            ]),
            ("evidence", [
                ("image", "wrist-shaft-support-cad", "The differential's worm shafts, supported by bearings at both ends rather than hanging off the gearbox."),
                ("image", "wrist-assembly", "The bevel gear differential at the centre of the 2-DOF wrist, assembled."),
                ("image", "wrist-build", "The wrist with its worm stage, lead screw and gripper drive."),
            ]),
        ],
    },
    {
        "num": "05", "mech": "Gripper", "title": "Gripper", "model": "gripper",
        "blocks": [
            ("beat-media", "Design decision", [
                "A low speed, high torque N20 motor drives a lead screw against "
                "a fixed, rubber padded finger for a strong, controlled grip, "
                "with the jaw travel lined up to the competition's sample "
                "handling tasks rather than a generic centred pinch.",
            ], [
                ("image", "gripper-cad", "The gripper: a fixed, rubber padded finger and a lead screw driven jaw."),
            ]),
            ("beat", "Wireless", [
                "An onboard ESP32 replaced a slip ring at the wrist that had "
                "proven fragile and difficult to maintain, so the gripper now "
                "carries its own control and video link instead of routing "
                "everything through a rotating contact.",
            ]),
        ],
    },
]

CASE_STUDY_CLOSING = {
    "photo": ("rover-field", "The completed rover with its robotic arm deployed on a competition course."),
    "tag": "Complete manipulator, on course",
    "result": [
        ("Built to carry a ", None), ("5 kg", "b"), (" payload at full extension on a 5-DOF arm "
         "with a linear base. Placed ", None), ("2nd of 24 teams", "b"),
        (" from 15 countries at the European Rover Challenge, took ", None),
        ("1st in the Astrobiology Mission", "b"), (", and finished ", None),
        ("9th overall of 35+ institutions", "b"), (" at the International Rover Challenge.", None),
    ],
    "close": "Mechanical design, manufacturing, and testing. IIT Bombay Mars Rover Team.",
}


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


def shell(title, description, body, depth=0, extra_head=""):
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
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{asset(up, "style.css")}">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>&#9881;</text></svg>">
{extra_head}</head>
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


def coursework(groups):
    """Course codes in a narrow gutter, titles aligned in a column beside them,
    the same shape as the dates in a row list."""
    cols = []
    for heading, items in groups:
        rows = []
        for code, title in items:
            mark = ' <span class="now">now</span>' if code in CURRENT_COURSES else ""
            rows.append(f'<li><span class="code">{e(code)}</span>'
                        f"<span>{e(title)}{mark}</span></li>")
        cols.append(f'<div class="course-group"><h3>{e(heading)}</h3>'
                    f'<ul>{"".join(rows)}</ul></div>')
    return '<div class="courses">' + "".join(cols) + "</div>"


FEATURED = {"mars-rover-arm", "bipedal-robot"}
HERO_IMAGE = ("me", "portrait")


def project_role(p):
    """The annotation row's ROLE value: an explicit override where the project
    sets one, else a matching EXPERIENCE title (ties the project to what was
    actually done rather than just naming the org), else the org itself."""
    if p.get("role"):
        return p["role"]
    for x in EXPERIENCE:
        if p["org"].split(",")[0] in x["org"]:
            return x["title"]
    return p["org"]


def build_index():
    featured, more = [], []
    for i, p in enumerate(PROJECTS):
        (featured if p["slug"] in FEATURED else more).append((i, p))

    feature_blocks = []
    for i, p in featured:
        kind, name, alt = p["cover"]
        img = asset("", f'assets/{p["slug"]}/{name}'
                    + ("-poster.jpg" if kind == "video" else "-thumb.jpg"))
        stats = "".join(
            f'<div class="stat"><div class="n mono">{e(v)}</div><div class="l">{e(l)}</div></div>'
            for v, l in p["stats"][:3]
        )
        feature_blocks.append(
            f'<a class="feature" href="projects/{p["slug"]}.html">'
            f'<div class="feature-media" style="--ar:{ratio(p["slug"], name)}">'
            f'<img src="{img}" alt="{e(alt)}" loading="lazy" decoding="async"></div>'
            f'<div class="feature-text">'
            f'<div class="feature-num mono">{i + 1:02d}</div>'
            f'<h3>{e(p["title"])}</h3>'
            f'<p class="feature-sum">{e(p["summary"])}</p>'
            f'{f"<div class=\"stats\">{stats}</div>" if stats else ""}'
            f'<div class="feature-cta">Read the case study</div>'
            f"</div></a>"
        )

    cards = []
    for i, p in more:
        kind, name, alt = p["cover"]
        img = asset("", f'assets/{p["slug"]}/{name}'
                    + ("-poster.jpg" if kind == "video" else "-thumb.jpg"))
        tags = "".join(f"<li>{e(t)}</li>" for t in p["tags"][:3])
        cards.append(
            f'<a class="card" href="projects/{p["slug"]}.html">'
            f'<div class="card-num mono">{i + 1:02d}</div>'
            f'<div class="card-img"><img src="{img}" alt="{e(alt)}" loading="lazy" decoding="async"></div>'
            f'<div class="card-body">'
            f'<h3>{e(p["title"])}</h3>'
            f'<p class="card-sum">{e(p["summary"])}</p>'
            f'<ul class="tags">{tags}</ul>'
            f"</div></a>"
        )

    skills = "".join(f'<div class="skill"><dt>{e(k)}</dt><dd>{e(v)}</dd></div>' for k, v in SKILLS)

    hero_slug, hero_name = HERO_IMAGE
    hero_img = asset("", f"assets/{hero_slug}/{hero_name}-thumb.jpg")

    body = f"""
<header class="hero">
  <div class="wrap hero-inner">
    <div class="hero-text">
      <p class="hero-eyebrow">Third year Mechanical Engineering undergraduate, IIT Bombay</p>
      <h1>Mechanical engineering, robotics &amp; intelligent machines.</h1>
      <p class="hero-lede">{e(TAGLINE[1])}</p>
      <p class="hero-lede">{e(TAGLINE[0])}</p>
      <div class="btns">
        <a class="btn primary" href="#projects">See my work</a>
        <a class="btn" href="resume.pdf">Resume</a>
        <a class="btn" href="mailto:{EMAIL}">Email</a>
        <a class="btn" href="{GITHUB}">GitHub</a>
      </div>
    </div>
    <figure class="hero-media" style="--ar:{ratio(hero_slug, hero_name)}">
      <img src="{hero_img}" alt="Vidit Bohra" decoding="async">
    </figure>
  </div>
</header>

<main>

<section id="projects">
  <div class="wrap">
    <h2>Featured work</h2>
    {"".join(feature_blocks)}
  </div>
</section>

<section id="more-projects">
  <div class="wrap">
    <h2>More projects</h2>
    <div class="cards">{"".join(cards)}</div>
  </div>
</section>

<section id="experience">
  <div class="wrap"><h2>Experience</h2>{listing(EXPERIENCE)}</div>
</section>

<section id="education">
  <div class="wrap"><h2>Education</h2>{listing(EDUCATION)}</div>
</section>

<section id="skills">
  <div class="wrap"><h2>Skills</h2><dl class="skills">{skills}</dl></div>
</section>

<section id="coursework">
  <div class="wrap">
    <h2>Coursework</h2>
    <p class="section-note">Courses marked <span class="now">now</span> are running this semester.</p>
    {coursework(COURSEWORK)}
  </div>
</section>

<section id="other">
  <div class="wrap"><h2>Also worked on</h2>{listing(OTHER)}</div>
</section>

</main>
"""
    return shell(
        "Vidit Bohra",
        "Third year mechanical engineering at IIT Bombay. Robotics, mechanism "
        "design, control and estimation.",
        body,
    )


def case_block(slug, section, up, flip):
    """One row in a project's case study.

    A section's "media" is None (text only, full width - a result, a
    limitation, anything without its own natural picture), a single (kind,
    name, caption) tuple (the standard alternating image/text pair), or a
    list of tuples (more than one piece of media for the same point, e.g. a
    render plus the video that shows it running) - which renders full width
    with the media laid out as a horizontal strip below the text, rather
    than squeezing several items into one narrow column.

    Which side a single image falls on is passed in explicitly as `flip`
    rather than picked out with an nth-of-type CSS selector: nth-of-type
    counts by tag name among all sibling divs, including the lede paragraph
    before the first block, so it silently miscounts and the alternation
    comes out wrong from the very first section.
    """
    paras = "".join(f"<p>{e(t)}</p>" for t in section["body"])
    text = f'<div class="cb-text"><h3>{e(section["heading"])}</h3>{paras}</div>'
    media = section["media"]

    if media is None:
        return f'<div class="case-block text-only">{text}</div>'

    if isinstance(media, list):
        tiles = "".join(tile(k, slug, n, c, up) for k, n, c in media)
        return f'<div class="case-block horizontal">{text}<div class="grid cb-strip">{tiles}</div></div>'

    kind, name, caption = media
    fig = (f'<figure class="cb-media" style="--ar:{ratio(slug, name)}">'
           f'{media_button(kind, slug, name, caption, up)}'
           f"<figcaption>{e(caption)}</figcaption></figure>")
    cls = "case-block flip" if flip else "case-block"
    return f'<div class="{cls}">{fig}{text}</div>'


def case_evidence_item(slug, kind, name, caption, up):
    src = asset(up, f"assets/{slug}/{name}.{'mp4' if kind == 'video' else 'jpg'}")
    if kind == "video":
        return f'<div class="clip"><video src="{src}" muted loop playsinline autoplay></video></div>'
    return f'<div class="photo"><img src="{src}" alt="{e(caption)}"><div class="tag">{e(caption)}</div></div>'


def build_case_study_chapter(slug, up, chapter):
    parts = [f'<div class="ch-head"><span class="n">{chapter["num"]}</span><h2>{chapter["title"]}</h2></div>']
    for block in chapter["blocks"]:
        kind = block[0]
        if kind == "evidence":
            items = "".join(case_evidence_item(slug, k, n, c, up) for k, n, c in block[1])
            parts.append(f'<div class="evidence">{items}</div>')
        elif kind == "beat-media":
            label, body, media = block[1], block[2], block[3]
            paras = "".join(f"<p>{e(t)}</p>" for t in body)
            items = "".join(case_evidence_item(slug, k, n, c, up) for k, n, c in media)
            parts.append(
                '<div class="beat-row">'
                f'<div class="beat-row-media">{items}</div>'
                f'<div class="beat"><span class="label">{e(label)}</span>{paras}</div>'
                '</div>'
            )
        else:
            label, body = block[1], block[2]
            cls = "beat muted" if kind == "beat-muted" else "beat"
            paras = "".join(f"<p>{e(t)}</p>" for t in body)
            parts.append(f'<div class="{cls}"><span class="label">{e(label)}</span>{paras}</div>')

    model_attrs = ""
    if chapter.get("model"):
        part_label = "differential wrist" if chapter["mech"] == "Wrist" else chapter["mech"].lower()
        model_src = asset(up, f'assets/{slug}/{chapter["model"]}.glb')
        model_bytes = MODELS.get(f'{slug}/{chapter["model"]}', 0)
        model_attrs = (f' data-part-model="{model_src}" data-part-bytes="{model_bytes}"'
                        f' data-part-label="{e(part_label)}"')

    return (f'<section class="chapter" data-mech="{e(chapter["mech"])}"{model_attrs}>'
            + "".join(parts) + "</section>")


def build_case_study(p):
    """A one-off page, not routed through shell(): the dark, chrome-free
    scrollytelling treatment has nothing in common with the site's normal
    light header/footer, so this builds its own complete document instead
    of fighting shell()'s topbar and footer for control of the page.
    """
    up = "../"
    slug = p["slug"]

    chapters = "".join(build_case_study_chapter(slug, up, c) for c in CASE_STUDY_CHAPTERS)

    closing = CASE_STUDY_CLOSING
    photo_name, photo_alt = closing["photo"]
    photo_src = asset(up, f"assets/{slug}/{photo_name}.jpg")
    result_html = "".join(f"<b>{e(t)}</b>" if tag == "b" else e(t) for t, tag in closing["result"])

    title = f'{p["title"]} | Vidit Bohra'

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(p["summary"])}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(p["summary"])}">
<meta property="og:type" content="website">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{asset(up, "case-study.css")}">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>&#9881;</text></svg>">
<script type="importmap">{{"imports":{{
"three":"https://cdn.jsdelivr.net/npm/three@0.169.0/build/three.module.js",
"three/addons/":"https://cdn.jsdelivr.net/npm/three@0.169.0/examples/jsm/"
}}}}</script>
<script type="module" src="{asset(up, "case-study.js")}"></script>
</head>
<body>

<nav class="case-nav">
  <a class="back" href="{up}index.html">All work</a>
  <button id="theme-toggle" type="button" aria-label="Switch colour theme" title="Switch colour theme"></button>
</nav>

<section class="hero">
  <div class="hero-art"><img src="{photo_src}" alt=""></div>
  <div class="hero-scrim"></div>
  <div class="hero-copy">
    <div class="tags">{"".join(f"<span>{e(t)}</span>" for t in p["tags"][:4])}</div>
    <h1>{e(p["title"])}</h1>
    <p class="sub">{e(p["summary"])}</p>
  </div>
  <div class="scroll-cue"><span>Scroll to explore</span><span class="chev">&#8595;</span></div>
</section>

<div class="layout">
  <div class="stage-wrap" data-model="{asset(up, f"assets/{slug}/arm.glb")}">
    <canvas class="stage-canvas" id="stage-canvas"></canvas>
    <div class="stage-progress">
      <div class="num" id="prog-num">00 / 05</div>
      <div class="name" id="prog-name">Overview</div>
    </div>
    <div class="stage-hud" id="stage-hud"></div>
    <button class="inspect-btn" id="inspect-btn" type="button" hidden>
      <span class="inspect-btn-label">Inspect this part</span>
    </button>
  </div>
  <div class="chapters" id="chapters">
{chapters}
  </div>
</div>

<section class="final">
  <span class="n">The complete system</span>
  <h2>Designed. Built. Tested.</h2>
  <div class="final-photo"><img src="{photo_src}" alt="{e(photo_alt)}"><div class="tag">{e(closing["tag"])}</div></div>
  <p class="result">{result_html}</p>
  <p class="close">{e(closing["close"])}</p>
  <a class="back-link" href="{up}index.html">&#8592; All work</a>
</section>

<dialog class="inspect" id="inspect-dialog">
  <div class="inspect-head">
    <div>
      <div class="inspect-title" id="inspect-title">Part</div>
      <div class="inspect-specs" id="inspect-specs"></div>
    </div>
    <button class="inspect-close" id="inspect-close" type="button" aria-label="Close">&times;</button>
  </div>
  <canvas class="inspect-canvas" id="inspect-canvas"></canvas>
  <div class="inspect-progress" id="inspect-progress"></div>
  <div class="inspect-controls">
    <button class="inspect-reset" id="inspect-reset" type="button">Reset view</button>
    <span class="inspect-hint">Drag to orbit &middot; scroll to zoom &middot; arrow keys also work</span>
  </div>
</dialog>

<script src="{asset(up, "script.js")}"></script>
</body>
</html>
"""


def build_project(index):
    p = PROJECTS[index]
    up = "../"
    kind, name, alt = p["cover"]

    tags = "".join(f"<li>{e(t)}</li>" for t in p["tags"])
    lede = "".join(f'<p>{e(t)}</p>' for t in p.get("lede", []))

    media_row = 0
    blocks = []
    for s in p["sections"]:
        if s["media"] is not None and not isinstance(s["media"], list):
            media_row += 1
        blocks.append(case_block(p["slug"], s, up, flip=media_row % 2 == 0))
    blocks = "".join(blocks)
    tiles = "".join(tile(k, p["slug"], n, c, up) for k, n, c in p["gallery"])

    stats = "".join(
        f'<div class="stat"><div class="n mono">{e(v)}</div><div class="l">{e(l)}</div></div>'
        for v, l in p["stats"]
    )

    extra_head = ""

    n = len(PROJECTS)
    prev_p, prev_num = PROJECTS[index - 1], (index - 1) % n + 1
    next_p, next_num = PROJECTS[(index + 1) % n], (index + 1) % n + 1

    body = f"""
<main class="project-page">

<header class="project-head">
  <div class="wrap">
    <p class="project-num mono">{index + 1:02d} / {len(PROJECTS):02d}</p>
    <h1>{e(p["title"])}</h1>
    <p class="summary">{e(p["summary"])}</p>
    <ul class="annot">
      <li><span class="k">ROLE</span><span class="v">{e(project_role(p))}</span></li>
      <li><span class="k">WHEN</span><span class="v">{e(p["when"])}</span></li>
    </ul>
    <ul class="tags">{tags}</ul>
    {f'<div class="stats">{stats}</div>' if stats else ""}
    <figure class="cover" style="--ar:{ratio(p["slug"], name)}">
      {media_button(kind, p["slug"], name, alt, up)}
    </figure>
  </div>
</header>

<section class="writeup">
  <div class="wrap">
    {f'<div class="prose lede">{lede}</div>' if lede else ""}
    {blocks}
  </div>
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
      <span class="dir">{prev_num:02d} &middot; Previous</span><span class="name">{e(prev_p["title"])}</span></a>
    <a class="pager-link next" href="{next_p["slug"]}.html">
      <span class="dir">{next_num:02d} &middot; Next</span><span class="name">{e(next_p["title"])}</span></a>
  </div>
</nav>

</main>
"""
    return shell(f'{p["title"]} | Vidit Bohra', p["summary"], body, depth=1, extra_head=extra_head)


def main():
    # Fail loudly if the content references media that build_media.py did not produce.
    missing = []
    for p in PROJECTS:
        refs = [p["cover"]] + p["gallery"]
        for s in p["sections"]:
            m = s["media"]
            if m is None:
                continue
            refs += m if isinstance(m, list) else [m]
        for _, name, _ in refs:
            if f'{p["slug"]}/{name}' not in DIMS:
                missing.append(f'{p["slug"]}/{name}')
    if f'{HERO_IMAGE[0]}/{HERO_IMAGE[1]}' not in DIMS:
        missing.append(f'{HERO_IMAGE[0]}/{HERO_IMAGE[1]} (hero image)')
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
        html_out = build_case_study(p) if p.get("case_study") else build_project(i)
        (out / f'{p["slug"]}.html').write_text(html_out, encoding="utf-8")
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
