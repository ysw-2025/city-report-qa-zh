#!/usr/bin/env python3
"""
城市级报告质检工具 v2.0
检查报告是否满足city-report-qa Skill的全部规则
包含：8项必含指标 + P0/P1/P2专业硬伤检查
"""
import re
import sys
from pathlib import Path

# 8项必含指标
REQUIRED_INDICATORS = [
    ("全市门店总量", "1. 全市门店总量"),
    ("每万人门店数", "2. 每万人门店数"),
    ("各区门店密度", "3. 各区门店数量与密度"),
    ("价格带分布", "4. 价格带分布"),
    ("评分分布", "5. 评分分布"),
    ("头部品牌TOP", "6. 头部品牌"),
    ("细分品类分布", "7. 细分品类分布"),
    ("市场集中度", "8. 市场集中度"),
]

# P0级硬伤（必须规避）
P0_CHECKS = [
    ("回本测算公式", ["餐位数.*2㎡", "餐位.*客单.*翻台", "月营收.*=.*餐位", "实用面积.*÷", "÷.*㎡"], "回本测算缺少标准公式（餐位数=面积÷2㎡）"),
    ("数据口径统一", ["口径统一", "统一采用.*口径"], "缺少数据口径统一说明"),
    ("数据来源", ["数据来源", "数据样本", "数据口径"], "缺少数据来源说明"),
]

# P1级硬伤
P1_CHECKS = [
    ("品牌边界说明", ["广义.*品类", "狭义.*火锅", "跨品类"], "头部品牌缺少品类边界说明"),
    ("建成区密度", ["建成区", "全域密度", "5-8倍"], "区域密度缺少建成区说明"),
]

# P2级硬伤
P2_CHECKS = [
    ("一句话结论", ["⚡.*结论", "一句话结论", "一句话.*核心"], "缺少一句话结论（前置）"),
    ("死亡带定论", ["死亡带", "尴尬死亡带"], "缺少\"中端死亡带\"行业定论"),
    ("评分爬分", ["前3个月.*权重", "评分爬升", "新店.*差评"], "缺少评分爬分规则"),
    ("隐性成本", ["隐性成本", "排烟.*消防.*证照", "10-15%.*隐性"], "缺少隐性成本提示"),
    ("阴阳街", ["阴阳街", "客流差异.*30", "实地踏勘"], "缺少阴阳街效应提醒"),
    ("升单引导", ["升级.*商圈级", "999元.*商圈", "商圈级.*报告"], "升单引导未前置"),
]

def check_patterns(patterns, content):
    """检查是否有任意一个pattern匹配"""
    for p in patterns:
        if re.search(p, content, re.IGNORECASE):
            return True
    return False

def check_report(file_path):
    """检查报告是否达标"""
    path = Path(file_path)
    if not path.exists():
        return False, f"文件不存在: {file_path}"

    content = path.read_text(encoding='utf-8')

    print(f"\n{'='*60}")
    print(f"质检报告: {file_path}")
    print('='*60)

    score = 0
    p0_issues = []
    p1_issues = []
    p2_issues = []

    # 检查1: 8项必含指标
    print(f"\n【检查1】8项必含指标")
    for i, (name, marker) in enumerate(REQUIRED_INDICATORS, 1):
        if marker in content or name in content:
            print(f"  ✅ [{i}] {name}")
            score += 1
        else:
            print(f"  ❌ [{i}] {name} - 缺失")
    print(f"  得分: {score}/8")

    # 检查2: 一页纸决策结论
    print(f"\n【检查2】一页纸决策结论")
    if "核心决策结论" in content or "核心结论" in content:
        print(f"  ✅ 有决策结论页")
        score += 1
    else:
        print(f"  ❌ 缺失决策结论页")

    # 检查3: 多源数据对比
    print(f"\n【检查3】多源数据对比")
    sources = ["高德", "美团", "大众点评"]
    found = sum(1 for s in sources if s in content)
    if found >= 2:
        print(f"  ✅ 多源对比 ({found}/3)")
        score += 1
    else:
        print(f"  ❌ 缺少多源对比")

    # 检查4: 算账表
    print(f"\n【检查4】算账表")
    if "算账" in content or "投入产出" in content or "回本" in content:
        print(f"  ✅ 有算账维度")
        score += 1
    else:
        print(f"  ❌ 缺少算账表")

    # P0级硬伤检查
    print(f"\n{'='*60}")
    print("【P0级硬伤检查】（必须规避）")
    p0_score = 0
    for name, patterns, desc in P0_CHECKS:
        if check_patterns(patterns, content):
            print(f"  ✅ {name}")
            p0_score += 1
        else:
            print(f"  ❌ {name} - {desc}")
            p0_issues.append(desc)
    print(f"  P0得分: {p0_score}/{len(P0_CHECKS)}")

    # P1级硬伤检查
    print(f"\n【P1级硬伤检查】")
    p1_score = 0
    for name, patterns, desc in P1_CHECKS:
        if check_patterns(patterns, content):
            print(f"  ✅ {name}")
            p1_score += 1
        else:
            print(f"  ⚠️ {name} - {desc}")
            p1_issues.append(desc)
    print(f"  P1得分: {p1_score}/{len(P1_CHECKS)}")

    # P2级硬伤检查
    print(f"\n【P2级硬伤检查】")
    p2_score = 0
    for name, patterns, desc in P2_CHECKS:
        if check_patterns(patterns, content):
            print(f"  ✅ {name}")
            p2_score += 1
        else:
            print(f"  ⚠️ {name} - {desc}")
            p2_issues.append(desc)
    print(f"  P2得分: {p2_score}/{len(P2_CHECKS)}")

    # 综合评分
    print(f"\n{'='*60}")
    print("【综合评分】")
    base_score = score  # 8项指标+结论+多源+算账 = 11分
    total = 11 + len(P0_CHECKS) + len(P1_CHECKS) + len(P2_CHECKS)
    total_score = base_score + p0_score + p1_score + p2_score
    pct = total_score / total * 100

    print(f"  基础指标: {base_score}/11")
    print(f"  P0级: {p0_score}/{len(P0_CHECKS)}")
    print(f"  P1级: {p1_score}/{len(P1_CHECKS)}")
    print(f"  P2级: {p2_score}/{len(P2_CHECKS)}")
    print(f"  综合: {total_score}/{total} ({pct:.0f}%)")

    # 评级
    if p0_score == len(P0_CHECKS) and pct >= 90:
        grade = "✅ 可交付（90分+）"
    elif p0_score >= len(P0_CHECKS) - 1 and pct >= 75:
        grade = "⚠️ 需修正P0（75-89分）"
    elif pct >= 60:
        grade = "🔴 需大量修正（60-74分）"
    else:
        grade = "❌ 不达标（<60分）"
    print(f"  评级: {grade}")

    # 问题汇总
    if p0_issues or p1_issues or p2_issues:
        print(f"\n{'='*60}")
        print("【问题汇总】")
        if p0_issues:
            print("  🔴 P0级（必须修正）:")
            for i in p0_issues:
                print(f"    - {i}")
        if p1_issues:
            print("  🟡 P1级（建议修正）:")
            for i in p1_issues:
                print(f"    - {i}")
        if p2_issues:
            print("  🟢 P2级（可选修正）:")
            for i in p2_issues:
                print(f"    - {i}")

    print('='*60)
    return p0_score == len(P0_CHECKS), p0_issues

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python qa_check.py <报告文件>")
        print("示例: python qa_check.py report.md")
        sys.exit(1)
    ok, issues = check_report(sys.argv[1])
    sys.exit(0 if ok else 1)
