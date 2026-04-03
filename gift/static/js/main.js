document.addEventListener('DOMContentLoaded', function() {
    var alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() { alert.style.display = 'none'; }, 5000);
    });
    var deleteBtns = document.querySelectorAll('.btn-danger');
    deleteBtns.forEach(function(btn) {
        if (btn.getAttribute('onclick') === null) {
            btn.addEventListener('click', function(e) {
                if (!confirm('Are you sure?')) e.preventDefault();
            });
        }
    });
});