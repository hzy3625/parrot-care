# ParrotCare AI 鈥?璇︾粏璁捐璇存槑涔?

**鏂囨。鐗堟湰**: V1.0
**鍒涘缓鏃ユ湡**: 2026-06-12
**椤圭洰鍚嶇О**: ParrotCare AI
**瀵瑰簲闇€姹?*: REQ-PARROT-001 / REQ-PARROT-002 / REQ-PARROT-003

---

## 涓€銆佺郴缁熸灦鏋?

### 1.1 鎶€鏈爤

| 灞傜骇 | 鎶€鏈€夊瀷 | 璇存槑 |
|------|---------|------|
| 鍚庣妗嗘灦 | FastAPI (Python 3.10+) | 寮傛楂樻€ц兘锛岃嚜鍔?API 鏂囨。 |
| 鏁版嵁搴?| SQLite (MVP) 鈫?PostgreSQL (鐢熶骇) | 鍏崇郴鍨嬫暟鎹瓨鍌?|
| ORM | SQLAlchemy 2.0 | 鏁版嵁搴撴ā鍨嬫槧灏?|
| AI 寮曟搸 | librosa + 瑙勫垯寮曟搸 (MVP) 鈫?PyTorch (V1.0+) | 闊抽鐗瑰緛鎻愬彇 + 鍒嗙被 |
| 鍓嶇 | HTML5 + Bootstrap 5 (MVP) | 鍝嶅簲寮?Web 搴旂敤 |
| 瀹炴椂閫氫俊 | WebSocket (WebSocketManager) | 瀹炴椂鎺ㄩ€佸紓甯稿憡璀?|
| 瀹瑰櫒鍖?| Docker + Docker Compose | 寮€鍙?閮ㄧ讲鐜 |

### 1.2 椤圭洰缁撴瀯

```
parrot-care/
鈹溾攢鈹€ backend/
鈹?  鈹溾攢鈹€ app/
鈹?  鈹?  鈹溾攢鈹€ api/              # API 璺敱灞?
鈹?  鈹?  鈹?  鈹溾攢鈹€ users.py      # 鐢ㄦ埛娉ㄥ唽銆佺櫥褰?
鈹?  鈹?  鈹?  鈹溾攢鈹€ parrots.py    # 楣﹂箟妗ｆ绠＄悊
鈹?  鈹?  鈹?  鈹溾攢鈹€ events.py     # 浜嬩欢鏌ヨ銆佺粺璁?
鈹?  鈹?  鈹?  鈹斺攢鈹€ audio.py      # 闊抽涓婁紶銆佸垎绫?
鈹?  鈹?  鈹溾攢鈹€ models/           # 鏁版嵁妯″瀷灞?
鈹?  鈹?  鈹?  鈹溾攢鈹€ database.py   # SQLAlchemy ORM 妯″瀷
鈹?  鈹?  鈹?  鈹斺攢鈹€ schemas.py    # Pydantic 璇锋眰/鍝嶅簲 Schema
鈹?  鈹?  鈹溾攢鈹€ services/         # 涓氬姟閫昏緫灞?
鈹?  鈹?  鈹?  鈹溾攢鈹€ audio_classifier.py   # 闊抽鍒嗙被鏈嶅姟
鈹?  鈹?  鈹?  鈹斺攢鈹€ realtime_analyzer.py  # 瀹炴椂鍒嗘瀽鏈嶅姟
鈹?  鈹?  鈹溾攢鈹€ config.py         # 閰嶇疆绠＄悊
鈹?  鈹?  鈹斺攢鈹€ db.py             # 鏁版嵁搴撳垵濮嬪寲
鈹?  鈹溾攢鈹€ main.py               # 搴旂敤鍏ュ彛
鈹?  鈹溾攢鈹€ start.py              # 鍚姩鑴氭湰
鈹?  鈹溾攢鈹€ requirements.txt      # Python 渚濊禆
鈹?  鈹溾攢鈹€ dockerfile            # 瀹瑰櫒鏋勫缓
鈹?  鈹斺攢鈹€ .env.example          # 鐜鍙橀噺妯℃澘
鈹溾攢鈹€ web_app/
鈹?  鈹斺攢鈹€ index.html            # Web 鍓嶇鍏ュ彛
鈹溾攢鈹€ docker-compose.yml        # 瀹瑰櫒缂栨帓
鈹斺攢鈹€ docs/                     # 椤圭洰鏂囨。
```

### 1.3 妯″潡璁捐

```
鈹屸攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
鈹?                 FastAPI Application             鈹?
鈹溾攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
鈹? Users API  鈹?Parrots API 鈹?Events  鈹?Audio API 鈹?
鈹? 璺敱灞?    鈹? 璺敱灞?    鈹? 璺敱灞?鈹? 璺敱灞?  鈹?
鈹溾攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹粹攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹粹攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹粹攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
鈹?             Pydantic Schemas (鏁版嵁楠岃瘉)         鈹?
鈹溾攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
鈹? SQLAlchemy 鈹? Business Services                鈹?
鈹? ORM Models 鈹? 鈹屸攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹? 鈹?
鈹?            鈹? 鈹侫udioClassifier鈹俁ealtimeAnalyzer鈹? 鈹?
鈹溾攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹粹攢鈹€鈹粹攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹粹攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹粹攢鈹€鈹?
鈹?             SQLite / PostgreSQL                 鈹?
鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
```

---

## 浜屻€佹暟鎹簱璁捐

### 2.1 ER 鍥?

```
users 鈹€鈹€鈹€鈹€< parrots 鈹€鈹€鈹€鈹€< media_events 鈹€鈹€鈹€鈹€< user_feedback
  鈹?          鈹?             鈹?
  鈹斺攢鈹€< devices 鈹?             鈹?
               鈹斺攢鈹€鈹€鈹€> behavior_daily_stats
```

### 2.2 琛ㄧ粨鏋?

#### users 琛?

| 瀛楁 | 绫诲瀷 | 绾︽潫 | 璇存槑 |
|------|------|------|------|
| user_id | VARCHAR(64) | PK | UUID |
| nickname | VARCHAR(100) | NULL | 鏄电О |
| phone | VARCHAR(30) | UNIQUE, INDEX | 鎵嬫満鍙?|
| email | VARCHAR(100) | UNIQUE, INDEX | 閭 |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt 鍝堝笇 |
| subscription_status | VARCHAR(30) | DEFAULT 'free' | 璁㈤槄鐘舵€?|
| created_at | DATETIME | DEFAULT NOW | 鍒涘缓鏃堕棿 |

#### parrots 琛?

| 瀛楁 | 绫诲瀷 | 绾︽潫 | 璇存槑 |
|------|------|------|------|
| parrot_id | VARCHAR(64) | PK | UUID |
| user_id | VARCHAR(64) | FK 鈫?users | 鎵€灞炵敤鎴?|
| name | VARCHAR(100) | NOT NULL | 鍚嶇О |
| species | VARCHAR(100) | NOT NULL | 鍝佺 |
| age | INTEGER | NULL | 骞撮緞 |
| gender | VARCHAR(30) | NULL | 鎬у埆 |
| weight | DECIMAL(6,2) | NULL | 浣撻噸(g) |
| has_plucking_history | BOOLEAN | DEFAULT FALSE | 鎷旀瘺鍙?|
| has_night_fright_history | BOOLEAN | DEFAULT FALSE | 澶滄儕鍙?|
| created_at | DATETIME | DEFAULT NOW | 鍒涘缓鏃堕棿 |

#### media_events 琛?

| 瀛楁 | 绫诲瀷 | 绾︽潫 | 璇存槑 |
|------|------|------|------|
| event_id | VARCHAR(64) | PK | UUID |
| parrot_id | VARCHAR(64) | FK 鈫?parrots | 鎵€灞為功楣?|
| device_id | VARCHAR(64) | FK 鈫?devices, NULL | 璁惧 ID |
| event_time | DATETIME | INDEX | 浜嬩欢鏃堕棿 |
| event_type | VARCHAR(100) | NOT NULL | 琛屼负绫诲瀷 |
| media_type | VARCHAR(30) | NOT NULL | 濯掍綋绫诲瀷 |
| audio_url | TEXT | NULL | 闊抽 URL |
| video_url | TEXT | NULL | 瑙嗛 URL |
| duration | DECIMAL(8,2) | NULL | 鏃堕暱(绉? |
| confidence | DECIMAL(5,4) | NULL | 鍒嗙被缃俊搴?|
| is_abnormal | BOOLEAN | DEFAULT FALSE | 鏄惁寮傚父 |
| risk_level | VARCHAR(30) | NULL | 椋庨櫓绛夌骇 |
| created_at | DATETIME | DEFAULT NOW | 鍒涘缓鏃堕棿 |

#### user_feedback 琛?

| 瀛楁 | 绫诲瀷 | 绾︽潫 | 璇存槑 |
|------|------|------|------|
| feedback_id | VARCHAR(64) | PK | UUID |
| event_id | VARCHAR(64) | FK 鈫?media_events | 鍏宠仈浜嬩欢 |
| user_id | VARCHAR(64) | FK 鈫?users | 鐢ㄦ埛 ID |
| feedback_type | VARCHAR(50) | NOT NULL | 鍙嶉绫诲瀷 |
| feedback_label | VARCHAR(100) | NULL | 鍙嶉鏍囩 |
| comment | TEXT | NULL | 琛ュ厖璇存槑 |
| created_at | DATETIME | DEFAULT NOW | 鍒涘缓鏃堕棿 |

#### behavior_daily_stats 琛?

| 瀛楁 | 绫诲瀷 | 绾︽潫 | 璇存槑 |
|------|------|------|------|
| stat_id | VARCHAR(64) | PK | UUID |
| parrot_id | VARCHAR(64) | FK 鈫?parrots | 鎵€灞為功楣?|
| stat_date | DATETIME | INDEX | 缁熻鏃ユ湡 |
| chirp_count | INTEGER | DEFAULT 0 | 楦ｅ彨娆℃暟 |
| scream_count | INTEGER | DEFAULT 0 | 灏栧彨娆℃暟 |
| night_activity_count | INTEGER | DEFAULT 0 | 澶滈棿娲诲姩娆℃暟 |
| active_minutes | INTEGER | DEFAULT 0 | 娲昏穬鍒嗛挓鏁?|
| quiet_minutes | INTEGER | DEFAULT 0 | 瀹夐潤鍒嗛挓鏁?|
| abnormal_event_count | INTEGER | DEFAULT 0 | 寮傚父浜嬩欢鏁?|
| health_score | INTEGER | DEFAULT 100 | 鍋ュ悍璇勫垎 |

---

## 涓夈€丄PI 璁捐

### 3.1 鐢ㄦ埛妯″潡 `/api/users`

| 鏂规硶 | 璺緞 | 璇存槑 | 璇锋眰浣?| 鍝嶅簲 |
|------|------|------|--------|------|
| POST | `/register` | 鐢ㄦ埛娉ㄥ唽 | phone, password, nickname | UserResponse |
| POST | `/login` | 鐢ㄦ埛鐧诲綍 | phone, password | TokenResponse |

### 3.2 楣﹂箟妯″潡 `/api/parrots`

| 鏂规硶 | 璺緞 | 璇存槑 | 璇锋眰浣?| 鍝嶅簲 |
|------|------|------|--------|------|
| POST | `/` | 鍒涘缓楣﹂箟妗ｆ | ParrotCreate | ParrotResponse |
| GET | `/` | 鑾峰彇鐢ㄦ埛鎵€鏈夐功楣?| 鈥?| List[ParrotResponse] |
| GET | `/{parrot_id}` | 鑾峰彇楣﹂箟璇︽儏 | 鈥?| ParrotResponse |
| GET | `/{parrot_id}/summary` | 鑾峰彇楣﹂箟鍋ュ悍鎽樿 | 鈥?| ParrotSummary |

### 3.3 浜嬩欢妯″潡 `/api/events`

| 鏂规硶 | 璺緞 | 璇存槑 | 璇锋眰浣?| 鍝嶅簲 |
|------|------|------|--------|------|
| POST | `/` | 鍒涘缓浜嬩欢璁板綍 | EventCreate | EventDetail |
| GET | `/parrot/{parrot_id}` | 鑾峰彇楣﹂箟浜嬩欢鍒楄〃 | days (query) | List[EventDetail] |
| GET | `/abnormal/parrot/{parrot_id}` | 鑾峰彇寮傚父浜嬩欢鍒楄〃 | days (query) | List[EventDetail] |
| GET | `/today-summary/parrot/{parrot_id}` | 鑾峰彇浠婃棩鎽樿 | 鈥?| ParrotSummary |

### 3.4 闊抽妯″潡 `/api/audio`

| 鏂规硶 | 璺緞 | 璇存槑 | 璇锋眰浣?| 鍝嶅簲 |
|------|------|------|--------|------|
| POST | `/upload` | 涓婁紶闊抽骞跺垎绫?| AudioUpload | EventResponse |
| POST | `/upload-and-analyze` | 涓婁紶 + 瀹炴椂鍒嗘瀽 | AudioUpload | EventResponse |

---

## 鍥涖€佹牳蹇冧笟鍔￠€昏緫

### 4.1 闊抽鍒嗙被寮曟搸 (AudioClassifier)

```
杈撳叆: 闊抽鏂囦欢 (URL 鎴栨湰鍦拌矾寰?
  鈫?
1. 浣跨敤 librosa 鎻愬彇闊抽鐗瑰緛
   - MFCC 绯绘暟
   - 棰戣氨璐ㄥ績
   - 杩囬浂鐜?
   - 棰戣氨甯﹀
   - 棰戣氨瀵规瘮搴?
  鈫?
2. 瑙勫垯寮曟搸鍒嗙被 (MVP)
   - 楂橀 + 楂樿兘閲?+ 鐭寔缁?鈫?scream (灏栧彨)
   - 涓 + 闂存瓏 + 涓瓑鑳介噺 鈫?wing_flap (鎵戠繀)
   - 浣庨 + 绐佸彂楂樿兘閲?鈫?cage_bump (鎾炵)
   - 鍏朵粬 鈫?normal_chirp (姝ｅ父楦ｅ彨)
  鈫?
杈撳嚭: 鍒嗙被缁撴灉 + 缃俊搴?
```

### 4.2 瀹炴椂鍒嗘瀽鏈嶅姟 (RealtimeAnalyzer)

```
杈撳叆: 闊抽娴?/ 涓婁紶鐨勯煶棰戜簨浠?
  鈫?
1. 鏃堕棿绐楀彛鍒嗘瀽 (5 绉掔獥鍙?
  鈫?
2. 澶滈棿妯″紡妫€娴?(22:00-06:00)
   - 澶滈棿娲诲姩棰戠巼闃堝€? 3 娆?灏忔椂
   - 瓒呰繃闃堝€?鈫?risk_level = "high"
  鈫?
3. 寮傚父浜嬩欢鍒ゆ柇
   - 鍗曚簨浠跺紓甯?鈫?risk_level = "low/medium"
   - 杩炵画寮傚父 (3+) 鈫?risk_level = "high"
  鈫?
4. WebSocket 瀹炴椂鎺ㄩ€?
   - 鐢ㄦ埛鍦ㄧ嚎 鈫?鎺ㄩ€佷簨浠堕€氱煡
   - 鐢ㄦ埛绂荤嚎 鈫?鏍囪涓烘湭璇伙紝涓嬫鐧诲綍鏄剧ず
  鈫?
5. 鍋ュ悍璇勫垎璁＄畻
   - 鍩虹鍒? 100
   - 灏栧彨浜嬩欢: -10/娆?
   - 澶滈棿寮傚父: -15/娆?
   - 鎾炵浜嬩欢: -20/娆?
   - 鏈€浣庡垎: 0
```

### 4.3 鍋ュ悍璇勫垎绠楁硶

```python
def calculate_health_score(parrot_id: str, date: datetime) -> int:
    base_score = 100
    events = get_daily_events(parrot_id, date)
    
    deductions = 0
    for event in events:
        if event.event_type == "scream":
            deductions += 10
        elif event.is_abnormal and is_night(event.event_time):
            deductions += 15
        elif event.event_type == "cage_bump":
            deductions += 20
    
    return max(0, base_score - deductions)
```

---

## 浜斻€佸畨鍏ㄨ璁?

| 瀹夊叏鎺柦 | 瀹炵幇鏂瑰紡 |
|---------|---------|
| 瀵嗙爜鍔犲瘑 | bcrypt (salt rounds=12) |
| 璁よ瘉鏂瑰紡 | JWT Bearer Token (鏈夋晥鏈?24h) |
| CORS | 寮€鍙戠幆澧? *, 鐢熶骇鐜: 鐧藉悕鍗?|
| 杈撳叆楠岃瘉 | Pydantic Schema 鑷姩鏍￠獙 |
| SQL 娉ㄥ叆 | SQLAlchemy ORM (鍙傛暟鍖栨煡璇? |
| 鏂囦欢涓婁紶 | 闄愬埗澶у皬 < 10MB锛屼粎鍏佽闊抽鏍煎紡 |

---

## 鍏€侀儴缃叉灦鏋?

### 6.1 寮€鍙戠幆澧?

```
Docker Compose:
  - backend (FastAPI, port 8000)
  - SQLite (鍐呯疆锛屾寔涔呭寲鍗?
```

### 6.2 鐢熶骇鐜 (V1.0+)

```
Docker Compose:
  - backend (FastAPI, Gunicorn workers)
  - PostgreSQL (涓绘暟鎹簱)
  - Redis (缂撳瓨 + WebSocket 娑堟伅闃熷垪)
  - MinIO (瀵硅薄瀛樺偍 - 闊抽/瑙嗛鏂囦欢)
  - Nginx (鍙嶅悜浠ｇ悊 + 闈欐€佹枃浠?
```

---

## 涓冦€丮VP 寮€鍙戣鍒?

| Sprint | 鍐呭 | Story Points |
|--------|------|-------------|
| V0.1 | 鐢ㄦ埛绯荤粺 + 楣﹂箟妗ｆ + 鍩虹闊抽鍒嗙被 | 11 |
| V0.2 | 浜嬩欢鍒楄〃 + 寮傚父妫€娴?+ 鍋ュ悍璇勫垎 | 11 |
| V0.3 | 瀹炴椂鍒嗘瀽 + WebSocket 鎺ㄩ€?+ 鐢ㄦ埛鍙嶉 | 9 |

---

**鏂囨。鐘舵€?*: V1.0 瀹屾垚
**涓嬫鏇存柊**: V0.3 瀹屾垚鍚庤ˉ鍏呭疄鏃跺垎鏋愯缁嗚璁?
