# 구축과 검증 — 이관 전에 무엇을 통과해야 하는가

작성 2026-09-06 · 상태 `draft` · [MIGRATION.md](MIGRATION.md) Step 0

**결정:** 구성을 다 하고, 별도로 작동을 검증한 뒤에 데이터를 이관한다.
**v1 범위: 현미경(MS) 전용** → [PLAN.md](PLAN.md) §0. 픽스처 중 BD 원본을 쓰는 것(F2·F3·F6)은 v2로 미룬다.

이 순서는 취향이 아니라 rt `design/kb-schema.md` §0이 이미 근거를 적어둔 순서다:

> *"No KB entries are created. Only their shape is fixed. … **That order looks
> backwards on purpose.** BD's `I-075`/`I-076` already diagnosed the two ways a KB
> dies. **Filling before the form is fixed means throwing away what was filled
> when the form changes.**"*

그리고 rt README §4 Phase 2가 같은 것을 *"interlocks (**before** any KB content)"*로
못 박아 두었다. **이 결정은 세 리포의 설계와 일치한다.**

---

## 1. 문제 — 빈 KB로는 "작동을 잘 한다"를 판정할 수 없다

검색 시스템의 정상 동작은 **질의에 대해 맞는 것이 나오는 것**이다. `kb/`가 비어 있으면
모든 질의가 0건을 반환하고, 그건 다음 세 상태와 구별되지 않는다.

| 실제 상태 | 반환 |
|---|---|
| 코퍼스가 비었다 | 0건 |
| 색인이 안 붙었다 | 0건 |
| 토크나이저가 한국어를 못 자른다 | 0건 |
| 어댑터가 frontmatter를 못 읽었다 | 0건 |

**네 개가 같은 얼굴이다.** 그리고 이건 BD가 실물로 기록해 둔 사고와 같은 모양이다 —
`tools/kb.py`가 경로 하나 때문에 126개 엔트리에 대해 "0건"을 조용히 보고했고, 주석은
그것을 *"배선 안 된 checker와 같은 실패 모드"*라고 부른다.

**→ 해결: 픽스처 코퍼스.** 실제 엔트리를 **복사**해서 검증한다. 복사는 이관이 아니다.

| | 픽스처 (지금) | 이관 (나중) |
|---|---|---|
| 원본 | **무수정** | 삭제 |
| 되돌리기 | `fixtures/` 지우면 끝 | Step 4 증명 필요 |
| 위치 | `fixtures/` — `kb/`와 분리 | `kb/` |
| 수량 | 8건 | 264건 |

> **픽스처는 이관 시점에 폐기한다.** `kb/`로 옮기지 않는다 — 남겨두면 같은 엔트리가
> 두 곳에 존재하고, 그게 이 프로젝트가 없애려는 상태다.

---

## 2. 픽스처 8건 — 각각이 하나의 주장을 검증한다

> `kb/08-retrieval/` 추가에 따라 픽스처 **F9**가 붙는다 → [FEEDBACK.md](FEEDBACK.md) §5

설계 문서가 한 주장마다 픽스처 하나. 주장을 검증할 픽스처가 없으면 그 주장은 검사되지
않은 것이다.

| # | 검증하는 주장 | 픽스처 (복사 원본) |
|---|---|---|
| **F1** | evidence 티어가 **경로와 필드 양쪽**에 있고 어긋남이 잡힌다 ([TREE.md](TREE.md) §4) | MS `kb/calibrations/camera-readout.yaml` (measured) + BD `1995-mason-weitz-gser-microrheology.md` (assumed) |
| **F2** | BD 논문 → MS quantity 분해가 **1→N**이다 ([PLAN.md](PLAN.md) §1.4) | 같은 mason-weitz 엔트리 — `provides: [gser-formula, msd-to-moduli, newtonian-limit-check]` → 3개 파일 |
| **F3** | 05/06 경계가 **엔진 교체 테스트**로 갈린다 ([TREE.md](TREE.md) §2-B) | BD `wiki/concepts/water-298k.md` (→05) + `wiki/systems/` 카드 1개 (→06) |
| **F4** | `has_falsifier = 0`이 **엔트리 결함 보고서**가 된다 | MS `kb/expertise/oil-objective-trapping-in-water.md` (있음) + BD `entries/*.json` 1건 (없음) |
| **F5** | challenge가 **falsifier 타입으로 라우팅**된다 | 같은 oil-objective 엔트리 — rt README §2.2가 *"a challenge that was upheld"*로 기록해 둔 실례 |
| **F6** | 한국어·영어 혼재 코퍼스에서 검색이 된다 | BD paper 증류(본문 한국어) + MS expertise(영어) |
| **F7** | 파생물 부패가 **자동 검출**된다 ([PLAN.md](PLAN.md) §1.2) | BD `source/papers/INDEX.md` — 생성기 부재 + 40 vs 42 |
| **F8** | `caller_profile`이 결과를 **실제로 바꾼다** ([PLAN.md](PLAN.md) §5.1) | 같은 질문 × `ms:lens-4` / `bd:s2` / `rt:V1` |

**F5와 F4가 같은 파일을 쓰는 것은 의도다.** 그 엔트리 하나가 falsifier·`review_after`·
`supersedes` 슬롯·해결된 challenge를 전부 갖고 있어서, 왕복 전체를 실물로 검증할 수 있는
유일한 실례다.

---

## 3. 먼저 결정해야 하는 것 — 한국어 토크나이저

**스키마 생성 전에 정해야 한다.** FTS5 토크나이저는 `CREATE VIRTUAL TABLE` 시점에
고정되고, 나중에 바꾸려면 전면 재색인이다.

이 기계에서 실측했다 (SQLite 3.45.3):

```
본문: "GSER 로 프로브 입자의 MSD 하나만으로 매질의 복소점탄성률을 뽑는 관계식이다."

토크나이저      질의        결과
unicode61     무차원화      1건
unicode61     무차원       0건   ← "무차원화를" 안에 있는데 못 찾는다
unicode61     점탄성       0건   ← "복소점탄성률을" 안에 있는데 못 찾는다
trigram       무차원       1건
trigram       점탄성       1건
```

**기본 토크나이저(`unicode61`)는 한국어에서 조용히 0건을 반환한다.** BD 코퍼스는
본문이 한국어다 — 논문 증류, `entries/` claim, `wiki/CLAUDE.md` 전부. 즉 §1 표의
네 번째 행이 실제로 발생한다.

`trigram`으로 바꾸면 해결되지만 **2글자 질의에서 새 구멍이 생긴다:**

```
trigram    확산   0건      trigram    점도   0건
trigram    온도   0건      trigram    NA    0건   ← MS의 개구수
```

`NA`가 걸린다는 점이 중요하다 — 한국어 문제가 아니라 **모든 2글자 질의**의 문제이고,
MS 도메인에서 `NA`는 가장 자주 쓰이는 용어다.

### 해결 — 검증된 조합

```
trigram 테이블 하나 + 질의 길이로 분기
  ≥3글자 → MATCH   (BM25 랭킹 있음)
  ≤2글자 → LIKE '%q%'  (랭킹 없음, 정확함)
```

실측 확인:

```
trigram 테이블에 LIKE:   확산 1건 · 점도 1건 · 온도 1건 · NA 1건 · 확산계수 1건
```

**구멍이 없다.** 비용: 색인 크기 `unicode61` 124 KiB → `trigram` 196 KiB (같은 본문
500건, **약 1.6배**). 520 문서 규모에서 무시할 수 있다.

> **형태소 분석기(mecab-ko 등)는 채택하지 않는다.** 외부 의존성이 늘고, 분석 결과가
> 버전에 따라 바뀌면 **같은 질의가 다른 결과를 낸다.** 검색 결과의 유무가 판정에
> 쓰이므로(BD `I-052`) 재현성이 랭킹 품질보다 앞선다.

---

## 4. 인수 조건 — "작동을 잘 한다"의 정의

주관적 판단으로 두면 그것 자체가 rt가 금지한 **자연어를 상태로 쓰는 것**이 된다.
아래가 전부 통과하면 이관을 시작한다.

### A · 구조 (픽스처 없이 통과해야 함)

| 검사 | 통과 조건 |
|---|---|
| 주제 폴더 모양 | `kb/0X/` 6곳이 모두 같은 5슬롯 (`cards`·`evidence/{measured,assumed}`·`findings`·`questions`) |
| 스키마 형식성 | 분기·라우팅·판정에 쓰이는 필드에 **자연어 0개** — 전부 enum/숫자/ID/bool |
| 파생물 재생성 | `index/`·`map/` 전량 삭제 → 재생성 → **비트 단위 동일** |
| 빈 질의 상태 | 빈 `kb/`에 대한 질의가 `searched_empty`를 **명시 반환**. 0건 아님 |
| 좌표 필수 | 좌표(`repo@sha:path#locator`) 없는 히트를 반환하는 경로가 존재하지 않음 |

### B · 검색 (F1·F6·F7·F8)

| 검사 | 통과 조건 |
|---|---|
| 한국어 질의 | 2·3·4글자 및 부분어 질의가 모두 히트 (§3) |
| 프로파일 분기 | 같은 질문에 프로파일 3개가 **다른 상위 3건**. 같으면 프로파일은 장식이다 |
| 티어 교차검증 | `evidence/measured/`에 `evidence: assumed` 파일을 심으면 색인이 **잡는다** |
| 부패 검출 | F7의 두 결함(생성기 부재·40 vs 42)을 **자동으로** 재발견 |
| 티어 동반 | 모든 히트가 `evidence`/`tier`를 싣는다. 없는 히트는 반환 불가 |

### C · 왕복 (F2·F4·F5)

| 검사 | 통과 조건 |
|---|---|
| crosswalk 1→N | mason-weitz 1편 → MS `_template.md` **필수 섹션이 하나도 비지 않은** 초안 3건 |
| 결함 보고 | `has_falsifier = 0` 목록이 나온다 |
| challenge 라우팅 | `falsifier_cited` 없는 제기는 **거부**. 있으면 타입별로 4경로 라우팅 |
| 문헌 경로 한계 | `resolvable_by: literature`에 대해 locator 존재/부재만 판정, 그 외 `unknown` |

### D · 갱신과 격리 — **주 1회 자동화는 연기**

> **결정: 주 1회 정리는 나중에 구현한다.** 그래서 무인 운전 2주는 인수 조건에서 빠진다.
>
> **다만 색인 갱신 자체는 연기할 수 없다.** BD `I-076`이 KB가 죽는 두 방식 중 하나로
> 지목한 것이 정확히 *"색인이 상해서 파일은 다 있는데 검색이 안 되는 상태"*이고,
> [PLAN.md](PLAN.md) §1.2에서 그 초기 증상이 **이미 관측**되었다. 스케줄러를 연기하는
> 것은 **갱신 시점을 사람에게 옮기는 것**이고, 옮긴 만큼 방어를 대신 세워야 한다.

| 검사 | 통과 조건 |
|---|---|
| 명시적 재색인 | `librarian reindex` 한 명령으로 전량 재빌드. 증분 없음 |
| **부패 자기신고** | `manifest.json`의 SHA ≠ 현재 리포 SHA면 **모든 검색 응답이 `index_stale: true`를 싣는다** |
| 부패 차단 옵션 | `--strict`에서는 stale 색인이 검색을 **거부**한다 (기본값은 실패 — 철학 ①) |
| Tier 2 격리 | LLM 산출물이 `inbox/` 밖으로 나가는 경로가 없음 |
| publish-gate | 미발표 내용을 공개 경로에 쓰려는 시도가 차단됨을 테스트로 증명 |

**`index_stale` 플래그가 스케줄러의 대체물이다.** cron은 *갱신을 잊지 않게* 하고,
이 플래그는 *잊었다는 사실을 숨기지 않게* 한다. 둘 중 하나는 있어야 하고, 후자가
구현 비용이 낮으면서 실패를 조용하지 않게 만든다.

`export/` 도달 검사는 Step 3으로 이동한다 — 배선 자체가 Step 3이므로 Step 0의
인수 조건이 될 수 없다.

### E · 이관 개시 조건

**A·B·C·D 전부 통과 + 끊긴 참조 CI 검사 가동** ([MIGRATION.md](MIGRATION.md) Step 2).

마지막 항목이 A–D에 없는 이유: 그 검사는 Librarian이 아니라 **BD·MS 리포에** 들어간다.
Librarian이 혼자 통과해도 두 리포에 방어가 없으면 §1의 조용한 실패가 이관 중에 발생한다.

---

## 5. 순서 정리

```
Step 0  구축 + 픽스처 검증        ← 이 문서
          A 구조 → B 검색 → C 왕복 → D 갱신·격리 → E 준비완료
          (주 1회 자동화는 Step 0 밖. 나중에)
Step 1  흡수 (두 쪽 다 살아 있음)   MIGRATION.md
Step 2  참조 갱신 (실제 작업량)
Step 3  export/ 배선
Step 4  동등성 증명
Step 5  삭제
```

**Step 0에서 원본 리포는 한 글자도 바뀌지 않는다.** 픽스처는 복사이고, `export/` 배선은
Step 3이다. 그래서 Step 0 전체가 되돌릴 수 있다 — `Librarian_agent/`를 지우면 끝이다.

---

## 6. 결정이 필요한 것

| # | 결정 | 권고 | 근거 |
|---|---|---|---|
| 1 | 토크나이저 | **`trigram` + 2글자 LIKE 폴백** | §3 실측. 스키마 생성 전에 정해야 함 |
| 2 | 형태소 분석기 | **안 씀** | 재현성 > 랭킹 품질 (BD `I-052`) |
| 3 | 픽스처 8건으로 충분한가 | 주장 1개 = 픽스처 1개 원칙 유지 | 설계 문서에 주장이 추가되면 픽스처도 추가 |
| 4 | ~~Tier 1 무인 운전 기간~~ | **연기** — 주 1회 자동화는 나중 | 대신 `index_stale` 자기신고가 필수 (§4-D) |
| 5 | 픽스처 폐기 시점 | Step 1 시작 시 | 남기면 같은 엔트리가 두 곳에 |
