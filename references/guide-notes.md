# A3 Ultra 가이드 확인 사항

이 자료는 네 종류의 스킬 초안이 공유하는 출처 안내다. 공식 페이지 내용과 헤더 주소는 2026-11-17에 확인했다. 실제 A3 Ultra의 접속, 설치 버전, ROS 그래프, 배선과 동작은 검증하지 않았다.

## 버전과 증거 구분

- 공식 가이드의 적용 범위는 A3 Ultra 소프트웨어 3.3.x다. 다른 제품이나 버전의 인터페이스를 같은 것으로 취급하지 않는다. [V3.3 적용 범위](https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/)
- `catalog.json`은 공개 문서의 식별자와 절 주소를 찾는 색인이다. 원문 검토, SDK 정의 대조, 장비 조회, 실행 관측은 각각 별도 증거로 표시한다.
- 링크는 실제 헤더 `id`가 있는 경우 해당 주소를 사용한다. 헤더에 `id`가 없으면 페이지 주소와 절 제목을 제공한다. 없는 앵커를 만들어내지 않는다.
- SDK 예제 상대 경로만 알려진 경우 그 경로를 표시한다. GitHub에서 파일을 확인하지 못했다면 임의의 저장소 경로로 연결하지 않는다.

## 확인된 문서 불일치

| 항목 | 확인된 표기 | 처리 |
| --- | --- | --- |
| 보드와 내부 IP | 3절은 HDU를 `10.42.10.10`, MDU를 `10.42.10.12`, ADU를 `10.42.10.11`로 설명하지만 7장 개요는 앞의 두 보드 대응을 반대로 적는다. | URL의 호스트와 보드 이름을 별도 기록하고 실제 대상 보드는 설치 증거로 확인한다. [3.1](https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/03-second_develop_interface_overview#31-http-json-rpc), [7장 개요](https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/07-00-detailed_interface#7-detailed-interface-documentation) |
| 팔 compliance 조회 | 7.1.13의 인터페이스 이름은 `CheckArmCompliance`지만 URL 끝은 `DisableArmCompliance`다. | 조회 요청으로 실행하지 말고 정확한 경로를 SDK/장비 정의로 확인한다. 단순 문자열 치환을 검증으로 취급하지 않는다. [7.1.13](https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/07-01-motion_control#7113-check-arm-compliance) |
| MDU 개발 대상 | 4절은 MDU에 이차 개발 프로그램 배포를 금지한다. 5절 빌드 예제에는 `rk3588_mdu_aarch64` 대상이 있다. | 빌드 타깃의 존재를 MDU 배포 허용으로 해석하지 않는다. 적용 버전과 해당 개발 경로의 지원 범위를 확인한다. [4절](https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/04-second_develop_constraints_overview#4-basic-constraints-for-secondary-development), [5.6.1](https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/05-second_develop_program_deployment#561-build) |

## 환경과 하드웨어 경계

- 문서는 ROS 2 Jazzy/Fast DDS와 Topic 기본 QoS를 설명한다. 개별 Topic의 실제 QoS와 설치 환경은 장비에서 대조한다. [3.2 ROS2 Topic](https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/03-second_develop_interface_overview#32-ros2-topic)
- 4절은 온보드 시스템 의존성의 임의 변경과 `apt` 설치/제거를 금지하며 RPC 반복 호출 빈도를 제한한다. 개발 PC, 컨테이너, 로봇의 어느 환경을 변경하려는지 구분하고 해당 절을 읽는다. [4절 제약](https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/04-second_develop_constraints_overview#4-basic-constraints-for-secondary-development)
- 서비스함 USB-C는 공식 9장 2.3에서 리모컨 충전 전용으로 설명한다. 같은 커넥터 모양의 내부 포트와 기능을 혼동하지 않는다. 전원 수치와 핀 배열은 연결하려는 포트의 원문을 직접 확인한다. [서비스함 USB-C](https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/09-hardware_development_guide#23-usb-type-c), [외부 전원](https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/09-hardware_development_guide#1-power-supply-interface)
- 9장은 명시되지 않은 인터페이스가 기본적으로 이차 개발을 지원하지 않는다고 설명한다. 미기재 포트의 지원 여부를 추측하지 않는다. [하드웨어 가이드](https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/09-hardware_development_guide)

## 관련 GitHub

다음 공개 저장소의 존재와 기본 브랜치는 확인했지만, 이 초안에서 특정 모델 파일이나 실행 코드를 장비와 대조하지는 않았다. 파일 단위 근거는 [커밋이 고정된 관련 링크](related-links.json)를 사용한다. 검색 서비스의 캐시, 로컬 체크아웃, 현재 기본 브랜치의 내용은 서로 다를 수 있으므로 읽은 커밋과 파일 경로를 함께 표시한다.

| 저장소 | 사용할 때 |
| --- | --- |
| [AgibotTech/A3-A3U-robot-model](https://github.com/AgibotTech/A3-A3U-robot-model) | A3/A3 Ultra 로봇 모델과 변형별 관절, 기구 자료를 찾을 때. 실제 장비와 모델 변형을 확인한다. |
| [AgibotTech/sonic_for_a3](https://github.com/AgibotTech/sonic_for_a3) | 강화학습, 시뮬레이션과 전신 제어 공개 구현을 조사할 때. 고수준 AimDK API와 별도 개발 경로이며 실행 요건을 따로 검토한다. |

## 이번 초안의 경계

이 묶음은 초보자 설명, 인터페이스 이해, 하드웨어 자료 조사, 정확한 Topic/API 검색을 다룬다. 상시 에이전트 실행, 실제 크레인 조작, 센서 배치, 자동 복구 권한, 강화학습 배포 정책을 확정하지 않는다. 해당 사항은 사용자와의 후속 논의와 별도 검증이 필요하다.
