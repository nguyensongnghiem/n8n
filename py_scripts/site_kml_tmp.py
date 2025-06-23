import sys
import json
import os  # Để xử lý đường dẫn file

# Hàm tạo một placemark cho điểm
def create_point_placemark(site_name, lat, lon, description, icon_url, icon_scale):
	def format_coord(lon, lat):
		return f"{lon},{lat},0" # Altitude is 0 for points unless specified

	style_id = f"pointStyle_{site_name.replace(' ', '_').replace('.', '')}_{abs(int(lon*1000))}_{abs(int(lat*1000))}"
	style_kml = f"""
	<Style id="{style_id}">
	  <IconStyle>
		<scale>{icon_scale}</scale>
		<Icon>
		  <href>{icon_url}</href>
		</Icon>
	  </IconStyle>
	</Style>"""

	description_kml = f"<description>{description}</description>" if description else ""

	placemark_kml = f"""
	<Placemark>
	  <name>{site_name}</name>
	  {description_kml}
	  <styleUrl>#{style_id}</styleUrl>
	  <Point>
		<coordinates>
		  {format_coord(lon, lat)}
		</coordinates>
	  </Point>
	</Placemark>"""

	return style_kml, placemark_kml

# Hàm chính sửa đổi để đọc từ file và tạo điểm
def main(file_path="/tmp/site_kml_tmp.json"):
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

	# Xử lý dữ liệu n8n_input_items
	items_to_process = []
	if isinstance(n8n_input_items, list):
		items_to_process = n8n_input_items
	elif isinstance(n8n_input_items, dict) and "json" in n8n_input_items: # If it's a single item from n8n's rawData
		items_to_process = [n8n_input_items["json"]]
	elif isinstance(n8n_input_items, dict): # If it's a single direct dict
		items_to_process = [n8n_input_items]
	else:
		print(json.dumps({
			"kmlContent": "",
			"fileName": "error.kml",
			"message": "Định dạng dữ liệu trong file không hợp lệ."
		}), file=sys.stderr)
		sys.exit(1)

	all_styles = []
	grouped_placemarks = {}
	has_valid_data = False

	for i, item in enumerate(items_to_process):
		data_item = item
		
		try:
			required_keys = ["SiteName", "Latitude", "Longitude", "Icon"]
			if not all(key in data_item for key in required_keys):
				print(f"[LOG]: Lỗi: Thiếu khóa bắt buộc ({', '.join(required_keys)}) trong hàng {i}. Bỏ qua hàng. Dữ liệu: {json.dumps(data_item)}", file=sys.stderr)
				continue

			site_name = str(data_item["SiteName"])
			lat = float(data_item["Latitude"])
			lon = float(data_item["Longitude"])
			folder_name = str(data_item.get("FolderName", "")).strip()
			description = str(data_item.get("Description", "")).strip()
			icon_url = str(data_item["Icon"])
			icon_scale = float(data_item.get("IconScale", 1.0)) # Default scale is 1.0

			style_kml, placemark_kml = create_point_placemark(
				site_name, lat, lon, description, icon_url, icon_scale
			)
			
			all_styles.append(style_kml)
			
			if folder_name not in grouped_placemarks:
				grouped_placemarks[folder_name] = []
			grouped_placemarks[folder_name].append(placemark_kml)
			
			has_valid_data = True

		except ValueError as e:
			print(f"[LOG]: Lỗi: Không thể chuyển đổi dữ liệu số (hàng {i}). Chi tiết: {e}. Dữ liệu: {json.dumps(data_item)}", file=sys.stderr)
		except Exception as e:
			print(f"[LOG]: Đã xảy ra lỗi không mong muốn khi xử lý hàng {i}: {e}. Dữ liệu: {json.dumps(data_item)}", file=sys.stderr)

	if not has_valid_data:
		print(json.dumps({
			"kmlContent": "",
			"fileName": "empty_points.kml",
			"message": "No valid data found to generate KML."
		}), file=sys.stdout)
		return

	unique_styles = sorted(list(set(all_styles)))
	styles_combined = "".join(unique_styles)
	
	folder_and_root_content = []
	sorted_folders = sorted(grouped_placemarks.keys(), key=lambda x: (x == '', x))

	for folder in sorted_folders:
		placemarks_list = grouped_placemarks[folder]
		if folder:
			folder_content = "".join(placemarks_list)
			folder_kml = f"""
	<Folder>
	  <name>{folder}</name>
	  {folder_content}
	</Folder>"""
			folder_and_root_content.append(folder_kml)
		else:
			folder_and_root_content.extend(placemarks_list)
			
	placemarks_combined_in_folders = "".join(folder_and_root_content)

	full_kml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
	<name>Google Sheet KML Point Data with Folders and Descriptions</name>
	{styles_combined}
	{placemarks_combined_in_folders}
  </Document>
</kml>
"""
	
	# Trả về kết quả dưới dạng JSON ra stdout
	print(json.dumps({
		"kmlContent": full_kml_content,
		"fileName": "site_kml_tmp.kml",
		"pointCount": len(unique_styles)
	}))

# Khối main để chạy script
if __name__ == "__main__":
	main()