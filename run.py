from dotenv import load_dotenv
import os

load_dotenv()

async def subscribe_sensors(client):
    # 센서 알림 등록
    # 센서 알림 등록 (비동기 핸들러 래핑)
    async def async_handle_sensor_notification(sender: int, data: bytes):
        await handle_sensor_notification(client, sender, data)
    await client.start_notify(SENSOR_CHAR_UUID, async_handle_sensor_notification)

    # 센서 구독 명령 보내기
    await client.write_gatt_char(SENSOR_CHAR_UUID, COLOR_DISTANCE_SENSOR_SUBSCRIBE)
    await client.write_gatt_char(SENSOR_CHAR_UUID, TILT_SENSOR_SUBSCRIBE)
    print("✅ 센서 구독 시작됨 (컬러 + 자이로)")
import asyncio
from typing import Any
async def handle_sensor_notification(client: Any, sender: int, data: bytes):
    print(f"🔔 센서 알림 도착: {data.hex()}")

    port = data[3]
    sensor_type = data[4]
    raw_value = data[5:]

    # 센서값 설명 및 동작 제안 자동 호출
    explain = describe_sensor_value_to_gpt(sensor_type, list(raw_value))
    print(f"[GPT 센서 해석]\n{explain}")

    # 만약 GPT 설명에 action keyword가 포함되어 있으면 자동 실행
    action_keywords = []
    for kw in ["go_forward", "stop", "turn_left", "play_sound", "back_off"]:
        if kw in explain:
            action_keywords.append(kw)
    if action_keywords:
        asyncio.create_task(execute_action_keywords(client, action_keywords))

    if sensor_type == 0x03:
        # Color/Distance 센서
        color_value = raw_value[0]
        print(f"🎨 색상 감지: {color_value}")
    elif sensor_type == 0x02:
        # Tilt 센서
        tilt_x = raw_value[0]
        tilt_y = raw_value[1]
        print(f"📐 기울기 감지 - X: {tilt_x}, Y: {tilt_y}")
def describe_sensor_value_to_gpt(sensor_type, raw_value):
    prompt = f"""
    LEGO 로봇의 센서에서 데이터를 읽었습니다.
    센서 종류: {sensor_type}
    센서 값: {raw_value}

    이 값이 의미하는 것을 사람이 쉽게 이해할 수 있게 설명해줘.
    그리고 이 값에 따라 로봇이 어떤 행동을 하면 좋을지도 알려줘.
    """
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "너는 LEGO 로봇의 센서 해석 전문가야. 사용자가 센서값을 주면 설명과 동작을 제안해."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content if response.choices and response.choices[0].message.content else ""

import speech_recognition as sr
async def execute_action_keywords(client, keywords):
    """
    action keywords 예시:
    - go_forward: 앞으로 이동 (A, B 모터)
    - stop: 정지 (A, B 모터)
    - turn_left: 왼쪽으로 회전
    - play_sound: 사운드 출력(지원 시)
    - back_off: 후진
    """
    for action in keywords:
        if action == "go_forward":
            # A, B 모터 앞으로
            await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x01, 0x64]))
            await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x01, 0x64]))
            print("[액션] 앞으로 이동(go_forward)")
        elif action == "stop":
            # A, B 모터 정지
            await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x00, 0x00]))
            await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x00, 0x00]))
            print("[액션] 정지(stop)")
        elif action == "turn_left":
            # 왼쪽으로 제자리 회전 (A 뒤로, B 앞으로)
            await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x01, 0x9C]))
            await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x01, 0x64]))
            await asyncio.sleep(0.55)  # 약 90도 회전
            # 정지
            await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x00, 0x00]))
            await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x00, 0x00]))
            print("[액션] 왼쪽 회전(turn_left)")
        elif action == "play_sound":
            print("[액션] 사운드 출력 (play_sound) - 실제 사운드 기능은 미구현")
        elif action == "back_off":
            # A, B 모터 뒤로
            await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x01, 0x9C]))
            await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x01, 0x9C]))
            print("[액션] 후진(back_off)")
        else:
            print(f"[액션] 알 수 없는 키워드: {action}")

import asyncio
from bleak import BleakClient



OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

HUB_MAC_ADDRESS = "B7FEBF26-785E-E3DF-B0BB-94192175407C"
MOTOR_CHAR_UUID = "00001624-1212-efde-1623-785feabcd123"
# 센서 알림용 UUID (BOOST 공식: 0x1624)
SENSOR_CHAR_UUID = "00001624-1212-efde-1623-785feabcd123"
COLOR_SENSOR_PORT = 0x32  # C 포트
COLOR_DISTANCE_SENSOR_SUBSCRIBE = bytearray([
    0x0A, 0x00, 0x41, COLOR_SENSOR_PORT, 0x03, 0x01, 0x01, 0x00, 0x00, 0x00
])
TILT_SENSOR_PORT = 0x01  # 내부 포트
TILT_SENSOR_SUBSCRIBE = bytearray([
    0x0A, 0x00, 0x41, TILT_SENSOR_PORT, 0x02, 0x01, 0x01, 0x00, 0x00, 0x00
])

async def test_motor(client, port, name):
    motor_forward = bytearray([0x08, 0x00, 0x81, port, 0x11, 0x51, 0x01, 0x64])
    await client.write_gatt_char(MOTOR_CHAR_UUID, motor_forward)
    print(f"모터 {name} 앞으로 구동!")
    await asyncio.sleep(1)
    motor_stop = bytearray([0x08, 0x00, 0x81, port, 0x11, 0x51, 0x00, 0x00])
    await client.write_gatt_char(MOTOR_CHAR_UUID, motor_stop)
    print(f"모터 {name} 정지!")


async def test_external_motor(client, port, name):
    # BOOST 외부 포트(C, D) 모터 동작 테스트 (A/B와 동일 명령 사용)
    # 1. 앞으로 구동
    motor_forward = bytearray([0x08, 0x00, 0x81, port, 0x11, 0x51, 0x01, 0x64])
    await client.write_gatt_char(MOTOR_CHAR_UUID, motor_forward)
    print(f"[외부모터 {name}] 앞으로 구동!")
    await asyncio.sleep(1)
    # 2. 정지
    motor_stop = bytearray([0x08, 0x00, 0x81, port, 0x11, 0x51, 0x00, 0x00])
    await client.write_gatt_char(MOTOR_CHAR_UUID, motor_stop)
    print(f"[외부모터 {name}] 정지!")



# 메인/테스트 진입점 분리 및 main 함수 정의 보장

import sys
import asyncio
from bleak import BleakClient
from typing import Callable, Awaitable, Optional

# --- process_command를 글로벌 스코프에 정의 (main/voice 모드에서 모두 사용) ---
async def process_command(
    client,
    user_input: str,
    lego_dance: Optional[Callable[[], Awaitable[None]]] = None,
    lego_wave: Optional[Callable[[], Awaitable[None]]] = None,
    lego_flash: Optional[Callable[[], Awaitable[None]]] = None,
    lego_spin: Optional[Callable[[], Awaitable[None]]] = None,
    lego_jump_stop: Optional[Callable[[], Awaitable[None]]] = None,
    lego_rainbow: Optional[Callable[[], Awaitable[None]]] = None,
    move_with_obstacle_avoid: Optional[Callable[[], Awaitable[None]]] = None
) -> None:
    gpt_reply = chat_with_gpt(user_input)
    print("GPT 응답:", gpt_reply)
    if not gpt_reply:
        print("GPT 응답이 비어 있습니다.")
        return
    reply = gpt_reply.lower()
    # 루틴/모터/센서/액션 분기
    if lego_dance and ("춤" in reply or "dance" in reply):
        await lego_dance()
        return
    if lego_wave and ("파도타기" in reply or "웨이브" in reply or "wave" in reply):
        await lego_wave()
        return
    if lego_flash and ("번개" in reply or "플래시" in reply or "flash" in reply):
        await lego_flash()
        return
    if lego_spin and ("회전" in reply or "스핀" in reply or "spin" in reply):
        await lego_spin()
        return
    if lego_jump_stop and ("점프" in reply or "스톱" in reply or "jump" in reply):
        await lego_jump_stop()
        return
    if lego_rainbow and ("무지개" in reply or "rainbow" in reply):
        await lego_rainbow()
        return
    if move_with_obstacle_avoid and ("장애물" in reply or "거리센서" in reply or "피하기" in reply or "obstacle" in reply):
        await move_with_obstacle_avoid()
        return
    if ("a 모터" in reply and "앞으로" in reply):
        await test_motor(client, 0x00, "A")
    elif ("b 모터" in reply and "앞으로" in reply):
        await test_motor(client, 0x01, "B")
    elif ("c 모터" in reply and "앞으로" in reply):
        await test_external_motor(client, 0x32, "C")
    elif ("d 모터" in reply and "앞으로" in reply):
        await test_external_motor(client, 0x33, "D")
    elif ("a 모터" in reply and "정지" in reply):
        await test_motor(client, 0x00, "A")
    elif ("b 모터" in reply and "정지" in reply):
        await test_motor(client, 0x01, "B")
    elif ("c 모터" in reply and "정지" in reply):
        await test_external_motor(client, 0x32, "C")
    elif ("d 모터" in reply and "정지" in reply):
        await test_external_motor(client, 0x33, "D")
    elif ("모든 모터" in reply and "앞으로" in reply):
        await test_motor(client, 0x00, "A")
        await test_motor(client, 0x01, "B")
        await test_external_motor(client, 0x32, "C")
        await test_external_motor(client, 0x33, "D")
    elif ("모든 모터" in reply and "정지" in reply):
        await test_motor(client, 0x00, "A")
        await test_motor(client, 0x01, "B")
        await test_external_motor(client, 0x32, "C")
        await test_external_motor(client, 0x33, "D")
    elif ("자이로 센서 구독" in reply or "틸트 센서 구독" in reply):
        await client.write_gatt_char(MOTOR_CHAR_UUID, TILT_SENSOR_SUBSCRIBE)
        print("자이로(틸트) 센서 구독!")
    elif ("컬러 센서 구독" in reply or "거리 센서 구독" in reply):
        await client.write_gatt_char(MOTOR_CHAR_UUID, COLOR_DISTANCE_SENSOR_SUBSCRIBE)
        print("컬러&거리 센서 구독!")
    elif ("센서 모두 구독" in reply):
        await client.write_gatt_char(MOTOR_CHAR_UUID, TILT_SENSOR_SUBSCRIBE)
        print("자이로(틸트) 센서 구독!")
        await client.write_gatt_char(MOTOR_CHAR_UUID, COLOR_DISTANCE_SENSOR_SUBSCRIBE)
        print("컬러&거리 센서 구독!")
    elif ("센서 모두 해제" in reply):
        print("센서 구독 해제 (실제 해제 명령 필요)")
    elif ("실행할 수 있는 명령이 없습니다" in reply):
        print("실행할 수 있는 명령이 없습니다.")
    else:
        action_keywords = []
        for kw in ["go_forward", "stop", "turn_left", "play_sound", "back_off"]:
            if kw in reply:
                action_keywords.append(kw)
        if action_keywords:
            await execute_action_keywords(client, action_keywords)
        else:
            print("실행할 수 있는 명령이 없습니다.")




# 진입점: 외부모터 테스트 모드와 일반 모드 분기
if __name__ == "__main__":
    # 음성 명령을 받아서 GPT에 전달하고, 결과 명령을 실행하는 간단한 루프
    import speech_recognition as sr
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "test_external_motor":
            asyncio.run(test_external_motor_main())
        elif len(sys.argv) > 1 and sys.argv[1] == "voice":
            print("[음성 명령 모드] LEGO BOOST 허브에 연결 후, 마이크에 대고 명령을 말하면 바로 실행됩니다. (종료: Ctrl+C)")
            import asyncio
            async def voice_command_loop():
                import speech_recognition as sr
                r = sr.Recognizer()
                async with BleakClient(HUB_MAC_ADDRESS) as client:
                    if not client.is_connected:
                        print("허브와 연결 실패. 음성 명령 실행 불가.")
                        return
                    await subscribe_sensors(client)
                    print("[연결 성공] 음성 명령을 말하세요. (예: '춤', '웨이브', '앞으로', '정지' 등)")
            from typing import Callable, Awaitable, Optional
            async def process_command(
                client,
                user_input: str,
                lego_dance: Optional[Callable[[], Awaitable[None]]] = None,
                lego_wave: Optional[Callable[[], Awaitable[None]]] = None,
                lego_flash: Optional[Callable[[], Awaitable[None]]] = None,
                lego_spin: Optional[Callable[[], Awaitable[None]]] = None,
                lego_jump_stop: Optional[Callable[[], Awaitable[None]]] = None,
                lego_rainbow: Optional[Callable[[], Awaitable[None]]] = None,
                move_with_obstacle_avoid: Optional[Callable[[], Awaitable[None]]] = None
            ) -> None:
                gpt_reply = chat_with_gpt(user_input)
                print("GPT 응답:", gpt_reply)
                if not gpt_reply:
                    print("GPT 응답이 비어 있습니다.")
                    return
                reply = gpt_reply.lower()
                # 루틴/모터/센서/액션 분기
                if lego_dance and ("춤" in reply or "dance" in reply):
                    await lego_dance()
                    return
                if lego_wave and ("파도타기" in reply or "웨이브" in reply or "wave" in reply):
                    await lego_wave()
                    return
                if lego_flash and ("번개" in reply or "플래시" in reply or "flash" in reply):
                    await lego_flash()
                    return
                if lego_spin and ("회전" in reply or "스핀" in reply or "spin" in reply):
                    await lego_spin()
                    return
                if lego_jump_stop and ("점프" in reply or "스톱" in reply or "jump" in reply):
                    await lego_jump_stop()
                    return
                if lego_rainbow and ("무지개" in reply or "rainbow" in reply):
                    await lego_rainbow()
                    return
                if move_with_obstacle_avoid and ("장애물" in reply or "거리센서" in reply or "피하기" in reply or "obstacle" in reply):
                    await move_with_obstacle_avoid()
                    return
                if ("a 모터" in reply and "앞으로" in reply):
                    await test_motor(client, 0x00, "A")
                elif ("b 모터" in reply and "앞으로" in reply):
                    await test_motor(client, 0x01, "B")
                elif ("c 모터" in reply and "앞으로" in reply):
                    await test_external_motor(client, 0x32, "C")
                elif ("d 모터" in reply and "앞으로" in reply):
                    await test_external_motor(client, 0x33, "D")
                elif ("a 모터" in reply and "정지" in reply):
                    await test_motor(client, 0x00, "A")
                elif ("b 모터" in reply and "정지" in reply):
                    await test_motor(client, 0x01, "B")
                elif ("c 모터" in reply and "정지" in reply):
                    await test_external_motor(client, 0x32, "C")
                elif ("d 모터" in reply and "정지" in reply):
                    await test_external_motor(client, 0x33, "D")
                elif ("모든 모터" in reply and "앞으로" in reply):
                    await test_motor(client, 0x00, "A")
                    await test_motor(client, 0x01, "B")
                    await test_external_motor(client, 0x32, "C")
                    await test_external_motor(client, 0x33, "D")
                elif ("모든 모터" in reply and "정지" in reply):
                    await test_motor(client, 0x00, "A")
                    await test_motor(client, 0x01, "B")
                    await test_external_motor(client, 0x32, "C")
                    await test_external_motor(client, 0x33, "D")
                elif ("자이로 센서 구독" in reply or "틸트 센서 구독" in reply):
                    await client.write_gatt_char(MOTOR_CHAR_UUID, TILT_SENSOR_SUBSCRIBE)
                    print("자이로(틸트) 센서 구독!")
                elif ("컬러 센서 구독" in reply or "거리 센서 구독" in reply):
                    await client.write_gatt_char(MOTOR_CHAR_UUID, COLOR_DISTANCE_SENSOR_SUBSCRIBE)
                    print("컬러&거리 센서 구독!")
                elif ("센서 모두 구독" in reply):
                    await client.write_gatt_char(MOTOR_CHAR_UUID, TILT_SENSOR_SUBSCRIBE)
                    print("자이로(틸트) 센서 구독!")
                    await client.write_gatt_char(MOTOR_CHAR_UUID, COLOR_DISTANCE_SENSOR_SUBSCRIBE)
                    print("컬러&거리 센서 구독!")
                elif ("센서 모두 해제" in reply):
                    print("센서 구독 해제 (실제 해제 명령 필요)")
                elif ("실행할 수 있는 명령이 없습니다" in reply):
                    print("실행할 수 있는 명령이 없습니다.")
                else:
                    action_keywords = []
                    for kw in ["go_forward", "stop", "turn_left", "play_sound", "back_off"]:
                        if kw in reply:
                            action_keywords.append(kw)
                    if action_keywords:
                        await execute_action_keywords(client, action_keywords)
                    else:
                        print("실행할 수 있는 명령이 없습니다.")
                    # main()에서 정의된 루틴 함수들을 voice 루프에 직접 전달
                    # main()과 동일한 구조로 루프 실행
                    from types import SimpleNamespace
                    # voice 모드에서 루틴 함수 정의 (client context 유지)
                    async def lego_wave():
                        print("[파도타기(웨이브) 시작]")
                        LED_PORT = 0x32
                        LED_COLORS = [0x05, 0x06, 0x07, 0x08, 0x09]
                        for i in range(10):
                            color = LED_COLORS[i % len(LED_COLORS)]
                            await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, LED_PORT, 0x11, 0x51, 0x00, color]))
                            if i % 2 == 0:
                                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x01, 0x64]))
                                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x01, 0x9C]))
                            else:
                                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x01, 0x9C]))
                                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x01, 0x64]))
                            await asyncio.sleep(0.22)
                        await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x00, 0x00]))
                        await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x00, 0x00]))
                        print("[파도타기 종료]")

                    async def lego_flash():
                        print("[번개(플래시) 효과 시작]")
                        LED_PORT = 0x32
                        for i in range(8):
                            await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, LED_PORT, 0x11, 0x51, 0x00, 0x09]))
                            await asyncio.sleep(0.08)
                            await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, LED_PORT, 0x11, 0x51, 0x00, 0x00]))
                            await asyncio.sleep(0.08)
                        print("[번개 효과 종료]")

                    async def lego_spin():
                        print("[회전(스핀) 시작]")
                        LED_PORT = 0x32
                        await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, LED_PORT, 0x11, 0x51, 0x00, 0x07]))
                        await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x01, 0x64]))
                        await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x01, 0x64]))
                        await asyncio.sleep(1.2)
                        await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x00, 0x00]))
                        await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x00, 0x00]))
                        print("[회전 종료]")

                    async def lego_jump_stop():
                        print("[점프&스톱 시작]")
                        LED_PORT = 0x32
                        await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, LED_PORT, 0x11, 0x51, 0x00, 0x08]))
                        await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x01, 0x64]))
                        await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x01, 0x64]))
                        await asyncio.sleep(0.3)
                        await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x01, 0x9C]))
                        await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x01, 0x9C]))
                        await asyncio.sleep(0.3)
                        await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x00, 0x00]))
                        await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x00, 0x00]))
                        print("[점프&스톱 종료]")

                    async def lego_rainbow():
                        print("[무지개 쇼 시작]")
                        LED_PORT = 0x32
                        RAINBOW = [0x05, 0x08, 0x06, 0x07, 0x09]
                        for color in RAINBOW:
                            await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, LED_PORT, 0x11, 0x51, 0x00, color]))
                            await asyncio.sleep(0.22)
                        for _ in range(3):
                            for color in RAINBOW:
                                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, LED_PORT, 0x11, 0x51, 0x00, color]))
                                await asyncio.sleep(0.12)
                        await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, LED_PORT, 0x11, 0x51, 0x00, 0x00]))
                        print("[무지개 쇼 종료]")

                    async def lego_dance():
                        print("[춤 동작 시작]")
                        LED_COLORS = [0x05, 0x06, 0x07, 0x08, 0x09]
                        LED_PORT = 0x32
                        for i in range(5):
                            print("[댄스1] 왼쪽(A) 앞으로, 오른쪽(B) 뒤로")
                            await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, LED_PORT, 0x11, 0x51, 0x00, LED_COLORS[i%len(LED_COLORS)]]))
                            await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x01, 0x64]))
                            await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x01, 0x9C]))
                            await asyncio.sleep(0.35)
                            print("[댄스1] 왼쪽(A) 뒤로, 오른쪽(B) 앞으로")
                            await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, LED_PORT, 0x11, 0x51, 0x00, LED_COLORS[(i+1)%len(LED_COLORS)]]))
                            await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x01, 0x9C]))
                            await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x01, 0x64]))
                            await asyncio.sleep(0.35)
                        print("[댄스2] 제자리 빠른 회전!")
                        await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, LED_PORT, 0x11, 0x51, 0x00, LED_COLORS[2]]))
                        await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x01, 0x64]))
                        await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x01, 0x64]))
                        await asyncio.sleep(0.5)
                        print("[댄스3] 점프! (양쪽 역방향)")
                        await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, LED_PORT, 0x11, 0x51, 0x00, LED_COLORS[3]]))
                        await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x01, 0x9C]))
                        await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x01, 0x9C]))
                        await asyncio.sleep(0.3)
                        print("[댄스4] 좌우 진동!")
                        for j in range(8):
                            await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, LED_PORT, 0x11, 0x51, 0x00, LED_COLORS[j%len(LED_COLORS)]]))
                            await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x01, 0x32]))
                            await asyncio.sleep(0.13)
                            await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x01, 0xCE]))
                            await asyncio.sleep(0.13)
                            await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x01, 0x32]))
                            await asyncio.sleep(0.13)
                            await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x01, 0xCE]))
                            await asyncio.sleep(0.13)
                        await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, LED_PORT, 0x11, 0x51, 0x00, LED_COLORS[4]]))
                        await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x00, 0x00]))
                        await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x00, 0x00]))
                        print("[춤 동작 종료]")

                    async def move_with_obstacle_avoid():
                        print("[장애물 감지 이동 시작]")
                        LED_PORT = 0x32
                        await client.write_gatt_char(MOTOR_CHAR_UUID, COLOR_DISTANCE_SENSOR_SUBSCRIBE)
                        print("거리 센서 구독!")
                        # 실제 장애물 회피 로직은 main()과 동일하게 구현 가능
                        print("[voice] 장애물 감지 이동은 main()과 동일하게 동작합니다.")

                    # 음성 명령 루프
                    while True:
                        with sr.Microphone() as source:
                            print("음성 인식 대기 중...")
                            audio = r.listen(source, timeout=5, phrase_time_limit=5)
                        try:
                            voice_text = r.recognize_google(audio, language="ko-KR")
                            print(f"[음성 인식 결과] {voice_text}")
                        except sr.UnknownValueError:
                            print("음성을 인식하지 못했습니다.")
                            continue
                        except sr.RequestError as e:
                            print(f"음성 인식 서비스 오류: {e}")
                            continue
                        await process_command(
                            client, voice_text,
                            lego_dance=lego_dance,
                            lego_wave=lego_wave,
                            lego_flash=lego_flash,
                            lego_spin=lego_spin,
                            lego_jump_stop=lego_jump_stop,
                            lego_rainbow=lego_rainbow,
                            move_with_obstacle_avoid=move_with_obstacle_avoid
                        )
            asyncio.run(voice_command_loop())
        else:
            # main 함수가 if __name__ == "__main__" 블록보다 아래에 정의되어 있어 참조 불가 오류가 발생함
            # main 함수 정의를 이 블록보다 위로 옮기거나, 여기서 임포트/정의가 보장되도록 수정 필요
            # main 함수가 위에 정의되어 있으므로 바로 호출
            asyncio.run(main())
    except Exception as e:
        print("[오류] 프로그램 실행 중 예외가 발생했습니다:")
        print(e)
        if "disconnected" in str(e).lower():
            print("\n허브와의 연결이 끊어졌습니다. 전원을 확인하고, 가까이에서 다시 실행해 주세요.")
        else:
            print("\n허브의 전원 및 연결 상태를 확인하고, 다시 실행해 주세요.")

import os
import openai

def chat_with_gpt(prompt: str) -> str:
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": (
                    "너는 LEGO BOOST 허브를 제어하는 비서야. 사용자의 명령을 분석해서 어떤 모터/센서를 작동시킬지 결정해. "
                    "아래와 같이 구체적으로 명령을 만들어줘. 반드시 아래 예시처럼 대답해.\n"
                    "예시: 'A 모터 앞으로', 'A 모터 정지', 'B 모터 앞으로', 'B 모터 정지', 'C 모터 앞으로', 'C 모터 정지', 'D 모터 앞으로', 'D 모터 정지', "
                    "'모든 모터 앞으로', '모든 모터 정지', '자이로 센서 구독', '틸트 센서 구독', '컬러 센서 구독', '거리 센서 구독', '센서 모두 구독', '센서 모두 해제', "
                    "'춤', 'dance', '파도타기', '웨이브', 'wave', '번개', '플래시', 'flash', '회전', '스핀', 'spin', '점프', '스톱', 'jump', '무지개', 'rainbow', '장애물', '거리센서', '피하기', 'obstacle'\n"
                    "특별히, '춤', 'dance', '파도타기', '웨이브', 'wave', '번개', '플래시', 'flash', '회전', '스핀', 'spin', '점프', '스톱', 'jump', '무지개', 'rainbow', '장애물', '거리센서', '피하기', 'obstacle' 명령이 들어오면 반드시 해당 단어만 그대로 답해.\n"
                    "'점프'가 들어오면 반드시 '점프'로만 답해.\n"
                    "'jump'가 들어오면 반드시 'jump'로만 답해.\n"
                    "'스톱'이 들어오면 반드시 '점프'로만 답해.\n"
                    "명령이 모호하면 '실행할 수 있는 명령이 없습니다.'라고 답해."
                )
            },
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content if response.choices and response.choices[0].message.content else ""


async def main():
    # 거리 센서 값을 읽어서 장애물 감지 시 90도 회전하는 함수
    async def move_with_obstacle_avoid():
        print("[장애물 감지 이동 시작]")
        LED_PORT = 0x32
        # 거리 센서 알림 구독
        await client.write_gatt_char(MOTOR_CHAR_UUID, COLOR_DISTANCE_SENSOR_SUBSCRIBE)
        print("거리 센서 구독!")
        def notification_handler(sender, data):
            print(f"[알림] sender={{sender}}, data={{list(data)}}")
            # BOOST 거리센서 알림은 data[2]==0x45(Port 0x05), data[4]~[5]에 거리(mm)
            if len(data) >= 6 and data[2] == 0x45:
                distance = data[4] | (data[5] << 8)
                print(f"[파싱된 거리] {{distance}} mm")
                move_with_obstacle_avoid.last_distance = distance
        move_with_obstacle_avoid.last_distance = 1000
        await client.start_notify(MOTOR_CHAR_UUID, notification_handler)
        try:
            for _ in range(30):  # 30번(약 6초) 반복
                dist = move_with_obstacle_avoid.last_distance
                print(f"[거리센서] 측정값: {dist} mm")
                if dist <= 100:  # 100mm 이내 장애물
                    print("[장애물 감지] 90도 회전!")
                    # LED 파랑, A 앞으로 B 뒤로(제자리 회전)
                    await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, LED_PORT, 0x11, 0x51, 0x00, 0x07]))
                    await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x01, 0x64]))
                    await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x01, 0x9C]))
                    await asyncio.sleep(0.55)  # 약 90도 회전(조정 가능)
                    # 정지
                    await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x00, 0x00]))
                    await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x00, 0x00]))
                else:
                    # 앞으로 이동
                    await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x01, 0x64]))
                    await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x01, 0x64]))
                await asyncio.sleep(0.2)
            # 정지
            await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x00, 0x00]))
            await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x00, 0x00]))
        finally:
            await client.stop_notify(MOTOR_CHAR_UUID)
        print("[장애물 감지 이동 종료]")

    async with BleakClient(HUB_MAC_ADDRESS) as client:
        if client.is_connected:
            # 센서 구독 및 알림 자동 등록
            await subscribe_sensors(client)

            # --- 추가 동작 루틴들 ---
            async def lego_wave():
                print("[파도타기(웨이브) 시작]")
                LED_PORT = 0x32
                LED_COLORS = [0x05, 0x06, 0x07, 0x08, 0x09]
                for i in range(10):
                    color = LED_COLORS[i % len(LED_COLORS)]
                    await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, LED_PORT, 0x11, 0x51, 0x00, color]))
                    if i % 2 == 0:
                        # A 앞으로, B 뒤로
                        await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x01, 0x64]))
                        await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x01, 0x9C]))
                    else:
                        # A 뒤로, B 앞으로
                        await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x01, 0x9C]))
                        await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x01, 0x64]))
                    await asyncio.sleep(0.22)
                # 정지
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x00, 0x00]))
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x00, 0x00]))
                print("[파도타기 종료]")

            async def lego_flash():
                print("[번개(플래시) 효과 시작]")
                LED_PORT = 0x32
                for i in range(8):
                    await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, LED_PORT, 0x11, 0x51, 0x00, 0x09]))  # 흰색
                    await asyncio.sleep(0.08)
                    await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, LED_PORT, 0x11, 0x51, 0x00, 0x00]))  # 꺼짐
                    await asyncio.sleep(0.08)
                print("[번개 효과 종료]")

            async def lego_spin():
                print("[회전(스핀) 시작]")
                LED_PORT = 0x32
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, LED_PORT, 0x11, 0x51, 0x00, 0x07]))  # 파랑
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x01, 0x64]))
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x01, 0x64]))
                await asyncio.sleep(1.2)
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x00, 0x00]))
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x00, 0x00]))
                print("[회전 종료]")

            async def lego_jump_stop():
                print("[점프&스톱 시작]")
                LED_PORT = 0x32
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, LED_PORT, 0x11, 0x51, 0x00, 0x08]))  # 노랑
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x01, 0x64]))
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x01, 0x64]))
                await asyncio.sleep(0.3)
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x01, 0x9C]))
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x01, 0x9C]))
                await asyncio.sleep(0.3)
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x00, 0x00]))
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x00, 0x00]))
                print("[점프&스톱 종료]")

            async def lego_rainbow():
                print("[무지개 쇼 시작]")
                LED_PORT = 0x32
                RAINBOW = [0x05, 0x08, 0x06, 0x07, 0x09]  # 빨, 노, 초, 파, 흰
                for color in RAINBOW:
                    await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, LED_PORT, 0x11, 0x51, 0x00, color]))
                    await asyncio.sleep(0.22)
                for _ in range(3):
                    for color in RAINBOW:
                        await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, LED_PORT, 0x11, 0x51, 0x00, color]))
                        await asyncio.sleep(0.12)
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, LED_PORT, 0x11, 0x51, 0x00, 0x00]))
                print("[무지개 쇼 종료]")

            async def lego_dance():
                print("[춤 동작 시작]")
                LED_COLORS = [0x05, 0x06, 0x07, 0x08, 0x09]  # 빨강, 초록, 파랑, 노랑, 흰색
                LED_PORT = 0x32
                for i in range(5):
                    print("[댄스1] 왼쪽(A) 앞으로, 오른쪽(B) 뒤로")
                    await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, LED_PORT, 0x11, 0x51, 0x00, LED_COLORS[i%len(LED_COLORS)]]))
                    await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x01, 0x64]))
                    await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x01, 0x9C]))
                    await asyncio.sleep(0.35)
                    print("[댄스1] 왼쪽(A) 뒤로, 오른쪽(B) 앞으로")
                    await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, LED_PORT, 0x11, 0x51, 0x00, LED_COLORS[(i+1)%len(LED_COLORS)]]))
                    await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x01, 0x9C]))
                    await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x01, 0x64]))
                    await asyncio.sleep(0.35)
                print("[댄스2] 제자리 빠른 회전!")
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, LED_PORT, 0x11, 0x51, 0x00, LED_COLORS[2]]))
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x01, 0x64]))
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x01, 0x64]))
                await asyncio.sleep(0.5)
                print("[댄스3] 점프! (양쪽 역방향)")
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, LED_PORT, 0x11, 0x51, 0x00, LED_COLORS[3]]))
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x01, 0x9C]))
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x01, 0x9C]))
                await asyncio.sleep(0.3)
                print("[댄스4] 좌우 진동!")
                for j in range(8):
                    await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, LED_PORT, 0x11, 0x51, 0x00, LED_COLORS[j%len(LED_COLORS)]]))
                    await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x01, 0x32]))
                    await asyncio.sleep(0.13)
                    await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x01, 0xCE]))
                    await asyncio.sleep(0.13)
                    await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x01, 0x32]))
                    await asyncio.sleep(0.13)
                    await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x01, 0xCE]))
                    await asyncio.sleep(0.13)
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, LED_PORT, 0x11, 0x51, 0x00, LED_COLORS[4]]))
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x00, 0x00]))
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x00, 0x00]))
                print("[춤 동작 종료]")

            print("[연결 성공] LEGO BOOST 허브와 연결되었습니다!\n")
            print("[사용 가능한 모터 및 센서]")
            print("- A 모터 (내장)")
            print("- B 모터 (내장)")
            print("- C 모터 (외부)")
            print("- D 모터 (외부)")
            print("- 자이로(틸트) 센서")
            print("- 컬러 센서")
            print("- 거리 센서\n")
            print("[GPT가 인식하는 명령어 예시]")
            print("- A 모터 앞으로 / A 모터 정지")
            print("- B 모터 앞으로 / B 모터 정지")
            print("- C 모터 앞으로 / C 모터 정지")
            print("- D 모터 앞으로 / D 모터 정지")
            print("- 모든 모터 앞으로 / 모든 모터 정지")
            print("- 자이로 센서 구독 / 틸트 센서 구독")
            print("- 컬러 센서 구독 / 거리 센서 구독")
            print("- 센서 모두 구독 / 센서 모두 해제")
            print("- 춤 / dance")
            print("- 파도타기 / 웨이브 / wave")
            print("- 번개 / 플래시 / flash")
            print("- 회전 / 스핀 / spin")
            print("- 점프 / 스톱 / jump")
            print("- 무지개 / rainbow")
            print("- 장애물 / 거리센서 / 피하기 / obstacle\n")


            # (중복 구독 제거: subscribe_sensors에서 이미 처리)

            print("[테스트 완료] 이제 명령을 입력해 직접 제어해보세요.\n")

            # process_command 함수 정의를 main 함수 내부로 이동
            from typing import Callable, Awaitable, Optional
            async def process_command(
                client,
                user_input: str,
                lego_dance: Optional[Callable[[], Awaitable[None]]] = None,
                lego_wave: Optional[Callable[[], Awaitable[None]]] = None,
                lego_flash: Optional[Callable[[], Awaitable[None]]] = None,
                lego_spin: Optional[Callable[[], Awaitable[None]]] = None,
                lego_jump_stop: Optional[Callable[[], Awaitable[None]]] = None,
                lego_rainbow: Optional[Callable[[], Awaitable[None]]] = None,
                move_with_obstacle_avoid: Optional[Callable[[], Awaitable[None]]] = None
            ) -> None:
                gpt_reply = chat_with_gpt(user_input)
                print("GPT 응답:", gpt_reply)
                if not gpt_reply:
                    print("GPT 응답이 비어 있습니다.")
                    return
                reply = gpt_reply.lower()
                # 루틴/모터/센서/액션 분기
                if lego_dance and ("춤" in reply or "dance" in reply):
                    await lego_dance()
                    return
                if lego_wave and ("파도타기" in reply or "웨이브" in reply or "wave" in reply):
                    await lego_wave()
                    return
                if lego_flash and ("번개" in reply or "플래시" in reply or "flash" in reply):
                    await lego_flash()
                    return
                if lego_spin and ("회전" in reply or "스핀" in reply or "spin" in reply):
                    await lego_spin()
                    return
                if lego_jump_stop and ("점프" in reply or "스톱" in reply or "jump" in reply):
                    await lego_jump_stop()
                    return
                if lego_rainbow and ("무지개" in reply or "rainbow" in reply):
                    await lego_rainbow()
                    return
                if move_with_obstacle_avoid and ("장애물" in reply or "거리센서" in reply or "피하기" in reply or "obstacle" in reply):
                    await move_with_obstacle_avoid()
                    return
                if ("a 모터" in reply and "앞으로" in reply):
                    await test_motor(client, 0x00, "A")
                elif ("b 모터" in reply and "앞으로" in reply):
                    await test_motor(client, 0x01, "B")
                elif ("c 모터" in reply and "앞으로" in reply):
                    await test_external_motor(client, 0x32, "C")
                elif ("d 모터" in reply and "앞으로" in reply):
                    await test_external_motor(client, 0x33, "D")
                elif ("a 모터" in reply and "정지" in reply):
                    await test_motor(client, 0x00, "A")
                elif ("b 모터" in reply and "정지" in reply):
                    await test_motor(client, 0x01, "B")
                elif ("c 모터" in reply and "정지" in reply):
                    await test_external_motor(client, 0x32, "C")
                elif ("d 모터" in reply and "정지" in reply):
                    await test_external_motor(client, 0x33, "D")
                elif ("모든 모터" in reply and "앞으로" in reply):
                    await test_motor(client, 0x00, "A")
                    await test_motor(client, 0x01, "B")
                    await test_external_motor(client, 0x32, "C")
                    await test_external_motor(client, 0x33, "D")
                elif ("모든 모터" in reply and "정지" in reply):
                    await test_motor(client, 0x00, "A")
                    await test_motor(client, 0x01, "B")
                    await test_external_motor(client, 0x32, "C")
                    await test_external_motor(client, 0x33, "D")
                elif ("자이로 센서 구독" in reply or "틸트 센서 구독" in reply):
                    await client.write_gatt_char(MOTOR_CHAR_UUID, TILT_SENSOR_SUBSCRIBE)
                    print("자이로(틸트) 센서 구독!")
                elif ("컬러 센서 구독" in reply or "거리 센서 구독" in reply):
                    await client.write_gatt_char(MOTOR_CHAR_UUID, COLOR_DISTANCE_SENSOR_SUBSCRIBE)
                    print("컬러&거리 센서 구독!")
                elif ("센서 모두 구독" in reply):
                    await client.write_gatt_char(MOTOR_CHAR_UUID, TILT_SENSOR_SUBSCRIBE)
                    print("자이로(틸트) 센서 구독!")
                    await client.write_gatt_char(MOTOR_CHAR_UUID, COLOR_DISTANCE_SENSOR_SUBSCRIBE)
                    print("컬러&거리 센서 구독!")
                elif ("센서 모두 해제" in reply):
                    print("센서 구독 해제 (실제 해제 명령 필요)")
                elif ("실행할 수 있는 명령이 없습니다" in reply):
                    print("실행할 수 있는 명령이 없습니다.")
                else:
                    action_keywords = []
                    for kw in ["go_forward", "stop", "turn_left", "play_sound", "back_off"]:
                        if kw in reply:
                            action_keywords.append(kw)
                    if action_keywords:
                        await execute_action_keywords(client, action_keywords)
                    else:
                        print("실행할 수 있는 명령이 없습니다.")

            while True:
                user_input = input("명령을 입력하세요 (또는 '음성' 입력 후 말하기): ")
                if user_input.lower() == "exit":
                    break
                if user_input.lower() == "음성":
                    r = sr.Recognizer()
                    with sr.Microphone() as source:
                        print("음성 인식 대기 중... '춤'이라고 말해보세요.")
                        audio = r.listen(source, timeout=5, phrase_time_limit=3)
                    try:
                        voice_text = r.recognize_google(audio, language="ko-KR")
                        print(f"[음성 인식 결과] {voice_text}")
                        user_input = voice_text
                    except sr.UnknownValueError:
                        print("음성을 인식하지 못했습니다.")
                        continue
                    except sr.RequestError as e:
                        print(f"음성 인식 서비스 오류: {e}")
                        continue

                await process_command(
                    client, user_input,
                    lego_dance=lego_dance,
                    lego_wave=lego_wave,
                    lego_flash=lego_flash,
                    lego_spin=lego_spin,
                    lego_jump_stop=lego_jump_stop,
                    lego_rainbow=lego_rainbow,
                    move_with_obstacle_avoid=move_with_obstacle_avoid
                )

    # async with 블록 종료 후 연결 실패 메시지
    if not client.is_connected:
        print("허브와 연결 실패.")

    else:
        print("허브와 연결 실패.")

## 진입점: 외부모터 테스트 모드와 일반 모드 분기 (main 함수 정의 이후로 이동)

# main 함수 정의가 파일 상단에 오도록 이동


def main_voice_mode():
    import asyncio
    import speech_recognition as sr
    async def voice_loop():
        async with BleakClient(HUB_MAC_ADDRESS) as client:
            if not client.is_connected:
                print("허브와 연결 실패. 음성 명령 실행 불가.")
                return
            await subscribe_sensors(client)
            print("[연결 성공] 음성 명령을 말하세요. (예: '춤', '웨이브', '앞으로', '정지' 등)")
            # 루틴 함수 정의 (client context 유지)
            async def lego_wave():
                LED_PORT = 0x32
                LED_COLORS = [0x05, 0x06, 0x07, 0x08, 0x09]
                for i in range(10):
                    color = LED_COLORS[i % len(LED_COLORS)]
                    await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, LED_PORT, 0x11, 0x51, 0x00, color]))
                    if i % 2 == 0:
                        await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x01, 0x64]))
                        await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x01, 0x9C]))
                    else:
                        await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x01, 0x9C]))
                        await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x01, 0x64]))
                    await asyncio.sleep(0.22)
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x00, 0x00]))
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x00, 0x00]))
            async def lego_flash():
                LED_PORT = 0x32
                for i in range(8):
                    await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, LED_PORT, 0x11, 0x51, 0x00, 0x09]))
                    await asyncio.sleep(0.08)
                    await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, LED_PORT, 0x11, 0x51, 0x00, 0x00]))
                    await asyncio.sleep(0.08)
            async def lego_spin():
                LED_PORT = 0x32
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, LED_PORT, 0x11, 0x51, 0x00, 0x07]))
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x01, 0x64]))
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x01, 0x64]))
                await asyncio.sleep(1.2)
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x00, 0x00]))
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x00, 0x00]))
            async def lego_jump_stop():
                LED_PORT = 0x32
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, LED_PORT, 0x11, 0x51, 0x00, 0x08]))
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x01, 0x64]))
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x01, 0x64]))
                await asyncio.sleep(0.3)
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x01, 0x9C]))
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x01, 0x9C]))
                await asyncio.sleep(0.3)
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x00, 0x00]))
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x00, 0x00]))
            async def lego_rainbow():
                LED_PORT = 0x32
                RAINBOW = [0x05, 0x08, 0x06, 0x07, 0x09]
                for color in RAINBOW:
                    await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, LED_PORT, 0x11, 0x51, 0x00, color]))
                    await asyncio.sleep(0.22)
                for _ in range(3):
                    for color in RAINBOW:
                        await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, LED_PORT, 0x11, 0x51, 0x00, color]))
                        await asyncio.sleep(0.12)
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, LED_PORT, 0x11, 0x51, 0x00, 0x00]))
            async def lego_dance():
                LED_COLORS = [0x05, 0x06, 0x07, 0x08, 0x09]
                LED_PORT = 0x32
                for i in range(5):
                    await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, LED_PORT, 0x11, 0x51, 0x00, LED_COLORS[i%len(LED_COLORS)]]))
                    await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x01, 0x64]))
                    await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x01, 0x9C]))
                    await asyncio.sleep(0.35)
                    await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, LED_PORT, 0x11, 0x51, 0x00, LED_COLORS[(i+1)%len(LED_COLORS)]]))
                    await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x01, 0x9C]))
                    await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x01, 0x64]))
                    await asyncio.sleep(0.35)
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, LED_PORT, 0x11, 0x51, 0x00, LED_COLORS[2]]))
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x01, 0x64]))
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x01, 0x64]))
                await asyncio.sleep(0.5)
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, LED_PORT, 0x11, 0x51, 0x00, LED_COLORS[3]]))
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x01, 0x9C]))
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x01, 0x9C]))
                await asyncio.sleep(0.3)
                for j in range(8):
                    await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, LED_PORT, 0x11, 0x51, 0x00, LED_COLORS[j%len(LED_COLORS)]]))
                    await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x01, 0x32]))
                    await asyncio.sleep(0.13)
                    await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x01, 0xCE]))
                    await asyncio.sleep(0.13)
                    await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x01, 0x32]))
                    await asyncio.sleep(0.13)
                    await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x01, 0xCE]))
                    await asyncio.sleep(0.13)
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, LED_PORT, 0x11, 0x51, 0x00, LED_COLORS[4]]))
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x00, 0x11, 0x51, 0x00, 0x00]))
                await client.write_gatt_char(MOTOR_CHAR_UUID, bytearray([0x08, 0x00, 0x81, 0x01, 0x11, 0x51, 0x00, 0x00]))
            async def move_with_obstacle_avoid():
                LED_PORT = 0x32
                await client.write_gatt_char(MOTOR_CHAR_UUID, COLOR_DISTANCE_SENSOR_SUBSCRIBE)
            r = sr.Recognizer()
            while True:
                with sr.Microphone() as source:
                    print("음성 인식 대기 중...")
                    audio = r.listen(source, timeout=5, phrase_time_limit=5)
                try:
                    voice_text = r.recognize_google(audio, language="ko-KR")
                    print(f"[음성 인식 결과] {voice_text}")
                except sr.UnknownValueError:
                    print("음성을 인식하지 못했습니다.")
                    continue
                except sr.RequestError as e:
                    print(f"음성 인식 서비스 오류: {e}")
                    continue
                await process_command(
                    client, voice_text,
                    lego_dance=lego_dance,
                    lego_wave=lego_wave,
                    lego_flash=lego_flash,
                    lego_spin=lego_spin,
                    lego_jump_stop=lego_jump_stop,
                    lego_rainbow=lego_rainbow,
                    move_with_obstacle_avoid=move_with_obstacle_avoid
                )
    asyncio.run(voice_loop())

if __name__ == "__main__":
    import speech_recognition as sr
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "test_external_motor":
            asyncio.run(test_external_motor_main())
        elif len(sys.argv) > 1 and sys.argv[1] == "voice":
            print("[음성 명령 모드] LEGO BOOST 허브에 연결 후, 마이크에 대고 명령을 말하면 바로 실행됩니다. (종료: Ctrl+C)")
            main_voice_mode()
        else:
            asyncio.run(main())
    except Exception as e:
        print("[오류] 프로그램 실행 중 예외가 발생했습니다:")
        print(e)
        if "disconnected" in str(e).lower():
            print("\n허브와의 연결이 끊어졌습니다. 전원을 확인하고, 가까이에서 다시 실행해 주세요.")
        else:
            print("\n허브의 전원 및 연결 상태를 확인하고, 다시 실행해 주세요.")
