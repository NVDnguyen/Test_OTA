# Dự án Pi App

## Hướng dẫn cài đặt

### 1. Chạy Backend bằng Docker

Idol có thể chạy backend bằng Docker như sau:

```fish
# Build và khởi động backend
docker compose up --build
```

Lệnh này sẽ sử dụng file `docker-compose.yml` và `Dockerfile` ở thư mục gốc dự án để build và khởi động server backend.

### 2. Chạy Backend thủ công

Idol cũng có thể chạy backend trực tiếp bằng Python:

```fish
python -m backend.app
```

#### Cấu hình Backend
- Backend sử dụng cấu hình từ `backend/config.py`.
- Các thiết lập được lấy từ biến môi trường hoặc file `.env` (xem `model_config` trong config).
- Các biến môi trường quan trọng:
  - `APP_ENV`: "development" hoặc "production"
  - `MONGO_URI`: Chuỗi kết nối MongoDB
  - `REDIS_URI`: Chuỗi kết nối Redis
  - `JWT_SECRET_KEY`: Khóa bí mật JWT
  - `VIETQR_WEBHOOK_SECRET_KEY`: Khóa bí mật webhook VietQR
  - `ADMIN_EMAIL`: Email admin đầu tiên
  - `VIETQR_BANK_BIN`, `VIETQR_ACCOUNT_NO`, `VIETQR_ACCOUNT_NAME`: Cấu hình thanh toán VietQR
  - `JWT_ACCESS_TOKEN_EXPIRES`, `JWT_REFRESH_TOKEN_EXPIRES`: Thời gian sống của token (thiết lập trong code)
- Idol có thể chỉnh sửa file `backend/config.py` hoặc tạo file `.env` trong thư mục backend để thay đổi cấu hình.

### 3. Chạy ứng dụng QT Client

#### Cài các gói cần thiết
- `source .venv/bin/activate`
- `pip install -r requirements.txst`
- `brew install zbar`

Để khởi động ứng dụng QT client, sử dụng lệnh sau:

```fish
python -m qt_client.main
```

#### Cấu hình QT Client
- Cấu hình cho QT client nằm ở `qt_client/config/settings.py`.
- Các thiết lập được lấy từ biến môi trường hoặc file `.env` trong thư mục `qt_client`.
- Các biến môi trường cần chú ý:
  - `API_BASE_URL`: Địa chỉ API backend
  - `SERIAL_PORT`: Đường dẫn thiết bị serial
  - `SERIAL_BAUDRATE`: Tốc độ truyền serial
- Idol có thể chỉnh sửa file `qt_client/config/settings.py` hoặc file `.env` trong thư mục `qt_client` để thay đổi cấu hình.

---

## Ghi chú bổ sung
- Đảm bảo idol đã cài đặt Python 3.10 trở lên.
- Cài đặt các thư viện phụ thuộc bằng lệnh:
  ```fish
  pip install -r requirements.txt
  ```
