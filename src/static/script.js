$(document).ready(function(){

    // ==================== РЕГИСТРАЦИЯ ====================
    $('#67').on('submit', function(e){
        e.preventDefault();
        let err = 0;
        if ($('#fullname').val().trim() === '' ||
            $('#password').val().trim() !== $('#confirm_password').val().trim()){
            err = 1;
            alert('paroli ne sovpadayut');
        }
        if (err === 0){
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
                    window.location = '/ai_chat';
                },
                error: function(xhr){
                    alert(xhr.responseText);
                }
            });
        }
    });

    // ==================== ЛОГИН ====================
    $('#login').on('submit', function(e){
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
                window.location = '/ai_chat';
            },
            error: function(xhr){
                alert(xhr.responseText);
            }
        });
    });

    // ==================== ПОПОЛНЕНИЕ ====================
    $('#topup').on('submit', function(e){
        e.preventDefault();
        $.ajax({
            url: '/topup',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ amount: $('#amount').val() }),
            success: function(res){
                $('#balance').text(res.balance);
                $('#amount').val('');
            },
            error: function(xhr){
                alert(xhr.responseText);
            }
        });
    });

    // ==================== AI-ЧАТ ====================
    const chatHistory = [];

    function appendMsg(role, text){
        const $log = $('#chat_log');
        if (!$log.length) return null;
        const $msg = $('<div>').addClass('msg ' + role).text(text);
        $log.append($msg);
        $log.scrollTop($log[0].scrollHeight);
        return $msg;
    }

    $('#ai_form').on('submit', function(e){
        e.preventDefault();
        const prompt = $('#ai_prompt').val().trim();
        if (!prompt) return;

        appendMsg('user', prompt);
        chatHistory.push({ role: 'user', content: prompt });
        $('#ai_prompt').val('');
        $('#ai_send').prop('disabled', true);

        const $thinking = appendMsg('assistant', 'Думаю...');

        $.ajax({
            url: '/ai_suggest',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ prompt: prompt, history: chatHistory.slice(0, -1) }),
            success: function(res){
                const answer = res.answer || '';
                $thinking.text(answer);
                chatHistory.push({ role: 'assistant', content: answer });
            },
            error: function(xhr){
                let msg = 'Ошибка AI';
                try { msg = JSON.parse(xhr.responseText).error || msg; }
                catch(e) { msg = xhr.responseText || msg; }
                $thinking.text('⚠ ' + msg);
            },
            complete: function(){
                $('#ai_send').prop('disabled', false);
                $('#ai_prompt').focus();
            }
        });
    });

    // ==================== ЗМЕЙКА ====================
    const canvas = document.getElementById('snake_canvas');
    if (canvas) {
        const ctx = canvas.getContext('2d');
        const CELL = 20;
        const COLS = canvas.width / CELL;
        const ROWS = canvas.height / CELL;

        let snake, dir, nextDir, food, score, timer, running;

        function reset(){
            snake = [{x: 9, y: 9}, {x: 8, y: 9}, {x: 7, y: 9}];
            dir = {x: 1, y: 0};
            nextDir = {x: 1, y: 0};
            score = 0;
            running = false;
            clearInterval(timer);
            placeFood();
            draw();
            $('#score').text(0);
            $('#snake_msg').text('Нажми «Старт» или стрелки, чтобы начать');
        }

        function placeFood(){
            while (true) {
                const f = {
                    x: Math.floor(Math.random() * COLS),
                    y: Math.floor(Math.random() * ROWS)
                };
                if (!snake.some(s => s.x === f.x && s.y === f.y)) {
                    food = f;
                    return;
                }
            }
        }

        function draw(){
            ctx.fillStyle = '#111';
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            // еда
            ctx.fillStyle = '#e63946';
            ctx.beginPath();
            ctx.arc(food.x*CELL + CELL/2, food.y*CELL + CELL/2, CELL/2 - 2, 0, Math.PI*2);
            ctx.fill();

            // змейка
            snake.forEach((s, i) => {
                ctx.fillStyle = i === 0 ? '#4ade80' : '#22c55e';
                ctx.fillRect(s.x*CELL + 1, s.y*CELL + 1, CELL - 2, CELL - 2);
            });
        }

        function step(){
            dir = nextDir;
            const head = { x: snake[0].x + dir.x, y: snake[0].y + dir.y };

            if (head.x < 0 || head.x >= COLS || head.y < 0 || head.y >= ROWS) {
                return gameOver();
            }
            if (snake.some(s => s.x === head.x && s.y === head.y)) {
                return gameOver();
            }

            snake.unshift(head);

            if (head.x === food.x && head.y === food.y) {
                score++;
                $('#score').text(score);
                placeFood();
            } else {
                snake.pop();
            }
            draw();
        }

        function gameOver(){
            running = false;
            clearInterval(timer);
            $('#snake_msg').text('💀 Игра окончена. Съедено яблок: ' + score);
        }

        function start(){
            reset();
            running = true;
            $('#snake_msg').text('');
            clearInterval(timer);
            timer = setInterval(step, 120);
        }

        function setDir(name){
            const map = {
                up:    {x: 0,  y: -1},
                down:  {x: 0,  y: 1},
                left:  {x: -1, y: 0},
                right: {x: 1,  y: 0},
            };
            const d = map[name];
            if (!d) return;
            if (d.x === -dir.x && d.y === -dir.y) return;
            nextDir = d;
            if (!running && snake) {
                running = true;
                clearInterval(timer);
                timer = setInterval(step, 120);
                $('#snake_msg').text('');
            }
        }

        $('.controls button[data-dir]').on('click', function(){
            setDir($(this).data('dir'));
        });

        $(document).on('keydown.snake', function(e){
            const k = e.key.toLowerCase();
            if (['arrowup','w','ц'].includes(k))         { e.preventDefault(); setDir('up'); }
            else if (['arrowdown','s','ы'].includes(k))  { e.preventDefault(); setDir('down'); }
            else if (['arrowleft','a','ф'].includes(k))  { e.preventDefault(); setDir('left'); }
            else if (['arrowright','d','в'].includes(k)) { e.preventDefault(); setDir('right'); }
        });

        $('#snake_start').on('click', start);

        reset();
    }

});