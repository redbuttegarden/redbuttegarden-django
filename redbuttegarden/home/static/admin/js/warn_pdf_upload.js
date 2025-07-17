document.addEventListener('DOMContentLoaded', () => {
    console.log('✅ Script loaded, waiting for uploader...');

    const waitForUploader = () => {
        const fileUploadEl = document.querySelector('#fileupload');
        if (!fileUploadEl) {
            console.log('⏳ Waiting for #fileupload element...');
            return setTimeout(waitForUploader, 100);
        }

        const $el = window.jQuery && window.jQuery(fileUploadEl);
        const uploader = $el && $el.data('blueimp-fileupload') || $el && $el.data('fileupload');

        if (!uploader) {
            console.log('⏳ Waiting for uploader initialization...');
            return setTimeout(waitForUploader, 100);
        }

        if (uploader._pdfOverrideApplied) {
            console.log('⚠️ Override already applied.');
            return;
        }

        uploader._pdfOverrideApplied = true;

        const originalAdd = uploader.options.add;

        uploader.options.add = function (e, data) {
            const file = data.files[0];
            console.log('📄 Intercepted file:', file);

            if (file && file.type === 'application/pdf') {
                Swal.fire({
                    title: 'Is Your PDF Accessible?',
                    html: '<p>PDF documents are not accessible by default. It is your responsibility to ensure PDF documents shared on the website are accessible to all users.</p><p>Consider creating the content within Wagtail rather than uploading a PDF. For information on making PDFs accessible please refer to <a href="https://intranet.redbutte.utah.edu/staff-info/accessibility-considerations-for-pdf-documents/" title="PDF Accessibility Considerations">this intranet article</a>.</p><p>If you are sure the PDF document you are uploading is already accessible, click "Yes" to continue uploading.</p>',
                    icon: 'warning',
                    showCancelButton: true,
                    confirmButtonText: 'Yes, upload it',
                    cancelButtonText: 'Cancel'
                }).then((result) => {
                    if (result.isConfirmed) {
                        originalAdd.call(this, e, data);
                    } else {
                        console.log('🚫 PDF upload canceled by user.');
                    }
                });
            } else {
                originalAdd.call(this, e, data);
            }
        };

        console.log('✅ PDF upload override applied.');
    };

    waitForUploader();
});
