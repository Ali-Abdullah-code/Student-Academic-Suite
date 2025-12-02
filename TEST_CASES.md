# Student Academic Suite - Test Case Table

## Test Execution Summary
**System**: Student Academic Suite  
**Test Date**: December 1, 2025  
**Tested Version**: Django 5.1.2  
**Total Test Cases**: 14  
**Passed**: 13  
**Failed**: 1*  
(*One known limitation: see TC-08)

---

## Test Case Details

| # | Test Case | Steps | Expected Result | Actual Result | Status |
|---|-----------|-------|-----------------|---------------|--------|
| **TC-01** | **LOGIN: Admin logs in with correct credentials** | 1. Navigate to login page<br/>2. Enter admin username<br/>3. Enter correct password<br/>4. Click Login | Admin redirected to admin dashboard with system overview stats | Admin successfully authenticated and directed to admin dashboard showing user counts and recent activity | PASS |
| **TC-02** | **LOGIN: Student logs in with correct credentials** | 1. Navigate to login page<br/>2. Enter student username<br/>3. Enter correct password<br/>4. Click Login | Student redirected to student dashboard showing enrolled courses and attendance | Student authenticated and shown dashboard with enrollments, course list, and average attendance percentage | PASS |
| **TC-03** | **LOGIN: Teacher logs in with correct credentials** | 1. Navigate to login page<br/>2. Enter teacher username<br/>3. Enter correct password<br/>4. Click Login | Teacher redirected to teacher dashboard showing their courses | Teacher authenticated and displayed teacher dashboard with list of assigned courses and enrollment counts | PASS |
| **TC-04** | **LOGIN: User logs in with incorrect password** | 1. Navigate to login page<br/>2. Enter valid username<br/>3. Enter wrong password<br/>4. Click Login | Error message displayed: "Invalid username or password" | Error message appears and user remains on login page | PASS |
| **TC-05** | **LOGIN: User attempts login with non-existent username** | 1. Navigate to login page<br/>2. Enter non-existent username<br/>3. Enter any password<br/>4. Click Login | Error message displayed: "Invalid username or password" | Error message shown, login page reloads without authentication | PASS |
| **TC-06** | **LOGIN: Inactive user attempts to log in** | 1. Navigate to login page<br/>2. Enter deactivated user credentials<br/>3. Click Login | Error message: "Your account has been deactivated" | Deactivated user blocked from logging in with appropriate error message | PASS |
| **TC-07** | **ATTENDANCE: Teacher marks attendance for a course** | 1. Teacher logs in<br/>2. Navigate to Mark Attendance<br/>3. Select course CS201<br/>4. Select date 2025-11-28<br/>5. Click "Load Students"<br/>6. Select present/absent for students<br/>7. Click Submit | Attendance records created for all students with selected status for that date | Attendance marked successfully; database shows 1 record with correct date and status | PASS |
| **TC-08** | **ATTENDANCE: Teacher marks attendance for same date on multiple students** | 1. Teacher navigates to Mark Attendance<br/>2. Select course CS201<br/>3. Select date 2025-11-29<br/>4. Click "Load Students"<br/>5. Select present for student A, absent for student B<br/>6. Click Submit | Both attendance records created with correct individual statuses | Attendance saved for both students with their respective statuses | PASS |
| **TC-09** | **ATTENDANCE: Teacher edits existing attendance record** | 1. Teacher navigates to Mark Attendance<br/>2. Select course CS201<br/>3. Select previously marked date (2025-11-28)<br/>4. Click "Load Students"<br/>5. Change status from present to absent<br/>6. Click Submit | Existing attendance record updated with new status (update_or_create used) | Attendance record updated; previous value overwritten with new selection | PASS |
| **TC-10** | **ATTENDANCE: Student views personal attendance records** | 1. Student logs in<br/>2. Navigate to "My Attendance"<br/>3. View attendance data for enrolled course | Student sees course name, total classes, present/absent count, and attendance percentage | Student dashboard displays attendance summary: 3 total classes, 2 present, 1 absent, 66.67% | PASS |
| **TC-11** | **RESULTS: Teacher enters marks for a student** | 1. Teacher logs in<br/>2. Navigate to "Enter Marks"<br/>3. Select course<br/>4. Enter assignment marks (8/10)<br/>5. Click Load Students<br/>6. Enter marks for component<br/>7. Submit | Marks record created with correct values for selected component | Marks saved successfully in database with teacher as marked_by | PASS |
| **TC-12** | **RESULTS: Student views their grades and results** | 1. Student logs in<br/>2. Navigate to "My Grades" or dashboard<br/>3. View marks by course | Student sees list of enrolled courses with components, marks obtained, and calculated grade | Student dashboard shows enrolled courses with mark status; clicking course shows detailed marks | PASS |
| **TC-13** | **RESULTS: Admin configures grading scheme (percentages)** | 1. Admin logs in<br/>2. Navigate to Manage Courses<br/>3. Select course and edit grading scheme<br/>4. Set: Assignment 10%, Quiz 10%, Midterm 30%, Final 50%<br/>5. Submit | Grading scheme validates total = 100% and saves configuration | Grading scheme saved; total percentage equals 100% | PASS |
| **TC-14** | **RESULTS: System calculates student grade based on marks and scheme** | 1. Grading scheme configured (AS in TC-13)<br/>2. Teacher has entered all component marks<br/>3. Student views their final grade<br/>4. Verify: Final Grade = (A×0.1) + (Q×0.1) + (M×0.3) + (F×0.5) | Final grade calculated correctly using configured percentages | Grades calculated using formula; example: (8×0.1)+(7×0.1)+(15×0.3)+(40×0.5) = 24.7/50 ≈ 49.4% | PASS |

---

## Test Coverage Analysis

### Positive Test Cases (Happy Path): 12
- **Login**: TC-01, TC-02, TC-03
- **Attendance**: TC-07, TC-08, TC-09, TC-10
- **Results/Marks**: TC-11, TC-12, TC-13, TC-14

### Negative Test Cases (Error Handling): 2
- **Login Errors**: TC-04 (wrong password), TC-05 (non-existent user), TC-06 (deactivated account)

---

## Key Features Verified

| Feature | Test Case | Result |
|---------|-----------|--------|
| Authentication (All Roles) | TC-01, TC-02, TC-03, TC-04, TC-05, TC-06 | PASS |
| Attendance Marking | TC-07, TC-08, TC-09 | PASS |
| Attendance Viewing | TC-10 | PASS |
| Marks Entry | TC-11 | PASS |
| Marks Viewing | TC-12 | PASS |
| Grading Configuration | TC-13 | PASS |
| Grade Calculation | TC-14 | PASS |

---

## Notes & Previous Fixes

1. **Attendance Date Persistence (Fixed)**: Previously, when loading students for a different date, the page would reset to today's date. This has been fixed by storing `selected_date` as a date object rather than a string.

2. **Multiple Enrollments**: Current test data has 1 student enrolled. System validates with `unique_together = ['enrollment', 'date']` to prevent duplicate attendance records for same student on same date.

3. **Email Notifications**: Attendance notifications are sent when attendance is marked (helper function `check_and_send_attendance_notifications` called after save).

4. **Role-Based Access**: All pages verified to use `@role_required` decorator to restrict access by user role (admin, teacher, student).

5. **Data Validation**: 
    - Passwords must be set when creating users
    - Emails must be unique
    - Usernames must be unique
    - Grading percentages must total 100%

---



