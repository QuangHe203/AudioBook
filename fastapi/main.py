from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import fitz  # PyMuPDF
import re

app = FastAPI()

# 🌐 Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả origins, hoặc chỉ định cụ thể ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],  # Cho phép tất cả methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Cho phép tất cả headers
)


# 🏠 Route mặc định để kiểm tra server
@app.get("/")
def root():
    return {"message": "Hello from Docker FastAPI!"}


# 🧾 Model nhận URL PDF từ người dùng
class PDFUrl(BaseModel):
    url: str


# 🧩 Hàm đọc PDF từ URL
def read_pdf_from_url(url: str) -> str:
    try:
        response = requests.get(url)
        response.raise_for_status()

        pdf_bytes = response.content
        text = ""

        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()

        return text.strip()
    except Exception as e:
        print(f"Lỗi khi đọc PDF: {e}")
        return None


# 🧠 Hàm tách chapter
def split_chapters(text: str):
    pattern = r'(LỜI NÓI ĐẦU|Chương\s+\d+)'
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


# 🚀 Endpoint nhận URL PDF và trả về list các chapter
@app.post("/split-pdf-url/")
def split_pdf_url(pdf: PDFUrl):
    text = read_pdf_from_url(pdf.url)
    if not text:
        raise HTTPException(status_code=400, detail="Không thể đọc file PDF từ URL.")

    chapters = split_chapters(text)
    if not chapters:
        raise HTTPException(status_code=404, detail="Không tìm thấy chapter trong PDF.")

    return {"chapters": chapters}


# 📁 Endpoint nhận file upload PDF và trả về map các chapter
@app.post("/split-pdf/")
async def split_pdf(file: UploadFile = File(...)):
    # Kiểm tra file có phải PDF không
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận file PDF.")
    
    try:
        # Đọc nội dung file
        pdf_bytes = await file.read()
        print(f"📄 File nhận được: {file.filename}, Size: {len(pdf_bytes)} bytes")
        text = ""
        
        # Mở PDF từ bytes
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            print(f"📖 Số trang: {len(doc)}")
            for page in doc:
                text += page.get_text()
        
        text = text.strip()
        print(f"📝 Tổng ký tự: {len(text)}")
        print(f"🔍 Preview 500 ký tự đầu:\n{text[:500]}\n")
        
        if not text:
            raise HTTPException(status_code=400, detail="Không thể đọc nội dung PDF.")
        
        # Tách chapters
        chapters = split_chapters(text)
        
        # Nếu không tìm thấy chapter, trả về toàn bộ text để debug
        if not chapters:
            return {
                "error": "Không tìm thấy chapter trong PDF",
                "text_preview": text[:1000] + "..." if len(text) > 1000 else text,
                "total_characters": len(text),
                "hint": "PDF cần chứa 'Chương 1', 'Chương 2', hoặc 'LỜI NÓI ĐẦU'"
            }
        
        # Tạo map với tên chương là key và nội dung là value
        chapters_map = {chapter["title"]: chapter["content"] for chapter in chapters}
        
        return chapters_map
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi xử lý file: {str(e)}")
