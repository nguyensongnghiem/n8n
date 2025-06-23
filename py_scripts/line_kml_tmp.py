import sys
import json
import os  # Để xử lý đường dẫn file

# Hàm tạo một placemark đơn lẻ (giữ nguyên)
def create_single_line_placemark(coord1, coord2, line_name, description, line_color, line_width):
    def format_coord(coord_tuple):
        lon = coord_tuple[0]
        lat = coord_tuple[1]
        alt = coord_tuple[2] if len(coord_tuple) > 2 else 0
        return f"{lon},{lat},{alt}"

    style_id = f"lineStyle_{line_name.replace(' ', '_').replace('.', '')}_{abs(int(coord1[0]*1000))}_{abs(int(coord1[1]*1000))}"
    style_kml = f"""
    <Style id="{style_id}">
      <LineStyle>
        <color>{line_color}</color>
        <width>{line_width}</width>
      </LineStyle>
    </Style>"""

    description_kml = f"<description>{description}</description>" if description else ""

    placemark_kml = f"""
    <Placemark>
      <name>{line_name}</name>
      {description_kml}
      <styleUrl>#{style_id}</styleUrl>
      <LineString>
        <coordinates>
          {format_coord(coord1)}
          {format_coord(coord2)}
        </coordinates>
      </LineString>
    </Placemark>"""

    return style_kml, placemark_kml

# Hàm chính sửa đổi để đọc từ file
def main(file_path="/tmp/output.json"):
    # Kiểm tra file tồn tại
    if not os.path.exists(file_path):
        print(json.dumps({
            "kmlContent": "",
            "fileName": "error.kml",
            "message": f"File {file_path} không tồn tại."
        }), file=sys.stderr)
        sys.exit(1)

    # Đọc dữ liệu từ file JSON
    try:
        with open(file_path, 'r') as file:
            n8n_input_items = json.load(file)[0]["rawData"]
            # print(n8n_input_items)  # In ra dữ liệu để kiểm tra
    except json.JSONDecodeError as e:
        print(json.dumps({
            "kmlContent": "",
            "fileName": "error.kml",
            "message": f"Lỗi parse JSON trong file {file_path}: {e}"
        }), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(json.dumps({
            "kmlContent": "",
            "fileName": "error.kml",
            "message": f"Lỗi khi đọc file {file_path}: {e}"
        }), file=sys.stderr)
        sys.exit(1)

    # Xử lý dữ liệu n8n_input_items (giống code gốc)
    items_to_process = []
    if isinstance(n8n_input_items, list):
        items_to_process = n8n_input_items
    elif isinstance(n8n_input_items, dict) and "json" in n8n_input_items:
        items_to_process = [n8n_input_items]
    else:
        print(json.dumps({
            "kmlContent": "",
            "fileName": "error.kml",
            "message": "Định dạng dữ liệu trong file không hợp lệ."
        }), file=sys.stderr)
        sys.exit(1)

    all_styles = []
    # Cấu trúc mới để hỗ trợ thư mục lồng nhau
    # Key: Tên thư mục cấp 1, Value: {'placemarks': [...], 'subfolders': {tên_thư_mục_cấp_2: [...]}}
    grouped_placemarks = {} 
    has_valid_data = False

    for i, item in enumerate(items_to_process):
        data_item = item
        
        try:
            required_keys = ["Longitude1", "Latitude1", "Longitude2", "Latitude2", "LineName", "Color", "Width"]
            if not all(key in data_item for key in required_keys):
                print(f"[LOG]: Lỗi: Thiếu khóa bắt buộc ({', '.join(required_keys)}) trong hàng {i}. Bỏ qua hàng. Dữ liệu: {json.dumps(data_item)}", file=sys.stderr)
                continue

            lon1 = float(data_item["Longitude1"])
            lat1 = float(data_item["Latitude1"])
            lon2 = float(data_item["Longitude2"])
            lat2 = float(data_item["Latitude2"])
            line_name = str(data_item["LineName"])
            folder_name = str(data_item.get("FolderName", "")).strip()
            second_folder_name = str(data_item.get("SecondFolderName", "")).strip() # Thêm thư mục cấp 2
            description = str(data_item.get("Description", "")).strip()
            line_color = str(data_item["Color"])
            line_width = int(data_item["Width"])

            coord1 = (lon1, lat1)
            coord2 = (lon2, lat2)
            
            style_kml, placemark_kml = create_single_line_placemark(
                coord1, coord2, line_name, description, line_color, line_width
            )
            
            all_styles.append(style_kml)
            
            # Logic nhóm mới cho 2 cấp thư mục
            if folder_name not in grouped_placemarks:
                grouped_placemarks[folder_name] = {'placemarks': [], 'subfolders': {}}
            
            if second_folder_name:
                if second_folder_name not in grouped_placemarks[folder_name]['subfolders']:
                    grouped_placemarks[folder_name]['subfolders'][second_folder_name] = []
                grouped_placemarks[folder_name]['subfolders'][second_folder_name].append(placemark_kml)
            else:
                grouped_placemarks[folder_name]['placemarks'].append(placemark_kml)
            
            has_valid_data = True

        except ValueError as e:
            print(f"[LOG]: Lỗi: Không thể chuyển đổi dữ liệu số (hàng {i}). Chi tiết: {e}. Dữ liệu: {json.dumps(data_item)}", file=sys.stderr)
        except Exception as e:
            print(f"[LOG]: Đã xảy ra lỗi không mong muốn khi xử lý hàng {i}: {e}. Dữ liệu: {json.dumps(data_item)}", file=sys.stderr)

    if not has_valid_data:
        print(json.dumps({
            "kmlContent": "",
            "fileName": "empty_lines.kml",
            "message": "No valid data found to generate KML."
        }), file=sys.stdout)
        return

    unique_styles = sorted(list(set(all_styles)))
    styles_combined = "".join(unique_styles)
    
    folder_and_root_content = []
    # Sắp xếp các thư mục cấp 1, đưa các mục ở gốc (key rỗng) xuống cuối
    sorted_folders_level1 = sorted(grouped_placemarks.keys(), key=lambda x: (x == '', x))

    for folder1_name in sorted_folders_level1:
        folder1_data = grouped_placemarks[folder1_name]
        placemarks_in_folder1 = folder1_data['placemarks']
        subfolders_data = folder1_data['subfolders']

        if folder1_name: # Nếu là một thư mục có tên, không phải gốc
            level1_content = []
            
            # Xử lý các thư mục con (cấp 2) trước
            sorted_folders_level2 = sorted(subfolders_data.keys())
            for folder2_name in sorted_folders_level2:
                placemarks_in_folder2 = subfolders_data[folder2_name]
                folder2_content = "".join(placemarks_in_folder2)
                folder2_kml = f"""
        <Folder>
          <name>{folder2_name}</name>
          {folder2_content}
        </Folder>"""
                level1_content.append(folder2_kml)
            
            # Thêm các placemark nằm trực tiếp trong thư mục cấp 1
            level1_content.extend(placemarks_in_folder1)

            final_level1_content = "".join(level1_content)
            folder1_kml = f"""
    <Folder>
      <name>{folder1_name}</name>
      {final_level1_content}
    </Folder>"""
            folder_and_root_content.append(folder1_kml)
        else: # Các placemark này nằm ở cấp gốc của Document
            folder_and_root_content.extend(placemarks_in_folder1)
            
    placemarks_combined_in_folders = "".join(folder_and_root_content)

    full_kml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Google Sheet KML Data with Folders and Descriptions</name>
    {styles_combined}
    {placemarks_combined_in_folders}
  </Document>
</kml>
"""
    
    # Trả về kết quả dưới dạng JSON ra stdout
    print(json.dumps({
        "kmlContent": full_kml_content,
        "fileName": "google_sheet_lines_with_folders_and_descriptions.kml",
        "lineCount": len(unique_styles)
    }))

# Khối main để chạy script
if __name__ == "__main__":
    main()  # Gọi hàm main với đường dẫn file mặc định