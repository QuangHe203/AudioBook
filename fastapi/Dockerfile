# 1️⃣ Sử dụng Python 3.11 (gọn nhẹ)
FROM python:3.11-slim

# 2️⃣ Tạo thư mục làm việc trong container
WORKDIR /app

# 3️⃣ Copy file requirements vào container
COPY requirements.txt .

# 4️⃣ Cài các thư viện cần thiết
RUN pip install --no-cache-dir -r requirements.txt

# 5️⃣ Copy toàn bộ code hiện tại vào container
COPY . .

# 6️⃣ Mở cổng 8000 để truy cập từ bên ngoài
EXPOSE 8000

# 7️⃣ Lệnh khởi chạy ứng dụng
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]