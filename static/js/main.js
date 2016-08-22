function open_turnover() {
    $('#get_stat').click(function(event) {
        var form = $('form');

        form.ajaxForm({
            'dataType': 'html',
            'beforeSend': function(xhr,setting) {
                $('#table1').empty();
                $('#table2').empty();
                $('#messages div').empty();
                $('#loader').show();

                $('input, select, button').attr('readonly', 'readonly');
			    $('input, select, button').attr('disabled', 'disabled');
                $('a').addClass('disabled');
            },
            'error': function(){
//                $('#table1').empty();
                $('input, select, button').attr('readonly', false);
			    $('input, select, button').attr('disabled', false);
                $('a').removeClass('disabled');
                $('#loader').hide();
                $('#messages div').html('<div class="alert alert-warning">Error on server!</div>');
                return false;
            },
            'success': function(data, status, xhr) {
                var html = $(data), newform = html.find('form');

                $('input, select, button').attr('readonly', false);
			    $('input, select, button').attr('disabled', false);
			    $('a').removeClass('disabled');

                $('#loader').hide();
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