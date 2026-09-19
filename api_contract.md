# SkillSaathi API Contract

Specification for Frontend-to-Backend communication in the SkillSaathi voice-first skilling-recommendation application.

All JSON request bodies must include `Content-Type: application/json` unless specified as `multipart/form-data`.

---

## Summary of Endpoints

| Endpoint | Method | Description | Content-Type |
| :--- | :--- | :--- | :--- |
| `/session` | `POST` | Initialize a new user session | `application/json` |
| `/stt` | `POST` | Convert speech audio to transcribed text | `multipart/form-data` |
| `/turn` | `POST` | Dialogue turn: process worker message & update profile | `application/json` |
| `/readback` | `POST` | Generate profile summary for user confirmation | `application/json` |
| `/confirm` | `POST` | Confirm or correct the captured profile | `application/json` |
| `/recommend` | `POST` | Generate ranked skilling program recommendations | `application/json` |
| `/tts` | `POST` | Convert response text to spoken audio | `application/json` |

---

## 1. POST `/session`
Initializes a new session and dialogue state.

### Pydantic Models
```python
from typing import Optional
from pydantic import BaseModel, Field

class SessionCreateRequest(BaseModel):
    language: Optional[str] = Field(default="hi", description="Preferred language code (e.g. 'hi', 'en')")

class SessionResponse(BaseModel):
    session_id: str
    status: str
    language: str
    greeting: str
```

### Example Request JSON
```json
{
  "language": "hi"
}
```

### Example Response JSON (`200 OK`)
```json
{
  "session_id": "sess_9b2d8e41",
  "status": "active",
  "language": "hi",
  "greeting": "Namaste! Main SkillSaathi hoon. Aap abhi kya kaam karte hain?"
}
```

---

## 2. POST `/stt`
Converts voice audio into text using speech-to-text.

> **Note:** Accepts `multipart/form-data`. (Also accessible via `/transcribe`).

### Pydantic Models
```python
from typing import Optional
from pydantic import BaseModel

class STTResponse(BaseModel):
    text: str
    language: str
    error: Optional[str] = None
```

### Request Format
- **Content-Type**: `multipart/form-data`
- **Field**: `audio` (binary file, `.wav`, `.mp3`, `.m4a`, or `.webm`)
- Optional query parameter or form field: `session_id`

### Example Response JSON (`200 OK` - Success)
```json
{
  "text": "Main pichle teen saal se gaon mein bijli aur wiring ka kaam karta hoon.",
  "language": "hi"
}
```

### Example Response JSON (`200 OK` - No Speech / Silence Fallback)
```json
{
  "text": "",
  "error": "no_speech_detected"
}
```

---

## 3. POST `/turn`
Sends worker utterance to the conversational agent; extracts profile details and returns the next question.

### Pydantic Models
```python
from typing import Any, Dict, Optional
from pydantic import BaseModel

class UserProfile(BaseModel):
    occupation: Optional[str] = None
    experience_years: Optional[float] = None
    education: Optional[str] = None
    district: Optional[str] = None
    age: Optional[int] = None

class TurnRequest(BaseModel):
    session_id: str
    user_message: str

class TurnResponse(BaseModel):
    session_id: str
    agent_message: str
    is_complete: bool
    profile: UserProfile
```

### Example Request JSON
```json
{
  "session_id": "sess_9b2d8e41",
  "user_message": "Main electrician hoon aur 3 saal se wiring karta hoon."
}
```

### Example Response JSON (`200 OK`)
```json
{
  "session_id": "sess_9b2d8e41",
  "agent_message": "Bahut badhiya. Aapne padhai kahan tak ki hai?",
  "is_complete": false,
  "profile": {
    "occupation": "electrician",
    "experience_years": 3.0,
    "education": null,
    "district": null,
    "age": null
  }
}
```

---

## 4. POST `/readback`
Summarizes collected profile information into spoken text so the worker can verify accuracy.

### Pydantic Models
```python
from pydantic import BaseModel

class ReadbackRequest(BaseModel):
    session_id: str

class ReadbackResponse(BaseModel):
    session_id: str
    readback_text: str
    profile: UserProfile
```

### Example Request JSON
```json
{
  "session_id": "sess_9b2d8e41"
}
```

### Example Response JSON (`200 OK`)
```json
{
  "session_id": "sess_9b2d8e41",
  "readback_text": "Aap Varanasi se hain, 10th pass hain, aur 3 saal se electrician ka kaam karte hain. Kya yeh sab sahi hai?",
  "profile": {
    "occupation": "electrician",
    "experience_years": 3.0,
    "education": "10th pass",
    "district": "Varanasi",
    "age": 24
  }
}
```

---

## 5. POST `/confirm`
Records worker confirmation or note of correction for the profile readback.

### Pydantic Models
```python
from typing import Optional
from pydantic import BaseModel

class ConfirmRequest(BaseModel):
    session_id: str
    confirmed: bool
    corrections: Optional[str] = None

class ConfirmResponse(BaseModel):
    session_id: str
    confirmed: bool
    ready_for_recommendation: bool
    message: str
```

### Example Request JSON
```json
{
  "session_id": "sess_9b2d8e41",
  "confirmed": true,
  "corrections": null
}
```

### Example Response JSON (`200 OK`)
```json
{
  "session_id": "sess_9b2d8e41",
  "confirmed": true,
  "ready_for_recommendation": true,
  "message": "Profile verified successfully."
}
```

---

## 6. POST `/recommend`
Maps worker profile to NSQF category and generates curated government skilling program recommendations with spoken reasons.

### Pydantic Models
```python
from typing import List, Optional
from pydantic import BaseModel

class ProgramRecommendation(BaseModel):
    program_id: str
    title: str
    provider: str
    duration: str
    cost: str
    eligibility: str
    reason: str

class RecommendRequest(BaseModel):
    session_id: str

class RecommendResponse(BaseModel):
    session_id: str
    nsqf_category: str
    recommendations: List[ProgramRecommendation]
```

### Example Request JSON
```json
{
  "session_id": "sess_9b2d8e41"
}
```

### Example Response JSON (`200 OK`)
```json
{
  "session_id": "sess_9b2d8e41",
  "nsqf_category": "Construction & Electrical",
  "recommendations": [
    {
      "program_id": "prog_pmkvy_elec",
      "title": "PMKVY Assistant Electrician",
      "provider": "National Skill Development Corporation (NSDC)",
      "duration": "3 months",
      "cost": "Free (Government Sponsored)",
      "eligibility": "10th Pass",
      "reason": "Aapke 3 saal ke wiring anubhav ko sarkari praman-patra milega jisse behtar dihadi mil sakegi."
    },
    {
      "program_id": "prog_iti_wireman",
      "title": "CTS Wireman Certification",
      "provider": "Directorate General of Training (DGT)",
      "duration": "1 year",
      "cost": "Nominal / Subsidized",
      "eligibility": "8th Pass",
      "reason": "Formal trade certificate for commercial and industrial electrical installations."
    }
  ]
}
```

---

## 7. POST `/tts`
Synthesizes speech audio from text for voice output on mobile/web.

### Pydantic Models
```python
from typing import Optional
from pydantic import BaseModel, Field

class TTSRequest(BaseModel):
    text: str
    language: Optional[str] = Field(default="hi", description="Language code (e.g. 'hi', 'en')")

class TTSResponse(BaseModel):
    audio_base64: str
    format: str = "mp3"
```

### Example Request JSON
```json
{
  "text": "Aapke anubhav ke aadhar par PMKVY Assistant Electrician program sabse behtar hai.",
  "language": "hi"
}
```

### Example Response JSON (`200 OK`)
```json
{
  "audio_base64": "//uQxAAAAAAAAAAAA...",
  "format": "mp3"
}
```

> **Direct Audio Stream Option**: The server also supports returning binary audio directly (`audio/mpeg` content type) when requested by frontend via query param `?format=stream`.

---

## Common Error Responses

| Status Code | Meaning | Response JSON Example |
| :--- | :--- | :--- |
| `400 Bad Request` | Invalid input or corrupted file | `{"detail": "Invalid or corrupted audio file"}` |
| `404 Not Found` | Unknown session ID | `{"detail": "Session not found"}` |
| `422 Unprocessable Entity` | Pydantic validation failure | `{"detail": [{"loc": ["body", "user_message"], "msg": "field required"}]}` |
| `503 Service Unavailable` | STT or LLM provider failure | `{"error": "stt_unavailable"}` |
