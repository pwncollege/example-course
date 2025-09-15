# Example Course
This repository features an example course that could be ran on the dojo infrastructure.

# Course Specific Files
In addition to the standard dojo files, a dojo course must create some additional files to identify students and perform course specific grading.


## students.yml
**students.yml** contains a list of unique identifiers, where each identifier corresponds a student in the course.

## course.yml
**student_id** is the prompt users will see, requesting the unique identifier you will use to identify students taking the class.

**syllabus** is a freeform markdown section where instructors may list their syllabus or other instructions for their course.

## grade.py
Because every course has unique grading criteria, grade calculations are definable by course instructors via **grade.py**.  This file must contain a function, `grade(data)`, which performs the grade calculations.  Grade calculations are performed via pyoxide in the users web browser.  Once implemented, students will be able to view their grade in via the course dojo's grading page.  Similarly, course instructors may view the state of the class by leveraging the dojo admin grades page. A basic example can be found at [grade.py](./grade.py).

The data object contains the following:
- `data['solves']` contains the solve information for the user to compute the course grade.
- `data['modules']` contains information about the modules included in the dojo, such as challenge name,description, and whether the challenge is marked as optional or not in dojo.yml.
- `data['course']` is a mapping of `course.yml`.  Any custom data listed under the student ID in `students.yml` will be accessible from `data['course']['student']`.  This allows for customizable data such as deadline extensions, extra credit, or the inclusion of graded assignments outside the pwn.college platform.

# Linking Students with the course
Once the course has been configured, each user must join the private dojo via the join link listed on the admin.  This will grant them access to the dojo, but this does not identify the user as a student.

Students must self-identify with the dojo, by clicking the "course" icon near the top of the dojo and select the "Identity" page.  This page will display the **student_id** prompt defined in `students.yml`.  Students must then enter a unique student identifier listed in the `students.yml` file.  Once this step is complete, the user is considered a student of the course.

Course grades and solves can then be exported by the dojo admin via the admin page.
