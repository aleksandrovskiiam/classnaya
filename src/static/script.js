$(document).ready(function(){
    $('#67').on('submit',function(e){
        e.preventDefault();
        err = 0;
        if ($('#fullname').val().trim() === '' || $('#password').val().trim() != $('#confirm_password').val().trim()){
            err = 1;
            alert('paroli ne sovpadayut');
        }else{
            err = 0;
        }
        if (err == 0){
            $.ajax({
                url: '/user_register',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({
                    name: $('#fullname').val(),
                    password: $('#password').val(),
                    email: $('#email').val()
                }),
                success: function(){
                    window.location = '/balance';
                },
                error: function(xhr){
                    alert(xhr.responseText);
                }
            })
        }
    })

    $('#login').on('submit',function(e){
        e.preventDefault();
        $.ajax({
            url: '/user_login',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                email: $('#username').val(),
                password: $('#password').val()
            }),
            success: function(){
                window.location = '/balance';
            },
            error: function(xhr){
                alert(xhr.responseText);
            }
        })
    })

    $('#topup').on('submit',function(e){
        e.preventDefault();
        $.ajax({
            url: '/topup',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                amount: $('#amount').val()
            }),
            success: function(res){
                $('#balance').text(res.balance);
                $('#amount').val('');
            },
            error: function(xhr){
                alert(xhr.responseText);
            }
        })
    })
})