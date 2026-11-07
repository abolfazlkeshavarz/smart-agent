"""Generate personal-knowledge examples about the user (verified facts only).

Run:  python training/generate_personal.py
Out:  training/personal_train.jsonl, training/personal_eval.jsonl

Sources: abolfazl.fun, github.com/abolfazlkeshavarz, the CV PDF, the degree certificate image,
and facts the user stated in this project's chat. NOT included on purpose: national ID,
phone number, emails, father's name, birth date, LinkedIn (login wall). Transcript data was read
from the user's screenshots (the PDF text itself extracts as garbled characters), and unconfirmed claims from the ChatGPT file (the Scientific Reports
paper, "31 repositories" - GitHub shows 32). The preferred name "Liam" was confirmed by the user.
"""
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_dataset import DEVS, styl, sysmsg  # noqa: E402

rng = random.Random(7)

# Each entry: ([question phrasings], answer). Answers are short and speakable.
FACTS = [
    (["what is my name", "who am I"], "You're Abolfazl Keshavarz, and you like to be called Liam."),
    (["what should you call me", "what name should you use for me", "what is my preferred name"],
     "I'll call you Liam."),
    (["what do I do", "what is my profession", "how would you describe me"],
     "You're a computer scientist and software and systems engineer who works across firmware, networks, backend, and deployment."),
    (["where am I based", "where do I live"], "Your website lists Qazvin and Tehran, Iran."),
    (["what is my website", "what is my personal website"], "Your website is abolfazl.fun."),
    (["what is my github username", "what is my GitHub"], "Your GitHub username is abolfazlkeshavarz."),
    (["what is my linkedin"], "Your GitHub links to the LinkedIn profile abolfazl-keshavarz-lin."),
    (["how many github repositories do I have", "how many public repos do I have"],
     "You have 32 public repositories on GitHub."),
    (["what do I have pinned on github", "which repositories are pinned"],
     "Your pinned repositories are Cofferant, Data-Base-Project-TurboJet, Oximeter-using-ESP8266, and Todo."),
    (["when was I born", "what year was I born"], "You were born in 2003."),
    # education
    (["what do I know about my education", "what is my education", "where did I study"],
     "You have a bachelor's degree in computer science from the University of Guilan in Rasht, Iran."),
    (["when did I study computer science", "when did I start university"],
     "You studied computer science at the University of Guilan from October 2021 to September 2025."),
    (["when did I graduate", "when did I finish my bachelor's degree"],
     "You finished your bachelor's degree on September 14, 2025."),
    (["which faculty was my degree from"],
     "Your degree is from the Faculty of Mathematical Sciences at the University of Guilan."),
    (["what was my senior project", "what was my bachelor's project"],
     "Your senior project was deepfake detection on the DF-Platter dataset, classifying images as real or AI-generated with Python, OpenCV, and TensorFlow."),
    (["what courses did I take", "what was my coursework"],
     "Your coursework included artificial intelligence, algorithms, data structures, operating systems, computer networks, databases, advanced programming, and microprocessors."),
    # research
    (["what research did I do", "tell me about my digital twin research"],
     "From February 2024 to June 2025 you were a researcher on a digital twin ecosystem study with an international team, doing data extraction, classification, and analysis for a systematic literature review."),
    (["what are my research interests", "what am I interested in"],
     "Your interests are AI, machine learning, AI security, digital twin ecosystems, IoT, computer vision, and computer networks."),
    # projects
    (["what is Cofferant"],
     "Cofferant is your multi-tenant Django platform for restaurants, with QR menus, online ordering, order tracking, a live kitchen view, payments, coupons, and subscription licensing."),
    (["how is Cofferant deployed", "what technologies does Cofferant use"],
     "Cofferant uses Python and Django, with Docker, Nginx, automated backups, tenant data isolation, and VPS provisioning and migration scripts."),
    (["what is Chatters"],
     "Chatters is your real-time messaging platform with direct and group chats, built with Go, Gin, WebSockets, JWT, React, and PostgreSQL."),
    (["how did I deploy Chatters"],
     "You deployed Chatters on a Linux VPS with systemd, Nginx, HTTPS, and PostgreSQL configured by hand."),
    (["what is RadGard", "what is my GPS tracking project"],
     "RadGard is your vehicle GPS tracking platform. An ESP32 with a NEO-6M GPS and a SIM800C modem reports over MQTT to a Go backend with PostgreSQL and Redis, shown on a React map dashboard."),
    (["what is my guarantee management system"],
     "It's a warranty and repair platform for a home-appliance business, built with Go, Gin, GORM, PostgreSQL, and React."),
    (["what is my attendance system"],
     "It's a face-recognition attendance kiosk where staff clock in at a tablet, with FastAPI and React, and recognition running in the browser so it works offline."),
    (["what is my gym management system"],
     "It's a Persian right-to-left site and admin panel for a gym, built with Node.js, Express, and SQLite, with memberships, schedules, and reports."),
    (["what is VProtocol"],
     "VProtocol is your cross-platform SSH VPN client for Windows and Linux, written in Go with a modern desktop interface."),
    (["what is my plant infection project", "tell me about plant infection classification"],
     "You trained a YOLO11x binary classifier to separate fungal-infected plants from healthy ones, reaching 100 percent top-1 accuracy on the held-out test set."),
    (["what is my ESP32 project", "tell me about my body vitals monitor"],
     "It's your microprocessors course project: an ESP32 station measuring heart rate, SpO2, and body temperature with MAX30100 and MAX30205 sensors, plus a Python Tkinter app that stores the readings."),
    (["what is my ESP8266 project", "what is my oximeter project"],
     "It's a standalone ESP8266 pulse oximeter with a MAX30100 sensor and an OLED display, serving live heart rate and SpO2 from its own web server."),
    (["what kind of projects do I build"],
     "You build full systems end to end, from embedded hardware and backends to deployment, across web platforms, real-time services, AI, and IoT."),
    # experience
    (["where did I work", "what is my work experience"],
     "You were a programming instructor at Poulstar, a website assistant at Bon Asia, a teaching assistant at the University of Guilan, and a hardware technician at Pardis PC."),
    (["what did I teach at Poulstar", "tell me about my teaching"],
     "At Poulstar, from October 2024 to September 2025, you taught electronics, Python, programming fundamentals, and Django to about 150 students."),
    (["what did I do at Bon Asia"],
     "From August 2024 to February 2025 you handled website management and day-to-day technical support at Bon Asia."),
    (["what did I do at Pardis PC"],
     "From October 2021 to September 2022 you diagnosed and repaired computer hardware and power supplies at Pardis PC."),
    (["what courses was I a teaching assistant for"],
     "You were a teaching assistant for Introduction to Programming in fall 2023 and Advanced Programming in winter 2024."),
    # skills
    (["what programming languages do I use"], "You use Python, Go, C and C++ for embedded work, and Bash."),
    (["what backend technologies do I know"], "You work with Django, Gin, REST APIs, WebSockets, and JWT authentication."),
    (["what frontend technologies do I use"], "You use React, HTML, and CSS."),
    (["which databases do I use"], "You use PostgreSQL, MySQL, SQLite, and MongoDB."),
    (["what AI tools do I know"],
     "You work with TensorFlow, OpenCV, machine learning, computer vision, and data preprocessing and analysis."),
    (["what are my infrastructure skills", "what are my networking skills"],
     "You work with Linux administration, Nginx, VPS deployment, SSL and TLS, TCP/IP, KVM and ESXi, and Docker."),
    (["which microcontrollers do I work with"], "You work with the ESP32, ESP8266, ESP-01S, Arduino, and RP2040."),
    (["what tools do I use"], "You use Git and GitHub, Docker, systemd, and LaTeX."),
    (["what languages do I speak"], "You speak Persian natively and English at an advanced level."),
    (["what certificates do I have", "what courses have I completed online"],
     "You completed six Coursera courses in 2023, covering supervised machine learning, Python for data science and AI, data processing with Python, software engineering and image manipulation, introduction to AI, and Python 3 programming."),
    # --- transcript (read from screenshots; course names translated from Persian) ---
    (["how many credits did I pass", "how many units did I pass"],
     "You passed 136 credits out of 157 attempted."),
    (["what was my final gpa", "what is my overall average"],
     "Your overall average is 16.35 out of 20."),
    (["what was my class rank", "how did I rank in my class"],
     "Your transcript shows a rank of 12 out of 35."),
    (["what was my best semester", "which semester had my highest gpa"],
     "Your best semester was the seventh, with an average of 18."),
    (["what was my gpa in my first semester"], "Your first semester average was 17.83."),
    (["what was my gpa in my second semester"], "Your second semester average was 15.69."),
    (["what was my gpa in my third semester"], "Your third semester average was 15.73."),
    (["what was my gpa in my fourth semester"], "Your fourth semester average was 15.14."),
    (["what was my gpa in my fifth semester"], "Your fifth semester average was 16.31."),
    (["what was my gpa in my sixth semester"], "Your sixth semester average was 17.61."),
    (["what was my gpa in my seventh semester"], "Your seventh semester average was 18."),
    (["what was my gpa in my eighth semester", "what was my last semester gpa"],
     "Your eighth and last semester average was 17.61."),
    (["how did I do in the summer terms"],
     "Your two summer terms averaged 12.50 and 13.20, since you used them for retaking harder math courses."),
    (["which courses did I get 20 in", "what courses did I get a perfect score in"],
     "You scored 20 in Operating Systems Principles, Compiler, Artificial Intelligence, Computer Workshop, Fundamentals of Computer and Programming, and your bachelor's project."),
    (["what were my lowest grades"],
     "Your lowest grades were 10 in General Math 1 on the retake and 10 in Fundamentals of Mathematical Analysis."),
    (["which courses did I retake or drop", "which courses did I withdraw from"],
     "You withdrew from and later passed General Math 1, Combinatorics, Linear Algebra, Data Structures and Algorithms, Probability 1, and Numerical Analysis."),
    (["what was my grade in my bachelor's project", "what grade did I get on my senior project"],
     "You got 20 out of 20 on your computer science bachelor's project."),
    (["what grade did I get in operating systems"], "You got 20 out of 20 in Operating Systems Principles."),
    (["what grade did I get in compilers", "what grade did I get in compiler design"],
     "You got 20 out of 20 in Compiler."),
    (["what grade did I get in artificial intelligence"], "You got 20 out of 20 in Artificial Intelligence."),
    (["what grade did I get in microprocessors", "what grade did I get in microprocessor"],
     "You got 19.5 out of 20 in Microprocessor 1."),
    (["what grade did I get in computer networks"], "You got 18.25 out of 20 in Computer Networks."),
    (["what grade did I get in databases", "what grade did I get in database systems"],
     "You got 17.5 out of 20 in Databases."),
    (["what grade did I get in advanced programming"], "You got 18.25 out of 20 in Advanced Programming."),
    (["what grade did I get in computer fundamentals", "what grade did I get in intro to programming"],
     "You got 20 out of 20 in Fundamentals of Computer and Programming."),
    (["what grade did I get in data structures", "what grade did I get in data structures and algorithms"],
     "You got 16.25 out of 20 in Data Structures and Algorithms, after withdrawing the first time."),
    (["what grade did I get in algorithm design", "what grade did I get in design and analysis of algorithms"],
     "You got 13.04 out of 20 in Design and Analysis of Algorithms."),
    (["what grade did I get in computer systems principles"],
     "You got 17.25 out of 20 in Principles of Computer Systems."),
    (["what grade did I get in computational intelligence"],
     "You got 17.75 out of 20 in Fundamentals of Computational Intelligence."),
    (["what grade did I get in computer simulation"], "You got 17 out of 20 in Computer Simulation."),
    (["what grade did I get in secure computing"], "You got 15 out of 20 in Fundamentals of Secure Computing."),
    (["what grade did I get in theory of computation"],
     "You got 13.5 in Theory of Computation, and 13 in Fundamentals of Theory of Computation."),
    (["what grade did I get in logic circuits"], "You got 15.25 out of 20 in Logic Circuits."),
    (["what grade did I get in logic and set theory"],
     "You got 16.7 out of 20 in Fundamentals of Logic and Set Theory."),
    (["what grade did I get in probability"],
     "You got 16 in Fundamentals of Probability, and 12.5 in Probability 1 after withdrawing the first time."),
    (["what grade did I get in combinatorics"], "You got 12 out of 20 in Fundamentals of Combinatorics."),
    (["what grade did I get in linear algebra"],
     "You got 14.5 in Matrices and Linear Algebra, and 14.25 in Numerical Linear Algebra."),
    (["what grade did I get in numerical analysis"],
     "You got 15 out of 20 in Fundamentals of Numerical Analysis."),
    (["what grade did I get in nonlinear optimization"],
     "You got 15.5 out of 20 in Nonlinear Optimization."),
    (["what grade did I get in general math", "what grade did I get in calculus"],
     "You got 10 in General Math 1 on the retake, 15 in General Math 2, and 12 in General Math 3."),
    (["what grade did I get in differential equations"], "You got 13 out of 20 in Differential Equations."),
    (["what grade did I get in engineering economics"], "You got 12.75 out of 20 in Engineering Economics."),
    (["what grade did I get in entrepreneurship"], "You got 19.13 out of 20 in Fundamentals of Entrepreneurship."),
    (["what grade did I get in english", "what grade did I get in specialized english"],
     "You got 17.5 out of 20 in Specialized English, and 17.5 in Foreign Language."),
    (["what grade did I get in physics"], "You got 19 in General Physics 1 and 17 in its lab."),
    (["what grade did I get in the computer workshop"], "You got 20 out of 20 in Computer Workshop."),
    (["what kind of student was I", "how did I do academically"],
     "You finished with a 16.35 average, ranked 12 out of 35, with your strongest results in programming, systems, and AI courses."),
    # --- added from the CV PDF, website and GitHub ---
    (["what is my full name"], "Your full name is Abolfazl Keshavarz Tork."),
    (["what was my gpa", "what was my grade point average"],
     "Your overall GPA was 16.35 out of 20."),
    (["what was my gpa in my last credits"], "You scored 17 out of 20 across your final 65 credits."),
    (["who supervised my senior project", "who was my senior project supervisor"],
     "Dr. Amir Hossein Tabatabaei, an assistant professor at the University of Guilan, supervised your senior project."),
    (["who are my academic references"],
     "Your CV lists Dr. Sadegh Eskandari, Dr. Amir Hossein Tabatabaei, and Dr. Ali Jamalian, all assistant professors of computer science at the University of Guilan."),
    (["what does my website say about me", "how does my website describe me"],
     "It calls you a computer scientist and software and systems engineer who builds dependable systems from embedded devices to production servers."),
    (["what do I like about building systems"],
     "You like owning a system end to end, including provisioning, backups, TLS, and migrations."),
    (["what did teaching teach me"],
     "Working with about 150 students taught you to explain ideas clearly."),
    (["what is GPSTracker"],
     "GPSTracker is your web-based GPS tracking application for location monitoring, published on its own domain."),
    (["what stack does RadGard use"],
     "RadGard uses Go, MQTT, PostgreSQL, Redis, React with TypeScript, MapLibre GL on self-hosted OpenStreetMap tiles, and an ESP32 tracker in C++."),
    (["what is my personnel attendance system built with"],
     "It's built with FastAPI, SQLAlchemy, and React with TypeScript, with Persian right-to-left support and Jalali dates."),
    (["what is my guarantee system's tech stack"], "It uses Go, Gin, GORM, PostgreSQL, React, and role-based access control."),
    (["what is my gym system built with"], "It uses Node.js, Express, SQLite, JWT, Docker, and Nginx."),
    (["what other repositories do I have on github"],
     "They include WareHouseManager, jenkins-python-ci, portfolio, VProtocol, RFID-Attendance-System, DFDetector, Todo_DRF, Algorithm-Project, and Ada learning code."),
    (["what is my RFID project", "what is RFID attendance system"],
     "RFID-Attendance-System is your C++ repository for an RFID-based attendance system."),
    (["what is DFDetector"],
     "DFDetector is a Jupyter notebook repository you forked, a practical project for multi-face deepfake detection."),
    (["what languages have I tried besides the main ones"],
     "You have also written Ada, as shown by your Ada learning repository."),
    (["what networking certificates do I know about"],
     "Your CV lists Network+ and LPIC-1 knowledge."),
    (["how many followers do I have on github"], "You have 18 followers on GitHub."),
    (["what is in my github profile readme"], "It says you graduated in computer science and links your socials."),
    # this project / setup (stated in chat)
    (["what is my current project", "what am I building now"],
     "You're building a local voice assistant that uses a small language model to control your microcontrollers and answer questions."),
    (["which boards do I have", "what hardware do I own"],
     "You have an Arduino, an ESP32, an ESP-01S, and an RP2040."),
    (["what computers do I use for this project"],
     "You use a CPU-only office PC and a home laptop with a GTX 1650 graphics card."),
    (["how should you answer me", "how do I like my answers"],
     "Short, plain spoken sentences in English, with no markdown."),
    (["what language should you speak to me"], "You want me to speak English."),
]


def one(q, a, active):
    user = styl(rng.choice(["", "", "hey, ", "tell me, ", "quick question, "]) + q)
    return {"messages": [sysmsg(active), {"role": "user", "content": user},
                         {"role": "assistant", "content": a}]}


def main():
    rows, seen = [], set()
    for qs, a in FACTS:
        made = 0
        for _ in range(60):
            if made >= 6:
                break
            q = rng.choice(qs)
            r = one(q, a, rng.choice(DEVS))
            key = json.dumps(r, sort_keys=True)
            if key in seen:
                continue
            seen.add(key)
            rows.append(r)
            made += 1
    rng.shuffle(rows)
    cut = len(rows) // 10
    out = ROOT / "training"
    for name, part in (("personal_eval.jsonl", rows[:cut]), ("personal_train.jsonl", rows[cut:])):
        with open(out / name, "w", encoding="utf-8") as f:
            for r in part:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"facts={len(FACTS)} train={len(rows) - cut} eval={cut}")


if __name__ == "__main__":
    main()
