import datetime
from typing import Tuple


class Class:
    weeks: Tuple[list, list] = ()

    def find_day(self, date):
        for week in self.weeks:
            if not week:
                continue
            for day in week:
                if datetime.date.fromisoformat(day['day']) == date:
                    return day
        return None
