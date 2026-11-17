---
name: a3-interface-guide
description: A3 Ultra 기능을 구현할 때 ROS 2 Topic, HTTP JSON RPC, SDK 예제의 역할과 호출 조건을 비교하고 원문 절에 근거한 인터페이스 사용 흐름을 설명한다.
---

# A3 Ultra 인터페이스 가이드

검토용 초안이다. 기능을 구현하는 데 필요한 통신 방식과 호출 순서를 이해하도록 돕는다. 이름 검색이 목적이면 [ROS/API 검색 스킬](../a3-ros-interface-finder/SKILL.md)을 참고한다.

설치 경로가 심볼릭 링크이면 먼저 `SKILL.md`의 실제 경로(realpath)를 확인하고 모든 상대 참조와 명령 경로를 실제 경로 기준으로 해석한다.

## 사용할 자료

- [HTML 목차](../../index.html)와 [공통 색인](../../catalog.json)
- [버전과 불일치 확인 사항](../../references/guide-notes.md)
- [3. 인터페이스 개요](https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/03-second_develop_interface_overview#3-secondary-development-interface-overview)
- [7. 상세 인터페이스 문서](https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/07-00-detailed_interface#7-detailed-interface-documentation)

## 작업 순서

1. 목표를 상태 읽기, 명령 보내기, 응답 또는 완료 확인으로 나눈다. 검색 결과에서 각각에 해당하는 실제 인터페이스를 찾고 해당 절을 읽는다.
2. 전송 방식을 원문 그대로 구분한다. HTTP JSON RPC를 ROS service/topic으로 바꾸거나, 문서에 없는 일반적인 ROS 이름으로 대체하지 않는다.
3. 호출 계약을 정리한다. 정확한 이름, 메시지 타입 또는 메서드, 필드/단위, 발행과 구독의 주체, 대상 보드/호스트, 실행 모드, 기존 발행자, QoS, 권장 주기, 시간 제한과 해제 동작을 확인한다. 원문에 없는 값은 미확인으로 남긴다.
4. 코드나 명령 생성 전 SDK 정의와 예제 경로를 대조한다. 실행 대상이 연결되어 있고 확인이 요청 범위에 포함된다면 설치 버전과 실제 통신 그래프도 확인한다. 문서 내용과 장비 증거는 별도 표시한다.
5. 명령 접수, 상태 전환 완료, 실제 동작 결과를 나눠 검증한다. 예를 들어 상태 전환 호출의 응답만으로 전환이 완료됐다고 보고하지 않는다.

## 필요한 절만 읽기

| 상황 | 원문 절 |
| --- | --- |
| ROS 환경과 QoS | [3.2.1 환경 변수](https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/03-second_develop_interface_overview#321-environment-variable-setup), [3.2.2 QoS](https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/03-second_develop_interface_overview#322-qos-settings) |
| 모션 상태와 제어권 | [7.1.1 Overview](https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/07-01-motion_control#711-overview) |
| 상태 전환과 완료 조회 | [7.1.2 State Machine Switching and Query](https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/07-01-motion_control#712-state-machine-switching-and-query-rpc-interfaces) |
| 팔 위치 명령과 피드백 | [7.1.5 Arm Command and State](https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/07-01-motion_control#715-arm-control-command-and-state-topic-interfaces) |
| 팔 Kp/Kd 설정 | [7.1.6 Configurable Kp/Kd](https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/07-01-motion_control#716-arm-control-command-configurable-kpkd) |
| SDK 코드 구조 | [5.4 SDK Dependency Description](https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/05-second_develop_program_deployment#54-sdk-dependency-description), [5.7 Python Packaging](https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/05-second_develop_program_deployment#57-python-packaging-and-deployment) |

## 전달할 결과

요청 기능에서 각 인터페이스가 맡는 역할을 짧게 설명하고, 호출 계약과 근거 링크를 표로 제공한다. 기능 명세로부터 개발 흐름도를 요청받았다면 확인된 인터페이스만 사용하고, 해결되지 않은 경계는 흐름도에 표시한다. 이 스킬이 사용자의 승인 범위나 크레인 운영 정책을 새로 결정하지 않는다.

색인 검색은 읽기 전용이다. 검색을 위해 로봇 상태를 바꾸거나, 개인 로그와 자격 증명을 외부 검색 서비스로 보내지 않는다.
