# Dịch phim trực tiếp bằng AI (Anh → Việt)

Ứng dụng lấy âm thanh từ tab trình duyệt đang phát phim, nhận dạng lời thoại tiếng Anh bằng Whisper,
dịch sang tiếng Việt bằng mô hình GPT và có thể đọc bản dịch thành tiếng.

## 1. Yêu cầu

- Windows 10/11
- Python 3.10 trở lên
- Google Chrome hoặc Microsoft Edge
- OpenAI API key có quyền sử dụng API

## 2. Cấu trúc thư mục

```text
DichPhim_AI/
├── server.py
├── index.html
├── requirements.txt
├── .env.example
├── start.bat
└── README.md
```

## 3. Cài đặt API key

Mở PowerShell tại thư mục dự án và chạy:

```powershell
$env:OPENAI_API_KEY="YOUR_API_KEY"
```

Thay `YOUR_API_KEY` bằng API key của bạn. Không chia sẻ key và không dán key vào `index.html`.

Có thể tùy chỉnh model:

```powershell
$env:STT_MODEL="whisper-1"
$env:TRANSLATE_MODEL="gpt-4o-mini"
```

## 4. Chạy ứng dụng

Trong PowerShell:

```powershell
python server.py
```

Hoặc sau khi đã đặt biến môi trường API key, nhấp đúp `start.bat`.

Mở trình duyệt tại:

http://localhost:8000

## 5. Cách sử dụng

1. Mở phim trong Chrome hoặc Edge.
2. Mở ứng dụng tại `http://localhost:8000`.
3. Nhấn **Bắt đầu**.
4. Chọn đúng tab đang phát phim.
5. Bật tùy chọn **Chia sẻ âm thanh tab** rồi xác nhận chia sẻ.
6. Ứng dụng sẽ hiện câu tiếng Anh, bản dịch tiếng Việt và đọc bản dịch nếu bật lồng tiếng.
7. Nhấn **Dừng** để kết thúc.

## 6. AI đang được tích hợp

- **Whisper**: chuyển giọng nói trong âm thanh thành văn bản tiếng Anh.
- **GPT**: dịch lời thoại sang tiếng Việt tự nhiên, có dùng tối đa 4 câu trước làm ngữ cảnh.
- **Text-to-Speech của trình duyệt**: đọc bản dịch tiếng Việt; giọng đọc phụ thuộc giọng tiếng Việt đã cài trên máy.

## 7. Lưu ý

- API key được giữ ở máy chủ, không gửi xuống mã giao diện.
- Việc dùng API có thể phát sinh chi phí theo mức giá và mức sử dụng của tài khoản API.
- Chrome/Edge trên máy tính thường hỗ trợ chia sẻ âm thanh tab tốt hơn các trình duyệt khác.
- Nếu không nghe được bản dịch, kiểm tra giọng tiếng Việt trong cài đặt hệ điều hành/trình duyệt.
- Máy chủ hiện chỉ lắng nghe tại `127.0.0.1`, phù hợp chạy trên máy cá nhân.
