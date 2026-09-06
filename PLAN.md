# Librarian — J1 실행체 구축 계획

작성 2026-09-06 · 상태 `draft` · 근거: 세 리포 live 원격 읽음 (아래 §1)

세 리포([agentic-microscope](https://github.com/kyu-softmatter/agentic-microscope) ·
[Brownian-Dynamics-Agent](https://github.com/kyu-softmatter/Brownian-Dynamics-Agent) ·
[research-topic](https://github.com/kyu-softmatter/research-topic))와 MCP로 상호작용하는
지식 통합·검색·정제 에이전트.

---

## 0. 범위 — v1은 현미경 에이전트 전용

**결정 (2026-09-06):**

| | |
|---|---|
| **정체성** | **네 번째 축.** 지식의 관리·보관·상호작용. ~~rt의 J1 실행체~~ — `research-topic`은 **연구 제안·검증**으로 남는다 |
| **v1 범위** | **현미경 에이전트(MS) 전용 사서.** 이후 시뮬레이션(BD) → 리서치(RT)로 확장 |
| **데이터** | 구성 완료 + 작동 검증 후 이관 → [BUILD.md](BUILD.md) · [MIGRATION.md](MIGRATION.md) |
| **주 1회 정리** | **연기.** 대신 `index_stale` 자기신고 → [BUILD.md](BUILD.md) §4-D |

### 0.1 v1에서 만드는 것 / 안 만드는 것

| | v1 (MS) | v2 (BD) | v3 (RT) |
|---|---|---|---|
| 어댑터 | `kb/` 5종 · `data/*.yaml` · MM 메타데이터 | `wiki`·`source`·`entries`·`runs` | `design/` |
| 프로파일 | 렌즈 1–8 | `bd:s1`–`s8` · `lit-*` | `V1`·`V2` |
| 주제 폴더 | `00`·`01`·`02`·`03`·`07`·`08` | `05`·`06` 채워짐 | — |
| crosswalk (row 2) | **불가 — BD 쪽이 없다** | ★ 최우선 | — |
| challenge 라우팅 | MS 내부만 | 리포 간 | 문헌 경로 |

> **`kb/` 8개 폴더는 v1에서 전부 만든다. 내용만 비워 둔다.**
> rt `kb-schema.md` §0: *"형식이 고정되기 전에 채우면 형식이 바뀔 때 채운 것을 버린다."*
> 폴더가 없으면 v2에서 `05`·`06`을 만들 때 모양을 다시 정하게 된다.

### 0.2 v1의 최우선 산출물 — 설계는 있고 아무도 안 만든 것

MS 리포를 읽고 확인한 것. **세 개 모두 MS 혼자서 값이 나오고, BD를 기다리지 않는다.**

**① `kb/envelope.sqlite` — 취득 2,343건의 정량 색인. 미구축.**

`docs/02` §1·§6에 스키마가 설계되어 있고, §7에 파서 규격이 완비되어 있는데
**파일이 존재하지 않는다.** 규격에 이미 적혀 있는 것들:

| 항목 | 규격 |
|---|---|
| 파일 크기 | 최대 44 MB → **헤더만 스트리밍** (Summary + 첫 FrameKey + 96 kB tail) |
| 이중 스키마 | MM 1.4.23 (2,137건 · 91 %) ≠ 2.0.3 |
| 시스템 식별 | PC 이름으로 가르면 틀린다 → 디바이스 라벨 집합 + 카메라 칩/시리얼 해시 |
| 라벨 오타 | `Prime95B` vs **`Pirme95B` 20건** → alias 표 필요 |
| 폴더명 파싱 | `Las10`=레벨 · `Las488`=파장 · `Las555_5`=555 nm 5 %. 350–800 정수는 파장 |
| 드롭 스크리닝 | tail의 `ElapsedTime-ms`로 `(last−first)/(n−1)` — 어디서 몇 개인지는 못 말한다 |

**사용자가 말한 "데이터가 쌓일 때 대비"가 정확히 이것이고, 규격이 이미 있다.**

**② `kb_gaps` — 입력이 없어 `BLOCKED`인 게이트 목록.**

`docs/07` Phase 0이 `power_at_sample_mw`를 *"the top blocker"*로 기록하고 있고,
*"미터가 도착할 때까지 모든 dose/SNR 숫자는 상대값으로 남고 그 필드를 필요로 하는
게이트는 설계상 `BLOCKED`을 반환한다"*고 적어 두었다. **어떤 게이트가 무엇 때문에
막혀 있는지가 질의 가능해진다.**

**③ `kb/literature/` 첫 엔트리 — 현재 0건.**

README와 `_template.md`만 있다. MS 자신의 표현: *"이 폴더에 있는 것이 정확히
**다음에 측정할 가치가 있는 것**"*. v1이 채울 수 있는 유일한 KB 폴더다.

### 0.3 v1에서 미루는 것

| 미루는 것 | 이유 |
|---|---|
| BD·RT 어댑터 | 범위. 어댑터는 **가산적**이라 나중에 붙여도 구조가 안 바뀐다 |
| row 2 crosswalk | BD 쪽 42건이 없으면 매핑할 대상이 없다 |
| 주 1회 자동화 | 사용자 결정. `index_stale`로 대체 (§6 개정) |
| `05`·`06` 내용 | BD 도메인 |

> **미루지 않는 것이 하나 있다 — 토크나이저.** v1은 MS 전용이고 MS 본문은 영어라
> `unicode61`로 충분하다. 그런데 v2에서 BD(본문 한국어)가 들어올 때 `unicode61`은
> **에러가 아니라 0건**을 반환한다 ([BUILD.md](BUILD.md) §3 실측). 조용한 실패를
> 나중에 발견하는 대신 **v1부터 `trigram` + 2글자 LIKE 폴백으로 간다.**
> 재색인 비용이 아니라 실패가 조용하다는 것이 이유다.

## 1. 확인된 사실 — 계획의 근거

2026-09-06에 세 원격을 직접 읽고 확인한 것. 추측이 아닌 부분과 아닌 부분을 나눈다.

### 1.1 코퍼스 규모 — FTS5가 이제 정당하다

| 저장소 | 실측 |
|---|---|
| BD `knowledge/entries/*.json` | **135** |
| BD `knowledge/source/papers/*.md` | **42** (+ `INDEX.md`) |
| BD `knowledge/source/books/` | **2** |
| BD `knowledge/wiki/**/*.md` | **44** (benchmarks 5 · concepts 3 · findings 23 · questions 2 · systems 11 · techniques 2) |
| BD `runs/*/record.json` | **256** |
| MS `kb/` | **40** (calibrations 4 · decisions 20 · expertise 6 · literature **2 = README+템플릿만** · systems 8) |
| **합계** | **~520 문서** |

BD `tools/kb.py`의 주석은 *"A SQLite + FTS5 store is the plan, but it is overkill below
100 runs"*라고 적어 놓았다. **runs만 256개다.** 그 조건은 이미 넘었다.

### 1.2 색인 부패가 이미 시작되었다 — I-076의 실측 사례

`knowledge/source/papers/INDEX.md` 1행:

```
<!-- 생성됨: docs/tools/wiki_index.py — 직접 고치지 말 것 -->
```

- **`docs/tools/` 디렉터리는 리포에 없다.** 생성기가 사라지고 생성물만 남았다.
- INDEX.md는 항목 수를 **40**으로 적고 있다. 실제 파일은 **42**개다.

즉 *"직접 고치지 말 것"이라고 적힌 파일을, 고칠 수 있는 유일한 수단이 없는 상태에서,
이미 2개 뒤처진 채로* 두 리포가 읽고 있다. 이것이 BD `I-076`이 예고한
*"파일은 다 있는데 검색이 안 되는 상태"*의 초기 증상이고, **Librarian의 존재 이유 중
가장 검증 가능한 항목이다.**

### 1.3 BD 안에 이미 미해결 스키마 분열이 있다

BD `docs/03-knowledge-base.md` §1이 스스로 *"the largest piece of debt in the
repository"*라고 부르는 것:

| | `wiki/` + `source/` | `entries/` |
|---|---|---|
| 형식 | Markdown + YAML frontmatter | flat JSON |
| 쓰는 주체 | 사람/에이전트가 의도적으로 | `tools/kb.py add` |
| 읽는 주체 | skill `bd-knowledge` | `tools/kb.py query` |
| 규모 | 44 + 44 | 135 |

*"A lesson filed in one is not found by a tool reading the other. … the honest
interim rule is **query both**."*

**"query both"를 한 번의 질의로 만드는 것이 Librarian의 첫 측정 가능한 성과다.**
리포 간 통합보다 쉽고, 같은 메커니즘을 쓰며, 성공/실패가 즉시 드러난다.

### 1.4 Row 2가 가장 날카로운 틈이고, 1:1이 아니다

README §2.1 row 2: BD는 문헌 증류 42개를 가지고 있고, MS는 그것을 받도록 만들어진
**빈 폴더**(`kb/literature/` — README와 `_template.md`뿐)를 가지고 있다.

그런데 두 쪽의 **저장 단위가 다르다.** MS `kb/literature/README.md`:

> *"One file per quantity per subject. `bleach-photons-alexafluor488.md`, not
> `smith-2019.md`: the unit of storage is the number a gate consumes, not the paper
> it came out of. One paper supplying three quantities becomes three files."*

BD의 단위는 **논문 1편 = 파일 1개**(`provides: [gser-formula, msd-to-moduli, …]`)다.

**그래서 crosswalk는 1→N이다.** BD 엔트리의 `provides` 배열이 MS의 파일 분해 단위와
정확히 대응한다 — BD `mason-weitz-1995`의 `provides` 3항목은 MS 형식에서 3개 파일이 된다.
이것은 스키마 협상이 필요한 문제가 아니라 **이미 양쪽에 있는 필드를 매핑하는 문제다.**

### 1.5 네 번째 수렴 — 전송층에서 강제할 수 있다

세 리포가 독립적으로 같은 규칙에 도달했다: **출판된 숫자는 유효 조건 없이 쓸 수 없고,
결코 측정값으로 계산되지 않는다.**

| 리포 | 표현 |
|---|---|
| research-topic | `literature.conditions` |
| MS | `evidence: assumed` — 절대 `measured` 아님 → `advances: NO`. `## Transfer conditions` 필수 |
| BD | provenance `from_paper`/`assumed`/`derived` + **tier**. 파생값은 재계산, 절대 그대로 신뢰 안 함 |

BD는 이걸 어긴 비용을 기록해 두었다: `T = 300 K`를 tier 1(measured)로 잘못 적어
**하류 모든 `τ_B`에 −4 %~−14 % 오차가 전파**되었다.

**→ 설계 결론: 검색 결과의 모든 히트는 `evidence`/`tier`/`provenance`를 반드시 함께
반환한다.** 티어 없는 히트는 반환하지 않는다. 그러면 티어 오분류가 전송 시점에 검출된다.

### 1.6 두 리포는 서로 다른 기계에 있다

MS `.mcp.json`:

```json
"command": "C:\\Users\\<lab PC>\\venvs\\auto_microscope\\Scripts\\python.exe"
```

MS의 MCP 서버는 **랩 Windows PC**에서 하드웨어를 잡고 돌아간다. BD는 macOS + conda
`simulation_bot`이다. **로컬 파일시스템을 공통 접근 경로로 가정할 수 없다.**

다만 **세 리포 모두 public이다** (확인: `visibility: PUBLIC` × 3). 그래서 `git fetch`가
플랫폼 독립적인 수집 채널이 되고, 부수 효과로 **커밋 SHA가 색인의 provenance가 된다.**

---

## 2. 상속하는 제약 — 바꿀 수 없는 것

`research-topic` README §0: *"바꾸면 안 되는 것은 §3의 6개 철학 항목과 charter §3의 경계
표뿐"* — 둘 다 기존 두 리포에서 상속되었거나 두 리포가 독립 수렴한 지점에서 유도되었기
때문에 이 리포 혼자 바꿀 수 없다. Librarian도 같은 구속을 받는다.

| # | 제약 | Librarian에서의 구체적 금지 |
|---|---|---|
| ① | 기본값은 실패다 | 검색 결과 없음 = `not_searched`가 기본. `open`이 아니다 |
| ② | LLM은 숫자를 만들지 않는다 | 주간 잡의 LLM 단계는 **인용·locator만** 생산. 값 요약 금지 |
| ③ | 모든 판단은 자기를 뒤집을 검사를 가진다 | 모든 히트에 falsifier 필드를 실어 보낸다 |
| ④ | 자연어는 상태가 아니다 | 분기·라우팅·판정에 쓰이는 필드는 enum/숫자/ID/bool만 |
| ⑤ | rigor에서 불일치는 버그, value에서 불일치는 산출물 | Librarian은 value를 다루지 않는다 → 집계·평균 금지 |
| ⑥ | value의 정본 출처는 교과서가 아니다 | 해당 없음 (J2 소관) |

추가로 `charter.md` §5의 구조적 금지에서:

- **값·임계값을 정하지 않는다.** 임계값은 BD/MS 소유.
- **시뮬레이션·실험을 돌리지 않는다.** enforcer가 아니다.
- **자기가 falsifier를 돌릴 수 없는 challenge를 판결하지 않는다.** 라우팅만 한다.

### 2.1 상충처럼 보이지만 아닌 것 — 검색 점수

`kb-schema.md` §3은 **`value_score: 0.7`을 금지**한다. 평균이 가능해지면 divergence가
사라지기 때문이다.

**검색 relevance 점수는 여기에 걸리지 않는다** — 검색 순위는 *가치 주장*이 아니라
*검색 순서*다. 다만 위험이 정확히 이 지점에서 재발한다:

> **규칙: 순위(rank)는 반환만 하고 엔트리에 저장하지 않는다.** 저장되는 순간 그것은
> "이게 더 중요하다"는 스칼라 가치 주장이 되고, §3이 금지한 것이 새 옷을 입고 돌아온다.

---

## 3. 아키텍처 — 색인하되 병합하지 않는다

`charter.md` §4 · README §7의 현행 결정은 **option A (three repos + indexing)**이고,
근거는 BD `I-057`: *경계는 되돌릴 수 있고 검사 가능한가에서 그어진다. 색인은 되돌릴 수
있고 이전(migration)은 아니다.*

```text
        ┌──────────────── Librarian (이 리포, private) ────────────────┐
        │                                                              │
        │   cache/            git clone --depth 1 × 3   (read-only)   │
        │     ├── bd@<sha>                                             │
        │     ├── ms@<sha>                                             │
        │     └── rt@<sha>                                             │
        │            │                                                 │
        │            ▼  adapters/  (리포별 파서 — frontmatter 계약 파싱) │
        │   index/                                                     │
        │     ├── kb.sqlite      FTS5 + 메타 (파생물, 언제든 재생성)     │
        │     └── manifest.json  {repo: sha, built_at, doc_count}      │
        │            │                                                 │
        │            ▼                                                 │
        │   mcp/server.py    ← 읽기 도구 8개 (§5)                       │
        │                                                              │
        │   store/           ★ Librarian이 쓰는 유일한 곳               │
        │     ├── challenge/    은퇴 메커니즘 (7번째 엔트리 종)          │
        │     ├── crosswalk/    BD paper → MS quantity 매핑 (1→N)       │
        │     ├── digest/       주간 정제 산출물                        │
        │     └── inbox/        LLM 제안 — 사람 승인 대기               │
        └──────────────────────────────────────────────────────────────┘
                 │ 읽기만                          │ 제안만 (PR/이슈)
                 ▼                                 ▼
        BD · MS · research-topic          사람이 승인한 뒤에만 반영
```

### 3.1 세 개의 불변식

이 세 개가 깨지면 Librarian은 enforcer가 되고 `charter.md` §5를 위반한다.

1. **원본 리포에 절대 쓰지 않는다.** 쓰기는 `store/`와, 사람이 승인하는 PR뿐.
   → 되돌릴 수 있음이 보존된다.
2. **엔트리 파일이 정본, 색인은 파생물.** 색인을 손으로 고치는 코드 경로는 존재하지
   않는다 (`kb-schema.md` §5). `index/`는 삭제하고 재생성해도 정보 손실이 없어야 한다.
3. **모든 히트는 `repo@sha:path#locator` 형태의 좌표를 갖는다.** 좌표 없는 히트는
   반환하지 않는다. BD의 handbook 계약(*"책이 저장소에 없어도 주장을 페이지까지
   되짚을 수 있다"*)을 색인 전체로 확장한 것.

### 3.2 왜 벡터 검색이 1차 경로가 아닌가

BD `I-052`: 질문의 운명은 **검색 결과의 유무**로 결정되고 LLM 투표로 결정되지 않는다.
임베딩 유사도는 재현 가능하지만 **왜 이게 걸렸는지를 좌표로 설명할 수 없다.**

→ **FTS5/BM25가 1차 경로**(결정론적, 설명 가능, 분기 가능). 임베딩은 **재순위화
전용 옵션 레이어**로 두고, 검색 결과 유무 판정에는 절대 관여시키지 않는다.

---

## 4. 색인 설계

### 4.1 문서 정규화 — 최소 공통 스키마

리포별 어댑터가 서로 다른 6종 포맷을 하나의 행으로 정규화한다. **자연어 필드와 분기
가능 필드를 물리적으로 분리한다**(제약 ④).

```
doc(
  -- 좌표 (전부 ID/문자열, 자유 텍스트 아님)
  uid            TEXT PK,        -- <repo>:<path>#<locator>
  repo           TEXT,           -- enum: bd | ms | rt
  commit_sha     TEXT,
  path           TEXT,
  locator        TEXT,           -- 섹션·표 행·JSON 포인터

  -- 분기 가능 필드 (enum / 숫자 / bool)
  kind           TEXT,           -- enum: paper|book|entry|run|wiki_*|expertise|literature|calibration|decision|system|challenge
  origin         TEXT,           -- enum: BD ORIGINS ∪ MS source ∪ rt
  evidence       TEXT,           -- enum: measured | assumed | confirmed_default | null
  tier           INTEGER,
  provenance     TEXT,           -- enum: from_drawing|from_paper|from_knowledge|assumed|derived
  reproduced     TEXT,           -- enum: yes | no | partial | null
  lab_authored   INTEGER,        -- bool
  advances       INTEGER,        -- bool — evidence=measured 에서만 1
  review_after   DATE,
  superseded_by  TEXT,           -- uid 또는 null
  has_falsifier  INTEGER,        -- bool  ← challenge 가능 여부를 결정
  doi            TEXT,

  -- 사람이 읽는 필드 (어떤 코드도 분기하지 않음)
  title          TEXT,
  body           TEXT,           -- FTS5 대상
  conditions     TEXT            -- 유효 조건 원문
)
```

`has_falsifier`가 특히 중요하다. `kb-schema.md` §4.7: *"falsifier 없는 엔트리는
challenge할 수 없다. 그건 그 엔트리의 결함이고 여기의 빈틈이 아니다."*
→ **`has_falsifier = 0`인 엔트리 목록 자체가 두 리포에 돌려줄 결함 보고서다.**

### 4.2 필드 매핑 — 실제 frontmatter 계약에서

추측이 아니라 각 리포가 기계용으로 선언해 둔 계약에서 읽는다.

| 출처 | 계약 위치 | 매핑되는 필드 |
|---|---|---|
| BD wiki/source | `knowledge/wiki/CLAUDE.md` frontmatter (`source_frontmatter_required`, `precedence`, `wiki_types`) | kind · origin · lab_authored · reproduced · cites |
| BD entries | `tools/kb.py` `SCHEMA_ENTRY`, `ORIGINS` | kind · origin · system_tags · source |
| BD runs | `bdbot.record/0.1` | tier · dimensionless · observables · provenance |
| MS kb/literature | `kb/literature/_template.md` frontmatter | evidence · confidence · gate · scope · measured_on · review_after · superseded_by_measurement |
| MS kb/expertise | 실제 엔트리 frontmatter (`Q-002`가 domain-neutral로 확인) | question · evidence · scope · applies_to_systems · review_after · supersedes |
| rt | `kb-schema.md` §4.1–4.7 | 7종 엔트리 스키마 |

> **BD `wiki/CLAUDE.md`가 명시한다: "코드는 경로를 하드코딩하지 말고 frontmatter를
> 파싱한다."** 어댑터는 이 지시를 그대로 따른다. 경로를 하드코딩하면 BD가 폴더를
> 옮길 때 §1.2의 실패(생성기와 생성물의 분리)를 Librarian이 재현한다.

### 4.3 drift 감지 — 색인이 상하는 것을 색인이 잡는다

`kb-schema.md` §6의 열린 항목 *"`rigor/`가 BD·MS의 실제 파일과 어긋나는 것을 어떻게
감지하는가 — 손으로 관리하는 `implemented_in`은 상한다"*에 대한 답.

매 색인 빌드가 계산하는 결정론적 리포트:

| 검사 | 검출하는 것 |
|---|---|
| `review_after < today` | 만료된 엔트리 |
| `superseded_by_measurement` 대상 부재 | 끊긴 승계 사슬 |
| `has_falsifier = 0` | challenge 불가능한 엔트리 = 엔트리 결함 |
| 생성물 vs 생성기 부재 | §1.2 — INDEX.md류 고아 생성물 |
| 선언된 항목 수 ≠ 실제 파일 수 | §1.2 — 뒤처진 색인 |
| `[[wikilink]]` / 상대경로 대상 부재 | 끊긴 상호참조 |
| `reproduced: no`인데 근거로 인용됨 | BD wiki 규율 위반 |
| `evidence: assumed`인데 `advances: YES` | **§1.5의 −4~−14 % 사고 재발** |

**마지막 두 개가 이 리포트의 값이다.** 나머지는 위생이고, 이 둘은 두 리포가 스스로
비용을 기록해 둔 실제 사고의 재발 탐지다.

---

## 5. MCP 도구 표면

### 5.1 문맥 인식 검색 — 프로파일이지 LLM 판단이 아니다

사용자 요구의 핵심(*"각 에이전트/서브에이전트의 문맥을 포함한 질문"*)에 대한 답은
BD `I-053`에 이미 있다:

> *관점 분리는 별도의 저장소로 만드는 것이 아니라 **페르소나마다 다른 검색 질의**로
> 만든다. 결과: 큰 코퍼스는 컨텍스트 비용이 0이다 — 그건 색인이고 컨텍스트가 아니다.*

→ **`caller_profile`은 버전 관리되는 설정 파일이다. LLM이 매번 만드는 질의가 아니다.**

```yaml
# profiles/ms-lens4-photo.yaml
id: ms:lens-4-photo-perturbation
prefer_kinds:   [literature, calibration, expertise, paper]
require_fields: [evidence, tier]         # 없으면 히트 자체를 버린다
boost:
  quantity_match: 3.0                    # data/*.yaml 필드명 일치
  gate_match:     2.5                    # G10 등
exclude:
  reproduced: [no]                       # 미재현 값을 근거로 올리지 않는다
return_always:  [falsifier, conditions, transfer_conditions]
```

프로파일 초기 세트 (각 리포의 실제 서브에이전트에서 도출):

| 프로파일 | 도출 근거 |
|---|---|
| `ms:lens-{1..8}` | MS `.claude/agents/` 5개 + 게이트 모듈 |
| `bd:s1`…`bd:s8` | BD `.claude/skills/bd-pipeline/references/s*.md` |
| `bd:lit-distill` · `bd:lit-scan` | BD `.claude/agents/bd-lit-*.md` |
| `rt:V1-frontier` · `rt:V2-unfinished` | rt `design/personas/` |

### 5.2 도구 8개

읽기 6개 + 쓰기 2개. **쓰기는 `store/`에만 닿는다.**

| 도구 | 서명 | 반환 |
|---|---|---|
| `kb_search` | `(question, caller_profile, kinds?, limit?)` | 히트 + `repo@sha:path#locator` + evidence/tier + falsifier. **결과 0개는 `not_searched`가 아니라 `searched_empty`로 명시** (제약 ①) |
| `kb_get` | `(uid)` | 본문 + frontmatter 전체 |
| `kb_neighbors` | `(uid, relation)` | `cites` / `used_by` / `supersedes` 그래프 이웃 |
| `kb_supplies` | `(field \| gate)` | 그 레지스트리 필드/게이트를 공급하는 엔트리. **MS의 `bleach_photons`×G10이 살아있는 사례** |
| `kb_gaps` | `(caller_profile)` | 입력이 없어 `BLOCKED`인 게이트 · `parameters_extracted: no` 논문 · `has_falsifier=0` 엔트리 |
| `kb_stale` | `()` | §4.3 drift 리포트 |
| `kb_challenge_raise` | `(target_uid, doubt_kind, falsifier_cited, …)` | `store/challenge/`에 기록 + **falsifier 타입으로 라우팅**. `falsifier_cited` 없으면 거부 |
| `kb_digest` | `(week?)` | 주간 정제 산출물 |

**`kb_challenge_raise`의 두 강제 사항** (`kb-schema.md` §4.7):

- `falsifier_cited`는 **필수**이고 **대상 안을 가리켜야 한다** — 도전자 쪽이 아니다.
  이게 challenge를 *논증*이 아니라 *작업 지시*로 만든다.
- 라우팅은 **발신자가 아니라 falsifier의 종류**가 결정한다:
  측정 → MS · 런 → BD · 유효조건 → rt · 없음 → 사람.
- `depth` 증가 · `cost` 기록. 없으면 루프가 주제 대신 의심을 순환시킨다(`C-001`).

**Librarian이 판결할 수 있는 유일한 것:** `resolvable_by: literature`에 대해
**locator의 존재/부재만** (인용된 섹션이 실제로 있는가, 그 조건을 진술하는가).
그 외는 `unknown`을 낸다. `kb-schema.md` §6은 이걸 *"문서에서 가장 큰 미해결 항목"*
(`C-007`)으로 기록해 두었고 — **Librarian은 그것을 해결하지 않고, 약한 질문에만
결정론적으로 답한다.**

---

## 6. 주간 잡 — 토→일 새벽  ⏸ **연기 (2026-09-06)**

> **주 1회 자동화는 나중에 구현한다.** 아래 설계는 유지하되 v1 인수 조건에서 빠진다.
> 색인 갱신은 `librarian reindex` + `index_stale` 자기신고로 대체 → [BUILD.md](BUILD.md) §4-D

사용자 요구: 주 1회 주간 축적분(실험 데이터·논문)을 종합해 정제·재저장.

이건 `kb-schema.md` §5의 *"refresh는 문서가 아니라 hook이다"* 를 스케줄로 옮긴 것이다.
**다만 결정론적 부분과 LLM 부분을 반드시 분리한다** — 제약 ②가 걸린다.

### Tier 1 — 결정론적. 무조건 돈다

**GitHub Actions cron: `0 18 * * 6`** (토 18:00 UTC = **일 03:00 KST**).
노트북이 깨어 있어야 하는 조건과 API 예산에서 독립시킨다. 세 리포가 public이므로
CI가 clone할 수 있다.

1. `git fetch` × 3 → 새 SHA 기록
2. 색인 전면 재빌드 (증분 아님 — 파생물이므로 재빌드가 정본)
3. 지난주 `manifest.json`과 diff → **주간 델타**: 새 run, 새 논문, 새 decision, 새 finding
4. §4.3 drift 리포트 전량 실행
5. `store/digest/<ISO주차>/` 에 커밋: `delta.json` · `drift.json` · `manifest.json`
6. drift에 신규 항목이 있으면 **Librarian 리포에 이슈 생성** (BD/MS에는 쓰지 않는다)

**Tier 1은 LLM을 쓰지 않는다.** 그래서 실패해도 조용히 틀리지 않고 명확히 실패한다.

### Tier 2 — LLM 정제. 제안만 한다

Tier 1이 끝난 뒤 로컬 스케줄 작업으로 실행. **산출물은 전부 `store/inbox/`에 제안으로
들어가고, 사람 승인 없이는 어디에도 반영되지 않는다.**

| 정제 작업 | 산출물 | 왜 제안인가 |
|---|---|---|
| 새 BD 논문 → MS `_template.md` 형식으로 분해 (1→N, §1.4) | `inbox/crosswalk/*.md` | MS `kb/literature/`에 들어갈 값이다. 값은 MS 소유(charter §3) |
| 새 run 256+개 중 반복 패턴 → `entries/` 후보 | `inbox/entries/*.json` | BD `entries/` 소유는 BD |
| 만료된 `review_after` → challenge 초안 | `inbox/challenge/*.json` | `falsifier_cited` 인용이 맞는지는 사람이 본다 |
| `kb_gaps` 종합 → "다음에 측정할 것" 목록 | `digest/worklist.md` | MS README: *"이 폴더에 있는 것이 정확히 다음에 측정할 가치가 있는 것"* |

**Tier 2에 금지된 것:**

- 숫자 생성·값 요약 (제약 ②). 인용과 locator만 생산한다.
- 여러 엔트리를 평균·집계 (제약 ⑤, `kb-schema.md` §3)
- `evidence: measured` 부여 — Librarian은 아무것도 측정하지 않는다
- 원본 리포 직접 수정 (§3.1 불변식 1)

### 6.1 공개 범위 게이트 — 첫 digest 전에 있어야 한다

`research-topic` README §8이 미해결로 남긴 `T-019`①:

> *"KB에 쌓일 주제 평가는 미발표 연구 방향이다. … 이건 누가 리포를 읽을 수 있는가의
> 문제가 아니라 **J1이 리포에 무엇을 쓸 수 있는가의 규칙**이 된다. 그 규칙은 아직
> 없고, 첫 주제 평가가 들어오기 전에 있어야 한다 — 공개 리포에서는 나중에 파일을
> 지워도 공개가 되돌려지지 않는다."*

**주간 digest가 정확히 그 산출물이다.** 그래서:

1. ~~Librarian 리포는 private로 시작한다.~~ → **public으로 결정 (2026-09-06).**
   그래서 이 절의 부담이 커진다: Librarian이 생산하는 것은 세 리포의 *교차 종합*이고,
   그게 미발표 연구 방향에 가장 가까운 형태다. **주간 digest는 연기되었으므로 지금은
   노출이 없지만, 구현 시점에 `publish-gate`가 이미 있어야 한다** — 공개 리포에서는
   나중에 파일을 지워도 공개가 되돌려지지 않는다 (rt `T-019`①).
2. **`publish-gate`**: 공개 경로에 쓰려는 시도를 차단하는 검사. BD가 이미 같은 문제를
   폴더 단위로 풀어 놓았다 — `source/papers/`(공개) vs `source/lab/`(gitignore),
   *"보호해야 할 것은 저작자가 아니라 아직 발표되지 않았다는 사실"*. 같은 경계를
   `store/` 안에 재현한다.
3. **인명 금지 상속**: rt `T-018`/`T-035` — *"인용은 남고 귀속은 간다."*
   digest가 "X 교수라면 이걸 …로 볼 것"류 문장을 생산하면 안 된다.

---

## 7. 단계별 계획

각 단계는 **종료 조건**을 가진다. 종료 조건 없는 단계는 끝나지 않는다(rt README §4 방식).

### Phase 0 — 골격과 어댑터 (읽기 전용)

| 작업 | 종료 조건 |
|---|---|
| 리포 초기화, `cache/` git fetch 3종 | `manifest.json`이 세 SHA를 기록 |
| 어댑터 6종 (BD wiki·source·entries·runs, MS kb, rt design) | **520 문서가 하나의 `doc` 테이블에 들어가고, 좌표 없는 행이 0개** |
| §4.3 drift 리포트 | §1.2의 두 결함(생성기 부재·항목 수 2 차이)을 **자동으로 재발견** |

> 마지막 종료 조건이 Phase 0의 핵심이다. 사람이 손으로 찾은 결함을 도구가 못 찾으면
> 그 도구는 아직 아무것도 하지 않는다.

### Phase 1 — 검색과 MCP (사용자 요구의 본체)

| 작업 | 종료 조건 |
|---|---|
| FTS5 색인 + `kb_search`/`kb_get`/`kb_neighbors` | BD의 **"query both"가 한 번의 질의로 해결** (§1.3) — `wiki/`와 `entries/`에 각각 있는 교훈이 같은 결과 집합에 나온다 |
| `caller_profile` 3개 (MS lens 1개, BD stage 1개, rt persona 1개) | 같은 질문 + 다른 프로파일 → **다른 상위 결과**. 같으면 프로파일은 장식이다 |
| `kb_supplies` · `kb_gaps` | MS `bleach_photons` × G10에 대해 *"현재 BLOCKED, 공급 후보 없음"* 을 정확히 반환 |
| MCP 서버 등록 | 세 리포 각각의 Claude Code 세션에서 도구가 호출됨 |

### Phase 2 — 인터록 (내용 축적 **전에**)

rt README §4 Phase 2와 같은 순서. **거꾸로 보이는 것이 의도다** — 형식이 고정되기 전에
채우면 형식이 바뀔 때 채운 것을 버린다.

| 작업 | 종료 조건 |
|---|---|
| Tier 1 주간 잡 | 2주 연속 사람 개입 없이 digest 생성 |
| `publish-gate` (§6.1) | 미발표 내용을 공개 경로에 쓰려는 시도가 **차단됨을 테스트로 증명** |
| 색인 재생성 강제 | `index/` 전체 삭제 후 재빌드 → 결과가 비트 단위 동일 |
| ID 발급 규칙 | `kb-schema.md` §6의 *"누가 ID를 발급하는가 — 순차 번호는 병렬 쓰기에서 충돌"* → **내용 해시 기반**으로 결정 (BD `run_id` 방식 상속) |

### Phase 3 — Row 2 crosswalk

가장 값이 큰 단일 산출물. §1.4에서 매핑이 이미 1→N으로 확정되었으므로 협상이 없다.

| 작업 | 종료 조건 |
|---|---|
| BD `provides` → MS quantity 분해기 | BD 논문 1편이 MS 형식 N개 파일 초안으로 나온다 |
| Tier 2 LLM 정제 | `inbox/crosswalk/`에 **MS `_template.md`의 필수 섹션이 하나도 비지 않은** 초안 |
| 사람 승인 경로 | 승인된 1건이 MS `kb/literature/`에 **PR로** 들어가 머지 — **MS의 첫 문헌 엔트리** |

> **이게 성공하면 row 2가 닫힌다.** README §2.1이 *"가장 날카로운 틈"*이라고 부른 행이고,
> 한쪽은 내용 42건, 다른 쪽은 그것을 받도록 만든 빈 폴더를 갖고 있다.

### Phase 4 — 은퇴(custody)

| 작업 | 종료 조건 |
|---|---|
| `kb_challenge_raise` + 라우팅 표 | falsifier 타입별로 4개 경로가 모두 한 번씩 라우팅됨 |
| `resolvable_by: literature`의 약한 결정자 | locator 존재/부재만 판정, 그 외 `unknown`. **`C-007`을 해결하지 않는다** |
| `depth` · `cost` 상한 | 상한 초과 challenge가 사람 경로로 나간다 |

### 계획에 없는 것

- **J2 (주제 선정)** — 별개 job. Librarian이 J2를 하기 시작하면 rt `charter.md` §5의
  *"주제의 가치를 판정하지 않는다"* 를 위반한다.
- **J3 (rigor 정의)** — 소유자는 rt. Librarian은 `implemented_in` **drift만 감지**한다.
- **monorepo 전환 (option B)** — rt README §7의 결정 시점은 Phase 1 이후이고, 그건
  Librarian의 결정이 아니다.
- **회고적 가치 검증** — rt `C-003`. 답이 없다고 기록되어 있다.

---

## 8. 실패 모드 — 미리 이름 붙인 것

BD `I-075`/`I-076`은 KB가 죽는 두 방식을 이미 진단했다. Librarian은 **그 두 방식의
방어 장치 자체**이므로, 자기가 그 방식으로 죽으면 아무 방어가 없다.

| 실패 | 증상 | 방어 |
|---|---|---|
| **아무도 안 채운다** (`I-075`) | `store/inbox/`가 승인 대기로 쌓임 | Tier 1은 사람 없이 돈다. Tier 2 적체 자체를 digest가 보고 |
| **색인이 상한다** (`I-076`) | §1.2의 재발 | 색인은 매주 전면 재빌드. 증분 없음 |
| **생성기와 생성물이 분리된다** | §1.2 실측 사례 | 생성물 헤더에 생성기 경로 + SHA. drift 검사가 생성기 부재를 잡음 |
| **자연어가 상태가 된다** (`I-133`) | digest 요약문을 다른 에이전트가 근거로 인용 | digest는 좌표만 싣는다. 요약 문단에는 인용 가능한 ID를 부여하지 않는다 |
| **Librarian이 enforcer가 된다** | 값을 정하거나 challenge를 판결 | §3.1 불변식 3개. 쓰기 경로가 `store/`뿐 |
| **미발표 방향이 공개된다** | 공개 리포에 digest 유출 | private 시작 + `publish-gate` (§6.1) |
| **검색 순위가 가치가 된다** | rank가 엔트리에 저장됨 | §2.1 — 반환만, 저장 안 함 |

---

## 9. 결정이 필요한 것

계획은 아래 기본값으로 작성되었다. 바꿀 항목이 있으면 해당 절이 바뀐다.

| # | 결정 | 기본값(권고) | 바뀌면 영향 |
|---|---|---|---|
| 1 | Librarian 리포 공개 범위 | ✅ **public — 결정 2026-09-06** | 그래서 `publish-gate`(§6.1)가 Phase 0으로 앞당겨진다. 주간 digest 구현 **전에** 있어야 함 |
| 2 | 세 리포 접근 경로 | **public remote `git fetch`** + 로컬 경로 override | §1.6. 로컬 전용이면 MS(Windows)에서 안 돌아감 |
| 3 | 원본 리포 쓰기 권한 | **없음.** PR 제안만 | §3.1. 직접 쓰기를 허용하면 되돌릴 수 없어지고 option A의 근거가 사라짐 |
| 4 | Tier 1 실행 위치 | **GitHub Actions** (일 03:00 KST) | 로컬 launchd면 노트북이 깨어 있어야 함 |
| 5 | 임베딩 레이어 | **Phase 1에서 미포함**. FTS5로 먼저 측정 | §3.2. 넣으면 결정론성 경계를 명시해야 함 |
| 6 | 첫 프로파일 | MS lens 4 (photo) · BD s2 (prediction) · rt V1 | §5.1. 다른 조합을 원하면 Phase 1 종료 조건이 바뀜 |
| 8 | `D:\\data` 접근 경로 | **랩 PC에서 실행** 또는 메타데이터 export 반입 | 취득 2,343건이 리포 밖에 있다 (§0.2①) |
| 7 | 언어 | 코드·스키마 영어 / 문서 한국어 | BD는 한국어 혼용, MS·rt는 영어. 색인 본문은 양쪽 다 들어옴 |

---

## 10. 참조

| 문서 | 이 계획에서 쓰인 곳 |
|---|---|
| rt `README.md` §1 · §2.1 · §2.2 · §4 · §7 · §8 | J1 정의 · row 2 · challenge · phase 방식 · option A · 공개범위 |
| rt `design/charter.md` §3 · §4 · §5 | 소유권 경계 · 색인≠이전 · 구조적 금지 |
| rt `design/kb-schema.md` §1 · §3 · §4.1 · §4.7 · §5 · §6 | 자연어≠상태 · 스칼라 금지 · literature 스키마 · challenge · 색인 · 미해결 |
| BD `docs/03-knowledge-base.md` §1 · §4 | 두 스키마 부채 · provenance/tier 사고 |
| BD `knowledge/wiki/CLAUDE.md` | frontmatter 계약 (경로 하드코딩 금지) |
| BD `tools/kb.py` | ORIGINS · FTS5 계획 · 조용히 빈 읽기 사고 |
| MS `kb/literature/README.md` · `_template.md` | 저장 단위 · advances 규칙 · transfer conditions |
| MS `kb/expertise/oil-objective-trapping-in-water.md` | 이미 성립한 challenge의 실례 |
