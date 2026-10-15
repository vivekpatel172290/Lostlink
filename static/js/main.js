// ==========================================================================
// LostLink - Coder Army Cyber Developer Logic
// Animated Dynamic Text, Drag & Drop Preview, Interactive Modals, Tabs
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
    // ----------------------------------------------------
    // 1. Dynamic Animated Text Rotator (Hero Headline)
    // ----------------------------------------------------
    const TxtRotate = function(el, toRotate, period) {
        this.toRotate = toRotate;
        this.el = el;
        this.loopNum = 0;
        this.period = parseInt(period, 10) || 2000;
        this.txt = '';
        this.tick();
        this.isDeleting = false;
    };

    TxtRotate.prototype.tick = function() {
        const i = this.loopNum % this.toRotate.length;
        const fullTxt = this.toRotate[i];

        if (this.isDeleting) {
            this.txt = fullTxt.substring(0, this.txt.length - 1);
        } else {
            this.txt = fullTxt.substring(0, this.txt.length + 1);
        }

        this.el.innerHTML = '<span class="wrap">' + this.txt + '</span>';

        let that = this;
        let delta = 150 - Math.random() * 50;

        if (this.isDeleting) { delta /= 2; }

        if (!this.isDeleting && this.txt === fullTxt) {
            delta = this.period;
            this.isDeleting = true;
        } else if (this.isDeleting && this.txt === '') {
            this.isDeleting = false;
            this.loopNum++;
            delta = 400;
        }

        setTimeout(function() {
            that.tick();
        }, delta);
    };

    const elements = document.getElementsByClassName('txt-rotate');
    for (let i = 0; i < elements.length; i++) {
        const toRotate = elements[i].getAttribute('data-rotate');
        const period = elements[i].getAttribute('data-period');
        if (toRotate) {
            new TxtRotate(elements[i], JSON.parse(toRotate), period);
        }
    }

    // ----------------------------------------------------
    // 2. Mobile Navigation Toggle
    // ----------------------------------------------------
    const mobileToggle = document.getElementById('mobileToggle');
    const navLinks = document.getElementById('navLinks');
    if (mobileToggle && navLinks) {
        mobileToggle.addEventListener('click', () => {
            navLinks.classList.toggle('show');
        });
    }

    // ----------------------------------------------------
    // 3. Flash Alert Dismissal
    // ----------------------------------------------------
    const alertCloses = document.querySelectorAll('.alert-close');
    alertCloses.forEach(btn => {
        btn.addEventListener('click', () => {
            const alert = btn.closest('.alert');
            if (alert) {
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 250);
            }
        });
    });

    // ----------------------------------------------------
    // 4. Image Drag & Drop and Instant Live Preview
    // ----------------------------------------------------
    const imageInput = document.getElementById('imageInput');
    const dropzone = document.getElementById('uploadDropzone');
    const previewWrapper = document.getElementById('previewWrapper');
    const previewImg = document.getElementById('previewImg');
    const removePreviewBtn = document.getElementById('removePreviewBtn');

    if (imageInput && dropzone) {
        ['dragenter', 'dragover'].forEach(name => {
            dropzone.addEventListener(name, (e) => {
                e.preventDefault();
                dropzone.classList.add('dragover');
            }, false);
        });

        ['dragleave', 'drop'].forEach(name => {
            dropzone.addEventListener(name, (e) => {
                e.preventDefault();
                dropzone.classList.remove('dragover');
            }, false);
        });

        dropzone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files && files.length > 0) {
                imageInput.files = files;
                showPreview(files[0]);
            }
        });

        imageInput.addEventListener('change', () => {
            if (imageInput.files && imageInput.files[0]) {
                showPreview(imageInput.files[0]);
            }
        });

        if (removePreviewBtn) {
            removePreviewBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                imageInput.value = '';
                previewWrapper.style.display = 'none';
                previewImg.src = '';
                dropzone.style.display = 'block';
            });
        }
    }

    function showPreview(file) {
        if (!file.type.startsWith('image/')) return;
        const reader = new FileReader();
        reader.onload = (e) => {
            previewImg.src = e.target.result;
            previewWrapper.style.display = 'block';
            dropzone.style.display = 'none';
        };
        reader.readAsDataURL(file);
    }

    // ----------------------------------------------------
    // 5. Protected Reporter Contact Reveal (PDF spec #15)
    // ----------------------------------------------------
    window.revealContact = function(btn) {
        const contactContent = document.getElementById('protectedContactContent');
        if (contactContent) {
            contactContent.style.display = 'block';
            btn.style.display = 'none';
        }
    };

    // ----------------------------------------------------
    // 6. Copy to Clipboard
    // ----------------------------------------------------
    window.copyToClipboard = function(text, btnElement) {
        navigator.clipboard.writeText(text).then(() => {
            const original = btnElement.innerHTML;
            btnElement.innerHTML = '✓ Copied!';
            btnElement.style.borderColor = '#00F2FE';
            btnElement.style.color = '#00F2FE';
            setTimeout(() => {
                btnElement.innerHTML = original;
                btnElement.style.borderColor = '';
                btnElement.style.color = '';
            }, 2000);
        }).catch(err => {
            console.error('Failed to copy: ', err);
        });
    };

    // ----------------------------------------------------
    // 7. Admin Tab Switcher
    // ----------------------------------------------------
    window.switchAdminTab = function(tabName, event) {
        const tabBtns = document.querySelectorAll('.admin-tab-btn');
        tabBtns.forEach(b => b.classList.remove('active'));
        if (event && event.target) {
            event.target.classList.add('active');
        }

        const tabPanels = document.querySelectorAll('.admin-tab-panel');
        tabPanels.forEach(p => p.style.display = 'none');

        const activePanel = document.getElementById(`panel-${tabName}`);
        if (activePanel) {
            activePanel.style.display = 'block';
        }
    };

    // ----------------------------------------------------
    // 8. Submit Form Loading State
    // ----------------------------------------------------
    const postForm = document.getElementById('reportItemForm');
    const submitBtn = document.getElementById('submitBtn');
    if (postForm && submitBtn) {
        postForm.addEventListener('submit', () => {
            submitBtn.disabled = true;
            submitBtn.innerHTML = `
                <svg style="animation: spin 1s linear infinite; display: inline-block; vertical-align: middle; margin-right: 8px;" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10" stroke-opacity="0.25"></circle>
                    <path d="M12 2a10 10 0 0 1 10 10"></path>
                </svg>
                Processing Embeddings...
            `;
        });
    }
});

// Loading spinner animation
const dynamicStyle = document.createElement("style");
dynamicStyle.innerText = `
@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
`;
document.head.appendChild(dynamicStyle);
