"""课表解析与空闲时段计算 —— 命令行入口。

用法：
    # 需求1：从 CSV 读入并打印周课表
    python main.py show data/zhumenghan.csv

    # 需求1：手动录入
    python main.py show --manual

    # 需求2：计算某个人每天的空闲时段
    python main.py free data/zhumenghan.csv [--day-start 08:00 --day-end 22:00]

    # 需求3：计算多人的共同空闲时间（按时长降序）
    python main.py common data/zhumenghan.csv data/wangtianyi.csv [--day-start 08:00 --day-end 22:00]
"""

from __future__ import annotations

import argparse
import sys

from schedule_core import (
    DAY_NAMES,
    Course,
    Schedule,
    fmt_time,
    parse_time,
)


def cmd_show(args: argparse.Namespace) -> None:
    if args.manual:
        schedule = _read_manual()
    else:
        if not args.csv:
            sys.exit("请提供 CSV 文件路径，或使用 --manual 手动录入")
        schedule = Schedule.from_csv(args.csv)
    print(schedule.to_text())


def _read_manual() -> Schedule:
    print("手动录入课表（输入空行结束）。")
    print("每行格式：课程名,星期几(1-7),开始时间(HH:MM),结束时间(HH:MM)")
    entries: list[tuple[str, int, str, str]] = []
    while True:
        try:
            line = input("> ").strip()
        except EOFError:
            break
        if not line:
            break
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != 4:
            print("  格式错误，应为 4 个字段，已跳过")
            continue
        try:
            name, day_s, start, end = parts
            entries.append((name, int(day_s), start, end))
        except ValueError:
            print("  星期几必须是 1-7 的整数，已跳过")
    return Schedule.from_manual(entries)


def cmd_free(args: argparse.Namespace) -> None:
    from schedule_core import free_time_week

    schedule = Schedule.from_csv(args.csv)
    day_start = parse_time(args.day_start)
    day_end = parse_time(args.day_end)
    gap = args.gap
    print(f"每日可用时间：{args.day_start} - {args.day_end}（合并 ≤{gap} 分钟的小间隔）")
    print("-" * 56)
    for day in range(1, 8):
        slots = free_time_week(schedule, day, day_start, day_end, gap_tol=gap)
        print(f"【{DAY_NAMES[day]}】")
        if not slots:
            print("  （无空闲）")
        for s, e in slots:
            print(f"  {fmt_time(s):>5} - {fmt_time(e):>5}  ({e - s} 分钟)")
    print("-" * 56)


def cmd_common(args: argparse.Namespace) -> None:
    from schedule_core import common_free_time

    schedules = [Schedule.from_csv(p) for p in args.csvs]
    day_start = parse_time(args.day_start)
    day_end = parse_time(args.day_end)
    gap = args.gap
    print(f"共同空闲时间（共 {len(schedules)} 人）")
    print(f"每日可用时间：{args.day_start} - {args.day_end}（合并 ≤{gap} 分钟的小间隔）")
    print("-" * 56)
    results = common_free_time(schedules, day_start, day_end, gap_tol=gap)
    if not results:
        print("（无共同空闲时间）")
    for day, s, e in results:
        print(f"  {DAY_NAMES[day]}  {fmt_time(s):>5} - {fmt_time(e):>5}  ({e - s} 分钟)")
    print("-" * 56)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="课表解析与空闲时段计算")
    sub = p.add_subparsers(dest="cmd", required=True)

    # show
    sp = sub.add_parser("show", help="读入课表并打印周课表文本视图")
    sp.add_argument("csv", nargs="?", help="CSV 文件路径")
    sp.add_argument("--manual", action="store_true", help="手动录入")
    sp.set_defaults(func=cmd_show)

    # free
    sp = sub.add_parser("free", help="计算单人每天的空闲时段")
    sp.add_argument("csv", help="CSV 文件路径")
    sp.add_argument("--day-start", default="08:00", help="每日可用开始时间 (default: 08:00)")
    sp.add_argument("--day-end", default="22:00", help="每日可用结束时间 (default: 22:00)")
    sp.add_argument("--gap", type=int, default=15, help="合并小间隔的阈值（分钟）(default: 15)")
    sp.set_defaults(func=cmd_free)

    # common
    sp = sub.add_parser("common", help="计算多人的共同空闲时间，按时长降序")
    sp.add_argument("csvs", nargs="+", help="多人的 CSV 文件路径")
    sp.add_argument("--day-start", default="08:00", help="每日可用开始时间 (default: 08:00)")
    sp.add_argument("--day-end", default="22:00", help="每日可用结束时间 (default: 22:00)")
    sp.add_argument("--gap", type=int, default=15, help="合并小间隔的阈值（分钟）(default: 15)")
    sp.set_defaults(func=cmd_common)

    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
