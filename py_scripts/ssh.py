from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoAuthenticationException, NetmikoTimeoutException
import sys
import json
import argparse

def ssh_to_router_with_netmiko(device_type, hostname, username, password, command, port=22, timeout=10):
    """
    Kết nối SSH tới một thiết bị router bằng Netmiko và thực hiện một câu lệnh.

    Args:
        device_type (str): Kiểu thiết bị (ví dụ: 'juniper', 'cisco_ios', 'arista_eos', v.v.).
                           Tham khảo tài liệu Netmiko để biết danh sách đầy đủ.
        hostname (str): Địa chỉ IP hoặc hostname của router.
        username (str): Tên người dùng SSH.
        password (str): Mật khẩu SSH.
        command (str): Câu lệnh CLI cần thực hiện.
        port (int): Cổng SSH (mặc định là 22).
        timeout (int): Thời gian chờ kết nối (mặc định là 10 giây).

    Returns:
        dict: Một từ điển chứa kết quả (output), lỗi (error) và trạng thái thành công/thất bại.
              Ví dụ: {'success': True, 'output': '...', 'error': None}
    """
    device_params = {
        'device_type': device_type,
        'host': hostname,
        'username': username,
        'password': password,
        'port': port,
        'timeout': timeout,      
        'global_delay_factor': 2 # Tăng độ trễ giữa các lệnh nếu thiết bị chậm phản hồi
    }

    try:
        # Tạo đối tượng kết nối
        with ConnectHandler(**device_params) as net_connect:
            # Chạy lệnh và lấy kết quả
            output = net_connect.send_command(command,read_timeout= 120)
            return {'success': True, 'output': output.strip(), 'error': None}

    except NetmikoAuthenticationException:
        return {'success': False, 'output': None, 'error': "Lỗi xác thực: Tên người dùng hoặc mật khẩu không đúng."}
    except NetmikoTimeoutException:
        return {'success': False, 'output': None, 'error': "Lỗi timeout: Không thể kết nối hoặc thiết bị không phản hồi."}
    except Exception as e:
        # Bắt các lỗi chung khác
        return {'success': False, 'output': None, 'error': f"Đã xảy ra lỗi không mong muốn: {e}"}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ứng dụng Python SSH dùng Netmiko để chạy lệnh trên thiết bị router.")
    parser.add_argument('--device_type', required=True, help='Kiểu thiết bị Netmiko (ví dụ: juniper, cisco_ios).')
    parser.add_argument('--ip', required=True, help='Địa chỉ IP hoặc hostname của router.')
    parser.add_argument('--user', required=True, help='Tên người dùng SSH.')
    parser.add_argument('--password', required=True, help='Mật khẩu SSH.')
    parser.add_argument('--command', required=True, help='Câu lệnh CLI cần thực hiện trên router (đặt trong dấu ngoặc kép nếu có khoảng trắng).')
    parser.add_argument('--port', type=int, default=22, help='Cổng SSH (mặc định: 22).')
    parser.add_argument('--timeout', type=int, default=10, help='Thời gian chờ kết nối SSH (mặc định: 10 giây).')

    args = parser.parse_args()

    # Gọi hàm Netmiko chính
    result = ssh_to_router_with_netmiko(
        device_type=args.device_type,
        hostname=args.ip,
        username=args.user,
        password=args.password,
        command=args.command,
        port=args.port,
        timeout=args.timeout
    )

    # In kết quả ra console dưới dạng JSON
    print(json.dumps(result, indent=2))

    # Nếu có lỗi, thoát với mã lỗi khác 0
    if not result.get('success'):
        sys.exit(1)