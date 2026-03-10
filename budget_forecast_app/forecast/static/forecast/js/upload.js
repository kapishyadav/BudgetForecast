const form = document.getElementById('uploadForm');
const loading = document.getElementById('loading');
const forecastTypeSelect = document.getElementById('forecast_type');
const accountNameWrapper = document.getElementById('account_name_wrapper');
const serviceNameWrapper = document.getElementById('service_name_wrapper');
const buCodeWrapper = document.getElementById('bu_code_wrapper');
const segmentNameWrapper = document.getElementById('segment_name_wrapper');

// Hide dropdowns initially
accountNameWrapper.style.display = 'none';
serviceNameWrapper.style.display = 'none';
buCodeWrapper.style.display = 'none';
segmentNameWrapper.style.display = 'none';

// Show/hide account & service inputs based on forecast type
forecastTypeSelect.addEventListener('change', function() {
    const type = this.value;

    accountNameWrapper.style.display = 'none';
    serviceNameWrapper.style.display = 'none';
    buCodeWrapper.style.display = 'none';
    segmentNameWrapper.style.display = 'none';

    if (type === 'account') {
        accountNameWrapper.style.display = 'block';
        serviceNameWrapper.style.display = 'none';
    } else if (type === 'service') {
        accountNameWrapper.style.display = 'block';
        serviceNameWrapper.style.display = 'block';
    } else if (type === 'bu_code') {
        buCodeWrapper.style.display = 'block';
    } else if (type === 'segment') {
        accountNameWrapper.style.display = 'block';
        serviceNameWrapper.style.display = 'block';
        segmentNameWrapper.style.display = 'block';
    }

    // Initialize Select2 when dropdown becomes visible
    initializeSelect2();
});

// Loading animation when form is submitted
form.addEventListener('submit', (e) => {
    loading.style.display = 'block';

    // Wait a short moment to ensure Django session is updated
    setTimeout(() => {
        initializeSelect2();
    }, 1500); // enough for session save
});

// --- Function to initialize Select2 dynamically ---
function initializeSelect2() {
    console.log("🔁 Initializing Select2 with latest file data...");

    // Destroy previous instances (to avoid duplicate bindings)
    if ($('#account_name').data('select2')) {
        $('#account_name').select2('destroy');
    }
    if ($('#service_name').data('select2')) {
        $('#service_name').select2('destroy');
    }
    if ($('#bu_code').data('select2')) {
        $('#bu_code').select2('destroy');
    }
    if ($('#segment_name').data('select2')) {
        $('#segment_name').select2('destroy');
    }

    // Initialize Select2 for Account Name
    $('#account_name').select2({
        placeholder: 'Search or select an account...',
        minimumInputLength: 1,
        width: '100%',
        ajax: {
            url: '/get_suggestions/',
            dataType: 'json',
            delay: 250,
            data: function (params) {
                return {
                    q: params.term,
                    field: 'account'
                };
            },
            processResults: function (data) {
                return {
                    results: (data.suggestions || []).map(item => ({ id: item, text: item }))
                };
            },
            cache: false
        }
    });

    // Initialize Select2 for Service Name
    $('#service_name').select2({
        placeholder: 'Search or select a service...',
        minimumInputLength: 1,
        width: '100%',
        ajax: {
            url: '/get_suggestions/',
            dataType: 'json',
            delay: 250,
            data: function (params) {
                return {
                    q: params.term,
                    field: 'service'
                };
            },
            processResults: function (data) {
                return {
                    results: (data.suggestions || []).map(item => ({ id: item, text: item }))
                };
            },
            cache: false
        }
    });

    // Initialize Select2 for BU Code
    $('#bu_code').select2({
        placeholder: 'Search or select a bu code...',
        minimumInputLength: 1,
        width: '100%',
        ajax: {
            url: '/get_suggestions/',
            dataType: 'json',
            delay: 250,
            data: function (params) {
                return {
                    q: params.term,
                    field: 'bu_code'
                };
            },
            processResults: function (data) {
                return {
                    results: (data.suggestions || []).map(item => ({ id: item, text: item }))
                };
            },
            cache: false
        }
    });

    // Initialize Select2 for Segment Name
    $('#segment_name').select2({
        placeholder: 'Search or select a segment...',
        minimumInputLength: 1,
        width: '100%',
        ajax: {
            url: '/get_suggestions/',
            dataType: 'json',
            delay: 250,
            data: function (params) {
                return {
                    q: params.term,
                    field: 'segment'
                };
            },
            processResults: function (data) {
                return {
                    results: (data.suggestions || []).map(item => ({ id: item, text: item }))
                };
            },
            cache: false
        }
    });
}