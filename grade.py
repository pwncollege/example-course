import pandas as pd

letter_grades = {
    "A+": 1.00,
    "A": 0.93,
    "A-": 0.90,
    "B+": 0.88,
    "B": 0.83,
    "B-": 0.80,
    "C+": 0.78,
    "C": 0.70,
    "E": 0.00,
}

assignment_starts = {
    "hello": "2025-08-21T16:30:00-07:00",
    "world": "2025-08-28T16:30:00-07:00",
    "Reverse Engineering":  "2025-09-04T16:30:00-07:00",
    "demo":  "2025-09-11T16:30:00-07:00",
    "lectures":  "2025-09-18T16:30:00-07:00",
}

assignment_deadlines = {
    "hello": {
        "Challenges": "2025-08-28T16:30:00-07:00",
    },
    "world": {
            "Challenges": "2025-09-04T16:30:00-07:00",
    },
    "demo": {
            "Challenges": "2025-09-11T16:30:00-07:00",
    },
    "lectures": {
            "Challenges": "2025-09-18T16:30:00-07:00",
    },
    "Reverse Engineering": {
            "Challenges": "2025-09-18T16:30:00-07:00",
    },
}

assignment_type_weight = {
    "Challenges": 1,
}

late_credit = 0.5
late_credit_end = None

#
# Grading Logic
#

for module, deadlines in assignment_deadlines.items():
    for assignment_type, deadline in deadlines.items():
        deadlines[assignment_type] = pd.to_datetime(deadline)


def grade(data):
    print(data)
    print(data['solves'])
    print(data['modules'])
    print(data['course'])
    if any(field not in data for field in ["solves", "modules", "course"]):
        return None

    now = pd.Timestamp.now(tz="UTC")

    solves_df = pd.DataFrame(data["solves"], columns=["module_id", "challenge_id", "timestamp"]).set_index(["module_id", "challenge_id"])
    solves_df["timestamp"] = pd.to_datetime(solves_df["timestamp"], format="mixed", utc=True)

    modules_df = (
        pd.json_normalize(
            data["modules"],
            record_path="challenges",
            meta=["id", "name", "required", "description"],
            record_prefix="challenge_",
            meta_prefix="module_",
            errors='ignore',
        )
        .set_index(["module_id", "challenge_id"])
        .join(solves_df["timestamp"].rename("solved_timestamp"), how="left")
    )

    # Do not count optional challenges
    modules_df = modules_df[modules_df['challenge_required'] == True]

    # Individual deadline extensions can be added in the students.yml file
    extensions = data["course"].get("student", {}).get("extensions", {})

    assignments_df = (
        pd.DataFrame([
            {
                "module": module,
                "type": assignment_type,
                "deadline": assignment_deadline,
                "start": pd.to_datetime(assignment_starts[module], format="mixed", utc=True),
                "extension": pd.Timedelta(days=extensions.get(module, 0)),
                "weight": assignment_type_weight[assignment_type],
            }
            for module, deadlines in assignment_deadlines.items()
            for assignment_type, assignment_deadline in deadlines.items()
        ])
        .set_index(["module", "type"])
    )

    assignments_df = assignments_df[assignments_df['start'] < now]
    assignment_data = assignments_df.apply(grade_assignment, axis=1, modules_df=modules_df)
    flat = {
        f"{module} - {typ}": row.to_dict()
        for (module, typ), row in assignment_data.iterrows()
    }

    assignments = format_assignments(flat)
    total_weight = sum(a['weight'] for a in assignments)
    assignments_score = sum([a['credit'] * a['weight'] / total_weight for a in assignments])

    overall_letter = next(letter for letter, credit in letter_grades.items() if assignments_score >= credit)

    return {
        "overall": dict(credit=assignments_score, letter=overall_letter),
        "assignments": assignments
    }


def grade_assignment(row, modules_df):
    '''
    Module grading logic that allows for
    - Individual deadline extensions
    - Late credit with configurable cutoff
    - Assignment weightings
    '''

    name, assignment_type = row.name
    module_id = name.lower().replace(' ', '-')
    res = dict()
    res['target'] = 0
    res['credit'] = 0 
    res['on_time'] = 0
    res['late'] = 0
    res['weight'] =  assignment_type_weight[assignment_type]

    credit = 0

    if module_id not in modules_df.index.get_level_values('module_id'):
        return res

    relevant_chals = modules_df.xs(module_id, level="module_id", drop_level=False)
    deadline = row.deadline + row.extension
    on_time = len(relevant_chals[relevant_chals['solved_timestamp'] < deadline])
    late_solves = relevant_chals[relevant_chals['solved_timestamp'] >= deadline]
    if late_credit_end:
        late_solves = late_solves[late_solves['solved_timestamp'] <= late_credit_end]
    late_count = len(late_solves)
    target = len(relevant_chals)

    if assignment_type == 'Challenges':
        credit = on_time / target + late_count / target * late_credit

    res['target'] = target
    res['credit'] = credit
    res['on_time'] = on_time
    res['late'] = late_count
    res['deadline'] = deadline
    res['weight'] =  assignment_type_weight[assignment_type]

    return pd.Series(res)

def format_assignments(flat_dat):
    '''
    Formats data to fit the grades page template.
    '''
    assignments = []

    for name, vals in flat_dat.items():
        if vals['late'] > 0:
            prog_string = f"{vals['on_time']:.0f} + ({vals['late']:.0f}) / {vals['target']:.0f}"
        else:
            prog_string = f"{vals['on_time']:.0f} / {vals['target']:.0f}"

        assignments.append({
          "name": name,
          "deadline": str(vals['deadline']),
          "weight": int(vals['weight']),
          "progress": prog_string,
          "credit": vals['credit'],
        })

    return assignments
