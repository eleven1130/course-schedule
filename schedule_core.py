"""课表解析核心模块。

数据模型：
    - Course：一节课（课程名、星期几、开始时间、结束时间）。
    - Schedule：某人一周的课表，由若干 Course 组成。

时间统一用「从 00:00 起的分钟数」（int）表示，便于区间运算；
对外展示和 CSV 交互使用 "HH:MM" 字符串。
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from typing import Iterable

# 星期一 ~ 星期日 对应数字 1~7
DAY_NAMES = ["", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]


@dataclass(frozen=True)
class Course:
    name: str
    day: int          # 1=Monday ... 7=Sunday
    start: int        # minutes from 00:00
    end: int          # minutes from 00:00

    def __post_init__(self) -> None:
        if not 1 <= self.day <= 7:
            raise ValueError(f"day 必须在 1~7 之间，当前为 {self.day}")
        if self.start >= self.end:
            raise ValueError(
                f"课程 {self.name!r} 的开始时间必须早于结束时间"
            )


@dataclass
class Schedule:
    courses: list[Course] = field(default_factory=list)

    # ---------- 构造 ----------
    @classmethod
    def from_csv(cls, path: str) -> "Schedule":
        """从 CSV 读入课表。

        CSV 表头需包含：name, day, start, end
            name  : 课程名
            day   : 星期几，1~7（1=周一）
            start : 开始时间，HH:MM
            end   : 结束时间，HH:MM
        """
        courses: list[Course] = []
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            required = {"name", "day", "start", "end"}
            if reader.fieldnames is None or not required.issubset(reader.fieldnames):
                raise ValueError(
                    f"CSV 表头必须包含 {sorted(required)}，实际为 {reader.fieldnames}"
                )
            for i, row in enumerate(reader, start=2):
                try:
                    courses.append(Course(
                        name=row["name"].strip(),
                        day=int(row["day"]),
                        start=parse_time(row["start"]),
                        end=parse_time(row["end"]),
                    ))
                except Exception as e:
                    raise ValueError(f"CSV 第 {i} 行解析失败: {e}") from e
        return cls(courses)

    @classmethod
    def from_manual(cls, entries: Iterable[tuple[str, int, str, str]]) -> "Schedule":
        """手动录入。entries 为 (name, day, start_str, end_str) 的可迭代对象。"""
        courses = [
            Course(name=n, day=d, start=parse_time(s), end=parse_time(e))
            for n, d, s, e in entries
        ]
        return cls(courses)

    # ---------- 查询 ----------
    def courses_on(self, day: int) -> list[Course]:
        """返回某一天的课程，按开始时间排序。"""
        return sorted(
            (c for c in self.courses if c.day == day),
            key=lambda c: c.start,
        )

    # ---------- 展示 ----------
    def to_text(self) -> str:
        """生成本周课表的文本视图。"""
        lines: list[str] = []
        lines.append("=" * 56)
        lines.append("本周课表")
        lines.append("=" * 56)
        for day in range(1, 8):
            day_courses = self.courses_on(day)
            lines.append("")
            lines.append(f"【{DAY_NAMES[day]}】")
            if not day_courses:
                lines.append("  （无课）")
                continue
            for c in day_courses:
                lines.append(
                    f"  {fmt_time(c.start):>5} - {fmt_time(c.end):>5}  {c.name}"
                )
        lines.append("")
        lines.append("=" * 56)
        return "\n".join(lines)


# ---------- 时间工具 ----------
def parse_time(s: str) -> int:
    """'HH:MM' -> 分钟数。"""
    s = s.strip()
    try:
        h, m = s.split(":")
        return int(h) * 60 + int(m)
    except Exception as e:
        raise ValueError(f"无法解析时间 {s!r}，应为 'HH:MM'") from e


def fmt_time(minutes: int) -> str:
    """分钟数 -> 'HH:MM'。"""
    return f"{minutes // 60:02d}:{minutes % 60:02d}"
