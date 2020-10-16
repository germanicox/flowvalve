$(document).ready(function() {
    $('form').on('submit', function(event) {
        $.ajax({
            data : {
                flow : $('#flow_input').val(), 
                unit : $('#flow_unit_input').val(),
            }, 
            type : 'POST', 
            url : '/process'
        })
        .done(function(data) {
            if (data.error){
                $('#errorAlert').text(data.error).show();
                $('#successAlert').hide()
            }
            else {
                $('#successAlert').text("GPM"+data.flow + " esto " + data.unit).show();
                $('#ResultMin').text("Cv: " + data.flow + " " + data.unit).show();
                $('#errorAlert').hide();
            }
        });
        event.preventDefault();
    });
});