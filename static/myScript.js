
function getNextSong(callback){
    console.log(counter);
    $.ajax({
        url : '/getNextSong',
        data : {'count':counter},
        type : 'POST',
        success : callback,
        error : function(error){
            console.log(error)
        }
    });
    counter++;
}

$(document).ready(function(){

	$('#login-btn').click(function(){
		var email = $('#email').val();
		var password = $('#password').val();

		$.ajax({
            url: '/AuthenticateLogIn',
            data: {'email':email,'password':password},
            type: 'POST',
            success: function(response) {
                var resp = JSON.parse(response);
                if(resp.status=='success')
                    window.location.href = resp.message;
                else
                    alert(resp.message);
                console.log(response);
            },
            error: function(error) {
                var err = JSON.parse(error);
                alert(err.message);
                console.log(error);
            }
        }); 
	});

	$('#signup-btn').click(function(){
		var name = $('#_name').val();
		var email = $('#_email').val();
		var password = $('#_password').val();

		$.ajax({
            url: '/AuthenticateSignUp',
            data: {'name':name, 'email':email, 'password':password},
            type: 'POST',
            success: function(response) {
                var resp = JSON.parse(response);
                if(resp.status=='success')
                    window.location.href = resp.message;
                else
                    alert(resp.message);
                console.log(response);
            },
            error: function(error) {
                var err = JSON.parse(error);
                alert(err.message);
                console.log(error);
            }
        });
	});

    $('#logout-btn').click(function(){
        $.ajax({
            url: '/logout',
            data: {},
            type: 'POST',
            success: function(response){
                console.log(response);
                var resp = JSON.parse(response);
                if(resp.status=='success')
                    window.location.href = resp.message;
                else
                    alert(resp.message);
            },
            error: function(error){
                console.log(error);
                var err = JSON.parse(error);
                alert(err.message);
            }
        });
    });

    $('input').click(function(){
        var id = $(this).attr('id');
        var songId = id.slice(id.lastIndexOf('-')+1,id.length);
        var vote = id.slice(id.indexOf('-')+1, id.lastIndexOf('-'));
        console.log(id + ' '+ songId + ' ' + vote )
        if(!(isNaN(songId) || isNaN(vote) || id.slice(0,id.indexOf('-'))!='ip')){
            console.log('voted')
            $.ajax({
                url : '/vote',
                data : { 'songId' : songId, 'vote' : vote},
                type : 'POST',
                success : function(response){
                    var resp = JSON.parse(response)
                    if(resp.status == 'success')
                        window.location.href = resp.message;
                    else
                        alert(resp.message)
                    console.log(response);
                },
                error : function(error){
                    alert(JSON.parse(error).message)
                    console.log(error);
                }
            });
        }
    });


    $('#my-audio').on('ended', function(){
        getNextSong(function(response){
            var resp = JSON.parse(response);
            console.log(resp)
            $('#song-src').attr('src', '/uploads/'+resp);
            $('#song-playing').html('Now Playing : '+String(resp));
            $('#my-audio').trigger('play');
        });
    });

});