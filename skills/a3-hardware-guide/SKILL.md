---
name: a3-hardware-guide
description: A3 Ultra의 MDU/HDU/ADU, 네트워크, 센서, 전원과 확장 포트를 조사할 때 공식 하드웨어 절과 모델 저장소를 연결하고 문서 사양과 실제 장비 증거를 구분한다.
---

# A3 Ultra 하드웨어 가이드

검토용 초안이다. 보드와 센서의 역할, 물리 인터페이스, 관련 모델과 보정 자료를 찾는다. 문서상의 구성은 실물의 설치 상태나 배선 검증을 뜻하지 않는다.

설치 경로가 심볼릭 링크이면 먼저 `SKILL.md`의 실제 경로(realpath)를 확인하고 모든 상대 참조와 명령 경로를 실제 경로 기준으로 해석한다.

## 근거와 탐색 경로

- [HTML 목차](../../index.html), [공통 출처 색인](../../catalog.json)
- [버전, 문서 불일치, 관련 GitHub](../../references/guide-notes.md)

| 조사할 것 | 공식 문서의 해당 절 |
| --- | --- |
| 부품과 센서 배치 | [1.1 Component Description](https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/01-a3_overview#11-component-description), [1.4 Camera Field of View](https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/01-a3_overview#14-robot-camera-field-of-view) |
| 보드 구성과 내부 네트워크 | [1.6 Industrial PC Specifications](https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/01-a3_overview#16-industrial-pc-specifications), [1.5 Network Topology](https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/01-a3_overview#15-network-topology) |
| 외부 전원과 핀 정의 | [9장 Power Supply Interface](https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/09-hardware_development_guide#1-power-supply-interface), [Pin Definition](https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/09-hardware_development_guide#11-pin-definition) |
| 서비스함 USB와 RJ45 | [Service Compartment Interfaces](https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/09-hardware_development_guide#2-service-compartment-interfaces-service-breakout-interfaces) |
| 가슴 내부 카메라 연결 | [Camera Interfaces](https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/09-hardware_development_guide#3-camera-interfaces-inside-the-chest-compartment) |
| 네트워크 포트 | [Network Interfaces](https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/09-hardware_development_guide#4-network-interfaces) |
| 센서 데이터와 보정 자료 경로 | [7.6 Sensor Data](https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/07-06-sensor_data#76-sensor-data) |

## 조사 순서

1. 대상 보드, 센서 또는 포트와 사용 목적을 특정한다. 외형 사진, 문서 명칭, 장비 식별 정보, 소프트웨어 버전을 서로 대조한다.
2. 색인에서 해당 원문 절과 그림을 읽는다. 커넥터의 모양만으로 전압, 핀 배열, 데이터 지원 여부를 판단하지 않는다. 특히 서비스함 USB-C와 내부 USB-C는 각자의 절을 확인한다.
3. 전원 작업이면 핀 배열, 극성, 전압 범위, 연속/순간 전력 한도와 커넥터 사양을 함께 정리한다. 문서 수치의 적용 대상을 명시하고 실제 배선 검증과 구분한다.
4. 센서 작업이면 데이터 인터페이스, 좌표계, 내부/외부 보정, 타임스탬프와 동기화에 대한 근거를 찾는다. 경로가 문서에 있다는 사실과 실제 보정 파일이 존재한다는 사실을 구분한다. 확인되지 않은 정렬/동기화를 가정하지 않는다.
5. 로봇 모델을 사용할 때는 모델 변형, 관절 명칭과 순서, 단위, 좌표계, 파일 버전을 실제 장비와 대조한다. 시뮬레이션 모델이 있다는 사실을 물리 정확도의 증거로 쓰지 않는다.

## 전달할 결과

대상, 문서 사양, 현장 관측, 미확인 항목, 정확한 원문/모델 파일 링크를 제공한다. 사용자의 요청 범위에서 다음 확인 한 가지를 제안한다. 하드웨어 연결이나 보드 설정 변경이 요청되지 않았다면 조사 결과만 제공한다.

이 스킬은 핀이나 제어 인터페이스를 추측해 추가하지 않는다. 공식 9장에 없는 확장 포트는 지원 여부가 확인되지 않은 항목으로 기록하고, 다른 제품의 핀 정의를 대입하지 않는다.
