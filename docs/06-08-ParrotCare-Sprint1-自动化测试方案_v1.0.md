# ParrotCare V0.4 Sprint 1 鑷姩鍖栨祴璇曟柟妗?

**鐗堟湰**: v1.0
**鏃ユ湡**: 2026-06-12
**璐熻矗浜?*: dev (寮€鍙戝伐绋嬪笀)

---

## 1. 娴嬭瘯鑼冨洿

### 1.1 娴嬭瘯鐩爣
楠岃瘉 V0.4 Sprint 1 鏂板鍔熻兘鐨?API 姝ｇ‘鎬с€佽竟鐣屾潯浠跺拰閿欒澶勭悊銆?

### 1.2 鍔熻兘鑼冨洿

| 妯″潡 | API 鏁伴噺 | 娴嬭瘯鐢ㄤ緥鏁?|
|------|---------|-----------|
| 鐢ㄦ埛璁よ瘉 | 4 | 4 |
| 瀵嗙爜閲嶇疆 | 3 | 5 |
| 涓汉淇℃伅 | 4 | 5 |
| 娑堟伅涓績 | 6 | 5 |
| 鍋ュ悍妗ｆ | 2 | 2 |
| **鎬昏** | **19** | **21** |

---

## 2. 娴嬭瘯鐢ㄤ緥鍒楄〃

### 2.1 鐢ㄦ埛璁よ瘉娴嬭瘯

| 缂栧彿 | 娴嬭瘯鐢ㄤ緥 | 楠岃瘉鐐?|
|------|---------|-------|
| UC-01 | test_register_new_user | 娉ㄥ唽鎴愬姛锛岃繑鍥?token |
| UC-02 | test_register_duplicate_phone | 閲嶅鎵嬫満鍙疯繑鍥?400 |
| UC-03 | test_login_success | 鐧诲綍鎴愬姛锛岃繑鍥?token |
| UC-04 | test_login_wrong_password | 瀵嗙爜閿欒杩斿洖 401 |

### 2.2 瀵嗙爜閲嶇疆娴嬭瘯

| 缂栧彿 | 娴嬭瘯鐢ㄤ緥 | 楠岃瘉鐐?|
|------|---------|-------|
| PR-01 | test_request_password_reset | 璇锋眰鎴愬姛 |
| PR-02 | test_password_reset_frequency_limit | 绗?娆¤姹傝繑鍥?429 |
| PR-03 | test_confirm_password_reset | 鏈夋晥 Token 閲嶇疆鎴愬姛 |
| PR-04 | test_confirm_expired_token | 杩囨湡 Token 杩斿洖 400 |
| PR-05 | test_password_strength_validation | 寮卞瘑鐮佽繑鍥?400 |

### 2.3 涓汉淇℃伅娴嬭瘯

| 缂栧彿 | 娴嬭瘯鐢ㄤ緥 | 楠岃瘉鐐?|
|------|---------|-------|
| PF-01 | test_get_profile | 鑾峰彇涓汉淇℃伅鎴愬姛 |
| PF-02 | test_update_profile | 鏇存柊鏄电О/閭鎴愬姛 |
| PF-03 | test_update_duplicate_email | 宸插崰鐢ㄩ偖绠辫繑鍥?400 |
| PF-04 | test_change_password | 淇敼瀵嗙爜鎴愬姛 |
| PF-05 | test_change_password_wrong_old | 鏃у瘑鐮侀敊璇繑鍥?400 |

### 2.4 娑堟伅涓績娴嬭瘯

| 缂栧彿 | 娴嬭瘯鐢ㄤ緥 | 楠岃瘉鐐?|
|------|---------|-------|
| NT-01 | test_create_notification | 鍒涘缓娑堟伅鎴愬姛 |
| NT-02 | test_list_notifications | 鍒嗛〉鍒楄〃姝ｇ‘ |
| NT-03 | test_unread_count | 鏈璁℃暟姝ｇ‘ |
| NT-04 | test_mark_notification_read | 鍗曟潯鏍囪宸茶 |
| NT-05 | test_mark_all_read | 鎵归噺鏍囪宸茶 |

### 2.5 鍋ュ悍妗ｆ娴嬭瘯

| 缂栧彿 | 娴嬭瘯鐢ㄤ緥 | 楠岃瘉鐐?|
|------|---------|-------|
| HO-01 | test_health_overview_single | 鍗曢功楣夋€昏姝ｇ‘ |
| HO-02 | test_health_overview_all | 鍏ㄩ功楣夋€昏姝ｇ‘ |

---

## 3. 娴嬭瘯鐜閰嶇疆

### 3.1 鎶€鏈爤

| 绫诲埆 | 宸ュ叿 | 鐗堟湰 |
|------|------|------|
| 娴嬭瘯妗嗘灦 | pytest | >=7.4.0 |
| 寮傛鏀寔 | pytest-asyncio | >=0.21.0 |
| HTTP 瀹㈡埛绔?| httpx | >=0.24.0 |
| 鏁版嵁搴?| SQLite (鍐呭瓨) | via aiosqlite |
| ORM | SQLAlchemy | >=2.0.0 |

### 3.2 娴嬭瘯鏁版嵁搴?

- 浣跨敤 SQLite 鍐呭瓨鏁版嵁搴?(:memory:)
- 姣忎釜娴嬭瘯鐙珛鏁版嵁搴撳疄渚?
- 娴嬭瘯缁撴潫鍚庝簨鍔″洖婊?

### 3.3 娴嬭瘯闅旂

- 姣忎釜娴嬭瘯鍑芥暟鐙珛鐨?db_session
- 浣跨敤 fixture 娉ㄥ叆娴嬭瘯鐢ㄦ埛
- auth_client 鑷姩鎼哄甫璁よ瘉 token

---

## 4. 杩愯鏂瑰紡

### 4.1 瀹夎娴嬭瘯渚濊禆
`ash
cd backend
pip install -r requirements.txt
`

### 4.2 杩愯鍏ㄩ儴娴嬭瘯
`ash
cd backend
pytest test_sprint1.py -v
`

### 4.3 杩愯鍗曚釜娴嬭瘯
`ash
pytest test_sprint1.py::test_register_new_user -v
`

### 4.4 杩愯鎸囧畾妯″潡娴嬭瘯
`ash
pytest test_sprint1.py -k "password" -v
`

### 4.5 鏌ョ湅娴嬭瘯瑕嗙洊鐜囷紙鍙€夛級
`ash
pytest test_sprint1.py --cov=app --cov-report=html
`

---

## 5. 娴嬭瘯缁撴灉棰勬湡

| 妯″潡 | 棰勬湡缁撴灉 | 澶囨敞 |
|------|---------|------|
| 鐢ㄦ埛璁よ瘉 | 鍏ㄩ儴閫氳繃 | 鍩虹鍔熻兘 |
| 瀵嗙爜閲嶇疆 | 鍏ㄩ儴閫氳繃 | 鍚鐜囬檺鍒堕獙璇?|
| 涓汉淇℃伅 | 鍏ㄩ儴閫氳繃 | 鍚敮涓€鎬ч獙璇?|
| 娑堟伅涓績 | 鍏ㄩ儴閫氳繃 | 鍚垎椤甸獙璇?|
| 鍋ュ悍妗ｆ | 鍏ㄩ儴閫氳繃 | 鍚粺璁¤绠楅獙璇?|

**棰勬湡鎬昏**: 21 涓祴璇曠敤渚嬪叏閮ㄩ€氳繃

---

## 6. 闄勫綍

### 6.1 娴嬭瘯鏂囦欢缁撴瀯
`
backend/
鈹溾攢鈹€ conftest.py          # 娴嬭瘯閰嶇疆鍜?fixtures
鈹溾攢鈹€ test_sprint1.py      # Sprint 1 娴嬭瘯鐢ㄤ緥
鈹斺攢鈹€ requirements.txt     # 鍖呭惈娴嬭瘯渚濊禆
`

### 6.2 鍏抽敭 fixtures

| Fixture | 浣滅敤 |
|---------|------|
| db_session | 寮傛鏁版嵁搴撲細璇濓紙浜嬪姟鍥炴粴锛?|
| client | 寮傛 HTTP 瀹㈡埛绔?|
| test_user | 娴嬭瘯鐢ㄦ埛锛堝凡娉ㄥ唽锛?|
| auth_token | JWT token |
| auth_client | 甯﹁璇佺殑 HTTP 瀹㈡埛绔?|

---

**鏂囨。缁撴潫**