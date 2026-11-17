# A3 Ultra T3D0 관절 모델 근거

## 무엇을 확인했는가

이 문서는 로컬 파일을 원격 저장소의 확인한 Git 커밋과 바이트 단위로 대조하고, XML을 파싱해 얻은 **모델 구조**를 설명한다. 실기기 모터 수, 현재 손 종류, 캘리브레이션 또는 공개 API의 명령 차원을 검증한 자료는 아니다.

- 저장소: [AgibotTech/A3-A3U-robot-model](https://github.com/AgibotTech/A3-A3U-robot-model)
- 확인한 커밋: `589f508ff357447c610a3f3004419035ddc8f153`
- 대상: A3 Ultra T3D0. T2D5나 다른 손 옵션에 이 수치를 그대로 적용하지 않는다.
- [원본 URDF](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf), [planning URDF](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model_planning.urdf), [planning SRDF](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model_planning.srdf)
- [전체 관절 추출 JSON](joints.json): 모든 joint의 type, parent/child, origin, axis, limit, mimic, 원문 행 번호 포함.

## 관절 수와 자유도를 구분하기

| 항목 | model.urdf | model_planning.urdf |
| --- | ---: | ---: |
| link | 95 | 95 |
| joint 전체 | 94 | 94 |
| revolute joint | 63 | 31 |
| fixed joint | 31 | 63 |
| mimic 종속 joint | 12 | 0 |
| mimic이 없는 revolute 변수 | 51 | 31 |
| transmission 정의 | 0 | 0 |
| 루트 link | pelvis_link | pelvis_link |

원본의 63개 회전 joint는 **몸체 31개 + 손 16개씩 32개**다. 각 손의 16개 중 6개는 다른 관절을 따라 움직이는 mimic 종속 좌표이므로 손마다 10개의 비-mimic 회전 변수가 남는다. 이 모델의 비-mimic 회전 변수 수는 다음과 같다.

```text
몸체: 허리 3 + 머리 2 + 왼팔 7 + 오른팔 7 + 왼다리 6 + 오른다리 6 = 31
손:   (회전 16 - mimic 6) × 2 = 20
합계: 31 + 20 = 51개의 비-mimic 회전 변수
```

[공식 개요 1.2](https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/01-a3_overview#12-robot-specifications)의 active DOF 51이라는 수치와 일치한다. 그러나 **수치가 같다는 사실은 실물 구성과 API 차원이 검증됐다는 뜻이 아니다.** URDF에는 transmission 정의가 없어 이 파일만으로 실제 모터와 드라이버의 대응을 입증할 수 없다.

planning URDF에서는 원본의 손 회전 joint 32개를 fixed로 바꾸고 mimic 태그를 제거했다. 따라서 이 planning 모델을 그대로 사용하면 손가락 조작을 계획하는 모델이 되지 않는다. 두 파일 모두 world/free_joint 예제가 XML 주석 안에 있어 실제 파싱 대상이 아니다. 시뮬레이터의 floating base 좌표는 이 집계에 포함하지 않았다.

두 URDF의 기하학도 완전히 같지는 않다. 양쪽 ankle_pitch_joint의 origin y는 원본에서 0 m지만 planning 파일은 왼쪽 약 +0.0015 m, 오른쪽 약 -0.0015 m로 기록한다. z는 부동소수 표기 수준의 차이가 있다. 따라서 planning 파일을 손만 고정한 완전 동일 모델로 간주하지 않는다.

## 몸체와 손의 구조

```text
pelvis_link
├─ 허리: yaw → roll → pitch → torso_Link
│  ├─ 머리: yaw → ultra_head_pitch
│  ├─ 왼팔: shoulder pitch → roll → yaw → elbow → wrist roll → pitch → yaw
│  │  └─ 왼손: 회전 joint 16개, mimic 6개, 비-mimic 회전 변수 10개
│  └─ 오른팔: shoulder pitch → roll → yaw → elbow → wrist roll → pitch → yaw
│     └─ 오른손: 회전 joint 16개, mimic 6개, 비-mimic 회전 변수 10개
├─ 왼다리: hip pitch → roll → yaw → knee → ankle pitch → roll
└─ 오른다리: hip pitch → roll → yaw → knee → ankle pitch → roll
```

위 요약에서는 고정 센서, 외장, palm 부착과 fingertip link를 생략했다. 아래 전체 tree와 JSON에는 포함한다. 직렬 URDF 트리는 기구학 표현이며, 실제 발목/허리의 모터 기구가 직렬이라는 증거로 사용하지 않는다.

각 손의 분기와 mimic 관계는 다음과 같다. L/R 접두어는 각각 왼손/오른손이다. ABAD, MCP, PIP, DIP는 원본 파일의 관절 명칭을 그대로 사용했다.

| 손가락 분기 | revolute | mimic | 비-mimic revolute | 관계 |
| --- | ---: | ---: | ---: | --- |
| thumb | 5 | 2 | 3 | pip = 1.33 × mcp, dip = 1.3 × mcp |
| index | 3 | 1 | 2 | dip = 1.097 × pip |
| middle | 2 | 1 | 1 | abad는 fixed, dip = 1.097 × pip |
| ring | 3 | 1 | 2 | dip = 1.097 × pip |
| pinky | 3 | 1 | 2 | dip = 1.097 × pip |
| 한 손 합계 | 16 | 6 | 10 | 모든 mimic offset은 0 rad |

일반식은 `q_child = multiplier × q_target + offset`이다. 예를 들어 L_thumb_pip_joint는 자체 자유 변수를 추가하지 않고 L_thumb_mcp_joint를 따른다. [원본 mimic 정의](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L726)

## 좌표와 단위

- `origin xyz`는 parent link에서 joint 기준 좌표계로의 위치를 m로 기록한다. `origin rpy`는 rad다.
- `axis`는 joint 기준 좌표계에 표현한 무차원 회전축이다. 이름의 roll/pitch/yaw만 보고 세계 좌표계 축과 같다고 가정하지 않는다.
- revolute의 position lower/upper는 rad, velocity는 rad/s, effort는 N m다. fixed joint는 운동 자유도와 회전축이 없다.
- 여기의 limit는 **URDF에 선언된 값**이다. 실기기 또는 해당 API의 허용값, 동적 토크 한계, 열 한계와 같다고 간주하지 않는다.
- 표의 숫자는 소수점 6자리까지 표시하고, JSON에는 추출한 수치를 유지한다.

URDF joint와 limit의 의미는 [ROS 2 Jazzy URDF 튜토리얼](https://docs.ros.org/en/jazzy/Tutorials/Intermediate/URDF/Building-a-Movable-Robot-Model-with-URDF.html)에서 확인할 수 있다.

## 모델과 공개 제어 API의 대응

### 팔: 이름과 배열 순서 대조

[공식 7.1.5](https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/07-01-motion_control#715-arm-control-command-and-state-topic-interfaces)의 14개 관절 이름은 이 URDF의 팔 이름과 일치한다. 문서의 명령 배열은 왼팔 7개 다음 오른팔 7개이며, 양팔 손목 순서는 roll → pitch → yaw다.

```text
left_shoulder_pitch_joint
left_shoulder_roll_joint
left_shoulder_yaw_joint
left_elbow_joint
left_wrist_roll_joint
left_wrist_pitch_joint
left_wrist_yaw_joint
right_shoulder_pitch_joint
right_shoulder_roll_joint
right_shoulder_yaw_joint
right_elbow_joint
right_wrist_roll_joint
right_wrist_pitch_joint
right_wrist_yaw_joint
```

실제 상태 메시지의 name, 설치 버전, 영점과 좌표계 대응은 추가 확인해야 한다. URDF 전체 joint 순서를 그대로 명령 배열로 보내지 않는다.

### 목: 이름 불일치

| API 문서 | T3D0 URDF |
| --- | --- |
| head_yaw_joint | head_yaw_joint |
| head_pitch_joint | ultra_head_pitch_joint |

이름 차이는 원문에서 관측된 사실이며, alias 또는 자동 변환을 검증하지 않았다. [URDF](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L255), [공식 7.1.8](https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/07-01-motion_control#718-neck-control-command-and-state-topic-interfaces)

### 손: 좌표와 API 추상값을 구분

[공식 7.1.10](https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/07-01-motion_control#7110-finger-control-command-and-state-topic-interfaces)은 손 명령 position을 0~2000의 무차원 추상값으로, 상태 position을 0~4096으로 설명한다. AgiHand/O10Hand 종류와 상태 메시지의 frame_id/name을 확인하도록 안내하며 AgiHand 상태를 12 dimensions로 설명한다.

따라서 이 모델의 한 손 16개 회전좌표 또는 10개 비-mimic 변수와 API 배열의 차원을 직접 동일시하지 않는다. URDF rad와 API 무차원 값의 변환, 2000↔4096 선형 비례, 구동 관절 순서는 아직 검증되지 않았다. 실제 손 옵션과 프로토콜을 확인한 뒤 대응표를 만들어야 한다.

### 다리와 허리: 모델 존재가 공개 저수준 API를 뜻하지 않음

URDF에 다리 관절과 limit가 있어도 고수준 개발 가이드가 개별 다리 관절의 직접 제어를 제공한다는 뜻은 아니다. [7.1.4 보행 인터페이스](https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/07-01-motion_control#714-walking-control-command-topic-interface)는 보행 속도 배율을, [7.1.7 허리 인터페이스](https://open.agibot.com/docs/en/aimdk/a3-ultra/v3_3/dev_guide/07-01-motion_control#717-waist-posture-control-topic-interface)는 별도의 자세/높이 입력을 정의한다. RL 배포 경로의 제어 계약은 고수준 API와 별도로 확인해야 한다.

## planning SRDF에서 확인한 링크 불일치

planning SRDF의 링크 참조 568회 중 30회가 planning URDF에 없는 세 이름을 사용한다.

| SRDF 참조 이름 | 미존재 참조 수 | URDF에서 관측한 관련 이름 |
| --- | ---: | --- |
| head_pitch_Link | 19 | ultra_head_pitch_Link |
| left_hand_palm_Link | 5 | L_palm |
| right_hand_palm_Link | 6 | R_palm |

이 표의 관련 이름은 **검증된 치환표가 아니다.** 충돌 제외 규칙의 의도와 기하학을 검토하지 않고 자동 치환하면 다른 충돌 설정을 만들 수 있다. 원본은 수정하지 않았다. [SRDF 머리 참조](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model_planning.srdf#L8), [SRDF 손 참조](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model_planning.srdf#L71), [planning URDF 머리](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model_planning.urdf#L324), [planning URDF 왼손](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model_planning.urdf#L789), [planning URDF 오른손](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model_planning.urdf#L1589)

## 재현과 검증

다음 명령은 이 스킬 저장소의 최상위에서 실행한다. 모델 파일은 별도로 확보한 정확한 커밋의 파일을 지정한다. 스크립트는 네트워크, 시뮬레이터, 로봇에 접근하지 않는다.

```bash
python3 scripts/inspect_joint_model.py /path/to/a3_ultra_t3d0/urdf/model.urdf \
  --source-url https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf \
  --output references/joints.json
python3 -m unittest discover -s tests -p test_joint_model.py -v
```

| 파일 | SHA-256 |
| --- | --- |
| model.urdf | 726bb83e52a55b47c192142f711b2e1353d3d4c3efabfa6267e6b3ce6011f1eb |
| model_planning.urdf | cd7416e3653fd8462d6463b09c833909e13c1d52fc078e887c5aee5351fad83c |
| model_planning.srdf | 1c586515a84ea959e35b69e8718ef61865781db16c02b80c1ec10021332ca30e |

원본 세 파일은 확인한 커밋의 blob과 바이트 단위로 일치했다. XML tree의 단일 루트와 부모 관계, mimic 참조를 검사했고, 별도 Expat 집계로 관절 수를 대조했다. 파서 회귀시험은 주석 제외, 좌표/limit/mimic 보존, 미존재 링크, 미존재 mimic과 자기 참조, 연결되지 않은 순환을 확인한다.

MoveIt 로딩, 실제 모터 구조, ROS 실행, 손 명령 변환, 실물 관절 한계와 물리 정확도는 안 돌려 봤음.

## 전체 joint tree

<details>
<summary>95개 link와 94개 joint의 전체 연결 보기</summary>

R은 revolute, F는 fixed다. 각 줄은 joint → child link를 나타낸다. 센서/외장 고정 연결도 포함한다.

```text
pelvis_link
├─ waist_yaw_joint [R] → waist_yaw_Link
│  └─ waist_roll_joint [R] → waist_roll_Link
│     └─ waist_pitch_joint [R] → torso_Link
│        ├─ torso_shell_joint [F] → torso_shell_Link
│        ├─ imu_in_torso_joint [F] → imu_in_torso_Link
│        ├─ head_yaw_joint [R] → head_yaw_Link
│        │  ├─ ultra_head_pitch_joint [R] → ultra_head_pitch_Link
│        │  │  ├─ ultra_head_stereo_camera_joint [F] → ultra_head_stereo_camera_Link
│        │  │  ├─ ultra_head_fisheye_camera_left_joint [F] → ultra_head_fisheye_camera_left_Link
│        │  │  ├─ ultra_head_fisheye_camera_right_joint [F] → ultra_head_fisheye_camera_right_Link
│        │  │  └─ ultra_head_fisheye_camera_back_joint [F] → ultra_head_fisheye_camera_back_Link
│        │  └─ ultra_head_mid360_joint [F] → ultra_head_mid360_Link
│        ├─ left_shoulder_pitch_joint [R] → left_shoulder_pitch_Link
│        │  └─ left_shoulder_roll_joint [R] → left_shoulder_roll_Link
│        │     └─ left_shoulder_yaw_joint [R] → left_shoulder_yaw_Link
│        │        └─ left_elbow_joint [R] → left_elbow_Link
│        │           └─ left_wrist_roll_joint [R] → left_wrist_roll_Link
│        │              └─ left_wrist_pitch_joint [R] → left_wrist_pitch_Link
│        │                 └─ left_wrist_yaw_joint [R] → left_wrist_yaw_Link
│        │                    ├─ left_palm_joint [F] → left_palm_Link
│        │                    │  └─ L_palm_joint [F] → L_palm
│        │                    │     ├─ L_thumb_roll_joint [R] → L_thumb_roll_link
│        │                    │     │  └─ L_thumb_abad_joint [R] → L_thumb_abad_link
│        │                    │     │     └─ L_thumb_mcp_joint [R] → L_thumb_mcp_link
│        │                    │     │        └─ L_thumb_pip_joint [R; mimic L_thumb_mcp_joint] → L_thumb_pip_link
│        │                    │     │           └─ L_thumb_dip_joint [R; mimic L_thumb_mcp_joint] → L_thumb_dip_link
│        │                    │     │              └─ L_thumb_tip_joint [F] → L_thumb_tip
│        │                    │     ├─ L_index_abad_joint [R] → L_index_abad_link
│        │                    │     │  └─ L_index_pip_joint [R] → L_index_pip_link
│        │                    │     │     └─ L_index_dip_joint [R; mimic L_index_pip_joint] → L_index_dip_link
│        │                    │     │        └─ L_index_tip_joint [F] → L_index_tip
│        │                    │     ├─ L_middle_abad_joint [F] → L_middle_abad_link
│        │                    │     │  └─ L_middle_pip_joint [R] → L_middle_pip_link
│        │                    │     │     └─ L_middle_dip_joint [R; mimic L_middle_pip_joint] → L_middle_dip_link
│        │                    │     │        └─ L_middle_tip_joint [F] → L_middle_tip
│        │                    │     ├─ L_ring_abad_joint [R] → L_ring_abad_link
│        │                    │     │  └─ L_ring_pip_joint [R] → L_ring_pip_link
│        │                    │     │     └─ L_ring_dip_joint [R; mimic L_ring_pip_joint] → L_ring_dip_link
│        │                    │     │        └─ L_ring_tip_joint [F] → L_ring_tip
│        │                    │     └─ L_pinky_abad_joint [R] → L_pinky_abad_link
│        │                    │        └─ L_pinky_pip_joint [R] → L_pinky_pip_link
│        │                    │           └─ L_pinky_dip_joint [R; mimic L_pinky_pip_joint] → L_pinky_dip_link
│        │                    │              └─ L_pinky_tip_joint [F] → L_pinky_tip
│        │                    └─ left_hand_camera_joint [F] → left_hand_camera_Link
│        ├─ right_shoulder_pitch_joint [R] → right_shoulder_pitch_Link
│        │  └─ right_shoulder_roll_joint [R] → right_shoulder_roll_Link
│        │     └─ right_shoulder_yaw_joint [R] → right_shoulder_yaw_Link
│        │        └─ right_elbow_joint [R] → right_elbow_Link
│        │           └─ right_wrist_roll_joint [R] → right_wrist_roll_Link
│        │              └─ right_wrist_pitch_joint [R] → right_wrist_pitch_Link
│        │                 └─ right_wrist_yaw_joint [R] → right_wrist_yaw_Link
│        │                    ├─ right_palm_joint [F] → right_palm_Link
│        │                    │  └─ R_palm_joint [F] → R_palm
│        │                    │     ├─ R_thumb_roll_joint [R] → R_thumb_roll_link
│        │                    │     │  └─ R_thumb_abad_joint [R] → R_thumb_abad_link
│        │                    │     │     └─ R_thumb_mcp_joint [R] → R_thumb_mcp_link
│        │                    │     │        └─ R_thumb_pip_joint [R; mimic R_thumb_mcp_joint] → R_thumb_pip_link
│        │                    │     │           └─ R_thumb_dip_joint [R; mimic R_thumb_mcp_joint] → R_thumb_dip_link
│        │                    │     │              └─ R_thumb_tip_joint [F] → R_thumb_tip
│        │                    │     ├─ R_index_abad_joint [R] → R_index_abad_link
│        │                    │     │  └─ R_index_pip_joint [R] → R_index_pip_link
│        │                    │     │     └─ R_index_dip_joint [R; mimic R_index_pip_joint] → R_index_dip_link
│        │                    │     │        └─ R_index_tip_joint [F] → R_index_tip
│        │                    │     ├─ R_middle_abad_joint [F] → R_middle_abad_link
│        │                    │     │  └─ R_middle_pip_joint [R] → R_middle_pip_link
│        │                    │     │     └─ R_middle_dip_joint [R; mimic R_middle_pip_joint] → R_middle_dip_link
│        │                    │     │        └─ R_middle_tip_joint [F] → R_middle_tip
│        │                    │     ├─ R_ring_abad_joint [R] → R_ring_abad_link
│        │                    │     │  └─ R_ring_pip_joint [R] → R_ring_pip_link
│        │                    │     │     └─ R_ring_dip_joint [R; mimic R_ring_pip_joint] → R_ring_dip_link
│        │                    │     │        └─ R_ring_tip_joint [F] → R_ring_tip
│        │                    │     └─ R_pinky_abad_joint [R] → R_pinky_abad_link
│        │                    │        └─ R_pinky_pip_joint [R] → R_pinky_pip_link
│        │                    │           └─ R_pinky_dip_joint [R; mimic R_pinky_pip_joint] → R_pinky_dip_link
│        │                    │              └─ R_pinky_tip_joint [F] → R_pinky_tip
│        │                    └─ right_hand_camera_joint [F] → right_hand_camera_Link
│        ├─ D457_in_torso_joint [F] → D457_in_torso_Link
│        ├─ D415_in_torso_joint [F] → D415_in_torso_Link
│        └─ senyun_in_torso_joint [F] → senyun_in_torso_Link
├─ imu_in_pelvis_joint [F] → imu_in_pelvis_Link
├─ left_hip_pitch_joint [R] → left_hip_pitch_Link
│  └─ left_hip_roll_joint [R] → left_hip_roll_Link
│     └─ left_hip_yaw_joint [R] → left_hip_yaw_Link
│        └─ left_knee_joint [R] → left_knee_Link
│           ├─ left_knee_shell_joint [F] → left_knee_shell_Link
│           └─ left_ankle_pitch_joint [R] → left_ankle_pitch_Link
│              └─ left_ankle_roll_joint [R] → left_ankle_roll_Link
└─ right_hip_pitch_joint [R] → right_hip_pitch_Link
   └─ right_hip_roll_joint [R] → right_hip_roll_Link
      └─ right_hip_yaw_joint [R] → right_hip_yaw_Link
         └─ right_knee_joint [R] → right_knee_Link
            ├─ right_knee_shell_joint [F] → right_knee_shell_Link
            └─ right_ankle_pitch_joint [R] → right_ankle_pitch_Link
               └─ right_ankle_roll_joint [R] → right_ankle_roll_Link
```

</details>

## 회전 관절 limit 전체 표

<details>
<summary>모델에 선언된 63개 회전 joint의 limit 보기</summary>

이 값으로 실기기 명령 허용 범위를 정하지 않는다. 각 source 링크는 해당 URDF joint 정의를 가리킨다.

| Joint / 원문 | axis (joint frame) | lower (rad) | upper (rad) | velocity (rad/s) | effort (N m) | mimic target |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| [waist_yaw_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L85) | 0 0 1 | -2.617994 | 2.617994 | 12.042772 | 220.000000 | 없음 |
| [waist_roll_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L114) | 1 0 0 | -0.349066 | 0.349066 | 22.700000 | 46.000000 | 없음 |
| [waist_pitch_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L143) | 0 1 0 | -0.488692 | 0.418879 | 9.247850 | 118.000000 | 없음 |
| [head_yaw_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L226) | 0 0 1 | -1.047198 | 1.047198 | 12.775810 | 6.000000 | 없음 |
| [ultra_head_pitch_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L255) | 0 1 0 | -0.436332 | 0.261799 | 12.775810 | 6.000000 | 없음 |
| [left_shoulder_pitch_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L419) | 0 1 0 | -2.879793 | 2.879793 | 13.613568 | 60.000000 | 없음 |
| [left_shoulder_roll_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L448) | 1 0 0 | -0.087266 | 2.617994 | 13.613568 | 60.000000 | 없음 |
| [left_shoulder_yaw_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L477) | 0 0 1 | -2.792527 | 2.792527 | 15.707963 | 24.000000 | 없음 |
| [left_elbow_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L506) | 0 1 0 | -0.959931 | 1.745329 | 15.707963 | 24.000000 | 없음 |
| [left_wrist_roll_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L535) | 1 0 0 | -2.792527 | 2.792527 | 15.707963 | 24.000000 | 없음 |
| [left_wrist_pitch_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L564) | 0 1 0 | -1.623156 | 1.623156 | 12.775810 | 6.000000 | 없음 |
| [left_wrist_yaw_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L593) | 0 0 1 | -1.623156 | 1.623156 | 12.775810 | 6.000000 | 없음 |
| [L_thumb_roll_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L654) | 1 0 0 | -1.121374 | 0.029671 | 8.729000 | 0.784000 | 없음 |
| [L_thumb_abad_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L676) | 0 0 1 | -0.045379 | 1.642355 | 11.636000 | 0.588000 | 없음 |
| [L_thumb_mcp_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L698) | 1 0 0 | -0.841598 | 0.000000 | 3.879000 | 1.764000 | 없음 |
| [L_thumb_pip_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L726) | 1 0 0 | -1.134464 | 0.000000 | 3.879000 | 1.764000 | L_thumb_mcp_joint |
| [L_thumb_dip_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L755) | 1 0 0 | -1.134464 | 0.000000 | 3.879000 | 1.764000 | L_thumb_mcp_joint |
| [L_index_abad_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L798) | 1 0 0 | 0.000000 | 0.164061 | 2.204000 | 1.863000 | 없음 |
| [L_index_pip_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L820) | 0 1 0 | 0.000000 | 1.483530 | 3.879000 | 1.764000 | 없음 |
| [L_index_dip_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L847) | 0 1 0 | 0.000000 | 1.754056 | 3.879000 | 1.764000 | L_index_pip_joint |
| [L_middle_pip_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L910) | 0 1 0 | 0.000000 | 1.483530 | 3.879000 | 1.764000 | 없음 |
| [L_middle_dip_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L937) | 0 1 0 | 0.000000 | 1.754056 | 3.879000 | 1.764000 | L_middle_pip_joint |
| [L_ring_abad_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L981) | 1 0 0 | -0.169297 | 0.000000 | 1.484000 | 2.766000 | 없음 |
| [L_ring_pip_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L1003) | 0 1 0 | 0.000000 | 1.483530 | 3.879000 | 1.764000 | 없음 |
| [L_ring_dip_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L1030) | 0 1 0 | 0.000000 | 1.754056 | 3.879000 | 1.764000 | L_ring_pip_joint |
| [L_pinky_abad_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L1072) | 1 0 0 | -0.185005 | 0.000000 | 1.210000 | 3.393000 | 없음 |
| [L_pinky_pip_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L1095) | 0 1 0 | 0.000000 | 1.483530 | 3.879000 | 1.764000 | 없음 |
| [L_pinky_dip_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L1122) | 0 1 0 | 0.000000 | 1.754056 | 3.879000 | 1.764000 | L_pinky_pip_joint |
| [right_shoulder_pitch_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L1220) | 0 1 0 | -2.879793 | 2.879793 | 13.613568 | 60.000000 | 없음 |
| [right_shoulder_roll_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L1249) | 1 0 0 | -2.617994 | 0.087266 | 13.613568 | 60.000000 | 없음 |
| [right_shoulder_yaw_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L1278) | 0 0 1 | -2.792527 | 2.792527 | 15.707963 | 24.000000 | 없음 |
| [right_elbow_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L1307) | 0 1 0 | -0.959931 | 1.745329 | 15.707963 | 24.000000 | 없음 |
| [right_wrist_roll_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L1336) | 1 0 0 | -2.792527 | 2.792527 | 15.707963 | 24.000000 | 없음 |
| [right_wrist_pitch_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L1365) | 0 1 0 | -1.623156 | 1.623156 | 12.775810 | 6.000000 | 없음 |
| [right_wrist_yaw_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L1394) | 0 0 1 | -1.623156 | 1.623156 | 12.775810 | 6.000000 | 없음 |
| [R_thumb_roll_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L1451) | 1 0 0 | -0.029671 | 1.121374 | 8.729000 | 0.784000 | 없음 |
| [R_thumb_abad_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L1473) | 0 0 1 | -1.642355 | 0.045379 | 11.636000 | 0.588000 | 없음 |
| [R_thumb_mcp_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L1494) | 1 0 0 | 0.000000 | 0.841598 | 3.879000 | 1.764000 | 없음 |
| [R_thumb_pip_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L1521) | 1 0 0 | 0.000000 | 1.134464 | 3.879000 | 1.764000 | R_thumb_mcp_joint |
| [R_thumb_dip_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L1549) | 1 0 0 | 0.000000 | 1.134464 | 3.879000 | 1.764000 | R_thumb_mcp_joint |
| [R_index_abad_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L1592) | 1 0 0 | -0.164061 | 0.000000 | 2.204000 | 1.863000 | 없음 |
| [R_index_pip_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L1615) | 0 1 0 | 0.000000 | 1.483530 | 3.879000 | 1.764000 | 없음 |
| [R_index_dip_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L1642) | 0 1 0 | 0.000000 | 1.754056 | 3.879000 | 1.764000 | R_index_pip_joint |
| [R_middle_pip_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L1705) | 0 1 0 | 0.000000 | 1.483530 | 3.879000 | 1.764000 | 없음 |
| [R_middle_dip_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L1732) | 0 1 0 | 0.000000 | 1.754056 | 3.879000 | 1.764000 | R_middle_pip_joint |
| [R_ring_abad_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L1774) | 1 0 0 | 0.000000 | 0.169297 | 1.484000 | 2.766000 | 없음 |
| [R_ring_pip_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L1797) | 0 1 0 | 0.000000 | 1.483530 | 3.879000 | 1.764000 | 없음 |
| [R_ring_dip_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L1824) | 0 1 0 | 0.000000 | 1.754056 | 3.879000 | 1.764000 | R_ring_pip_joint |
| [R_pinky_abad_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L1866) | 1 0 0 | 0.000000 | 0.185005 | 1.210000 | 3.393000 | 없음 |
| [R_pinky_pip_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L1889) | 0 1 0 | 0.000000 | 1.483530 | 3.879000 | 1.764000 | 없음 |
| [R_pinky_dip_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L1916) | 0 1 0 | 0.000000 | 1.754056 | 3.879000 | 1.764000 | R_pinky_pip_joint |
| [left_hip_pitch_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L2125) | 0 1 0 | -2.513274 | 2.932153 | 12.042772 | 220.000000 | 없음 |
| [left_hip_roll_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L2154) | 1 0 0 | -0.523599 | 1.483530 | 12.042772 | 220.000000 | 없음 |
| [left_hip_yaw_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L2183) | 0 0 1 | -2.722714 | 2.722714 | 12.042772 | 220.000000 | 없음 |
| [left_knee_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L2212) | 0 1 0 | -0.122173 | 2.530727 | 14.660766 | 320.000000 | 없음 |
| [left_ankle_pitch_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L2268) | 0 1 0 | -0.907571 | 0.523599 | 10.800000 | 118.200000 | 없음 |
| [left_ankle_roll_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L2297) | 1 0 0 | -0.349066 | 0.349066 | 19.370000 | 54.750000 | 없음 |
| [right_hip_pitch_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L2326) | 0 1 0 | -2.513274 | 2.932153 | 12.042772 | 220.000000 | 없음 |
| [right_hip_roll_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L2355) | 1 0 0 | -1.483530 | 0.523599 | 12.042772 | 220.000000 | 없음 |
| [right_hip_yaw_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L2384) | 0 0 1 | -2.722714 | 2.722714 | 12.042772 | 220.000000 | 없음 |
| [right_knee_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L2413) | 0 1 0 | -0.122173 | 2.530727 | 14.660766 | 320.000000 | 없음 |
| [right_ankle_pitch_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L2469) | 0 1 0 | -0.907571 | 0.523599 | 10.800000 | 118.200000 | 없음 |
| [right_ankle_roll_joint](https://github.com/AgibotTech/A3-A3U-robot-model/blob/589f508ff357447c610a3f3004419035ddc8f153/a3_ultra_t3d0/urdf/model.urdf#L2498) | 1 0 0 | -0.349066 | 0.349066 | 19.370000 | 54.750000 | 없음 |

</details>
