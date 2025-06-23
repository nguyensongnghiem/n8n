import textfsm
import io

# 1. Đầu ra (CLI Output) từ thiết bị mạng
cli_output = """
Interface              IP-Address      OK? Method Status                Protocol
GigabitEthernet0/0     192.168.1.1     YES manual up                    up
GigabitEthernet0/1     unassigned      YES unset  administratively down down
Loopback0              10.0.0.1        YES manual up                    up
Vlan1                  172.16.0.1      YES manual up                    up
"""

# 2. Template TextFSM dưới dạng chuỗi (string)
# Lưu ý: Các ký tự xuống dòng (\n) là quan trọng để template được định dạng đúng.
template_string = """
Value Interface (\\S+)
Value IP_Address (\\S+)
Value Status (up|down|administratively down)
Value Protocol (up|down)

Start
  ^Interface.*
  ^${Interface}\\s+${IP_Address}\\s+\\S+\\s+\\S+\\s+(${Status})\\s+(${Protocol}) -> Record
"""

# 3. Chạy TextFSM
try:
    # Sử dụng io.StringIO để biến chuỗi template thành một đối tượng giống file
    # mà TextFSM có thể đọc.
    template_file_like_object = io.StringIO(template_string)

    # Khởi tạo đối tượng TextFSM parser
    # TextFSM có thể nhận đối tượng giống file này
    re_table = textfsm.TextFSM(template_file_like_object)

    # Phân tích cú pháp output
    fsm_results = re_table.ParseText(cli_output)

    # Lấy tên các cột (header) từ template
    header = re_table.header

    print("Header (Tên cột):", header)
    print("\nKết quả phân tích (dạng list of lists):")
    for row in fsm_results:
        print(row)

    # Chuyển đổi thành list of dictionaries để dễ sử dụng hơn
    parsed_data = []
    for row in fsm_results:
        row_dict = dict(zip(header, row))
        parsed_data.append(row_dict)

    print("\nKết quả phân tích (dạng list of dictionaries):")
    for item in parsed_data:
        print(item)

except textfsm.TextFSMTemplateError as e:
    print(f"Lỗi template TextFSM: {e}")
except Exception as e:
    print(f"Đã xảy ra lỗi: {e}")