# 파일트리 설계

작성 2026-09-06 · 상태 `draft` · [PLAN.md](PLAN.md) §0 대체
· **§3 개정** — 세 리포 KB 삭제 결정 반영 → [MIGRATION.md](MIGRATION.md)
· **`kb/08-retrieval/` 추가** — 자체 피드백 지식 → [FEEDBACK.md](FEEDBACK.md)
· **v1 = 현미경(MS) 전용.** 폴더는 8개 다 만들고 `05`·`06`은 v2까지 비워 둔다 → [PLAN.md](PLAN.md) §0

**범위 변경 반영:** Librarian은 `research-topic`의 J1이 아니라 **네 번째 축**이다.
`research-topic`은 연구 제안·검증으로 남고, Librarian은 **지식의 관리·보관·상호작용**을
맡는다. 이 변경의 실질적 귀결은 하나다 — **Librarian은 내용을 소유한다.** 이전 계획은
"색인만 하고 병합하지 않음"이었고, 이제 정본(canonical)을 직접 갖는다. 트리 설계가
이 지점에서 갈린다.

---

## 1. 제안하는 7개 카테고리 — 무엇이 이미 맞는가

사용자 목록은 두 리포가 독립적으로 도달한 구분과 이미 일치하는 부분이 있다. 근거를
붙여 둔다 — 근거 있는 경계는 나중에 흔들리지 않기 때문이다.

**① `1 실험-재료`를 `2 현미경-하드웨어`에서 분리한 것은 정확하다.**
MS `docs/02-knowledge-base.md` §8이 `kb/samples/`를 만든 이유가 그대로 이것이다:

> *"Knowledge attached to **what is being imaged**, not to a system. **It survives
> hardware changes.**"*

두 카테고리를 가르는 축은 주제가 아니라 **수명**이다. 대물렌즈를 바꾸면 2는 바뀌고
1은 남는다. 그래서 이 분리는 취향이 아니라 검사 가능한 규칙이다.

**② `7 주요 학술자료-도서`를 별도로 둔 것도 정확하다.** 다만 이유는 주제가 아니라
**저작권 경계**다. BD는 이걸 이미 폴더 단위로 풀었다 — `raw/`는 gitignore, 증류만 in-git,
그리고 handbook 계약: *"책이 저장소에 없어도 주장을 페이지까지 되짚을 수 있다."*

---

## 2. 구조적 문제 세 개 — 주제로만 가르면 깨지는 것

### 문제 A · 카테고리 4는 나머지 여섯과 종류가 다르다

`1·2·3·5·6·7`은 **세계에 대한 지식**이다. `4 각 (서브)에이전트의 구조/기능`은
**시스템 자신에 대한 지식**이고, 결정적으로 **파생물이다** — 세 리포에 커밋이 들어가면
즉시 낡는다.

| | 1·2·3·5·6·7 | 4 |
|---|---|---|
| 출처 | 측정·문헌·경험 | 세 리포의 파일 |
| 변화 속도 | 느림 (달 단위) | 커밋마다 |
| 쓰는 주체 | 사람·에이전트 | **생성기만** |
| 손으로 고쳐도 되나 | 예 | **아니오** |

같은 층에 두면 주간 잡이 곤란해진다 — 전부 재생성하면 사람이 쓴 것을 지우고,
아무것도 재생성하지 않으면 4가 상한다. 그리고 **그 실패는 이미 BD에서 관측되었다**:
`knowledge/source/papers/INDEX.md`는 "직접 고치지 말 것"이라고 적혀 있는데 생성기
`docs/tools/wiki_index.py`는 리포에 없고, 항목 수도 40 vs 실제 42로 뒤처져 있다.

**→ 4는 `map/`(파생)으로 분리한다. `kb/`(정본)에서 번호 04가 비는 것이 이 규칙의 표시다.**

### 문제 B · `5 물리현상`과 `6 시뮬레이션`이 겹친다

GSER(`knowledge/source/papers/1995-mason-weitz-gser-microrheology.md`)은 물리현상인가
시뮬레이션인가? 물리현상이지만 시뮬레이션이 소비한다. 두 폴더가 다 있으면 한쪽에
들어가고 다른 쪽 검색에서 빠진다. **이건 BD가 이미 "리포 최대 부채"라고 부른
`wiki/` vs `entries/` 분열이 폴더 층에서 재발하는 것이다.**

경계 규칙 하나로 자른다:

> **엔진을 HOOMD → LAMMPS로 바꾸면 그 엔트리가 바뀌는가?**
> 바뀐다 → `06-simulation` · 안 바뀐다 → `05-physics`

GSER은 안 바뀐다 → 05. `Δt` 게이트, 무차원화 규약, 평형화 판정은 바뀐다 → 06.
검사 가능한 규칙이므로 두 사람이 같은 답을 낸다.

### 문제 C · `3 현미경-소프트웨어`가 세 가지를 가리킨다

MS 안에 서로 다른 세 종류의 "소프트웨어"가 실재한다.

| 무엇 | 실제 위치 | 어디로 가야 하나 |
|---|---|---|
| (a) **장비 제어 스택** — MicroManager `.cfg`, piezo command set, LUNF/DAQ | MS `config/micromanager/`, `reference/npcd-command-set.md` | **`03-control`** |
| (b) **MS 에이전트 자신의 코드** — 8 gate 모듈, G1–G32 | MS `optics/`, `sample/`, `compute/`… | **`map/04-agents`** (파생) |
| (c) **분석 코드** — `D:\codes` | 리포 밖. MS lens 6만 읽는다 | **결정 필요** (§6) |

(c)가 특히 문제다. MS `.claude/agents/measurement-validity.md`는 lens 6을
*"the only lens that also reads the analysis code (`D:\codes`)"*로 정의한다.
즉 **판정에 쓰이는 코드가 세 리포 어디에도 없다.** 색인 대상인지가 정해져야 한다.

---

## 3. 제안 트리 — 쓰기 권한으로 최상위를 가른다

주제는 두 번째 층이다. 최상위는 **누가 쓸 수 있는가**로 가른다. 그것이 "이 파일을
지우고 재생성해도 되는가"를 결정하는 유일한 축이기 때문이다.

```
Librarian_agent/
│
├── kb/                    ★ 정본. 사람·에이전트가 쓴다. 재생성 불가
│   ├── README.md              쓰기 규칙 + 번호 04가 없는 이유
│   ├── 00-decisions/          결정 로그 (주제 아님, 시간순) — MS kb/decisions/ 20건 상속
│   ├── 01-materials/          ← 1 실험-재료
│   ├── 02-hardware/           ← 2 현미경-하드웨어
│   ├── 03-control/            ← 3 현미경-소프트웨어 (a: 장비 제어 스택)
│   ├── 05-physics/            ← 5 물리현상
│   ├── 06-simulation/         ← 6 시뮬레이션
│   ├── 07-sources/            ← 7 주요 학술자료·도서
│   │   ├── papers/                증류 1편 = 1파일. in-git
│   │   ├── books/                 증류만. `<증류>#<절> ← [약칭] p.<쪽>`
│   │   └── raw/                   ★ .gitignore — 원본 PDF는 저장소에 안 들어간다
│   └── 08-retrieval/          ★ 자체 지식 — 어떤 질문에 무엇을 답했고 무엇이 인용됐나
│       ├── sessions/              질의 1건 = 형식 객체 1개
│       ├── oracles/               회귀 테스트로 승격된 레코드 (사람 승인)
│       └── findings/              "이 프로파일은 이래서 실패한다" — 원인
│                              → 스키마·규칙: FEEDBACK.md
│
├── map/                   ◆ 파생. 주간 잡이 전면 재생성. 손으로 고치지 않는다
│   ├── 04-agents/             ← 4 각 (서브)에이전트의 구조/기능
│   │   ├── bd/                    9 agents · 6 skills · 4 rules · A1–A10
│   │   ├── ms/                    5 lenses · 8 gate 모듈 · G1–G32
│   │   └── rt/                    personas V1·V2 · J1–J3 · charter 경계표
│   └── manifest.json          {repo: sha, built_at, doc_count}
│                              ※ mirror/ 는 삭제 — KB 이관 후 가리킬 대상이 없다
│
├── export/                ◆ 파생·역방향. Librarian → 세 리포로 내보내는 읽기 전용 사본
│   ├── bd/                    BD가 오프라인·grep으로 읽는 경로 (pytest 오라클 포함)
│   └── ms/                    MS 렌즈가 Read/Grep/Glob 으로 읽는 경로
│                              → 왜 필요한가: MIGRATION.md §3
│
├── index/                 ◆ 파생. 전량 삭제 후 재생성해도 손실 0
│   └── kb.sqlite              FTS5 + 메타
│
├── store/                 ● Librarian이 발행하는 것
│   ├── challenge/             은퇴 메커니즘
│   ├── digest/<ISO주차>/      주간 정제 산출물
│   ├── crosswalk/             BD paper → MS quantity 매핑 (1→N)
│   └── inbox/                 LLM 제안 — 사람 승인 대기
│
├── profiles/              caller_profile YAML — 문맥별 질의 (PLAN.md §5.1)
├── adapters/              리포별 frontmatter 파서
├── mcp/                   MCP 서버
└── cache/                 .gitignore — 세 리포 shallow clone
```

**최상위 4구역의 불변식:**

| 구역 | 표시 | 쓰기 주체 | 지워도 되나 |
|---|---|---|---|
| `kb/` | ★ 정본 | 사람 · 승인된 에이전트 | **아니오** |
| `map/` · `index/` | ◆ 파생 | 생성기만 | **예** — 재생성이 정본 |
| `store/` | ● 발행물 | Librarian | 아니오 (이력) |
| `cache/` | — | git fetch | 예 |

> **`map/`과 `index/`가 지워도 되는 것이 설계의 핵심이다.**
> 이 성질을 유지하는 한 §2 문제 A의 부패(생성기 없는 생성물)가 구조적으로 불가능하다.
> 파생물이 정본을 조금이라도 담게 되면 이 성질이 깨지고, 그 순간 BD `INDEX.md`와
> 같은 상태가 된다.

---

## 4. 주제 폴더 내부 — 여섯 곳 모두 같은 모양

두 번째 층을 **또 주제로 나누지 않는다.** 주제를 더 깊게 파면 두 곳에 속하는 파일이
반드시 나오고, 거기서 분류가 죽는다.

대신 **검증 방식으로 나눈다.** BD `docs/03-knowledge-base.md` §2의 근거를 그대로 상속한다:
*"six kinds, **because they are verified differently**."*

```
kb/0X-<subject>/
├── _index.md          ◆ 생성물. 헤더에 생성기 경로 + SHA 필수
├── cards/             ★ 정본 단위 — (대상 × 목적) 1쌍 = 1파일
├── evidence/
│   ├── measured/          이 랩에서 측정.  evidence: measured  → advances 가능
│   └── assumed/           문헌·추정.      evidence: assumed   → advances 금지
├── findings/          Q→A + 인용.  dead-end-<slug>.md 포함
└── questions/         아직 답 없음. 삭제하지 않고 status로 닫는다
```

### 왜 `cards/`가 값과 분리되는가

BD `knowledge/wiki/CLAUDE.md`가 실측으로 보여준 것: **무차원화 규약과 주요 파라미터는
계 하나만으로 정해지지 않는다.** 같은 랩 안에서 기준 단위가 셋으로 갈렸다 —
ABP×제어는 기준시간 `τ_r`, 브러시콜로이드×비평형접촉은 `τ_D`, 수동tracer×수송도 `τ_D`.

> *"카드가 없는 쌍을 만나면 즉흥으로 무차원화하지 않는다."*

**카드는 규약과 라우팅을 소유하고, 값은 소유하지 않는다.** 값은 `evidence/`에 있고
티어가 붙는다. 이 분리가 없으면 "이 계에서 `dt`를 얼마로 했는가"에 출처가 안 붙는다.

각 주제의 카드 단위:

| 주제 | 카드 = |
|---|---|
| `01-materials` | (시료계 × 관측 목적) — ATPS PEG/dextran × 계면완화 |
| `02-hardware` | (장비 구성 × 모드) — current-laser × 광집게 |
| `03-control` | (제어 스택 × 작업) — MicroManager dualcam × 2색 동시취득 |
| `05-physics` | (현상 × 체제) — 미세유변학 × 점탄성 선형응답 |
| `06-simulation` | (계 × 목적 동역학) — **BD 규약 그대로 상속** |
| `07-sources` | 카드 없음. 증류 1편 = 1파일 |

### 왜 `evidence/measured` vs `assumed`가 **폴더**인가 (frontmatter가 아니라)

두 리포가 이미 폴더로 갈랐다. MS: `kb/calibrations/`(측정) vs `kb/literature/`(문헌),
그리고 *"a value this lab has measured … **outranks anything here**."*
BD: `source/papers/`(공개 가능) vs `source/lab/`(gitignore).

BD가 그 이유를 명시한다: **공개 경계가 폴더 단위로 걸린다.**

그리고 티어 오분류의 비용이 실측되어 있다 — BD는 `T = 300 K`를 tier 1(measured)로
잘못 적어 **하류 모든 `τ_B`에 −4 %~−14 % 오차를 전파**시켰다. frontmatter 한 줄은
잘못 적히고 눈에 안 띈다. **경로는 눈에 띈다.**

> `evidence` frontmatter는 그대로 유지한다. 폴더는 중복이 아니라 **교차검증**이다 —
> 경로와 필드가 어긋나면 색인이 잡는다 ([PLAN.md](PLAN.md) §4.3 마지막 행).

---

## 5. 실험 데이터 본체는 트리에 들어오지 않는다

사용자 요구 중 *"주간에 쌓인 실험데이터"* 항목. MS `docs/02` §6이 실측 규모를 기록해
두었다: **아카이브된 취득 2,343건**, `kb/envelope.sqlite`로 색인.

**Librarian은 취득 데이터를 보관하지 않는다.** 보관하는 것은 세 가지뿐:

| 들어오는 것 | 어디로 |
|---|---|
| 취득의 **색인** (조건·메타데이터) | `index/kb.sqlite` — MS `envelope.sqlite` 스키마 상속 |
| 취득에서 나온 **측정값** | `kb/0X/evidence/measured/` |
| 취득에서 나온 **해석** | `kb/0X/findings/` |
| 이미지·프레임·원시 배열 | **들어오지 않는다.** 좌표만 |

`raw/`를 gitignore하는 것과 같은 이유이고, BD가 같은 규칙을 이미 적용하고 있다 —
*"저장소는 PDF 보관소가 아니다."*

---

## 6. 결정이 필요한 것

| # | 결정 | 권고 | 근거 |
|---|---|---|---|
| 1 | 분석 코드 `D:\codes` (§2-C의 c) | **`map/`에 색인, `kb/`에 안 넣음** | 리포 밖 · 커밋마다 변함 → 파생물의 성질 |
| 2 | 카테고리 3의 이름 | `03-control` | "소프트웨어"는 세 가지를 가리킨다 (§2-C) |
| 3 | `05` / `06` 경계 | 엔진 교체 테스트 (§2-B) | 검사 가능해야 두 사람이 같은 답을 낸다 |
| 4 | ~~`map/mirror/`가 포인터냐 사본이냐~~ | **폐기** — KB 이관으로 대상이 사라짐 | → [MIGRATION.md](MIGRATION.md) |
| 5 | 번호 04를 `kb/`에서 비울 것인가 | **비운다** | 빈 번호가 쓰기 권한 분리의 표시가 된다 |
| 6 | `01-materials`가 MS `kb/samples/`를 흡수하나 | **아니오 — 미러** | MS `kb/samples/`는 아직 미구축. 만들어지면 소유는 MS |
| 7 | 한국어 파일명 허용 | **아니오. 경로는 ASCII** | BD entries 파일명이 이미 한글 슬러그로 깨져 있다 (`handbook__buckingham-pi-의-i-n-r-에서…`) |

> **7번은 근거가 실물로 있다.** BD `knowledge/entries/`의 파일명이
> `handbook__c_d-24-re-는-f-3-pi-mu-d-v-와-정확히-같은-것이다-실행-확인.json` 형태다.
> 슬러그 생성기가 한글을 그대로 통과시켜 만들어진 것이고, 이런 이름은 플랫폼 간
> 정규화(NFC/NFD)에서 갈린다 — macOS와 Windows가 섞인 환경(§1.6)에서 같은 파일이
> 다른 파일로 보인다. **본문은 한국어, 경로는 ASCII.**

---

## 7. 사용자 목록 → 최종 매핑

| # | 사용자 카테고리 | 위치 | 변경 |
|---|---|---|---|
| 1 | 실험-재료 | `kb/01-materials/` | 그대로 |
| 2 | 현미경-하드웨어 | `kb/02-hardware/` | 그대로 |
| 3 | 현미경-소프트웨어 | `kb/03-control/` | **범위 축소** — 장비 제어 스택만. 에이전트 코드는 4로, 분석 코드는 결정 대기 |
| 4 | (서브)에이전트 구조/기능 | `map/04-agents/` | **구역 이동** — 정본이 아니라 파생물 |
| 5 | 물리현상 | `kb/05-physics/` | **경계 규칙 추가** — 엔진 교체 테스트 |
| 6 | 시뮬레이션 | `kb/06-simulation/` | 동일 규칙의 반대편 |
| 7 | 주요 학술자료·도서 | `kb/07-sources/` | **3분할** — `papers/` · `books/` · `raw/`(gitignore) |
| — | (없음) | `kb/00-decisions/` | **추가** — MS `kb/decisions/` 20건의 착지점. 시간순이고 주제가 아니다 |
| — | (없음) | `store/` | **추가** — challenge · digest · crosswalk는 주제가 아니다 |
| — | (없음) | `export/` | **추가** — 이관 후 두 리포가 오프라인으로 읽을 경로 |
| — | (없음) | `kb/08-retrieval/` | **추가** — 검색 품질 피드백. Librarian이 자기 자신에 대해 갖는 유일한 정본 지식 → [FEEDBACK.md](FEEDBACK.md) |

7개 중 **4개는 그대로, 3개는 경계 조정, 1개는 구역 이동**이고, 주제가 아닌 산출물을
담을 구역 하나가 추가된다.
