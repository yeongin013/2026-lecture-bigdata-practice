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
| w04-stream | — | — | — | — |
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
| w04-stream | `w04-submit` | 예정 |
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
| 루트 공용 파일 | `README.md` `check.py` `Makefile` `Dockerfile` `requirements.txt` `.devcontainer/` — 주차별 파일이 아니고, 각 주차 README가 `python3 ../check.py wNN`을 실행하라고 하므로 남겨둔다 |
| w02 · w04 · w05 · w06 · w07 | 아직 시작하지 않아 트리에서 제외 |

빠진 주차의 원본은 지워진 것이 아니라 `upstream`에 그대로 있다. 시작할 때 가져온다:

```bash
git fetch upstream
git checkout upstream/main -- w04-stream
```

## 원본에서 바꾼 것

교수님이 준 파일 중 **채워 넣으라고 되어 있는 곳**(각 주차 `task*.py`의 스텁) 외에
내용을 손댄 것은 `.gitignore` 하나뿐이다. 그 외에는 아직 시작하지 않은 주차 폴더를
트리에서 뺀 것뿐이고, 그 파일들의 내용은 바꾸지 않았다.

**`.gitignore` — `*/out/` 무시 규칙 삭제**

원본은 학생 결과물인 `*/out/`을 추적하지 않는다. 제출용 레포에서는 `out/`이 곧 제출물이므로
추적 대상으로 바꿨다.

수정 금지 파일인 `bench.py`, 그리고 실행만 하면 되는 `task2_crossover.py`는 **원본 그대로다.**

## w03 측정에서 알게 된 것

`task2.md`는 `--sizes 4000,8000,16000`까지 밀어보라고 하는데, 세 사이즈 모두 에러 없이
실행되지만 비교 횟수가 전부 2,246,140으로 같다. `bench.build()`가 2,120개 문서를 고정으로
돌려주므로 `bench.build()[:n]`은 n > 2,120에서 아무것도 자르지 않는다. 즉 그 구간은 같은
코퍼스의 반복 측정이고, 제공된 `task2_crossover.py`의 경로로 측정 가능한 최대 코퍼스는
2,120개다. 자세한 건
`w03-lsh/out/curve.md`에 적어뒀다.
