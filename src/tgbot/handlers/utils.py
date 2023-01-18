from tgbot.services.grades_fixer import get_mean_gr, fix_to4, fix_to5
import aiogram.utils.markdown as fmt


def show_grades(grades):
    text = ['вот твои оценки']
    floor_grades = {3: [], 4: [], 5: []}
    for name, grade in grades.items():
        txt, floor_gr = show_grade(name, grade)
        text.append(txt)
        if floor_gr == 0:
            continue
        if floor_gr < 3.5:
            floor_grades[3].append(name)
        elif floor_gr < 4.5:
            floor_grades[4].append(name)
        else:
            floor_grades[5].append(name)
    if floor_grades[5]:
        lessons = ', '.join(floor_grades[5])
        text.append(fmt.text(fmt.hbold('5 выходит по урокам'), lessons))
    if floor_grades[4]:
        lessons = ', '.join(floor_grades[4])
        text.append(fmt.text(fmt.hbold('4 выходит по урокам'), lessons))
    if floor_grades[3]:
        lessons = ', '.join(floor_grades[3])
        text.append(fmt.text(fmt.hbold('3 выходит по урокам'), lessons))
    text.append('чтобы узнать, как исправить оценки можешь использовать /fix_grades')
    return '\n'.join(text)


def show_grade(name, grade):
    gr = ', '.join([str(gra['grade']) for gra in grade]) + ', '
    if gr == ', ':
        return fmt.text(fmt.hunderline(name), fmt.hbold('нет оценок')), 0
    else:
        floor_gr = get_mean_gr([gra['grade'] for gra in grade])
        return fmt.text(fmt.hunderline(name), gr, fmt.hitalic('средняя'), f'{floor_gr:_.3f}'), floor_gr


def lower_keys(grades):
    return {key.lower(): value for key, value in grades.items()}


def show_grades_for_lesson(grades):
    text = []
    for grade in grades:
        gr = grade['grade']
        date = '\n'.join(grade['date'])
        text.append(fmt.text(fmt.text(fmt.hunderline('оценка'), gr), date, sep='\n'))
    grades_list = [grade['grade'] for grade in grades]
    round_grade = get_mean_gr(grades_list)
    text.append(fmt.text(fmt.hitalic('средняя'), round_grade))
    if round_grade < 3.5:
        text.append(show_fix_to4(grades_list))
    if round_grade < 4.5:
        text.append(show_fix_to5(grades_list))
    return '\n'.join(text)


def show_fix_to5(grades_list):
    tooltips = ', '.join([str(i) for i in fix_to5(grades_list)])
    return fmt.text('для', fmt.hitalic('исправления оценки до 5'), 'можно получить', tooltips)


def show_fix_to4(grades_list):
    tooltips = ' или '.join([fmt.text(*var, sep=', ') for var in fix_to4(grades_list)])
    return fmt.text('для', fmt.hitalic('исправления оценки до 4'), 'можно получить', tooltips)


def show_fix_grades(grades):
    text = []
    for name, grade in grades.items():
        txt, round_grade = show_grade(name, grade)
        text.append(txt)
        grades_list = [gr['grade'] for gr in grade]
        if round_grade < 3.5:
            text.append(show_fix_to4(grades_list))
        if round_grade < 4.5:
            text.append(show_fix_to5(grades_list))
    return '\n'.join(text)