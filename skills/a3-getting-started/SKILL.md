---
name: a3-getting-started
description: A3 Ultra 개발을 처음 시작할 때 보드 역할, ROS 2와 RPC, 개발 환경, 첫 상태 조회를 공식 문서의 해당 절과 연결해 설명한다.
---

# A3 Ultra 처음 시작하기

검토용 초안이다. A3 Ultra 3.3.x 문서를 기준으로 학습과 첫 개발 과정을 안내한다. 이 스킬 자체가 로봇에 연결되거나 상시 실행 프로그램을 제공하지는 않는다.

설치 경로가 심볼릭 링크이면 먼저 `SKILL.md`의 실제 경로(realpath)를 확인하고 모든 상대 참조와 명령 경로를 실제 경로 기준으로 해석한다.

## 시작점

- 사람용 탐색 화면: [HTML 목차](../../index.html)
- 공통 출처: [문서와 인터페이스 색인](../../catalog.json)
- 버전 경계와 문서 불일치: [확인 사항](../../references/guide-notes.md)

## 안내 순서

1. 사용자가 배우려는 기능과 현재 확보한 자료를 확인한다. 로봇 실물, 설치 버전, SDK, 시뮬레이션 자산을 구분한다. 제품 문서나 모델 파일만으로 장비 접속과 실행 준비가 끝났다고 판단하지 않는다.
2. 해당 작업에 필요한 개념만 설명한다. MDU는 운동 제어, HDU는 상호작용과 외부 네트워크, ADU는 AI 연산 역할로 문서에 소개되어 있다. 실제 설치 구성을 조사한 경우에만 장비 정보로 표시한다.
3. ROS 2 Topic은 메시지를 발행/구독하는 통신, HTTP JSON RPC는 요청과 응답으로 기능을 호출하는 통신이라고 설명한다. 정확한 인터페이스 이름은 색인과 원문에서 찾는다.
4. 관련 H1/H2/H3 절, SDK 예제, 필요한 환경 순으로 연결한다. 한 단계마다 무엇을 확인하면 완료인지 설명한다. 조회 예제와 동작 예제를 명확히 구분하고, 현재 요청의 범위에 맞는 예제를 선택한다.
5. SDK나 장비를 다룰 때는 문서 버전과 실제 버전, 실행 대상 보드, 통신 환경을 대조한다. 사용자가 승인한 개발/실행 범위와 기존 프로젝트 절차를 유지한다.

## 학습 경로

| 질문 | 바로 읽을 공식 절 |
| --- | --- |
| 세 보드가 무엇을 하는가 | [1.6 Industrial PC Specifications](https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/01-a3_overview#16-industrial-pc-specifications) |
| 어떤 방식으로 호출하는가 | [3.1 HTTP JSON RPC](https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/03-second_develop_interface_overview#31-http-json-rpc), [3.2 ROS2 Topic](https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/03-second_develop_interface_overview#32-ros2-topic) |
| 개발 시 지켜야 할 장비 제약은 무엇인가 | [4. Basic Constraints](https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/04-second_develop_constraints_overview#4-basic-constraints-for-secondary-development) |
| 개발 환경을 준비하려면 | [5.1 Development Tools and Installation](https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/05-second_develop_program_deployment#51-development-tools-and-installation) |
| 처음 상태를 읽으려면 | [6.3 Upper Limb Joint State](https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/06-second_develop_quick_start#63-example-get-robot-upper-limb-joint-state) |
| 유선 ROS 2 연결을 확인하려면 | [6.6 Wired Communication](https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/06-second_develop_quick_start#66-ros2-communication-over-a-wired-connection) |

## 전달할 결과

현재 단계, 필요한 개념, 정확한 원문 절, 실행했다면 관측한 결과, 다음 확인 한 가지를 한국어로 정리한다. 명령을 제시할 때는 실행 위치와 대상 보드, 기대 결과를 함께 적는다. 문서만 읽었다면 연결/실행 검증은 하지 않았다고 명시한다.

관련 공개 코드가 필요하면 [확인 사항의 GitHub 경로](../../references/guide-notes.md#관련-github)를 따른다. 예제 파일이 SDK 안에만 있으면 실제 SDK 상대 경로를 표시하고, 존재하지 않는 GitHub URL을 만들지 않는다.
