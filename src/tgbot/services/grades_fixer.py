"""Функции, которые определяют, как можно исправить оценки."""

def fix_to4(grades):
    """Как можно исправить оценку до 4."""
    results = []
    count_5 = 0
    while True:
        new_grades = grades.copy()
        added_grades = []
        new_grades += [5] * count_5
        added_grades += [5] * count_5
        if get_mean_gr(new_grades) >= 3.5:
            results.append(added_grades)
            break
        while get_mean_gr(new_grades) < 3.5:
            new_grades.append(4)
            added_grades.append(4)
        results.append(added_grades)
        count_5 += 1
    return results


def fix_to5(grades):
    """Как можно исправить оценку до 5."""
    new_grades = grades.copy()
    added_grades = []
    while get_mean_gr(new_grades) < 4.5:
        new_grades.append(5)
        added_grades.append(5)
    return added_grades


def get_mean_gr(grades):
    """Средняя оценка."""
    if grades:
        sum_grades = sum(grades)
        return sum_grades / len(grades)
    else:
        return 0