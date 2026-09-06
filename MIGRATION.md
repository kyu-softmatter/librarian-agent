# KB 이관 — 세 리포의 KB를 Librarian으로 옮기고 삭제하기

작성 2026-09-06 · 상태 `draft` · [TREE.md](TREE.md) §3 보충

**결정:** Librarian 구축 후 세 에이전트의 KB를 삭제한다.
**v1 범위: MS `kb/` 40건만.** BD 224건·RT는 v2·v3 ([PLAN.md](PLAN.md) §0) —
리포를 하나씩 처리하는 것이 §4 Step 4의 동등성 증명을 리포 단위로 만들어 더 안전하다.

이 문서는 그 결정을 실행 가능한 순서로 바꾼 것이다. 삭제가 **무엇을 깨뜨리는지 실제로
확인**한 결과부터 시작한다 — 추측으로 순서를 정하면 순서가 틀린다.

---

## 1. 확인 결과 — 예상보다 안전하다

2026-09-06에 두 리포의 코드·테스트·에이전트 정의를 직접 grep해서 확인했다.
**결론부터: 삭제는 어느 리포의 실행 코드도 깨뜨리지 않는다.**

| 확인 항목 | 결과 |
|---|---|
| MS 게이트가 `kb/`를 런타임에 읽는가 | **아니오.** 게이트는 `data/*.yaml`을 읽는다 (`optics/components.py` → `fluorophores.yaml` · `filters.yaml` · `pixel_size.yaml`) |
| MS 테스트가 `kb/` 파일을 읽는가 | **아니오.** 주석 인용뿐 |
| BD 파이프라인이 `knowledge/`를 읽는가 | **아니오.** `tools/kb.py`(CLI 도구)만 `knowledge/entries/`를 읽는다 |
| BD `pytest`가 `wiki/benchmarks/`를 읽는가 | **아니오.** `benchmark` 마커는 10곳 이상에서 쓰이지만 전부 `test_s*.py` 안이고, 값이 **하드코딩**되어 있다 |
| `tests/test_knowledge.py` | **존재하지 않는다.** `conftest.py` 헤더가 *"knowledge/wiki/benchmarks 회귀"*로 등록해 놓았지만 파일이 없다 |

**즉 KB는 이미 "실행에 안 물려 있는" 상태다.** 이건 삭제 계획에 유리한 사실이고,
제가 처음 우려했던 "테스트가 깨진다"는 근거가 없다.

### 실제 소비자는 코드가 아니라 에이전트와 사람이다

| 소비자 | 어떻게 읽는가 | 삭제 후 |
|---|---|---|
| MS 렌즈 5개 | `tools: Read, Grep, Glob` — **MCP 도구가 없다** | **읽을 수 없다** ← 결정적 |
| BD `bd-knowledge` 스킬 | `SKILL.md`에 경로 10곳 하드코딩 (`ls knowledge/wiki/systems/`, `grep -rl … knowledge/source/papers/`) | 명령이 빈 결과를 반환 |
| BD `tools/kb.py` | `ENTRY_DIR = ROOT/"knowledge"/"entries"` | 조용히 0건 |
| 코드 주석 ~27곳 | `bdbot/constants.py` → `knowledge/wiki/concepts/water-298k.md`, `hardware/lunf_power.py` → `kb/decisions/2026-08-29-…` | **끊긴 감사 추적** |
| 사람 | 리포를 열어서 | 못 읽음 |

---

## 2. 진짜 위험 — 조용히 실패한다

§1의 표에서 **아무 항목도 에러를 내지 않는다.** 없는 디렉터리에 `grep`을 걸면 빈 결과가
나오고, 그건 "지식이 없다"와 구별되지 않는다.

**이 실패는 BD에서 이미 한 번 발생했고 기록되어 있다.** `tools/kb.py` 42행 주석:

> *"이건 `kb/entries`를 가리키고 있었는데 merge가 `knowledge/entries`로 이름을 바꿨다.
> 결과는 에러가 아니었다 — `kb.py list`가 기존 126개 엔트리에 대해 그냥
> "run-less knowledge 0"을 보고했다. **조용히 빈 읽기는 배선 안 된 checker와 같은
> 실패 모드다.**"*

그리고 `wiki/benchmarks/` 삭제의 귀결이 정확히 이 모양이다:

> **테스트는 계속 통과한다. 그 숫자들의 근거만 사라진다.**
>
> `test_s4_nondim.py`·`test_s5_scheme.py`의 `@pytest.mark.benchmark` 값은 하드코딩이고,
> 그 정당화가 `wiki/benchmarks/`에 있다. 근거를 지우면 테스트는 초록색을 유지하면서
> **출처 없는 숫자**가 된다 — BD `docs/03` §4가 *"a number without a source is not a
> number"*라고 부르는 상태.

**→ 이관에서 가장 먼저 처리할 것은 파일 이동이 아니라 참조 갱신이다.**

---

## 3. `export/` — 왜 사본을 되돌려 보내야 하는가

§1의 결정적 항목: **MS 렌즈 5개는 `tools: Read, Grep, Glob`이다.** MCP 도구가 선언되어
있지 않으므로 Librarian을 호출할 수 없다. 선택지는 두 개뿐이다.

| 선택 | 내용 | 비용 |
|---|---|---|
| **(가) 에이전트 정의 재작성** | 5개 렌즈 + BD 9개 에이전트에 MCP 도구 추가 | 지식 가용성이 **실행 중인 서비스에 의존**하게 된다. MCP가 죽으면 렌즈는 지식이 0인 상태로 판정한다 |
| **(나) `export/` 역방향 생성물** ★ | Librarian이 각 리포에 읽기 전용 사본을 생성해 넣는다 | 사본이 하나 늘어난다 |

**(나)를 권고한다.** 이유는 두 리포가 이미 확립한 원칙 두 개와 맞기 때문이다.

1. **파생물은 복제해도 된다.** 정본이 하나면 사본은 색인이다. `export/`는 생성기를
   가지고 전면 재생성되므로 [TREE.md](TREE.md) §3의 파생물 불변식을 만족한다.
2. **기본값은 실패다** (철학 ①). 오프라인에서 지식이 0이 되는 설계는 이 원칙을
   거꾸로 쓴 것이다 — 실패해야 할 때 실패하는 게 아니라, **실패했는데 통과처럼 보인다.**

```
Librarian/kb/          ★ 정본. 여기서만 편집
      │
      └── 생성 ──▶ Librarian/export/ms/  ──git subtree──▶ MS/kb-export/  ◆ 읽기 전용
                    Librarian/export/bd/                   BD/knowledge-export/
```

**`export/`에 반드시 들어가는 것:** 생성기 경로 + Librarian 커밋 SHA를 담은 헤더.
`INDEX.md`가 생성기 없이 남아 항목 수 40 vs 42로 뒤처진 상태가 이 규칙의 반례다.

> 이렇게 하면 삭제 결정이 유지된다 — **정본은 옮겨지고 두 리포에 남는 것은
> 손으로 못 고치는 파생물뿐이다.** "kb를 삭제한다"가 "kb를 편집 권한과 함께
> 삭제한다"로 정확해진다.

---

## 4. 이관 순서 — 삭제는 마지막이다

> **Step 0 (구축 + 픽스처 검증)이 아래 Step 1보다 앞선다.**
> 결정: 구성을 다 하고 작동을 검증한 뒤에 이관한다. → [BUILD.md](BUILD.md)
> Step 0의 인수 조건 A–E를 통과하지 않으면 Step 1을 시작하지 않는다.

각 단계는 **검증 가능한 종료 조건**을 가진다. 삭제는 되돌릴 수 있지만(git 이력에 남는다)
**끊긴 참조는 조용하므로**, 순서가 안전장치다.

### Step 1 · 흡수 (두 쪽 다 살아 있음)

| 작업 | 종료 조건 |
|---|---|
| §5 표대로 `kb/`에 내용 이관 | 원본 파일 수 = 착지 파일 수. 손실 0 |
| **frontmatter 계약 흡수** | BD `knowledge/wiki/CLAUDE.md`의 기계 계약(`source_frontmatter_required` · `precedence` · `promotion`)이 Librarian `kb/README.md`에 상속됨 |
| 색인 구축 | 두 쪽에서 같은 질의가 같은 결과를 낸다 |

> **`wiki/CLAUDE.md`는 파일이 아니라 계약이다.** 그냥 지우면 BD의
> `type`/`author`/`drafted`/`reproduced` 어휘와 `precedence` L0–L3 규칙이 사라진다.
> `tests/test_s5_pair.py:113`이 *"`reproduced: no` 문헌값을 근거처럼 쓰지 않는다
> (knowledge/wiki/CLAUDE.md)"*를 강제하고 있으므로, **계약을 먼저 옮기지 않으면
> 테스트의 근거가 먼저 사라진다.**

### Step 2 · 참조 갱신 (여기가 실제 작업량이다)

| 작업 | 종료 조건 |
|---|---|
| 코드 주석 ~27곳의 경로 치환 | `grep -rn "knowledge/\|kb/"` 결과에 존재하지 않는 경로가 0개 |
| `bd-knowledge` SKILL.md 명령 10곳 | MCP 도구 호출 또는 `export/` 경로로 치환 |
| `tools/kb.py` `ENTRY_DIR` | Librarian을 가리키거나 도구 자체를 은퇴 |
| **끊긴 참조 검사를 CI에 추가** | 존재하지 않는 경로를 인용한 주석이 있으면 **빌드 실패** |

> **마지막 행이 §2 위험의 유일한 방어다.** 조용한 실패를 시끄럽게 만드는 것.
> 이 검사가 없으면 이관 후 어느 시점에 누가 경로를 되짚다가 발견하게 된다.

### Step 3 · `export/` 배선

| 작업 | 종료 조건 |
|---|---|
| `export/{bd,ms}/` 생성기 | 전량 삭제 후 재생성 결과가 비트 단위 동일 |
| 두 리포에 subtree 배선 | MS 렌즈 5개가 `Grep`으로 이관된 지식을 **찾는다** |
| 헤더 규칙 | 모든 생성 파일에 생성기 경로 + Librarian SHA |

### Step 4 · 동등성 증명

**삭제 직전 관문.** 삭제해도 되는지를 판정하는 유일한 검사.

| 검사 | 통과 조건 |
|---|---|
| BD `pytest` 전량 | Step 0 시점과 동일한 결과 |
| MS 게이트 판정 | 고정 입력 집합에 대해 G1–G32 판정이 **글자 단위 동일** |
| 렌즈 재현 | 같은 질문에 렌즈 5개가 이관 전/후 같은 근거 파일을 인용 |
| 끊긴 참조 | 0개 |

### Step 5 · 삭제

한 커밋으로, **Step 4의 증명을 커밋 메시지에 인용해서** 지운다.
`runs/`는 지우지 않는다 (§5).

---

## 5. 항목별 착지점

실측 파일 수 기준. **`runs/`와 `research-topic`은 이관 대상이 아니다.**

### BD `knowledge/` (224 파일)

| 원본 | 수 | 착지 |
|---|---|---|
| `source/papers/*.md` | 42 | `kb/07-sources/papers/` |
| `source/papers/INDEX.md` | 1 | `map/` — 생성물. **생성기와 함께** 재작성 |
| `source/books/*.md` | 2 | `kb/07-sources/books/` (증류만, 원본 없음 규칙 유지) |
| `wiki/systems/` | 11 | `kb/06-simulation/cards/` — (계 × 목적동역학) 규약 그대로 |
| `wiki/concepts/` | 3 | `kb/05-physics/` |
| `wiki/techniques/` | 2 | `kb/06-simulation/` (HOW-TO는 엔진에 묶인다) |
| `wiki/benchmarks/` | 5 | `kb/05-physics/evidence/assumed/` **+ `export/bd/`** (테스트 근거) |
| `wiki/findings/` | 23 | `kb/05-physics/findings/` · `kb/06-simulation/findings/` (엔진 교체 테스트로 분류) |
| `wiki/questions/` | 2 | `kb/0X/questions/` |
| `wiki/CLAUDE.md` | 1 | **계약 흡수** → `kb/README.md`. 파일 이동이 아니다 |
| `entries/*.json` | 135 | `origin`별 분해: `tooling` 52·`method` 45 → `map/04-agents` 또는 `06-simulation` / `handbook` 25 → `07-sources/books` 파생 / `intake` 10 → `06-simulation` / `paper` 3 → `07-sources` |
| `runs/*/record.json` | 256 | **이관 안 함.** run provenance는 BD 소유 — 색인만 가져온다 |

### MS `kb/` (40 파일)

| 원본 | 수 | 착지 |
|---|---|---|
| `decisions/` | 20 | `kb/00-decisions/` — 시간순, 주제 아님 |
| `systems/` | 8 | `kb/02-hardware/cards/`. 단 `PyTool_*.reference`·`aresis-support-email-draft.md`는 `03-control` 또는 지식 아님으로 분류 |
| `expertise/` | 6 | `kb/01-materials/` (coverslip·immersion·medium-RI) · `kb/02-hardware/` (oil-objective-trapping) |
| `calibrations/` | 4 | `kb/02-hardware/evidence/measured/`. `disk-bandwidth.yaml`은 `03-control` |
| `literature/` | 2 | 규칙 흡수 → `kb/07-sources/` + `_template.md`는 `kb/0X/evidence/assumed/`의 서식으로 |

### `research-topic`

**이관하지 않는다.** 연구 제안·검증 축으로 남는다. `design/kb-schema.md`의 7종 스키마 중
`challenge/`만 Librarian이 `store/challenge/`로 구현한다 — 나머지는 rt 소유.

---

## 6. 짚어둘 결과 하나 — 공개 방향이 뒤집힌다

BD `source/papers/` 42건은 **의도적으로 공개**되어 있다. BD `wiki/CLAUDE.md`가 그 이유를
명시한다:

> *"왜 저작자가 아니라 발표 여부로 가르는가 — 공개 경계가 **폴더 단위**로 걸리기
> 때문이다. … 보호해야 할 것은 저작자가 아니라 **아직 발표되지 않았다는 사실**이다."*

[PLAN.md](PLAN.md) §6.1은 Librarian을 **private**로 권고했다. 두 결정을 합치면
**현재 공개된 문헌 증류 42건이 비공개 저장소로 들어간다.** 유출은 아니지만
공개 자산의 회수이고, BD가 폴더 경계로 지킨 구분이 사라진다.

선택지:

| 선택 | 결과 |
|---|---|
| (가) `kb/07-sources/`만 공개 | BD의 원래 규칙을 그대로 상속 |
| **(나) Librarian 전체 public** | ✅ **결정 2026-09-06.** 공개 자산 42건 회수 문제가 사라진다. 대가: 주간 digest가 미발표 연구 방향을 공개할 수 있다 (`T-019`①) → `publish-gate` 필수 |
| (다) Librarian 전체 private | 공개 자산 42건 회수 |

**(나)로 결정되었다.** 이관되는 BD `source/papers/` 42건이 공개 상태를 유지하므로 §6의
원래 우려는 해소된다. **남는 것은 반대 방향의 부담이다** — 이 리포에 무엇을 **쓸 수
있는가**의 규칙이 필요하고, 그것이 `publish-gate`다. `07-sources/raw/`가 gitignore인 것과
같은 층의 규칙이다.

---

## 7. 결정이 필요한 것

| # | 결정 | 권고 | 안 정하면 |
|---|---|---|---|
| 1 | 오프라인 읽기 경로 | **`export/` 생성물** (§3-나) | MCP 장애 시 렌즈가 지식 0으로 판정 |
| 2 | 공개 범위 | ✅ **전체 public — 결정 2026-09-06** | 대신 `publish-gate`가 digest 구현 전 선행 조건 |
| 3 | `tools/kb.py` 처리 | 은퇴 (Librarian MCP가 대체) | `ENTRY_DIR`이 0건을 조용히 반환 |
| 4 | 끊긴 참조 CI 검사 | **Step 2에 필수** | §2의 조용한 실패가 그대로 남는다 |
| 5 | `runs/` 256건 | 이관 안 함, 색인만 | run provenance 소유가 흐려진다 |
| 6 | `entries/` 135건 분해 | `origin`별 (§5) | 52+45건 tooling·method가 주제 폴더를 오염 |
| 7 | 삭제 시점 | Step 4 통과 후 | — |
