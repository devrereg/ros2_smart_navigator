# 브랜치 전략 (Branching Strategy)

> 1일차 — A: 저장소 구조와 브랜치 규칙 정리

## 기본 원칙

- `main`: 항상 실행 가능한 안정 버전만 유지한다. 직접 커밋하지 않고 PR을 통해서만 병합한다.
- `integration`: 팀원들의 기능 브랜치를 모아 통합 테스트하는 브랜치. 매일 통합 실행을 확인한 뒤 문제가 없으면 `main`으로 병합한다.
- 기능 브랜치: `feature/<담당자>-<기능>` 형식으로 생성한다.

## 브랜치 네이밍 규칙

| 종류 | 형식 | 예시 |
|---|---|---|
| 기능 개발 | `feature/<담당자>-<설명>` | `feature/b-scan-subscriber`, `feature/c-cmd-vel-control` |
| 버그 수정 | `fix/<담당자>-<설명>` | `fix/c-cmdvel-type` |
| 실험/QoS | `experiment/<설명>` | `experiment/qos-reliability` |
| 문서 | `docs/<설명>` | `docs/architecture` |

## 커밋 메시지 규칙

`[담당자] 유형: 설명` 형식을 사용한다.

- 유형: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`
- 예: `[B] feat: /scan 구독 노드 기본 구현`

## PR 및 통합 절차

1. 기능 브랜치에서 작업 후 `integration` 브랜치로 PR을 생성한다.
2. A가 인터페이스 호환성과 통합 실행 여부를 확인한 뒤 머지한다.
3. 매일 통합 실행을 확인한다 (`plans.md` 6장 일일 체크리스트 참고).
4. `integration`이 안정화되면 주요 마일스톤(중간 시연, 최종 발표 전)에 `main`으로 병합한다.

## 리뷰 기준

- 인터페이스 변경(토픽명, 메시지 타입, QoS 등) 시 머지 전에 팀에 공유한다.
- 머지 전 해당 기능이 로컬 환경에서 정상 실행되는지 직접 확인한다.
