document.addEventListener('DOMContentLoaded', () => {
        const form = document.getElementById('uploadForm');
        const progressContainer = document.getElementById('progress');
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');
        const statusDiv = document.getElementById('status');
        const resultContainer = document.getElementById('resultContainer');
        const fileInput = document.getElementById('fileInput');
        const uploadButton = document.querySelector('.upload-button');
        const exportButton = document.querySelector('.export-button');
        let allResults = []; // 用于存储所有结果

        // 设置年份为2019-当前年
        const currentYear = new Date().getFullYear();
        document.getElementById('year').textContent = `2019-${currentYear}`;

        fileInput.addEventListener('change', function() {
            const files = fileInput.files;
            if (files.length > 0) {
                statusDiv.innerHTML = `选择了 ${files.length} 个文件`;
                uploadButton.style.display = 'inline';
            } else {
                uploadButton.style.display = 'none';
            }
        });

        form.addEventListener('submit', function(event) {
            event.preventDefault();
            const files = fileInput.files;

            if (files.length === 0) {
                alert('请选择文件上传');
                return;
            }

            progressContainer.style.display = 'block';
            progressBar.style.width = '0%';
            statusDiv.innerHTML = '正在上传...';
            allResults = []; // 清空之前的结果

            let currentFileIndex = 0;
            const totalFiles = files.length;

            const uploadNextFile = () => {
                if (currentFileIndex >= totalFiles) {
                    statusDiv.innerHTML = '所有文件上传完成！';
                    exportButton.style.display = 'inline'; // 显示导出按钮
                    return;
                }

                const file = files[currentFileIndex];
                const formData = new FormData();
                formData.append('files', file);

                statusDiv.innerHTML = `${file.name} 正在上传，共${totalFiles}个文件，正在上传第${currentFileIndex + 1}个文件，剩余${totalFiles - currentFileIndex - 1}个文件`;

                const xhr = new XMLHttpRequest();
                xhr.open('POST', '/upload', true);

                xhr.upload.onprogress = function(event) {
                    if (event.lengthComputable) {
                        const percentComplete = Math.round((event.loaded / event.total) * 100);
                        progressBar.style.width = percentComplete + '%';
                        progressText.innerHTML = percentComplete + '%';
                    }
                };

                xhr.onload = function() {
                    if (xhr.status === 200) {
                        const result = JSON.parse(xhr.responseText);
                        const m3u8Url = result[0].url;
                        const resultItem = document.createElement('div');
                        resultItem.className = 'result-item';
                        resultItem.innerHTML = `${file.name}<br>M3U8文件链接：<span>${m3u8Url}</span>`;
                        const copyButton = document.createElement('button');
                        copyButton.className = 'copy-button';
                        copyButton.innerHTML = '复制';
                        copyButton.onclick = () => copyToClipboard(m3u8Url);
                        resultItem.appendChild(copyButton);
                        resultContainer.appendChild(resultItem);
                        allResults.push(`${file.name}: ${m3u8Url}`);
                    } else {
                        statusDiv.innerHTML = `上传失败：${xhr.statusText}`;
                    }
                    currentFileIndex++;
                    uploadNextFile();
                };

                xhr.onerror = function() {
                    statusDiv.innerHTML = `上传出错：${xhr.statusText}`;
                };

                xhr.send(formData);
            };

            uploadNextFile();
        });

        function copyToClipboard(text) {
            if (navigator.clipboard) {
                navigator.clipboard.writeText(text).then(() => {
                    alert('链接已复制到剪贴板！');
                }).catch(err => {
                    fallbackCopyToClipboard(text);
                });
            } else {
                fallbackCopyToClipboard(text);
            }
        }

        function fallbackCopyToClipboard(text) {
            const textArea = document.createElement("textarea");
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            try {
                document.execCommand("copy");
                alert('链接已复制到剪贴板！');
            } catch (err) {
                console.error('复制失败', err);
            }
            document.body.removeChild(textArea);
        }

        exportButton.addEventListener('click', function() {
            const blob = new Blob([allResults.join('\n')], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'results.txt';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        });

        const busuanzi_value_site_pv = document.getElementById("busuanzi_value_site_pv");
        const busuanziValue = window.busuanzi;
        if (busuanziValue && busuanziValue.site_pv) {
            busuanzi_value_site_pv.innerText = busuanziValue.site_pv;
        }
	});
