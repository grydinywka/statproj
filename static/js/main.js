function open_turnover() {
    $('#get_stat, .pg').click(function(event) {
        var form = $('form');

        form.ajaxForm({
//            'url': '/reports_stat/',
            'dataType': 'html',

            'beforeSend': function(xhr,setting) {
                $('#table1').empty();
                $('#table2').empty();
                $('#messages div').empty();
                $('#loader').show();

                $('input, select, button').attr('readonly', 'readonly');
			    $('input, select, button').attr('disabled', 'disabled');
                $('a').addClass('disabled');

                $('form *').removeClass('has-error');
                $('.help-block').empty();
                $('#nav').remove();
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
//                    $('form').load('/form/');
//                    $('form *').removeClass('has-error');
//                    $('.help-block').empty();
                    $('#table1').html(html.find('#table1').children());
                    $('#table2').html(html.find('#table2').children());
                    html.find('#nav').insertAfter("#table1");
                }
                load_more();

            }
        });
    });
}

function load_more() {
    $('.pg').click(function(event){
        var val1 = $(this).attr("value");

        event.preventDefault();
        $('a.pg').parent().removeClass('active');
        $(this).parent().addClass('active');
        $.ajax({
            'url': '/reports_stat/',
            'dataType': 'html',
            'type': 'post',
            'data': {
                'cat_num': val1,
                'date_from': $('form #date_from').val(),
                'date_to': $('form #date_to').val(),
                'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val(),
                'get_stat': true,
                'shops':  $('form #shops').val(),
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


                } else {
                    $('#messages div').empty();
                    $('#table1').html(html.find('#table1').children());
                    $('#table2').html(html.find('#table2').children());
                }
            },
            'beforeSend': function(xhr,setting) {
                $('#table1').empty();
                $('#table2').empty();
                $('#messages div').empty();
                $('#loader').show();

                $('input, select, button').attr('readonly', 'readonly');
			    $('input, select, button').attr('disabled', 'disabled');
                $('a').addClass('disabled');

                $('form *').removeClass('has-error');
                $('.help-block').empty();
            },
            'error': function(){
                $('input, select, button').attr('readonly', false);
			    $('input, select, button').attr('disabled', false);
                $('a').removeClass('disabled');
                $('#loader').hide();
                $('#messages div').html('<div class="alert alert-warning">Error on server!</div>');
                return false;
            }
        });
    });
}


$(document).ready(function() {
    open_turnover();
});