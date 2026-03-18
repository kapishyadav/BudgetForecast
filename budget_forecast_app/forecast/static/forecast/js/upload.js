
document.addEventListener('DOMContentLoaded', function() {
    const forecastTypeSelect = document.getElementById('forecast_type');
    const accountNameWrapper = document.getElementById('account_name_wrapper');
    const serviceNameWrapper = document.getElementById('service_name_wrapper');
    const buCodeWrapper = document.getElementById('bu_code_wrapper');
    const segmentNameWrapper = document.getElementById('segment_name_wrapper');

    // Hide dropdowns initially (Only if the elements exist on the page)
    if (accountNameWrapper) accountNameWrapper.style.display = 'none';
    if (serviceNameWrapper) serviceNameWrapper.style.display = 'none';
    if (buCodeWrapper) buCodeWrapper.style.display = 'none';
    if (segmentNameWrapper) segmentNameWrapper.style.display = 'none';

    // Show/hide account & service inputs based on forecast type
    if (forecastTypeSelect) {
        forecastTypeSelect.addEventListener('change', function() {
            const type = this.value;

            // Reset all to none first
            accountNameWrapper.style.display = 'none';
            serviceNameWrapper.style.display = 'none';
            buCodeWrapper.style.display = 'none';
            segmentNameWrapper.style.display = 'none';

            if (type === 'account') {
                accountNameWrapper.style.display = 'block';
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

            // Initialize Select2 when a dropdown becomes visible
            initializeSelect2();
        });
    }

// ==========================================
// UX ENHANCEMENTS: Clickable Wrappers & Auto-Focus (FIXED)
// ==========================================

    // 1. Make the whole wrapper clickable
    $('.custom-select-wrapper').on('click', function(e) {
        let $select = $(this).find('select');

        // Check if Select2 is actually initialized before trying to open it
        if ($select.hasClass('select2-hidden-accessible')) {

            // If the user clicked the text label, stop the browser from fighting us
            if (e.target.tagName.toLowerCase() === 'label') {
                e.preventDefault();
            }

            // Open Select2 if they clicked the wrapper whitespace (not the box itself)
            if (!$(e.target).closest('.select2-container').length) {
                $select.select2('open');
            }
        }
    });

    // 2. Force the blinking cursor into the search box
    $(document).on('select2:open', function() {
        // Increased timeout slightly to wait for the Select2 open animation to finish
        setTimeout(function() {
            // Target ONLY the search field belonging to the actively opened dropdown
            let searchField = document.querySelector('.select2-container--open .select2-search__field');
            if (searchField) {
                searchField.focus();
            }
        }, 100);
    });

// ==========================================
// CORE LOGIC: Initialize Select2 dynamically
// ==========================================
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
        placeholder: 'Search or select a BU code...',
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
