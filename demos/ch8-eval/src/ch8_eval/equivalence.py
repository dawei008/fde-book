"""Equivalence classes for fault-type strings.

Ch6 6.3 节那个 40% 评估器把 "伺服系统" 和 "伺服电机" 判错——它们
明明是同一回事。FDE 第一次跑评估容易踩这个坑：把 string equality
当成 semantic equality。这份字典是真实业务上"同义"的一手清单。

Two predictions are semantically equal iff they share at least one
equivalence class. A prediction not in any class falls back to
strict string equality (so unknown labels still grade conservatively).
"""

from __future__ import annotations

# 每个 list 是一个等价类。机械组 / 电气组各几大类。维护者: 合昇售后主管。
EQUIVALENCE_CLASSES: list[list[str]] = [
    # 伺服系列
    ["伺服系统", "伺服电机", "伺服", "伺服驱动"],
    # 回零 / 编码器
    ["回零/编码器", "回零", "编码器", "参考点"],
    # 主轴 / 传动
    ["主轴/传动", "主轴", "传动"],
    # Z 轴 / 丝杠 — 含空格 / 不含空格两版
    ["Z 轴/丝杠", "Z轴/丝杠", "Z 轴", "Z轴", "丝杠"],
    # 传感器
    ["传感器", "感应器", "探头", "限位"],
    # PLC + 通信
    ["PLC/通信", "PLC", "通信", "网络", "上位机"],
    # 液压
    ["液压系统", "液压"],
    # 液压 / 冷却 — 客户口语
    ["液压/冷却", "冷却", "切削液"],
    # 电源
    ["电源系统", "电源", "供电"],
    # 导轨 / 润滑
    ["导轨/润滑", "导轨", "润滑"],
]


def canonical(label: str) -> str | None:
    """Return the first member of the equivalence class containing `label`,
    or None if `label` is not in any known class.
    """
    if not label:
        return None
    for cls in EQUIVALENCE_CLASSES:
        if label in cls:
            return cls[0]
    return None


def semantic_equal(predicted: str, expected: str) -> bool:
    """True iff predicted and expected are in the same equivalence class,
    or — for unknown labels — they string-match exactly.
    """
    if predicted == expected:
        return True
    cp = canonical(predicted)
    ce = canonical(expected)
    if cp is None or ce is None:
        return False  # Unknown labels: only exact match counts
    return cp == ce
