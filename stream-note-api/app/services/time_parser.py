from datetime import datetime, timedelta
from typing import Optional
import re


class TimeParser:
    def __init__(self):
        self.weekday_map = {
            "一": 0,
            "二": 1,
            "三": 2,
            "四": 3,
            "五": 4,
            "六": 5,
            "日": 6,
        }

    def parse(
        self, text: str, base_time: Optional[datetime] = None
    ) -> Optional[datetime]:
        if base_time is None:
            base_time = datetime.now()

        text = text.lower()

        date_result = self._parse_date(text, base_time)
        return self._parse_time(text, date_result)

    def _parse_date(self, text: str, base_time: datetime) -> datetime:
        result = base_time.replace(hour=0, minute=0, second=0, microsecond=0)

        if "今天" in text:
            return result
        elif "明天" in text:
            return result + timedelta(days=1)
        elif "后天" in text:
            return result + timedelta(days=2)

        week_match = re.search(r"下周([一二三四五六日])", text)
        if week_match:
            target_day = self.weekday_map.get(week_match.group(1), 0)
            days_ahead = 7 - base_time.weekday() + target_day
            return result + timedelta(days=days_ahead)

        month_day_match = re.search(r"(\d{1,2})月(\d{1,2})日?", text)
        if month_day_match:
            month = int(month_day_match.group(1))
            day = int(month_day_match.group(2))
            try:
                return result.replace(month=month, day=day)
            except ValueError:
                return result

        return result

    def _parse_time(self, text: str, base_date: datetime) -> datetime:
        result = base_date

        time_match = re.search(r"(\d{1,2})[点时](\d{1,2})?分?", text)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2)) if time_match.group(2) else 0

            if "下午" in text or "晚上" in text:
                if hour < 12:
                    hour += 12
            elif "上午" in text or "早上" in text:
                pass

            try:
                result = result.replace(hour=hour, minute=minute)
            except ValueError:
                pass

        return result
