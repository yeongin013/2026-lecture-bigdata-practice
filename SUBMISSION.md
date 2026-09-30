# 제출 레포

고려대 세종 · 2026-2 빅데이터개론 실습 제출본.

원본은 교수님이 제공한 [`codingchild2424/2026-lecture-bigdata-practice`](https://github.com/codingchild2424/2026-lecture-bigdata-practice)
이고, 이 레포는 그 히스토리를 그대로 이어받아 내 구현과 측정 결과를 얹은 것이다.
원본은 `upstream` 리모트로 남아 있다.

```bash
git fetch upstream          # 원본이 갱신되면 받아올 수 있다
```

## 진행 상황

| 주차 | Task 1 구현 | Task 2 측정 | Task 3 개선 | 제출물 |
|---|---|---|---|---|
| w03-lsh | 완료 | 완료 | **strong** | `w03-lsh/out/` |
| w04-stream | 완료 | 완료 | **strong** | `w04-stream/out/` |
| w05-pagerank | — | — | — | — |
| w06-apriori | — | — | — | — |
| w07-kmeans | — | — | — | — |

선택 과제(w02, w05 task4, w06 task4)는 Spark이 필요하다. 이 노트북의 JDK는 23이라
그대로는 안 돌아가고, `make image` → `make shell`(Ubuntu 24.04 + JDK 17 + PySpark)로
컨테이너 안에서 돌려야 한다.

## 제출 주소

주차를 마칠 때마다 `wNN-submit` 태그를 찍고, **그 태그의 해당 주차 폴더 주소**를 제출한다.
태그는 고정된 스냅샷이므로 다음 주차를 올려도 이미 제출한 주소의 내용은 바뀌지 않는다.

| 주차 | 태그 | 제출 주소 |
|---|---|---|
| w03-lsh | `w03-submit` | https://github.com/yeongin013/2026-lecture-bigdata-practice/tree/w03-submit/w03-lsh |
| w04-stream | `w04-submit` | https://github.com/yeongin013/2026-lecture-bigdata-practice/tree/w04-submit/w04-stream |
| w05-pagerank | `w05-submit` | 예정 |
| w06-apriori | `w06-submit` | 예정 |
| w07-kmeans | `w07-submit` | 예정 |

새 주차를 제출할 때 쓰는 명령:

```bash
git add -A wNN-*                        # 그 주차의 코드와 out/
git commit -m "wNN-topic: 요약"
git tag -a wNN-submit -m "wNN 제출"
git push origin main wNN-submit
```

## 트리에 무엇이 있나

트리에는 **제출한 주차와 공용 파일만** 둔다. 아직 시작하지 않은 주차는 커밋하지 않는다 —
채워지지 않은 스텁이 트리에 있으면 제출물과 구분이 안 되기 때문이다.

| | |
|---|---|
| `w03-lsh/` | 제출 완료 |
| `w04-stream/` | 제출 완료 |
| 루트 공용 파일 | `README.md` `check.py` `Makefile` `Dockerfile` `requirements.txt` `.devcontainer/` — 주차별 파일이 아니고, 각 주차 README가 `python3 ../check.py wNN`을 실행하라고 하므로 남겨둔다 |
| w02 · w05 · w06 · w07 | 아직 시작하지 않아 트리에서 제외 |

빠진 주차의 원본은 지워진 것이 아니라 `upstream`에 그대로 있다. 시작할 때 가져온다:

```bash
git fetch upstream
git checkout upstream/main -- w05-pagerank
```

## 원본에서 바꾼 것

교수님이 준 파일 중 **채워 넣으라고 되어 있는 곳**(각 주차 `task*.py`의 스텁) 외에
내용을 손댄 것은 `.gitignore` 하나뿐이다. 그 외에는 아직 시작하지 않은 주차 폴더를
트리에서 뺀 것뿐이고, 그 파일들의 내용은 바꾸지 않았다.

**`.gitignore` — `*/out/` 무시 규칙 삭제**

원본은 학생 결과물인 `*/out/`을 추적하지 않는다. 제출용 레포에서는 `out/`이 곧 제출물이므로
추적 대상으로 바꿨다.

수정 금지 파일인 `bench.py`, 그리고 실행만 하면 되는 `task2_crossover.py`는 **원본 그대로다.**

새로 추가한 스크립트는 셋이고, 모두 제공 파일을 고치지 않고 추가 측정을 재현하기 위한 것이다.

| 파일 | 원자료 | 용도 |
|---|---|---|
| `w03-lsh/task2_extend.py` | `w03-lsh/out/crossover_ext.json` | 2,120개 천장 너머의 A2 |
| `w04-stream/task1_fm_rules.py` | `w04-stream/out/fm_rules.json` | FM 결합 규칙 40회 비교 |
| `w04-stream/task2_exact_only.py` | `w04-stream/out/limits_exact_only.json` | FM 없이 exact 만 잰 A2 두 점 |

커밋 기록 한 가지: `1477b98` 은 메시지가 ".gitignore" 뿐이지만, 실제로는 `w04-stream/` 의 원본
파일 9개를 upstream 에서 복원한 것도 함께 들어갔다. 복원된 내용은 upstream 과 바이트 단위로 같다.

## w03 측정에서 알게 된 것

`task2.md`는 `--sizes 4000,8000,16000`까지 밀어보라고 하는데, 세 사이즈 모두 에러 없이
실행되지만 비교 횟수가 전부 2,246,140으로 같다. `bench.build()`가 2,120개 문서를 고정으로
돌려주므로 `bench.build()[:n]`은 n > 2,120에서 아무것도 자르지 않는다. 즉 그 구간은 같은
코퍼스의 반복 측정이다.

그 너머는 `task2_extend.py`로 쟀다. `bench.build()` 뒤에 `bench.build(1)`, `bench.build(2)`, …를
이어 붙이고, 제공된 `task2_crossover.timed()`와 같은 `BruteForce`·`YourFinder`로 측정한다.
결과는 `w03-lsh/out/crossover_ext.json`에 따로 두어 `crossover.json`은 원본 스크립트의 출력만
담는다. brute force는 **n = 6,500에서 66.10초**로 1분을 넘었고, 그때 메모리는 59.2 KB였다 —
먼저 바닥난 건 시간이다. 자세한 건 `w03-lsh/out/curve.md`의 A2 절.

## w04 측정에서 알게 된 것

**§4.5.3 을 문자 그대로 읽은 결합 규칙이 40회 중 30%만 2배 안에 들었다.** 그룹 안에서
*평균*을 내기 때문이다 — 2^R 은 지수 분포라 8개짜리 그룹의 평균을 그 그룹의 최댓값이
거의 결정하고, 그러면 그룹 평균 8개가 전부 위로 끌려가 중앙값을 취해도 살아나지 않는다.
지수 R 을 먼저 평균한 뒤 지수화하는 쪽이 100%(중앙값 0.98)였고 그걸 썼다. 재현은
`task1_fm_rules.py`, 자세한 건 `w04-stream/out/observation.md`.

**베이스라인 `NaiveFilter` 는 선언한 메모리의 8배를 쓴다.** `bytearray(n_bits)` 는
n_bits *바이트*(= 640,000비트)인데 `memory_bits()` 는 80,000 을 돌려준다. Task 3 의 R3 이
"네 메모리를 전부 세라"고 못 박은 이유가 이것이고, 내 필터는 비트를 실제로 패킹해서
`len(bits) * 8 = 80,000` 이 진짜 값이다.

**A2 에 도달하기 위해 exact 만 따로 측정했다.** `flajolet_martin` 은 아이템당 63 µs 로
n 에 선형이라 n = 102.4M 이면 약 1.8시간이다. 그건 exact 의 한계가 아니라 내 FM 구현의
한계이고 A2 가 묻는 것은 exact 쪽이므로, 제공된 `task2_limits.exact_distinct()` 를 그대로
호출해 exact 만 두 점 더 쟀다(`task2_exact_only.py`, 원자료 `out/limits_exact_only.json`).
`task2_limits.py` 는 수정하지 않았고, 그래서 그 두 줄은 `limits.json` 에 없다.
