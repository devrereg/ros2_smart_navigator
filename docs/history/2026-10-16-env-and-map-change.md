# 2026-10-16 — 환경 확인 및 맵 변경, 문서 정비 (A)

**브랜치 / 이슈:** `1-ryubengock` / [#1](https://github.com/devrereg/ros2_smart_navigator/issues/1)

## 한 일

1. **`.gitignore` 정리** — `build/`, `install/`, `log/` (colcon 빌드 산출물) 제외.
2. **문서 갱신**
   - `docs/plans.md`, `docs/environment.md`, `docs/test_plan.md`, `README.md`: 맵을 TurtleBot3 기본 월드로 변경, 실행 명령 교체, 맵 변경 기록 추가.
   - `docs/environment.md`: `ros2 --version`을 `ros2 doctor --report`로 변경, A 환경 값 기록.
   - `docs/interfaces.md`, `docs/plans.md`: `/cmd_vel`을 `TwistStamped`로 확정, `/scan`·`/cmd_vel`의 QoS 기록.
   - `docs/getting_started.md`: 신규 팀원용 설치·실행 가이드 신규 작성.
   - `docs/branching.md`, `README.md`, `docs/getting_started.md`: 브랜치명을 `{이슈번호}-{닉네임}`으로 통일하고, `integration` 브랜치를 건너뛰고 `main`으로 바로 PR을 보내도록 수정.
   - `README.md`: 시작 가이드와 작업 히스토리 링크 추가.
   - `docs/history/`: 작업 히스토리 디렉토리 (처음에는 `docs/history.md` 단일 파일이었으나 날짜별 파일로 분리).

## 결정 사항과 이유

| 결정 | 이유 |
|---|---|
| Robotnik 월드 대신 TurtleBot3 기본 월드 사용 | `robotnik_lab_world`가 ROS 1 코드라 Jazzy + Harmonic에서 빌드 불가. Jazzy용으로 변환된 월드는 `electrical_substation_world` 하나뿐이다. |
| 브랜치명은 `{이슈번호}-{닉네임}` | 이슈 번호로 작업과 브랜치를 연결하기 위해. 작업 종류는 브랜치가 아니라 이슈 제목·내용으로 구분한다. |
| `integration` 브랜치는 당분간 건너뛰고 `main`으로 PR | 현재 팀 규모와 작업량에서는 별도 통합 브랜치가 과하다. 필요해지면 `docs/branching.md`의 보류된 절차로 전환한다. |
| 이후 자체 제작 맵으로 전환 | 팀원과 상의해 정함. 담당과 일정은 미정. |

## 이 시점의 미커밋 변경

`.gitignore`, `README.md`, `docs/environment.md`, `docs/interfaces.md`, `docs/plans.md`, `docs/test_plan.md`, `docs/getting_started.md`, `docs/history/`.
