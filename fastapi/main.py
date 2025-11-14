from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import fitz
import re
import os
from gtts import gTTS
import tempfile
import uuid

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Hello from Docker FastAPI!"}

class FileId(BaseModel):
    file_id: str

def split_chapters(text: str):
    pattern = r"(LỜI NÓI ĐẦU|Chương\s+\d+)"
    sections = re.split(pattern, text, flags=re.IGNORECASE)
    chapters = []
    title = None

    for part in sections:
        if re.match(pattern, part, re.IGNORECASE):
            title = part.strip()
            chapters.append({"title": title, "content": ""})
        elif title and chapters:
            chapters[-1]["content"] += part.strip() + "\n"

    for c in chapters:
        c["content"] = c["content"].strip()

    return chapters

@app.post("/process-pdf-by-id/")
def process_pdf_by_id(file_data: FileId):
    try:
        file_id = file_data.file_id
        print(f"📁 Đang xử lý file ID: {file_id}")
        
        uploads_path = "/uploads"
        
        file_name = f"{file_id}.pdf" if not file_id.endswith('.pdf') else file_id
        pdf_path = os.path.join(uploads_path, file_name)
        
        if not os.path.exists(pdf_path):
            alt_path = os.path.join(uploads_path, file_id)
            if os.path.exists(alt_path):
                pdf_path = alt_path
            else:
                files_list = os.listdir(uploads_path) if os.path.exists(uploads_path) else []
                raise HTTPException(
                    status_code=404,
                    detail=f"Không tìm thấy file với ID: {file_id}. Files có sẵn: {files_list[:10]}"
                )
        
        text = ""
        with fitz.open(pdf_path) as doc:
            print(f"📖 PDF có {len(doc)} trang")
            for page in doc:
                text += page.get_text()
        
        text = text.strip()
        
        if not text:
            raise HTTPException(status_code=400, detail="Không thể đọc nội dung từ PDF")
        
        # Tách chapters
        chapters = split_chapters(text)
        
        if not chapters:
            raise HTTPException(
                status_code=400, 
                detail="Không tìm thấy chapter trong PDF. PDF cần chứa 'Chương 1', 'Chương 2', hoặc 'LỜI NÓI ĐẦU'"
            )
        
        result = []
        for index, chapter in enumerate(chapters, 1):
            result.append({
                "id": index,
                "title": chapter["title"],
                "content": chapter["content"]
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi xử lý PDF: {str(e)}")

class TextToSpeech(BaseModel):
    text: str
    speed: float = 1.0  # Tốc độ đọc (0.5 - 2.0)

@app.post("/text-to-speech/")
def text_to_speech(data: TextToSpeech):
    try:
        if not data.text.strip():
            raise HTTPException(status_code=400, detail="Text không được để trống")
        
        # Tạo tên file unique
        audio_filename = f"audio_{uuid.uuid4().hex[:8]}.mp3"
        temp_dir = tempfile.gettempdir()
        audio_path = os.path.join(temp_dir, audio_filename)
        
        # Tạo audio từ text
        tts = gTTS(
            text=data.text,
            lang='vi',  # Tiếng Việt
            slow=False if data.speed >= 1.0 else True
        )
        
        tts.save(audio_path)
        
        # Trả về file audio
        return FileResponse(
            path=audio_path,
            media_type='audio/mpeg',
            filename=audio_filename,
            headers={"Content-Disposition": f"attachment; filename={audio_filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi tạo audio: {str(e)}")
