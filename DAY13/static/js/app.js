document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('file-input');
    const dropzonePrompt = document.getElementById('dropzone-prompt');
    const previewContainer = document.getElementById('preview-container');
    const previewImg = document.getElementById('preview-img');
    const previewVideo = document.getElementById('preview-video');
    const previewFallback = document.getElementById('preview-fallback');
    const fallbackFilename = document.getElementById('fallback-filename');
    const clearBtn = document.getElementById('clear-btn');
    const analyzeBtn = document.getElementById('analyze-btn');
    const loaderOverlay = document.getElementById('loader-overlay');
    const loaderStatus = document.getElementById('loader-status');
    const resultsPanel = document.getElementById('results-panel');
    
    // Results DOM Elements
    const recommendationBanner = document.getElementById('recommendation-banner');
    const bannerActionTitle = document.getElementById('banner-action-title');
    const bannerAction = document.getElementById('banner-action');
    const bannerDesc = document.getElementById('banner-desc');
    const gaugeFillCircle = document.getElementById('gauge-fill-circle');
    const gaugePct = document.getElementById('gauge-pct');
    const healthyFramesVal = document.getElementById('healthy-frames-val');
    const anomalyFramesVal = document.getElementById('anomaly-frames-val');
    const machineTypeVal = document.getElementById('machine-type-val');
    const machineTypeIcon = document.getElementById('machine-type-icon');
    const classBreakdownContainer = document.getElementById('class-breakdown-container');
    const asciiConsole = document.getElementById('ascii-console');
    const copyReportBtn = document.getElementById('copy-report-btn');

    let selectedFile = null;
    let statusInterval = null;

    // Drag and Drop Event Listeners
    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove('dragover');
        }, false);
    });

    dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            handleFileSelect(files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });

    // Handle selected file validation and preview
    function handleFileSelect(file) {
        // Validate is image or video (using MIME type and file extension fallback)
        const filename = file.name.toLowerCase();
        const isImage = file.type.startsWith('image/') || 
                        filename.endsWith('.png') || 
                        filename.endsWith('.jpg') || 
                        filename.endsWith('.jpeg') || 
                        filename.endsWith('.webp') || 
                        filename.endsWith('.bmp');
        
        const isVideo = file.type.startsWith('video/') || 
                        filename.endsWith('.mp4') || 
                        filename.endsWith('.avi') || 
                        filename.endsWith('.mov') || 
                        filename.endsWith('.mkv') || 
                        filename.endsWith('.webm');

        if (!isImage && !isVideo) {
            alert('Invalid file format. Please upload a valid image or video file.');
            return;
        }

        selectedFile = file;
        
        // Hide dropzone prompt, show preview container
        dropzone.style.display = 'none';
        previewContainer.style.display = 'block';
        previewFallback.style.display = 'none';
        clearBtn.style.display = 'inline-flex';
        analyzeBtn.removeAttribute('disabled');

        // Render preview
        const objectURL = URL.createObjectURL(file);
        if (isImage) {
            previewVideo.style.display = 'none';
            previewVideo.pause();
            previewVideo.src = '';
            
            previewImg.src = objectURL;
            previewImg.style.display = 'block';
        } else {
            previewImg.style.display = 'none';
            previewImg.src = '';
            
            // Handle browser media loading issues (like missing codecs or bad MIME type serving)
            previewVideo.onerror = () => {
                previewVideo.style.display = 'none';
                previewFallback.style.display = 'flex';
                fallbackFilename.innerText = file.name;
            };
            
            previewVideo.src = objectURL;
            previewVideo.style.display = 'block';
            previewVideo.load();
        }
    }

    // Clear and Reset View
    clearBtn.addEventListener('click', () => {
        resetUI();
    });

    function resetUI() {
        selectedFile = null;
        fileInput.value = '';
        
        previewImg.style.display = 'none';
        previewImg.src = '';
        
        previewVideo.pause();
        previewVideo.style.display = 'none';
        previewVideo.src = '';
        
        previewFallback.style.display = 'none';
        fallbackFilename.innerText = '';
        
        previewContainer.style.display = 'none';
        dropzone.style.display = 'flex';
        clearBtn.style.display = 'none';
        analyzeBtn.setAttribute('disabled', 'true');
        resultsPanel.classList.add('results-hidden');
        
        if (statusInterval) {
            clearInterval(statusInterval);
        }
    }

    // Dynamic processing loading text rotation
    function startLoaderTextAnimation() {
        const statuses = [
            "Uploading media payload...",
            "Loading YOLO weights pipeline...",
            "Decoding video codecs & channels...",
            "Iterating frame matrices (10-step sync)...",
            "Evaluating CNN features for anomalies...",
            "Collating machine classification health scores...",
            "Compiling final prediction audit report..."
        ];
        
        let idx = 0;
        loaderStatus.innerText = statuses[idx];
        
        statusInterval = setInterval(() => {
            idx = (idx + 1) % statuses.length;
            loaderStatus.innerText = statuses[idx];
        }, 2200);
    }

    // Run Health Analysis API Call
    analyzeBtn.addEventListener('click', () => {
        if (!selectedFile) return;

        const formData = new FormData();
        formData.append('file', selectedFile);

        // Show Loader Overlay
        loaderOverlay.style.display = 'flex';
        startLoaderTextAnimation();

        fetch('http://127.0.0.1:5000/predict', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.error || 'Server error occurred'); });
            }
            return response.json();
        })
        .then(data => {
            displayResults(data);
        })
        .catch(err => {
            console.error(err);
            alert(`Error: ${err.message}`);
        })
        .finally(() => {
            // Hide Loader
            loaderOverlay.style.display = 'none';
            if (statusInterval) {
                clearInterval(statusInterval);
            }
        });
    });

    // Populate Results on UI
    function displayResults(data) {
        // Show Results Panel
        resultsPanel.classList.remove('results-hidden');

        // Scroll to results panel
        resultsPanel.scrollIntoView({ behavior: 'smooth' });

        // Update Recommendation Banner
        recommendationBanner.className = 'recommendation-banner'; // Reset
        recommendationBanner.classList.add(`banner-${data.ui_theme}`);
        
        bannerActionTitle.className = 'banner-action-title'; // Reset
        bannerActionTitle.classList.add(data.ui_theme);
        
        bannerAction.innerText = data.recommendation;
        bannerDesc.innerText = data.status_desc;

        // Circular Health Gauge Animation
        // Circumference is 2 * PI * r (for r=50 it is ~314.159)
        const circumference = 314.159;
        const pct = data.health_score;
        const offset = circumference - (pct / 100) * circumference;
        
        // CSS Transition handles the animation of strokeDashoffset
        gaugeFillCircle.style.strokeDashoffset = offset;
        gaugePct.innerText = `${pct.toFixed(1)}%`;
        
        // Set gauge color based on state
        if (data.ui_theme === 'success') {
            gaugeFillCircle.style.stroke = 'var(--color-success)';
        } else if (data.ui_theme === 'warning') {
            gaugeFillCircle.style.stroke = 'var(--color-warning)';
        } else {
            gaugeFillCircle.style.stroke = 'var(--color-danger)';
        }

        // Update frames count details
        healthyFramesVal.innerText = data.healthy_frames;
        anomalyFramesVal.innerText = data.anomaly_frames;

        // Update Detected Machine Details
        machineTypeVal.innerText = data.machine_type;
        
        if (data.machine_type.toLowerCase().includes('cnc')) {
            machineTypeIcon.className = 'fa-solid fa-industry';
        } else {
            machineTypeIcon.className = 'fa-solid fa-soap';
        }

        // Render YOLO class breakdown distribution progress bars
        classBreakdownContainer.innerHTML = '';
        
        // Find maximum frame count to scale percentages properly
        const maxVal = Math.max(...Object.values(data.class_breakdown), 1);
        const totalFrames = Object.values(data.class_breakdown).reduce((sum, v) => sum + v, 0);

        Object.entries(data.class_breakdown).forEach(([className, count]) => {
            const percentage = totalFrames > 0 ? (count / totalFrames) * 100 : 0;
            const isAnomaly = className.toLowerCase().includes('anomoly') || className.toLowerCase().includes('anomaly');
            
            const itemHTML = `
                <div class="breakdown-item">
                    <div class="breakdown-header">
                        <span class="breakdown-name">${className.replace('_', ' ')}</span>
                        <span class="breakdown-count">${count} frame${count !== 1 ? 's' : ''} (${percentage.toFixed(1)}%)</span>
                    </div>
                    <div class="breakdown-bar-bg">
                        <div class="breakdown-bar-fill ${isAnomaly ? 'anomaly' : ''}" style="width: ${percentage}%"></div>
                    </div>
                </div>
            `;
            classBreakdownContainer.insertAdjacentHTML('beforeend', itemHTML);
        });

        // Set the exact ASCII Report matching the user's requirement
        asciiConsole.innerText = data.ascii_report;

        // Clipboard Copy Action Handler
        copyReportBtn.onclick = () => {
            navigator.clipboard.writeText(data.ascii_report).then(() => {
                const originalHTML = copyReportBtn.innerHTML;
                copyReportBtn.innerHTML = `<i class="fa-solid fa-check"></i> Copied!`;
                copyReportBtn.style.color = 'var(--color-success)';
                copyReportBtn.style.borderColor = 'var(--color-success)';
                
                setTimeout(() => {
                    copyReportBtn.innerHTML = originalHTML;
                    copyReportBtn.style.color = '';
                    copyReportBtn.style.borderColor = '';
                }, 2000);
            }).catch(e => {
                console.error("Could not copy text to clipboard: ", e);
            });
        };
    }
});
