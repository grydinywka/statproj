function open_turnover() {
    $('#get_stat').click(function(event) {
        var form = $('form');

        form.ajaxForm({
            'dataType': 'html',
            'beforeSend': function(xhr,setting) {
                $('#table1').empty();
                $('#messages div').empty();
            },
            'error': function(){
                $('#table1').empty();
                $('#messages div').html('<div class="alert alert-warning">Error on server!</div>');
                return false;
            },
            'success': function(data, status, xhr) {
                var html = $(data), newform = html.find('form');

                if ( newform.length > 0 ) {
                    $('#messages div').html(html.find('#messages .alert'));
                    $('form').html(newform);

                    open_turnover();
                } else {
                    $('#messages div').empty();
                    $('form').load('/form/');
                    $('#table1').html(html.find('#table1').children());
                    $('#table2').html(html.find('#table2').children());
                }
            }
        });
    });
}


$(document).ready(function() {
    open_turnover();
});