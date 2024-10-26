CREATE TABLE m3u8infos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_ip VARCHAR(1024),
    ip_type VARCHAR(255),
    upload_time DATETIME,
    upload_path TEXT,
    file_name VARCHAR(10240),
    browser_ua TEXT,
    converted_path TEXT,
    m3u8_url TEXT
);