var username_field = document.getElementById('username')
var game_ext_id_field = document.getElementById('game_ext_id')
var username_create = document.getElementById('username_create')

function join() {
  console.log('join function called');
  username = username_field.value;
  game_ext_id = game_ext_id_field.value;
  console.log('username: ' + username);
  console.log('game_ext_id: ' + game_ext_id);

  var xhr = new XMLHttpRequest();
  xhr.open('POST', '/api/' + game_ext_id + '/join', true);
  xhr.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
  xhr.send(JSON.stringify({
    'username': username
  }))

  xhr.onreadystatechange = function () {
    if (xhr.readyState === XMLHttpRequest.DONE) {
      if (xhr.status === 200) {
        resp = JSON.parse(xhr.responseText);
        sessionStorage.setItem('session_key', resp['session_key']);
        sessionStorage.setItem('game_ext_id', game_ext_id);
        console.log('/api/' + game_ext_id + '/join response: ' + JSON.stringify(resp));

        window.location.replace('/' + game_ext_id);
      } else {
        alert('There was a problem with the request.');
      }
    }
  }
}

function create() {
  console.log('create function called')
  username = username_create.value;
  console.log('username: ' + username);

  var xhr = new XMLHttpRequest();
  xhr.open('POST', '/api/create', true);
  xhr.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
  xhr.send(JSON.stringify({
    'username': username
  }));

  xhr.onreadystatechange = function () {
    if (xhr.readyState === XMLHttpRequest.DONE) {
      if (xhr.status === 200) {
        resp = JSON.parse(xhr.responseText);
        sessionStorage.setItem('session_key', resp['session_key']);
        game_ext_id = resp['game_ext_id'];
        sessionStorage.setItem('game_ext_id', resp['game_ext_id']);
        console.log('/api/create response: ' + JSON.stringify(resp));

        window.location.replace('/' + game_ext_id);
      } else {
        alert('There was a problem with the request.');
      }
    }
  }
}
