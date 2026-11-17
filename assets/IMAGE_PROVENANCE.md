# 설명 그림 생성과 검토

생성일: 2026-11-17 KST. 사용자 요청에 따라 내장 image_gen 도구를 사용했다. CLI/API fallback은 사용하지 않았다.

| 최종 그림 | 최초 프롬프트 | 수정 프롬프트 | 검토 범위 |
| --- | --- | --- | --- |
| [architecture.png](architecture.png) | [architecture.txt](prompts/architecture.txt) | [architecture-review.txt](prompts/architecture-review.txt) | 12개 스킬은 총괄 개발 영역에만 표기. 제안 실행 모듈, 물리 조작과 센서 피드백, 센서 배치 미정 표시 확인 |
| [ros2-topology.png](ros2-topology.png) | [ros2-topology.txt](prompts/ros2-topology.txt) | 없음 | HDU/MDU/ADU 역할, ROS 2 Topic/HTTP JSON RPC 구분, AimRT 내부 모듈, 팔 Topic 이름 대조 |
| [joint-overview.png](joint-overview.png) | [joint-overview.txt](prompts/joint-overview.txt) | [joint-overview-review.txt](prompts/joint-overview-review.txt) | 몸체 31, 손 32, 회전 63, mimic 12, 비-mimic 변수 51을 추출 JSON과 대조. 색상 범례를 정확한 joint 위치가 아닌 부위 설명으로 수정 |

관절 그림에는 기존 A3 Ultra 모델 미리보기를 외형 참고로 사용했다. 원본 미리보기나 사용자가 제공한 조종기 사진/도면 자체는 이 묶음에 복제하지 않았다. 조종기 외형 설명과 조건은 README에서 사용자 제공 자료와 미확인 사양으로 구분한다.

세 그림은 설명용 개략도다. 실제 ROS 노드 그래프, 실장비 배치, 기구 회전축, 액추에이터 수 또는 안전 인증의 증거가 아니다. 정확한 이름과 수치의 기준은 [아키텍처 근거](../references/architecture.md), [관절 근거](../references/joint-model.md), [추출 JSON](../references/joints.json)이다.
