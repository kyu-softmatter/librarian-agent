# 자체 지식 — `kb/08-retrieval/`

작성 2026-09-06 · 상태 `draft` · [TREE.md](TREE.md) `kb/08-retrieval/`

목적: **어떤 질문에 어떻게 답하는 게 좋았는지**를 보관해서 검색이 나아지게 한다.
Librarian이 자기 자신에 대해 갖는 유일한 정본 지식이다.

---

## 1. 문제 — "좋은 답"은 상태가 될 수 없다

이 스토어는 설계 전체에서 **철학 ④(자연어는 상태가 아니다)를 위반할 확률이 가장 높은
지점**이다. "이 답이 좋았다"는 그 자체로 자연어 가치 판단이기 때문이다.

rt `kb-schema.md` §1이 이 위반을 미리 지목해 두었다:

> *"Where the violation will happen here is predictable — because a value
> judgment is natural language to begin with. **The sentence "this topic is
> interesting" cannot be state.**"*

그리고 BD `I-133`은 이 안티패턴을 실물에서 찾아냈다 — `MDCrow/mdcrow/agent/memory.py:119`가
**LLM이 쓴 자연어 요약을 상태로 사용**하고 있었고, BD가 요구한 대체물은
*"`{engine, config hash, seed, steps completed, checkpoint, observable, convergence state}` 형태의
형식 객체"*였다.

**"이 답이 좋았다"를 그대로 저장하면 `I-133`을 새 폴더에서 재현하는 것이다.**

---

## 2. 형식화 — 판단이 아니라 사실을 저장한다

핵심 전환 하나로 풀린다.

> **저장할 수 있는 것은 "좋았다"가 아니라 "어떤 히트가 실제로 인용되었는가"다.**
> 전자는 판단이고 후자는 사실이다. 그리고 검색을 개선하는 신호는 후자다.

`kb/08-retrieval/sessions/<id>.json`:

```json
{
  "id": "ret-8f3a1c02",
  "schema": "librarian.retrieval/0.1",

  "query": "bleach photons for AlexaFluor488 at 470 nm",
  "caller_profile": "ms:lens-5-photo-perturbation",
  "asked_by": "agent",
  "index_sha": "a19c4e7",
  "index_stale": false,

  "returned": ["ms:kb/literature/bleach-photons-af488#verdict",
               "ms:data/fluorophores.yaml#AlexaFluor488",
               "ms:kb/decisions/2026-08-10-labeling-and-laser-recommend#outcome"],
  "cited":    ["ms:data/fluorophores.yaml#AlexaFluor488"],
  "missing":  [],

  "verdict": "missing_entry",
  "action": "none",
  "action_ref": null,

  "note": "레지스트리 필드는 찾았지만 값이 비어 있어 G10 이 여전히 BLOCKED"
}
```

### 어느 필드가 분기 가능한가

| 필드 | 역할 | 허용 |
|---|---|---|
| `caller_profile` · `verdict` · `action` | 라우팅·판정 | **enum만** |
| `returned` · `cited` · `missing` · `action_ref` | 참조 | **uid 배열** |
| `index_sha` · `index_stale` | 재현 조건 | 해시 · bool |
| `query` | 재현 입력 | 문자열이지만 **자유 텍스트가 아니라 식별자로 취급** — 그대로 재실행된다 |
| `note` | 증거의 내용 | **자연어. 어떤 코드도 분기하지 않는다** |

`verdict` 어휘 — 무엇이 잘못됐는지를 **원인별로** 가른다:

| 값 | 의미 | 고칠 곳 |
|---|---|---|
| `useful` | 인용된 히트가 상위에 있었다 | — |
| `wrong_ranking` | 있었지만 아래에 있었다 | `profiles/` |
| `missing_entry` | 코퍼스에 없다 | `kb/` |
| `wrong_tier` | 티어가 잘못 붙어 나왔다 | 엔트리 frontmatter |
| `no_result` | 검색이 0건 | 토크나이저 · 어댑터 |
| `not_searched` | **기본값** | — |

> **`not_searched`가 기본값인 것이 철학 ①이다** (rt `kb-schema.md` §4.2:
> *"`not_searched` is the default, not `open`"*). 기록되지 않은 질의는
> "괜찮았다"가 아니라 "확인되지 않았다"다.
>
> 그리고 `no_result`와 `not_searched`를 가르는 것이 §1 [BUILD.md](BUILD.md)의
> 네 얼굴 문제에 대한 답이다 — 0건이 반환된 것과 애초에 안 찾은 것은 다른 사건이다.

---

## 3. 왜 `cited`가 핵심인가 — 회귀 오라클이 된다

`cited`는 사실이므로 저장할 수 있고, **동시에 테스트가 된다.**

```
oracles/<id>.json  :  (query, caller_profile) → cited 가 top-N 안에 있어야 한다
```

**이 패턴은 BD가 이미 쓰고 있고, 이유도 같다.** BD `knowledge/wiki/CLAUDE.md`:

> *"**검증 오라클 공급** — `benchmarks/`가 `pytest`로 실행되는 회귀 테스트의 근거가 된다.
> **우리 도메인에는 채점자가 없으므로 문헌이 그 역할을 대신한다.**"*

검색에도 채점자가 없다. 그래서 **과거에 확인된 인용이 그 역할을 대신한다.**
이것이 [BUILD.md](BUILD.md) §4-B의 "프로파일이 결과를 실제로 바꾼다"를 픽스처 8건이
아니라 축적된 실사용으로 검증하게 만든다.

---

## 4. 금지 두 개

### ① 스칼라 만족도 금지

**금지: `profile_satisfaction: 0.82`.**

rt `kb-schema.md` §3과 정확히 같은 이유다 — *"점수를 만들면 평균이 가능해지고,
평균하는 순간 divergence가 사라진다."* 여기서 사라지는 것은 **무엇이 왜 실패했는지**다.
만족도 0.82는 `wrong_ranking` 20건과 `missing_entry` 20건을 같은 숫자로 만든다.
고칠 곳이 `profiles/`와 `kb/`로 서로 다른데도.

**대신: `verdict`별 실패 질의 목록.** 집계가 아니라 열거다.

### ② `note`로 분기 금지

`note`는 사람이 읽는다. 코드가 `note`를 읽고 무엇을 하면 그 순간 `I-133`이다.
검사: **이 필드를 읽고 분기하는 코드가 있는가?** 있으면 enum으로 승격하거나 지운다.

---

## 5. 승격은 사람 승인 — 자기확증을 막는다

```
sessions/  ──(사람 승인)──▶  oracles/
```

**BD의 `promotion: finding_to_concept: human_gated`를 상속한다.** BD가 붙인 이유는
*"에이전트가 스스로 개념을 인플레이션시키는 것을 막는다"*였고, 여기서는 더 직접적이다.

> **에이전트가 자기 검색 결과를 스스로 정답으로 승격시키면 그것은 자기확증 루프다.**
> 상위에 나온 것을 인용하고, 인용했으니 오라클이 되고, 오라클이니 상위에 유지된다.
>
> **이건 rt README §2가 이 시스템 전체에 대해 제기한 반론과 같은 것이다** —
> *"positive feedback loop는 발산하거나 자기를 확증한다. 세 축이 서로를 먹이면
> 그들이 공유하는 편향이 증폭된다"* (`C-001`). 검색 피드백은 그 루프가 가장 짧게
> 닫히는 지점이고, **감쇠 장치는 사람 승인 하나뿐이다.**

승격 조건 (전부 만족):

| 조건 | 왜 |
|---|---|
| `verdict: useful` | 실패 기록은 오라클이 아니다 |
| `cited`가 비어 있지 않음 | 인용 없는 세션은 신호가 없다 |
| **서로 다른 `index_sha` 2회 이상에서 재현** | 한 색인 상태의 우연이 아님 |
| 사람 승인 | 자기확증 차단 |

### 픽스처 F9

[BUILD.md](BUILD.md) §2에 붙는다.

| # | 검증하는 주장 | 픽스처 |
|---|---|---|
| **F9** | `oracles/`가 회귀를 **실제로 잡는다** | 오라클 1건을 만든 뒤 프로파일을 의도적으로 망가뜨리면 **테스트가 실패해야 한다** |

> F9의 통과 조건이 "실패해야 한다"인 것에 주의. 망가뜨렸는데 초록색이면
> 오라클은 배선되지 않은 checker다 — BD `tools/kb.py`가 기록한 그 실패 모드.

---

## 6. 결정이 필요한 것

| # | 결정 | 권고 | 근거 |
|---|---|---|---|
| 1 | `cited`를 어떻게 수집하나 | **호출 에이전트가 보고**. 자동 추론 안 함 | 추론하면 사실이 아니라 추정이 된다 |
| 2 | 보고 누락 시 | `not_searched`로 남는다 (기본값 = 실패) | 철학 ① |
| 3 | `query` 원문 보관 | **보관.** 재현 입력이므로 | 없으면 오라클을 재실행할 수 없다 |
| 4 | 미발표 내용이 `query`에 섞이면 | `publish-gate` 적용 대상 | 질의 자체가 연구 방향을 드러낸다 → [PLAN.md](PLAN.md) §6.1 |
| 5 | 승격 재현 횟수 | **서로 다른 색인 2회** | 1회는 우연과 구별 안 됨 |
