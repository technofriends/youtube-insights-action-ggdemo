from pydantic import BaseModel

class Payload(BaseModel):
    video_id: str
    application_section: str = "4-YT-Su"