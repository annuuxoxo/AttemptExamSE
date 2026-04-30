# Online Examination System — Attempt Exam Subsystem

**Course:** Software Engineering
**Student:** Anushree Upasham | **ID:** 241071077

---

## Overview

This project implements the **Attempt Exam** use case of an Online Examination System as an interactive command-line application in Python. It simulates the complete lifecycle of a student attempting an online exam — from OTP-based identity verification, through randomised question delivery, to final submission — including all alternate flows and exception scenarios defined in the software requirements.

The system also ships a comprehensive **test suite** covering both **black-box** (ECP + BVA) and **white-box** (statement, branch, path, and loop coverage) techniques across 35 test cases.

---

## Use Case: Attempt Exam

### Actors
- **Student** — a registered user enrolled in one or more courses.
- **System** — the Online Examination System.

### Normal Flow
1. Student logs in and selects an active exam from the dashboard.
2. System validates enrolment, exam window, and re-attempt eligibility.
3. System sends a one-time password (OTP) to the student's registered email.
4. Student enters the OTP within the 120-second validity window.
5. System starts the exam session with browser-lock enabled.
6. Questions are presented in randomised order, one at a time.
7. Student answers each question; answers are saved after each entry.
8. Student reviews answers at any point before submitting.
9. Student submits the exam.
10. System evaluates MCQ answers automatically; subjective answers are flagged for manual grading.
11. System displays a submission confirmation with scores and unanswered question count.

### Alternate Flows
| ID | Trigger | Outcome |
|----|---------|---------|
| AF-1 | Student enters a wrong OTP | Warning shown; up to 3 attempts allowed before access is blocked |
| AF-2 | Exam timer expires | Session is auto-submitted with all answers saved so far |

### Exceptions
| ID | Trigger | Outcome |
|----|---------|---------|
| EX-1 | 3 tab-switch events detected | Session is flagged for malpractice and immediately terminated |
| EX-2 | System failure during exam | Partial save of answered questions; session terminates gracefully |

---

## Project Files

```
interactive_attempt_exam.py   ← Main application (run this to attempt an exam)
test_attempt_exam.py          ← Full test suite (20 black-box + 15 white-box TCs)
README.md                     ← This file
```

---

## Requirements

- Python **3.8 or later**
- No third-party packages — the project uses only the Python standard library (`os`, `sys`, `random`, `time`, `datetime`, `enum`, `collections`)

---

## How to Run

### 1. Run the interactive exam portal

```bash
python3 interactive_attempt_exam.py
```

You will see a main menu with three options:

```
  [1]  Attempt Exam
  [2]  View Attempted Exams
  [0]  Exit
```

Select **[1]** to start an exam attempt. The portal walks you through every step interactively.

### 2. Run the test suite

```bash
python3 test_attempt_exam.py
```

The script runs all 35 test cases and prints two result tables — black-box first, then white-box — followed by a combined score summary.

---

## What to Expect When Running the Exam Portal

### Dashboard
After launch you will see a list of three pre-loaded exams:

| Exam | Status |
|------|--------|
| Software Engineering Mid-Sem (120 min) | OPEN |
| Data Structures Quiz 1 (30 min) | OPEN |
| Software Engineering End-Sem (CLOSED) | CLOSED |

Select exam **1** or **2** to proceed; selecting **3** will trigger an `ExamWindowClosedException`.

### OTP Verification
The system prints the simulated OTP directly to the terminal (in a real deployment this would be emailed). Enter it when prompted. Entering a wrong OTP three times locks access for that session.

### Answering Questions
Questions appear one at a time in randomised order. Each prompt shows:
- Question number and total count
- Question type (MCQ / Short Answer / Descriptive)
- Marks allocated
- Time remaining (MM:SS)

**Special inputs you can type at any answer prompt:**

| Input | Effect |
|-------|--------|
| `TAB` | Simulates a tab-switch malpractice event (3 events = termination) |
| `TIMEOUT` | Simulates timer expiry — auto-submits the exam immediately |
| `FAIL` | Simulates a system failure — partial save and session exit |
| *(blank Enter)* | Skips the current question (marked as not attempted) |

For MCQ questions type the full option text (e.g. `A. One Time Password`) or any consistent string — exact-match evaluation is used.

### Submission
After the last question you are prompted to submit. You can:
- Type `yes` to submit immediately
- Type `review` to see all your answers before submitting
- Type `no` to go back through questions and change answers

A confirmation screen shows your MCQ auto-score, questions pending manual grading, and unanswered question IDs.

---

## What to Expect from the Test Suite

```
═══════════════════════════════════════════════════════════════════
  BLACK BOX TEST RESULTS — Attempt Exam Subsystem (Interactive)
═══════════════════════════════════════════════════════════════════
  TC-01  Valid duration — typical              ECP (EC1)     ✔ PASS
  TC-02  Invalid duration — zero               ECP (EC2)     ✔ PASS
  ...
  FINAL SCORE: 20/20 tests passed  |  0 failed

═══════════════════════════════════════════════════════════════════
  WHITE BOX TEST RESULTS — Attempt Exam Subsystem (Interactive)
═══════════════════════════════════════════════════════════════════
  WB-01  ExamSchedule.__init__ ...             Statement     ✔ PASS
  ...
  WB SCORE : 15/15 white-box tests passed  |  0 failed
  BB SCORE : 20/20 black-box tests passed  |  0 failed
  TOTAL    : 35/35 tests passed            |  0 failed
═══════════════════════════════════════════════════════════════════
```

All 35 tests should pass with a clean exit code of `0`. If any test fails, the exit code is `1` and the failing test's "Got" field will show what was returned instead of the expected output.

---

## Test Coverage Summary

### Black-Box Tests (20 TCs) — ECP + BVA

| Group | TCs | Technique | What is tested |
|-------|-----|-----------|----------------|
| Exam duration | TC-01 to TC-07 | ECP + BVA | Valid/invalid/boundary durations; end_time calculation |
| Re-attempt constraints | TC-08 to TC-14 | ECP + BVA | Allow/block re-attempts; exact and over-limit boundaries |
| Combined + interactive | TC-15 to TC-20 | ECP | Closed window, OTP flow, malpractice detection, system failure |

### White-Box Tests (15 TCs)

| Coverage type | TCs | What is tested |
|---------------|-----|----------------|
| Statement | WB-01 to WB-03 | Every assignment in `ExamSchedule`, `Student`, `ExamSession` `__init__` |
| Branch | WB-04 to WB-09 | Both outcomes of `is_active()`, `select_exam()`, `evaluate()` |
| Path | WB-10 to WB-12 | All distinct paths through `verify_otp()` and `flag_malpractice()` |
| Loop | WB-13 to WB-15 | Zero / one / many iterations of the `partial_save` comprehension |

---

## Architecture at a Glance

The system follows an MVC-inspired layered structure:

```
Boundary layer        QuestionUI, AttemptExamUI
      ↓
Controller layer      AttemptExamController, SubmitExamController,
                      StudentVerificationController
      ↓
Entity layer          Student, Exam, ExamSchedule, Question,
                      ExamSession, Response
      ↓
Enums & Exceptions    QuestionType, AttemptStatus,
                      InvalidOTPException, MalpracticeException, etc.
```

Controllers own all business logic. Boundary classes handle I/O only. Entities carry state and minimal validation.

---

*Generated as part of the Software Engineering course project — R5IT2009T.*
