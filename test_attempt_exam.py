"""
Black Box Test Script — Attempt Exam Subsystem
Course: Software Engineering (R5IT2009T)
Student: Anushree Upasham | ID: 241071077

Technique : ECP (Equivalence Class Partitioning) + BVA (Boundary Value Analysis)
Parameters : exam_duration (must be > 0) | re-attempt permission constraints
             OTP verification | malpractice detection | system failure | submission
Total TCs  : 20
"""

import sys
import os
from datetime import datetime, timedelta

# ── Import from interactive attempt exam program ──────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

from interactive_attempt_exam import (
    Student, ExamSchedule, Exam, Question, QuestionType,
    AttemptExamController, SubmitExamController,
    StudentVerificationController, ExamSession, Response, AttemptStatus,
    InvalidExamDurationException,
    ExamAlreadyAttemptedException,
    ReAttemptNotAllowedException,
    ExamWindowClosedException,
    InvalidOTPException,
    OTPExpiredException,
    MalpracticeException,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_student(sid="S001", courses=None):
    return Student(
        student_id=sid,
        name="Test Student",
        email="test@vjti.ac.in",
        enrolled_courses=courses or ["R5IT2009T"]
    )

def make_schedule(duration, active=True):
    """active=True → window currently open. active=False → window already closed."""
    if active:
        start = datetime.now() - timedelta(minutes=5)
    else:
        start = datetime.now() - timedelta(hours=3)
    return ExamSchedule(start_time=start, duration_minutes=duration)

def make_exam(duration=60, allow_reattempt=False, max_reattempts=0,
              active=True, exam_id="EX01"):
    schedule = make_schedule(duration, active=active)
    questions = [
        Question("Q1", "Sample MCQ?", QuestionType.MCQ,
                 options=["A", "B", "C", "D"], correct_answer="A", marks=2)
    ]
    return Exam(
        exam_id=exam_id,
        course_id="R5IT2009T",
        title="Test Exam",
        schedule=schedule,
        question_bank=questions,
        allow_reattempt=allow_reattempt,
        max_reattempts=max_reattempts
    )

def run_select(student, exam):
    """Call select_exam on a fresh controller (suppresses print output)."""
    ctrl = AttemptExamController()
    ctrl.select_exam(student, exam)


# ── Test Runner ────────────────────────────────────────────────────────────────

passed = 0
failed = 0
results = []

def run_test(tc_id, name, technique, input_desc, expected, test_fn):
    global passed, failed
    try:
        result_label, ok = test_fn()
    except Exception as e:
        result_label = f"UNEXPECTED ERROR: {type(e).__name__}: {e}"
        ok = False

    status = "PASS" if ok else "FAIL"
    if ok:
        passed += 1
    else:
        failed += 1

    results.append((tc_id, name, technique, input_desc, expected, result_label, status))


# ══════════════════════════════════════════════════════════════════════════════
# TEST CASES — EXAM DURATION (TC-01 to TC-07)
# ══════════════════════════════════════════════════════════════════════════════

# TC-01 | ECP EC1 | Valid duration — typical value
def tc01():
    try:
        make_exam(duration=60)
        return "ExamSchedule created successfully", True
    except Exception as e:
        return str(e), False

run_test("TC-01", "Valid duration — typical",
         "ECP (EC1)", "duration=60",
         "Exam created successfully", tc01)


# TC-02 | ECP EC2 | Invalid duration — zero
def tc02():
    try:
        make_exam(duration=0)
        return "No exception raised", False
    except InvalidExamDurationException as e:
        return f"InvalidExamDurationException: {e}", True

run_test("TC-02", "Invalid duration — zero",
         "ECP (EC2)", "duration=0",
         "InvalidExamDurationException raised", tc02)


# TC-03 | ECP EC3 | Invalid duration — large negative
def tc03():
    try:
        make_exam(duration=-10)
        return "No exception raised", False
    except InvalidExamDurationException as e:
        return f"InvalidExamDurationException: {e}", True

run_test("TC-03", "Invalid duration — large negative",
         "ECP (EC3)", "duration=-10",
         "InvalidExamDurationException raised", tc03)


# TC-04 | BVA EC1 | Minimum valid duration — just above zero
def tc04():
    try:
        e = make_exam(duration=1)
        if e.schedule.duration_minutes == 1:
            return "Exam created with duration=1 min", True
        return "Exam created but duration mismatch", False
    except Exception as ex:
        return str(ex), False

run_test("TC-04", "Boundary — minimum valid (duration=1)",
         "BVA (EC1)", "duration=1",
         "Exam created with 1-min session", tc04)


# TC-05 | BVA EC2 | Boundary — exactly zero
def tc05():
    try:
        make_exam(duration=0)
        return "No exception raised", False
    except InvalidExamDurationException as e:
        return f"InvalidExamDurationException: {e}", True

run_test("TC-05", "Boundary — exactly zero",
         "BVA (EC2)", "duration=0",
         "InvalidExamDurationException raised", tc05)


# TC-06 | BVA EC3 | Just below zero
def tc06():
    try:
        make_exam(duration=-1)
        return "No exception raised", False
    except InvalidExamDurationException as e:
        return f"InvalidExamDurationException: {e}", True

run_test("TC-06", "Boundary — just below zero (duration=-1)",
         "BVA (EC3)", "duration=-1",
         "InvalidExamDurationException raised", tc06)


# TC-07 | BVA EC1 | Large valid duration — verify end_time
def tc07():
    try:
        start = datetime.now()
        s = ExamSchedule(start_time=start, duration_minutes=120)
        expected_end = start + timedelta(minutes=120)
        diff = abs((s.end_time - expected_end).total_seconds())
        if diff < 1:
            return "end_time = start_time + 120 min ✓", True
        return f"end_time mismatch (diff={diff}s)", False
    except Exception as ex:
        return str(ex), False

run_test("TC-07", "Valid large duration — end_time check (duration=120)",
         "BVA (EC1)", "duration=120",
         "end_time = start_time + 120 min", tc07)


# ══════════════════════════════════════════════════════════════════════════════
# TEST CASES — RE-ATTEMPT CONSTRAINTS (TC-08 to TC-14)
# ══════════════════════════════════════════════════════════════════════════════

# TC-08 | ECP EC5 | Re-attempt not allowed, student already attempted
def tc08():
    try:
        student = make_student()
        exam = make_exam(allow_reattempt=False)
        student.attempted_exams.append(exam.exam_id)   # 1 attempt done
        run_select(student, exam)
        return "No exception raised", False
    except ExamAlreadyAttemptedException as e:
        return f"ExamAlreadyAttemptedException: {e}", True

run_test("TC-08", "Re-attempt not allowed — 2nd try",
         "ECP (EC5)", "allow_reattempt=False, attempt_count=1",
         "ExamAlreadyAttemptedException raised", tc08)


# TC-09 | ECP EC4 | Re-attempt allowed, within limit (1st re-attempt)
def tc09():
    try:
        student = make_student()
        exam = make_exam(allow_reattempt=True, max_reattempts=1)
        student.attempted_exams.append(exam.exam_id)   # 1 attempt done → 1 re-attempt left
        run_select(student, exam)
        return "Re-attempt session initiated successfully", True
    except Exception as e:
        return f"{type(e).__name__}: {e}", False

run_test("TC-09", "Re-attempt allowed — within limit (max=1, attempts=1)",
         "ECP (EC4)", "allow_reattempt=True, max=1, attempt_count=1",
         "Session created for 2nd attempt", tc09)


# TC-10 | BVA EC4 | Re-attempt at exact limit boundary
def tc10():
    try:
        student = make_student()
        exam = make_exam(allow_reattempt=True, max_reattempts=1)
        student.attempted_exams.append(exam.exam_id)   # exactly at limit
        run_select(student, exam)
        return "Attempt allowed at exact limit boundary", True
    except Exception as e:
        return f"{type(e).__name__}: {e}", False

run_test("TC-10", "Boundary — at exact re-attempt limit (max=1, attempts=1)",
         "BVA (EC4)", "allow_reattempt=True, max=1, attempt_count=1",
         "Re-attempt allowed", tc10)


# TC-11 | BVA EC6 | Re-attempt one over the limit
def tc11():
    try:
        student = make_student()
        exam = make_exam(allow_reattempt=True, max_reattempts=1)
        student.attempted_exams.extend([exam.exam_id, exam.exam_id])  # 2 attempts done
        run_select(student, exam)
        return "No exception raised", False
    except ReAttemptNotAllowedException as e:
        return f"ReAttemptNotAllowedException: {e}", True

run_test("TC-11", "Boundary — one over re-attempt limit (max=1, attempts=2)",
         "BVA (EC6)", "allow_reattempt=True, max=1, attempt_count=2",
         "ReAttemptNotAllowedException raised", tc11)


# TC-12 | ECP EC6 | max_reattempts=0, student tries 2nd attempt
def tc12():
    try:
        student = make_student()
        exam = make_exam(allow_reattempt=True, max_reattempts=0)
        student.attempted_exams.append(exam.exam_id)   # 1 attempt done, max=0
        run_select(student, exam)
        return "No exception raised", False
    except ReAttemptNotAllowedException as e:
        return f"ReAttemptNotAllowedException: {e}", True

run_test("TC-12", "Re-attempt allowed flag true but max=0 — 2nd try",
         "ECP (EC6)", "allow_reattempt=True, max=0, attempt_count=1",
         "ReAttemptNotAllowedException raised", tc12)


# TC-13 | BVA EC4 | max=2, attempts=2 — exactly at limit
def tc13():
    try:
        student = make_student()
        exam = make_exam(allow_reattempt=True, max_reattempts=2)
        student.attempted_exams.extend([exam.exam_id, exam.exam_id])  # 2 attempts done
        run_select(student, exam)
        return "Re-attempt allowed at max=2, attempts=2", True
    except Exception as e:
        return f"{type(e).__name__}: {e}", False

run_test("TC-13", "Boundary — at limit max=2, attempts=2",
         "BVA (EC4)", "allow_reattempt=True, max=2, attempt_count=2",
         "Re-attempt allowed", tc13)


# TC-14 | BVA EC6 | max=2, attempts=3 — just over limit
def tc14():
    try:
        student = make_student()
        exam = make_exam(allow_reattempt=True, max_reattempts=2)
        student.attempted_exams.extend(
            [exam.exam_id, exam.exam_id, exam.exam_id]   # 3 attempts done
        )
        run_select(student, exam)
        return "No exception raised", False
    except ReAttemptNotAllowedException as e:
        return f"ReAttemptNotAllowedException: {e}", True

run_test("TC-14", "Boundary — one over limit max=2, attempts=3",
         "BVA (EC6)", "allow_reattempt=True, max=2, attempt_count=3",
         "ReAttemptNotAllowedException raised", tc14)


# ══════════════════════════════════════════════════════════════════════════════
# TEST CASES — COMBINED (TC-15)
# ══════════════════════════════════════════════════════════════════════════════

# TC-15 | ECP EC1+EC5 | Valid duration but exam window already closed
def tc15():
    try:
        student = make_student()
        exam = make_exam(duration=90, active=False)   # window closed
        run_select(student, exam)
        return "No exception raised", False
    except ExamWindowClosedException as e:
        return f"ExamWindowClosedException: {e}", True

run_test("TC-15", "Valid duration but exam window closed",
         "ECP (EC1+EC5)", "duration=90, window=closed",
         "ExamWindowClosedException raised", tc15)


# ══════════════════════════════════════════════════════════════════════════════
# NEW TEST CASES — INTERACTIVE SYSTEM SPECIFIC (TC-16 to TC-20)
# ══════════════════════════════════════════════════════════════════════════════

# TC-16 | ECP (OTP-EC1) | Valid OTP → session created successfully
def tc16():
    try:
        student = make_student()
        exam    = make_exam()
        ctrl    = AttemptExamController()
        otp     = ctrl.send_otp(student)       # generate real OTP
        session = ctrl.verify_and_start(student, exam, otp)  # enter correct OTP
        if session is not None and session.status == AttemptStatus.IN_PROGRESS:
            return "Session created with status IN_PROGRESS", True
        return "Session created but unexpected state", False
    except Exception as e:
        return f"{type(e).__name__}: {e}", False

run_test("TC-16", "Valid OTP — session created (IN_PROGRESS)",
         "ECP (OTP-EC1)", "otp=correct, freshly generated",
         "ExamSession created, status=IN_PROGRESS", tc16)


# TC-17 | ECP (OTP-EC2) | Invalid OTP → InvalidOTPException raised
def tc17():
    try:
        student = make_student()
        exam    = make_exam()
        ctrl    = AttemptExamController()
        ctrl.send_otp(student)                          # generate OTP (discard)
        ctrl.verify_and_start(student, exam, "000000")  # enter wrong OTP
        return "No exception raised", False
    except InvalidOTPException as e:
        return f"InvalidOTPException: {e}", True
    except Exception as e:
        return f"Unexpected {type(e).__name__}: {e}", False

run_test("TC-17", "Invalid OTP — InvalidOTPException raised",
         "ECP (OTP-EC2)", "otp=000000 (wrong)",
         "InvalidOTPException raised", tc17)


# TC-18 | ECP (MAL-EC1) | 2 tab-switch events — warning, not terminated
def tc18():
    try:
        student = make_student()
        exam    = make_exam()
        ctrl    = AttemptExamController()
        otp     = ctrl.send_otp(student)
        session = ctrl.verify_and_start(student, exam, otp)

        ctrl.monitor_malpractice(session)   # event #1
        ctrl.monitor_malpractice(session)   # event #2

        if (session.malpractice_count == 2
                and session.status == AttemptStatus.IN_PROGRESS):
            return "malpractice_count=2, session still IN_PROGRESS", True
        return f"Unexpected state: count={session.malpractice_count}, status={session.status}", False
    except MalpracticeException as e:
        return f"MalpracticeException raised too early: {e}", False
    except Exception as e:
        return f"{type(e).__name__}: {e}", False

run_test("TC-18", "2 tab-switches — warning only, session continues",
         "ECP (MAL-EC1)", "tab_switch_count=2, threshold=3",
         "malpractice_count=2, status still IN_PROGRESS", tc18)


# TC-19 | ECP (MAL-EC2) | 3rd tab-switch → MalpracticeException + session terminated
def tc19():
    try:
        student = make_student()
        exam    = make_exam()
        ctrl    = AttemptExamController()
        otp     = ctrl.send_otp(student)
        session = ctrl.verify_and_start(student, exam, otp)

        ctrl.monitor_malpractice(session)   # event #1
        ctrl.monitor_malpractice(session)   # event #2
        ctrl.monitor_malpractice(session)   # event #3 → should raise
        return "No exception raised on 3rd tab-switch", False
    except MalpracticeException as e:
        return f"MalpracticeException: {e}", True
    except Exception as e:
        return f"Unexpected {type(e).__name__}: {e}", False

run_test("TC-19", "3rd tab-switch — MalpracticeException raised",
         "ECP (MAL-EC2)", "tab_switch_count=3",
         "MalpracticeException raised, session flagged", tc19)


# TC-20 | ECP (SYS-EC1) | System failure → partial_save returns answered Q IDs
def tc20():
    try:
        student = make_student()
        exam    = make_exam()
        ctrl    = AttemptExamController()
        otp     = ctrl.send_otp(student)
        session = ctrl.verify_and_start(student, exam, otp)

        # Answer one question before the "failure"
        qid = session.questions_ordered[0].question_id
        ctrl.record_answer(session, qid, "A")

        saved = ctrl.handle_system_failure(session)

        if (session.status == AttemptStatus.PARTIAL_SAVE
                and qid in saved):
            return f"PARTIAL_SAVE status, saved={saved}", True
        return f"Unexpected: status={session.status}, saved={saved}", False
    except Exception as e:
        return f"{type(e).__name__}: {e}", False

run_test("TC-20", "System failure → partial save with answered Q IDs",
         "ECP (SYS-EC1)", "1 answer saved before FAIL trigger",
         "status=PARTIAL_SAVE, answered Q in saved list", tc20)


# ══════════════════════════════════════════════════════════════════════════════
# RESULTS TABLE
# ══════════════════════════════════════════════════════════════════════════════

TOTAL = 20

print()
print("═" * 90)
print("  BLACK BOX TEST RESULTS — Attempt Exam Subsystem (Interactive)")
print("  Course: Software Engineering (R5IT2009T) | Anushree Upasham | 241071077")
print("═" * 90)
print(f"  {'TC':<6} {'Test Case Name':<42} {'Technique':<14} {'Status':<6}")
print("─" * 90)

for (tc_id, name, technique, input_desc, expected, result_label, status) in results:
    marker = "✔" if status == "PASS" else "✘"
    print(f"  {tc_id:<6} {name:<42} {technique:<14} {marker} {status}")

print("─" * 90)
print(f"\n  DETAILED RESULTS")
print("─" * 90)

for (tc_id, name, technique, input_desc, expected, result_label, status) in results:
    marker = "✔" if status == "PASS" else "✘"
    print(f"\n  [{marker}] {tc_id} | {name}")
    print(f"       Technique  : {technique}")
    print(f"       Input      : {input_desc}")
    print(f"       Expected   : {expected}")
    print(f"       Got        : {result_label}")
    print(f"       Status     : {status}")

print()
print("═" * 90)
print(f"  FINAL SCORE: {passed}/{TOTAL} tests passed  |  {failed} failed")
print("═" * 90)

# ══════════════════════════════════════════════════════════════════════════════
# WHITE BOX TESTS — Interactive Attempt Exam  (WB-01 to WB-15)
# Coverage: Statement | Branch | Path | Loop
# ══════════════════════════════════════════════════════════════════════════════

# ── WB Helpers ────────────────────────────────────────────────────────────────

def make_multi_question_exam(n=3, duration=60, active=True):
    """Exam with n MCQ questions — used for loop coverage tests."""
    questions = [
        Question(f"Q{i}", f"MCQ Question {i}?", QuestionType.MCQ,
                 options=["A", "B", "C", "D"], correct_answer="A", marks=2)
        for i in range(1, n + 1)
    ]
    schedule = make_schedule(duration, active=active)
    return Exam(
        exam_id="EX_MULTI",
        course_id="R5IT2009T",
        title="Multi-Question Exam",
        schedule=schedule,
        question_bank=questions,
        allow_reattempt=False
    )

def make_session(student=None, exam=None):
    """Directly create ExamSession (bypasses OTP — unit test only)."""
    student = student or make_student()
    exam    = exam    or make_exam()
    return ExamSession(student, exam)

# ── WB Test Runner ─────────────────────────────────────────────────────────────

wb_passed = 0
wb_failed = 0
wb_results = []

def run_wb_test(tc_id, name, coverage_type, input_desc, expected, test_fn):
    global wb_passed, wb_failed
    try:
        result_label, ok = test_fn()
    except Exception as e:
        result_label = f"UNEXPECTED ERROR: {type(e).__name__}: {e}"
        ok = False
    status = "PASS" if ok else "FAIL"
    if ok:
        wb_passed += 1
    else:
        wb_failed += 1
    wb_results.append((tc_id, name, coverage_type, input_desc, expected, result_label, status))


# ══════════════════════════════════════════════════════════════════════════════
# STATEMENT / CODE COVERAGE  (WB-01 to WB-03)
# Every statement in key __init__ methods must execute at least once
# ══════════════════════════════════════════════════════════════════════════════

# WB-01 | Statement Coverage | ExamSchedule.__init__ valid path
# Covered statements: guard (False), start_time =, duration_minutes =, end_time =
def wb01():
    start = datetime.now()
    s = ExamSchedule(start_time=start, duration_minutes=45)
    checks = [
        s.start_time       == start,
        s.duration_minutes == 45,
        s.end_time         == start + timedelta(minutes=45),
    ]
    if all(checks):
        return "All 3 ExamSchedule assignment statements executed correctly", True
    return f"Statement mismatch: {checks}", False

run_wb_test("WB-01", "ExamSchedule.__init__ — all statements executed",
            "Statement Coverage", "duration=45 (valid)",
            "start_time, duration_minutes, end_time all assigned", wb01)


# WB-02 | Statement Coverage | Student.__init__ valid path
# Covered statements: all 4 guard checks (pass) + 5 attribute assignments
def wb02():
    s = make_student(sid="S999")
    checks = [
        s.student_id       == "S999",
        s.name             == "Test Student",
        "@" in s.email,
        len(s.enrolled_courses) > 0,
        s.attempted_exams  == [],
    ]
    if all(checks):
        return "All Student.__init__ statements executed, attempted_exams=[]", True
    return f"Statement mismatch: {checks}", False

run_wb_test("WB-02", "Student.__init__ — all statements executed",
            "Statement Coverage", "valid student data (sid=S999)",
            "5/5 attributes assigned; attempted_exams=[]", wb02)


# WB-03 | Statement Coverage | ExamSession.__init__ — all 8 fields initialised
# Covered: session_id, questions_ordered, responses, status, start_timestamp,
#          submit_timestamp, malpractice_count, browser_lock
def wb03():
    session = make_session()
    checks = [
        session.session_id is not None and len(session.session_id) > 0,
        isinstance(session.questions_ordered, list) and len(session.questions_ordered) > 0,
        isinstance(session.responses, dict) and len(session.responses) > 0,
        session.status            == AttemptStatus.IN_PROGRESS,
        session.start_timestamp   is not None,
        session.submit_timestamp  is None,
        session.malpractice_count == 0,
        session.browser_lock      is True,
    ]
    if all(checks):
        return "All 8 ExamSession fields initialised correctly", True
    bad = [i + 1 for i, c in enumerate(checks) if not c]
    return f"Fields at positions {bad} failed init check", False

run_wb_test("WB-03", "ExamSession.__init__ — all 8 fields initialised",
            "Statement Coverage", "valid student + active exam",
            "8/8 fields correctly set after __init__", wb03)


# ══════════════════════════════════════════════════════════════════════════════
# BRANCH COVERAGE  (WB-04 to WB-09)
# True and False outcome for every conditional in key methods
# ══════════════════════════════════════════════════════════════════════════════

# WB-04 | Branch Coverage | ExamSchedule.is_active — True branch
def wb04():
    s = make_schedule(duration=120, active=True)
    if s.is_active():
        return "is_active() → True (window open branch)", True
    return "is_active() returned False unexpectedly", False

run_wb_test("WB-04", "is_active() — True branch (window open)",
            "Branch Coverage", "start=now-5min, duration=120min",
            "is_active() returns True", wb04)


# WB-05 | Branch Coverage | ExamSchedule.is_active — False branch
def wb05():
    s = make_schedule(duration=60, active=False)
    if not s.is_active():
        return "is_active() → False (window closed branch)", True
    return "is_active() returned True unexpectedly", False

run_wb_test("WB-05", "is_active() — False branch (window closed)",
            "Branch Coverage", "start=now-3h, duration=60min",
            "is_active() returns False", wb05)


# WB-06 | Branch Coverage | select_exam — not enrolled → PermissionError branch
def wb06():
    student = make_student(courses=["CS101"])
    exam    = make_exam()
    ctrl    = AttemptExamController()
    try:
        ctrl.select_exam(student, exam)
        return "No exception raised", False
    except PermissionError as e:
        return f"PermissionError (not-enrolled branch): {e}", True

run_wb_test("WB-06", "select_exam — not enrolled → PermissionError",
            "Branch Coverage", "student.courses=['CS101'], exam.course='R5IT2009T'",
            "PermissionError raised via not-enrolled branch", wb06)


# WB-07 | Branch Coverage | select_exam — first attempt (count=0) → success branch
def wb07():
    student = make_student()
    exam    = make_exam()
    ctrl    = AttemptExamController()
    try:
        result = ctrl.select_exam(student, exam)
        if result is exam:
            return "select_exam returns exam (first-attempt branch)", True
        return "select_exam returned unexpected value", False
    except Exception as e:
        return f"{type(e).__name__}: {e}", False

run_wb_test("WB-07", "select_exam — count=0 → allowed (success branch)",
            "Branch Coverage", "attempt_count=0",
            "select_exam returns exam without exception", wb07)


# WB-08 | Branch Coverage | Response.evaluate — MCQ correct → full marks branch
def wb08():
    q = Question("Q1", "Test?", QuestionType.MCQ,
                 options=["A", "B"], correct_answer="A", marks=4)
    r = Response(q)
    r.save_answer("A")
    r.evaluate()
    if r.marks_awarded == 4:
        return "MCQ-correct branch: marks_awarded=4 (full marks)", True
    return f"Expected 4, got {r.marks_awarded}", False

run_wb_test("WB-08", "Response.evaluate — MCQ correct → full marks",
            "Branch Coverage", "QuestionType.MCQ, answer=correct",
            "marks_awarded == question.marks (4)", wb08)


# WB-09 | Branch Coverage | Response.evaluate — non-MCQ → None (manual grading branch)
def wb09():
    q = Question("Q2", "Explain X.", QuestionType.SHORT, marks=5)
    r = Response(q)
    r.save_answer("Some answer")
    r.evaluate()
    if r.marks_awarded is None:
        return "non-MCQ branch: marks_awarded=None (manual grading)", True
    return f"Expected None, got {r.marks_awarded}", False

run_wb_test("WB-09", "Response.evaluate — non-MCQ → marks_awarded=None",
            "Branch Coverage", "QuestionType.SHORT",
            "marks_awarded=None (manual grading branch)", wb09)


# ══════════════════════════════════════════════════════════════════════════════
# PATH COVERAGE  (WB-10 to WB-12)
# Distinct complete execution paths through multi-decision methods
# ══════════════════════════════════════════════════════════════════════════════

# WB-10 | Path Coverage | verify_otp — Path A: no OTP record → immediate exit
# Execution path: entry → record is None → raise InvalidOTPException  (exits at guard)
def wb10():
    student = make_student()
    vc = StudentVerificationController()
    # send_otp never called → _store is empty
    try:
        vc.verify_otp(student, "123456")
        return "No exception raised", False
    except InvalidOTPException as e:
        return f"Path A (no record): InvalidOTPException → {e}", True

run_wb_test("WB-10", "verify_otp — Path A: no record → InvalidOTPException",
            "Path Coverage", "no OTP sent before verify",
            "InvalidOTPException raised at 'no-record' guard", wb10)


# WB-11 | Path Coverage | verify_otp — Path B: full success path
# Execution path: entry → record found → not expired → attempt++ → otp matches
#                → delete record → return True
def wb11():
    student = make_student()
    vc  = StudentVerificationController()
    otp = vc.send_otp(student)
    try:
        result = vc.verify_otp(student, otp)
        # After success the record must be deleted; second call should fail
        try:
            vc.verify_otp(student, otp)
            return "OTP record NOT deleted after success", False
        except InvalidOTPException:
            return f"Path B (success): returned {result}, record cleaned up ✓", True
    except Exception as e:
        return f"Unexpected {type(e).__name__}: {e}", False

run_wb_test("WB-11", "verify_otp — Path B: correct OTP → True + record deleted",
            "Path Coverage", "correct OTP entered on 1st attempt",
            "returns True and OTP record is removed", wb11)


# WB-12 | Path Coverage | flag_malpractice — Path A (count<3 warn) + Path B (count==3 terminate)
# Exercises both decision branches inside flag_malpractice in sequence
def wb12():
    session = make_session()
    # Path A — calls 1 and 2 must NOT raise
    session.flag_malpractice()   # count=1
    session.flag_malpractice()   # count=2
    if session.malpractice_count != 2 or session.status != AttemptStatus.IN_PROGRESS:
        return "Path A failed: expected count=2, status=IN_PROGRESS", False
    # Path B — call 3 MUST raise and set MALPRACTICE_FLAGGED
    try:
        session.flag_malpractice()
        return "Path B not taken: no exception on 3rd call", False
    except MalpracticeException:
        if session.status == AttemptStatus.MALPRACTICE_FLAGGED:
            return "Path A (warn×2) + Path B (terminate on 3rd) both covered ✓", True
        return "Exception raised but status not MALPRACTICE_FLAGGED", False

run_wb_test("WB-12", "flag_malpractice — Path A (warn) + Path B (terminate)",
            "Path Coverage", "3 successive flag_malpractice() calls",
            "count<3 → warn; count==3 → MalpracticeException + FLAGGED", wb12)


# ══════════════════════════════════════════════════════════════════════════════
# LOOP COVERAGE  (WB-13 to WB-15)
# Zero / One / Many iterations of the partial_save comprehension loop
# ══════════════════════════════════════════════════════════════════════════════

# WB-13 | Loop Coverage | partial_save — 0 iterations (nothing answered)
# Loop body executes 0 times → saved list must be empty
def wb13():
    exam    = make_multi_question_exam(n=3)
    session = make_session(exam=exam)
    # No answers recorded → all responses.is_attempted == False
    saved = session.partial_save()
    if saved == [] and session.status == AttemptStatus.PARTIAL_SAVE:
        return "Loop 0 iters: saved=[], status=PARTIAL_SAVE ✓", True
    return f"Unexpected: saved={saved}, status={session.status}", False

run_wb_test("WB-13", "partial_save loop — 0 iterations (no answers)",
            "Loop Coverage", "3-question exam, 0 answers recorded",
            "saved=[], status=PARTIAL_SAVE", wb13)


# WB-14 | Loop Coverage | partial_save — 1 iteration (exactly one answer)
# Loop body executes exactly once
def wb14():
    exam    = make_multi_question_exam(n=3)
    session = make_session(exam=exam)
    qid     = session.questions_ordered[0].question_id
    session.record_answer(qid, "A")   # only Q1 answered
    saved = session.partial_save()
    if len(saved) == 1 and qid in saved:
        return f"Loop 1 iter: saved=[{qid}] ✓", True
    return f"Unexpected: saved={saved}", False

run_wb_test("WB-14", "partial_save loop — 1 iteration (1 answer saved)",
            "Loop Coverage", "3-question exam, 1 answer recorded",
            "saved contains exactly 1 question ID", wb14)


# WB-15 | Loop Coverage | partial_save — N iterations (all 3 answered)
# Loop body executes 3 times — many-iteration coverage
def wb15():
    exam    = make_multi_question_exam(n=3)
    session = make_session(exam=exam)
    for q in session.questions_ordered:
        session.record_answer(q.question_id, "A")   # answer every question
    saved   = session.partial_save()
    all_ids = {q.question_id for q in session.questions_ordered}
    if len(saved) == 3 and all_ids == set(saved):
        return f"Loop 3 iters: saved={sorted(saved)} ✓", True
    return f"Unexpected: saved={saved}, expected={sorted(all_ids)}", False

run_wb_test("WB-15", "partial_save loop — N iterations (all 3 answers saved)",
            "Loop Coverage", "3-question exam, 3 answers recorded",
            "saved contains all 3 question IDs", wb15)


# ══════════════════════════════════════════════════════════════════════════════
# WHITE BOX RESULTS TABLE
# ══════════════════════════════════════════════════════════════════════════════

WB_TOTAL = 15

print()
print("═" * 95)
print("  WHITE BOX TEST RESULTS — Attempt Exam Subsystem (Interactive)")
print("  Course: Software Engineering (R5IT2009T) | Anushree Upasham | 241071077")
print("═" * 95)
print(f"  {'TC':<7} {'Test Case Name':<44} {'Coverage Type':<22} {'Status':<6}")
print("─" * 95)

for (tc_id, name, ctype, input_desc, expected, result_label, status) in wb_results:
    marker = "✔" if status == "PASS" else "✘"
    print(f"  {tc_id:<7} {name:<44} {ctype:<22} {marker} {status}")

print("─" * 95)
print(f"\n  DETAILED WHITE BOX RESULTS")
print("─" * 95)

for (tc_id, name, ctype, input_desc, expected, result_label, status) in wb_results:
    marker = "✔" if status == "PASS" else "✘"
    print(f"\n  [{marker}] {tc_id} | {name}")
    print(f"       Coverage   : {ctype}")
    print(f"       Input      : {input_desc}")
    print(f"       Expected   : {expected}")
    print(f"       Got        : {result_label}")
    print(f"       Status     : {status}")

print()
print("═" * 95)
print(f"  WB SCORE : {wb_passed}/{WB_TOTAL} white-box tests passed  |  {wb_failed} failed")
print("─" * 95)
print(f"  BB SCORE : {passed}/{TOTAL} black-box tests passed   |  {failed} failed")
print("─" * 95)
print(f"  TOTAL    : {passed + wb_passed}/{TOTAL + WB_TOTAL} tests passed        |  {failed + wb_failed} failed")
print("═" * 95)

if (failed + wb_failed) > 0:
    sys.exit(1)