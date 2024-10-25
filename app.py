import os
import random
import string
from flask import Flask, request, jsonify, send_file
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import ipaddress
import subprocess
import time
import sys

app = Flask(__name__)
UPLOAD_FOLDER = '/www/qiepian/uploads'  # 上传目录
OUTPUT_FOLDER = '/www/qiepian/output'    # 输出目录
BASE_URL = 'http://abc.com:9630'         # 你的域名或IP

# 数据库连接设置
db_config = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'password',
    'database': 'm3u8info',
    'port': '3306'
}

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'.mp4', '.mp3', '.wav', '.avi', '.mov', '.ogg', '.flac', '.flv'}

# 随机生成文件名
def random_string(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# 启动时检测数据库连接
def check_db_connection_on_start():
    try:
        conn = mysql.connector.connect(**db_config)
        if conn.is_connected():
            conn.close()
            print("数据库连接成功，程序启动中...")
            return True
        else:
            raise Exception("无法连接到数据库")
    except Error as e:
        print(f"与数据库通信失败，请检查数据库信息是否正确，数据库是否正常运行。错误详情: {e}")
        sys.exit(1)  # 停止程序运行

# 检查文件扩展名
def allowed_file(filename):
    return '.' in filename and os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS

# 保存转换信息到数据库
def save_to_db(client_ip, ip_type, upload_path, filename, user_agent, output_path, m3u8_url):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        query = """INSERT INTO m3u8infos (client_ip, ip_type, upload_time, upload_path, file_name, browser_ua, converted_path, m3u8_url)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
        data = (client_ip, ip_type, datetime.now(), upload_path, filename, user_agent, output_path, m3u8_url)
        cursor.execute(query, data)
        conn.commit()
        cursor.close()
        conn.close()
    except Error as e:
        print(f"无法写入数据库，请检查数据库是否指向正确或权限是否足够。错误详情: {e}")
        raise Exception("数据库插入失败，程序中断")

# 接收上传文件
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'files' not in request.files:
        return jsonify({'error': '没有文件上传'}), 400

    files = request.files.getlist('files')
    if not files:
        return jsonify({'error': '文件列表为空'}), 400

    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    # 确定 IP 类型
    ip_type = 'IPv6' if ipaddress.ip_address(client_ip).version == 6 else 'IPv4'
    
    user_agent = request.headers.get('User-Agent')

    results = []
    for file in files:
        if file and file.filename:  # 检查文件是否存在且有文件名
            # 检查文件类型
            if not allowed_file(file.filename):
                return jsonify({'error': f'不支持的文件格式: {file.filename}'}), 400
            
            # 重命名文件，添加两个时间戳防止覆盖
            filename = file.filename
            timestamp_formatted = datetime.now().strftime('%Y%m%d_%H%M%S')
            unix_timestamp = str(int(time.time()))
            filename_with_timestamps = f"{os.path.splitext(filename)[0]}_{timestamp_formatted}_{unix_timestamp}{os.path.splitext(filename)[1]}"
            file_path = os.path.join(UPLOAD_FOLDER, filename_with_timestamps)
            file.save(file_path)

            # 随机生成输出名称
            output_name = random_string()
            output_path = os.path.join(OUTPUT_FOLDER, output_name)
            os.makedirs(output_path, exist_ok=True)

            # 根据文件格式选择FFmpeg命令
            if file.filename.endswith(('.mp4', '.avi', '.mov', '.flv')):  # 视频文件处理
                ffmpeg_cmd = f"ffmpeg -i '{file_path}' -codec: copy -start_number 0 -hls_time 5 -hls_list_size 0 -f hls '{output_path}/{output_name}.m3u8'"
            elif file.filename.endswith(('.mp3', '.wav', '.ogg', '.flac')):  # 音频文件处理
                ffmpeg_cmd = f"ffmpeg -i '{file_path}' -c:a aac -b:a 128k -f hls -hls_time 1 -hls_list_size 0 -hls_segment_filename '{output_path}/{output_name}_%03d.ts' '{output_path}/{output_name}.m3u8'"

            # 执行FFmpeg命令
            try:
                subprocess.run(ffmpeg_cmd, shell=True, check=True)
            except subprocess.CalledProcessError as e:
                print(f"FFmpeg 处理错误: {e}")
                continue

            # 返回M3U8的URL
            m3u8_url = f"{BASE_URL}/{output_name}/{output_name}.m3u8"
            results.append({'filename': filename_with_timestamps, 'url': m3u8_url})

            # 保存转换信息到数据库，包括上传路径
            try:
                save_to_db(client_ip, ip_type, file_path, filename_with_timestamps, user_agent, output_path, m3u8_url)
            except Exception as db_err:
                return jsonify({'error': str(db_err)}), 500

    return jsonify(results)

# 导出URL为TXT文件
@app.route('/export', methods=['GET'])
def export_urls():
    urls_file_path = os.path.join(OUTPUT_FOLDER, 'urls.txt')
    try:
        with open(urls_file_path, 'w') as f:
            for result in results:
                f.write(f"{result['filename']}\nM3U8文件链接：{result['url']}\n\n")
        
        return send_file(urls_file_path, as_attachment=True, attachment_filename='urls.txt')
    except Exception as e:
        return jsonify({'error': f'导出失败: {e}'}), 500

if __name__ == '__main__':
    # 在应用启动前进行数据库连接检测
    if check_db_connection_on_start():
        app.run(host='0.0.0.0', port=7788)