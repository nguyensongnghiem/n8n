# Đây là chuỗi của bạn, ví dụ từ một trường JSON hoặc bất kỳ nguồn nào
my_string_with_newlines = ""

# Tên file bạn muốn tạo
file_name = "converted.txt"

# Mở file ở chế độ ghi ('w') với encoding UTF-8 (để hỗ trợ tiếng Việt và nhiều ký tự khác)
try:
    with open(file_name, 'w', encoding='utf-8') as f:
        f.write(my_string_with_newlines)
    print(f"Đã ghi chuỗi vào '{file_name}' thành công.")
except Exception as e:
    print(f"Có lỗi xảy ra: {e}")