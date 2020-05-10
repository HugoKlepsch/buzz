console.log('game view page');

var player_list_table = document.getElementById('player_list');
var player_list_tbody = document.getElementById('player_list_tbody');
var q_num_field = document.getElementById('q_num');
var session_key = sessionStorage.getItem('session_key');
var game_ext_id = sessionStorage.getItem('game_ext_id');
var q_num = 0;

if (session_key === null || game_ext_id === null) {
  window.location.replace('/');
}

setInterval(function () {
  console.log('game view update trigger');

  var xhr = new XMLHttpRequest();
  xhr.open('POST', '/api/' + game_ext_id, true);
  xhr.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
  xhr.send(JSON.stringify({
    'session_key': session_key
  }));

  xhr.onreadystatechange = function () {
    if (xhr.readyState === XMLHttpRequest.DONE) {
      if (xhr.status === 200) {
        resp = JSON.parse(xhr.responseText);
        q_num = resp['q_num'];
        player_list = resp['player_list'];

        q_num_field.innerHTML = q_num;

        var new_tbody = document.createElement('tbody');
        player_list.forEach(function (player) {
          var newRow = new_tbody.insertRow(-1);

          var playerCell = newRow.insertCell(0);
          var playerText = document.createTextNode(player['username']);
          playerCell.appendChild(playerText);

          var buzzOrderCell = newRow.insertCell(1);
          var buzzOrderText = document.createTextNode(player['buzz_order']);
          buzzOrderCell.appendChild(buzzOrderText);
        })
        player_list_table.replaceChild(new_tbody, player_list_tbody);
        player_list_tbody = new_tbody;

        console.log('/api/' + game_ext_id + ' response: ' + JSON.stringify(resp));
      } else if (xhr.status === 401) {
        window.location.replace('/');
      } else {
        console.log('There was a problem with the request');
      }
    }
  }
}, 200);

function buzz() {
  var xhr = new XMLHttpRequest();
  xhr.open('POST', '/api/' + game_ext_id + '/buzz', true);
  xhr.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
  xhr.send(JSON.stringify({
    'session_key': session_key
  }))

  xhr.onreadystatechange = function () {
    if (xhr.readyState === XMLHttpRequest.DONE) {
      if (xhr.status === 200) {
        resp = JSON.parse(xhr.responseText);
        console.log('/api/' + game_ext_id + '/buzz response: ' + JSON.stringify(resp));
      } else {
        console.log('Buzz failed: ' + xhr.status);
      }
    }
  }
}

function clearbuzz() {
  var xhr = new XMLHttpRequest();
  xhr.open('POST', '/api/' + game_ext_id + '/clearbuzz', true);
  xhr.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
  xhr.send(JSON.stringify({
    'session_key': session_key
  }))

  xhr.onreadystatechange = function () {
    if (xhr.readyState === XMLHttpRequest.DONE) {
      if (xhr.status === 200) {
        resp = JSON.parse(xhr.responseText);
        console.log('/api/' + game_ext_id + '/clearbuzz response: ' + JSON.stringify(resp));
      } else {
        console.log('Clearbuzz failed: ' + xhr.status);
      }
    }
  }
}

function q_num_up() {
  q_num = q_num + 1;
  set_q_num_call();
}

function q_num_down() {
  q_num = q_num - 1;
  set_q_num_call();
}

function set_q_num_call() {
  var xhr = new XMLHttpRequest();
  xhr.open('POST', '/api/' + game_ext_id + '/set_q_num', true);
  xhr.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
  xhr.send(JSON.stringify({
    'session_key': session_key,
    'q_num': q_num
  }))

  xhr.onreadystatechange = function () {
    if (xhr.readyState === XMLHttpRequest.DONE) {
      if (xhr.status === 200) {
        resp = JSON.parse(xhr.responseText);
        console.log('/api/' + game_ext_id + '/set_q_num response: ' + JSON.stringify(resp));
      } else {
        console.log('Set q num failed: ' + xhr.status);
      }
    }
  }
}
