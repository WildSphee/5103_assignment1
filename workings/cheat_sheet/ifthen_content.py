"""Side 4 content: turning "if... then..." rules into linear constraints.

CHECKS pairs each rule's meaning in words (a Python test on 0/1 values) with its
constraint(s); validate.py enumerates every 0/1 combination to prove they match.
"""

INTRO=('**Set-up:** six candidate projects; xᵢ=1 means "do project i", xᵢ=0 means "skip it". '
 'Every rule below becomes a **linear** constraint on these switches, so the model stays an IP the solver can handle. '
 '**Good habit:** test each rule by plugging in 0s and 1s and checking it accepts every allowed combo and rejects every forbidden one.')

CORE_RULES=[
 ['At most one of projects 1, 2, 3','x₁ + x₂ + x₃ ≤ 1','Only one switch can be on','any two or all three on'],
 ['Exactly two of projects 2–6','x₂ + x₃ + x₄ + x₅ + x₆ = 2','Exactly two switches on','any count other than 2 (0, 1, 3, 4, 5 on)'],
 ['If 1, then 4','x₁ ≤ x₄','If x₁ = 1, x₄ is forced to be 1','(x₁, x₄) = (1, 0) only'],
 ['If 2, then NOT 5','x₂ + x₅ ≤ 1','They can’t both be on','(x₂, x₅) = (1, 1) only'],
 ['If not 1, then 6','x₁ + x₆ ≥ 1','At least one of them must be on','(x₁, x₆) = (0, 0) only'],
 ['4 and 5 go together','x₄ = x₅','Both on or both off','(1, 0) and (0, 1)'],
 ['If 3, then 1 or 5','x₃ ≤ x₁ + x₅','Doing 3 needs at least one helper','(x₃, x₁, x₅) = (1, 0, 0) only'],
 ['If 3 AND 4, then 6','x₆ ≥ x₃ + x₄ − 1','The right side only reaches 1 when both are on','(x₃, x₄, x₆) = (1, 1, 0) only'],
]

MORE_RULES=[
 ['If 2, then 3 AND 4','x₂ ≤ x₃  and  x₂ ≤ x₄','One row per required project. 2x₂ ≤ x₃ + x₄ is also valid for 0/1 but gives a weaker LP relaxation'],
 ['If 1 or 2, then 3','x₁ ≤ x₃  and  x₂ ≤ x₃','Either trigger alone forces 3. Not x₁ + x₂ ≤ x₃ (that wrongly bans doing 1 and 2 together)'],
 ['If 1 and 2, then NOT 3','x₁ + x₂ + x₃ ≤ 2','Blocks only all three on'],
 ['If 1, then at least 2 of {3, 4, 5}','x₃ + x₄ + x₅ ≥ 2x₁','x₁ = 0 gives ≥ 0 (no effect); x₁ = 1 gives ≥ 2'],
 ['If 1, then none of {2, 3}','x₂ + x₃ ≤ 2(1 − x₁)','x₁ = 1 makes the right side 0; x₁ = 0 makes it 2 (no effect)'],
 ['Exactly one of 1, 2 (either/or)','x₁ + x₂ = 1','Blocks both off and both on'],
 ['1 and 2 can’t both be skipped','x₁ + x₂ ≥ 1','Same as "if not 1 then 2" and "1 unless 2"'],
 ['1 only if 4   /   1 if 4','x₁ ≤ x₄   /   x₄ ≤ x₁','"Only if" points at the requirement: "1 only if 4" = "if 1 then 4"'],
 ['x₁ = x₂ · x₃  (all binary)','x₁ ≤ x₂,  x₁ ≤ x₃,  x₁ ≥ x₂ + x₃ − 1','x₁ = 1 exactly when both are on (an AND switch)'],
 ['x₁ = x₂ · x₃  (x₂ binary, 0 ≤ x₃ ≤ M)','−Mx₂ ≤ x₁ ≤ Mx₂;  −M(1 − x₂) ≤ x₁ − x₃ ≤ M(1 − x₂)','x₂ = 0 forces x₁ = 0; x₂ = 1 forces x₁ = x₃'],
 ['If y = 1, then aᵀx ≤ b  (x continuous)','aᵀx ≤ b + M(1 − y)','y = 1: the real row; y = 0: M makes it slack. M = valid upper bound on aᵀx − b'],
 ['Either aᵀx ≤ b OR cᵀx ≤ d','aᵀx ≤ b + My;  cᵀx ≤ d + M(1 − y)','y picks which row must hold; the other is switched off'],
 ['Produce x > 0 only if facility y is open','0 ≤ x ≤ My','y = 0 forces x = 0; add fixed cost K·y to the objective'],
]

NOTES=[
'''## A RECIPE THAT WORKS FOR ANY RULE
**1. Write it as logic:** IF (conditions) THEN (results).
**2. Find the one bad case:** the rule is broken only when **every** condition is true and the result is false. Your constraint must cut off exactly that corner.
**3. Literals:** "i is done" → xᵢ; "i is skipped" → (1 − xᵢ).
**4. One-line formula for "THEN A OR B":** ∑(1 − condition literals) + ∑(result literals) ≥ 1. For "THEN A AND B", write one row per result.
**Examples:** If 3 AND 4 then 6: (1−x₃)+(1−x₄)+x₆ ≥ 1 ⇒ **x₆ ≥ x₃+x₄−1**. If 3 then 1 or 5: (1−x₃)+x₁+x₅ ≥ 1 ⇒ **x₃ ≤ x₁+x₅**. If not 1 then 6: x₁+x₆ ≥ 1. If 2 then not 5: (1−x₂)+(1−x₅) ≥ 1 ⇒ **x₂+x₅ ≤ 1**.
## THE 0/1 TEST, WORKED
List every 0/1 combo (2 variables = 4 rows, 3 = 8). Mark what the words allow, then plug in.
**x₆ ≥ x₃+x₄−1**, combos (x₃,x₄,x₆): 000 ✓ 001 ✓ 010 ✓ 011 ✓ 100 ✓ 101 ✓ **110 ✗** 111 ✓. Only "3 and 4 on, 6 off" fails. Correct.
**x₃ ≤ x₁+x₅**, combos (x₃,x₁,x₅): only **100** gives 1 ≤ 0 ✗; all 7 others pass. Correct.
**Wrong try x₆ ≥ x₃ and x₆ ≥ x₄:** blocks 100-style rows (3 on, 4 off, 6 off) the words allow. That means "if 3 OR 4 then 6": too strong.''',
'''## COMMON TRAPS
**Direction:** "if 1 then 4" is x₁ ≤ x₄. Writing x₄ ≤ x₁ means the converse "if 4 then 1".
**Contrapositive is the same rule:** "if not 4 then not 1" also gives x₁ ≤ x₄.
**Three look-alikes:** "if not 1 then 6": x₁+x₆ ≥ 1. "If 1 then not 6": x₁+x₆ ≤ 1. "Exactly one of 1, 6": x₁+x₆ = 1.
**OR uses a sum:** "if 3 then 1 or 5" is x₃ ≤ x₁+x₅. 2x₃ ≤ x₁+x₅ would demand both.
**AND in the condition needs −1:** x₆ ≥ x₃+x₄−1; when only one is on the right side is 0 and nothing is forced.
**An if-then never forces anything when the condition is off.** Check the "condition off" rows are all still allowed.
**Big-M:** choose the smallest valid M; test y = 0 and y = 1 separately.
## QUICK DRILL (cover the answers)
**a)** At least 2 of projects 1–4 → x₁+x₂+x₃+x₄ ≥ 2
**b)** If 5, then neither 1 nor 6 → x₅+x₁ ≤ 1, x₅+x₆ ≤ 1
**c)** If not 4, then 5 and 6 → 1−x₄ ≤ x₅, 1−x₄ ≤ x₆
**d)** If 2, then exactly one of 3, 4 → x₃+x₄ ≥ x₂, x₃+x₄ ≤ 2−x₂
**e)** At most 3 of projects 1–6, and if 6 then 1 → ∑xᵢ ≤ 3, x₆ ≤ x₁
**f)** Do 1 if and only if both 2 and 3 → x₁ ≤ x₂, x₁ ≤ x₃, x₁ ≥ x₂+x₃−1''',
]

# (meaning in words, constraint) pairs over x[1..6]; validate.py checks all 64 combos.
CHECKS={
 'at most one of 1,2,3':(lambda x:x[1]+x[2]+x[3]<=1, lambda x:x[1]+x[2]+x[3]<=1),
 'exactly two of 2-6':(lambda x:sum(x[2:7])==2, lambda x:x[2]+x[3]+x[4]+x[5]+x[6]==2),
 'if 1 then 4':(lambda x:(not x[1]) or x[4], lambda x:x[1]<=x[4]),
 'if 2 then not 5':(lambda x:(not x[2]) or not x[5], lambda x:x[2]+x[5]<=1),
 'if not 1 then 6':(lambda x:x[1] or x[6], lambda x:x[1]+x[6]>=1),
 '4 and 5 together':(lambda x:x[4]==x[5], lambda x:x[4]==x[5]),
 'if 3 then 1 or 5':(lambda x:(not x[3]) or x[1] or x[5], lambda x:x[3]<=x[1]+x[5]),
 'if 3 and 4 then 6':(lambda x:not(x[3] and x[4]) or x[6], lambda x:x[6]>=x[3]+x[4]-1),
 'if 2 then 3 and 4':(lambda x:(not x[2]) or (x[3] and x[4]), lambda x:x[2]<=x[3] and x[2]<=x[4]),
 'if 2 then 3 and 4 (aggregated)':(lambda x:(not x[2]) or (x[3] and x[4]), lambda x:2*x[2]<=x[3]+x[4]),
 'if 1 or 2 then 3':(lambda x:not(x[1] or x[2]) or x[3], lambda x:x[1]<=x[3] and x[2]<=x[3]),
 'if 1 and 2 then not 3':(lambda x:not(x[1] and x[2]) or not x[3], lambda x:x[1]+x[2]+x[3]<=2),
 'if 1 then >=2 of 3,4,5':(lambda x:(not x[1]) or x[3]+x[4]+x[5]>=2, lambda x:x[3]+x[4]+x[5]>=2*x[1]),
 'if 1 then none of 2,3':(lambda x:(not x[1]) or not(x[2] or x[3]), lambda x:x[2]+x[3]<=2*(1-x[1])),
 'exactly one of 1,2':(lambda x:(x[1]+x[2])==1, lambda x:x[1]+x[2]==1),
 '1 and 2 not both skipped':(lambda x:x[1] or x[2], lambda x:x[1]+x[2]>=1),
 '1 only if 4':(lambda x:(not x[1]) or x[4], lambda x:x[1]<=x[4]),
 '1 if 4':(lambda x:(not x[4]) or x[1], lambda x:x[4]<=x[1]),
 'x1 = x2*x3':(lambda x:x[1]==x[2]*x[3], lambda x:x[1]<=x[2] and x[1]<=x[3] and x[1]>=x[2]+x[3]-1),
 'drill a':(lambda x:sum(x[1:5])>=2, lambda x:x[1]+x[2]+x[3]+x[4]>=2),
 'drill b':(lambda x:(not x[5]) or not(x[1] or x[6]), lambda x:x[5]+x[1]<=1 and x[5]+x[6]<=1),
 'drill c':(lambda x:x[4] or (x[5] and x[6]), lambda x:1-x[4]<=x[5] and 1-x[4]<=x[6]),
 'drill d':(lambda x:(not x[2]) or x[3]+x[4]==1, lambda x:x[3]+x[4]>=x[2] and x[3]+x[4]<=2-x[2]),
 'drill e':(lambda x:sum(x[1:7])<=3 and ((not x[6]) or x[1]), lambda x:sum(x[1:7])<=3 and x[6]<=x[1]),
 'drill f':(lambda x:x[1]==(x[2] and x[3]), lambda x:x[1]<=x[2] and x[1]<=x[3] and x[1]>=x[2]+x[3]-1),
}
# Constraints that the sheet calls wrong must disagree with the words somewhere.
WRONG={
 'if 3 and 4 then 6 as x6>=x3, x6>=x4':(lambda x:not(x[3] and x[4]) or x[6], lambda x:x[6]>=x[3] and x[6]>=x[4]),
 'if 1 or 2 then 3 as x1+x2<=x3':(lambda x:not(x[1] or x[2]) or x[3], lambda x:x[1]+x[2]<=x[3]),
 'if 3 then 1 or 5 as 2x3<=x1+x5':(lambda x:(not x[3]) or x[1] or x[5], lambda x:2*x[3]<=x[1]+x[5]),
 'if 1 then 4 as x4<=x1':(lambda x:(not x[1]) or x[4], lambda x:x[4]<=x[1]),
}
