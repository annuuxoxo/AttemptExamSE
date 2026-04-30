"""
Online Examination System — Interactive CLI
Course: Software Engineering (R5IT2009T)
Student: Anushree Upasham | ID: 241071077

Run: python3 interactive_attempt_exam.py

Special inputs during exam:
  TAB      → simulate tab-switch malpractice (3 triggers = terminated)
  TIMEOUT  → simulate auto-timeout (submits whatever is saved)
  FAIL     → simulate system failure (partial save + exit)
  (blank)  → skip / leave question unanswered
"""

import os
import sys
import random
import time
from datetime import datetime, timedelta
from enum import Enum


# ══════════════════════════════════════════════
# ENUMS
# ══════════════════════════════════════════════

class QuestionType(Enum):
    MCQ         = "MCQ"
    SHORT       = "Short Answer"
    DESCRIPTIVE = "Descriptive"

class AttemptStatus(Enum):
    IN_PROGRESS         = "In Progress"
    SUBMITTED           = "Submitted"
    AUTO_SUBMITTED      = "Auto Submitted"
    MALPRACTICE_FLAGGED = "Malpractice Flagged"
    PARTIAL_SAVE        = "Partially Saved (System Failure)"


# ══════════════════════════════════════════════
# CUSTOM EXCEPTIONS
# ══════════════════════════════════════════════

class InvalidOTPException(Exception):         pass
class OTPExpiredException(Exception):         pass
class ExamWindowClosedException(Exception):   pass
class ExamAlreadyAttemptedException(Exception): pass
class MalpracticeException(Exception):        pass
class InvalidExamDurationException(Exception): pass
class ReAttemptNotAllowedException(Exception): pass
class SystemFailureException(Exception):      pass


# ══════════════════════════════════════════════
# ENTITIES
# ══════════════════════════════════════════════

class Student:
    def __init__(self, student_id, name, email, enrolled_courses):
        if not student_id.strip():        raise ValueError("Student ID empty.")
        if not name.strip():              raise ValueError("Name empty.")
        if "@" not in email:              raise ValueError("Invalid email.")
        if not enrolled_courses:          raise ValueError("No enrolled courses.")
        self.student_id       = student_id
        self.name             = name
        self.email            = email
        self.enrolled_courses = enrolled_courses
        self.attempted_exams  = []

class Question:
    def __init__(self, question_id, text, q_type, options=None,
                 correct_answer=None, marks=1):
        self.question_id    = question_id
        self.text           = text
        self.q_type         = q_type
        self.options        = options or []
        self.correct_answer = correct_answer
        self.marks          = marks

class ExamSchedule:
    def __init__(self, start_time, duration_minutes):
        if duration_minutes <= 0:
            raise InvalidExamDurationException(
                f"Duration must be > 0. Got: {duration_minutes}")
        self.start_time       = start_time
        self.duration_minutes = duration_minutes
        self.end_time         = start_time + timedelta(minutes=duration_minutes)

    def is_active(self):
        return self.start_time <= datetime.now() <= self.end_time

class Exam:
    def __init__(self, exam_id, course_id, title, schedule,
                 question_bank, allow_reattempt=False, max_reattempts=0):
        if not question_bank: raise ValueError("Question bank empty.")
        self.exam_id         = exam_id
        self.course_id       = course_id
        self.title           = title
        self.schedule        = schedule
        self.question_bank   = question_bank
        self.allow_reattempt = allow_reattempt
        self.max_reattempts  = max_reattempts if allow_reattempt else 0

    def get_randomised_questions(self):
        q = self.question_bank.copy()
        random.shuffle(q)
        return q


# ══════════════════════════════════════════════
# RUNTIME STATE
# ══════════════════════════════════════════════

class Response:
    def __init__(self, question):
        self.question      = question
        self.answer        = None
        self.is_attempted  = False
        self.marks_awarded = 0

    def save_answer(self, answer):
        self.answer       = answer
        self.is_attempted = True

    def evaluate(self):
        if self.question.q_type == QuestionType.MCQ:
            self.marks_awarded = (
                self.question.marks
                if self.answer == self.question.correct_answer else 0
            )
        else:
            self.marks_awarded = None   # manual grading


class ExamSession:
    def __init__(self, student, exam):
        self.session_id        = f"{student.student_id}_{exam.exam_id}_{int(time.time())}"
        self.student           = student
        self.exam              = exam
        self.questions_ordered = exam.get_randomised_questions()
        self.responses         = {q.question_id: Response(q)
                                   for q in self.questions_ordered}
        self.status            = AttemptStatus.IN_PROGRESS
        self.start_timestamp   = datetime.now()
        self.submit_timestamp  = None
        self.malpractice_count = 0
        self.browser_lock      = True

    def time_remaining(self):
        elapsed = (datetime.now() - self.start_timestamp).total_seconds() / 60
        return max(0, self.exam.schedule.duration_minutes - elapsed)

    def is_timed_out(self):
        return self.time_remaining() <= 0

    def record_answer(self, question_id, answer):
        if self.status != AttemptStatus.IN_PROGRESS:
            raise RuntimeError("Session not active.")
        self.responses[question_id].save_answer(answer)

    def flag_malpractice(self):
        self.malpractice_count += 1
        if self.malpractice_count >= 3:
            self.status       = AttemptStatus.MALPRACTICE_FLAGGED
            self.browser_lock = False
            raise MalpracticeException(
                f"Student {self.student.student_id} flagged. Exam terminated.")

    def partial_save(self):
        self.status = AttemptStatus.PARTIAL_SAVE
        saved = [qid for qid, r in self.responses.items() if r.is_attempted]
        return saved


# ══════════════════════════════════════════════
# CONTROLLERS
# ══════════════════════════════════════════════

class StudentVerificationController:
    OTP_VALIDITY_SECONDS = 120
    MAX_ATTEMPTS         = 3

    def __init__(self):
        self._store = {}

    def send_otp(self, student):
        otp = str(random.randint(100000, 999999))
        self._store[student.student_id] = {
            "otp":      otp,
            "expiry":   datetime.now() + timedelta(seconds=self.OTP_VALIDITY_SECONDS),
            "attempts": 0
        }
        return otp

    def verify_otp(self, student, entered):
        rec = self._store.get(student.student_id)
        if not rec:
            raise InvalidOTPException("No OTP found. Request a new one.")
        if datetime.now() > rec["expiry"]:
            del self._store[student.student_id]
            raise OTPExpiredException("OTP expired. Request a new one.")
        rec["attempts"] += 1
        remaining = self.MAX_ATTEMPTS - rec["attempts"]
        if rec["otp"] != entered:
            if rec["attempts"] >= self.MAX_ATTEMPTS:
                raise InvalidOTPException("Max OTP attempts exceeded. Access blocked.")
            raise InvalidOTPException(
                f"Invalid OTP. {remaining} attempt(s) remaining.")
        del self._store[student.student_id]
        return True


class AttemptExamController:
    def __init__(self):
        self.verifier = StudentVerificationController()
        self.sessions = {}

    def select_exam(self, student, exam):
        if exam.course_id not in student.enrolled_courses:
            raise PermissionError(f"Not enrolled in '{exam.course_id}'.")
        if not exam.schedule.is_active():
            raise ExamWindowClosedException(f"'{exam.title}' window is closed.")
        count = student.attempted_exams.count(exam.exam_id)
        if count > 0:
            if not exam.allow_reattempt:
                raise ExamAlreadyAttemptedException(
                    f"Re-attempts not allowed for '{exam.title}'.")
            if count > exam.max_reattempts:
                raise ReAttemptNotAllowedException(
                    f"Re-attempt limit ({exam.max_reattempts}) reached.")
        return exam

    def send_otp(self, student):
        return self.verifier.send_otp(student)

    def verify_and_start(self, student, exam, otp):
        self.verifier.verify_otp(student, otp)
        session = ExamSession(student, exam)
        self.sessions[session.session_id] = session
        return session

    def record_answer(self, session, question_id, answer):
        session.record_answer(question_id, answer)

    def monitor_malpractice(self, session):
        session.flag_malpractice()

    def handle_system_failure(self, session):
        return session.partial_save()


class SubmitExamController:
    def submit(self, session, auto=False):
        if session.status != AttemptStatus.IN_PROGRESS:
            raise RuntimeError("Session not active.")
        session.status           = AttemptStatus.AUTO_SUBMITTED if auto else AttemptStatus.SUBMITTED
        session.submit_timestamp = datetime.now()
        session.browser_lock     = False
        for r in session.responses.values():
            r.evaluate()
        session.student.attempted_exams.append(session.exam.exam_id)
        return self._summary(session)

    def auto_submit(self, session):
        return self.submit(session, auto=True)

    def _summary(self, session):
        mcq_score = sum(
            r.marks_awarded for r in session.responses.values()
            if r.question.q_type == QuestionType.MCQ and r.marks_awarded is not None
        )
        pending = [r.question.question_id for r in session.responses.values()
                   if r.question.q_type != QuestionType.MCQ]
        unanswered = [r.question.question_id for r in session.responses.values()
                      if not r.is_attempted]
        return {
            "Session ID":             session.session_id,
            "Student":                session.student.name,
            "Exam":                   session.exam.title,
            "Status":                 session.status.value,
            "MCQ Auto-Score":         mcq_score,
            "Pending Manual Grading": pending,
            "Unanswered":             unanswered,
            "Submitted At":           str(session.submit_timestamp)
        }


# ══════════════════════════════════════════════
# BOUNDARIES
# ══════════════════════════════════════════════

class QuestionUI:
    def display(self, q, index, total, time_remaining):
        sep()
        mins = int(time_remaining)
        secs = int((time_remaining - mins) * 60)
        print(f"  Question {index + 1} of {total}   "
              f"[{q.q_type.value}]   "
              f"Marks: {q.marks}   "
              f"Time left: {mins:02d}:{secs:02d}")
        print(f"  {'─'*60}")
        print(f"  {q.text}")
        if q.q_type == QuestionType.MCQ:
            print()
            for opt in q.options:
                print(f"    {opt}")
        print()
        print("  Special: TAB = malpractice | TIMEOUT = auto-submit | FAIL = system failure")
        print("  Press Enter to skip this question.")


class AttemptExamUI:
    def __init__(self, exams, student):
        self.exams       = exams
        self.student     = student
        self.attempt_ctrl = AttemptExamController()
        self.submit_ctrl  = SubmitExamController()
        self.question_ui  = QuestionUI()

    # ── Dashboard ──────────────────────────────────────────
    def show_dashboard(self):
        header("EXAM DASHBOARD")
        print(f"  Welcome, {self.student.name}  (ID: {self.student.student_id})")
        print()
        print("  Available Exams:")
        print(f"  {'#':<4} {'Title':<35} {'Course':<14} {'Duration':<10} {'Window'}")
        print(f"  {'─'*80}")
        for i, ex in enumerate(self.exams, 1):
            sc = ex.schedule
            active = "OPEN" if sc.is_active() else "CLOSED"
            print(f"  {i:<4} {ex.title:<35} {ex.course_id:<14} "
                  f"{sc.duration_minutes} min    "
                  f"{sc.start_time.strftime('%H:%M')}–{sc.end_time.strftime('%H:%M')}  [{active}]")
        print()

    # ── Full Flow ───────────────────────────────────────────
    def run(self):
        self.show_dashboard()

        # Step 1
        banner("[STEP 1] Select Exam")
        while True:
            raw = prompt("Enter exam number (or 0 to exit)")
            if raw == "0":
                print("  Exiting. Goodbye.")
                return
            if raw.isdigit() and 1 <= int(raw) <= len(self.exams):
                exam = self.exams[int(raw) - 1]
                break
            print("  Invalid choice. Try again.")

        try:
            self.attempt_ctrl.select_exam(self.student, exam)
        except (ExamWindowClosedException, ExamAlreadyAttemptedException,
                ReAttemptNotAllowedException, PermissionError) as e:
            error(str(e))
            return

        # Step 2
        banner("[STEP 2] Exam Details")
        sc = exam.schedule
        print(f"  Title    : {exam.title}")
        print(f"  Course   : {exam.course_id}")
        print(f"  Duration : {sc.duration_minutes} minutes")
        print(f"  Window   : {sc.start_time.strftime('%H:%M')} → {sc.end_time.strftime('%H:%M')}")
        print(f"  Questions: {len(exam.question_bank)}")
        print(f"  Re-attempt: {'Yes (max ' + str(exam.max_reattempts) + ')' if exam.allow_reattempt else 'No'}")

        # Step 3
        banner("[STEP 3] Instructions")
        print("  1. Questions appear one by one in random order.")
        print("  2. Type your answer and press Enter.")
        print("  3. Press Enter on a blank line to skip a question.")
        print("  4. Type TAB to simulate a tab-switch (3 = malpractice termination).")
        print("  5. Type TIMEOUT to trigger auto-submit.")
        print("  6. Type FAIL to trigger system failure (partial save).")
        print()
        prompt("Press Enter to proceed to OTP verification")

        # Step 4
        banner("[STEP 4] OTP Verification")
        otp = self.attempt_ctrl.send_otp(self.student)
        print(f"  OTP sent to {self.student.email}")
        print(f"  [SIMULATED] Your OTP is: {otp}")
        print()

        # Step 5 — OTP entry with retry loop (Alternate Flow 1)
        banner("[STEP 5] Enter OTP")
        session = None
        while session is None:
            entered = prompt("Enter OTP")
            try:
                session = self.attempt_ctrl.verify_and_start(self.student, exam, entered)
                print(f"\n  [STEP 5] OTP verified. Browser-lock ON. Session started.")
            except OTPExpiredException as e:
                error(str(e))
                print("  Requesting new OTP...")
                otp = self.attempt_ctrl.send_otp(self.student)
                print(f"  [SIMULATED] New OTP: {otp}")
            except InvalidOTPException as e:
                # [ALT FLOW 1]
                warn(f"[ALT FLOW 1] {e}")
                if "blocked" in str(e).lower():
                    error("Access blocked. Exiting.")
                    return

        # Steps 6, 7, 8
        banner("[STEPS 6–8] Answering Questions")
        print("  Questions displayed in random order. Answer each one.")
        print()
        questions = session.questions_ordered
        i = 0
        while i < len(questions):
            q = questions[i]

            # check timeout before each question
            if session.is_timed_out():
                print()
                warn("[ALT FLOW 2] Time is up! Auto-submitting...")
                summary = self.submit_ctrl.auto_submit(session)
                self._show_confirmation(summary)
                return

            self.question_ui.display(q, i, len(questions), session.time_remaining())
            answer = prompt("Your answer")

            # Special inputs
            if answer.strip().upper() == "TAB":
                print()
                warn(f"[EXCEPTION 1] Tab-switch detected!")
                try:
                    self.attempt_ctrl.monitor_malpractice(session)
                    warn(f"  Malpractice event #{session.malpractice_count}. "
                         f"{3 - session.malpractice_count} more = termination.")
                except MalpracticeException as e:
                    error(f"[EXCEPTION 1] {e}")
                    return
                continue   # re-display same question

            if answer.strip().upper() == "TIMEOUT":
                print()
                warn("[ALT FLOW 2] TIMEOUT triggered. Auto-submitting...")
                summary = self.submit_ctrl.auto_submit(session)
                self._show_confirmation(summary)
                return

            if answer.strip().upper() == "FAIL":
                print()
                warn("[EXCEPTION 2] System failure triggered!")
                saved = self.attempt_ctrl.handle_system_failure(session)
                error(f"[EXCEPTION 2] Partial save. Saved responses: {saved}")
                error("Session terminated due to system failure.")
                return

            # Normal answer
            if answer.strip() == "":
                print(f"  Skipped — Q{i+1} marked as not attempted.")
            else:
                self.attempt_ctrl.record_answer(session, q.question_id, answer.strip())
                print(f"  [STEP 8] Answer saved for {q.question_id}.")
            i += 1

        # Step 9 — Submit prompt with review option
        banner("[STEP 9] Submit Exam")
        self._review_and_submit(session)

    def _review_and_submit(self, session):
        while True:
            print()
            unanswered = [r.question.question_id for r in session.responses.values()
                          if not r.is_attempted]
            if unanswered:
                warn(f"  {len(unanswered)} unanswered question(s): {unanswered}")
            ans = prompt("Submit Exam? (yes / review / no)").strip().lower()

            if ans == "yes":
                break

            elif ans == "review":
                self._show_review(session)

            elif ans == "no":
                print("  Returning to questions...")
                questions = session.questions_ordered
                for i, q in enumerate(questions):
                    r = session.responses[q.question_id]
                    self.question_ui.display(q, i, len(questions), session.time_remaining())
                    if r.is_attempted:
                        print(f"  Current answer: {r.answer}")
                    change = prompt("New answer (Enter to keep current)").strip()
                    if change.upper() == "TIMEOUT":
                        warn("[ALT FLOW 2] TIMEOUT — auto-submitting...")
                        summary = self.submit_ctrl.auto_submit(session)
                        self._show_confirmation(summary)
                        return
                    if change:
                        session.record_answer(q.question_id, change)
                        print(f"  [STEP 8] Answer updated for {q.question_id}.")
                banner("[STEP 9] Submit Exam")

            else:
                print("  Please type yes, review, or no.")

        # Step 10
        banner("[STEP 10] Confirming Submission")
        print("  Processing your responses...")
        time.sleep(0.5)
        summary = self.submit_ctrl.submit(session)

        # Step 11
        self._show_confirmation(summary)

    def _show_review(self, session):
        sep()
        print("  ANSWER REVIEW")
        sep()
        for idx, q in enumerate(session.questions_ordered, 1):
            r = session.responses[q.question_id]
            status = r.answer if r.is_attempted else "— not attempted —"
            print(f"  Q{idx} [{q.q_type.value}] {q.text[:55]}")
            print(f"       Answer: {status}")
        sep()

    def _show_confirmation(self, summary):
        # Step 11
        header("[STEP 11] SUBMISSION CONFIRMED")
        for k, v in summary.items():
            print(f"  {k:<26}: {v}")
        sep()
        print()


# ══════════════════════════════════════════════
# DISPLAY HELPERS
# ══════════════════════════════════════════════

def cls():
    os.system("cls" if os.name == "nt" else "clear")

def header(title=""):
    print()
    print("  ╔" + "═" * 58 + "╗")
    if title:
        pad = (58 - len(title)) // 2
        print(f"  ║{' ' * pad}{title}{' ' * (58 - pad - len(title))}║")
    print("  ╚" + "═" * 58 + "╝")
    print()

def banner(text):
    print()
    print(f"  ┌── {text} {'─' * max(0, 52 - len(text))}┐")

def sep():
    print(f"  {'─' * 62}")

def prompt(msg):
    try:
        return input(f"  ▶ {msg}: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n  Interrupted. Exiting.")
        sys.exit(0)

def warn(msg):
    print(f"  ⚠  {msg}")

def error(msg):
    print(f"  ✘  {msg}")


# ══════════════════════════════════════════════
# SAMPLE DATA
# ══════════════════════════════════════════════

def build_sample_data():
    student = Student(
        student_id="241071077",
        name="Anushree Upasham",
        email="anushree@vjti.ac.in",
        enrolled_courses=["R5IT2009T", "CS101"]
    )

    se_questions = [
        Question("Q1", "What does OTP stand for?", QuestionType.MCQ,
                 options=["A. One Time Password", "B. Open Transfer Protocol",
                          "C. Online Test Platform", "D. One To Peer"],
                 correct_answer="A. One Time Password", marks=2),
        Question("Q2", "Which of the following is NOT an OOP principle?",
                 QuestionType.MCQ,
                 options=["A. Inheritance", "B. Compilation",
                          "C. Polymorphism", "D. Abstraction"],
                 correct_answer="B. Compilation", marks=2),
        Question("Q3", "What is a Use Case Diagram used for?", QuestionType.MCQ,
                 options=["A. Show database schema", "B. Show actor-system interactions",
                          "C. Show code flow", "D. Show deployment"],
                 correct_answer="B. Show actor-system interactions", marks=2),
        Question("Q4", "Define encapsulation in OOP.", QuestionType.SHORT, marks=3),
        Question("Q5", "Explain the Attempt Exam use case with its normal flow, "
                       "alternate flows, and exceptions.", QuestionType.DESCRIPTIVE, marks=5),
    ]

    ds_questions = [
        Question("Q1", "Which data structure uses FIFO ordering?", QuestionType.MCQ,
                 options=["A. Stack", "B. Queue", "C. Tree", "D. Graph"],
                 correct_answer="B. Queue", marks=2),
        Question("Q2", "What is the time complexity of binary search?", QuestionType.MCQ,
                 options=["A. O(n)", "B. O(n²)", "C. O(log n)", "D. O(1)"],
                 correct_answer="C. O(log n)", marks=2),
        Question("Q3", "Define a linked list and its types.", QuestionType.SHORT, marks=3),
    ]

    exams = [
        Exam(
            exam_id="SE_MID_2025",
            course_id="R5IT2009T",
            title="Software Engineering Mid-Sem",
            schedule=ExamSchedule(
                start_time=datetime.now() - timedelta(minutes=10),
                duration_minutes=120
            ),
            question_bank=se_questions,
            allow_reattempt=True,
            max_reattempts=1
        ),
        Exam(
            exam_id="DS_QUIZ_01",
            course_id="CS101",
            title="Data Structures Quiz 1",
            schedule=ExamSchedule(
                start_time=datetime.now() - timedelta(minutes=5),
                duration_minutes=30
            ),
            question_bank=ds_questions,
            allow_reattempt=False
        ),
        Exam(
            exam_id="SE_END_2025",
            course_id="R5IT2009T",
            title="Software Engineering End-Sem (CLOSED)",
            schedule=ExamSchedule(
                start_time=datetime.now() - timedelta(hours=5),
                duration_minutes=180
            ),
            question_bank=se_questions,
            allow_reattempt=False
        ),
    ]

    return student, exams


# ══════════════════════════════════════════════
# MAIN MENU
# ══════════════════════════════════════════════

def main():
    student, exams = build_sample_data()

    while True:
        cls()
        header("ONLINE EXAMINATION SYSTEM")
        print(f"  Student : {student.name}")
        print(f"  ID      : {student.student_id}")
        print(f"  Courses : {', '.join(student.enrolled_courses)}")
        print()
        print("  [1]  Attempt Exam")
        print("  [2]  View Attempted Exams")
        print("  [0]  Exit")
        print()

        choice = prompt("Select option")

        if choice == "1":
            portal = AttemptExamUI(exams, student)
            portal.run()
            print()
            prompt("Press Enter to return to menu")

        elif choice == "2":
            sep()
            if not student.attempted_exams:
                print("  No exams attempted yet.")
            else:
                from collections import Counter
                counts = Counter(student.attempted_exams)
                print(f"  {'Exam ID':<20} {'Attempts'}")
                print(f"  {'─'*30}")
                for eid, cnt in counts.items():
                    print(f"  {eid:<20} {cnt}")
            sep()
            prompt("Press Enter to return to menu")

        elif choice == "0":
            print("  Goodbye!")
            sys.exit(0)

        else:
            print("  Invalid option.")
            time.sleep(0.8)


if __name__ == "__main__":
    main()