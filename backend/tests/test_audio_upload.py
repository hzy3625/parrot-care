# -*- coding: utf-8 -*-
"""音频上传 API 测试 - AC-015-7"""

import io
import wave

import pytest


def _make_wav_bytes(duration_sec: float = 1.0) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"\x00\x00" * int(16000 * duration_sec))
    return buf.getvalue()


@pytest.mark.asyncio
async def test_audio_upload_success(auth_client, db_session, test_user):
    from app.models.database import Parrot, generate_id

    parrot = Parrot(
        parrot_id=generate_id(),
        user_id=test_user.user_id,
        name="小灰",
        species="African Grey",
        age=3,
    )
    db_session.add(parrot)
    await db_session.commit()

    audio_bytes = _make_wav_bytes()
    response = await auth_client.post(
        "/api/audio/upload",
        data={"parrot_id": parrot.parrot_id},
        files={"audio_file": ("test.wav", audio_bytes, "audio/wav")},
    )

    assert response.status_code == 200, response.text
    result = response.json()
    assert "event_id" in result
    assert "event_type" in result
    assert "is_abnormal" in result
    assert "confidence" in result
